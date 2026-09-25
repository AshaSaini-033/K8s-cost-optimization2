import time
from kubernetes import client
from agents.health_agent import load_k8s_config

def restart_pod(namespace, pod_name):
    # Raw kubectl ya LLM command nahi; sirf predefined Kubernetes SDK action.
    load_k8s_config()
    client.CoreV1Api().delete_namespaced_pod(pod_name, namespace)
    return {"action": "restart_pod", "status": "requested", "pod": pod_name}

def scale_deployment(namespace, deployment, replicas):
    # Replica count validated Python se aata hai.
    load_k8s_config()
    client.AppsV1Api().patch_namespaced_deployment_scale(
        deployment, namespace, {"spec": {"replicas": int(replicas)}})
    return {"action": "scale_deployment", "status": "requested",
            "deployment": deployment, "replicas": int(replicas)}

def verify_pod(namespace, pod_name, wait_seconds=5):
    time.sleep(wait_seconds)
    load_k8s_config()
    pod = client.CoreV1Api().read_namespaced_pod(pod_name, namespace)
    return pod.status.phase == "Running"

def verify_deployment(namespace, deployment, expected_replicas):
    load_k8s_config()
    obj = client.AppsV1Api().read_namespaced_deployment_scale(deployment, namespace)
    return obj.spec.replicas == int(expected_replicas)
