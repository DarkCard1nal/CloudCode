from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Response

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])

SUCCESS_COUNT = Counter('http_requests_success', 'Number of successful requests', ['endpoint'])
FAILURE_COUNT = Counter('http_requests_failure', 'Number of failed requests', ['endpoint'])

REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request duration', ['endpoint'])

def get_metrics():
    """Exports metrics in Prometheus format."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)