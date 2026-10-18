"use strict";
const $ = (id) => document.getElementById(id);
const node = (tag, text, cls) => {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
};
const clock = (s) =>
  new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Denver",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(s));
const duration = (s) =>
  Number.isFinite(s)
    ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`
    : "Unknown";
const labels = {
  target: "Within target",
  fringe: "Within longer-duration fringe",
  beyond: "Beyond target and fringe",
  unknown: "Unknown / incomplete",
  error: "Request failed",
  not_evaluated: "Outside routing study",
  no_qualifying_returned_route: "No qualifying journey returned",
  pending: "Checking exact point…",
  stale: "Needs recheck · parameters changed",
};
const map = L.map("map", { preferCanvas: true }).setView([40.76, -111.87], 13);
map.attributionControl.setPrefix("Leaflet 1.9.4");
map.attributionControl.addAttribution(
  '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
);
const areas = L.layerGroup().addTo(map),
  markers = L.layerGroup().addTo(map),
  routes = L.featureGroup().addTo(map);
let config,
  active = null,
  epoch = 0,
  nextPoint = 1,
  areaJob = null,
  areaTimer = null,
  sliderTimer = null,
  sliderAuto = false;
const points = new Map();
const scenario = () => ({
  destination: $("destination").value,
  arrival: $("arrival").value,
  mode: $("mode").value,
  changes: $("mode").value === "bike" ? 0 : Number($("changes").value),
  target: Number($("target").value),
  fringe: 10,
});
async function json(url, options = {}) {
  const r = await fetch(url, options);
  const body = await r.json();
  if (!r.ok) throw Error(body.error || `Request failed (${r.status})`);
  return body;
}
const post = (url, body, signal) =>
  json(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
function decode(encoded) {
  let lat = 0,
    lon = 0,
    i = 0,
    out = [];
  while (i < encoded.length) {
    const read = () => {
      let b,
        shift = 0,
        v = 0;
      do {
        if (i >= encoded.length || shift > 30) throw Error("Invalid geometry");
        b = encoded.charCodeAt(i++) - 63;
        v |= (b & 31) << shift;
        shift += 5;
      } while (b >= 32);
      return v & 1 ? ~(v >> 1) : v >> 1;
    };
    lat += read();
    lon += read();
    out.push([lat / 1e5, lon / 1e5]);
  }
  return out;
}
function updateLabels() {
  const t = Number($("target").value);
  $("target-value").textContent = `${t} min`;
  $("fringe-copy").textContent =
    `Also explore journeys up to ${t + 10} minutes.`;
  $("target-label").textContent = `Target ≤${t} min`;
  $("fringe-label").textContent = `Fringe ${t}–${t + 10} min`;
  $("changes").disabled = $("mode").value === "bike";
}
function invalidate(cancelArea) {
  epoch++;
  active = null;
  clearTimeout(areaTimer);
  areas.clearLayers();
  routes.clearLayers();
  if (cancelArea && areaJob) {
    json(`/api/area/${areaJob}`, { method: "DELETE" }).catch(() => {});
    areaJob = null;
  }
  for (const p of points.values()) {
    p.controller?.abort();
    p.result = null;
    p.status = "stale";
    renderPoint(p);
  }
  $("add-point").disabled = true;
  $("recheck").disabled = true;
  $("area-progress").hidden = true;
  $("retry-area").hidden = true;
  $("area-status").textContent =
    "Parameters changed. Previous area is cleared; apply to calculate this commute.";
  $("form-status").textContent = "Changes not applied.";
  $("map-instruction").textContent =
    "Apply your parameters before selecting points.";
}
for (const id of ["destination", "arrival", "mode", "changes", "target"])
  $(id).addEventListener("input", () => {
    const wasActive = !!active || sliderAuto;
    clearTimeout(sliderTimer);
    updateLabels();
    invalidate(id !== "target");
    sliderAuto = id === "target" && wasActive;
    if (sliderAuto)
      sliderTimer = setTimeout(() => {
        sliderAuto = false;
        $("parameters").requestSubmit();
      }, 350);
  });
function drawArea(area) {
  areas.clearLayers();
  const colors = {
    target: "#087e83",
    fringe: "#b2dedd",
    unknown: "#959eaa",
    outside_band: "#dbcbaa",
  };
  for (const f of area.features) {
    L.geoJSON(f, {
      interactive: false,
      style: {
        color: colors[f.properties.band],
        weight: f.properties.band === "unknown" ? 0.5 : 0,
        dashArray: f.properties.band === "unknown" ? "1 3" : undefined,
        fillColor: colors[f.properties.band],
        fillOpacity:
          f.properties.band === "unknown"
            ? 0.22
            : f.properties.band === "outside_band"
              ? 0.16
              : 0.58,
      },
    }).addTo(areas);
  }
  // Draw only exterior raster edges, preserving holes and disconnected components.
  for (const band of ["target", "fringe"]) {
    const edges = new Map();
    for (const f of area.features.filter((f) => f.properties.band === band)) {
      const c = f.geometry.coordinates[0];
      for (let i = 0; i < 4; i++) {
        const a = c[i],
          b = c[i + 1];
        const key = [a.join(","), b.join(",")].sort().join("|");
        if (edges.has(key)) edges.delete(key);
        else edges.set(key, [a, b]);
      }
    }
    for (const [a, b] of edges.values())
      L.polyline(
        [
          [a[1], a[0]],
          [b[1], b[0]],
        ],
        {
          interactive: false,
          color: band === "target" ? "#075f64" : "#77b7b6",
          weight: band === "target" ? 2 : 1,
          opacity: 0.9,
        },
      ).addTo(areas);
  }
}
async function pollArea(key, requestEpoch, s) {
  try {
    const result = await json(`/api/area/${key}?target=${s.target}`);
    if (epoch !== requestEpoch || !active) return;
    if (result.status === "complete") {
      drawArea(result.area);
      $("area-progress").hidden = true;
      const a = result.area;
      $("area-status").textContent =
        `Approximate raster contour · ${a.cell_metres_max} m cells · ${a.sample_count} queried origins · ${Math.round(a.elapsed_seconds)} s calculation. Mixed cells stay unknown; click to verify a location.`;
      return;
    }
    if (["failed", "cancelled"].includes(result.status)) {
      throw Error(
        result.error ||
          "Area calculation cancelled. Select Retry to calculate.",
      );
    }
    $("area-progress").hidden = false;
    $("area-progress").max = result.total || 1;
    $("area-progress").value = result.done;
    $("area-status").textContent =
      `${result.status === "queued" ? "Waiting for prior calculation to stop" : "Calculating actual journeys"} · ${result.done}/${result.total || "…"} origins. You can check points while this runs.`;
    areaTimer = setTimeout(() => pollArea(key, requestEpoch, s), 1000);
  } catch (e) {
    if (epoch === requestEpoch) {
      $("area-status").textContent = `Area unavailable: ${e.message}`;
      $("area-progress").hidden = true;
      $("retry-area").hidden = false;
    }
  }
}
async function startArea(s, requestEpoch) {
  $("area-status").textContent = "Starting area calculation…";
  $("retry-area").hidden = true;
  try {
    const r = await post("/api/area", { scenario: s });
    if (epoch !== requestEpoch) return;
    areaJob = r.job_id;
    pollArea(areaJob, requestEpoch, s);
  } catch (e) {
    if (epoch === requestEpoch) {
      $("area-status").textContent = `Area unavailable: ${e.message}`;
      $("retry-area").hidden = false;
    }
  }
}
$("parameters").onsubmit = (e) => {
  e.preventDefault();
  if (!$("parameters").reportValidity()) return;
  clearTimeout(sliderTimer);
  invalidate(false);
  active = scenario();
  const current = epoch;
  updateLabels();
  $("form-status").textContent =
    `Applied: ${active.arrival.replace("T", " ")} Denver · ${active.target} min + 10 min fringe`;
  $("map-instruction").textContent =
    "Select places to explore — inside or beyond the contour.";
  $("add-point").disabled = false;
  $("recheck").disabled = points.size === 0;
  $("points-hint").textContent =
    "Each point gets its own commute check. Results are comparable only under these applied parameters.";
  startArea({ ...active }, current);
  for (const p of points.values()) checkPoint(p);
};
$("retry-area").onclick = () => {
  if (active) startArea({ ...active }, epoch);
};
function pointMarker(p) {
  p.marker = L.marker([p.origin.lat, p.origin.lon], {
    icon: L.divIcon({
      className: "point-marker",
      html: String(p.id),
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    }),
  }).addTo(markers);
  p.marker.on("click", () =>
    p.element.scrollIntoView({ block: "nearest", behavior: "smooth" }),
  );
}
function addPoint(origin) {
  if (!active) {
    $("form-status").textContent = "Apply a commute first.";
    return;
  }
  if (points.size >= 6) {
    $("points-hint").textContent =
      "Compare up to six points. Remove a point to add another.";
    return;
  }
  const p = {
    id: nextPoint++,
    origin,
    status: "pending",
    element: node("article", undefined, "point-card"),
  };
  p.element.id = `point-${p.id}`;
  points.set(p.id, p);
  $("points").append(p.element);
  pointMarker(p);
  $("recheck").disabled = false;
  checkPoint(p);
}
map.on("click", (e) => addPoint({ lat: e.latlng.lat, lon: e.latlng.lng }));
$("coordinate-form").onsubmit = (e) => {
  e.preventDefault();
  addPoint({
    lat: Number($("latitude").value),
    lon: Number($("longitude").value),
  });
};
$("recheck").onclick = () => {
  if (active) for (const p of points.values()) checkPoint(p);
};
async function checkPoint(p) {
  // An old path must not survive while its evidence is being replaced.
  routes.clearLayers();
  p.controller?.abort();
  p.controller = new AbortController();
  const signal = p.controller.signal;
  const requestEpoch = epoch,
    s = { ...active };
  p.status = "pending";
  p.result = null;
  renderPoint(p);
  try {
    const r = await post(
      "/api/point",
      { origin: p.origin, scenario: s },
      signal,
    );
    if (epoch !== requestEpoch || signal.aborted || !points.has(p.id)) return;
    p.result = r;
    p.status = r.status;
    renderPoint(p);
  } catch (e) {
    if (epoch !== requestEpoch || signal.aborted || !points.has(p.id)) return;
    p.status = "error";
    p.result = { error: e.message };
    renderPoint(p);
  }
}
function metric(label, text) {
  const e = node("div", undefined, "metric");
  e.append(node("strong", text), node("span", label));
  return e;
}
function modes(it) {
  return (
    [
      ...new Set(
        it.legs
          .filter((l) => l.transitLeg)
          .map(
            (l) =>
              `${l.mode === "TRAM" ? "TRAX" : "Bus"} ${l.route?.shortName || ""}`,
          ),
      ),
    ].join(" + ") || "Bike / pushing"
  );
}
function renderItinerary(it, container) {
  // Details changed: the previous overlay no longer represents this selection.
  routes.clearLayers();
  container.replaceChildren();
  const m = node("div", undefined, "metrics");
  m.append(
    metric("Elapsed · door to door", duration(it.elapsed_seconds)),
    metric("Arrival · Denver", clock(it.arrival)),
    metric("Departure · Denver", clock(it.departure)),
    metric("Before latest arrival", duration(it.earliness_seconds)),
  );
  container.append(
    m,
    node(
      "p",
      `${labels[it.band] || "Outside scenario constraints"} · ${it.vehicle_changes} vehicle changes`,
    ),
  );
  const b = it.breakdown;
  container.append(
    node(
      "p",
      `Walk ${duration(b.walk)} · Wait ${duration(b.wait)} · Ride ${duration(b.ride)} · Bike ${duration(b.bike)}`,
      "hint",
    ),
  );
  if (it.reasons.length)
    container.append(
      node("p", `Does not meet scenario: ${it.reasons.join(", ")}`, "error"),
    );
  const show = node("button", "Show this journey on map", "quiet");
  show.type = "button";
  show.onclick = () => {
    routes.clearLayers();
    for (const l of it.legs) {
      if (!l.legGeometry?.points) continue;
      try {
        L.polyline(decode(l.legGeometry.points), {
          color:
            l.mode === "TRAM"
              ? "#087e83"
              : l.mode === "BUS"
                ? "#075b89"
                : l.mode === "BICYCLE"
                  ? "#98624b"
                  : "#526b76",
          weight: 4,
          dashArray: l.mode === "WALK" ? "4 6" : undefined,
        }).addTo(routes);
      } catch {
        container.append(node("p", "Some geometry unavailable.", "hint"));
      }
    }
    if (routes.getLayers().length)
      map.fitBounds(routes.getBounds().pad(0.1), { maxZoom: 15 });
  };
  container.append(show);
  const details = node("details");
  details.append(node("summary", "Inspect journey legs"));
  for (const l of it.legs) {
    const name =
      l.mode === "TRAM"
        ? "TRAX"
        : l.mode === "BUS"
          ? "Bus"
          : l.mode === "BICYCLE"
            ? "Bike / pushing"
            : "Walk";
    const leg = node("div", undefined, `leg ${l.mode.toLowerCase()}`);
    leg.append(
      node("strong", `${name} ${l.route?.shortName || ""}`),
      node(
        "div",
        `${l.from?.name || "Origin"} → ${l.to?.name || "Destination"}`,
      ),
      node(
        "div",
        `${clock(l.start.scheduledTime)} → ${clock(l.end.scheduledTime)}`,
      ),
    );
    details.append(leg);
  }
  container.append(details);
}
function renderPoint(p) {
  const panel = p.element;
  panel.replaceChildren();
  const head = node("div", undefined, "point-head"),
    remove = node("button", "Remove", "quiet");
  remove.type = "button";
  remove.setAttribute("aria-label", `Remove point ${p.id}`);
  remove.onclick = () => {
    p.controller?.abort();
    p.marker.remove();
    panel.remove();
    points.delete(p.id);
    routes.clearLayers();
    $("recheck").disabled = !active || !points.size;
  };
  head.append(node("h3", `Point ${p.id}`), remove);
  panel.append(
    head,
    node(
      "p",
      `${p.origin.lat.toFixed(6)}, ${p.origin.lon.toFixed(6)}`,
      "coords",
    ),
    node("p", labels[p.status] || p.status, `badge ${p.status}`),
  );
  const r = p.result;
  if (!r) return;
  if (r.error) panel.append(node("p", r.error, "error"));
  if (r.scenario)
    panel.append(
      node(
        "p",
        `${r.scenario.arrival.replace("T", " ")} Denver · ${r.scenario.mode} · target ${r.scenario.target} min`,
        "hint",
      ),
    );
  if (r.searches) {
    for (const s of r.searches) {
      if (!s.complete || s.errors.length)
        panel.append(
          node(
            "p",
            `${s.mode.toUpperCase()}: incomplete search${s.errors.length ? " / routing error" : ""}. Other alternatives may remain.`,
            "hint",
          ),
        );
    }
  }
  if (p.status === "no_qualifying_returned_route")
    panel.append(
      node(
        "p",
        "No matching journey returned by the bounded search. This is not proof of inaccessibility.",
        "hint",
      ),
    );
  if (p.status === "unknown")
    panel.append(
      node(
        "p",
        "Search or elevation evidence is incomplete; this point is not labeled unreachable.",
        "hint",
      ),
    );
  const its = r.itineraries || [];
  if (!its.length) return;
  const select = node("select");
  select.id = `alternatives-${p.id}`;
  const label = node("label", "Journey alternatives");
  label.htmlFor = select.id;
  for (const [i, it] of its.entries()) {
    const option = node(
      "option",
      `${modes(it)} · ${duration(it.elapsed_seconds)} · ${labels[it.band] || "Rejected"}`,
    );
    option.value = i;
    select.append(option);
  }
  const detail = node("div");
  panel.append(label, select, detail);
  select.onchange = () => renderItinerary(its[Number(select.value)], detail);
  select.onchange();
}
(async () => {
  try {
    config = await json("/api/config");
    const [w, s, e, n] = config.study_bounds;
    const bounds = [
      [s, w],
      [n, e],
    ];
    map.fitBounds(bounds);
    $("reset").onclick = () => map.fitBounds(bounds);
    L.rectangle(bounds, {
      interactive: false,
      color: "#526b76",
      weight: 2,
      dashArray: "6 5",
      fill: false,
    }).addTo(map);
    const [rw, rs, re, rn] = config.routing_bounds;
    L.rectangle(
      [
        [rs, rw],
        [rn, re],
      ],
      {
        interactive: false,
        color: "#91a7b0",
        weight: 1,
        dashArray: "2 6",
        fill: false,
      },
    ).addTo(map);
    const d = config.destination;
    L.circleMarker([d.lat, d.lon], {
      radius: 7,
      color: "#fff",
      weight: 2,
      fillColor: "#075b89",
      fillOpacity: 1,
    })
      .addTo(map)
      .bindTooltip("ART · southwest entrance", {
        permanent: true,
        direction: "right",
        className: "destination-label",
      });
    const streets = await json("/map-data/streets.geojson");
    L.geoJSON(streets, {
      interactive: false,
      style: (f) => ({
        color: ["primary", "secondary", "trunk"].includes(f.properties?.highway)
          ? "#a9bdc4"
          : "#c9d6da",
        weight: ["primary", "secondary", "trunk"].includes(
          f.properties?.highway,
        )
          ? 2
          : 1,
        opacity: 0.8,
      }),
    })
      .addTo(map)
      .bringToBack();
    updateLabels();
  } catch (e) {
    $("form-status").textContent = `Setup problem: ${e.message}`;
  }
})();
