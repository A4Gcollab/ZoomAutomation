from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Define metrics
recordings_processed = Counter('recordings_processed_total', 'Total recordings processed', ['status'])
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
api_latency = Histogram('api_latency_seconds', 'API request latency', ['endpoint'])
active_websockets = Gauge('active_websockets', 'Number of active WebSocket connections')
background_service_status = Gauge('background_service_status', 'Background service status (1=running, 0=stopped)')

def get_metrics():
    """Return Prometheus metrics"""
    return generate_latest()
