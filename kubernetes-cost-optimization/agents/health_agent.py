from kubernetes import client, config

def load_k8s_config():
    # Cluster ke andar in-cluster config, local testing ke liye kubeconfig.
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

def detect_health_issues(namespace="default", restart_threshold=3):
    # Failed/CrashLoopBackOff/repeated restart ko simple incident mein convert kar rahe hain.
    load_k8s_config()
    pods = client.CoreV1Api().list_namespaced_pod(namespace)
    incidents = []
    for pod in pods.items:
        statuses = pod.status.container_statuses or []
        restarts = sum((c.restart_count or 0) for c in statuses)
        waiting = [c.state.waiting.reason for c in statuses
                   if c.state and c.state.waiting and c.state.waiting.reason]
        problem = None
        if pod.status.phase == "Failed":
            problem = "Failed"
        elif "CrashLoopBackOff" in waiting:
            problem = "CrashLoopBackOff"
        elif restarts >= restart_threshold:
            problem = "ExcessiveRestarts"
        if problem:
            incidents.append({"problem": problem, "namespace": namespace,
                              "pod": pod.metadata.name, "severity": "medium",
                              "restart_count": restarts})
    return incidents

def get_pod_status(namespace, pod_name):
    # Yeh sirf read tool hai; LLM ko direct cluster access nahi milta.
    load_k8s_config()
    pod = client.CoreV1Api().read_namespaced_pod(pod_name, namespace)
    return {"phase": pod.status.phase, "pod": pod_name, "namespace": namespace}

def get_recent_events(namespace="default", limit=10):
    # Recent events failure ka basic context dene mein useful hain.
    load_k8s_config()
    events = client.CoreV1Api().list_namespaced_event(namespace).items
    events = sorted(events, key=lambda e: e.metadata.creation_timestamp or 0, reverse=True)
    return [{"reason": e.reason, "message": e.message, "type": e.type} for e in events[:limit]]
