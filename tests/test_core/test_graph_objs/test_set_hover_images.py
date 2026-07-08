import pytest

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def test_set_hover_images_no_existing_customdata():
    fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]))
    fig.set_hover_images(
        ["https://a.com/1.png", "https://a.com/2.png", "https://a.com/3.png"]
    )

    trace = fig.data[0]
    assert trace.meta == {
        "hover_image": {"customdata_index": 0, "max_width": 300, "max_height": 300}
    }
    assert list(trace.customdata[:, 0]) == [
        "https://a.com/1.png",
        "https://a.com/2.png",
        "https://a.com/3.png",
    ]


def test_set_hover_images_appends_after_existing_customdata():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[4, 5], customdata=[["a"], ["b"]]))
    fig.set_hover_images(["https://a.com/1.png", "https://a.com/2.png"])

    trace = fig.data[0]
    assert trace.meta["hover_image"]["customdata_index"] == 1
    assert list(trace.customdata[:, 0]) == ["a", "b"]
    assert list(trace.customdata[:, 1]) == [
        "https://a.com/1.png",
        "https://a.com/2.png",
    ]


def test_set_hover_images_custom_max_size():
    fig = go.Figure(go.Scatter(x=[1], y=[2]))
    fig.set_hover_images(["https://a.com/1.png"], max_width=100, max_height=50)

    assert fig.data[0].meta["hover_image"]["max_width"] == 100
    assert fig.data[0].meta["hover_image"]["max_height"] == 50


def test_set_hover_images_length_mismatch_raises():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[4, 5], customdata=[["a"], ["b"]]))
    with pytest.raises(ValueError):
        fig.set_hover_images(["https://a.com/only-one.png"])


def test_set_hover_images_non_dict_meta_raises():
    fig = go.Figure(go.Scatter(x=[1], y=[2], meta="not-a-dict"))
    with pytest.raises(ValueError):
        fig.set_hover_images(["https://a.com/1.png"])


def test_set_hover_images_selector_row_col():
    fig = make_subplots(rows=1, cols=2)
    fig.add_scatter(x=[1, 2], y=[3, 4], row=1, col=1)
    fig.add_scatter(x=[1, 2], y=[3, 4], row=1, col=2)

    fig.set_hover_images(["https://a.com/1.png", "https://a.com/2.png"], row=1, col=1)

    assert fig.data[0].meta is not None
    assert fig.data[0].meta["hover_image"]["customdata_index"] == 0
    assert fig.data[1].meta is None
