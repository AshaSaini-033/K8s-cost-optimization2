from scripts.optimizer import get_workload_metrics

def analyze_cost(namespace="default", deployment="busy-worker"):
    # Existing Prometheus logic reuse kar rahe hain; duplicate optimizer nahi bana rahe.
    metrics = get_workload_metrics(namespace, deployment)
    replicas = metrics["replicas"]
    cpu = metrics.get("cpu_percent")
    if cpu is not None and cpu < 10 and replicas > 1:
        return {"recommendation": "scale_down", "reason": "Workload is underutilized",
                "current_replicas": replicas, "suggested_replicas": 1, "cpu_percent": cpu}
    return {"recommendation": "no_action", "reason": "No clear cost optimization opportunity",
            "current_replicas": replicas, "suggested_replicas": replicas, "cpu_percent": cpu}
