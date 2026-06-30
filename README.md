# Enterprise Ticket Resolution Engine

A multi-agent backend that automatically classifies, routes, and resolves enterprise support tickets using a graph-based agent orchestration layer, with live operational visibility over WebSockets.

This is not a CRUD wrapper around an LLM call. The interesting engineering problem here is **coordinating state across a graph of specialized agents while keeping the system observable, debuggable, and recoverable** — the same problem enterprise automation vendors solve for their clients.

---

## Why this exists

Most support ticket triage follows a predictable pattern: classify the issue, route it to the right team, resolve it if it's routine, escalate it if it's not. Doing this with a single large prompt works for demos but breaks down in production — you lose the ability to retry a single failed step, audit why a decision was made, or swap out one agent's logic without touching the rest.

This project treats ticket resolution as an explicit **state machine** rather than a single opaque LLM call. Each stage of resolution is a node in a graph with defined inputs and outputs, which means failures are isolated, decisions are traceable, and the system can be extended with new agent types without restructuring existing ones.

---

## System architecture

```mermaid
flowchart TB
    subgraph Client["External clients"]
        ext["External system<br/>(CRM, monitoring tool)"]
        admin["Admin dashboard"]
    end

    subgraph API["FastAPI gateway"]
        auth["OAuth2 / JWT auth"]
        ticketRoute["POST /tickets"]
        getRoutes["GET /tickets"]
        ws["WebSocket /ws/dashboard"]
    end

    subgraph Agents["LangGraph agent workflow"]
        orch["Orchestrator<br/>classifies ticket"]
        billing["Billing agent"]
        tech["Tech agent"]
        escalation["Escalation agent"]
    end

    subgraph Data["Data layer"]
        pg[("PostgreSQL<br/>tickets, events, users")]
        pinecone[("Pinecone<br/>past resolutions")]
        redis[("Redis Pub/Sub<br/>event bus")]
    end

    ext -->|API token| ticketRoute
    admin -->|JWT| ticketRoute
    admin --> getRoutes
    admin -.->|live updates| ws

    ticketRoute --> auth
    auth --> pg
    ticketRoute -.->|background task| orch

    orch --> billing
    orch --> tech
    orch --> escalation

    billing <--> pinecone
    tech <--> pinecone

    billing --> pg
    tech --> pg
    escalation --> pg

    pg --> redis
    redis --> ws
```

The gateway never blocks on agent execution. A ticket submission returns `202 Accepted` immediately; the graph runs as a background task and reports its own progress through Redis. This separation exists because LLM calls are slow and unpredictable in latency — coupling API response time to model inference time is the most common mistake in systems like this.

---

## The agent graph

Routing is handled as a conditional edge in a LangGraph `StateGraph`, not as if/else branching inside a monolithic function. The orchestrator's only job is classification — it has no knowledge of how billing or technical issues get resolved, which keeps it swappable and easy to reason about in isolation.

```mermaid
flowchart TD
    START([Ticket received]) --> orch["Orchestrator node<br/>classifies category"]
    orch -->|billing| billingNode["Billing agent<br/>+ Pinecone context"]
    orch -->|technical| techNode["Tech agent<br/>+ Pinecone context"]
    orch -->|general / unresolved| escNode["Escalation agent<br/>writes human-readable reason"]
    billingNode --> persist["Persist result<br/>+ publish to Redis"]
    techNode --> persist
    escNode --> persist
    persist --> END([Dashboard updates live])
```

Each node receives and returns the same `TicketState` shape — a `TypedDict` carrying the ticket's identity, classification, accumulated message history, and resolution status. This is what makes the graph composable: a node doesn't need to know what ran before it, only what shape of state to expect.

**Why retrieval-augmented context matters here:** before a specialist agent attempts a resolution, it queries Pinecone for semantically similar tickets that were resolved previously, filtered by category. The agent's prompt is built with that precedent as context. This is the difference between an agent that reasons from scratch every time and one that benefits from the organization's accumulated resolution history — closer to how a human support team actually improves over time.

---

## Data model

The schema separates **current state** from **history** deliberately. A ticket row only ever reflects its current status; every transition it goes through is written as an immutable `ticket_events` row. This is the pattern enterprise systems use for audit compliance — you can reconstruct exactly what happened to a ticket and when, rather than relying on `updated_at` timestamps that overwrite the story.

```mermaid
erDiagram
    USERS ||--o{ ESCALATIONS : "assigned to"
    USERS ||--o{ API_TOKENS : owns
    TICKETS ||--o{ AGENT_TASKS : "routed to"
    TICKETS ||--o{ TICKET_EVENTS : logs
    TICKETS ||--o| ESCALATIONS : escalates

    USERS {
        uuid id PK
        string email
        enum role
    }
    TICKETS {
        uuid id PK
        string title
        text description
        enum category
        enum status
        enum priority
    }
    AGENT_TASKS {
        uuid id PK
        uuid ticket_id FK
        enum agent_type
        enum status
        text result
    }
    TICKET_EVENTS {
        uuid id PK
        uuid ticket_id FK
        enum event_type
        text message
    }
    ESCALATIONS {
        uuid id PK
        uuid ticket_id FK
        uuid assigned_to FK
        text reason
        enum status
    }
    API_TOKENS {
        uuid id PK
        uuid created_by FK
        string token_hash
    }
```

A few decisions worth explaining rather than just stating: `escalations.ticket_id` carries a unique constraint, enforcing a one-to-one relationship at the database level rather than only in application code — if a bug ever attempted to create a second escalation for the same ticket, the database rejects it rather than silently corrupting state. `escalations.assigned_to` is nullable because a ticket can escalate before any human has claimed it; making it required would make the row impossible to create at the moment it's most needed.

---

## Why these specific tools

| Layer | Tool | Reasoning |
|---|---|---|
| Agent orchestration | LangGraph | Models the workflow as an explicit graph with inspectable state, rather than hiding control flow inside a framework's internal loop. Production agent systems need this level of control for debugging and partial retries. |
| LLM orchestration | LangChain (LCEL) | Composable `prompt \| llm \| parser` chains keep prompt engineering, model calls, and output parsing as separable concerns. |
| Vector retrieval | Pinecone | Gives agents access to institutional memory — past resolutions — without retraining anything. This is the RAG pattern applied to operational knowledge rather than documents. |
| Event distribution | Redis Pub/Sub | Decouples the agent workflow from the dashboard. The graph doesn't know or care whether anyone is watching; it publishes and moves on. |
| Real-time UI | WebSockets | The dashboard reflects agent state changes within milliseconds of them happening, without polling. |
| Auth | OAuth2 / JWT | Distinguishes between human dashboard users and machine-to-machine API tokens — they have different trust boundaries and shouldn't share an auth mechanism. |

---

## Request lifecycle, end to end

```mermaid
sequenceDiagram
    participant C as Client system
    participant API as FastAPI
    participant DB as PostgreSQL
    participant G as LangGraph
    participant P as Pinecone
    participant R as Redis
    participant D as Dashboard

    C->>API: POST /tickets
    API->>DB: insert ticket (status=PENDING)
    API-->>C: 202 Accepted
    API->>G: run workflow (background)
    G->>G: orchestrator classifies
    G->>P: search similar resolved tickets
    P-->>G: relevant context
    G->>G: specialist agent resolves
    G->>DB: persist result + event log
    G->>P: store new resolution
    G->>R: publish status update
    R->>D: push via WebSocket
```

The client never waits for any of this beyond the initial acknowledgment. This matters because LLM round trips are the slowest part of the system by an order of magnitude — anywhere from one to several seconds — and no API consumer should be blocked on that.

---

## What this demonstrates

Building this required reasoning through several tradeoffs that don't have a single correct answer, which is the actual point of the project:

- **Where database writes belong.** Agent nodes return state; they don't write to the database directly. Persistence happens once, after the graph completes, which keeps the agent logic pure and testable in isolation from infrastructure concerns.
- **What happens when an agent fails.** Every node has explicit error handling that defaults to escalation rather than silent failure — an LLM timeout should never result in a ticket disappearing into an unresolved state with no human aware of it.
- **Why one-to-one relationships need database-level enforcement,** not just application-level discipline, because application code has bugs and databases are the last line of defense.

---

## Stack

FastAPI · PostgreSQL · SQLAlchemy (async) · LangChain · LangGraph · Pinecone · Redis · WebSockets · OAuth2 · Docker

---

## Running locally

### Prerequisites
- Python 3.11+
- Docker (for PostgreSQL and Redis)
- An OpenAI API key
- A Pinecone account and API key

### 1. Clone and install

```bash
git clone <repo-url>
cd ticket-system-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ticketdb

# Redis
REDIS_URL=redis://localhost:6379

# Auth
SECRET_KEY=your-secret-key-here

# AI
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
```

`SECRET_KEY` signs JWT tokens — generate one rather than leaving it blank:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL and Redis as background containers. Confirm both are running:
```bash
docker compose ps
```

### 4. Create the Pinecone index (one-time setup)

```bash
python -m app.scripts.create_pinecone_index
```

This only needs to run once. Running it again will error since the index already exists — that's expected.

### 5. Create database tables

```bash
python -c "import asyncio; from app.db.create_db import create_db_and_tables; asyncio.run(create_db_and_tables())"
```

### 6. Run the API

```bash
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Interactive docs are available at `http://localhost:8000/docs`.

### 7. Verify the setup

Hit the docs page and try creating a ticket through `POST /tickets`. If everything is wired correctly, you should see:
- A new row in the `tickets` table
- A background agent workflow kick off (check your terminal logs)
- A resolved or escalated status within a few seconds

---

## Environment variables reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Async PostgreSQL connection string. Use `postgresql+asyncpg://` scheme, not plain `postgresql://`. |
| `REDIS_URL` | Yes | Redis connection string for the Pub/Sub event bus. |
| `SECRET_KEY` | Yes | Used to sign JWT tokens. Never reuse a dev key in production. |
| `OPENAI_API_KEY` | Yes | Used by every LangChain `ChatOpenAI` call across all agent nodes. |
| `PINECONE_API_KEY` | Yes | Used for similarity search against past resolved tickets. |
