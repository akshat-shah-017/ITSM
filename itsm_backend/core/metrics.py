"""
Metrics Collection - Phase 5B

In-memory metrics for monitoring:
- HTTP request latency (histogram for p95/p99)
- Request/error counters
- Cache hit/miss counters
- DB query duration (coarse-grained)

Thread-safe implementation using locks.
Optional Prometheus-compatible text export.
"""
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional
import logging

logger = logging.getLogger('core.metrics')


class MetricsRegistry:
    """
    Thread-safe in-memory metrics registry.
    
    Stores counters and histograms with labels.
    Can be exported in Prometheus text format.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize metrics storage."""
        self._counters: Dict[str, Dict[tuple, int]] = defaultdict(lambda: defaultdict(int))
        self._histograms: Dict[str, Dict[tuple, List[float]]] = defaultdict(lambda: defaultdict(list))
        self._counter_lock = threading.Lock()
        self._histogram_lock = threading.Lock()
        
        # Max samples per histogram (for memory bounds)
        self._max_histogram_samples = 10000
    
    def increment_counter(self, name: str, value: int = 1, **labels):
        """
        Increment a counter.
        
        Args:
            name: Metric name (e.g., 'http_requests_total')
            value: Amount to increment (default 1)
            **labels: Label key-value pairs
        """
        label_key = tuple(sorted(labels.items()))
        with self._counter_lock:
            self._counters[name][label_key] += value
    
    def observe_histogram(self, name: str, value: float, **labels):
        """
        Record a histogram observation.
        
        Args:
            name: Metric name (e.g., 'http_request_latency_seconds')
            value: Observed value
            **labels: Label key-value pairs
        """
        label_key = tuple(sorted(labels.items()))
        with self._histogram_lock:
            samples = self._histograms[name][label_key]
            samples.append(value)
            # Trim if too many samples (keep recent)
            if len(samples) > self._max_histogram_samples:
                self._histograms[name][label_key] = samples[-self._max_histogram_samples:]
    
    def get_counter(self, name: str, **labels) -> int:
        """Get counter value."""
        label_key = tuple(sorted(labels.items()))
        return self._counters[name].get(label_key, 0)
    
    def get_histogram_percentile(self, name: str, percentile: float, **labels) -> Optional[float]:
        """
        Get histogram percentile.
        
        Args:
            name: Metric name
            percentile: Percentile (0-100), e.g., 95 for p95
            **labels: Label key-value pairs
        
        Returns:
            Percentile value, or None if no samples
        """
        label_key = tuple(sorted(labels.items()))
        samples = self._histograms[name].get(label_key, [])
        if not samples:
            return None
        
        sorted_samples = sorted(samples)
        idx = int(len(sorted_samples) * percentile / 100)
        idx = min(idx, len(sorted_samples) - 1)
        return sorted_samples[idx]
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-compatible metrics text
        """
        lines = []
        
        # Export counters
        for name, label_values in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            for labels, value in label_values.items():
                label_str = self._format_labels(labels)
                lines.append(f"{name}{label_str} {value}")
        
        # Export histograms (as summary with percentiles)
        for name, label_values in self._histograms.items():
            lines.append(f"# TYPE {name} summary")
            for labels, samples in label_values.items():
                if not samples:
                    continue
                
                label_str = self._format_labels(labels)
                
                # Calculate percentiles
                sorted_samples = sorted(samples)
                for p in [50, 95, 99]:
                    idx = int(len(sorted_samples) * p / 100)
                    idx = min(idx, len(sorted_samples) - 1)
                    p_label = f'quantile="{p/100}"'
                    if label_str:
                        full_labels = f'{label_str[:-1]},{p_label}}}'
                    else:
                        full_labels = f'{{{p_label}}}'
                    lines.append(f"{name}{full_labels} {sorted_samples[idx]:.6f}")
                
                # Count and sum
                lines.append(f"{name}_count{label_str} {len(samples)}")
                lines.append(f"{name}_sum{label_str} {sum(samples):.6f}")
        
        return '\n'.join(lines)
    
    def _format_labels(self, labels: tuple) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ''
        parts = [f'{k}="{v}"' for k, v in labels]
        return '{' + ','.join(parts) + '}'
    
    def reset(self):
        """Reset all metrics (for testing)."""
        with self._counter_lock:
            self._counters.clear()
        with self._histogram_lock:
            self._histograms.clear()


# Global registry instance
metrics = MetricsRegistry()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def increment_request_counter(method: str, path: str, status: int):
    """Increment HTTP request counter."""
    metrics.increment_counter(
        'http_requests_total',
        method=method,
        path=_normalize_path(path),
        status=str(status)
    )


def increment_error_counter(method: str, path: str, error_class: str):
    """Increment HTTP error counter."""
    metrics.increment_counter(
        'http_errors_total',
        method=method,
        path=_normalize_path(path),
        error_class=error_class
    )


def observe_request_latency(method: str, path: str, status: int, latency_seconds: float):
    """Record HTTP request latency."""
    metrics.observe_histogram(
        'http_request_latency_seconds',
        latency_seconds,
        method=method,
        path=_normalize_path(path),
        status=str(status)
    )


def increment_cache_operation(operation: str, result: str):
    """
    Increment cache operation counter.
    
    Args:
        operation: 'get', 'set', 'delete'
        result: 'hit', 'miss', 'ok'
    """
    metrics.increment_counter(
        'cache_operations_total',
        operation=operation,
        result=result
    )


def observe_db_query_duration(operation: str, duration_seconds: float):
    """Record database query duration (coarse-grained)."""
    metrics.observe_histogram(
        'db_query_duration_seconds',
        duration_seconds,
        operation=operation
    )


def _normalize_path(path: str) -> str:
    """
    Normalize path for metrics labels.
    
    Replaces UUIDs and numeric IDs with placeholders to reduce label cardinality.
    """
    import re
    
    # Replace UUIDs
    path = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '{id}',
        path,
        flags=re.IGNORECASE
    )
    
    # Replace numeric IDs
    path = re.sub(r'/\d+(/|$)', r'/{id}\1', path)
    
    return path


class Timer:
    """
    Context manager for timing operations.
    
    Example:
        with Timer() as t:
            do_something()
        print(f"Took {t.elapsed_seconds}s")
    """
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.perf_counter()
    
    @property
    def elapsed_seconds(self) -> float:
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time
