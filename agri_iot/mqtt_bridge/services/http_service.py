"""
HTTP Service for the Industrial IoT Bridge
Handles communication with Odoo via HTTP webhooks
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional
import httpx
from httpx import TimeoutException, RequestError

from config.settings import settings

logger = logging.getLogger(__name__)


def _jsonrpc_envelope(params: Dict[str, Any]) -> Dict[str, Any]:
    """Bungkus params ke envelope JSON-RPC 2.0 untuk route Odoo ``type='json'``.

    B18 (10 Nov 2026): Odoo 18 ``JsonRPCDispatcher.dispatch`` (``odoo/http.py``)
    hanya mengisi ``request.params`` dari member ``params`` envelope
    (``request.params = dict(self.jsonrequest.get('params', {}), **args)``).
    Body JSON polos (tanpa envelope) tiba sebagai ``params`` kosong di
    controller, sehingga controller yang sudah diperbaiki (B16,
    ``request.jsonrequest`` -> ``request.params``) tetap menerima data kosong.
    Format: ``{"jsonrpc": "2.0", "method": "call", "params": {...}, "id": ...}``.
    Member ``method`` diabaikan Odoo (routing memakai path HTTP).
    """
    return {
        "jsonrpc": "2.0",
        "method": "call",
        "params": params,
        "id": str(uuid.uuid4()),
    }


def _unwrap_jsonrpc(body: Any) -> Dict[str, Any]:
    """Buka envelope JSON-RPC balasan Odoo ``type='json'``.

    B18 (10 Nov 2026): Odoo membungkus hasil controller menjadi
    ``{"jsonrpc": "2.0", "id": ..., "result": {...}}`` (atau ``"error"``
    bila exception). Kode lama mengembalikan body mentah lalu pemanggil
    mengecek ``response.get("status")`` -> selalu ``None`` -> dispatch
    selalu dianggap gagal. Fungsi ini mengembalikan isi ``result`` apa
    adanya (kontrak lama pemanggil: dict dengan kunci ``status`` /
    ``device_id`` / ``mqtt`` / ``topics`` / ``error``), atau dict
    ``{"status": "error", ...}`` bila balasan membawa member ``error``.
    Body non-envelope (subscriber non-Odoo) diteruskan apa adanya.
    """
    if isinstance(body, dict) and "jsonrpc" in body:
        if "result" in body:
            result = body["result"]
            if isinstance(result, dict):
                return result
            return {"status": "success", "result": result}
        if "error" in body:
            err = body["error"]
            message = err.get("message") if isinstance(err, dict) else str(err)
            return {"status": "error", "error": message, "jsonrpc_error": err}
        return {"status": "error", "error": "Empty JSON-RPC response"}
    if isinstance(body, dict):
        return body
    return {"status": "error", "error": f"Unexpected response: {body!r}"}


class HTTPService:
    """
    Service class for handling HTTP communication with Odoo
    """

    def __init__(self):
        # Create HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.HTTP_REQUEST_TIMEOUT, connect=settings.HTTP_REQUEST_TIMEOUT)
        )

    async def get_device_config(self, serial: str, token: str) -> Dict[str, Any]:
        """
        Request device configuration from Odoo

        Args:
            serial: Device serial number
            token: Configuration token

        Returns:
            Configuration response from Odoo
        """
        url = f"{settings.ODOO_BASE_URL}{settings.ODOO_CONFIG_ENDPOINT}"

        payload = {
            "serial": serial,
            "token": token
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            response = await self.client.post(url, json=_jsonrpc_envelope(payload), headers=headers)

            if response.status_code == 200:
                return _unwrap_jsonrpc(response.json())
            else:
                logger.error(f"Failed to get device config: {response.status_code} - {response.text}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "error"
                }
        except TimeoutException:
            logger.error("Timeout while getting device config")
            return {
                "error": "Request timeout",
                "status": "error"
            }
        except RequestError as e:
            logger.error(f"Request error while getting device config: {str(e)}")
            return {
                "error": f"Request error: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Error getting device config: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }

    async def send_telemetry(self, device_id: str, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send telemetry data to Odoo

        Args:
            device_id: Device identifier
            topic: MQTT topic where data was received
            payload: Telemetry data

        Returns:
            Response from Odoo
        """
        url = f"{settings.ODOO_BASE_URL}{settings.ODOO_WEBHOOK_ENDPOINT}/{device_id}"

        data = {
            "topic": topic,
            "payload": payload
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            response = await self.client.post(url, json=_jsonrpc_envelope(data), headers=headers)

            if response.status_code == 200:
                return _unwrap_jsonrpc(response.json())
            else:
                logger.error(f"Failed to send telemetry: {response.status_code} - {response.text}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "error"
                }
        except TimeoutException:
            logger.error("Timeout while sending telemetry")
            return {
                "error": "Request timeout",
                "status": "error"
            }
        except RequestError as e:
            logger.error(f"Request error while sending telemetry: {str(e)}")
            return {
                "error": f"Request error: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Error sending telemetry: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }

    async def send_ota_status(self, device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send OTA status update to Odoo

        Args:
            device_id: Device identifier
            payload: OTA status data

        Returns:
            Response from Odoo
        """
        url = f"{settings.ODOO_BASE_URL}{settings.ODOO_WEBHOOK_ENDPOINT}/{device_id}"

        data = {
            "topic": f"ota/{device_id}/status",
            "payload": payload
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            response = await self.client.post(url, json=_jsonrpc_envelope(data), headers=headers)

            if response.status_code == 200:
                return _unwrap_jsonrpc(response.json())
            else:
                logger.error(f"Failed to send OTA status: {response.status_code} - {response.text}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "error"
                }
        except TimeoutException:
            logger.error("Timeout while sending OTA status")
            return {
                "error": "Request timeout",
                "status": "error"
            }
        except RequestError as e:
            logger.error(f"Request error while sending OTA status: {str(e)}")
            return {
                "error": f"Request error: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Error sending OTA status: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }

    async def send_command_to_device(self, device_id: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a command to a device through Odoo (for internal use)

        Args:
            device_id: Device identifier
            action: Command action
            params: Command parameters

        Returns:
            Response from Odoo
        """
        url = f"{settings.ODOO_BASE_URL}{settings.ODOO_COMMAND_ENDPOINT}/{device_id}"

        data = {
            "action": action,
            "params": params or {}
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            response = await self.client.post(url, json=_jsonrpc_envelope(data), headers=headers)

            if response.status_code == 200:
                return _unwrap_jsonrpc(response.json())
            else:
                logger.error(f"Failed to send command: {response.status_code} - {response.text}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "error"
                }
        except TimeoutException:
            logger.error("Timeout while sending command")
            return {
                "error": "Request timeout",
                "status": "error"
            }
        except RequestError as e:
            logger.error(f"Request error while sending command: {str(e)}")
            return {
                "error": f"Request error: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def fetch_gateway_config(self) -> Dict[str, Any]:
        """
        Fetch this bridge's configuration from Odoo
        """
        url = f"{settings.ODOO_BASE_URL}{settings.ODOO_GATEWAY_CONFIG_ENDPOINT}"

        data = {
            "gateway_id": settings.BRIDGE_ID
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            response = await self.client.post(url, json=_jsonrpc_envelope(data), headers=headers)

            if response.status_code == 200:
                return _unwrap_jsonrpc(response.json())
            else:
                logger.error(f"Failed to fetch gateway config: {response.status_code} - {response.text}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "error"
                }
        except Exception as e:
            logger.error(f"Error fetching gateway config: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    async def register_bridge(self) -> Dict[str, Any]:
        """
        Register this bridge with Odoo on startup
        """
        url = f"{settings.ODOO_BASE_URL}{settings.ODOO_REGISTER_ENDPOINT}"

        data = {
            "gateway_id": settings.BRIDGE_ID,
            "name": settings.BRIDGE_NAME,
            "url": settings.BRIDGE_PUBLIC_URL
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            response = await self.client.post(url, json=_jsonrpc_envelope(data), headers=headers)

            if response.status_code == 200:
                logger.info(f"Successfully registered bridge {settings.BRIDGE_ID} with Odoo")
                return _unwrap_jsonrpc(response.json())
            else:
                logger.error(f"Failed to register bridge: {response.status_code} - {response.text}")
                return {
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status": "error"
                }
        except Exception as e:
            logger.error(f"Error registering bridge: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }

    async def dispatch_webhook(self, url: str, device_id: str, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a generic webhook to a subscriber
        """
        data = {
            "device_id": device_id,
            "topic": topic,
            "payload": payload
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.ODOO_API_KEY:
            headers["Authorization"] = f"Bearer {settings.ODOO_API_KEY}"

        try:
            # B18: subscriber default adalah webhook Odoo (URL di bawah
            # ODOO_BASE_URL) -> kirim envelope JSON-RPC + buka `result`.
            # Subscriber eksternal (callback URL arbitrary) tetap menerima
            # body polos seperti kontrak lama, dan balasannya diteruskan mentah.
            is_odoo = url.startswith(settings.ODOO_BASE_URL)
            body = _jsonrpc_envelope(data) if is_odoo else data
            response = await self.client.post(url, json=body, headers=headers)
            if response.status_code == 200:
                return _unwrap_jsonrpc(response.json()) if is_odoo else response.json()
            else:
                logger.error(f"Webhook dispatch failed to {url}: {response.status_code}")
                return {"status": "error", "code": response.status_code}
        except Exception as e:
            logger.error(f"Error dispatching webhook to {url}: {str(e)}")
            return {"status": "error", "error": str(e)}