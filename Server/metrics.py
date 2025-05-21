from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Response


class Metrics:
    def __init__(self):
        self.request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
        self.success_count = Counter('http_requests_success_total', 'Number of successful requests', ['method', 'endpoint'])
        self.failure_count = Counter('http_requests_failure_total', 'Number of failed requests', ['endpoint'])
        self.request_latency = Histogram('http_request_duration_seconds', 'HTTP request duration', ['endpoint'])

    def get_metrics(self):
        """Exports metrics in Prometheus format."""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
