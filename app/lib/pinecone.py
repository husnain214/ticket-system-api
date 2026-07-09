from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import settings
from app.db.enums import TicketCategory
from dotenv import load_dotenv

load_dotenv()

embeddings = OpenAIEmbeddings()
pc = Pinecone(api_key=settings.PINECONE_API_KEY)


def _get_vector_store() -> PineconeVectorStore:
    index = pc.Index("ticket-resolutions")
    return PineconeVectorStore(index=index, embedding=embeddings)


vector_store: PineconeVectorStore | None = None


def get_vector_store() -> PineconeVectorStore:
    global vector_store
    if vector_store is None:
        vector_store = _get_vector_store()
    return vector_store


async def create_pinecone_index() -> None:
    """
    Creates the Pinecone index if it doesn't already exist.
    Safe to call on every startup.
    """
    existing = [i.name for i in pc.list_indexes()]

    if "ticket-resolutions" in existing:
        print("Pinecone index already exists — skipping")
        return

    pc.create_index(
        name="ticket-resolutions",
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    print("Pinecone index created successfully")


def search_similar_tickets(
    description: str,
    category: TicketCategory | None,
    k: int = 3,
) -> str:
    """
    Searches Pinecone for similar past resolved tickets in the same category.
    Returns a formatted context string for use in agent prompts.
    """
    try:
        category_str = category.value if category else "general"

        results = get_vector_store().similarity_search(
            description,
            k=k,
            filter={"category": category_str},
        )

        if not results:
            return "No similar past tickets found."

        context_parts = []
        for i, doc in enumerate(results, 1):
            resolution = doc.metadata.get("resolution", "No resolution recorded")
            context_parts.append(
                f"{i}. {doc.page_content}\n   Resolution: {resolution}"
            )

        return "\n".join(context_parts)

    except Exception:
        return "No similar past tickets found."


def store_resolved_ticket(
    description: str,
    resolution: str,
    category: TicketCategory | None,
) -> None:
    """
    Stores a resolved ticket in Pinecone so future agents
    can use it as context for similar tickets.
    """
    category_str = category.value if category else "general"

    get_vector_store().add_texts(
        texts=[description],
        metadatas=[{"resolution": resolution, "category": category_str}],
    )
