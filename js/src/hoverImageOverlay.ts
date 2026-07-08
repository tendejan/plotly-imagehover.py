// Installs a floating, cursor-following image tooltip on a plotly.js graph
// div. Shared by js/src/widget.ts (FigureWidget), js/src/mimeExtension.ts
// (the default JupyterLab/VSCode/nteract renderer), and, compiled as a
// standalone bundle via hoverImagePostScript.ts, by plain HTML output
// (fig.show() in a browser, write_html()) through the `post_script` hook.
//
// A trace opts in by setting `meta.hover_image = {customdata_index, max_width,
// max_height}` and appending the (already base64-encoded, if local)
// image source as a customdata column at that index -- see
// plotly/_hover_image.py and plotly/basedatatypes.py::set_hover_images
// on the Python side. This module has no dependency on anywidget,
// JupyterLab, or Lumino: it only relies on plotly.js's own DOM events and
// browser DOM APIs, so it can be installed unconditionally, with the
// per-hover-event `meta` check acting as the opt-in/opt-out.

const DEFAULT_MAX_WIDTH = 300;
const DEFAULT_MAX_HEIGHT = 300;
const CURSOR_OFFSET = 16;

interface HoverImageMeta {
  customdata_index: number;
  max_width?: number;
  max_height?: number;
}

const installedGraphDivs = new WeakSet<object>();

function getHoverImageMeta(point: any): HoverImageMeta | null {
  const meta = point && point.data ? point.data.meta : null;
  if (meta && typeof meta === "object" && meta.hover_image) {
    return meta.hover_image as HoverImageMeta;
  }
  return null;
}

function getImageSource(point: any, meta: HoverImageMeta): string | null {
  const row = point.customdata;
  const value = Array.isArray(row) ? row[meta.customdata_index] : row;
  return typeof value === "string" && value.length > 0 ? value : null;
}

function createOverlayElement(): { container: HTMLDivElement; img: HTMLImageElement } {
  const container = document.createElement("div");
  container.style.cssText = [
    "position: fixed",
    "display: none",
    "pointer-events: none",
    "z-index: 2147483647",
    "background: #fff",
    "border: 1px solid rgba(0, 0, 0, 0.2)",
    "border-radius: 4px",
    "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25)",
    "padding: 4px",
    "line-height: 0",
  ].join(";");

  const img = document.createElement("img");
  img.style.cssText = "display: block;";
  container.appendChild(img);
  document.body.appendChild(container);

  return { container, img };
}

/**
 * Install the hover-image overlay on `gd`, a plotly.js graph div (i.e. an
 * element that has already had Plotly.newPlot/react called on it, or will
 * before any `plotly_hover` event can fire). Idempotent: calling this more
 * than once on the same element is a no-op after the first call.
 */
export function installHoverImageOverlay(gd: any): void {
  if (!gd || installedGraphDivs.has(gd)) {
    return;
  }
  installedGraphDivs.add(gd);

  const { container, img } = createOverlayElement();
  let visible = false;
  let lastX = 0;
  let lastY = 0;
  let haveMousePosition = false;

  function position(clientX: number, clientY: number) {
    // Measure after the image has (possibly) loaded/changed size.
    const rect = container.getBoundingClientRect();
    let left = clientX + CURSOR_OFFSET;
    let top = clientY + CURSOR_OFFSET;

    if (left + rect.width > window.innerWidth) {
      left = clientX - CURSOR_OFFSET - rect.width;
    }
    if (top + rect.height > window.innerHeight) {
      top = clientY - CURSOR_OFFSET - rect.height;
    }
    container.style.left = Math.max(0, left) + "px";
    container.style.top = Math.max(0, top) + "px";
  }

  function hide() {
    visible = false;
    container.style.display = "none";
  }

  function onHover(data: any) {
    const points = data && data.points;
    if (!points || !points.length) {
      hide();
      return;
    }
    const point = points[0];
    const meta = getHoverImageMeta(point);
    const src = meta ? getImageSource(point, meta) : null;
    if (!meta || !src) {
      hide();
      return;
    }

    img.src = src;
    img.style.maxWidth = (meta.max_width || DEFAULT_MAX_WIDTH) + "px";
    img.style.maxHeight = (meta.max_height || DEFAULT_MAX_HEIGHT) + "px";
    container.style.display = "block";
    visible = true;

    const evt = data.event;
    if (evt && typeof evt.clientX === "number") {
      lastX = evt.clientX;
      lastY = evt.clientY;
      haveMousePosition = true;
    } else if (!haveMousePosition && gd.getBoundingClientRect) {
      // No mouse position observed yet (e.g. hover triggered
      // programmatically); fall back to the hovered point's pixel
      // position within the graph div.
      const gdRect = gd.getBoundingClientRect();
      lastX = gdRect.left + (point.xPixel || 0);
      lastY = gdRect.top + (point.yPixel || 0);
    }
    position(lastX, lastY);
    // Re-position once the image has loaded, since its size (and
    // therefore the viewport-edge clamping) isn't known until then.
    img.onload = () => {
      if (visible) {
        position(lastX, lastY);
      }
    };
  }

  function onMouseMove(event: MouseEvent) {
    lastX = event.clientX;
    lastY = event.clientY;
    haveMousePosition = true;
    if (visible) {
      position(lastX, lastY);
    }
  }

  gd.on("plotly_hover", onHover);
  gd.on("plotly_unhover", hide);
  gd.addEventListener("mousemove", onMouseMove);
}
