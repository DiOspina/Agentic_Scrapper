"""
Base agent class for all agents in the system.
"""
import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import structlog

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool

from app.core.config import settings
from app.models.agent_log import AgentType, LogLevel
from app.schemas.agent_log import AgentLogResponse

logger = structlog.get_logger(__name__)


class AgentState(str, Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentContext:
    """Context passed between agents in a pipeline."""
    execution_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result of an agent execution."""
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[AgentLogResponse] = field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.agent_type = agent_type
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.config = config or {}
        self.state = AgentState.IDLE
        self.logger = logger.bind(agent=self.name, agent_type=agent_type.value)
        self._execution_id: Optional[str] = None
        self._start_time: Optional[float] = None
        self._logs: List[AgentLogResponse] = []

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main logic."""
        pass

    async def initialize(self) -> None:
        """Initialize the agent."""
        self.state = AgentState.INITIALIZING
        self.logger.info("Initializing agent")
        await self._on_initialize()
        self.state = AgentState.IDLE
        self.logger.info("Agent initialized")

    async def _on_initialize(self) -> None:
        """Override for custom initialization logic."""
        pass

    async def run(self, context: AgentContext) -> AgentResult:
        """Run the agent with timing and error handling."""
        self._execution_id = context.execution_id
        self._start_time = time.time()
        self.state = AgentState.RUNNING

        self.log(LogLevel.INFO, f"Starting execution", step_name="start")

        try:
            result = await self.execute(context)
            duration_ms = int((time.time() - self._start_time) * 1000)
            result.duration_ms = duration_ms

            if result.success:
                self.state = AgentState.COMPLETED
                self.log(
                    LogLevel.INFO,
                    f"Execution completed successfully",
                    step_name="complete",
                    duration_ms=duration_ms,
                    tokens_used=result.tokens_used,
                    cost_usd=result.cost_usd,
                )
            else:
                self.state = AgentState.FAILED
                self.log(
                    LogLevel.ERROR,
                    f"Execution failed: {result.error}",
                    step_name="error",
                    duration_ms=duration_ms,
                )

            return result

        except Exception as e:
            duration_ms = int((time.time() - self._start_time) * 1000)
            self.state = AgentState.FAILED
            self.logger.exception("Execution failed with exception", error=str(e))
            self.log(LogLevel.CRITICAL, f"Execution failed: {str(e)}", step_name="exception", duration_ms=duration_ms)

            return AgentResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                logs=self._logs.copy(),
            )

    def log(
        self,
        level: LogLevel,
        message: str,
        step_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
    ) -> AgentLogResponse:
        """Create and store a log entry."""
        log_entry = AgentLogResponse(
            id=len(self._logs) + 1,
            execution_id=int(self._execution_id) if self._execution_id and self._execution_id.isdigit() else 0,
            agent_type=self.agent_type,
            level=level,
            message=message,
            details=details,
            step_name=step_name,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            created_at=__import__("datetime").datetime.utcnow(),
        )
        self._logs.append(log_entry)
        return log_entry

    def get_logs(self) -> List[AgentLogResponse]:
        """Get all logs from this execution."""
        return self._logs.copy()

    def clear_logs(self) -> None:
        """Clear logs for next execution."""
        self._logs.clear()

    async def call_llm(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AIMessage:
        """Call the LLM with the given messages."""
        if not self.llm:
            raise ValueError("No LLM configured for this agent")

        temp = temperature if temperature is not None else settings.AGENT_TEMPERATURE
        max_tok = max_tokens if max_tokens is not None else settings.AGENT_MAX_TOKENS

        self.log(LogLevel.DEBUG, f"Calling LLM", tool_name="llm", input_data={"messages_count": len(messages), "temperature": temp})

        start = time.time()
        response = await self.llm.ainvoke(messages, temperature=temp, max_tokens=max_tok)
        duration_ms = int((time.time() - start) * 1000)

        self.log(
            LogLevel.DEBUG,
            f"LLM response received",
            tool_name="llm",
            output_data={"content_length": len(response.content) if response.content else 0},
            duration_ms=duration_ms,
        )

        return response

    async def stream_llm(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response."""
        if not self.llm:
            raise ValueError("No LLM configured for this agent")

        temp = temperature if temperature is not None else settings.AGENT_TEMPERATURE
        max_tok = max_tokens if max_tokens is not None else settings.AGENT_MAX_TOKENS

        async for chunk in self.llm.astream(messages, temperature=temp, max_tokens=max_tok):
            if chunk.content:
                yield chunk.content


class AgentOrchestrator:
    """Orchestrates multiple agents in a pipeline."""

    def __init__(self, agents: List[BaseAgent]):
        self.agents = {agent.name: agent for agent in agents}
        self.logger = logger.bind(component="orchestrator")

    async def initialize_all(self) -> None:
        """Initialize all agents."""
        await asyncio.gather(*[agent.initialize() for agent in self.agents.values()])

    async def run_pipeline(
        self,
        context: AgentContext,
        agent_sequence: Optional[List[str]] = None,
    ) -> Dict[str, AgentResult]:
        """Run a sequence of agents."""
        sequence = agent_sequence or list(self.agents.keys())
        results = {}

        for agent_name in sequence:
            agent = self.agents.get(agent_name)
            if not agent:
                self.logger.warning(f"Agent not found: {agent_name}")
                continue

            self.logger.info(f"Running agent: {agent_name}")
            result = await agent.run(context)
            results[agent_name] = result

            # Merge output into context for next agent
            context.output_data.update(result.output_data)
            context.shared_memory[agent_name] = result.output_data

            if not result.success:
                self.logger.error(f"Agent {agent_name} failed, stopping pipeline", error=result.error)
                context.errors.append(f"{agent_name}: {result.error}")
                break

        return results

    async def run_parallel(
        self,
        context: AgentContext,
        agent_names: List[str],
    ) -> Dict[str, AgentResult]:
        """Run multiple agents in parallel."""
        tasks = []
        for agent_name in agent_names:
            agent = self.agents.get(agent_name)
            if agent:
                # Create a copy of context for each agent
                agent_context = AgentContext(
                    execution_id=context.execution_id,
                    input_data=context.input_data.copy(),
                    output_data={},
                    metadata=context.metadata.copy(),
                    shared_memory=context.shared_memory.copy(),
                )
                tasks.append(agent.run(agent_context))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for i, agent_name in enumerate(agent_names):
            if i < len(results_list):
                result = results_list[i]
                if isinstance(result, Exception):
                    results[agent_name] = AgentResult(success=False, error=str(result))
                else:
                    results[agent_name] = result
                    # Merge outputs
                    context.output_data.update(result.output_data)
                    context.shared_memory[agent_name] = result.output_data

        return results