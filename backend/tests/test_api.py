"""
Tests for API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "services" in data

    @pytest.mark.asyncio
    async def test_liveness(self, client: AsyncClient):
        """Test liveness probe."""
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestExecutionEndpoints:
    """Test execution endpoints."""

    @pytest.mark.asyncio
    async def test_create_execution(self, client: AsyncClient, sample_execution_data):
        """Test creating an execution."""
        response = await client.post("/api/v1/executions", json=sample_execution_data)
        assert response.status_code == 201
        data = response.json()
        assert "execution_id" in data
        assert data["execution_type"] == sample_execution_data["execution_type"]
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_executions(self, client: AsyncClient):
        """Test listing executions."""
        response = await client.get("/api/v1/executions")
        assert response.status_code == 200
        data = response.json()
        assert "executions" in data
        assert "total" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, client: AsyncClient):
        """Test getting non-existent execution."""
        response = await client.get("/api/v1/executions/non-existent-id")
        assert response.status_code == 404


class TestDocumentEndpoints:
    """Test document endpoints."""

    @pytest.mark.asyncio
    async def test_list_documents(self, client: AsyncClient):
        """Test listing documents."""
        response = await client.get("/api/v1/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client: AsyncClient):
        """Test getting non-existent document."""
        response = await client.get("/api/v1/documents/non-existent-id")
        assert response.status_code == 404


class TestWorkflowEndpoints:
    """Test workflow endpoints."""

    @pytest.mark.asyncio
    async def test_create_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test creating a workflow."""
        response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        assert response.status_code == 201
        data = response.json()
        assert "workflow_id" in data
        assert data["name"] == sample_workflow_data["name"]

    @pytest.mark.asyncio
    async def test_list_workflows(self, client: AsyncClient):
        """Test listing workflows."""
        response = await client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_workflow_templates(self, client: AsyncClient):
        """Test getting workflow templates."""
        response = await client.get("/api/v1/workflows/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0


class TestAgentEndpoints:
    """Test agent endpoints."""

    @pytest.mark.asyncio
    async def test_get_agents_status(self, client: AsyncClient):
        """Test getting agent status."""
        response = await client.get("/api/v1/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 3
        agent_names = {a["name"] for a in data["agents"]}
        assert agent_names == {"scraper", "analyst", "synthesizer"}


class TestChatEndpoints:
    """Test chat endpoints."""

    @pytest.mark.asyncio
    async def test_create_chat_session(self, client: AsyncClient):
        """Test creating a chat session."""
        response = await client.post("/api/v1/chat/sessions", json={"title": "Test Chat"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["title"] == "Test Chat"

    @pytest.mark.asyncio
    async def test_query_without_session(self, client: AsyncClient):
        """Test stateless query."""
        response = await client.post("/api/v1/chat/query", json={
            "message": "Hello",
            "use_rag": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data


class TestMetricsEndpoints:
    """Test metrics endpoints."""

    @pytest.mark.asyncio
    async def test_metrics_summary(self, client: AsyncClient):
        """Test metrics summary."""
        response = await client.get("/api/v1/metrics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "executions" in data
        assert "agents" in data

    @pytest.mark.asyncio
    async def test_prometheus_metrics(self, client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics/prometheus")
        assert response.status_code == 200
        assert "agenttic_" in response.text


class TestN8nEndpoints:
    """Test n8n integration endpoints."""

    @pytest.mark.asyncio
    async def test_n8n_health(self, client: AsyncClient):
        """Test n8n health check."""
        response = await client.get("/api/v1/n8n/health")
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data