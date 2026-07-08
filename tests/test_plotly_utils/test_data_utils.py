import base64

import pytest

from _plotly_utils.data_utils import image_source_to_data_uri


def test_data_uri_passthrough():
    uri = "data:image/png;base64,ABCD"
    assert image_source_to_data_uri(uri) == uri


@pytest.mark.parametrize(
    "url", ["http://example.com/a.png", "https://example.com/a.png"]
)
def test_url_passthrough(url):
    assert image_source_to_data_uri(url) == url


def test_local_path_encoding(tmp_path):
    content = b"some-arbitrary-bytes"
    path = tmp_path / "img.png"
    path.write_bytes(content)

    result = image_source_to_data_uri(str(path))

    assert result.startswith("data:image/png;base64,")
    encoded = result.split(",", 1)[1]
    assert base64.b64decode(encoded) == content


def test_local_path_mime_type_guessed_from_extension(tmp_path):
    path = tmp_path / "img.jpg"
    path.write_bytes(b"jpegbytes")

    result = image_source_to_data_uri(str(path))

    assert result.startswith("data:image/jpeg;base64,")


def test_missing_file_raises(tmp_path):
    missing = tmp_path / "does-not-exist.png"
    with pytest.raises(FileNotFoundError):
        image_source_to_data_uri(str(missing))


def test_non_string_non_pil_raises_type_error():
    with pytest.raises(TypeError):
        image_source_to_data_uri(12345)


def test_pil_image_encoded_as_png():
    pil = pytest.importorskip("PIL.Image")
    img = pil.new("RGB", (2, 2))

    result = image_source_to_data_uri(img)

    assert result.startswith("data:image/png;base64,")
