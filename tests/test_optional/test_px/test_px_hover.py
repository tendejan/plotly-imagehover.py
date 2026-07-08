import plotly.express as px
import narwhals.stable.v1 as nw
import numpy as np
import pandas as pd
import pytest
from collections import OrderedDict  # an OrderedDict is needed for Python 2


@pytest.fixture
def hover_image_df(tmp_path):
    img_path_1 = tmp_path / "a.png"
    img_path_2 = tmp_path / "b.png"
    img_path_1.write_bytes(b"fake-png-bytes-a")
    img_path_2.write_bytes(b"fake-png-bytes-b")
    return pd.DataFrame(
        {
            "x": [1, 2],
            "y": [3, 4],
            "label": ["p", "q"],
            "img": [str(img_path_1), str(img_path_2)],
        }
    )


def test_hover_image_scatter_local_path(hover_image_df):
    fig = px.scatter(hover_image_df, x="x", y="y", hover_image="img")
    trace = fig.data[0]
    index = trace.meta["hover_image"]["customdata_index"]
    assert trace.meta["hover_image"] == {
        "customdata_index": index,
        "max_width": 300,
        "max_height": 300,
    }
    assert index == 0
    for value in trace.customdata[:, index]:
        assert value.startswith("data:image/png;base64,")


def test_hover_image_scatter_url_passthrough(hover_image_df):
    df = hover_image_df.assign(
        img=["https://example.com/a.png", "https://example.com/b.png"]
    )
    fig = px.scatter(df, x="x", y="y", hover_image="img")
    trace = fig.data[0]
    index = trace.meta["hover_image"]["customdata_index"]
    assert list(trace.customdata[:, index]) == [
        "https://example.com/a.png",
        "https://example.com/b.png",
    ]


def test_hover_image_with_custom_data_and_hover_data(hover_image_df):
    fig = px.scatter(
        hover_image_df,
        x="x",
        y="y",
        hover_image="img",
        custom_data=["label"],
        hover_data=["x"],
    )
    trace = fig.data[0]
    index = trace.meta["hover_image"]["customdata_index"]
    # custom_data + hover_data ("x") occupy the earlier columns; the
    # hover-image column is appended last and doesn't disturb them.
    assert index == trace.customdata.shape[1] - 1
    assert list(trace.customdata[:, 0]) == list(hover_image_df["label"])
    for value in trace.customdata[:, index]:
        assert value.startswith("data:image/png;base64,")


def test_hover_image_not_in_hovertemplate(hover_image_df):
    fig = px.scatter(hover_image_df, x="x", y="y", hover_image="img")
    trace = fig.data[0]
    index = trace.meta["hover_image"]["customdata_index"]
    assert ("customdata[%d]" % index) not in trace.hovertemplate
    for value in trace.customdata[:, index]:
        assert value not in trace.hovertemplate


def test_hover_image_missing_file_raises(hover_image_df):
    df = hover_image_df.assign(img=["/nonexistent/a.png", "/nonexistent/b.png"])
    with pytest.raises(FileNotFoundError):
        px.scatter(df, x="x", y="y", hover_image="img")


def test_skip_hover(backend):
    df = px.data.iris(return_type=backend)
    fig = px.scatter(
        df,
        x="petal_length",
        y="petal_width",
        size="species_id",
        hover_data={"petal_length": None, "petal_width": None},
    )
    assert fig.data[0].hovertemplate == "species_id=%{marker.size}<extra></extra>"


def test_hover_data_string_column(backend):
    df = px.data.tips(return_type=backend)
    fig = px.scatter(
        df,
        x="tip",
        y="total_bill",
        hover_data="sex",
    )
    assert "sex" in fig.data[0].hovertemplate


def test_composite_hover(backend):
    df = px.data.tips(return_type=backend)
    hover_dict = OrderedDict(
        {"day": False, "time": False, "sex": True, "total_bill": ":.1f"}
    )
    fig = px.scatter(
        df,
        x="tip",
        y="total_bill",
        color="day",
        facet_row="time",
        hover_data=hover_dict,
    )
    for el in ["tip", "total_bill", "sex"]:
        assert el in fig.data[0].hovertemplate
    for el in ["day", "time"]:
        assert el not in fig.data[0].hovertemplate
    assert ":.1f" in fig.data[0].hovertemplate


def test_newdatain_hover_data():
    hover_dicts = [
        {"comment": ["a", "b", "c"]},
        {"comment": (1.234, 45.3455, 5666.234)},
        {"comment": [1.234, 45.3455, 5666.234]},
        {"comment": np.array([1.234, 45.3455, 5666.234])},
        {"comment": pd.Series([1.234, 45.3455, 5666.234])},
    ]
    for hover_dict in hover_dicts:
        fig = px.scatter(x=[1, 2, 3], y=[3, 4, 5], hover_data=hover_dict)
        assert (
            fig.data[0].hovertemplate
            == "x=%{x}<br>y=%{y}<br>comment=%{customdata[0]}<extra></extra>"
        )
    fig = px.scatter(
        x=[1, 2, 3], y=[3, 4, 5], hover_data={"comment": (True, ["a", "b", "c"])}
    )
    assert (
        fig.data[0].hovertemplate
        == "x=%{x}<br>y=%{y}<br>comment=%{customdata[0]}<extra></extra>"
    )
    hover_dicts = [
        {"comment": (":.1f", (1.234, 45.3455, 5666.234))},
        {"comment": (":.1f", [1.234, 45.3455, 5666.234])},
        {"comment": (":.1f", np.array([1.234, 45.3455, 5666.234]))},
        {"comment": (":.1f", pd.Series([1.234, 45.3455, 5666.234]))},
    ]
    for hover_dict in hover_dicts:
        fig = px.scatter(
            x=[1, 2, 3],
            y=[3, 4, 5],
            hover_data=hover_dict,
        )
        assert (
            fig.data[0].hovertemplate
            == "x=%{x}<br>y=%{y}<br>comment=%{customdata[0]:.1f}<extra></extra>"
        )


def test_formatted_hover_and_labels(backend):
    df = px.data.tips(return_type=backend)
    fig = px.scatter(
        df,
        x="tip",
        y="total_bill",
        hover_data={"total_bill": ":.1f"},
        labels={"total_bill": "Total bill"},
    )
    assert ":.1f" in fig.data[0].hovertemplate


def test_fail_wrong_column():
    # Testing for each of bare string, list, and basic dictionary
    for hover_data_value in ["d", ["d"], {"d": True}]:
        with pytest.raises(ValueError) as err_msg:
            px.scatter(
                {"a": [1, 2], "b": [3, 4], "c": [2, 1]},
                x="a",
                y="b",
                hover_data=hover_data_value,
            )
        assert (
            "Value of 'hover_data_0' is not the name of a column in 'data_frame'."
            in str(err_msg.value)
        )
    # Testing other dictionary possibilities below
    with pytest.raises(ValueError) as err_msg:
        px.scatter(
            {"a": [1, 2], "b": [3, 4], "c": [2, 1]},
            x="a",
            y="b",
            hover_data={"d": ":.1f"},
        )
    assert (
        "Value of 'hover_data_0' is not the name of a column in 'data_frame'."
        in str(err_msg.value)
    )
    with pytest.raises(ValueError) as err_msg:
        px.scatter(
            {"a": [1, 2], "b": [3, 4], "c": [2, 1]},
            x="a",
            y="b",
            hover_data={"d": [3, 4, 5]},  # d is too long
        )
    assert (
        "All arguments should have the same length. The length of hover_data key `d` is 3"
        in str(err_msg.value)
    )
    with pytest.raises(ValueError) as err_msg:
        px.scatter(
            {"a": [1, 2], "b": [3, 4], "c": [2, 1]},
            x="a",
            y="b",
            hover_data={"d": (True, [3, 4, 5])},  # d is too long
        )
    assert (
        "All arguments should have the same length. The length of hover_data key `d` is 3"
        in str(err_msg.value)
    )
    with pytest.raises(ValueError) as err_msg:
        px.scatter(
            {"a": [1, 2], "b": [3, 4], "c": [2, 1]},
            x="a",
            y="b",
            hover_data={"c": [3, 4]},
        )
    assert (
        "Ambiguous input: values for 'c' appear both in hover_data and data_frame"
        in str(err_msg.value)
    )
    with pytest.raises(ValueError) as err_msg:
        px.scatter(
            {"a": [1, 2], "b": [3, 4], "c": [2, 1]},
            x="a",
            y="b",
            hover_data={"c": (True, [3, 4])},
        )
    assert (
        "Ambiguous input: values for 'c' appear both in hover_data and data_frame"
        in str(err_msg.value)
    )


def test_sunburst_hoverdict_color(backend):
    df = px.data.gapminder(year=2007, return_type=backend)
    fig = px.sunburst(
        df,
        path=["continent", "country"],
        values="pop",
        color="lifeExp",
        hover_data={"pop": ":,"},
    )
    assert "color" in fig.data[0].hovertemplate


def test_date_in_hover(constructor):
    df = nw.from_native(
        constructor({"date": ["2015-04-04 19:31:30+0100"], "value": [3]})
    ).with_columns(date=nw.col("date").str.to_datetime(format="%Y-%m-%d %H:%M:%S%z"))
    fig = px.scatter(df.to_native(), x="value", y="value", hover_data=["date"])

    # Check that what gets displayed is the local datetime
    assert nw.to_py_scalar(fig.data[0].customdata[0][0]) == nw.to_py_scalar(
        df.item(row=0, column="date")
    ).replace(tzinfo=None)
