"""
Notification Service for sending alerts via multiple channels.
"""
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.models.alert import AlertChannel, AlertStatus


class NotificationChannel(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class NotificationConfig:
    """Configuration for notification channels."""
    email: Dict[str, Any] = None
    telegram: Dict[str, Any] = None
    whatsapp: Dict[str, Any] = None
    slack: Dict[str, Any] = None
    webhook: Dict[str, Any] = None


class NotificationService:
    """Service for sending notifications across multiple channels."""

    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig(
            email={
                "smtp_host": getattr(settings, "SMTP_HOST", "localhost"),
                "smtp_port": getattr(settings, "SMTP_PORT", 587),
                "smtp_user": getattr(settings, "SMTP_USER", ""),
                "smtp_password": getattr(settings, "SMTP_PASSWORD", ""),
                "from_email": getattr(settings, "FROM_EMAIL", "noreply@agenttic.ai"),
                "use_tls": True,
            },
            telegram={
                "bot_token": getattr(settings, "TELEGRAM_BOT_TOKEN", ""),
                "default_chat_id": getattr(settings, "TELEGRAM_CHAT_ID", ""),
            },
            whatsapp={
                "api_url": getattr(settings, "WHATSAPP_API_URL", ""),
                "api_key": getattr(settings, "WHATSAPP_API_KEY", ""),
                "phone_number_id": getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", ""),
            },
            slack={
                "webhook_url": getattr(settings, "SLACK_WEBHOOK_URL", ""),
                "bot_token": getattr(settings, "SLACK_BOT_TOKEN", ""),
            },
            webhook={
                "default_url": getattr(settings, "DEFAULT_WEBHOOK_URL", ""),
                "secret": getattr(settings, "WEBHOOK_SECRET", ""),
            },
        )

    async def send(
        self,
        channel: NotificationChannel,
        recipient: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send notification via specified channel."""
        if channel == NotificationChannel.EMAIL:
            return await self._send_email(recipient, subject, message, metadata)
        elif channel == NotificationChannel.TELEGRAM:
            return await self._send_telegram(recipient, message, metadata)
        elif channel == NotificationChannel.WHATSAPP:
            return await self._send_whatsapp(recipient, message, metadata)
        elif channel == NotificationChannel.SLACK:
            return await self._send_slack(recipient, message, metadata)
        elif channel == NotificationChannel.WEBHOOK:
            return await self._send_webhook(recipient, subject, message, metadata)
        else:
            return {"success": False, "error": f"Unknown channel: {channel}"}

    async def send_batch(
        self,
        notifications: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Send multiple notifications."""
        results = []
        for notif in notifications:
            result = await self.send(
                channel=NotificationChannel(notif["channel"]),
                recipient=notif["recipient"],
                subject=notif.get("subject", ""),
                message=notif["message"],
                metadata=notif.get("metadata"),
            )
            results.append(result)
        return results

    async def _send_email(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send email notification."""
        config = self.config.email
        if not config.get("smtp_user"):
            return {"success": False, "error": "Email not configured"}

        try:
            msg = MIMEMultipart()
            msg["From"] = config["from_email"]
            msg["To"] = recipient
            msg["Subject"] = subject

            # Create HTML body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4f46e5;">{subject}</h2>
                        <div style="background: #f9fafb; padding: 20px; border-radius: 8px;">
                            {message.replace(chr(10), '<br>')}
                        </div>
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                        <p style="color: #6b7280; font-size: 12px;">
                            This is an automated message from Agenttic AI Orchestration System.
                        </p>
                    </div>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_body, "html"))
            msg.attach(MIMEText(message, "plain"))

            # Send
            with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
                if config.get("use_tls"):
                    server.starttls()
                server.login(config["smtp_user"], config["smtp_password"])
                server.send_message(msg)

            return {"success": True, "channel": "email", "recipient": recipient}

        except Exception as e:
            return {"success": False, "error": str(e), "channel": "email"}

    async def _send_telegram(
        self,
        recipient: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Telegram notification."""
        config = self.config.telegram
        bot_token = config.get("bot_token")
        if not bot_token:
            return {"success": False, "error": "Telegram not configured"}

        chat_id = recipient or config.get("default_chat_id")
        if not chat_id:
            return {"success": False, "error": "No chat ID provided"}

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                response.raise_for_status()

            return {"success": True, "channel": "telegram", "recipient": chat_id}

        except Exception as e:
            return {"success": False, "error": str(e), "channel": "telegram"}

    async def _send_whatsapp(
        self,
        recipient: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send WhatsApp notification via Meta Cloud API."""
        config = self.config.whatsapp
        api_url = config.get("api_url")
        api_key = config.get("api_key")
        phone_number_id = config.get("phone_number_id")

        if not all([api_url, api_key, phone_number_id]):
            return {"success": False, "error": "WhatsApp not configured"}

        try:
            url = f"{api_url}/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message},
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()

            return {"success": True, "channel": "whatsapp", "recipient": recipient}

        except Exception as e:
            return {"success": False, "error": str(e), "channel": "whatsapp"}

    async def _send_slack(
        self,
        recipient: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Slack notification."""
        config = self.config.slack
        webhook_url = config.get("webhook_url")
        bot_token = config.get("bot_token")

        if not webhook_url and not bot_token:
            return {"success": False, "error": "Slack not configured"}

        try:
            payload = {
                "text": message,
                "channel": recipient if recipient.startswith("#") or recipient.startswith("@") else None,
                "username": "Agenttic Bot",
                "icon_emoji": ":robot_face:",
            }

            if webhook_url:
                async with httpx.AsyncClient() as client:
                    response = await client.post(webhook_url, json=payload, timeout=10)
                    response.raise_for_status()
            elif bot_token:
                # Use Bot API
                url = "https://slack.com/api/chat.postMessage"
                headers = {
                    "Authorization": f"Bearer {bot_token}",
                    "Content-Type": "application/json",
                }
                payload["channel"] = recipient
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload, timeout=10)
                    response.raise_for_status()

            return {"success": True, "channel": "slack", "recipient": recipient}

        except Exception as e:
            return {"success": False, "error": str(e), "channel": "slack"}

    async def _send_webhook(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send generic webhook notification."""
        config = self.config.webhook
        url = recipient or config.get("default_url")

        if not url:
            return {"success": False, "error": "No webhook URL provided"}

        try:
            payload = {
                "subject": subject,
                "message": message,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            headers = {"Content-Type": "application/json"}
            secret = config.get("secret")
            if secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    secret.encode(),
                    __import__("json").dumps(payload).encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Signature"] = signature

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()

            return {"success": True, "channel": "webhook", "recipient": url}

        except Exception as e:
            return {"success": False, "error": str(e), "channel": "webhook"}


class AlertNotificationService:
    """Service specifically for alert notifications with retry logic."""

    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def send_alert(
        self,
        alert_id: str,
        channel: NotificationChannel,
        recipient: str,
        title: str,
        message: str,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send alert with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            result = await self.notification_service.send(
                channel=channel,
                recipient=recipient,
                subject=f"[{severity.upper()}] {title}",
                message=message,
                metadata={
                    "alert_id": alert_id,
                    "severity": severity,
                    "attempt": attempt + 1,
                    **(metadata or {}),
                },
            )

            if result.get("success"):
                return {
                    **result,
                    "alert_id": alert_id,
                    "status": AlertStatus.SENT.value,
                    "attempts": attempt + 1,
                }

            last_error = result.get("error")
            if attempt < self.max_retries - 1:
                import asyncio
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        return {
            "success": False,
            "alert_id": alert_id,
            "status": AlertStatus.FAILED.value,
            "error": last_error,
            "attempts": self.max_retries,
        }