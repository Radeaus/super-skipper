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
    activity: "Recent activity",
    activity_none: "Nothing happened yet. Activity shows up here as soon as the rule acts, with the reason.",
    debug: "Debug logging",
    debug_text:
      "Writes every track the players report and every decision to the Home Assistant log, until the next restart. Turn it on when a rule does something unexpected.",
    debug_unavailable: "Debug logging needs the logger integration, which is part of the default configuration.",
    open_logs: "Open logs",
    rules_text:
      "Rules are checked from top to bottom. When what plays matches more than one rule for the same player, only the first of them acts and the rules below leave the track alone. Drag a rule by its handle, or use the arrows, to change the order.",
    move_up: "Move up",
    move_down: "Move down",
    drag: "Drag to change the order",
    rule_intro:
      "A rule says which keywords to look for, on which players, and what to do when a keyword plays. Every field has a short explanation underneath it.",
    settings_text: "These settings apply to every rule.",
    now_playing: "Now playing",
    now_playing_text:
      "What the players of your rules play right now. Add the title or artist to a rule with a tap, without typing it.",
    now_playing_none: "None of the players is playing at the moment.",
    now_playing_tile:
      "The same button fits on a dashboard: add the feature “Add to Super Skipper” to a Tile card of a media player.",
    add_to_rule: "Add to rule",
    add_title: "Add to a rule",
    add_text:
      "Choose what to use as keyword, then pick the rule it belongs to. From then on the rule also acts when this plays again.",
    add_keywords: "Use as keyword",
    add_rules: "Add to this rule",
    add_rules_text: "Select a rule to add the keywords to it.",
    add_new_rule: "New rule with these keywords",
    add_also_player: "Also starts watching {player}",
    add_done: "Added {keywords} to {rule}.",
    add_exists: "{rule} already has these keywords.",
    add_pick_keyword: "Choose at least one keyword.",
    player_idle:
      "{player} is not playing anything right now. Start something and come back, or type the keyword in the rule yourself.",
    unknown_player: "This media player does not exist.",
    no_rules_yet: "There are no rules yet. Create one with these keywords.",
    section_auto_skip: "When a track plays: skip it",
    section_auto_switch: "When a radio stream plays: switch station, or mute without a station",
    section_skip: "Skipping",
    section_switch: "Switching station",
    section_mute: "Muting",
    action_auto:
      "Looks at what plays. A track is skipped; a radio stream switches to the station you choose below, or is muted until the keyword is gone when no station is set. The best choice for most rules.",
    action_skip: "Always goes to the next track. For Spotify, Music Assistant, Sonos queues and other players that can skip.",
    action_switch: "Always plays another station and returns to the previous one later. For radio.",
    action_mute: "Silences the player while the keyword plays and unmutes once something else has played for a moment.",
    match_mode_whole_word: "ABBA matches in “ABBA - Waterloo” but not in “Kabbalah”. Case and accents never matter.",
    match_mode_substring: "ABBA also matches in “Kabbalah”. Useful for word stems.",
    match_mode_regex: "Each keyword is a regular expression, for example ^Advert.*",
    repeat_mode_limited: "Switches again when the keyword still plays after returning, up to the limit below, then stays on the other station.",
    repeat_mode_unlimited: "Keeps switching as long as the keyword plays after returning.",
    repeat_mode_once: "Switches one time; after returning the rule leaves the player alone.",
    presence_mode_any_home: "The rule acts when at least one of the persons is home.",
    presence_mode_all_home: "The rule acts only when all of the persons are home.",
    presence_mode_none_home: "The rule acts only when none of the persons is home.",
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
    activity: "Recente activiteit",
    activity_none: "Er is nog niets gebeurd. Zodra de regel ingrijpt verschijnt het hier, met de reden.",
    debug: "Debug-logging",
    debug_text:
      "Schrijft elk nummer dat de spelers melden en elke beslissing naar het logboek van Home Assistant, tot de volgende herstart. Zet dit aan als een regel iets onverwachts doet.",
    debug_unavailable: "Debug-logging heeft de logger-integratie nodig; die hoort bij de standaardconfiguratie.",
    open_logs: "Log openen",
    rules_text:
      "Regels worden van boven naar beneden bekeken. Past wat er speelt bij meer dan één regel voor dezelfde speler, dan grijpt alleen de eerste in en laten de regels eronder het nummer met rust. Versleep een regel aan het handvat, of gebruik de pijltjes, om de volgorde te veranderen.",
    move_up: "Omhoog",
    move_down: "Omlaag",
    drag: "Sleep om de volgorde te veranderen",
    rule_intro:
      "Een regel zegt op welke trefwoorden je let, op welke spelers, en wat er gebeurt als een trefwoord speelt. Onder elk veld staat een korte uitleg.",
    settings_text: "Deze instellingen gelden voor alle regels.",
    now_playing: "Nu speelt",
    now_playing_text:
      "Wat de spelers van je regels nu spelen. Voeg de titel of artiest met één tik toe aan een regel, zonder typen.",
    now_playing_none: "Geen van de spelers speelt op dit moment iets.",
    now_playing_tile:
      "Dezelfde knop past op een dashboard: voeg de functie “Toevoegen aan Super Skipper” toe aan een tegelkaart van een mediaspeler.",
    add_to_rule: "Aan regel toevoegen",
    add_title: "Aan een regel toevoegen",
    add_text:
      "Kies wat je als trefwoord gebruikt en daarna de regel waar het bij hoort. Vanaf dan grijpt die regel ook in als dit weer speelt.",
    add_keywords: "Gebruik als trefwoord",
    add_rules: "Toevoegen aan deze regel",
    add_rules_text: "Kies een regel om de trefwoorden aan toe te voegen.",
    add_new_rule: "Nieuwe regel met deze trefwoorden",
    add_also_player: "Gaat ook op {player} letten",
    add_done: "{keywords} toegevoegd aan {rule}.",
    add_exists: "{rule} heeft deze trefwoorden al.",
    add_pick_keyword: "Kies minstens één trefwoord.",
    player_idle:
      "{player} speelt op dit moment niets. Start iets en kom terug, of typ het trefwoord zelf in de regel.",
    unknown_player: "Deze mediaspeler bestaat niet.",
    no_rules_yet: "Er zijn nog geen regels. Maak er een met deze trefwoorden.",
    section_auto_skip: "Als een nummer speelt: overslaan",
    section_auto_switch: "Als een radiostream speelt: andere zender, of dempen zonder zender",
    section_skip: "Overslaan",
    section_switch: "Andere zender",
    section_mute: "Dempen",
    action_auto:
      "Kijkt naar wat er speelt. Een nummer wordt overgeslagen; een radiostream gaat naar de zender die je hieronder kiest, of wordt gedempt tot het trefwoord weg is als er geen zender is. De beste keuze voor de meeste regels.",
    action_skip: "Gaat altijd naar het volgende nummer. Voor Spotify, Music Assistant, Sonos-wachtrijen en andere spelers die kunnen overslaan.",
    action_switch: "Speelt altijd een andere zender en keert later terug naar de vorige. Voor radio.",
    action_mute: "Zet het geluid uit zolang het trefwoord speelt en weer aan zodra er even iets anders heeft gespeeld.",
    match_mode_whole_word: "ABBA past in “ABBA - Waterloo” maar niet in “Kabbalah”. Hoofdletters en accenten maken nooit uit.",
    match_mode_substring: "ABBA past ook in “Kabbalah”. Handig voor woordstammen.",
    match_mode_regex: "Elk trefwoord is een reguliere expressie, bijvoorbeeld ^Reclame.*",
    repeat_mode_limited: "Schakelt opnieuw als het trefwoord na terugkeer nog speelt, tot de limiet hieronder, en blijft daarna op de andere zender.",
    repeat_mode_unlimited: "Blijft schakelen zolang het trefwoord na terugkeer speelt.",
    repeat_mode_once: "Schakelt één keer; na terugkeer laat de regel de speler met rust.",
    presence_mode_any_home: "De regel grijpt in als minstens één van de personen thuis is.",
    presence_mode_all_home: "De regel grijpt alleen in als alle personen thuis zijn.",
    presence_mode_none_home: "De regel grijpt alleen in als geen van de personen thuis is.",
  },
};

const ACTION_ICONS = { auto: "mdi:auto-fix", skip: "mdi:skip-next", switch: "mdi:radio", mute: "mdi:volume-off" };
const ACTIONS = ["auto", "skip", "switch", "mute"];
const MATCH_MODES = ["whole_word", "substring", "regex"];
const MATCH_FIELDS = ["title", "artist", "album", "channel"];
const REPEAT_MODES = ["limited", "unlimited", "once"];
const PRESENCE_MODES = ["any_home", "all_home", "none_home"];

const DEFAULT_RULE = {
  name: "",
  keywords: [],
  players: [],
  action: "auto",
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
// Nice to have: drag and drop for the rule list, and checkboxes on the add page.
const OPTIONAL = ["ha-sortable", "ha-checkbox"];
const PLAYING = new Set(["playing", "buffering"]);
const TRACK_FIELDS = { title: "media_title", artist: "media_artist", album: "media_album_name", channel: "media_channel" };

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
    this._prefill = null;
    this._add = null;
    this._playersSig = "";
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("keydown", (ev) => {
      if ((ev.key === " " || ev.key === "Enter") && ev.target?.dataset?.action === "toggle-keyword") this._onClick(ev);
    });
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
    loadComponents().then(() => {
      this._ready = true;
      this._render();
    });
    for (const tag of OPTIONAL) {
      customElements.whenDefined(tag).then(() => this._ready && this._render());
    }
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
      return;
    }
    const signature = this._playersSignature();
    if (signature === this._playersSig) return;
    this._playersSig = signature;
    const view = this._view();
    if (view.name === "add") this._render();
    else if (view.name === "overview") this._refreshNowPlaying();
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
    const add = this._path.match(/^\/add\/([^/]+)/);
    if (add) return { name: "add", player: decodeURIComponent(add[1]) };
    return { name: "overview" };
  }

  // What plays

  _watchedPlayers() {
    const players = [];
    for (const rule of this._state?.rules || []) {
      for (const player of rule.data.players || []) if (!players.includes(player)) players.push(player);
    }
    return players;
  }

  _nowPlaying(entityId) {
    const state = this._hass?.states?.[entityId];
    if (!state) return null;
    const attributes = state.attributes || {};
    const fields = {};
    for (const [field, attribute] of Object.entries(TRACK_FIELDS)) {
      if (attributes[attribute]) fields[field] = String(attributes[attribute]);
    }
    const parts = [fields.artist, fields.title].filter(Boolean);
    return {
      playing: PLAYING.has(state.state),
      fields,
      description: parts.join(" – ") || fields.channel || "",
    };
  }

  _playersSignature() {
    if (!this._state?.configured) return "";
    const view = this._view();
    const players = this._watchedPlayers();
    if (view.name === "add" && !players.includes(view.player)) players.push(view.player);
    return players
      .map((player) => {
        const now = this._nowPlaying(player);
        return now ? `${player}:${now.playing}:${JSON.stringify(now.fields)}` : player;
      })
      .join("|");
  }

  _refreshNowPlaying() {
    const card = this.shadowRoot.getElementById("now-playing");
    if (card) card.outerHTML = this._nowPlayingCard();
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
    this._add = null;
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
      this._draft = { ...DEFAULT_RULE, ...(this._prefill || {}) };
      this._prefill = null;
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
      case "add":
        this._navigate(`/add/${encodeURIComponent(data.player)}`);
        return;
      case "add-to":
        await this._addToRule(data.id);
        return;
      case "add-new":
        this._addToNewRule();
        return;
      case "toggle-keyword": {
        const chosen = new Set(this._add?.chosen || []);
        if (chosen.has(data.value)) chosen.delete(data.value);
        else chosen.add(data.value);
        this._add = { ...this._add, chosen: [...chosen] };
        this._render();
        return;
      }
      case "move":
        await this._moveRule(data.id, Number(data.dir));
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

  // Adding what plays to a rule

  _addPage() {
    const view = this._view();
    const now = this._nowPlaying(view.player);
    if (!this._add || this._add.player !== view.player) {
      // Artist first: that is usually what people want gone. Title otherwise.
      const chosen = now?.fields.artist ? ["artist"] : now?.fields.title ? ["title"] : [];
      this._add = { player: view.player, chosen };
    }
    const keywords = this._add.chosen.map((field) => now?.fields[field]).filter(Boolean);
    return { view, now, keywords };
  }

  async _addToRule(id) {
    const { view, keywords } = this._addPage();
    const rule = this._rule(id);
    if (!rule) return;
    if (!keywords.length) {
      this._notice = { type: "warning", text: this._t("add_pick_keyword") };
      this._render();
      return;
    }
    const existing = rule.data.keywords || [];
    const fresh = keywords.filter((keyword) => !existing.some((k) => k.toLowerCase() === keyword.toLowerCase()));
    const players = rule.data.players || [];
    if (!fresh.length && players.includes(view.player)) {
      this._notice = { type: "info", text: this._t("add_exists", { rule: rule.title }) };
      this._render();
      return;
    }
    await this._run("add", async () => {
      const data = {
        ...rule.data,
        keywords: [...existing, ...fresh],
        players: players.includes(view.player) ? players : [...players, view.player],
      };
      const result = await this._ws("save_rule", { subentry_id: id, data });
      if (result?.errors) {
        this._errors = result.errors;
        this._placeholders = result.placeholders || {};
        this._notice = { type: "error", text: this._t("fix_errors") };
        return;
      }
      this._navigate("");
      this._notice = { type: "success", text: this._t("add_done", { keywords: fresh.join(", "), rule: rule.title }) };
    });
  }

  _addToNewRule() {
    const { view, keywords } = this._addPage();
    if (!keywords.length) {
      this._notice = { type: "warning", text: this._t("add_pick_keyword") };
      this._render();
      return;
    }
    this._prefill = { name: keywords.join(", "), keywords, players: [view.player] };
    this._navigate("/rule/new");
  }

  // The order of the rules

  async _moveRule(id, direction) {
    const ids = this._state.rules.map((r) => r.id);
    const from = ids.indexOf(id);
    const to = from + direction;
    if (from < 0 || to < 0 || to >= ids.length) return;
    await this._reorder(from, to);
  }

  async _reorder(from, to) {
    const ids = this._state.rules.map((r) => r.id);
    const [moved] = ids.splice(from, 1);
    ids.splice(to, 0, moved);
    // Show the new order at once; the subscription confirms it.
    const rules = ids.map((id) => this._rule(id));
    this._state = { ...this._state, rules };
    this._stateJson = JSON.stringify(this._state);
    await this._run("reorder", () => this._ws("reorder_rules", { order: ids }));
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
    // One option per row, each with its own explanation.
    const choice = (key, values) => ({
      select: {
        mode: "box",
        box_max_columns: 1,
        options: values.map((value) => ({ value, label: this._option(key, value), description: this._t(`${key}_${value}`) })),
      },
    });
    const group = (name, title, schema) => ({ name, type: "expandable", flatten: true, expanded: true, title, schema });
    const number = (min, max, unit, step = 1) => ({
      number: { min, max, step, mode: "box", ...(unit ? { unit_of_measurement: unit } : {}) },
    });
    const sectionTitle = (step, section) =>
      this._localize(`config_subentries.rule.step.${step}.sections.${section}.name`) || section;
    const hasError = (...names) => names.some((name) => this._errors[name]);

    const action = ACTIONS.includes(draft.action) ? draft.action : "auto";
    const skipFields = [{ name: "max_consecutive", selector: number(0, 50) }];
    const switchFields = [
        { name: "station", selector: { media: {} } },
        { name: "station_actions", selector: { action: {} } },
        { name: "return_after_minutes", required: true, selector: number(0, 1440, "min") },
        { name: "return_fallback_media", selector: { media: {} } },
        { name: "return_fallback_actions", selector: { action: {} } },
        { name: "repeat_mode", required: true, selector: choice("repeat_mode", REPEAT_MODES) },
        { name: "repeat_limit", required: true, selector: number(1, 50) },
      ];
    const muteFields = [
      { name: "hold_seconds", required: true, selector: number(0, 300, "s") },
      { name: "max_mute_minutes", required: true, selector: number(0, 180, "min") },
    ];
    const specific = {
      auto: [
        group("skip", this._t("section_auto_skip"), skipFields),
        group("switch", this._t("section_auto_switch"), switchFields),
      ],
      skip: [group("skip", this._t("section_skip"), skipFields)],
      switch: [group("switch", this._t("section_switch"), switchFields)],
      mute: [group("mute", this._t("section_mute"), muteFields)],
    }[action];

    return [
      { name: "name", required: true, selector: { text: {} } },
      { name: "keywords", required: true, selector: { text: { multiple: true } } },
      { name: "players", required: true, selector: { entity: { domain: "media_player", multiple: true } } },
      { name: "action", required: true, selector: choice("action", ACTIONS) },
      ...specific,
      {
        name: "matching",
        type: "expandable",
        flatten: true,
        title: sectionTitle("basics", "matching"),
        expanded: hasError("match_mode", "match_fields", "ignore_texts"),
        schema: [
          { name: "match_mode", required: true, selector: choice("match_mode", MATCH_MODES) },
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
          { name: "presence_mode", required: true, selector: choice("presence_mode", PRESENCE_MODES) },
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

  _activityCard(rule) {
    const last = rule.last_match
      ? `<p>${esc(this._t("last_match"))}: ${esc(this._t("last_match_text", { description: rule.last_match.description, player: this._playerName(rule.last_match.player) }))}<br>
         <span class="hint">${esc(this._formatTime(rule.last_match.when))} · ${esc(this._t("matches", { count: rule.matches }))}</span></p>`
      : "";
    const events = (rule.events || []).slice().reverse();
    const list = events.length
      ? `<ul class="activity">${events
          .map(
            (event) => `<li><span class="when">${esc(this._formatTime(event.when))}</span><span class="what">${esc(event.message)}</span></li>`
          )
          .join("")}</ul>`
      : `<p class="hint">${esc(this._t("activity_none"))}</p>`;
    return `<ha-card header="${esc(this._t("activity"))}"><div class="card-content last">${last}${list}</div></ha-card>`;
  }

  // Rendering

  _render() {
    if (!this._hass) return;
    const view = this._view();
    let body;
    if (!this._state || !this._ready) body = this._loading();
    else if (!this._state.configured) body = this._message(this._t("not_configured"));
    else if (view.name === "rule") body = this._renderRule(view);
    else if (view.name === "add") body = this._renderAdd(view);
    else body = this._renderOverview();
    if (view.name !== "rule") this._ruleForm = null;
    this.shadowRoot.innerHTML = `<style>${STYLES}</style>${body}`;
    this._playersSig = this._playersSignature();
    const sortable = this.shadowRoot.querySelector("ha-sortable");
    if (sortable) {
      sortable.addEventListener("item-moved", (ev) => {
        ev.stopPropagation();
        const { oldIndex, newIndex } = ev.detail;
        // Let the drag finish before the list is drawn again.
        setTimeout(() => this._reorder(oldIndex, newIndex), 0);
      });
    }
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
    const count = this._state.rules.length;
    const index = this._state.rules.indexOf(rule);
    const canSort = count > 1 && this._state.loaded !== false;
    const handle = canSort && customElements.get("ha-sortable")
      ? `<span class="handle" title="${esc(this._t("drag"))}">${icon("mdi:drag")}</span>`
      : "";
    const arrows = canSort && !customElements.get("ha-sortable")
      ? `<ha-icon-button data-action="move" data-id="${esc(rule.id)}" data-dir="-1" label="${esc(this._t("move_up"))}" ${index === 0 ? "disabled" : ""}>${icon("mdi:arrow-up")}</ha-icon-button>
         <ha-icon-button data-action="move" data-id="${esc(rule.id)}" data-dir="1" label="${esc(this._t("move_down"))}" ${index === count - 1 ? "disabled" : ""}>${icon("mdi:arrow-down")}</ha-icon-button>`
      : "";
    return `<div class="row ${rule.enabled ? "" : "muted"}">
      ${handle}
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
        ${arrows}
        <ha-switch data-field="enabled" data-id="${esc(rule.id)}" ${rule.enabled ? "checked" : ""} ${this._busy.has("enabled" + rule.id) || !this._state.loaded ? "disabled" : ""} aria-label="${esc(this._t("enabled"))}"></ha-switch>
        <ha-icon-button data-action="edit" data-id="${esc(rule.id)}" label="${esc(this._t("edit_rule"))}">${icon("mdi:pencil-outline")}</ha-icon-button>
      </span>
    </div>`;
  }

  _nowPlayingCard() {
    const rows = this._watchedPlayers()
      .map((player) => ({ player, now: this._nowPlaying(player) }))
      .filter(({ now }) => now?.playing && now.description)
      .map(
        ({ player, now }) => `<div class="row">
          <div class="row-main static">
            <span class="row-icon">${icon("mdi:play-circle-outline")}</span>
            <span class="row-text"><span class="headline">${esc(now.description)}</span><span class="supporting">${esc(this._playerName(player))}</span></span>
          </div>
          <span class="row-end">${this._button(this._t("add_to_rule"), "add", { appearance: "outlined", data: { player }, iconName: "mdi:plus" })}</span>
        </div>`
      );
    return `<ha-card id="now-playing" header="${esc(this._t("now_playing"))}">
      <p class="card-text">${esc(this._t("now_playing_text"))}</p>
      ${rows.length ? `<div class="list">${rows.join("")}</div>` : `<p class="card-text">${esc(this._t("now_playing_none"))}</p>`}
      <p class="card-text hint last">${esc(this._t("now_playing_tile"))}</p>
    </ha-card>`;
  }

  _renderAdd(view) {
    const { now, keywords } = this._addPage();
    const name = this._playerName(view.player);
    let body;
    if (!now) {
      body = this._alert("warning", esc(this._t("unknown_player")));
    } else if (!now.playing || !Object.keys(now.fields).length) {
      body = this._alert("info", esc(this._t("player_idle", { player: name })));
    } else {
      // The row toggles the choice; the checkbox only shows it.
      const checkbox = (checked) =>
        customElements.get("ha-checkbox")
          ? `<ha-checkbox ${checked ? "checked" : ""} tabindex="-1"></ha-checkbox>`
          : `<input type="checkbox" ${checked ? "checked" : ""} tabindex="-1">`;
      const options = Object.entries(now.fields)
        .map(
          ([field, value]) => `<div class="row choice" role="checkbox" tabindex="0" aria-checked="${this._add.chosen.includes(field)}" data-action="toggle-keyword" data-value="${esc(field)}">
            ${checkbox(this._add.chosen.includes(field))}
            <span class="row-text"><span class="headline">${esc(value)}</span><span class="supporting">${esc(this._option("match_fields", field))}</span></span>
          </div>`
        )
        .join("");
      const rules = this._state.rules.map((rule) => {
        const watches = (rule.data.players || []).includes(view.player);
        return `<div class="row">
          <button class="row-main" type="button" data-action="add-to" data-id="${esc(rule.id)}" ${this._busy.has("add") ? "disabled" : ""}>
            <span class="row-icon">${icon(ACTION_ICONS[rule.data.action] || "mdi:music-note-off")}</span>
            <span class="row-text">
              <span class="headline">${esc(rule.title)}</span>
              <span class="supporting">${esc((rule.data.keywords || []).join(", "))}</span>
              ${watches ? "" : `<span class="supporting">${esc(this._t("add_also_player", { player: name }))}</span>`}
            </span>
          </button>
          <span class="row-end">${icon("mdi:plus")}</span>
        </div>`;
      });
      body = `<ha-card header="${esc(this._t("add_keywords"))}">
          <div class="card-content static-rows">
            <div class="row static"><div class="row-main static"><span class="row-icon">${icon("mdi:play-circle-outline")}</span>
              <span class="row-text"><span class="headline">${esc(now.description)}</span><span class="supporting">${esc(name)}</span></span></div></div>
          </div>
          <p class="card-text">${esc(this._t("add_text"))}</p>
          <div class="list">${options}</div>
          <div class="card-content"></div>
        </ha-card>
        <ha-card header="${esc(this._t("add_rules"))}">
          <p class="card-text">${esc(rules.length ? this._t("add_rules_text") : this._t("no_rules_yet"))}</p>
          <div class="list">${rules.join("")}</div>
          <div class="card-actions">${this._button(this._t("add_new_rule"), "add-new", {
            appearance: rules.length ? "outlined" : "accent",
            iconName: "mdi:plus",
            disabled: !keywords.length,
          })}</div>
        </ha-card>`;
    }
    return `${this._toolbar(this._t("add_title"), { back: true })}
      <div class="content"><div class="container">
        ${this._state.loaded ? "" : this._alert("warning", esc(this._t("not_loaded")))}
        ${this._notices()}${this._errorList()}
        ${body}
      </div></div>`;
  }

  _renderOverview() {
    const state = this._state;
    const list = `<div class="list">${state.rules.map((r) => this._ruleRow(r)).join("")}</div>`;
    const sortable = state.rules.length > 1 && customElements.get("ha-sortable");
    const rules = state.rules.length
      ? `<ha-card header="${esc(this._t("rules"))}">
         ${state.rules.length > 1 ? `<p class="card-text">${esc(this._t("rules_text"))}</p>` : ""}
         ${sortable ? `<ha-sortable handle-selector=".handle" draggable-selector=".row" ${this._busy.has("reorder") ? "disabled" : ""}>${list}</ha-sortable>` : list}
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
        ${state.rules.length ? this._nowPlayingCard() : ""}
        <ha-card header="${esc(this._t("snooze"))}">${snooze}</ha-card>
        <ha-card header="${esc(this._t("settings"))}">
          <p class="card-text">${esc(this._t("settings_text"))}</p>
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

  _errorList() {
    if (!Object.keys(this._errors).length) return "";
    return this._alert(
      "error",
      `<ul class="errors">${Object.entries(this._errors)
        .map(([field, code]) => `<li><b>${esc(this._fieldLabel(field))}</b>: ${esc(this._localize(`config_subentries.rule.error.${code}`, this._placeholders) || code)}</li>`)
        .join("")}</ul>`
    );
  }

  _renderRule(view) {
    const rule = view.id ? this._rule(view.id) : null;
    if (view.id && !rule) {
      return `${this._toolbar(this._t("title"), { back: true })}<div class="content"><div class="container">${this._alert("warning", esc(this._t("unknown_rule")))}</div></div>`;
    }
    const errorList = this._errorList();
    const lastMatch = rule ? this._activityCard(rule) : "";
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
          <p class="card-text intro">${esc(this._t("rule_intro"))}</p>
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
.handle { display: flex; align-items: center; padding-inline-start: var(--ss-space-2); color: var(--secondary-text-color); cursor: grab; touch-action: none; }
.handle:active { cursor: grabbing; }
.sortable-ghost { opacity: 0.4; }
.sortable-drag { background: var(--card-background-color); box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0, 0, 0, 0.2)); }
.row.choice { cursor: pointer; padding-inline-start: var(--ss-space-2); gap: var(--ss-space-3); }
.row.choice:hover { background: var(--secondary-background-color); }
.row.choice:focus-visible { outline: 2px solid var(--primary-color); outline-offset: -2px; }
.row.choice ha-checkbox, .row.choice input { pointer-events: none; }
.row.choice .row-text { padding: var(--ss-space-2) var(--ss-space-2) var(--ss-space-2) 0; }
.card-text.intro { padding-top: var(--ss-space-4); }
.static-rows { padding-bottom: 0; }
.row-end ha-icon { color: var(--secondary-text-color); padding: 0 var(--ss-space-2); }
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
.activity { list-style: none; margin: 0 0 var(--ss-space-2); padding: 0; }
.activity li { display: flex; gap: var(--ss-space-3); padding: var(--ss-space-1) 0; border-top: 1px solid var(--divider-color); }
.activity .when { flex: none; width: 11em; color: var(--secondary-text-color); font-size: var(--ha-font-size-s, 12px); font-variant-numeric: tabular-nums; }
.activity .what { flex: 1; overflow-wrap: anywhere; }
@media (max-width: 600px) { .activity li { flex-direction: column; gap: 0; } .activity .when { width: auto; } }
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
