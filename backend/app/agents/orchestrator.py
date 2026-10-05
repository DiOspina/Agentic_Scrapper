"""
Main Orchestrator Agent using LangGraph for multi-agent workflow coordination.
"""
import uuid
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool

from app.agents.base import BaseAgent, AgentContext, AgentResult, AgentOrchestrator
from app.agents.scraper import ScraperAgent, ScrapingConfig
from app.agents.analyst import AnalystAgent, AnalysisConfig, AnalysisType
from app.agents.synthesizer import SynthesizerAgent, ReportConfig, ReportType, ReportFormat
from app.models.agent_log import AgentType, LogLevel
from app.core.config import settings
from app.services.llm import get_llm
from app.db.database import get_db
from app.models.execution import Execution, ExecutionStatus, ExecutionType
from app.models.agent_log import AgentLog
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger(__name__)


class PipelineStage(str, Enum):
    SCRAPING = "scraping"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    NOTIFICATION = "notification"
    COMPLETE = "complete"


class OrchestratorState(TypedDict):
    """State for the LangGraph orchestrator."""
    execution_id: str
    workflow_id: Optional[int]
    input_data: Dict[str, Any]
    current_stage: PipelineStage
    stages_completed: List[PipelineStage]
    scraped_data: Dict[str, Any]
    analysis_results: List[Dict[str, Any]]
    query_results: List[Dict[str, Any]]
    report: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any]


@dataclass
class PipelineConfig:
    """Configuration for the full pipeline."""
    enabled_stages: List[PipelineStage] = field(default_factory=lambda: [
        PipelineStage.SCRAPING,
        PipelineStage.ANALYSIS,
        PipelineStage.SYNTHESIS,
    ])
    scraping_config: Optional[ScrapingConfig] = None
    analysis_config: Optional[AnalysisConfig] = None
    report_config: Optional[ReportConfig] = None
    notification_channels: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout_seconds: int = 300


class OrchestratorAgent:
    """Main orchestrator that coordinates all agents via LangGraph."""

    def __init__(
        self,
        llm=None,
        config: Optional[PipelineConfig] = None,
    ):
        self.config = config or PipelineConfig()
        self.llm = llm or get_llm()
        self.graph = self._build_graph()
        self.logger = logger.bind(component="orchestrator")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_state)
        workflow.add_node("scraping", self._run_scraping)
        workflow.add_node("analysis", self._run_analysis)
        workflow.add_node("synthesis", self._run_synthesis)
        workflow.add_node("notification", self._send_notifications)
        workflow.add_node("finalize", self._finalize_execution)

        # Add edges
        workflow.set_entry_point("initialize")

        workflow.add_conditional_edges(
            "initialize",
            self._should_run_scraping,
            {
                "scraping": "scraping",
                "analysis": "analysis",
                "synthesis": "synthesis",
                "finalize": "finalize",
            },
        )

        workflow.add_conditional_edges(
            "scraping",
            self._after_scraping,
            {
                "analysis": "analysis",
                "synthesis": "synthesis",
                "finalize": "finalize",
                "error": "finalize",
            },
        )

        workflow.add_conditional_edges(
            "analysis",
            self._after_analysis,
            {
                "synthesis": "synthesis",
                "finalize": "finalize",
                "error": "finalize",
            },
        )

        workflow.add_conditional_edges(
            "synthesis",
            self._after_synthesis,
            {
                "notification": "notification",
                "finalize": "finalize",
            },
        )

        workflow.add_edge("notification", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _initialize_state(self, state: OrchestratorState) -> OrchestratorState:
        """Initialize the pipeline state."""
        self.logger.info("Initializing pipeline", execution_id=state["execution_id"])

        return {
            **state,
            "current_stage": PipelineStage.SCRAPING,
            "stages_completed": [],
            "scraped_data": {},
            "analysis_results": [],
            "query_results": [],
            "report": {},
            "errors": [],
            "metadata": {
                "started_at": datetime.utcnow().isoformat(),
                "pipeline_config": self.config.__dict__,
            },
        }

    def _should_run_scraping(self, state: OrchestratorState) -> str:
        """Determine next stage after initialization."""
        if PipelineStage.SCRAPING in self.config.enabled_stages:
            urls = state["input_data"].get("urls", [])
            if urls:
                return "scraping"

        if PipelineStage.ANALYSIS in self.config.enabled_stages:
            return "analysis"

        if PipelineStage.SYNTHESIS in self.config.enabled_stages:
            return "synthesis"

        return "finalize"

    async def _run_scraping(self, state: OrchestratorState) -> OrchestratorState:
        """Run the scraping agent."""
        self.logger.info("Running scraping stage", execution_id=state["execution_id"])

        scraper = ScraperAgent(
            llm=self.llm,
            scraping_config=self.config.scraping_config,
        )
        await scraper.initialize()

        context = AgentContext(
            execution_id=state["execution_id"],
            input_data={
                "urls": state["input_data"].get("urls", []),
                "config": state["input_data"].get("scraping_config", {}),
            },
        )

        result = await scraper.run(context)

        new_state = {
            **state,
            "current_stage": PipelineStage.ANALYSIS,
            "stages_completed": state["stages_completed"] + [PipelineStage.SCRAPING],
            "scraped_data": result.output_data,
            "errors": state["errors"] + ([] if result.success else [result.error or "Scraping failed"]),
        }

        await scraper.close()
        return new_state

    def _after_scraping(self, state: OrchestratorState) -> str:
        """Determine next stage after scraping."""
        if state["errors"] and "Scraping failed" in str(state["errors"]):
            return "error"

        if PipelineStage.ANALYSIS in self.config.enabled_stages:
            return "analysis"

        if PipelineStage.SYNTHESIS in self.config.enabled_stages:
            return "synthesis"

        return "finalize"

    async def _run_analysis(self, state: OrchestratorState) -> OrchestratorState:
        """Run the analysis agent."""
        self.logger.info("Running analysis stage", execution_id=state["execution_id"])

        analyst = AnalystAgent(
            llm=self.llm,
            analysis_config=self.config.analysis_config,
        )
        await analyst.initialize()

        # Prepare documents from scraped data
        documents = self._prepare_documents_from_scraped(state["scraped_data"])

        context = AgentContext(
            execution_id=state["execution_id"],
            input_data={
                "documents": documents,
                "queries": state["input_data"].get("queries", []),
                "analysis_types": [t.value for t in (self.config.analysis_config.analysis_types if self.config.analysis_config else [])],
                "document_ids": state["input_data"].get("document_ids", []),
            },
        )

        result = await analyst.run(context)

        new_state = {
            **state,
            "current_stage": PipelineStage.SYNTHESIS,
            "stages_completed": state["stages_completed"] + [PipelineStage.ANALYSIS],
            "analysis_results": result.output_data.get("analyses", []),
            "query_results": result.output_data.get("query_results", []),
            "errors": state["errors"] + ([] if result.success else [result.error or "Analysis failed"]),
        }

        return new_state

    def _after_analysis(self, state: OrchestratorState) -> str:
        """Determine next stage after analysis."""
        if state["errors"] and "Analysis failed" in str(state["errors"]):
            return "error"

        if PipelineStage.SYNTHESIS in self.config.enabled_stages:
            return "synthesis"

        return "finalize"

    async def _run_synthesis(self, state: OrchestratorState) -> OrchestratorState:
        """Run the synthesis agent."""
        self.logger.info("Running synthesis stage", execution_id=state["execution_id"])

        synthesizer = SynthesizerAgent(
            llm=self.llm,
            report_config=self.config.report_config,
        )
        await synthesizer.initialize()

        context = AgentContext(
            execution_id=state["execution_id"],
            input_data={
                "analysis_results": state["analysis_results"],
                "scraped_data": state["scraped_data"],
                "query_results": state["query_results"],
                "metrics": {},
                "report_config": self.config.report_config.__dict__ if self.config.report_config else {},
                "execution_ids": [state["execution_id"]],
            },
        )

        result = await synthesizer.run(context)

        new_state = {
            **state,
            "current_stage": PipelineStage.NOTIFICATION,
            "stages_completed": state["stages_completed"] + [PipelineStage.SYNTHESIS],
            "report": result.output_data,
            "errors": state["errors"] + ([] if result.success else [result.error or "Synthesis failed"]),
        }

        return new_state

    def _after_synthesis(self, state: OrchestratorState) -> str:
        """Determine next stage after synthesis."""
        if self.config.notification_channels:
            return "notification"
        return "finalize"

    async def _send_notifications(self, state: OrchestratorState) -> OrchestratorState:
        """Send notifications via n8n webhooks."""
        self.logger.info("Sending notifications", execution_id=state["execution_id"])

        # This would integrate with n8n
        # For now, just log
        for channel in self.config.notification_channels:
            self.logger.info(f"Notification sent via {channel}", execution_id=state["execution_id"])

        return {
            **state,
            "current_stage": PipelineStage.COMPLETE,
            "stages_completed": state["stages_completed"] + [PipelineStage.NOTIFICATION],
        }

    async def _finalize_execution(self, state: OrchestratorState) -> OrchestratorState:
        """Finalize the execution and update database."""
        self.logger.info("Finalizing execution", execution_id=state["execution_id"])

        # Update execution in database
        await self._update_execution_in_db(state)

        return {
            **state,
            "current_stage": PipelineStage.COMPLETE,
            "metadata": {
                **state["metadata"],
                "completed_at": datetime.utcnow().isoformat(),
                "success": len(state["errors"]) == 0,
            },
        }

    def _prepare_documents_from_scraped(self, scraped_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert scraped pages to document format for analysis."""
        documents = []
        pages = scraped_data.get("pages", [])

        for page in pages:
            documents.append({
                "document_id": f"scraped_{hash(page['url'])}",
                "content": page.get("content", ""),
                "metadata": {
                    "source": "scraper",
                    "url": page.get("url"),
                    "title": page.get("title"),
                    "scraped_at": page.get("timestamp"),
                    **page.get("metadata", {}),
                },
            })

        return documents

    async def _update_execution_in_db(self, state: OrchestratorState) -> None:
        """Update execution record in database."""
        try:
            async for db in get_db():
                from sqlalchemy import select
                from app.models.execution import Execution, ExecutionStatus

                result = await db.execute(
                    select(Execution).where(Execution.execution_id == state["execution_id"])
                )
                execution = result.scalar_one_or_none()

                if execution:
                    execution.status = ExecutionStatus.COMPLETED if not state["errors"] else ExecutionStatus.FAILED
                    execution.output_data = {
                        "scraped_data": state["scraped_data"],
                        "analysis_results": state["analysis_results"],
                        "query_results": state["query_results"],
                        "report": state["report"],
                    }
                    execution.error_message = "; ".join(state["errors"]) if state["errors"] else None
                    execution.completed_at = datetime.utcnow()

                    if execution.started_at:
                        execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()

                    await db.commit()

        except Exception as e:
            self.logger.error("Failed to update execution in DB", error=str(e))

    async def run_pipeline(
        self,
        execution_id: str,
        input_data: Dict[str, Any],
        workflow_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run the complete pipeline."""
        initial_state: OrchestratorState = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "input_data": input_data,
            "current_stage": PipelineStage.SCRAPING,
            "stages_completed": [],
            "scraped_data": {},
            "analysis_results": [],
            "query_results": [],
            "report": {},
            "errors": [],
            "metadata": {},
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        return {
            "success": len(final_state["errors"]) == 0,
            "execution_id": execution_id,
            "stages_completed": [s.value for s in final_state["stages_completed"]],
            "scraped_data": final_state["scraped_data"],
            "analysis_results": final_state["analysis_results"],
            "query_results": final_state["query_results"],
            "report": final_state["report"],
            "errors": final_state["errors"],
            "metadata": final_state["metadata"],
        }


class SimpleOrchestrator:
    """Simple orchestrator without LangGraph for simpler use cases."""

    def __init__(
        self,
        llm=None,
        config: Optional[PipelineConfig] = None,
    ):
        self.config = config or PipelineConfig()
        self.llm = llm or get_llm()
        self.agent_orchestrator = AgentOrchestrator([])

    async def run(
        self,
        execution_id: str,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        """Run a simple sequential pipeline."""
        # Initialize agents
        scraper = ScraperAgent(llm=self.llm, scraping_config=self.config.scraping_config)
        analyst = AnalystAgent(llm=self.llm, analysis_config=self.config.analysis_config)
        synthesizer = SynthesizerAgent(llm=self.llm, report_config=self.config.report_config)

        await scraper.initialize()
        await analyst.initialize()
        await synthesizer.initialize()

        self.agent_orchestrator = AgentOrchestrator([scraper, analyst, synthesizer])

        context = AgentContext(execution_id=execution_id, input_data=input_data)

        # Run pipeline
        results = await self.agent_orchestrator.run_pipeline(
            context,
            agent_sequence=["scraper", "analyst", "synthesizer"],
        )

        # Combine results
        final_output = {}
        for agent_name, result in results.items():
            final_output[f"{agent_name}_result"] = result.output_data
            if not result.success:
                final_output["error"] = result.error

        # Cleanup
        await scraper.close()

        return AgentResult(
            success=all(r.success for r in results.values()),
            output_data=final_output,
            error="; ".join([r.error for r in results.values() if r.error]),
        )