import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agents.health_agent import detect_health_issues
from agents.cost_agent import analyze_cost
from agents.resource_agent import analyze_resources
from ai.claude_service import analyze_with_claude
from policy.risk_policy import check_risk
from agents.remediation_agent import restart_pod, scale_deployment, verify_pod, verify_deployment
from database.db import init_db, log_incident

class AgentState(TypedDict, total=False):
    incident: dict
    agent_results: list
    ai_recommendation: dict
    risk: str
    human_approved: bool
    action_result: dict
    verification_status: str

def monitor(state):
    # Pehle health signals observe kar rahe hain.
    issues = detect_health_issues()
    state["incident"] = issues[0] if issues else {}
    return state

def analyze(state):
    incident = state.get("incident", {})
    if not incident:
        state["agent_results"] = [{"recommendation": "no_action", "reason": "No incident detected"}]
        return state
    results = [incident]
    try:
        cost = analyze_cost(incident["namespace"], os.getenv("TARGET_DEPLOYMENT", "busy-worker"))
        results.append(cost)
        results.append(analyze_resources(cost.get("cpu_percent"),
                         current_replicas=cost.get("current_replicas", 1)))
    except Exception as exc:
        results.append({"recommendation": "no_action", "reason": f"Metrics unavailable: {exc}"})
    state["agent_results"] = results
    return state

def ai_reason(state):
    # Claude ko sirf collected incident context de rahe hain.
    state["ai_recommendation"] = analyze_with_claude(
        {"incident": state.get("incident", {}),
         "agent_recommendations": state.get("agent_results", [])})
    return state

def risk_check(state):
    incident = state.get("incident", {})
    ai = state.get("ai_recommendation", {})
    state["risk"] = check_risk(ai.get("action", "no_action"), incident.get("namespace", "default"))
    return state

def approval(state):
    if state.get("risk") != "high":
        state["human_approved"] = True
        return state
    print("AI recommends:", state.get("ai_recommendation", {}))
    # High-risk action ke liye human approval mandatory hai.
    state["human_approved"] = input("Risk: HIGH | Approve? (yes/no): ").strip().lower() == "yes"
    return state

def remediate(state):
    if not state.get("human_approved"):
        state["action_result"] = {"status": "rejected"}
        return state
    incident = state.get("incident", {})
    action = state.get("ai_recommendation", {}).get("action")
    ns = incident.get("namespace", "default")
    if action == "restart_pod" and incident.get("pod"):
        state["action_result"] = restart_pod(ns, incident["pod"])
    elif action == "scale_deployment":
        deployment = os.getenv("TARGET_DEPLOYMENT", "busy-worker")
        replicas = int(os.getenv("SUGGESTED_REPLICAS", "1"))
        state["action_result"] = scale_deployment(ns, deployment, replicas)
    else:
        state["action_result"] = {"status": "no_action"}
    return state

def verify(state):
    result = state.get("action_result", {})
    if result.get("status") in {"rejected", "no_action"}:
        state["verification_status"] = "not_required"
        return state
    try:
        incident = state["incident"]
        if result.get("action") == "restart_pod":
            ok = verify_pod(incident["namespace"], incident["pod"])
        else:
            ok = verify_deployment(incident["namespace"], result["deployment"], result["replicas"])
        state["verification_status"] = "success" if ok else "failure"
    except Exception as exc:
        state["verification_status"] = f"failure: {exc}"
    return state

def audit(state):
    # Failure ko infinite retry mein nahi bhejte; audit ke baad flow stop hota hai.
    try:
        init_db()
        incident = state.get("incident", {})
        log_incident({"namespace": incident.get("namespace", "default"),
          "resource_name": incident.get("pod", os.getenv("TARGET_DEPLOYMENT", "busy-worker")),
          "problem": incident.get("problem", "none"),
          "agent_recommendation": state.get("agent_results", []),
          "ai_recommendation": state.get("ai_recommendation", {}),
          "risk_level": state.get("risk", "low"),
          "human_approval": state.get("human_approved", False),
          "action_taken": str(state.get("action_result", {})),
          "verification_status": state.get("verification_status", "unknown")})
    except Exception as exc:
        print("Audit log unavailable:", exc)
    return state

def build_graph():
    # Graph intentionally small hai: Observe -> Analyze -> AI -> Risk -> Approve -> Act -> Verify -> Audit.
    graph = StateGraph(AgentState)
    for name, fn in [("health_monitor", monitor), ("analysis", analyze), ("claude", ai_reason),
                     ("risk_check", risk_check), ("human_approval", approval),
                     ("remediation", remediate), ("verification", verify), ("audit", audit)]:
        graph.add_node(name, fn)
    graph.add_edge(START, "health_monitor")
    graph.add_edge("health_monitor", "analysis")
    graph.add_edge("analysis", "claude")
    graph.add_edge("claude", "risk_check")
    graph.add_edge("risk_check", "human_approval")
    graph.add_edge("human_approval", "remediation")
    graph.add_edge("remediation", "verification")
    graph.add_edge("verification", "audit")
    graph.add_edge("audit", END)
    return graph.compile()

if __name__ == "__main__":
    print(build_graph().invoke({"agent_results": [], "human_approved": False}))
