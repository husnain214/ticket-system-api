from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.nodes.orchestrator import orchestrator_node, route_ticket
from app.agents.nodes.tech import tech_node
from app.agents.nodes.escalation import escalation_node
from app.agents.nodes.billing import billing_node

graph = StateGraph(AgentState)

graph.add_node("orchestrator", orchestrator_node)
graph.add_node("tech", tech_node)
graph.add_node("billing", billing_node)
graph.add_node("escalation", escalation_node)

graph.add_edge(START, "orchestrator")

graph.add_conditional_edges(
    "orchestrator",
    route_ticket,
    {
        "billing_agent": "billing",
        "tech_agent": "tech",
        "escalation_agent": "escalation",
    },
)

graph.add_edge("tech", END)
graph.add_edge("billing", END)
graph.add_edge("escalation", END)

app = graph.compile()
