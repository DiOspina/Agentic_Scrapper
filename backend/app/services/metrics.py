"""
Metrics Service for collecting and exposing system metrics.
"""
import time
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
from functools import wraps

from app.db.database import get_db
from app.models.metric import Metric, MetricType
from app.models.execution import Execution, ExecutionStatus
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


# Prometheus metrics
REQUEST_COUNT = Counter(
    "agenttic_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "agenttic_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

EXECUTION_COUNT = Counter(
    "agenttic_executions_total",
    "Total executions",
    ["type", "status"],
)

EXECUTION_DURATION = Histogram(
    "agenttic_execution_duration_seconds",
    "Execution duration",
    ["type"],
)

AGENT_DURATION = Histogram(
    "agenttic_agent_duration_seconds",
    "Agent execution duration",
    ["agent"],
)

ACTIVE_EXECUTIONS = Gauge(
    "agenttic_active_executions",
    "Currently active executions",
)

AGENT_TOKENS = Counter(
    "agenttic_agent_tokens_total",
    "Total tokens used by agents",
    ["agent"],
)

AGENT_COST = Counter(
    "agenttic_agent_cost_usd_total",
    "Total cost in USD",
    ["agent"],
)

VECTOR_STORE_OPERATIONS = Counter(
    "agenttic_vector_store_operations_total",
    "Vector store operations",
    ["operation", "status"],
)

DOCUMENT_PROCESSED = Counter(
    "agenttic_documents_processed_total",
    "Documents processed",
    ["type", "status"],
)

SYSTEM_CPU = Gauge(
    "agenttic_system_cpu_percent",
    "System CPU usage",
)

SYSTEM_MEMORY = Gauge(
    "agenttic_system_memory_percent",
    "System memory usage",
)

SYSTEM_DISK = Gauge(
    "agenttic_system_disk_percent",
    "System disk usage",
)


@dataclass
class MetricCollector:
    """Collects and aggregates metrics."""
    execution_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    execution_durations: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    agent_durations: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    agent_tokens: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    agent_costs: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class MetricsService:
    """Service for collecting and exposing metrics."""

    def __init__(self):
        self.collector = MetricCollector()
        self._start_time = time.time()

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    def record_execution(self, execution_type: str, status: str, duration: float):
        """Record execution metrics."""
        EXECUTION_COUNT.labels(type=execution_type, status=status).inc()
        EXECUTION_DURATION.labels(type=execution_type).observe(duration)
        self.collector.execution_counts[f"{execution_type}:{status}"] += 1
        self.collector.execution_durations[execution_type].append(duration)

    def record_agent(self, agent: str, duration: float, tokens: int = 0, cost: float = 0.0):
        """Record agent metrics."""
        AGENT_DURATION.labels(agent=agent).observe(duration)
        if tokens:
            AGENT_TOKENS.labels(agent=agent).inc(tokens)
            self.collector.agent_tokens[agent] += tokens
        if cost:
            AGENT_COST.labels(agent=agent).inc(cost)
            self.collector.agent_costs[agent] += cost
        self.collector.agent_durations[agent].append(duration)

    def record_vector_operation(self, operation: str, success: bool):
        """Record vector store operation."""
        VECTOR_STORE_OPERATIONS.labels(
            operation=operation,
            status="success" if success else "failure"
        ).inc()

    def record_document(self, doc_type: str, success: bool):
        """Record document processing."""
        DOCUMENT_PROCESSED.labels(
            type=doc_type,
            status="success" if success else "failure"
        ).inc()

    def increment_active_executions(self):
        """Increment active executions gauge."""
        ACTIVE_EXECUTIONS.inc()

    def decrement_active_executions(self):
        """Decrement active executions gauge."""
        ACTIVE_EXECUTIONS.dec()

    def record_error(self, error_type: str):
        """Record error."""
        self.collector.errors[error_type] += 1

    def update_system_metrics(self):
        """Update system metrics."""
        SYSTEM_CPU.set(psutil.cpu_percent(interval=0.1))
        SYSTEM_MEMORY.set(psutil.virtual_memory().percent)
        SYSTEM_DISK.set(psutil.disk_usage("/").percent)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime = time.time() - self._start_time

        return {
            "uptime_seconds": uptime,
            "executions": {
                "total": sum(self.collector.execution_counts.values()),
                "by_type_status": dict(self.collector.execution_counts),
                "avg_duration_by_type": {
                    k: sum(v) / len(v) if v else 0
                    for k, v in self.collector.execution_durations.items()
                },
            },
            "agents": {
                "avg_duration_by_agent": {
                    k: sum(v) / len(v) if v else 0
                    for k, v in self.collector.agent_durations.items()
                },
                "total_tokens": dict(self.collector.agent_tokens),
                "total_cost_usd": dict(self.collector.agent_costs),
            },
            "errors": dict(self.collector.errors),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            },
        }

    def get_prometheus_metrics(self) -> bytes:
        """Get Prometheus metrics output."""
        return generate_latest()


# Global metrics service instance
_metrics_service = None


def get_metrics_service() -> MetricsService:
    """Get or create metrics service."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service


def track_execution(execution_type: str):
    """Decorator to track execution metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_service()
            metrics.increment_active_executions()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                metrics.record_execution(execution_type, "success", duration)
                return result
            except Exception as e:
                duration = time.time() - start
                metrics.record_execution(execution_type, "failure", duration)
                metrics.record_error(type(e).__name__)
                raise
            finally:
                metrics.decrement_active_executions()
        return wrapper
    return decorator


def track_agent(agent_name: str):
    """Decorator to track agent metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_service()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                tokens = getattr(result, "tokens_used", 0) if hasattr(result, "tokens_used") else 0
                cost = getattr(result, "cost_usd", 0.0) if hasattr(result, "cost_usd") else 0.0
                metrics.record_agent(agent_name, duration, tokens, cost)
                return result
            except Exception as e:
                duration = time.time() - start
                metrics.record_agent(agent_name, duration)
                metrics.record_error(f"{agent_name}:{type(e).__name__}")
                raise
        return wrapper
    return decorator


async def persist_metrics_to_db(
    execution_id: int,
    metrics: Dict[str, float],
    agent_type: Optional[str] = None,
    step_name: Optional[str] = None,
) -> None:
    """Persist metrics to database."""
    async for db in get_db():
        for name, value in metrics.items():
            metric = Metric(
                execution_id=execution_id,
                name=name,
                metric_type=MetricType.PERFORMANCE,
                value=value,
                agent_type=agent_type,
                step_name=step_name,
            )
            db.add(metric)
        await db.commit()


async def get_execution_stats(
    db: AsyncSession,
    days: int = 7,
) -> Dict[str, Any]:
    """Get execution statistics from database."""
    since = datetime.utcnow() - timedelta(days=days)

    # Total executions
    total_result = await db.execute(
        select(func.count(Execution.id)).where(Execution.created_at >= since)
    )
    total = total_result.scalar()

    # By status
    status_result = await db.execute(
        select(Execution.status, func.count(Execution.id))
        .where(Execution.created_at >= since)
        .group_by(Execution.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    # By type
    type_result = await db.execute(
        select(Execution.execution_type, func.count(Execution.id))
        .where(Execution.created_at >= since)
        .group_by(Execution.execution_type)
    )
    by_type = {row[0].value: row[1] for row in type_result.all()}

    # Avg duration
    duration_result = await db.execute(
        select(func.avg(Execution.duration_seconds))
        .where(Execution.created_at >= since, Execution.duration_seconds.isnot(None))
    )
    avg_duration = duration_result.scalar()

    # Success rate
    completed = by_status.get("completed", 0)
    failed = by_status.get("failed", 0)
    total_finished = completed + failed
    success_rate = completed / total_finished if total_finished > 0 else 0

    return {
        "period_days": days,
        "total_executions": total,
        "by_status": by_status,
        "by_type": by_type,
        "avg_duration_seconds": avg_duration,
        "success_rate": success_rate,
    }