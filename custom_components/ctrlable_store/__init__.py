"""Ctrlable Store — private, license-gated installer for Ctrlable components.

Reads the device identity written by the ctrlable agent add-on, shows the
entitled catalog from portal.ctrlable.com, and installs/updates components into
custom_components/ (HACS-safe). No user config — it's appliance infrastructure.
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.instance_id import async_get as async_get_instance_id
from homeassistant.helpers.typing import ConfigType

from . import websocket_api
from .const import (
    DEFAULT_API_BASE,
    DOMAIN,
    PANEL_ELEMENT,
    PANEL_FOLDER,
    PANEL_ICON,
    PANEL_JS,
    PANEL_STATIC_URL,
    PANEL_TITLE,
    PANEL_URL_PATH,
)
from .store_client import StoreClient, read_agent_creds

_LOGGER = logging.getLogger(__name__)
_HERE = Path(__file__).resolve().parent


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    creds = await hass.async_add_executor_job(read_agent_creds)
    instance_id = await async_get_instance_id(hass)
    api_base = creds.get("API_BASE") or DEFAULT_API_BASE
    if api_base.rstrip("/").endswith("/v1"):  # agent stores .../v1 (enroll base)
        api_base = api_base.rstrip("/")
    client = StoreClient(
        async_get_clientsession(hass),
        device_token=creds.get("DEVICE_TOKEN", ""),
        instance_id=instance_id,
        api_base=api_base if api_base.endswith("/api/v1") else DEFAULT_API_BASE,
    )
    hass.data[DOMAIN] = {"client": client, "cc_dir": hass.config.path("custom_components")}
    if not client.configured:
        _LOGGER.warning(
            "Ctrlable Store: no device token found (is the Ctrlable agent enrolled?). "
            "The Store panel will load but can't reach the portal until enrolled."
        )

    websocket_api.async_register(hass)

    # Serve + register the panel (always available; appliance admin tool).
    await hass.http.async_register_static_paths(
        [StaticPathConfig(PANEL_STATIC_URL, str(_HERE / PANEL_FOLDER), False)]
    )
    try:
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            frontend_url_path=PANEL_URL_PATH,
            require_admin=True,
            config={
                "_panel_custom": {
                    "name": PANEL_ELEMENT,
                    "embed_iframe": False,
                    "trust_external": False,
                    "module_url": f"{PANEL_STATIC_URL}/{PANEL_JS}",
                }
            },
        )
    except ValueError:
        pass  # already registered
    return True
