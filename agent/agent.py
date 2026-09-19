from typing import TypedDict
import pandas as pd
from scoring import load_model, load_accounts, score_accounts
from langgraph.graph import StateGraph, START, END


class SalesAgentState(TypedDict, total=False):
    accounts: pd.DataFrame
    priority_accounts: pd.DataFrame
    recommendations: list[dict]
    rep_briefs: list[dict]
    queue_size: int
    
def score_accounts_node(state: SalesAgentState) -> SalesAgentState:
    """Load the model and account data, then score all accounts."""
    model = load_model()
    accounts = load_accounts()
    scored_accounts = score_accounts(model, accounts)
    return {
        "accounts": scored_accounts
    }
    
def select_priority_queue_node(
    state: SalesAgentState
) -> SalesAgentState:
    """Select the highest-ranked accounts based on sales capacity."""
    scored_accounts = state["accounts"]
    queue_size = state.get("queue_size", 20)

    priority_accounts = scored_accounts.head(queue_size).copy()

    return {
        "priority_accounts": priority_accounts
    }
    

def determine_sales_action(account: pd.Series) -> str:
    """Determine the sales action for a prioritized account."""
    sales_contacts = account["sales_contacts_90d"]

    if sales_contacts == 0:
        return "PRIORITIZE_OUTREACH"

    return "FOLLOW_UP"

def build_account_reasons(account: pd.Series) -> list[str]:
    """Build factual reasons from the account's observed signals."""
    reasons = []

    reasons.append(
        f"Ranked highly by the conversion model "
        f"({account['conversion_probability']:.2%})"
    )

    if account["mql_count_90d"] > 0:
        reasons.append(
            f"{int(account['mql_count_90d'])} MQL(s) in the last 90 days"
        )

    if account["trial_started"] == 1:
        reasons.append(
            f"Trial started with "
            f"{int(account['trial_active_users'])} active user(s)"
        )

    if account["web_touchpoints_90d"] > 0:
        reasons.append(
            f"{int(account['web_touchpoints_90d'])} web touchpoint(s) "
            f"in the last 90 days"
        )

    if account["sales_contacts_90d"] == 0:
        reasons.append("No recorded sales contacts in the last 90 days")
    else:
        reasons.append(
            f"{int(account['sales_contacts_90d'])} sales contact(s) "
            f"in the last 90 days"
        )

    return reasons

def build_next_step(action: str) -> str:
    """Return the suggested next sales step for an action."""

    if action == "PRIORITIZE_OUTREACH":
        return "Initiate sales outreach while recent engagement signals are present."

    if action == "FOLLOW_UP":
        return "Continue the existing sales motion using the account's recent engagement context."

    return "Keep the account in nurture and reassess when new engagement signals appear."


def recommend_actions_node(
    state: SalesAgentState
) -> SalesAgentState:
    """Generate a sales action for each account in the priority queue."""
    priority_accounts = state["priority_accounts"]

    recommendations = []

    for _, account in priority_accounts.iterrows():
        action = determine_sales_action(account)
        reasons = build_account_reasons(account)
        next_step = build_next_step(action)

        recommendations.append(
            {
                "account_id": account["account_id"],
                "conversion_probability": account["conversion_probability"],
                "action": action,
                "reasons": reasons,
                "next_step": next_step,
            }
        )

    return {
        "recommendations": recommendations
    }
       
    
def generate_rep_brief_node(
    state: SalesAgentState
) -> SalesAgentState:
    """Generate concise rep-facing briefs from grounded recommendations."""
    recommendations = state["recommendations"]

    rep_briefs = []

    for recommendation in recommendations:
        reasons_text = "; ".join(recommendation["reasons"])

        brief = (
            f"{recommendation['action']}: "
            f"{reasons_text}. "
            f"Suggested next step: {recommendation['next_step']}"
        )

        rep_briefs.append(
            {
                "account_id": recommendation["account_id"],
                "brief": brief,
            }
        )

    return {
        "rep_briefs": rep_briefs
    }
    
      
def build_sales_agent():
    """Build and compile the sales prioritization workflow."""
    graph = StateGraph(SalesAgentState)

    graph.add_node("score_accounts", score_accounts_node)
    graph.add_node("select_priority_queue", select_priority_queue_node)
    graph.add_node("recommend_actions", recommend_actions_node)
    graph.add_node("generate_rep_brief", generate_rep_brief_node)

    graph.add_edge(START, "score_accounts")
    graph.add_edge("score_accounts", "select_priority_queue")
    graph.add_edge("select_priority_queue", "recommend_actions")
    graph.add_edge("recommend_actions", "generate_rep_brief")
    graph.add_edge("generate_rep_brief", END)

    return graph.compile()
    
    
    
if __name__ == "__main__":
    sales_agent = build_sales_agent()

    result = sales_agent.invoke(
        {
            "queue_size": 20
        }
    )

    print(f"Total scored accounts: {len(result['accounts'])}")
    print(f"Priority queue size: {len(result['priority_accounts'])}")

    print("\nSales Rep Briefs:")

    for item in result["rep_briefs"][:5]:
        print(f"\n{item['account_id']}")
        print(item["brief"])