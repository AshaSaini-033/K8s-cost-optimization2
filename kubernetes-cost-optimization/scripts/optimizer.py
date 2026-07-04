import requests
from kubernetes import client, config

# Load K8s Config
config.load_kube_config()
apps_v1 = client.AppsV1Api()

# Internal Prometheus URL
PROM_URL = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/query"

def get_idle_pods():
    # Query for pods using less than 1% CPU
    query = 'avg(container_cpu_usage_seconds_total{namespace="default"}) by (pod) < 0.01'
    try:
        response = requests.get(PROM_URL, params={'query': query})
        return response.json()['data']['result']
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return []

def scale_down():
    idle_pods = get_idle_pods()
    if idle_pods:
        print(f"Detected {len(idle_pods)} idle workloads. Scaling down...")
        body = {'spec': {'replicas': 1}}
        apps_v1.patch_namespaced_deployment_scale("busy-worker", "default", body)
        print("Optimization Successful: Scaled to 1 replica.")
    else:
        print("Cluster is already optimized.")

if __name__ == "__main__":
    scale_down()