"""
n8n Client Service for workflow automation integration.
"""
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings


class N8nClient:
    """Client for interacting with n8n API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url or settings.N8N_API_URL
        self.api_key = api_key or settings.N8N_API_KEY
        self.webhook_url = settings.N8N_WEBHOOK_URL
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-N8N-API-KEY": self.api_key,
                "Content-Type": "application/json",
            } if self.api_key else {"Content-Type": "application/json"},
            timeout=30.0,
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    # Workflow Management
    async def list_workflows(
        self,
        active: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List workflows."""
        params = {}
        if active is not None:
            params["active"] = str(active).lower()
        if tags:
            params["tags"] = ",".join(tags)

        response = await self._client.get("/workflows", params=params)
        response.raise_for_status()
        return response.json().get("data", [])

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID."""
        response = await self._client.get(f"/workflows/{workflow_id}")
        response.raise_for_status()
        return response.json()

    async def create_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        response = await self._client.post("/workflows", json=workflow)
        response.raise_for_status()
        return response.json()

    async def update_workflow(self, workflow_id: str, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing workflow."""
        response = await self._client.put(f"/workflows/{workflow_id}", json=workflow)
        response.raise_for_status()
        return response.json()

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        response = await self._client.delete(f"/workflows/{workflow_id}")
        response.raise_for_status()
        return True

    async def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Activate a workflow."""
        response = await self._client.post(f"/workflows/{workflow_id}/activate")
        response.raise_for_status()
        return response.json()

    async def deactivate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Deactivate a workflow."""
        response = await self._client.post(f"/workflows/{workflow_id}/deactivate")
        response.raise_for_status()
        return response.json()

    # Execution Management
    async def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None,
        run_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        payload = {}
        if data:
            payload["data"] = data
        if run_data:
            payload["runData"] = run_data

        response = await self._client.post(f"/workflows/{workflow_id}/execute", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get execution history."""
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        if status:
            params["status"] = status

        response = await self._client.get("/executions", params=params)
        response.raise_for_status()
        return response.json().get("data", [])

    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution details."""
        response = await self._client.get(f"/executions/{execution_id}")
        response.raise_for_status()
        return response.json()

    # Webhook Management
    async def trigger_webhook(
        self,
        webhook_path: str,
        payload: Dict[str, Any],
        method: str = "POST",
    ) -> Dict[str, Any]:
        """Trigger a webhook."""
        url = f"{self.webhook_url}/{webhook_path}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    # Credentials
    async def list_credentials(self, type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List credentials."""
        params = {}
        if type:
            params["type"] = type

        response = await self._client.get("/credentials", params=params)
        response.raise_for_status()
        return response.json().get("data", [])

    # Workflow Templates
    async def import_workflow(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """Import workflow from JSON."""
        # n8n import uses the same endpoint as create
        return await self.create_workflow(workflow_json)

    async def export_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Export workflow as JSON."""
        return await self.get_workflow(workflow_id)

    # Health check
    async def health_check(self) -> bool:
        """Check if n8n is healthy."""
        try:
            response = await self._client.get("/healthz")
            return response.status_code == 200
        except Exception:
            return False


class N8nWebhookHandler:
    """Handler for incoming n8n webhooks."""

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or settings.WEBHOOK_SECRET
        self.handlers: Dict[str, callable] = {}

    def register_handler(self, event_type: str, handler: callable):
        """Register a webhook handler."""
        self.handlers[event_type] = handler

    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook."""
        handler = self.handlers.get(event_type)
        if not handler:
            return {"status": "ignored", "reason": f"No handler for {event_type}"}

        try:
            result = await handler(payload)
            return {"status": "processed", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        import hmac
        import hashlib

        expected = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)


# Pre-built workflow templates
WORKFLOW_TEMPLATES = {
    "data_pipeline": {
        "name": "Data Processing Pipeline",
        "nodes": [
            {
                "name": "Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": "data-pipeline-trigger",
                "parameters": {
                    "httpMethod": "POST",
                    "path": "data-pipeline",
                    "responseMode": "onReceived",
                },
            },
            {
                "name": "Scrape Data",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 2,
                "position": [500, 200],
                "parameters": {
                    "url": "={{ $json.url }}",
                    "method": "GET",
                    "responseFormat": "json",
                },
            },
            {
                "name": "Process with AI",
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": [750, 300],
                "parameters": {
                    "functionCode": "// Call Agenttic API for analysis\nconst response = await $http.post('http://backend:8000/api/v1/analyze', {\n  documents: [{ content: $json.content }],\n  queries: $json.queries || []\n});\nreturn response.data;",
                },
            },
            {
                "name": "Send Notification",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1,
                "position": [1000, 300],
                "parameters": {
                    "chatId": "={{ $json.chat_id }}",
                    "text": "Analysis complete: {{ $json.summary }}",
                },
            },
        ],
        "connections": {
            "Webhook Trigger": {
                "main": [["Scrape Data"]],
            },
            "Scrape Data": {
                "main": [["Process with AI"]],
            },
            "Process with AI": {
                "main": [["Send Notification"]],
            },
        },
    },
    "scheduled_scraping": {
        "name": "Scheduled Web Scraping",
        "nodes": [
            {
                "name": "Cron Trigger",
                "type": "n8n-nodes-base.cron",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "triggerTimes": {
                        "item": [
                            {"hour": 6, "minute": 0},
                        ],
                    },
                },
            },
            {
                "name": "Get URLs to Scrape",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 2,
                "position": [500, 200],
                "parameters": {
                    "url": "http://backend:8000/api/v1/urls/to-scrape",
                    "method": "GET",
                },
            },
            {
                "name": "Scrape Each URL",
                "type": "n8n-nodes-base.splitInBatches",
                "typeVersion": 1,
                "position": [750, 300],
                "parameters": {
                    "batchSize": 1,
                    "options": {},
                },
            },
            {
                "name": "Call Scraper API",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 2,
                "position": [1000, 300],
                "parameters": {
                    "url": "http://backend:8000/api/v1/scrape",
                    "method": "POST",
                    "jsonParameters": true,
                    "options": {},
                    "bodyParametersJson": "={{ JSON.stringify({ urls: [$json.url] }) }}",
                },
            },
            {
                "name": "Store Results",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 2,
                "position": [1250, 300],
                "parameters": {
                    "url": "http://backend:8000/api/v1/documents",
                    "method": "POST",
                    "jsonParameters": true,
                    "options": {},
                    "bodyParametersJson": "={{ JSON.stringify($json) }}",
                },
            },
        ],
        "connections": {
            "Cron Trigger": {
                "main": [["Get URLs to Scrape"]],
            },
            "Get URLs to Scrape": {
                "main": [["Scrape Each URL"]],
            },
            "Scrape Each URL": {
                "main": [["Call Scraper API"]],
            },
            "Call Scraper API": {
                "main": [["Store Results"]],
            },
        },
    },
}