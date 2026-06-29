# Ctrlable Store

On-appliance component for the **Ctrlable Store** — a private, license-gated
installer for Ctrlable custom components (an alternative to HACS for our own
products). It reuses the ctrlable agent's device identity, shows the entitled
catalog from `portal.ctrlable.com`, and installs/updates components into
`custom_components/` (HACS-safe staged swap), with a local Store panel.

Pairs with the portal `/api/v1/store/*` API. No user config — appliance infra.
