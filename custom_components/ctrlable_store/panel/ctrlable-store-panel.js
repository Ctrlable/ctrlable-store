// Ctrlable Store — appliance panel. Vanilla custom element; talks to the
// ctrlable_store websocket API. HA assigns `.hass`.
class CtrlableStorePanel extends HTMLElement {
  set hass(hass) { this._hass = hass; if (!this._init) { this._init = true; this._render(); this._load(); } }

  async _ws(msg) { return this._hass.connection.sendMessagePromise(msg); }

  _render() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;font-family:Inter,system-ui,sans-serif;background:#0F1216;color:#E7ECF3;min-height:100%}
        .wrap{max-width:900px;margin:0 auto;padding:24px}
        h1{font-size:20px;margin:0 0 4px}.sub{color:#8A94A6;font-size:13px;margin-bottom:20px}
        .card{background:#161B22;border:1px solid #232a33;border-radius:12px;padding:16px;margin-bottom:12px;display:flex;align-items:center;gap:16px}
        .meta{flex:1}.name{font-weight:600}.ver{color:#8A94A6;font-size:13px}
        .badge{font-size:11px;padding:2px 8px;border-radius:999px;background:#23304a;color:#9cc1ff;margin-left:8px}
        .badge.brk{background:#3a2330;color:#ff9cb0}
        button{background:#4C8DFF;color:#fff;border:0;border-radius:8px;padding:8px 16px;font-weight:600;cursor:pointer}
        button.sec{background:#232a33;color:#E7ECF3}button:disabled{opacity:.5;cursor:default}
        .ok{color:#5fd08a}.warn{color:#ffcf6b}.err{color:#ff7a7a}
        .bar{background:#161B22;border:1px solid #232a33;border-radius:10px;padding:12px 16px;margin-bottom:16px;display:none}
      </style>
      <div class="wrap">
        <h1>Ctrlable Store</h1>
        <div class="sub" id="sub">Licensed components for this appliance.</div>
        <div class="bar" id="bar"></div>
        <div id="list"></div>
      </div>`;
    this.shadowRoot.getElementById("bar").addEventListener("click", (e) => {
      if (e.target.dataset.act === "restart") this._restart();
    });
  }

  async _load() {
    const list = this.shadowRoot.getElementById("list");
    list.innerHTML = `<div class="sub">Loading…</div>`;
    let res;
    try { res = await this._ws({ type: "ctrlable_store/catalog" }); }
    catch (e) { list.innerHTML = `<div class="err">Failed to load catalog: ${e.message || e}</div>`; return; }
    if (!res.configured) {
      list.innerHTML = `<div class="warn">This appliance isn't enrolled yet (no device token). Install/enroll the Ctrlable agent first.</div>`;
      return;
    }
    if (!res.products.length) { list.innerHTML = `<div class="sub">No licensed products for this instance.</div>`; return; }
    list.innerHTML = res.products.map((p) => this._row(p)).join("");
    this.shadowRoot.querySelectorAll("button[data-install]").forEach((b) =>
      b.addEventListener("click", () => this._install(b.dataset.install, b)));
  }

  _row(p) {
    const action = !p.installed ? "Install" : (p.update_available ? "Update" : "Up to date");
    const dis = (p.installed && !p.update_available) ? "disabled" : "";
    const cur = p.installed ? ` · installed ${p.installed_version}` : "";
    const brk = p.breaking ? `<span class="badge brk">breaking</span>` : "";
    return `<div class="card">
      <div class="meta"><div class="name">${p.product}${brk}</div>
        <div class="ver">v${p.version}${cur}${p.changelog ? " — " + p.changelog : ""}</div></div>
      <button data-install="${p.product}" ${dis}>${action}</button></div>`;
  }

  async _install(product, btn) {
    btn.disabled = true; btn.textContent = "Installing…";
    try {
      const r = await this._ws({ type: "ctrlable_store/install", product });
      btn.textContent = `Installed ${r.version}`;
      if (r.restart_required) this._showRestart(`${product} ${r.version} installed — restart to apply.`);
    } catch (e) {
      btn.disabled = false; btn.textContent = "Retry";
      this._showRestart(`Install failed: ${e.message || e}`, false);
    }
  }

  _showRestart(text, restart = true) {
    const bar = this.shadowRoot.getElementById("bar");
    bar.style.display = "block";
    bar.innerHTML = `<span class="${restart ? "ok" : "err"}">${text}</span>` +
      (restart ? ` <button class="sec" data-act="restart" style="margin-left:12px">Restart now</button>` : "");
  }

  async _restart() {
    const bar = this.shadowRoot.getElementById("bar");
    bar.innerHTML = `<span class="warn">Restarting Home Assistant…</span>`;
    try { await this._ws({ type: "ctrlable_store/restart" }); } catch (e) {}
  }
}
customElements.define("ctrlable-store-panel", CtrlableStorePanel);
