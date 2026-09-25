import requests
from kubernetes import client, config

PROM_URL = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/query"

def load_k8s_config():
    # Cluster ke andar in-cluster config, local testing ke liye kubeconfig.
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

def query_prometheus(query):
    try:
        response = requests.get(PROM_URL, params={"query": query}, timeout=5)
        response.raise_for_status()
        return response.json().get("data", {}).get("result", [])
    except Exception as exc:
        print(f"Error fetching metrics: {exc}")
        return []

def get_workload_metrics(namespace="default", deployment="busy-worker"):
    # Existing Prometheus logic ko reusable function bana rahe hain.
    load_k8s_config()
    obj = client.AppsV1Api().read_namespaced_deployment(deployment, namespace)
    replicas = obj.spec.replicas or 0
    query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod=~"{deployment}-.*",container!="POD"}}[5m]))'
    results = query_prometheus(query)
    cpu_percent = None
    if results:
        try:
            cpu_percent = round((float(results[0]["value"][1]) / max(replicas, 1)) * 100, 2)
        except (KeyError, ValueError, TypeError):
            pass
    return {"replicas": replicas, "cpu_percent": cpu_percent}

def get_idle_pods():
    # Existing optimizer behavior preserve kar rahe hain.
    return query_prometheus('avg(container_cpu_usage_seconds_total{namespace="default"}) by (pod) < 0.01')

def scale_down():
    idle_pods = get_idle_pods()
    if idle_pods:
        load_k8s_config()
        client.AppsV1Api().patch_namespaced_deployment_scale(
            "busy-worker", "default", {"spec": {"replicas": 1}})
        print("Optimization Successful: Scaled to 1 replica.")
    else:
        print("Cluster is already optimized.")

if __name__ == "__main__":
    scale_down()
