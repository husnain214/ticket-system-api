from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.state import AgentState
from app.agents.prompts.escalation import escalation_prompt
from app.db.enums import TicketStatus

from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)


async def escalation_node(state: AgentState) -> AgentState:
    try:
        chain = escalation_prompt | llm | StrOutputParser()

        reason = await chain.ainvoke(
            {
                "title": state["title"],
                "description": state["description"],
                "priority": state["priority"],
                "category": state["category"],
            }
        )

        human_msg = HumanMessage(
            content=f"Escalate ticket: {state['title']} - {state['description']}"
        )
        ai_msg = AIMessage(content=reason)

        return {
            **state,
            "result": reason,
            "status": TicketStatus.ESCALATED,
            "messages": [human_msg, ai_msg],
            "error": None,
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "status": TicketStatus.ESCALATED,
        }
