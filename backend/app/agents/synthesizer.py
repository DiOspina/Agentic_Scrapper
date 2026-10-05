"""
Synthesizer Agent for generating executive reports in JSON and Markdown.
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.agent_log import AgentType, LogLevel
from app.core.config import settings


class ReportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class ReportType(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    TECHNICAL_REPORT = "technical_report"
    DASHBOARD_SNAPSHOT = "dashboard_snapshot"
    COMPARATIVE_REPORT = "comparative_report"
    TREND_REPORT = "trend_report"
    ANOMALY_REPORT = "anomaly_report"
    CUSTOM = "custom"


@dataclass
class ReportConfig:
    report_type: ReportType = ReportType.EXECUTIVE_SUMMARY
    formats: List[ReportFormat] = field(default_factory=lambda: [ReportFormat.JSON, ReportFormat.MARKDOWN])
    include_charts: bool = True
    include_raw_data: bool = False
    max_length: int = 10000
    language: str = "es"
    template: Optional[str] = None
    branding: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSection:
    title: str
    content: str
    order: int
    format: str = "markdown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedReport:
    report_id: str
    report_type: ReportType
    title: str
    sections: List[ReportSection]
    formats: Dict[ReportFormat, str]
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


class SynthesizerAgent(BaseAgent):
    """Agent for synthesizing analysis results into executive reports."""

    def __init__(
        self,
        llm=None,
        config: Optional[Dict[str, Any]] = None,
        report_config: Optional[ReportConfig] = None,
    ):
        super().__init__(
            agent_type=AgentType.SYNTHESIZER,
            name="synthesizer",
            llm=llm,
            config=config,
        )
        self.report_config = report_config or ReportConfig()
        self._templates: Dict[str, str] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default report templates."""
        self._templates["executive_summary"] = """# {title}

**Report ID:** {report_id}
**Generated:** {timestamp}
**Type:** {report_type}

---

## Executive Summary

{executive_summary}

---

## Key Findings

{key_findings}

---

## Metrics Overview

{metrics_overview}

---

## Recommendations

{recommendations}

---

## Appendix

{appendix}
"""

        self._templates["detailed_analysis"] = """# {title}

**Report ID:** {report_id}
**Generated:** {timestamp}
**Type:** {report_type}

---

## Introduction

{introduction}

---

## Methodology

{methodology}

---

## Detailed Findings

{detailed_findings}

---

## Data Analysis

{data_analysis}

---

## Charts & Visualizations

{charts}

---

## Conclusions

{conclusions}

---

## Recommendations

{recommendations}

---

## Appendices

{appendices}
"""

        self._templates["technical_report"] = """# {title}

**Report ID:** {report_id}
**Generated:** {timestamp}
**Type:** {report_type}

---

## Technical Overview

{technical_overview}

---

## Architecture

{architecture}

---

## Implementation Details

{implementation}

---

## Performance Metrics

{performance}

---

## Issues & Resolutions

{issues}

---

## Future Work

{future_work}
"""

    async def execute(self, context: AgentContext) -> AgentResult:
        """Generate reports from analysis results."""
        analysis_results = context.input_data.get("analysis_results", [])
        scraped_data = context.input_data.get("scraped_data", {})
        query_results = context.input_data.get("query_results", [])
        metrics = context.input_data.get("metrics", {})
        report_config_overrides = context.input_data.get("report_config", {})

        # Merge config
        report_config = ReportConfig(**{**self.report_config.__dict__, **report_config_overrides})

        # Prepare data for report generation
        report_data = self._prepare_report_data(
            analysis_results, scraped_data, query_results, metrics
        )

        # Generate report sections
        sections = await self._generate_sections(report_data, report_config)

        # Generate report in requested formats
        formats_output = {}
        for fmt in report_config.formats:
            if fmt == ReportFormat.JSON:
                formats_output[fmt] = self._generate_json_report(sections, report_data, report_config)
            elif fmt == ReportFormat.MARKDOWN:
                formats_output[fmt] = self._generate_markdown_report(sections, report_data, report_config)
            elif fmt == ReportFormat.HTML:
                formats_output[fmt] = self._generate_html_report(sections, report_data, report_config)

        # Create report object
        report = GeneratedReport(
            report_id=str(uuid.uuid4()),
            report_type=report_config.report_type,
            title=report_data.get("title", "Agenttic Analysis Report"),
            sections=sections,
            formats=formats_output,
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "source_executions": context.input_data.get("execution_ids", []),
                "analysis_count": len(analysis_results),
                "query_count": len(query_results),
                "config": report_config.__dict__,
            },
        )

        # Save reports if output directory configured
        output_paths = await self._save_reports(report, report_config)

        output_data = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "title": report.title,
            "formats": {k.value: v for k, v in formats_output.items()},
            "output_paths": output_paths,
            "metadata": report.metadata,
        }

        return AgentResult(
            success=True,
            output_data=output_data,
            metrics={"sections_generated": len(sections), "formats_generated": len(formats_output)},
        )

    def _prepare_report_data(
        self,
        analysis_results: List[Dict[str, Any]],
        scraped_data: Dict[str, Any],
        query_results: List[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare and structure data for report generation."""
        # Extract key findings from analyses
        key_findings = []
        all_metrics = {}
        anomalies = []
        patterns = []
        sentiments = []
        entities = []

        for analysis in analysis_results:
            atype = analysis.get("analysis_type")
            result = analysis.get("result", {})

            if atype == "summarization":
                for summary in result.get("summaries", []):
                    key_findings.append({
                        "type": "summary",
                        "document_id": summary.get("document_id"),
                        "content": summary.get("summary"),
                    })

            elif atype == "key_metrics":
                for metric in result.get("metrics", []):
                    if not metric.get("parse_error"):
                        key = metric.get("metric_name", "unknown")
                        all_metrics[key] = metric

            elif atype == "pattern_detection":
                patterns.append(result)

            elif atype == "anomaly_detection":
                for anomaly in result.get("anomalies", []):
                    anomalies.append(anomaly)

            elif atype == "sentiment_analysis":
                for sentiment in result.get("sentiments", []):
                    sentiments.append(sentiment)

            elif atype == "entity_extraction":
                for entity in result.get("entities", []):
                    entities.append(entity)

        return {
            "title": "Agenttic AI Analysis Report",
            "timestamp": datetime.utcnow().isoformat(),
            "key_findings": key_findings,
            "metrics": {**all_metrics, **metrics},
            "anomalies": anomalies,
            "patterns": patterns,
            "sentiments": sentiments,
            "entities": entities,
            "query_results": query_results,
            "scraped_summary": {
                "total_pages": scraped_data.get("total_pages", 0),
                "urls_processed": scraped_data.get("urls_processed", []),
            },
            "analysis_results": analysis_results,
        }

    async def _generate_sections(
        self,
        report_data: Dict[str, Any],
        config: ReportConfig,
    ) -> List[ReportSection]:
        """Generate report sections using LLM."""
        sections = []

        # Executive Summary
        exec_summary = await self._generate_executive_summary(report_data)
        sections.append(ReportSection(
            title="Executive Summary",
            content=exec_summary,
            order=1,
        ))

        # Key Findings
        if report_data.get("key_findings"):
            findings_content = await self._generate_key_findings_section(report_data)
            sections.append(ReportSection(
                title="Key Findings",
                content=findings_content,
                order=2,
            ))

        # Metrics Overview
        if report_data.get("metrics"):
            metrics_content = await self._generate_metrics_section(report_data)
            sections.append(ReportSection(
                title="Metrics Overview",
                content=metrics_content,
                order=3,
            ))

        # Patterns & Insights
        if report_data.get("patterns"):
            patterns_content = await self._generate_patterns_section(report_data)
            sections.append(ReportSection(
                title="Patterns & Insights",
                content=patterns_content,
                order=4,
            ))

        # Anomalies
        if report_data.get("anomalies"):
            anomalies_content = await self._generate_anomalies_section(report_data)
            sections.append(ReportSection(
                title="Anomalies Detected",
                content=anomalies_content,
                order=5,
            ))

        # Query Results
        if report_data.get("query_results"):
            queries_content = await self._generate_queries_section(report_data)
            sections.append(ReportSection(
                title="Query Responses",
                content=queries_content,
                order=6,
            ))

        # Recommendations
        recommendations = await self._generate_recommendations(report_data)
        sections.append(ReportSection(
            title="Recommendations",
            content=recommendations,
            order=7,
        ))

        # Technical Appendix
        if config.include_raw_data:
            appendix = self._generate_appendix(report_data)
            sections.append(ReportSection(
                title="Appendix: Raw Data",
                content=appendix,
                order=8,
            ))

        return sections

    async def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary using LLM."""
        prompt = f"""Create a concise executive summary (3-5 paragraphs) based on the following analysis data.
Focus on the most important findings, key metrics, and business implications.

Data:
- Total analyses: {len(data.get('analysis_results', []))}
- Key findings count: {len(data.get('key_findings', []))}
- Metrics found: {len(data.get('metrics', {}))}
- Anomalies detected: {len(data.get('anomalies', []))}
- Patterns identified: {len(data.get('patterns', []))}
- Queries answered: {len(data.get('query_results', []))}
- Pages scraped: {data.get('scraped_summary', {}).get('total_pages', 0)}

Key Findings: {json.dumps(data.get('key_findings', [])[:3], ensure_ascii=False)}
Top Metrics: {json.dumps(dict(list(data.get('metrics', {}).items())[:5]), ensure_ascii=False)}

Write in {self.report_config.language}. Be professional, concise, and actionable."""

        response = await self.call_llm([HumanMessage(content=prompt)])
        return response.content

    async def _generate_key_findings_section(self, data: Dict[str, Any]) -> str:
        """Generate key findings section."""
        findings = data.get("key_findings", [])

        if not findings:
            return "No key findings available."

        content = "## Key Findings\n\n"
        for i, finding in enumerate(findings, 1):
            content += f"### Finding {i}\n"
            if finding.get("type") == "summary":
                content += f"**Document:** {finding.get('document_id', 'N/A')}\n\n"
                content += f"{finding.get('content', '')}\n\n"
            else:
                content += f"{json.dumps(finding, indent=2, ensure_ascii=False)}\n\n"

        return content

    async def _generate_metrics_section(self, data: Dict[str, Any]) -> str:
        """Generate metrics overview section."""
        metrics = data.get("metrics", {})

        if not metrics:
            return "No metrics available."

        content = "## Metrics Overview\n\n"
        content += "| Metric | Value | Unit | Context |\n"
        content += "|--------|-------|------|---------|\n"

        for name, metric in list(metrics.items())[:20]:
            if isinstance(metric, dict):
                value = metric.get("value", "N/A")
                unit = metric.get("unit", "")
                context = metric.get("context", "")[:100]
            else:
                value = metric
                unit = ""
                context = ""

            content += f"| {name} | {value} | {unit} | {context} |\n"

        return content

    async def _generate_patterns_section(self, data: Dict[str, Any]) -> str:
        """Generate patterns section."""
        patterns = data.get("patterns", [])

        if not patterns:
            return "No patterns detected."

        content = "## Patterns & Insights\n\n"
        for pattern in patterns:
            result = pattern.get("result", {})
            if isinstance(result, dict):
                for category, items in result.items():
                    if isinstance(items, list) and items:
                        content += f"### {category.title()}\n"
                        for item in items[:10]:
                            if isinstance(item, dict):
                                content += f"- {item.get('name', item.get('description', str(item)))}\n"
                            else:
                                content += f"- {item}\n"
                        content += "\n"

        return content

    async def _generate_anomalies_section(self, data: Dict[str, Any]) -> str:
        """Generate anomalies section."""
        anomalies = data.get("anomalies", [])

        if not anomalies:
            return "No anomalies detected."

        content = "## Anomalies Detected\n\n"
        content += "| Severity | Description | Evidence |\n"
        content += "|----------|-------------|----------|\n"

        for anomaly in anomalies:
            if isinstance(anomaly, dict) and "anomalies" in anomaly:
                for a in anomaly["anomalies"]:
                    if isinstance(a, dict):
                        severity = a.get("severity", "unknown")
                        desc = a.get("description", "")[:200]
                        evidence = a.get("evidence", "")[:200]
                        content += f"| {severity} | {desc} | {evidence} |\n"

        return content

    async def _generate_queries_section(self, data: Dict[str, Any]) -> str:
        """Generate query results section."""
        queries = data.get("query_results", [])

        if not queries:
            return "No queries processed."

        content = "## Query Responses\n\n"
        for qr in queries:
            content += f"### Q: {qr.get('query', '')}\n\n"
            content += f"**A:** {qr.get('answer', '')}\n\n"
            content += f"*Confidence: {qr.get('confidence', 0):.0%}*\n\n"
            if qr.get("sources"):
                content += f"*Sources: {len(qr['sources'])} document(s)*\n\n"

        return content

    async def _generate_recommendations(self, data: Dict[str, Any]) -> str:
        """Generate recommendations based on analysis."""
        prompt = f"""Based on the following analysis results, provide 5-7 actionable recommendations.
Prioritize by impact and feasibility. Format as numbered list with brief explanations.

Key Findings: {json.dumps(data.get('key_findings', [])[:5], ensure_ascii=False)}
Metrics: {json.dumps(dict(list(data.get('metrics', {}).items())[:10]), ensure_ascii=False)}
Anomalies: {len(data.get('anomalies', []))} detected
Patterns: {json.dumps(data.get('patterns', [])[:2], ensure_ascii=False)}

Language: {self.report_config.language}"""

        response = await self.call_llm([HumanMessage(content=prompt)])
        return response.content

    def _generate_appendix(self, data: Dict[str, Any]) -> str:
        """Generate technical appendix with raw data."""
        content = "## Appendix: Raw Data\n\n"
        content += "### Analysis Results\n\n"
        content += f"```json\n{json.dumps(data.get('analysis_results', []), indent=2, ensure_ascii=False)}\n```\n\n"

        content += "### Query Results\n\n"
        content += f"```json\n{json.dumps(data.get('query_results', []), indent=2, ensure_ascii=False)}\n```\n\n"

        content += "### Scraped Data Summary\n\n"
        content += f"```json\n{json.dumps(data.get('scraped_summary', {}), indent=2, ensure_ascii=False)}\n```\n"

        return content

    def _generate_json_report(
        self,
        sections: List[ReportSection],
        data: Dict[str, Any],
        config: ReportConfig,
    ) -> str:
        """Generate JSON format report."""
        report = {
            "report_id": str(uuid.uuid4()),
            "report_type": config.report_type.value,
            "title": data.get("title", "Agenttic Analysis Report"),
            "generated_at": datetime.utcnow().isoformat(),
            "language": config.language,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "format": s.format,
                    "metadata": s.metadata,
                }
                for s in sections
            ],
            "data_summary": {
                "total_analyses": len(data.get("analysis_results", [])),
                "key_findings_count": len(data.get("key_findings", [])),
                "metrics_count": len(data.get("metrics", {})),
                "anomalies_count": len(data.get("anomalies", [])),
                "queries_answered": len(data.get("query_results", [])),
            },
            "raw_data": data if config.include_raw_data else None,
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    def _generate_markdown_report(
        self,
        sections: List[ReportSection],
        data: Dict[str, Any],
        config: ReportConfig,
    ) -> str:
        """Generate Markdown format report."""
        template = self._templates.get(config.report_type.value, self._templates["executive_summary"])

        # Build section content map
        section_map = {s.title.lower().replace(" ", "_"): s.content for s in sections}

        # Fill template
        markdown = template.format(
            title=data.get("title", "Agenttic Analysis Report"),
            report_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            report_type=config.report_type.value.replace("_", " ").title(),
            executive_summary=section_map.get("executive_summary", ""),
            key_findings=section_map.get("key_findings", ""),
            metrics_overview=section_map.get("metrics_overview", ""),
            recommendations=section_map.get("recommendations", ""),
            appendix=section_map.get("appendix:_raw_data", ""),
            introduction=section_map.get("introduction", ""),
            methodology=section_map.get("methodology", ""),
            detailed_findings=section_map.get("detailed_findings", ""),
            data_analysis=section_map.get("data_analysis", ""),
            charts=section_map.get("charts_&_visualizations", ""),
            conclusions=section_map.get("conclusions", ""),
            appendices=section_map.get("appendices", ""),
            technical_overview=section_map.get("technical_overview", ""),
            architecture=section_map.get("architecture", ""),
            implementation=section_map.get("implementation_details", ""),
            performance=section_map.get("performance_metrics", ""),
            issues=section_map.get("issues_&_resolutions", ""),
            future_work=section_map.get("future_work", ""),
        )

        return markdown

    def _generate_html_report(
        self,
        sections: List[ReportSection],
        data: Dict[str, Any],
        config: ReportConfig,
    ) -> str:
        """Generate HTML format report from Markdown."""
        markdown = self._generate_markdown_report(sections, data, config)

        # Simple markdown to HTML conversion
        html = self._markdown_to_html(markdown)

        # Wrap in full HTML document
        return f"""<!DOCTYPE html>
<html lang="{config.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.get('title', 'Agenttic Analysis Report')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 2rem; color: #333; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #4f46e5; padding-bottom: 0.5rem; }}
        h2 {{ color: #3730a3; margin-top: 2rem; border-bottom: 1px solid #e0e7ff; padding-bottom: 0.3rem; }}
        h3 {{ color: #4f46e5; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #e5e7eb; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #f3f4f6; font-weight: 600; }}
        code {{ background: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: 'Monaco', 'Consolas', monospace; }}
        pre {{ background: #1f2937; color: #e5e7eb; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        blockquote {{ border-left: 4px solid #4f46e5; padding-left: 1rem; color: #6b7280; margin: 1rem 0; }}
        .metadata {{ background: #f9fafb; padding: 1rem; border-radius: 8px; margin-bottom: 2rem; font-size: 0.9rem; }}
    </style>
</head>
<body>
    {html}
</body>
</html>"""

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (simplified)."""
        import re

        html = markdown

        # Headers
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

        # Code blocks
        html = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="language-\1">\2</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)

        # Lists
        html = re.sub(r'^\- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)

        # Paragraphs
        html = re.sub(r'^([^<\n].*$)', r'<p>\1</p>', html, flags=re.MULTILINE)

        # Tables (basic)
        # This is complex, skip for now

        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

        return html

    async def _save_reports(
        self,
        report: GeneratedReport,
        config: ReportConfig,
    ) -> Dict[str, str]:
        """Save reports to disk."""
        output_dir = Path(settings.UPLOAD_DIR) / "reports" / report.report_id
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = {}
        for fmt, content in report.formats.items():
            ext = fmt.value
            if fmt == ReportFormat.MARKDOWN:
                ext = "md"
            elif fmt == ReportFormat.HTML:
                ext = "html"

            file_path = output_dir / f"report.{ext}"
            file_path.write_text(content, encoding="utf-8")
            paths[fmt.value] = str(file_path)

        return paths