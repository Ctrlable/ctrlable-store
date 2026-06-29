"""Constants for the Ctrlable Store."""

DOMAIN = "ctrlable_store"

# Device credentials are written by the ctrlable agent add-on (ha-addon). The
# /ssl copy is readable from HA core; /data is the add-on-local fallback.
CREDS_PATHS = ["/ssl/ctrlable/ctrlable.conf", "/data/ctrlable.conf"]
DEFAULT_API_BASE = "https://portal.ctrlable.com/api/v1"

# Panel
PANEL_FOLDER = "panel"
PANEL_JS = "ctrlable-store-panel.js"
PANEL_STATIC_URL = "/ctrlable_store_panel"
PANEL_URL_PATH = "ctrlable-store"
PANEL_TITLE = "Ctrlable Store"
PANEL_ICON = "mdi:store-cog"
PANEL_ELEMENT = "ctrlable-store-panel"
