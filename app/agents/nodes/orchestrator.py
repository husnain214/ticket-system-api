from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.state import AgentState
from app.agents.prompts.orchestrator import orchestrator_prompt
from app.db.enums import TicketCategory
from app.core.config import settings

llm = ChatOpenAI(
    model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY.get_secret_value()
)


async def orchestrator_node(state: AgentState) -> AgentState:
    try:
        chain = orchestrator_prompt | llm | StrOutputParser()

        response = await chain.ainvoke(
            {
                "title": state["title"],
                "description": state["description"],
            }
        )

        category_str = response.strip().lower()

        category_map = {
            "billing": TicketCategory.BILLING,
            "technical": TicketCategory.TECHNICAL,
            "general": TicketCategory.GENERAL,
        }

        category = category_map.get(category_str, TicketCategory.GENERAL)
        human_msg = HumanMessage(
            content=f"Classify this ticket: {state['title']} - {state['description']}"
        )
        ai_msg = AIMessage(content=f"Category: {category_str}")

        return {
            **state,
            "category": category,
            "messages": [human_msg, ai_msg],
            "status": state["status"],
            "error": None,
        }
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "category": TicketCategory.GENERAL,
        }


def route_ticket(state: AgentState) -> str:
    """
    This is the conditional edge function.
    Reads category from state and returns which node to go to next.
    """

    category = state["category"]

    if category == TicketCategory.BILLING:
        return "billing_agent"
    elif category == TicketCategory.TECHNICAL:
        return "tech_agent"
    else:
        return "escalation_agent"
