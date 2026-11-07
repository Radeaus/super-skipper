// Super Skipper: the "Add to Super Skipper" feature of the Tile card.
// A card feature is the official way to put an extra button under the controls
// of a media player on a dashboard (https://contributors.home-assistant.io/frontend/custom-ui/card-feature/).
// It shows what the player plays and opens the Super Skipper page, where the
// title or artist is added to a rule with one tap.

const TYPE = "super-skipper-add";
const PANEL_PATH = "/super-skipper";

const STRINGS = {
  en: { name: "Add to Super Skipper", idle: "Nothing is playing" },
  nl: { name: "Toevoegen aan Super Skipper", idle: "Er speelt niets" },
};

const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
  );

const PLAYING = new Set(["playing", "buffering"]);

class SuperSkipperAddFeature extends HTMLElement {
  static getStubConfig() {
    return { type: `custom:${TYPE}` };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${STYLES}</style><button type="button" part="button"></button>`;
    this.shadowRoot.querySelector("button").addEventListener("click", (ev) => this._open(ev));
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  set context(context) {
    this._context = context;
    this._render();
  }

  // Older frontends pass the state instead of the context.
  set stateObj(stateObj) {
    this._stateObj = stateObj;
    this._render();
  }

  _entityId() {
    return this._context?.entity_id || this._stateObj?.entity_id;
  }

  _state() {
    const entityId = this._entityId();
    return (entityId && this._hass?.states?.[entityId]) || this._stateObj;
  }

  _t(key) {
    const language = (this._hass?.language || "en").split("-")[0];
    return (STRINGS[language] || STRINGS.en)[key];
  }

  _render() {
    const button = this.shadowRoot.querySelector("button");
    const state = this._state();
    const admin = this._hass?.user?.is_admin !== false;
    if (!state || !admin) {
      this.style.display = "none";
      return;
    }
    this.style.display = "";
    const playing = PLAYING.has(state.state);
    const attributes = state.attributes || {};
    const parts = [attributes.media_artist, attributes.media_title].filter(Boolean);
    const now = playing ? parts.join(" – ") || attributes.media_channel || "" : "";
    button.disabled = !playing || !now;
    button.innerHTML = `<ha-icon icon="mdi:skip-next-circle-outline"></ha-icon><span class="text"><span class="label">${esc(
      this._t("name")
    )}</span><span class="now">${esc(now || this._t("idle"))}</span></span>`;
  }

  _open(ev) {
    // Otherwise the tile opens the more-info dialog as well.
    ev.stopPropagation();
    const entityId = this._entityId();
    if (!entityId) return;
    const path = `${PANEL_PATH}/add/${encodeURIComponent(entityId)}`;
    history.pushState(null, "", path);
    window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
  }
}

const STYLES = `
:host { display: block; }
button {
  display: flex; align-items: center; gap: 12px; width: 100%; min-height: var(--feature-height, 42px);
  padding: 0 12px; border: none; border-radius: var(--feature-border-radius, 12px);
  background: color-mix(in srgb, var(--feature-color, var(--primary-color)) 20%, transparent);
  color: var(--primary-text-color); font: inherit; text-align: start; cursor: pointer;
  transition: background 180ms ease-in-out;
}
button:hover:not(:disabled) { background: color-mix(in srgb, var(--feature-color, var(--primary-color)) 30%, transparent); }
button:focus-visible { outline: 2px solid var(--feature-color, var(--primary-color)); outline-offset: 2px; }
button:disabled { cursor: default; opacity: 0.6; }
ha-icon { color: var(--feature-color, var(--primary-color)); flex: none; }
.text { display: flex; flex-direction: column; min-width: 0; line-height: 1.3; padding: 6px 0; }
.label { font-size: var(--ha-font-size-m, 14px); font-weight: var(--ha-font-weight-medium, 500); }
.now { font-size: var(--ha-font-size-s, 12px); color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
`;

if (!customElements.get(TYPE)) {
  customElements.define(TYPE, SuperSkipperAddFeature);
}

window.customCardFeatures = window.customCardFeatures || [];
if (!window.customCardFeatures.some((feature) => feature.type === TYPE)) {
  const supportsPlayer = (entityId) => !!entityId && entityId.startsWith("media_player.");
  window.customCardFeatures.push({
    type: TYPE,
    name: "Add to Super Skipper",
    isSupported: (hass, context) => supportsPlayer(context?.entity_id) && !!hass?.states?.[context.entity_id],
    // Frontends before the context API ask with the state.
    supported: (stateObj) => supportsPlayer(stateObj?.entity_id),
    configurable: false,
  });
}
