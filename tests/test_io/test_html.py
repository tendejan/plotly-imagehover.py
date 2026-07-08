import pytest
import numpy as np
import re


import plotly.graph_objs as go
import plotly.io as pio
from plotly.io._utils import plotly_cdn_url
from plotly.offline.offline import get_plotlyjs
from plotly.io._html import _generate_sri_hash


@pytest.fixture
def fig1(request):
    return go.Figure(
        data=[
            {
                "type": "scatter",
                "y": np.array([2, 1, 3, 2, 4, 2]),
                "marker": {"color": "green"},
            }
        ],
        layout={"title": {"text": "Figure title"}},
    )


def test_versioned_cdn_included(fig1):
    assert plotly_cdn_url() in pio.to_html(fig1, include_plotlyjs="cdn")


def test_html_deterministic(fig1):
    div_id = "plotly-root"
    assert pio.to_html(fig1, include_plotlyjs="cdn", div_id=div_id) == pio.to_html(
        fig1, include_plotlyjs="cdn", div_id=div_id
    )


def test_cdn_includes_integrity_attribute(fig1):
    """Test that the CDN script tag includes an integrity attribute with SHA256 hash"""
    html_output = pio.to_html(fig1, include_plotlyjs="cdn")

    # Check that the script tag includes integrity attribute
    assert 'integrity="sha256-' in html_output
    assert 'crossorigin="anonymous"' in html_output

    # Verify it's in the correct script tag
    cdn_pattern = re.compile(
        r'<script[^>]*src="'
        + re.escape(plotly_cdn_url())
        + r'"[^>]*integrity="sha256-[A-Za-z0-9+/=]+"[^>]*>'
    )
    match = cdn_pattern.search(html_output)
    assert match is not None, "CDN script tag with integrity attribute not found"


def test_outer_wrapper_carries_requested_dimensions(fig1):
    """
    Regression test for https://github.com/plotly/plotly.py/issues/5591.

    The outer wrapper div produced by ``to_html`` must carry the requested
    height/width so that percentage values propagate from a parent container
    down to the figure element. Without this, a default of ``height='100%'``
    collapses to zero (because the wrapper has no height) and plotly.js falls
    back to its hardcoded 450px, breaking any responsive layout.
    """
    html = pio.to_html(fig1, include_plotlyjs="cdn", full_html=False)

    wrapper_match = re.match(r'<div style="([^"]+)">', html)
    assert wrapper_match is not None, (
        "Outer wrapper div is missing inline style; responsive parents cannot "
        "propagate dimensions to the figure."
    )
    wrapper_style = wrapper_match.group(1)
    assert "height:100%" in wrapper_style
    assert "width:100%" in wrapper_style

    inner_match = re.search(
        r'<div id="[^"]+" class="plotly-graph-div" style="([^"]+)">',
        html,
    )
    assert inner_match is not None
    assert "height:100%" in inner_match.group(1)
    assert "width:100%" in inner_match.group(1)


def test_outer_wrapper_respects_explicit_pixel_dimensions(fig1):
    """Explicit pixel dimensions must reach the outer wrapper unchanged."""
    html = pio.to_html(
        fig1,
        include_plotlyjs="cdn",
        full_html=False,
        default_width=600,
        default_height=400,
    )

    wrapper_match = re.match(r'<div style="([^"]+)">', html)
    assert wrapper_match is not None
    wrapper_style = wrapper_match.group(1)
    assert "height:400px" in wrapper_style
    assert "width:600px" in wrapper_style


def test_cdn_integrity_hash_matches_bundled_content(fig1):
    """Test that the SRI hash in CDN script tag matches the bundled plotly.js content"""
    html_output = pio.to_html(fig1, include_plotlyjs="cdn")

    # Extract the integrity hash from the HTML output
    integrity_pattern = re.compile(r'integrity="(sha256-[A-Za-z0-9+/=]+)"')
    match = integrity_pattern.search(html_output)
    assert match is not None, "Integrity attribute not found"
    extracted_hash = match.group(1)

    # Generate expected hash from bundled content
    plotlyjs_content = get_plotlyjs()
    expected_hash = _generate_sri_hash(plotlyjs_content)

    # Verify they match
    assert extracted_hash == expected_hash, (
        f"Hash mismatch: expected {expected_hash}, got {extracted_hash}"
    )


def _hover_image_post_script_marker():
    # The generated post_script has "{plot_id}" substituted with the real
    # div id when injected into HTML output, so match on the fixed prefix
    # before that placeholder rather than the raw script verbatim.
    from plotly._hover_image import get_hover_image_post_script

    return get_hover_image_post_script().split("{plot_id}")[0]


def test_hover_image_post_script_not_injected_by_default(fig1):
    html = pio.to_html(fig1)
    assert _hover_image_post_script_marker() not in html


def test_hover_image_post_script_injected_when_present():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
    fig.set_hover_images(["https://a.com/1.png", "https://a.com/2.png"])

    html = fig.to_html()
    assert _hover_image_post_script_marker() in html


def test_hover_image_post_script_composes_with_user_post_script():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
    fig.set_hover_images(["https://a.com/1.png", "https://a.com/2.png"])

    marker = "window.myCustomPostScript = true;"
    html = fig.to_html(post_script=marker)

    assert marker in html
    assert _hover_image_post_script_marker() in html
