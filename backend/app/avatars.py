"""Turning an uploaded file into the one image shape this app is willing to store.

Nothing a user uploads is ever handed back to another browser as it arrived.
The bytes are decoded, cropped, and re-encoded, which is what makes "a file
someone picked" safe to serve: the re-encode drops anything that is not pixels,
including the EXIF block that carries GPS coordinates on most phone photos, and
it settles the content type rather than trusting the one the client claimed.
"""
import io

from PIL import Image, ImageOps, UnidentifiedImageError

# Stored square, so every caller can draw a circle without knowing the source
# aspect ratio. 512px covers a retina rendering of the largest avatar in the UI.
AVATAR_SIZE = 512
AVATAR_CONTENT_TYPE = "image/webp"
_AVATAR_FORMAT = "WEBP"
_AVATAR_QUALITY = 82

# What Pillow may be asked to decode. Deliberately a short list of raster
# formats: SVG is not here because an SVG is a document that can run script.
ACCEPTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF"})

# A 40MP source is already far more than a 512px avatar needs, and refusing
# larger ones keeps a decompression bomb from turning into gigabytes of RGBA.
MAX_SOURCE_PIXELS = 40_000_000


class AvatarError(ValueError):
    """An upload that cannot become an avatar. The message is user-facing."""


def normalize_avatar(raw: bytes) -> bytes:
    """Decode `raw`, centre-crop it to a square, and re-encode it as WebP.

    Raises AvatarError with a message worth showing the user.
    """
    if not raw:
        raise AvatarError("That file is empty.")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ACCEPTED_FORMATS:
                raise AvatarError("That file is not an image we can read.")
            width, height = image.size
            if width < 1 or height < 1:
                raise AvatarError("That image has no pixels.")
            # image.size comes from the header, so this rejects a bomb before
            # the decode below allocates anything for it.
            if width * height > MAX_SOURCE_PIXELS:
                raise AvatarError("That image is too large. Try one under 40 megapixels.")

            # Phone cameras record orientation in EXIF rather than rotating the
            # pixels; apply it here, because the re-encode is about to throw the
            # EXIF away and a sideways avatar would be the only trace left.
            oriented = ImageOps.exif_transpose(image)
            # Never upscale: a 64px upload should stay crisp and small rather
            # than being blurred up to 512.
            side = min(AVATAR_SIZE, oriented.width, oriented.height)
            square = ImageOps.fit(
                oriented, (side, side), method=Image.LANCZOS, centering=(0.5, 0.5)
            )
            square = square.convert("RGBA" if _has_alpha(oriented) else "RGB")

            out = io.BytesIO()
            square.save(out, _AVATAR_FORMAT, quality=_AVATAR_QUALITY, method=4)
    except AvatarError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as err:
        # Pillow reports a truncated or malformed file through any of these.
        raise AvatarError("That image could not be read. Try a JPEG or PNG.") from err
    return out.getvalue()


def _has_alpha(image: Image.Image) -> bool:
    """True when discarding the alpha channel would visibly change the image."""
    return image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )


def avatar_version(user) -> str | None:
    """The timestamp a user's avatar last changed, or None if they have none.

    Callers put this in responses so the frontend knows whether an avatar
    exists at all — without it, every picture-less user would cost a 404 — and
    so a freshly uploaded picture wins over the browser's cached copy.
    """
    picture = getattr(user, "profile_picture", None) if user else None
    if picture is None or picture.updated_at is None:
        return None
    return picture.updated_at.isoformat()
