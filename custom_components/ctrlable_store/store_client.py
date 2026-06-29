"""Portal Store client — reuses the ctrlable agent's device identity."""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Optional

import aiohttp

from .const import CREDS_PATHS, DEFAULT_API_BASE

_LOGGER = logging.getLogger(__name__)


def read_agent_creds() -> dict[str, str]:
    """Parse the ctrlable agent's conf (shell KEY=VALUE / KEY="VALUE")."""
    for path in CREDS_PATHS:
        if not os.path.isfile(path):
            continue
        creds: dict[str, str] = {}
        try:
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    creds[k.strip()] = v.strip().strip('"').strip("'")
        except OSError as exc:  # noqa: BLE001
            _LOGGER.warning("Could not read %s: %s", path, exc)
            continue
        if creds.get("DEVICE_TOKEN"):
            return creds
    return {}


class StoreError(Exception):
    """Store client error."""


class StoreClient:
    """Talks to portal.ctrlable.com /api/v1/store with the device token."""

    def __init__(self, session: aiohttp.ClientSession, device_token: str,
                 instance_id: str, api_base: str = DEFAULT_API_BASE) -> None:
        self._session = session
        self._token = device_token
        self._instance_id = instance_id
        self._base = api_base.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self._token)

    def _headers(self) -> dict[str, str]:
        return {"X-Device-Token": self._token}

    async def get_catalog(self) -> list[dict[str, Any]]:
        url = f"{self._base}/store/catalog"
        params = {"instance_id": self._instance_id}
        async with self._session.get(url, headers=self._headers(), params=params) as resp:
            if resp.status != 200:
                raise StoreError(f"catalog HTTP {resp.status}")
            data = await resp.json()
        return data.get("products", [])

    async def download(self, product: str, version: str, sha256: Optional[str] = None) -> bytes:
        url = f"{self._base}/store/download/{product}/{version}"
        params = {"instance_id": self._instance_id}
        async with self._session.get(url, headers=self._headers(), params=params) as resp:
            if resp.status == 403:
                raise StoreError("not licensed for this product")
            if resp.status != 200:
                raise StoreError(f"download HTTP {resp.status}")
            blob = await resp.read()
        if sha256:
            got = hashlib.sha256(blob).hexdigest()
            if got != sha256:
                raise StoreError(f"sha256 mismatch (expected {sha256[:12]}, got {got[:12]})")
        return blob
