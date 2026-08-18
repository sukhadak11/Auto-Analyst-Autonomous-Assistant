# src/agent/human_checkpoint.py
from graph_state import AgentState

def human_checkpoint_node(state: AgentState) -> AgentState:
    print("\n" + "=" * 60)
    print("HUMAN APPROVAL CHECKPOINT")
    print("=" * 60)

    print(f"\nCritic status: {'APPROVED' if state.get('approved') else 'NOT APPROVED'}")
    print(f"Revisions used: {state.get('revision_count', 0)}")

    print("\n--- FINAL REPORT ---\n")
    print(state.get("report", "No report generated."))

    if not state.get("approved", False):
        print("\n--- OUTSTANDING CRITIC ISSUES ---\n")
        print(state.get("critique", "No critique available."))

    print("\n" + "-" * 60)
    decision = input(
        "Approve this report for release? [y]es / [n]o / [e]dit notes: "
    ).strip().lower()

    if decision == "y":
        state["human_decision"] = "approved"
        print("\n✅ Report approved by human reviewer. Finalized.")
    elif decision == "e":
        notes = input("Enter revision notes for a future rerun: ")
        state["human_decision"] = "needs_revision"
        state["human_notes"] = notes
        print("\n📝 Notes recorded. Report marked for future revision.")
    else:
        state["human_decision"] = "rejected"
        print("\n❌ Report rejected by human reviewer.")

    state["messages"] = state.get("messages", []) + [
        f"Human checkpoint decision: {state['human_decision']}"
    ]
    return state
'''
if __name__ == "__main__":
    fake_state = {
        "question": "Why is churn spiking?",
        "report": "Churn is spiking due to contract type and tenure, per SHAP analysis. Industry average is 20-25% annually.",
        "critique": "VERDICT: APPROVED\nISSUES: None",
        "approved": True,
        "revision_count": 1,
        "messages": [],
    }
    result = human_checkpoint_node(fake_state)
    print("\nFinal state human_decision:", result["human_decision"])
    '''