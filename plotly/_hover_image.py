import pathlib
from functools import lru_cache

DEFAULT_MAX_WIDTH = 300
DEFAULT_MAX_HEIGHT = 300

_POST_SCRIPT_PATH = (
    pathlib.Path(__file__).parent / "package_data" / "hover_image_post_script.js"
)


def build_hover_image_meta(
    existing_meta,
    customdata_index,
    max_width=DEFAULT_MAX_WIDTH,
    max_height=DEFAULT_MAX_HEIGHT,
):
    """Merge hover-image bookkeeping into a trace's existing `meta` value.

    Raises
    ------
    ValueError
        If `existing_meta` is neither None nor a dict, since hover-image
        metadata must live inside a dict-shaped `meta` and we refuse to
        silently clobber a user's own non-dict `meta` (e.g. one used for
        `%{meta}` hovertemplate substitution).
    """
    if existing_meta is not None and not isinstance(existing_meta, dict):
        raise ValueError(
            "Cannot attach hover-image metadata to a trace whose `meta` is "
            "already set to a non-dict value (%r). Hover images store their "
            "bookkeeping inside `meta['hover_image']`, so `meta` must be a "
            "dict or unset." % (existing_meta,)
        )

    new_meta = dict(existing_meta) if existing_meta else {}
    new_meta["hover_image"] = {
        "customdata_index": customdata_index,
        "max_width": max_width,
        "max_height": max_height,
    }
    return new_meta


def figure_has_hover_images(fig):
    """True if any trace in `fig.data` carries hover-image metadata."""
    return any(
        isinstance(trace.meta, dict) and "hover_image" in trace.meta
        for trace in fig.data
    )


@lru_cache(maxsize=1)
def get_hover_image_post_script():
    """Return the compiled JS that installs the hover-image overlay.

    Built by `npm run build:postscript` (see js/package.json) from
    js/src/hoverImagePostScript.ts into plotly/package_data/hover_image_post_script.js.
    """
    return _POST_SCRIPT_PATH.read_text(encoding="utf-8")


def merge_post_script(user_post_script, generated_post_script):
    """Normalize `user_post_script` (None / str / list / tuple) and append
    `generated_post_script`, returning a list. Mirrors the composition
    convention already used by HtmlRenderer.to_mimebundle() and to_html().
    """
    if user_post_script is None:
        post_scripts = []
    elif isinstance(user_post_script, str):
        post_scripts = [user_post_script]
    else:
        post_scripts = list(user_post_script)

    return post_scripts + [generated_post_script]
