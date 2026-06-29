"""WebSocket API for the Ctrlable Store panel."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .installer import install_zip, installed_version

_LOGGER = logging.getLogger(__name__)


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_catalog)
    websocket_api.async_register_command(hass, ws_install)
    websocket_api.async_register_command(hass, ws_restart)


@websocket_api.websocket_command({vol.Required("type"): "ctrlable_store/catalog"})
@websocket_api.async_response
async def ws_catalog(hass, connection, msg):
    data = hass.data[DOMAIN]
    client, cc = data["client"], data["cc_dir"]
    if not client.configured:
        connection.send_result(msg["id"], {"configured": False, "products": []})
        return
    try:
        products = await client.get_catalog()
    except Exception as err:  # noqa: BLE001
        connection.send_error(msg["id"], "catalog_failed", str(err))
        return
    for p in products:
        inst = installed_version(cc, p["product"])
        p["installed_version"] = inst
        p["update_available"] = bool(inst) and inst != p["version"]
        p["installed"] = bool(inst)
    connection.send_result(msg["id"], {"configured": True, "products": products})


@websocket_api.websocket_command(
    {vol.Required("type"): "ctrlable_store/install", vol.Required("product"): str}
)
@websocket_api.async_response
async def ws_install(hass, connection, msg):
    data = hass.data[DOMAIN]
    client, cc = data["client"], data["cc_dir"]
    product = msg["product"]
    try:
        catalog = await client.get_catalog()
        entry = next((p for p in catalog if p["product"] == product), None)
        if entry is None:
            raise ValueError("product not in entitled catalog")
        blob = await client.download(product, entry["version"], entry.get("sha256"))
        version = await hass.async_add_executor_job(install_zip, cc, product, blob)
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Ctrlable Store install failed")
        connection.send_error(msg["id"], "install_failed", str(err))
        return
    connection.send_result(msg["id"], {"product": product, "version": version, "restart_required": True})


@websocket_api.websocket_command({vol.Required("type"): "ctrlable_store/restart"})
@websocket_api.async_response
async def ws_restart(hass, connection, msg):
    connection.send_result(msg["id"], {"restarting": True})
    await hass.services.async_call("homeassistant", "restart", blocking=False)
