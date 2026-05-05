"""Performance Metrics: measure page load time, response time during tests."""

import time
from datetime import datetime
from utils.logger import log


class PerformanceMonitor:
    """Collects performance metrics during test execution."""

    def __init__(self):
        self.metrics = []
        self._current_step = None
        self._step_start = None

    def start_step(self, step_id: str, action: str):
        """Mark the start of a step for timing."""
        self._current_step = step_id
        self._step_start = time.perf_counter()

    def end_step(self, step_id: str, success: bool = True):
        """Mark the end of a step and record timing."""
        if self._step_start is None:
            return
        elapsed_ms = (time.perf_counter() - self._step_start) * 1000
        self.metrics.append({
            "step_id": step_id,
            "duration_ms": round(elapsed_ms, 2),
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })
        self._step_start = None

    def measure_page_load(self, page, url: str = "") -> dict:
        """Measure page load performance metrics using Navigation Timing API."""
        try:
            timing = page.evaluate("""() => {
                const perf = performance.getEntriesByType('navigation')[0];
                if (!perf) return null;
                return {
                    dns: Math.round(perf.domainLookupEnd - perf.domainLookupStart),
                    tcp: Math.round(perf.connectEnd - perf.connectStart),
                    ttfb: Math.round(perf.responseStart - perf.requestStart),
                    download: Math.round(perf.responseEnd - perf.responseStart),
                    dom_interactive: Math.round(perf.domInteractive - perf.navigationStart),
                    dom_complete: Math.round(perf.domComplete - perf.navigationStart),
                    load_event: Math.round(perf.loadEventEnd - perf.navigationStart),
                    total: Math.round(perf.loadEventEnd - perf.navigationStart)
                };
            }""")

            if timing:
                timing["url"] = url or page.url
                timing["timestamp"] = datetime.now().isoformat()
                self.metrics.append({
                    "type": "page_load",
                    "url": timing["url"],
                    **timing,
                })
                log.info(
                    f"[Perf] Page load: {timing['url']} | "
                    f"TTFB={timing['ttfb']}ms | "
                    f"DOM={timing['dom_complete']}ms | "
                    f"Total={timing['total']}ms"
                )
                return timing
        except Exception as e:
            log.warning(f"Khong the do performance: {e}")

        return {}

    def measure_resource_count(self, page) -> dict:
        """Count and categorize loaded resources."""
        try:
            resources = page.evaluate("""() => {
                const entries = performance.getEntriesByType('resource');
                const summary = {total: entries.length, by_type: {}};
                entries.forEach(e => {
                    const type = e.initiatorType || 'other';
                    summary.by_type[type] = (summary.by_type[type] || 0) + 1;
                });
                summary.total_size_kb = Math.round(
                    entries.reduce((s, e) => s + (e.transferSize || 0), 0) / 1024
                );
                return summary;
            }""")
            if resources:
                log.info(
                    f"[Perf] Resources: {resources['total']} total, "
                    f"{resources['total_size_kb']}KB transferred"
                )
            return resources or {}
        except Exception:
            return {}

    def get_summary(self) -> dict:
        """Get a summary of all collected metrics."""
        step_metrics = [m for m in self.metrics if "type" not in m]
        page_loads = [m for m in self.metrics if m.get("type") == "page_load"]

        total_steps = len(step_metrics)
        avg_step_time = sum(m["duration_ms"] for m in step_metrics) / total_steps if total_steps else 0
        slowest_step = max(step_metrics, key=lambda m: m["duration_ms"]) if step_metrics else None

        return {
            "total_steps_measured": total_steps,
            "avg_step_duration_ms": round(avg_step_time, 2),
            "slowest_step": slowest_step,
            "page_loads": page_loads,
            "all_metrics": self.metrics,
        }

    def reset(self):
        """Clear all collected metrics."""
        self.metrics = []
        self._current_step = None
        self._step_start = None
