from app.lib.pinecone_tools import search_similar_tickets, store_resolved_ticket
from app.agents.state import AgentState
from app.agents.prompts.billing import billing_prompt
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from app.db.enums import TicketStatus
from app.core.config import settings

llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=settings.OPENAI_API_KEY)


async def billing_node(state: AgentState) -> AgentState:
    try:
        context = search_similar_tickets(
            category=state["category"], description=state["description"]
        )

        chain = billing_prompt | llm | StrOutputParser()

        resolution = await chain.ainvoke(
            {
                "title": state["title"],
                "description": state["description"],
                "priority": state["priority"],
                "context": context,
            }
        )

        store_resolved_ticket(
            category=state["category"],
            description=state["description"],
            resolution=resolution,
        )

        human_msg = HumanMessage(
            content=f"Resolve billing ticket: {state['title']} - {state['description']}"
        )
        ai_msg = AIMessage(content=resolution)

        return {
            **state,
            "result": resolution,
            "status": TicketStatus.RESOLVED,
            "messages": [human_msg, ai_msg],
            "error": None,
        }
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "status": TicketStatus.ESCALATED,
        }
