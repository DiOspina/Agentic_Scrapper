"""
Agent endpoints for direct agent interaction.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.agents.scraper import ScraperAgent, ScrapingConfig
from app.agents.analyst import AnalystAgent, AnalysisConfig, AnalysisType
from app.agents.synthesizer import SynthesizerAgent, ReportConfig, ReportType, ReportFormat
from app.services.llm import get_llm
from app.services.metrics import get_metrics_service, track_agent
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class ScrapeRequest(BaseModel):
    urls: List[str]
    config: Optional[Dict[str, Any]] = None


class AnalyzeRequest(BaseModel):
    documents: List[Dict[str, Any]]
    queries: Optional[List[str]] = None
    analysis_types: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None


class SynthesizeRequest(BaseModel):
    analysis_results: List[Dict[str, Any]]
    scraped_data: Optional[Dict[str, Any]] = None
    query_results: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    report_config: Optional[Dict[str, Any]] = None


@router.post("/scrape")
@track_agent("scraper")
async def scrape(request: ScrapeRequest):
    """Run scraper agent directly."""
    llm = get_llm()

    scraping_config = ScrapingConfig(**(request.config or {}))
    scraper = ScraperAgent(llm=llm, scraping_config=scraping_config)
    await scraper.initialize()

    try:
        from app.agents.base import AgentContext
        context = AgentContext(
            execution_id="api_scrape_" + __import__("uuid").uuid4().hex[:8],
            input_data={"urls": request.urls, "config": request.config or {}},
        )

        result = await scraper.run(context)
        await scraper.close()

        get_metrics_service().record_agent("scraper", result.duration_ms / 1000, result.tokens_used, result.cost_usd)

        return {
            "success": result.success,
            "data": result.output_data,
            "error": result.error,
            "metrics": result.metrics,
            "logs": [log.model_dump() for log in result.logs],
        }

    except Exception as e:
        await scraper.close()
        logger.error("Scrape failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
@track_agent("analyst")
async def analyze(request: AnalyzeRequest):
    """Run analyst agent directly."""
    llm = get_llm()

    analysis_config = AnalysisConfig()
    if request.analysis_types:
        analysis_config.analysis_types = [AnalysisType(t) for t in request.analysis_types if t in AnalysisType.__members__]

    analyst = AnalystAgent(llm=llm, analysis_config=analysis_config)
    await analyst.initialize()

    try:
        from app.agents.base import AgentContext
        context = AgentContext(
            execution_id="api_analyze_" + __import__("uuid").uuid4().hex[:8],
            input_data={
                "documents": request.documents,
                "queries": request.queries or [],
                "analysis_types": request.analysis_types or [],
                "document_ids": request.document_ids or [],
            },
        )

        result = await analyst.run(context)
        # Note: analyst doesn't have close method currently

        get_metrics_service().record_agent("analyst", result.duration_ms / 1000, result.tokens_used, result.cost_usd)

        return {
            "success": result.success,
            "data": result.output_data,
            "error": result.error,
            "metrics": result.metrics,
            "logs": [log.model_dump() for log in result.logs],
        }

    except Exception as e:
        logger.error("Analyze failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
@track_agent("synthesizer")
async def synthesize(request: SynthesizeRequest):
    """Run synthesizer agent directly."""
    llm = get_llm()

    report_config = ReportConfig(**(request.report_config or {}))
    synthesizer = SynthesizerAgent(llm=llm, report_config=report_config)
    await synthesizer.initialize()

    try:
        from app.agents.base import AgentContext
        context = AgentContext(
            execution_id="api_synthesize_" + __import__("uuid").uuid4().hex[:8],
            input_data={
                "analysis_results": request.analysis_results,
                "scraped_data": request.scraped_data or {},
                "query_results": request.query_results or [],
                "metrics": request.metrics or {},
                "report_config": request.report_config or {},
            },
        )

        result = await synthesizer.run(context)

        get_metrics_service().record_agent("synthesizer", result.duration_ms / 1000, result.tokens_used, result.cost_usd)

        return {
            "success": result.success,
            "data": result.output_data,
            "error": result.error,
            "metrics": result.metrics,
            "logs": [log.model_dump() for log in result.logs],
        }

    except Exception as e:
        logger.error("Synthesize failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agents_status():
    """Get status of all agents."""
    return {
        "agents": [
            {
                "name": "scraper",
                "type": "scraper",
                "status": "available",
                "capabilities": [
                    "dynamic_scraping",
                    "javascript_rendering",
                    "structured_extraction",
                    "table_extraction",
                    "link_crawling",
                ],
            },
            {
                "name": "analyst",
                "type": "analyst",
                "status": "available",
                "capabilities": [
                    "summarization",
                    "key_metrics_extraction",
                    "pattern_detection",
                    "sentiment_analysis",
                    "entity_extraction",
                    "comparative_analysis",
                    "trend_analysis",
                    "anomaly_detection",
                    "custom_queries",
                ],
            },
            {
                "name": "synthesizer",
                "type": "synthesizer",
                "status": "available",
                "capabilities": [
                    "executive_summary",
                    "detailed_analysis",
                    "technical_report",
                    "json_output",
                    "markdown_output",
                    "html_output",
                ],
            },
        ]
    }