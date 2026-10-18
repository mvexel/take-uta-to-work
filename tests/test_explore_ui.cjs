// DOM/Leaflet doubles exercise real application handlers in Node, not a browser.
// All routing responses and geometry here are synthetic.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

class Element {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.value = "";
  }
  append(...children) {
    this.children.push(...children);
  }
  replaceChildren(...children) {
    this.children = children;
  }
  setAttribute() {}
  addEventListener() {}
  remove() {}
  scrollIntoView() {}
}
function harness() {
  const elements = new Map();
  const requests = [];
  const layer = () => ({
    layers: [],
    addTo() {
      return this;
    },
    clearLayers() {
      this.layers = [];
    },
    getLayers() {
      return this.layers;
    },
    getBounds() {
      return {
        pad() {
          return this;
        },
      };
    },
  });
  const map = {
    setView() {
      return this;
    },
    on() {},
    fitBounds() {},
    attributionControl: { setPrefix() {}, addAttribution() {} },
  };
  const context = vm.createContext({
    document: {
      getElementById(id) {
        if (!elements.has(id)) elements.set(id, new Element("div"));
        return elements.get(id);
      },
      createElement: (tag) => new Element(tag),
    },
    L: {
      map: () => map,
      layerGroup: layer,
      featureGroup: layer,
      divIcon: (x) => x,
      marker: () => ({
        addTo() {
          return this;
        },
        on() {},
        remove() {},
      }),
      polyline: (coordinates, style) => ({
        addTo(group) {
          group.layers.push({ coordinates, style });
          return this;
        },
      }),
    },
    AbortController,
    setTimeout,
    clearTimeout,
    console,
    fetch: (url, options) =>
      new Promise((resolve) => {
        // Keep config bootstrap pending. Tests explicitly set the scenario.
        if (url !== "/api/config")
          requests.push({
            url,
            options,
            resolve: (body) => resolve({ ok: true, json: async () => body }),
          });
      }),
  });
  vm.runInContext(
    fs.readFileSync(path.join(__dirname, "../web/explore.js"), "utf8"),
    context,
  );
  const run = (code) => vm.runInContext(code, context);
  run(
    'active={mode:"both",changes:1,target:30,fringe:10,arrival:"2026-10-20T11:00",destination:"art"}; addPoint({lat:40.76,lon:-111.88});',
  );
  return { context, run, requests };
}
const fixture = (mode) => ({
  band: "target",
  qualifies: true,
  reasons: [],
  elapsed_seconds: 1200,
  earliness_seconds: 0,
  vehicle_changes: 0,
  arrival: "2026-10-20T11:00:00-06:00",
  departure: "2026-10-20T10:40:00-06:00",
  breakdown: { walk: 0, wait: 0, ride: 1200, bike: 0 },
  legs: [
    {
      mode,
      transitLeg: true,
      route: { shortName: mode === "TRAM" ? "703" : "455" },
      legGeometry: { points: "??AA" },
      from: { name: "Synthetic origin" },
      to: { name: "Synthetic destination" },
      start: { scheduledTime: "2026-10-20T10:40:00-06:00" },
      end: { scheduledTime: "2026-10-20T11:00:00-06:00" },
    },
  ],
});
const response = () => ({
  status: "target",
  itineraries: [fixture("BUS"), fixture("TRAM")],
});
const flush = () => new Promise((resolve) => setImmediate(resolve));
async function ready() {
  const h = harness();
  h.requests.shift().resolve(response());
  await flush();
  return h;
}
function find(element, tag) {
  if (element.tag === tag) return element;
  for (const child of element.children || []) {
    const result = find(child, tag);
    if (result) return result;
  }
}
function show(h) {
  const panel = h.run("points.get(1).element");
  const button = panel.children
    .flatMap((c) => c.children || [])
    .find(
      (e) => e.tag === "button" && e.textContent === "Show this journey on map",
    );
  assert.ok(button);
  button.onclick();
  assert.equal(h.run("routes.getLayers().length"), 1);
}

test("switching actual alternative handler removes shown bus geometry before rail details", async () => {
  const h = await ready();
  show(h);
  const select = find(h.run("points.get(1).element"), "select");
  select.value = "1";
  select.onchange();
  assert.equal(h.run("routes.getLayers().length"), 0);
  show(h);
  assert.equal(h.run("routes.getLayers()[0].style.color"), "#087e83");
  select.value = "0";
  select.onchange();
  assert.equal(h.run("routes.getLayers().length"), 0);
});
test("recheck clears overlay immediately, including a failed replacement", async () => {
  const h = await ready();
  show(h);
  h.run("checkPoint(points.get(1));");
  assert.equal(h.run("routes.getLayers().length"), 0);
  assert.equal(h.run("points.get(1).status"), "pending");
  h.requests
    .shift()
    .resolve({ status: "error", error: "Synthetic failed route" });
  await flush();
  assert.equal(h.run("routes.getLayers().length"), 0);
  assert.equal(h.run("points.get(1).status"), "error");
});
test("repeated rechecks ignore older responses and parameter invalidation removes geometry", async () => {
  const h = await ready();
  show(h);
  h.run("checkPoint(points.get(1)); checkPoint(points.get(1));");
  const [old, current] = h.requests.splice(0);
  current.resolve(response());
  await flush();
  show(h);
  old.resolve({ status: "error", error: "Stale response" });
  await flush();
  assert.equal(h.run("points.get(1).status"), "target");
  assert.equal(h.run("routes.getLayers().length"), 1);
  h.run("invalidate(false);");
  assert.equal(h.run("routes.getLayers().length"), 0);
  assert.equal(h.run("points.get(1).status"), "stale");
});
