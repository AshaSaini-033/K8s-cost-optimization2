def analyze_resources(cpu_percent, memory_percent=None, current_replicas=1):
    # Simple thresholds use kar rahe hain; ML/anomaly detection intentionally nahi hai.
    if cpu_percent is not None and cpu_percent > 80:
        return {"recommendation": "scale_up", "reason": "High CPU utilization"}
    if cpu_percent is not None and cpu_percent < 10 and current_replicas > 1:
        return {"recommendation": "scale_down", "reason": "Low CPU utilization"}
    return {"recommendation": "no_action", "reason": "Resource usage is within basic range"}
