// Super Skipper: the sidebar page that lists the rules and edits them.
// Plain web component, no build step. It is built from Home Assistant's own
// components (ha-card, ha-button, ha-form, ha-switch, ...) and design tokens,
// following https://contributors.home-assistant.io/design/. The field labels
// and help texts come from the integration's translations, so the page and the
// wizard in Settings always say the same thing.

const DOMAIN = "super_skipper";
const PANEL_PATH = "/super-skipper";

const STRINGS = {
  en: {
    title: "Super Skipper",
    back: "Back",
    save: "Save",
    saved: "Saved",
    cancel: "Cancel",
    rules: "Rules",
    create_rule: "Create rule",
    edit_rule: "Edit rule",
    empty_title: "No rules yet",
    empty_text:
      "Create a rule with the keywords to look for, the players to watch, and what to do when a keyword plays.",
    enabled: "Enabled",
    disabled: "Off",
    snooze: "Snooze",
    snooze_text: "Pause every rule for a while, for example during a party.",
    snooze_button: "Snooze for {minutes} minutes",
    snoozed_until: "Every rule is paused until {time}.",
    resume: "Resume",
    settings: "Settings",
    last_match: "Last match",
    last_match_none: "This rule has not acted yet.",
    last_match_text: "{description} on {player}",
    matches: "{count} times in total",
    delete_rule: "Delete rule",
    delete_text: "The rule and its entities are removed. This cannot be undone.",
    delete_confirm: "Delete {name}?",
    fix_errors: "Check the fields marked below.",
    error: "Something went wrong: {error}",
    not_loaded: "Super Skipper is not running. Check the integration page for errors.",
    not_configured: "Super Skipper is not set up yet. Add it under Settings > Devices & services.",
    open_integration: "Open integration page",
    players: "Players",
    keywords: "Keywords",
    unknown_rule: "This rule does not exist (anymore).",
    debug: "Debug logging",
    debug_text:
      "Writes every track the players report and every decision to the Home Assistant log, until the next restart. Turn it on when a rule does something unexpected.",
    debug_unavailable: "Debug logging needs the logger integration, which is part of the default configuration.",
    open_logs: "Open logs",
  },
  nl: {
    title: "Super Skipper",
    back: "Terug",
    save: "Opslaan",
    saved: "Opgeslagen",
    cancel: "Annuleren",
    rules: "Regels",
    create_rule: "Regel maken",
    edit_rule: "Regel bewerken",
    empty_title: "Nog geen regels",
    empty_text:
      "Maak een regel met de trefwoorden om op te letten, de spelers om in de gaten te houden, en wat er moet gebeuren als een trefwoord speelt.",
    enabled: "Ingeschakeld",
    disabled: "Uit",
    snooze: "Sluimeren",
    snooze_text: "Pauzeer alle regels een tijdje, bijvoorbeeld tijdens een feestje.",
    snooze_button: "{minutes} minuten sluimeren",
    snoozed_until: "Alle regels zijn gepauzeerd tot {time}.",
    resume: "Hervatten",
    settings: "Instellingen",
    last_match: "Laatste match",
    last_match_none: "Deze regel heeft nog niets gedaan.",
    last_match_text: "{description} op {player}",
    matches: "{count} keer in totaal",
    delete_rule: "Regel verwijderen",
    delete_text: "De regel en zijn entiteiten worden verwijderd. Dit kan niet ongedaan worden gemaakt.",
    delete_confirm: "{name} verwijderen?",
    fix_errors: "Controleer de gemarkeerde velden hieronder.",
    error: "Er ging iets mis: {error}",
    not_loaded: "Super Skipper draait niet. Kijk op de integratiepagina wat er mis is.",
    not_configured: "Super Skipper is nog niet ingesteld. Voeg het toe onder Instellingen > Apparaten & diensten.",
    open_integration: "Integratiepagina openen",
    players: "Spelers",
    keywords: "Trefwoorden",
    unknown_rule: "Deze regel bestaat niet (meer).",
    debug: "Debug-logging",
    debug_text:
      "Schrijft elk nummer dat de spelers melden en elke beslissing naar het logboek van Home Assistant, tot de volgende herstart. Zet dit aan als een regel iets onverwachts doet.",
    debug_unavailable: "Debug-logging heeft de logger-integratie nodig; die hoort bij de standaardconfiguratie.",
    open_logs: "Log openen",
  },
};

const ACTION_ICONS = { skip: "mdi:skip-next", switch: "mdi:radio", mute: "mdi:volume-off" };
const ACTIONS = ["skip", "switch", "mute"];
const MATCH_MODES = ["whole_word", "substring", "regex"];
const MATCH_FIELDS = ["title", "artist", "album", "channel"];
const REPEAT_MODES = ["limited", "unlimited", "once"];
const PRESENCE_MODES = ["any_home", "all_home", "none_home"];

const DEFAULT_RULE = {
  name: "",
  keywords: [],
  players: [],
  action: "skip",
  match_mode: "whole_word",
  match_fields: ["title", "artist"],
  ignore_texts: [],
  max_consecutive: 5,
  return_after_minutes: 5,
  repeat_mode: "limited",
  repeat_limit: 5,
  hold_seconds: 20,
  max_mute_minutes: 10,
  persons: [],
  presence_mode: "any_home",
  conditions: [],
};

// Where each field's label and help text live in the translations.
const FIELD_PATHS = {
  name: "step.basics.data.name",
  keywords: "step.basics.data.keywords",
  players: "step.basics.data.players",
  action: "step.basics.data.action",
  match_mode: "step.basics.sections.matching.data.match_mode",
  match_fields: "step.basics.sections.matching.data.match_fields",
  ignore_texts: "step.basics.sections.matching.data.ignore_texts",
  max_consecutive: "step.skip.data.max_consecutive",
  station: "step.switch.data.station",
  station_actions: "step.switch.data.station_actions",
  return_after_minutes: "step.switch.data.return_after_minutes",
  return_fallback_media: "step.switch.data.return_fallback_media",
  return_fallback_actions: "step.switch.data.return_fallback_actions",
  repeat_mode: "step.switch.data.repeat_mode",
  repeat_limit: "step.switch.data.repeat_limit",
  hold_seconds: "step.mute.data.hold_seconds",
  max_mute_minutes: "step.mute.data.max_mute_minutes",
  persons: "step.conditions.data.persons",
  presence_mode: "step.conditions.data.presence_mode",
  conditions: "step.conditions.sections.advanced.data.conditions",
};

const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
  );
const icon = (name, slot = "") =>
  `<ha-icon ${slot ? `slot="${slot}"` : ""} icon="${esc(name)}"></ha-icon>`;
// Help texts are written in Markdown for the wizard; the form shows plain text.
const plain = (text) => String(text ?? "").replace(/\*\*/g, "").replace(/`/g, "");

// Home Assistant only loads most of its components when a page needs them.
// Load the configuration panel once, which defines the form components we use.
const NEEDED = ["ha-card", "ha-button", "ha-alert", "ha-switch", "ha-spinner", "ha-icon-button", "ha-form"];

let componentsLoaded;
const loadComponents = () => {
  if (!componentsLoaded) componentsLoaded = doLoadComponents();
  return componentsLoaded;
};

async function doLoadComponents() {
  const ready = () => NEEDED.every((tag) => customElements.get(tag));
  if (ready()) return;
  try {
    await customElements.whenDefined("partial-panel-resolver");
    const resolver = document.createElement("partial-panel-resolver");
    resolver.hass = { panels: [{ url_path: "tmp", component_name: "config" }] };
    resolver._updateRoutes();
    await resolver.routerOptions.routes.tmp.load();
    await customElements.whenDefined("ha-panel-config");
    const config = document.createElement("ha-panel-config");
    await config.routerOptions.routes.script.load();
    if (!customElements.get("ha-form")) {
      await config.routerOptions.routes.helpers?.load?.();
    }
    if (!customElements.get("ha-form") && window.loadCardHelpers) {
      await window.loadCardHelpers();
      await customElements.get("hui-entities-card")?.getConfigElement?.();
    }
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn("Super Skipper: could not preload components", err);
  }
  await Promise.race([
    Promise.all(NEEDED.map((tag) => customElements.whenDefined(tag))),
    new Promise((resolve) => setTimeout(resolve, 8000)),
  ]);
}

class SuperSkipperPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = null;
    this._stateJson = "";
    this._path = "";
    this._routeSet = false;
    this._ready = false;
    this._translated = false;
    this._draft = null;
    this._draftId = undefined;
    this._errors = {};
    this._placeholders = {};
    this._optionsDraft = null;
    this._confirmDelete = false;
    this._notice = null;
    this._busy = new Set();
    this._unsubs = {};
    this._ruleForm = null;
    this._optionsForm = null;
    this._debug = null;
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
    loadComponents().then(() => {
      this._ready = true;
      this._render();
    });
  }

  // Properties Home Assistant sets on custom panels.

  set hass(hass) {
    const first = !this._hass;
    const language = hass?.language;
    this._hass = hass;
    for (const el of this.shadowRoot.querySelectorAll("ha-menu-button")) el.hass = hass;
    if (this._ruleForm) this._ruleForm.hass = hass;
    if (this._optionsForm) this._optionsForm.hass = hass;
    if (first) {
      this._subscribe();
      this._loadTranslations();
      this._loadDebug();
      this._render();
      return;
    }
    if (language !== this._language) {
      this._language = language;
      this._loadTranslations();
    }
    // The labels appear once the translations are in; render again then.
    if (!this._translated && this._localize(`config_subentries.rule.entry_type`)) {
      this._translated = true;
      this._render();
    }
  }

  get hass() {
    return this._hass;
  }

  set narrow(value) {
    this._narrow = value;
    for (const el of this.shadowRoot.querySelectorAll("ha-menu-button")) el.narrow = value;
  }

  set route(route) {
    const before = this._path;
    const first = !this._routeSet;
    this._routeSet = true;
    this._path = route?.path || "";
    if (first || before !== this._path) this._routeChanged();
  }

  set panel(_panel) {}

  connectedCallback() {
    if (this._hass && !this._unsubs.state) this._subscribe();
  }

  disconnectedCallback() {
    for (const key of Object.keys(this._unsubs)) this._unsub(key);
  }

  // Helpers

  _lang() {
    return (this._hass?.language || "en").split("-")[0];
  }

  _t(key, vars = {}) {
    const table = STRINGS[this._lang()] || STRINGS.en;
    const text = table[key] ?? STRINGS.en[key] ?? key;
    return text.replace(/\{(\w+)\}/g, (_, name) => vars[name] ?? "");
  }

  _localize(path, vars = {}) {
    const text = this._hass?.localize?.(`component.${DOMAIN}.${path}`) || "";
    return text.replace(/\{(\w+)\}/g, (_, name) => vars[name] ?? "");
  }

  _fieldLabel(name) {
    const path = FIELD_PATHS[name];
    return (path && this._localize(`config_subentries.rule.${path}`)) || name;
  }

  _fieldHelper(name) {
    const path = FIELD_PATHS[name];
    if (!path) return "";
    return plain(this._localize(`config_subentries.rule.${path.replace(".data.", ".data_description.")}`));
  }

  _option(key, value) {
    return this._localize(`selector.${key}.options.${value}`) || value;
  }

  async _loadTranslations() {
    if (!this._hass?.loadBackendTranslation) return;
    this._language = this._hass.language;
    try {
      await Promise.all(
        ["config_subentries", "options", "selector"].map((category) =>
          this._hass.loadBackendTranslation(category, DOMAIN)
        )
      );
    } catch (_err) {
      // The page still works, with the field names as labels.
    }
    this._translated = true;
    this._render();
  }

  _debugAvailable() {
    return (this._hass?.config?.components || []).includes("logger");
  }

  async _loadDebug() {
    if (!this._debugAvailable()) return;
    try {
      const info = await this._hass.callWS({ type: "logger/log_info" });
      const entry = info.find((item) => item.domain === DOMAIN);
      const debug = !!entry && entry.level > 0 && entry.level <= 10;
      if (debug !== this._debug) {
        this._debug = debug;
        this._render();
      }
    } catch (_err) {
      // Leave the switch as it is.
    }
  }

  async _setDebug(enabled) {
    await this._run("debug", async () => {
      await this._hass.callWS({
        type: "logger/integration_log_level",
        integration: DOMAIN,
        level: enabled ? "DEBUG" : "NOTSET",
        persistence: "once",
      });
      this._debug = enabled;
    });
    this._loadDebug();
  }

  _navigate(path, replace = false) {
    const url = PANEL_PATH + path;
    if (replace) history.replaceState(null, "", url);
    else history.pushState(null, "", url);
    window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace } }));
  }

  _ws(type, data = {}) {
    return this._hass.callWS({ type: `${DOMAIN}/${type}`, ...data });
  }

  async _sub(key, type, data, callback) {
    this._unsub(key);
    const promise = this._hass.connection.subscribeMessage(callback, { type: `${DOMAIN}/${type}`, ...data });
    this._unsubs[key] = promise;
    try {
      await promise;
    } catch (err) {
      if (this._unsubs[key] === promise) delete this._unsubs[key];
      throw err;
    }
  }

  _unsub(key) {
    const promise = this._unsubs[key];
    if (!promise) return;
    delete this._unsubs[key];
    promise.then((unsub) => unsub()).catch(() => {});
  }

  _subscribe() {
    this._sub("state", "subscribe", {}, (state) => {
      const json = JSON.stringify(state);
      if (json === this._stateJson) return;
      this._stateJson = json;
      this._state = state;
      this._stateChanged();
    }).catch((err) => {
      this._state = { configured: false, error: err.message };
      this._render();
    });
  }

  _view() {
    const match = this._path.match(/^\/rule\/([^/]+)/);
    if (match) {
      const id = decodeURIComponent(match[1]);
      return { name: "rule", id: id === "new" ? null : id };
    }
    return { name: "overview" };
  }

  _rule(id) {
    return this._state?.rules?.find((r) => r.id === id);
  }

  _playerName(entityId) {
    return this._hass?.states?.[entityId]?.attributes?.friendly_name || entityId;
  }

  async _run(key, fn) {
    this._busy.add(key);
    this._render();
    try {
      await fn();
    } catch (err) {
      this._notice = { type: "error", text: this._t("error", { error: err?.message || err?.code || err }) };
    } finally {
      this._busy.delete(key);
      this._render();
    }
  }

  // Reacting to changes

  _routeChanged() {
    this._notice = null;
    this._errors = {};
    this._confirmDelete = false;
    this._draft = null;
    this._draftId = undefined;
    this._prepareDraft();
    this._render();
  }

  _stateChanged() {
    this._prepareDraft();
    this._render();
  }

  _prepareDraft() {
    const view = this._view();
    if (view.name !== "rule" || !this._state?.configured) return;
    if (this._draftId === view.id && this._draft) return;
    if (view.id === null) {
      this._draft = { ...DEFAULT_RULE };
      this._draftId = null;
      return;
    }
    const rule = this._rule(view.id);
    if (!rule) return;
    this._draft = { ...DEFAULT_RULE, ...JSON.parse(JSON.stringify(rule.data)) };
    this._draftId = view.id;
  }

  // Events

  _onClick(ev) {
    const el = ev.composedPath().find((node) => node.dataset?.action);
    if (!el || el.disabled || el.hasAttribute?.("loading")) return;
    ev.preventDefault();
    this._action(el.dataset.action, el.dataset);
  }

  _onChange(ev) {
    const target = ev.composedPath().find((node) => node.dataset?.field);
    if (!target) return;
    if (target.dataset.field === "debug") {
      ev.stopPropagation();
      this._setDebug(target.checked);
      return;
    }
    if (target.dataset.field !== "enabled") return;
    ev.stopPropagation();
    const enabled = target.checked;
    this._run("enabled" + target.dataset.id, () =>
      this._ws("set_enabled", { subentry_id: target.dataset.id, enabled })
    );
  }

  async _action(action, data) {
    switch (action) {
      case "home":
        this._navigate("");
        return;
      case "create":
        this._navigate("/rule/new");
        return;
      case "edit":
        this._navigate(`/rule/${encodeURIComponent(data.id)}`);
        return;
      case "snooze":
        await this._run("snooze", () => this._ws("snooze"));
        return;
      case "unsnooze":
        await this._run("snooze", () => this._ws("unsnooze"));
        return;
      case "save-options":
        await this._run("options", async () => {
          await this._ws("save_options", { options: this._optionsDraft || this._state.options });
          this._optionsDraft = null;
          this._notice = { type: "success", text: this._t("saved") };
        });
        return;
      case "save-rule":
        await this._saveRule();
        return;
      case "delete-ask":
        this._confirmDelete = true;
        this._render();
        return;
      case "delete-cancel":
        this._confirmDelete = false;
        this._render();
        return;
      case "delete":
        await this._run("delete", async () => {
          await this._ws("delete_rule", { subentry_id: data.id });
          this._navigate("");
        });
        return;
      default:
        return;
    }
  }

  async _saveRule() {
    const view = this._view();
    await this._run("save", async () => {
      const payload = { data: this._draft };
      if (view.id) payload.subentry_id = view.id;
      const result = await this._ws("save_rule", payload);
      if (result?.errors) {
        this._errors = result.errors;
        this._placeholders = result.placeholders || {};
        this._notice = { type: "error", text: this._t("fix_errors") };
        return;
      }
      this._errors = {};
      this._navigate("");
      this._notice = { type: "success", text: this._t("saved") };
    });
  }

  // The rule form

  _ruleSchema(draft) {
    const select = (key, values, multiple = false) => ({
      select: {
        mode: multiple ? "dropdown" : "list",
        multiple,
        options: values.map((value) => ({ value, label: this._option(key, value) })),
      },
    });
    const number = (min, max, unit, step = 1) => ({
      number: { min, max, step, mode: "box", ...(unit ? { unit_of_measurement: unit } : {}) },
    });
    const sectionTitle = (step, section) =>
      this._localize(`config_subentries.rule.step.${step}.sections.${section}.name`) || section;
    const hasError = (...names) => names.some((name) => this._errors[name]);

    const action = ACTIONS.includes(draft.action) ? draft.action : "skip";
    const specific = {
      skip: [{ name: "max_consecutive", selector: number(0, 50) }],
      switch: [
        { name: "station", selector: { media: {} } },
        { name: "station_actions", selector: { action: {} } },
        { name: "return_after_minutes", required: true, selector: number(0, 1440, "min") },
        { name: "return_fallback_media", selector: { media: {} } },
        { name: "return_fallback_actions", selector: { action: {} } },
        { name: "repeat_mode", required: true, selector: select("repeat_mode", REPEAT_MODES) },
        { name: "repeat_limit", required: true, selector: number(1, 50) },
      ],
      mute: [
        { name: "hold_seconds", required: true, selector: number(0, 300, "s") },
        { name: "max_mute_minutes", required: true, selector: number(0, 180, "min") },
      ],
    }[action];

    return [
      { name: "name", required: true, selector: { text: {} } },
      { name: "keywords", required: true, selector: { text: { multiple: true } } },
      { name: "players", required: true, selector: { entity: { domain: "media_player", multiple: true } } },
      { name: "action", required: true, selector: select("action", ACTIONS) },
      ...specific,
      {
        name: "matching",
        type: "expandable",
        flatten: true,
        title: sectionTitle("basics", "matching"),
        expanded: hasError("match_mode", "match_fields", "ignore_texts"),
        schema: [
          { name: "match_mode", required: true, selector: select("match_mode", MATCH_MODES) },
          { name: "match_fields", required: true, selector: select("match_fields", MATCH_FIELDS, true) },
          { name: "ignore_texts", selector: { text: { multiple: true } } },
        ],
      },
      {
        name: "when",
        type: "expandable",
        flatten: true,
        title: this._localize("config_subentries.rule.step.conditions.title") || "Conditions",
        expanded: hasError("persons", "presence_mode", "conditions"),
        schema: [
          { name: "persons", selector: { entity: { domain: "person", multiple: true } } },
          { name: "presence_mode", required: true, selector: select("presence_mode", PRESENCE_MODES) },
          { name: "conditions", selector: { condition: {} } },
        ],
      },
    ];
  }

  _mountRuleForm(host) {
    if (!host || !this._draft) return;
    if (!this._ruleForm) {
      const form = document.createElement("ha-form");
      form.computeLabel = (schema) => this._fieldLabel(schema.name);
      form.computeHelper = (schema) => this._fieldHelper(schema.name);
      form.computeError = (error) =>
        this._localize(`config_subentries.rule.error.${error}`, this._placeholders) || error;
      form.addEventListener("value-changed", (ev) => {
        ev.stopPropagation();
        const value = ev.detail.value || {};
        const actionChanged = value.action !== this._draft?.action;
        this._draft = value;
        form.data = value;
        if (actionChanged) form.schema = this._ruleSchema(value);
        const title = this.shadowRoot.querySelector(".main-title");
        if (title) title.textContent = this._ruleTitle();
      });
      this._ruleForm = form;
    }
    const form = this._ruleForm;
    form.hass = this._hass;
    form.schema = this._ruleSchema(this._draft);
    form.data = this._draft;
    form.error = this._errors;
    form.disabled = this._busy.has("save");
    host.appendChild(form);
  }

  _mountOptionsForm(host) {
    if (!host) return;
    if (!this._optionsForm) {
      const form = document.createElement("ha-form");
      form.computeLabel = (schema) => this._localize(`options.step.init.data.${schema.name}`) || schema.name;
      form.computeHelper = (schema) => plain(this._localize(`options.step.init.data_description.${schema.name}`));
      form.addEventListener("value-changed", (ev) => {
        ev.stopPropagation();
        this._optionsDraft = ev.detail.value;
        form.data = this._optionsDraft;
      });
      form.schema = [
        { name: "snooze_minutes", required: true, selector: { number: { min: 1, max: 1440, mode: "box", unit_of_measurement: "min" } } },
        { name: "cooldown_seconds", required: true, selector: { number: { min: 0, max: 120, mode: "box", unit_of_measurement: "s" } } },
        { name: "confirm_seconds", required: true, selector: { number: { min: 0, max: 30, step: 0.5, mode: "box", unit_of_measurement: "s" } } },
      ];
      this._optionsForm = form;
    }
    const form = this._optionsForm;
    form.hass = this._hass;
    form.data = this._optionsDraft || this._state.options;
    form.disabled = this._busy.has("options");
    host.appendChild(form);
  }

  _ruleTitle() {
    const view = this._view();
    if (view.id === null) return this._draft?.name || this._t("create_rule");
    return this._draft?.name || this._rule(view.id)?.title || this._t("edit_rule");
  }

  // Rendering

  _render() {
    if (!this._hass) return;
    const view = this._view();
    let body;
    if (!this._state || !this._ready) body = this._loading();
    else if (!this._state.configured) body = this._message(this._t("not_configured"));
    else if (view.name === "rule") body = this._renderRule(view);
    else body = this._renderOverview();
    if (view.name !== "rule") this._ruleForm = null;
    this.shadowRoot.innerHTML = `<style>${STYLES}</style>${body}`;
    for (const el of this.shadowRoot.querySelectorAll("ha-menu-button")) {
      el.hass = this._hass;
      el.narrow = this._narrow;
    }
    this._mountRuleForm(this.shadowRoot.getElementById("rule-form"));
    this._mountOptionsForm(this.shadowRoot.getElementById("options-form"));
  }

  _toolbar(title, { back = false } = {}) {
    const lead = back
      ? `<ha-icon-button data-action="home" label="${esc(this._t("back"))}">${icon("mdi:arrow-left")}</ha-icon-button>`
      : `<ha-menu-button></ha-menu-button>`;
    return `<div class="toolbar">${lead}<div class="main-title">${esc(title)}</div></div>`;
  }

  _loading() {
    return `${this._toolbar(this._t("title"))}<div class="content center"><ha-spinner></ha-spinner></div>`;
  }

  _message(text) {
    return `${this._toolbar(this._t("title"))}<div class="content"><div class="container">${this._alert("warning", esc(text), {
      actions: this._link(this._t("open_integration"), "/config/integrations/integration/" + DOMAIN),
    })}</div></div>`;
  }

  _alert(type, text, { title = "", actions = "" } = {}) {
    return `<ha-alert alert-type="${type}" ${title ? `title="${esc(title)}"` : ""}>${text}${
      actions ? `<div slot="action" class="alert-actions">${actions}</div>` : ""
    }</ha-alert>`;
  }

  _notices() {
    return this._notice ? this._alert(this._notice.type, esc(this._notice.text)) : "";
  }

  _button(label, action, { appearance = "accent", variant = "brand", busy = false, disabled = false, data = {}, iconName = null } = {}) {
    const attrs = Object.entries(data)
      .map(([k, v]) => `data-${k}="${esc(v)}"`)
      .join(" ");
    return `<ha-button appearance="${appearance}" variant="${variant}" data-action="${action}" ${attrs} ${disabled ? "disabled" : ""} ${busy ? "loading" : ""}>${
      iconName ? icon(iconName, "start") : ""
    }${esc(label)}</ha-button>`;
  }

  _link(label, href, { iconName = null } = {}) {
    return `<a class="button-link" href="${esc(href)}"><ha-button appearance="outlined" variant="brand">${
      iconName ? icon(iconName, "start") : ""
    }${esc(label)}</ha-button></a>`;
  }

  _formatTime(iso) {
    try {
      return new Date(iso).toLocaleString(this._hass.language || "en", { dateStyle: "medium", timeStyle: "short" });
    } catch (_err) {
      return iso;
    }
  }

  _ruleRow(rule) {
    const data = rule.data;
    const players = (data.players || []).map((p) => this._playerName(p)).join(", ");
    const keywords = (data.keywords || []).join(", ");
    const last = rule.last_match
      ? `<span class="supporting">${esc(this._t("last_match"))}: ${esc(
          this._t("last_match_text", { description: rule.last_match.description, player: this._playerName(rule.last_match.player) })
        )}</span>`
      : "";
    return `<div class="row ${rule.enabled ? "" : "muted"}">
      <button class="row-main" type="button" data-action="edit" data-id="${esc(rule.id)}">
        <span class="row-icon">${icon(ACTION_ICONS[data.action] || "mdi:music-note-off")}</span>
        <span class="row-text">
          <span class="headline">${esc(rule.title)}</span>
          <span class="supporting">${esc(this._option("action", data.action))} · ${esc(keywords)}</span>
          <span class="supporting">${esc(players)}</span>
          ${last}
        </span>
      </button>
      <span class="row-end">
        <ha-switch data-field="enabled" data-id="${esc(rule.id)}" ${rule.enabled ? "checked" : ""} ${this._busy.has("enabled" + rule.id) || !this._state.loaded ? "disabled" : ""} aria-label="${esc(this._t("enabled"))}"></ha-switch>
        <ha-icon-button data-action="edit" data-id="${esc(rule.id)}" label="${esc(this._t("edit_rule"))}">${icon("mdi:pencil-outline")}</ha-icon-button>
      </span>
    </div>`;
  }

  _renderOverview() {
    const state = this._state;
    const rules = state.rules.length
      ? `<ha-card header="${esc(this._t("rules"))}"><div class="list">${state.rules.map((r) => this._ruleRow(r)).join("")}</div>
         <div class="card-actions">${this._button(this._t("create_rule"), "create", { iconName: "mdi:plus" })}</div></ha-card>`
      : `<ha-card><div class="empty"><div class="empty-icon">${icon("mdi:skip-next-circle-outline")}</div>
         <h2>${esc(this._t("empty_title"))}</h2><p>${esc(this._t("empty_text"))}</p>
         ${this._button(this._t("create_rule"), "create", { iconName: "mdi:plus" })}</div></ha-card>`;
    const snoozed = state.snoozed_until && new Date(state.snoozed_until) > new Date();
    const snooze = snoozed
      ? `<div class="card-content">${this._alert("info", esc(this._t("snoozed_until", { time: this._formatTime(state.snoozed_until) })), {
          actions: this._button(this._t("resume"), "unsnooze", { appearance: "plain", busy: this._busy.has("snooze") }),
        })}</div>`
      : `<p class="card-text">${esc(this._t("snooze_text"))}</p>
         <div class="card-actions start">${this._button(this._t("snooze_button", { minutes: state.options.snooze_minutes }), "snooze", {
           appearance: "outlined",
           iconName: "mdi:sleep",
           busy: this._busy.has("snooze"),
           disabled: !state.loaded,
         })}</div>`;
    return `${this._toolbar(this._t("title"))}
      <div class="content"><div class="container">
        ${state.loaded ? "" : this._alert("warning", esc(this._t("not_loaded")) + (state.reason ? `<br>${esc(state.reason)}` : ""))}
        ${this._notices()}
        ${rules}
        <ha-card header="${esc(this._t("snooze"))}">${snooze}</ha-card>
        <ha-card header="${esc(this._t("settings"))}">
          <div class="card-content"><div id="options-form"></div></div>
          <div class="card-actions">${this._button(this._t("save"), "save-options", { busy: this._busy.has("options"), disabled: !this._optionsDraft })}</div>
        </ha-card>
        ${this._debugCard()}
      </div></div>`;
  }

  _debugCard() {
    if (!this._debugAvailable()) {
      return `<ha-card header="${esc(this._t("debug"))}"><p class="card-text last">${esc(this._t("debug_unavailable"))}</p></ha-card>`;
    }
    return `<ha-card header="${esc(this._t("debug"))}">
      <div class="row">
        <div class="row-main static">
          <span class="row-icon">${icon("mdi:bug-outline")}</span>
          <span class="row-text"><span class="headline">${esc(this._t("debug"))}</span><span class="supporting">${esc(this._t("debug_text"))}</span></span>
        </div>
        <span class="row-end"><ha-switch data-field="debug" ${this._debug ? "checked" : ""} ${this._busy.has("debug") || this._debug === null ? "disabled" : ""} aria-label="${esc(this._t("debug"))}"></ha-switch></span>
      </div>
      <div class="card-actions">${this._link(this._t("open_logs"), "/config/logs?domain=" + DOMAIN, { iconName: "mdi:text-box-search-outline" })}</div>
    </ha-card>`;
  }

  _renderRule(view) {
    const rule = view.id ? this._rule(view.id) : null;
    if (view.id && !rule) {
      return `${this._toolbar(this._t("title"), { back: true })}<div class="content"><div class="container">${this._alert("warning", esc(this._t("unknown_rule")))}</div></div>`;
    }
    const errorList = Object.keys(this._errors).length
      ? this._alert(
          "error",
          `<ul class="errors">${Object.entries(this._errors)
            .map(([field, code]) => `<li><b>${esc(this._fieldLabel(field))}</b>: ${esc(this._localize(`config_subentries.rule.error.${code}`, this._placeholders) || code)}</li>`)
            .join("")}</ul>`
        )
      : "";
    const lastMatch = rule
      ? `<ha-card header="${esc(this._t("last_match"))}"><div class="card-content last">${
          rule.last_match
            ? `<p>${esc(this._t("last_match_text", { description: rule.last_match.description, player: this._playerName(rule.last_match.player) }))}<br>
               <span class="hint">${esc(this._formatTime(rule.last_match.when))} · ${esc(this._t("matches", { count: rule.matches }))}</span></p>`
            : `<p class="hint">${esc(this._t("last_match_none"))}</p>`
        }</div></ha-card>`
      : "";
    const remove = rule
      ? `<ha-card header="${esc(this._t("delete_rule"))}"><p class="card-text">${esc(this._t("delete_text"))}</p>${
          this._confirmDelete
            ? `<div class="card-content">${this._alert("warning", "", {
                title: this._t("delete_confirm", { name: rule.title }),
                actions:
                  this._button(this._t("cancel"), "delete-cancel", { appearance: "plain" }) +
                  this._button(this._t("delete_rule"), "delete", { variant: "danger", data: { id: rule.id }, busy: this._busy.has("delete") }),
              })}</div>`
            : `<div class="card-actions">${this._button(this._t("delete_rule"), "delete-ask", { appearance: "plain", variant: "danger", iconName: "mdi:delete-outline" })}</div>`
        }</ha-card>`
      : "";
    return `${this._toolbar(this._ruleTitle(), { back: true })}
      <div class="content"><div class="container">
        ${this._state.loaded ? "" : this._alert("warning", esc(this._t("not_loaded")))}
        ${this._notices()}${errorList}
        <ha-card>
          <div class="card-content form"><div id="rule-form"></div></div>
          <div class="card-actions">${this._button(this._t("cancel"), "home", { appearance: "plain" })}${this._button(this._t("save"), "save-rule", { busy: this._busy.has("save") })}</div>
        </ha-card>
        ${lastMatch}${remove}
      </div></div>`;
  }
}

// Layout only; the components bring their own Home Assistant styling.
const STYLES = `
:host {
  display: block;
  min-height: 100%;
  background: var(--primary-background-color);
  color: var(--primary-text-color);
  font-family: var(--ha-font-family-body, Roboto, Noto, sans-serif);
  font-size: var(--ha-font-size-m, 14px);
  line-height: var(--ha-line-height-normal, 1.6);
  -webkit-font-smoothing: antialiased;
  --ss-space-1: var(--ha-space-1, 4px);
  --ss-space-2: var(--ha-space-2, 8px);
  --ss-space-3: var(--ha-space-3, 12px);
  --ss-space-4: var(--ha-space-4, 16px);
  --ss-space-6: var(--ha-space-6, 24px);
  --ss-space-8: var(--ha-space-8, 32px);
}
* { box-sizing: border-box; }
.toolbar {
  display: flex; align-items: center; gap: var(--ss-space-1);
  height: var(--header-height, 56px); padding: 0 var(--ss-space-1);
  background: var(--app-header-background-color, var(--primary-color));
  color: var(--app-header-text-color, var(--text-primary-color, #fff));
  border-bottom: var(--app-header-border-bottom, none);
  position: sticky; top: 0; z-index: 2;
}
.main-title {
  margin-inline-start: var(--ss-space-3); font-size: var(--ha-font-size-xl, 20px);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.content { padding: var(--ss-space-4); }
.content.center { display: flex; justify-content: center; padding-top: 20vh; }
.container { max-width: 760px; margin: 0 auto; display: flex; flex-direction: column; gap: var(--ss-space-4); }
ha-card { display: block; overflow: hidden; }
.card-content { padding: 0 var(--ss-space-4) var(--ss-space-2); }
.card-content.form { padding-top: var(--ss-space-2); }
.card-content.last p { margin: 0 0 var(--ss-space-2); }
.card-text { margin: 0; padding: 0 var(--ss-space-4) var(--ss-space-2); color: var(--secondary-text-color); }
.card-actions { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: var(--ss-space-2); padding: var(--ss-space-2) var(--ss-space-4) var(--ss-space-4); }
.card-actions.start { justify-content: flex-start; }
.empty { text-align: center; padding: var(--ss-space-8) var(--ss-space-6); }
.empty h2 { font-size: var(--ha-font-size-xl, 20px); font-weight: var(--ha-font-weight-medium, 500); margin: var(--ss-space-4) 0 var(--ss-space-2); }
.empty p { color: var(--secondary-text-color); margin: 0 auto var(--ss-space-6); max-width: 420px; }
.empty-icon { color: var(--secondary-text-color); --mdc-icon-size: 64px; }
.list { display: flex; flex-direction: column; }
.row { display: flex; align-items: center; gap: var(--ss-space-2); min-height: 56px; width: 100%; padding: 0 var(--ss-space-2) 0 0; }
.row.muted .row-main { opacity: 0.6; }
.row-main {
  flex: 1; display: flex; align-items: center; gap: var(--ss-space-4); min-width: 0;
  padding: var(--ss-space-2) var(--ss-space-4); border: none; background: none; color: inherit;
  font: inherit; text-align: start; cursor: pointer; border-radius: var(--ha-border-radius-md, 8px);
}
.row-main:hover { background: var(--secondary-background-color); }
.row-main.static { cursor: default; }
.row-main.static:hover { background: none; }
.card-text.last { padding-bottom: var(--ss-space-4); }
.row-main:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
.row-icon { color: var(--state-icon-color, var(--secondary-text-color)); display: flex; }
.row-text { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.headline { font-size: var(--ha-font-size-l, 16px); overflow: hidden; text-overflow: ellipsis; }
.supporting { color: var(--secondary-text-color); font-size: var(--ha-font-size-m, 14px); overflow-wrap: anywhere; }
.row-end { display: flex; align-items: center; gap: var(--ss-space-1); color: var(--secondary-text-color); flex: none; }
.row-end ha-icon-button { --mdc-icon-button-size: 40px; }
ha-alert { display: block; }
.alert-actions { display: flex; gap: var(--ss-space-2); flex-wrap: wrap; }
.alert-actions ha-button { white-space: nowrap; }
.errors { margin: 0; padding-inline-start: var(--ss-space-4); }
.hint { font-size: var(--ha-font-size-s, 12px); color: var(--secondary-text-color); }
a.button-link { text-decoration: none; }
ha-form { display: block; }
@media (max-width: 600px) {
  .content { padding: var(--ss-space-2); }
}
`;

if (!customElements.get("super-skipper-panel")) {
  customElements.define("super-skipper-panel", SuperSkipperPanel);
}
