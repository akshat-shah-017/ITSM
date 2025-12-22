"""
Metrics Views - Phase 5B

Exposes Prometheus-compatible metrics endpoint.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from core.metrics import metrics


class MetricsView(APIView):
    """
    GET /metrics/
    
    Returns metrics in Prometheus text format.
    
    Unauthenticated access allowed for monitoring scraping.
    Consider restricting to internal network in production.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Export metrics in Prometheus format
        metrics_text = metrics.export_prometheus()
        
        return HttpResponse(
            metrics_text,
            content_type='text/plain; charset=utf-8'
        )
