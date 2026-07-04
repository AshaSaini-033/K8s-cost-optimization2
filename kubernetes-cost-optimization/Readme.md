# 💰 Kubernetes Cost Optimizer (FinOps Automation)

This project automates resource management in a Kubernetes cluster to reduce cloud bills by identifying and scaling down idle workloads.

## 🚀 How it works
1. **Metrics:** Prometheus collects CPU/RAM usage data.
2. **Analysis:** Python script queries Prometheus API to find pods with <1% utilization.
3. **Action:** Script uses K8s Python SDK and RBAC to scale deployments down to minimum replicas.
4. **Scheduling:** K8s CronJobs handle off-hour shutdowns for non-production namespaces.

## 📈 Impact
- **Simulated Savings:** ~50% reduction in resource footprint.
- **Resolution:** Fixed "Disk Pressure" and "Pending Pod" errors via dynamic reclaiming.

## 🛠️ Tech Stack
- **Cloud:** AWS (EC2, EBS)
- **Orchestration:** Kubernetes (Minikube)
- **Monitoring:** Prometheus, Grafana
- **Logic:** Python (Kubernetes-client, Requests)

commands:


### 1. Infrastructure Setup (EC2 & Minikube)
```bash
# Start Minikube with Docker driver
minikube start --driver=docker --memory=3000 --cpus=2

# Check Node status
kubectl get nodes
# Deploy the 3-replica busy-worker app
kubectl apply -f manifests/demo-app.yaml

# Verify pods are running (one might be pending due to resources)
kubectl get pods
# Add Helm repo and install monitoring stack
helm repo add prometheus-community [https://prometheus-community.github.io/helm-charts](https://prometheus-community.github.io/helm-charts)
helm repo update
kubectl create namespace monitoring
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring

# Access Grafana (Run in separate terminal)
kubectl port-forward --address 0.0.0.0 -n monitoring service/prometheus-grafana 3000:80

# Get Grafana Admin Password
kubectl get secret --namespace monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
# Apply Permissions
kubectl apply -f manifests/rbac.yaml

# Install Python dependencies
pip3 install kubernetes requests

# Run the Optimizer
python3 scripts/optimizer.py
# Deploy the Nightly CronJob
kubectl apply -f manifests/nightly-shutdown.yaml