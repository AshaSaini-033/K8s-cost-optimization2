import json
import os
from langchain_anthropic import ChatAnthropic

PROMPT = """You are a Kubernetes operations assistant.
Return ONLY JSON with root_cause, action, risk, reason.
Allowed actions: restart_pod, scale_deployment, no_action.
You only recommend; Python policy and predefined tools execute actions.
Do not invent metrics."""

def analyze_with_claude(context):
    # Claude ko limited context milta hai; direct Kubernetes access nahi.
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"root_cause": "unknown", "action": "no_action",
                "risk": "high", "reason": "ANTHROPIC_API_KEY is not configured"}
    model = ChatAnthropic(model=os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest"),
                          temperature=0, api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = model.invoke([("system", PROMPT), ("human", json.dumps(context, default=str))])
    text = response.content if isinstance(response.content, str) else str(response.content)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"root_cause": "unstructured_response", "action": "no_action",
                "risk": "high", "reason": text[:500]}
