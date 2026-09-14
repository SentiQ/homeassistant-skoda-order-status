const CHECKPOINTS = [
  { status: "ORDER_CONFIRMED", label: "Bestätigt" },
  { status: "IN_PRODUCTION", label: "In Produktion" },
  { status: "IN_DELIVERY", label: "Unterwegs" },
  { status: "TO_HANDOVER", label: "Zur Übergabe" },
];

function formatDate(iso) {
  if (!iso) return "offen";
  const parts = String(iso).split("-");
  if (parts.length < 3) return iso;
  return `${parts[2]}.${parts[1]}.${parts[0]}`;
}

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function cropCss(crop) {
  if (!crop || !crop.width || !crop.height) return null;
  const visW = crop.width - crop.left - crop.right;
  const visH = crop.height - crop.top - crop.bottom;
  if (visW <= 0 || visH <= 0) return null;
  return {
    wrap: `aspect-ratio:${visW} / ${visH};`,
    img: `width:${(crop.width / visW) * 100}%;height:auto;left:${(-crop.left / visW) * 100}%;top:${(-crop.top / visH) * 100}%;`,
  };
}

const VIEW_STORAGE_PREFIX = "skoda-order-card:";
const VIEW_OPTIONS = [
  { value: "side", label: "Seite" },
  { value: "front", label: "Front" },
  { value: "rear", label: "Heck" },
  { value: "interior_front", label: "Innenraum vorne" },
  { value: "interior_side", label: "Innenraum Seite" },
  { value: "boot", label: "Kofferraum" },
];

function viewStorageKey(entityId) {
  return `${VIEW_STORAGE_PREFIX}${entityId}:view`;
}

function configViewStorageKey(entityId) {
  return `${VIEW_STORAGE_PREFIX}${entityId}:configView`;
}

function storageGet(key) {
  try {
    return window.localStorage.getItem(key);
  } catch (err) {
    return null;
  }
}

function storageSet(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch (err) {
    /* ignore quota / private mode */
  }
}

function writeStoredView(entityId, viewId) {
  storageSet(viewStorageKey(entityId), viewId);
}

function collectImages(attr) {
  if (Array.isArray(attr.images) && attr.images.length) {
    return attr.images.filter((item) => item && item.id && item.url);
  }
  if (attr.entity_picture) {
    return [{ id: "side", label: "Seite", url: attr.entity_picture, crop: attr.image_crop || null }];
  }
  return [];
}

function resolveViewId(images, entityId, configView, preferConfig) {
  const ids = new Set(images.map((item) => item.id));
  const configured = configView && ids.has(configView)
    ? configView
    : (ids.has("side") ? "side" : (images[0] ? images[0].id : null));
  if (!configured) return null;
  if (preferConfig || !entityId) return configured;

  const lastConfig = storageGet(configViewStorageKey(entityId));
  if (lastConfig !== configured) {
    storageSet(configViewStorageKey(entityId), configured);
    if (lastConfig !== null) {
      storageSet(viewStorageKey(entityId), configured);
      return configured;
    }
  }
  const stored = storageGet(viewStorageKey(entityId));
  if (stored && ids.has(stored)) return stored;
  return configured;
}

function photoBox(images, currentImage) {
  const frameCrop = (currentImage && currentImage.crop)
    || ((images.find((item) => item && item.crop) || {}).crop)
    || null;
  const frame = cropCss(frameCrop);
  const imgCrop = currentImage ? cropCss(currentImage.crop) : null;
  return {
    wrap: frame ? frame.wrap : "aspect-ratio:16/6;",
    img: imgCrop
      ? imgCrop.img
      : "width:100%;height:100%;object-fit:cover;left:0;top:0;",
  };
}

class SkodaOrderCard extends HTMLElement {
  static getStubConfig() {
    return { layout: "combined", view: "side" };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: { entity: { filter: { domain: "sensor" } } },
        },
        {
          name: "layout",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "combined", label: "Kombiniert" },
                { value: "hero", label: "Hero" },
                { value: "timeline", label: "Timeline" },
              ],
            },
          },
        },
        {
          name: "view",
          selector: {
            select: {
              mode: "dropdown",
              options: VIEW_OPTIONS,
            },
          },
        },
      ],
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Ungültige Konfiguration");
    }
    this._config = { layout: "combined", view: "side", ...config };
    this._lastState = undefined;
    this._lastLayout = undefined;
    this._lastView = undefined;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const layout = (this._config && this._config.layout) || "combined";
    if (layout === "timeline") return 2;
    if (layout === "hero") return 3;
    return 5;
  }

  getGridOptions() {
    const layout = (this._config && this._config.layout) || "combined";
    if (layout === "timeline") {
      return { columns: 12, min_columns: 6, rows: 2, min_rows: 2 };
    }
    if (layout === "hero") {
      return { columns: 12, min_columns: 6, rows: 4, min_rows: 3 };
    }
    return { columns: 12, min_columns: 6, rows: 6, min_rows: 4 };
  }

  _openMoreInfo() {
    if (!this._config || !this._config.entity) return;
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId: this._config.entity },
      })
    );
  }

  _render() {
    if (!this._config) return;
    if (!this._shadow) {
      this._shadow = this.attachShadow({ mode: "open" });
    }

    const layout = this._config.layout || "combined";
    const view = this._config.view || "side";
    if (!this._config.entity) {
      this._lastState = undefined;
      this._lastLayout = undefined;
      this._lastView = undefined;
      this._shadow.innerHTML = `
        <ha-card><div class="pad warn">Bitte eine Entity wählen</div></ha-card>
        ${this._styles()}
      `;
      return;
    }
    const state = this._hass && this._hass.states[this._config.entity];
    if (!state) {
      this._lastState = undefined;
      this._lastLayout = undefined;
      this._lastView = undefined;
      this._shadow.innerHTML = `
        <ha-card><div class="pad warn">Entity nicht gefunden</div></ha-card>
        ${this._styles()}
      `;
      return;
    }

    if (state === this._lastState && layout === this._lastLayout && view === this._lastView) return;

    const attr = state.attributes || {};
    const unavailable = state.state === "unavailable" || state.state === "unknown";
    const accent = attr.accent_color || "#4a7a62";
    const model = attr.model || "Škoda";
    const trim = attr.trim_level || "";
    const paint = attr.paint_name || "";
    const statusLabel = unavailable ? "nicht verfügbar" : state.state;
    const images = collectImages(attr);
    const viewId = resolveViewId(images, this._config.entity, view, this.preview);
    const currentImage = images.find((item) => item.id === viewId) || images[0];
    const showPhoto = !unavailable && currentImage && layout !== "timeline";
    const showHero = layout !== "timeline";
    const showTimeline = layout !== "hero";
    const box = photoBox(images, currentImage);
    const photoDots = images.length > 1
      ? `<div class="photo-dots">${images.map((item) => `<span class="${item.id === currentImage.id ? "active" : ""}"></span>`).join("")}</div>`
      : "";
    const photoBlock = showPhoto ? `
            <button type="button" class="photo-btn" aria-label="${esc(currentImage.label)}">
            <div class="photo" style="${box.wrap}">
              <img alt="${esc(currentImage.label)}" src="${esc(currentImage.url)}" style="${box.img}" />
            </div>
            ${photoDots}
            </button>` : "";

    const reached = attr.checkpoints_reached || [];
    const reachedMap = Object.fromEntries(reached.map((item) => [item.status, item]));
    const lastReached = CHECKPOINTS.reduce((acc, item, index) => {
      const rec = reachedMap[item.status];
      return rec && rec.date ? index : acc;
    }, -1);
    const allDone =
      lastReached === CHECKPOINTS.length - 1 &&
      CHECKPOINTS.every((cp) => reachedMap[cp.status] && reachedMap[cp.status].date);
    const doneCount = CHECKPOINTS.filter((item) => reachedMap[item.status] && reachedMap[item.status].date).length;
    const segments = CHECKPOINTS.length - 1;
    let fillPct = 0;
    if (!unavailable && segments > 0 && lastReached >= 0) {
      fillPct = allDone ? 100 : ((lastReached + 0.5) / segments) * 100;
    }

    const chips = [];
    if (attr.battery_kwh != null) chips.push(`${attr.battery_kwh} kWh`);
    if (attr.max_performance_kw != null) chips.push(`${attr.max_performance_kw} kW`);
    if (paint) chips.push(paint);

    const steps = CHECKPOINTS.map((item, index) => {
      const rec = reachedMap[item.status];
      const done = Boolean(rec && rec.date);
      const isCurrent = !unavailable && !allDone && index === lastReached;
      return `
        <div class="step">
          <div class="dot${done ? " done" : ""}${isCurrent ? " current" : ""}"></div>
          <div class="step-label">${item.label}</div>
          <div class="step-date">${esc(formatDate(rec && rec.date))}</div>
        </div>`;
    }).join("");
    const mids = CHECKPOINTS.slice(0, -1)
      .map((_, index) => {
        const done = lastReached > index;
        const current = !unavailable && !allDone && index === lastReached;
        const left = ((index + 1) / CHECKPOINTS.length) * 100;
        return `<div class="dot mid${done ? " done" : ""}${current ? " current" : ""}" style="left:${left}%"></div>`;
      })
      .join("");

    this._shadow.innerHTML = `
      <ha-card class="${unavailable ? "dim" : ""}">
          ${showHero ? `
          <div class="hero">
            <button class="hit" aria-label="Mehr Infos">
            <div class="hero-top">
              <div>
                <div class="kicker">Škoda Bestellung</div>
                <div class="name">${esc(model)}${trim ? ` ${esc(trim)}` : ""}</div>
              </div>
              <span class="badge">${layout === "timeline" ? "" : esc(statusLabel)}</span>
            </div>
            </button>
            ${photoBlock}
            <button class="hit" aria-label="Mehr Infos">
            <div class="chips">${chips.map((c) => `<span class="chip">${esc(c)}</span>`).join("")}</div>
            </button>
          </div>` : `
          <button class="hit" aria-label="Mehr Infos">
          <div class="hero compact">
            <div class="hero-top">
              <div>
                <div class="kicker">${esc(model)}</div>
                <div class="name">Bestellstatus</div>
              </div>
              <span class="badge">${doneCount} / ${CHECKPOINTS.length}</span>
            </div>
          </div>
          </button>`}
          ${showTimeline ? `
          <button class="hit" aria-label="Mehr Infos">
          ${showHero ? `<div class="divider"></div>` : ""}
          <div class="timeline ${unavailable ? "dim" : ""}">
            <div class="steps">
              <div class="rail"><div class="rail-fill" style="width:${fillPct}%"></div></div>
              ${mids}
              ${steps}
            </div>
          </div>
          </button>` : ""}
      </ha-card>
      ${this._styles(accent)}
    `;

    const img = this._shadow.querySelector(".photo img");
    if (img) {
      img.addEventListener("error", () => {
        const btn = this._shadow.querySelector(".photo-btn");
        if (btn) btn.remove();
      });
    }
    const photoBtn = this._shadow.querySelector(".photo-btn");
    if (photoBtn && images.length >= 2) {
      photoBtn.addEventListener("click", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const idx = images.findIndex((item) => item.id === currentImage.id);
        const next = images[(idx + 1) % images.length];
        writeStoredView(this._config.entity, next.id);
        this._lastState = undefined;
        this._render();
      });
    }
    this._shadow.querySelectorAll(".hit").forEach((hit) => {
      hit.addEventListener("click", () => this._openMoreInfo());
    });

    this._lastState = state;
    this._lastLayout = layout;
    this._lastView = view;
  }

  _styles(accent) {
    const paint = accent || "#4a7a62";
    return `
      <style>
        :host { display: block; height: 100%; --skoda-paint: ${paint}; }
        ha-card {
          display: block;
          height: 100%;
          box-sizing: border-box;
          background: var(--ha-card-background, var(--card-background-color, var(--primary-background-color)));
          color: var(--primary-text-color);
          overflow: hidden;
        }
        ha-card.dim { opacity: .72; }
        .pad { padding: 1rem; }
        .warn { color: var(--secondary-text-color); }
        .hit {
          display: block; width: 100%; border: 0; padding: 0; margin: 0;
          background: transparent; color: inherit; text-align: left; cursor: pointer; font: inherit;
        }
        .photo-btn {
          display: block; width: 100%; border: 0; padding: 0; margin: 0;
          background: transparent; color: inherit; cursor: pointer; font: inherit;
        }
        .hero { padding: 1rem 1.1rem .85rem; }
        .hero.compact { padding-bottom: .35rem; }
        .hero-top { display: flex; justify-content: space-between; gap: .75rem; align-items: flex-start; }
        .kicker { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; opacity: .55; }
        .name { font-size: 1.15rem; font-weight: 650; line-height: 1.2; }
        .badge {
          background: color-mix(in srgb, var(--skoda-paint) 18%, transparent);
          color: var(--skoda-paint);
          border: 1px solid color-mix(in srgb, var(--skoda-paint) 45%, transparent);
          border-radius: 999px; padding: .2rem .65rem; font-size: .72rem; font-weight: 600; white-space: nowrap;
        }
        .photo {
          position: relative; overflow: hidden; margin: .35rem -.2rem .2rem;
          background: radial-gradient(ellipse at 50% 78%, color-mix(in srgb, var(--skoda-paint) 22%, transparent), transparent 64%);
        }
        .photo img { position: absolute; display: block; max-width: none; }
        .photo-dots {
          display: flex; justify-content: center; gap: .35rem; margin: .1rem 0 .05rem;
        }
        .photo-dots span {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--divider-color, rgba(127,127,127,.35));
        }
        .photo-dots span.active { background: var(--skoda-paint); }
        .chips { display: flex; gap: .45rem; flex-wrap: wrap; margin-top: .45rem; }
        .chip {
          font-size: .7rem; opacity: .85;
          background: var(--secondary-background-color, rgba(127,127,127,.12));
          border-radius: 8px; padding: .18rem .5rem;
        }
        .divider { height: 1px; background: var(--divider-color, rgba(127,127,127,.2)); margin: 0 1.1rem; }
        .timeline { padding: 1rem 1.1rem 1.15rem; }
        .steps { display: flex; justify-content: space-between; position: relative; }
        .rail {
          position: absolute; top: 11px; left: 12%; right: 12%; height: 2px;
          background: var(--divider-color, rgba(127,127,127,.25));
        }
        .rail-fill { height: 100%; background: var(--skoda-paint); border-radius: 2px; }
        .step { width: 25%; text-align: center; position: relative; z-index: 1; }
        .dot {
          width: 22px; height: 22px; border-radius: 50%; margin: 0 auto .4rem;
          border: 2px solid var(--divider-color, rgba(127,127,127,.35));
          background: var(--ha-card-background, var(--card-background-color));
        }
        .dot.done { background: var(--skoda-paint); border-color: var(--skoda-paint); }
        .dot.mid {
          position: absolute; top: 6px; width: 10px; height: 10px; margin: 0 0 0 -5px; z-index: 1;
        }
        .dot.current {
          border-color: var(--skoda-paint);
          box-shadow: 0 0 0 4px color-mix(in srgb, var(--skoda-paint) 28%, transparent);
          animation: skoda-pulse 2.4s ease-in-out infinite;
        }
        .dot.mid.current {
          box-shadow: 0 0 0 3px color-mix(in srgb, var(--skoda-paint) 28%, transparent);
          animation-name: skoda-pulse-mid;
        }
        .step-label { font-size: .68rem; font-weight: 600; }
        .step-date { font-size: .62rem; opacity: .5; margin-top: .1rem; }
        @keyframes skoda-pulse {
          0%, 100% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--skoda-paint) 28%, transparent); }
          50% { box-shadow: 0 0 0 7px color-mix(in srgb, var(--skoda-paint) 8%, transparent); }
        }
        @keyframes skoda-pulse-mid {
          0%, 100% { box-shadow: 0 0 0 3px color-mix(in srgb, var(--skoda-paint) 28%, transparent); }
          50% { box-shadow: 0 0 0 5px color-mix(in srgb, var(--skoda-paint) 8%, transparent); }
        }
        @media (prefers-reduced-motion: reduce) {
          .dot.current { animation: none; }
        }
      </style>
    `;
  }
}

if (!customElements.get("skoda-order-card")) {
  customElements.define("skoda-order-card", SkodaOrderCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "skoda-order-card")) {
  window.customCards.push({
    type: "skoda-order-card",
    name: "Škoda Order Status",
    description: "Bestellstatus mit Konfigurator-Bild und Timeline",
    preview: true,
    getEntitySuggestion: (hass, entityId) => {
      const state = hass && hass.states && hass.states[entityId];
      const attr = state && state.attributes;
      if (!attr || (!attr.image_crop && !attr.commission_id)) return null;
      return {
        config: { type: "custom:skoda-order-card", entity: entityId, layout: "combined", view: "side" },
      };
    },
  });
}
