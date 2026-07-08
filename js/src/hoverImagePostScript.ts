// Entry point bundled to plotly/package_data/hover_image_post_script.js and
// injected via the `post_script` hook of plotly/io/_html.py::to_html() (see
// plotly/_hover_image.py::get_hover_image_post_script and
// plotly/basedatatypes.py::_maybe_inject_hover_image_post_script). The
// "{plot_id}" placeholder is substituted by to_html() with the id of the
// div the plotly.js figure was created in, exactly like any other
// post_script string.

import { installHoverImageOverlay } from "./hoverImageOverlay";

installHoverImageOverlay(document.getElementById("{plot_id}"));
