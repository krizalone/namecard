#!/usr/bin/env python3
"""
Build script for The Tilak Card.

Generates, from photo.jpg and the details below:
  site/naveena-neerada-dasa.vcf  vCard 3.0 with embedded photo (for "Save My Contact")
  site/qr-contact.svg            QR code of the vCard without photo (error correction M)
  site/img/naveena.webp/.jpg     web portrait for the page (cropped to the 300x385 frame)

Requirements:  pip install pillow segno
Usage:         python build-vcf.py

Edit CONTACT below, re-run, and redeploy the site/ folder.
"""

import base64
import io
from pathlib import Path

from PIL import Image, ImageOps
import segno

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
PHOTO = ROOT / "photo.jpg"  # original, never modified

# Portrait crop from photo.jpg (left, top, right, bottom), then sized to
# PORTRAIT_SIZE. Matches the card frame: head near the top, shoulders at the bottom.
PORTRAIT_CROP = (63, 3, 433, 478)
PORTRAIT_SIZE = (300, 385)
# The frame is taller than a 300x385 photo fills. The old photo's white background
# blended into the frame's white fill; this one has a dark backdrop, so the web
# portrait extends its own top row upward to fill the frame (no hard edge).
PORTRAIT_TOP_PAD = 44

CONTACT = {
    "first": "Naveena Neerada",
    "last": "Dasa",
    "full": "Naveena Neerada Dasa",
    "org": "World Food Movement & The Akshaya Patra Foundation",
    "title": "Executive Director",
    "tel": "+18483389180",
    "email": "nnrd@iskconbangalore.org",
    "website": "https://wfmnj.org",
    "instagram": "https://www.instagram.com/naveenadasa/",
    "linkedin": "https://www.linkedin.com/in/naveena-neerada-dasa",
    # ADR fields: street, city, region, postal code, country
    "street": "7 Kilmer Ct",
    "city": "Edison",
    "region": "NJ",
    "postal": "08817",
    "country": "USA",
}

QR_DARK = "#1c120c"  # near-black warm brown: high contrast, still on-palette


def esc(value: str) -> str:
    """Escape a vCard 3.0 text value."""
    return (value.replace("\\", "\\\\").replace(",", "\\,")
                 .replace(";", "\\;").replace("\n", "\\n"))


def fold(line: str) -> str:
    """Fold a content line at 75 octets (RFC 2425); continuation lines start with a space."""
    data = line.encode("utf-8")
    if len(data) <= 75:
        return line
    parts, first = [], True
    while data:
        size = 75 if first else 74
        chunk = data[:size]
        # never split a multi-byte UTF-8 sequence
        while True:
            try:
                text = chunk.decode("utf-8")
                break
            except UnicodeDecodeError:
                chunk = chunk[:-1]
        parts.append(text if first else " " + text)
        data = data[len(chunk):]
        first = False
    return "\r\n".join(parts)


def vcard_lines(c: dict, photo_b64: str | None = None, extras: bool = True) -> list[str]:
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{esc(c['last'])};{esc(c['first'])};;;",
        f"FN:{esc(c['full'])}",
        f"ORG:{esc(c['org'])}",
        f"TITLE:{esc(c['title'])}",
        f"TEL;TYPE=CELL,VOICE:{c['tel']}",
        f"EMAIL;TYPE=INTERNET,WORK:{c['email']}",
        f"URL;TYPE=WORK:{c['website']}",
    ]
    if extras:
        lines += [
            f"item1.URL:{c['instagram']}",
            "item1.X-ABLabel:Instagram",
            f"item2.URL:{c['linkedin']}",
            "item2.X-ABLabel:LinkedIn",
        ]
    lines.append(
        f"ADR;TYPE=WORK:;;{esc(c['street'])};{esc(c['city'])};"
        f"{esc(c['region'])};{esc(c['postal'])};{esc(c['country'])}"
    )
    if photo_b64:
        lines.append(f"PHOTO;ENCODING=b;TYPE=JPEG:{photo_b64}")
    lines.append("END:VCARD")
    return lines


def contact_photo_b64() -> str:
    """Square ~300px crop, head-and-shoulders, compressed. Pixels are only cropped and resized."""
    im = portrait_image()
    w, h = im.size
    side = min(w, h)
    top = max(0, min(h - side, int(h * 0.02)))  # keep the head near the top of the square
    left = (w - side) // 2
    im = im.crop((left, top, left + side, top + side))
    if side > 300:
        im = im.resize((300, 300), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True, progressive=False)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def build_vcf() -> None:
    lines = vcard_lines(CONTACT, contact_photo_b64())
    text = "\r\n".join(fold(l) for l in lines) + "\r\n"
    out = SITE / "naveena-neerada-dasa.vcf"
    out.write_bytes(text.encode("utf-8"))
    print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size / 1024:.1f} KB)")


def build_qr() -> None:
    # Offline-scannable contact: no photo, no social links and terse property
    # parameters, so the code stays low-density and easy to scan.
    c = CONTACT
    payload = "\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{esc(c['last'])};{esc(c['first'])}",
        f"FN:{esc(c['full'])}",
        f"ORG:{esc(c['org'])}",
        f"TITLE:{esc(c['title'])}",
        f"TEL;TYPE=CELL:{c['tel']}",
        f"EMAIL:{c['email']}",
        f"URL:{c['website']}",
        f"ADR;TYPE=WORK:;;{esc(c['street'])};{esc(c['city'])};{esc(c['region'])};{esc(c['postal'])}",
        "END:VCARD",
    ])
    qr = segno.make(payload, error="m", micro=False, boost_error=False)
    out = SITE / "qr-contact.svg"
    qr.save(str(out), kind="svg", scale=1, border=4, dark=QR_DARK, light=None,
            xmldecl=False, omitsize=True, title="Contact card QR code for Naveena Neerada Dasa")
    # Keep module edges sharp when the browser scales the SVG.
    svg = out.read_text(encoding="utf-8")
    out.write_text(svg.replace("<svg ", '<svg shape-rendering="crispEdges" ', 1), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}  (QR version {qr.version}, "
          f"{qr.symbol_size(border=4)[0]} modules incl. quiet zone, {len(payload)} bytes)")


def portrait_image() -> Image.Image:
    """photo.jpg cropped and sized to the card's portrait frame. Crop and resize only; no retouching."""
    im = ImageOps.exif_transpose(Image.open(PHOTO)).convert("RGB")
    return im.crop(PORTRAIT_CROP).resize(PORTRAIT_SIZE, Image.LANCZOS)


def web_portrait() -> Image.Image:
    """portrait_image() with its top row extended by PORTRAIT_TOP_PAD px of matching backdrop."""
    im = portrait_image()
    w, h = im.size
    out = Image.new("RGB", (w, h + PORTRAIT_TOP_PAD))
    out.paste(im.crop((0, 0, w, 1)).resize((w, PORTRAIT_TOP_PAD)), (0, 0))
    out.paste(im, (0, PORTRAIT_TOP_PAD))
    return out


def build_portrait() -> None:
    """Write the web portrait (WebP + JPEG fallback)."""
    img_dir = SITE / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    im = web_portrait()
    im.save(img_dir / "naveena.webp", "WEBP", quality=86, method=6)
    im.save(img_dir / "naveena.jpg", "JPEG", quality=86, optimize=True, progressive=True)
    for name in ("naveena.webp", "naveena.jpg"):
        p = img_dir / name
        print(f"wrote {p.relative_to(ROOT)}  ({im.width}x{im.height}, {p.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    SITE.mkdir(exist_ok=True)
    build_portrait()
    build_vcf()
    build_qr()
