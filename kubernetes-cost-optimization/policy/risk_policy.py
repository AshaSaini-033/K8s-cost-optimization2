ALLOWED_ACTIONS = {"restart_pod", "scale_deployment", "no_action"}
DESTRUCTIVE_ACTIONS = {"delete_resource", "delete_node"}

def check_risk(action, namespace, current_replicas=None, suggested_replicas=None):
    # Final safety decision deterministic Python rules se hota hai, LLM se nahi.
    if action not in ALLOWED_ACTIONS or action in DESTRUCTIVE_ACTIONS:
        return "high"
    if namespace == "production" and action == "scale_deployment":
        if current_replicas is not None and suggested_replicas is not None:
            if suggested_replicas < max(1, current_replicas // 2):
                return "high"
    return "low"
