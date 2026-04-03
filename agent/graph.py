from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import router_node, query_node, chart_node, summary_node, validator_node


def route_decision(state: AgentState) -> str:
    """Tells LangGraph which node to go to after the router"""
    return state["route"]


def validation_decision(state: AgentState) -> str:
    """Tells LangGraph whether to accept answer or retry"""
    if state.get("is_valid"):
        return "end"
    else:
        return "retry"


def build_graph():
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("router", router_node)
    graph.add_node("query", query_node)
    graph.add_node("chart", chart_node)
    graph.add_node("summary", summary_node)
    graph.add_node("validator", validator_node)

    # Entry point
    graph.set_entry_point("router")

    # Router sends to one of three nodes
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "query": "query",
            "chart": "chart",
            "summary": "summary"
        }
    )

    # All three nodes feed into validator
    graph.add_edge("query", "validator")
    graph.add_edge("chart", "validator")
    graph.add_edge("summary", "validator")

    # Validator either ends or loops back to router
    graph.add_conditional_edges(
        "validator",
        validation_decision,
        {
            "end": END,
            "retry": "router"
        }
    )

    return graph.compile()