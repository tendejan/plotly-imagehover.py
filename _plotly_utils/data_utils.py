from io import BytesIO
import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from .png import Writer, from_array

try:
    from PIL import Image

    pil_imported = True
except ImportError:
    pil_imported = False


def image_array_to_data_uri(img, backend="pil", compression=4, ext="png"):
    """Converts a numpy array of uint8 into a base64 png or jpg string.

    Parameters
    ----------
    img: ndarray of uint8
        array image
    backend: str
        'auto', 'pil' or 'pypng'. If 'auto', Pillow is used if installed,
        otherwise pypng.
    compression: int, between 0 and 9
        compression level to be passed to the backend
    ext: str, 'png' or 'jpg'
        compression format used to generate b64 string
    """
    # PIL and pypng error messages are quite obscure so we catch invalid compression values
    if compression < 0 or compression > 9:
        raise ValueError("compression level must be between 0 and 9.")
    alpha = False
    if img.ndim == 2:
        mode = "L"
    elif img.ndim == 3 and img.shape[-1] == 3:
        mode = "RGB"
    elif img.ndim == 3 and img.shape[-1] == 4:
        mode = "RGBA"
        alpha = True
    else:
        raise ValueError("Invalid image shape")
    if backend == "auto":
        backend = "pil" if pil_imported else "pypng"
    if ext != "png" and backend != "pil":
        raise ValueError("jpg binary strings are only available with PIL backend")

    if backend == "pypng":
        ndim = img.ndim
        sh = img.shape
        if ndim == 3:
            img = img.reshape((sh[0], sh[1] * sh[2]))
        w = Writer(
            sh[1], sh[0], greyscale=(ndim == 2), alpha=alpha, compression=compression
        )
        img_png = from_array(img, mode=mode)
        prefix = "data:image/png;base64,"
        with BytesIO() as stream:
            w.write(stream, img_png.rows)
            base64_string = prefix + base64.b64encode(stream.getvalue()).decode("utf-8")
    else:  # pil
        if not pil_imported:
            raise ImportError(
                "pillow needs to be installed to use `backend='pil'. Please"
                "install pillow or use `backend='pypng'."
            )
        pil_img = Image.fromarray(img)
        if ext == "jpg" or ext == "jpeg":
            prefix = "data:image/jpeg;base64,"
            ext = "jpeg"
        else:
            prefix = "data:image/png;base64,"
            ext = "png"
        with BytesIO() as stream:
            pil_img.save(stream, format=ext, compress_level=compression)
            base64_string = prefix + base64.b64encode(stream.getvalue()).decode("utf-8")
    return base64_string


def image_source_to_data_uri(source):
    """Normalize a single image source into a string usable directly as an
    <img src="..."> value, with no dependency on an external file server.

    Parameters
    ----------
    source: str or PIL.Image.Image
        - A string already starting with "data:" is returned unchanged.
        - A string that looks like an http(s) URL is returned unchanged.
        - Any other string is treated as a local filesystem path: its bytes
          are read and base64-encoded into a data URI, with the MIME type
          guessed from the file extension.
        - A PIL.Image.Image is encoded as a PNG data URI.

    Returns
    -------
    str

    Raises
    ------
    TypeError
        If `source` is neither a string nor a PIL.Image.Image.
    FileNotFoundError
        If `source` is a string that is not a data URI or an http(s) URL,
        and no file exists at that path.
    """
    if pil_imported and isinstance(source, Image.Image):
        from _plotly_utils.basevalidators import ImageUriValidator

        return ImageUriValidator.pil_image_to_uri(source)

    if not isinstance(source, str):
        raise TypeError(
            "image source must be a string (file path, URL, or data URI) "
            "or a PIL.Image.Image, received value of type %s" % type(source)
        )

    if source.startswith("data:"):
        return source

    if urlparse(source).scheme in ("http", "https"):
        return source

    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(
            "Image source is not a data URI, an http(s) URL, or an existing "
            "file path: %r" % source
        )

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    base64_string = base64.b64encode(path.read_bytes()).decode("utf-8")
    return "data:%s;base64,%s" % (mime_type, base64_string)
