from typing import List, Dict
import statistics


class BenchmarkTelemetry:
    """
    Computes distribution metrics (p50, p90, p95, p99) for task latency and token throughput.
    """

    @staticmethod
    def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
        if not latencies:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        return {
            "p50": round(statistics.median(sorted_lat), 2),
            "p90": round(sorted_lat[int(n * 0.90)] if n > 1 else sorted_lat[-1], 2),
            "p95": round(sorted_lat[int(n * 0.95)] if n > 1 else sorted_lat[-1], 2),
            "p99": round(sorted_lat[int(n * 0.99)] if n > 1 else sorted_lat[-1], 2)
        }
