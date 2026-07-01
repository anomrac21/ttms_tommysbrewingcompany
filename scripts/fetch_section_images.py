#!/usr/bin/env python3
"""Update content/*/_index.md to icon + images.primary (client assets + Pexels)."""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
IMAGES_DIR = ROOT / "static" / "images"

PEX = "https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&w=900"

PEXELS: dict[str, tuple[str, str]] = {
    "wine.webp": (PEX.format(id="1283219"), "Pexels #1283219"),
    "craft-cocktails.webp": (PEX.format(id="274192"), "Pexels #274192"),
    "non-alcoholic.webp": (PEX.format(id="1267325"), "Pexels #1267325"),
}

SECTIONS: dict[str, str] = {
    "promotions": "Beer_bites_cover_1500x.webp",
    "burgers-and-sandwiches": "Signature_burger_1296x.webp",
    "beer-bites": "Beer_bites_cover_1500x.webp",
    "sides-extras": "BIRRIA.webp",
    "little-brewers": "yuca_frita.webp",
    "mains": "MEAL.webp",
    "street-tacos": "BAJA.webp",
    "salads-bowls": "SALAD.webp",
    "desserts": "brownie_720x.webp",
    "draft-beer": "Beer_bites_cover_1500x.webp",
    "wine": "wine.webp",
    "craft-cocktails": "craft-cocktails.webp",
    "non-alcoholic": "non-alcoholic.webp",
}


def img(name: str) -> str:
    return f"images/{name}"


def download_pexels(filename: str, url: str) -> bool:
    from PIL import Image

    webp = IMAGES_DIR / filename
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"SKIP {filename}: HTTP {e.code}")
        return webp.exists()
    Image.open(BytesIO(data)).save(webp, "WEBP", quality=85)
    print(f"OK {filename}")
    return True


def body_after_frontmatter(raw: str) -> str:
    if raw.count("---") < 2:
        return raw.strip()
    return raw.split("---", 2)[2].strip()


def legacy_section_image(raw: str) -> str | None:
    for key in ("image", "top"):
        m = re.search(rf"^\s*{key}:\s*(.+)$", raw, re.M)
        if not m:
            continue
        path = m.group(1).strip()
        if path.startswith("images/"):
            return path.split("/", 1)[1]
        if not path.startswith("http") and not path.startswith("/"):
            return path
    return None


def update_section_index(section: str, image_file: str) -> None:
    path = CONTENT / section / "_index.md"
    if not path.exists():
        return
    raw = path.read_text(encoding="utf-8")
    title_m = re.search(r"^title:\s*(.+)$", raw, re.M)
    weight_m = re.search(r"^weight:\s*(.+)$", raw, re.M)
    title = title_m.group(1).strip().strip('"') if title_m else section.replace("-", " ").title()
    weight = weight_m.group(1).strip().strip('"') if weight_m else "1"
    body = body_after_frontmatter(raw)

    legacy = legacy_section_image(raw)
    if legacy and (IMAGES_DIR / legacy).exists():
        image_file = legacy

    lines = [
        "---",
        f"title: {title}",
        f"weight: {weight}",
        f"icon: {img(image_file)}",
        "images:",
        f"    primary: {img(image_file)}",
        "---",
    ]
    if body:
        lines.extend(["", body])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def update_home_index() -> None:
    path = CONTENT / "_index.md"
    body = body_after_frontmatter(path.read_text(encoding="utf-8"))
    if not body.strip():
        body = "<p>Tommy's Brewing Company – craft beer and great food.</p>"
    text = (
        "---\n"
        'title: "Tommy\'s Brewing Company"\n'
        f"image: {img('MENU_HEADER_1512x.webp')}\n"
        "images:\n"
        f"    - image: {img('MENU_HEADER_1512x.webp')}\n"
        f"    - image: {img('Beer_bites_cover_1500x.webp')}\n"
        f"    - image: {img('Signature_burger_1296x.webp')}\n"
        f"    - image: {img('BAJA.webp')}\n"
        "slideshow:\n"
        f"    - image: {img('MENU_HEADER_1512x.webp')}\n"
        f"    - image: {img('Beer_bites_cover_1500x.webp')}\n"
        f"    - image: {img('Signature_burger_1296x.webp')}\n"
        f"    - image: {img('wings.webp')}\n"
        f"    - image: {img('brownie_720x.webp')}\n"
        f"    - image: {img('SALAD.webp')}\n"
        "---"
    )
    text += f"\n\n{body}\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    credits: list[str] = []

    for filename, (url, credit) in PEXELS.items():
        if download_pexels(filename, url):
            credits.append(f"- {filename} — {credit}")

    missing: list[str] = []
    for section, image_file in SECTIONS.items():
        if not (IMAGES_DIR / image_file).exists():
            missing.append(f"{section} → {image_file}")

    if missing:
        print("Missing images:")
        for line in missing:
            print(f"  {line}")
        return

    for section, image_file in SECTIONS.items():
        update_section_index(section, image_file)

    update_home_index()

    client_credits = sorted(
        {f for f in SECTIONS.values() if f not in PEXELS}
    )
    for name in client_credits:
        credits.append(f"- {name} — Tommy's Brewing Company (client-owned)")

    (IMAGES_DIR / "IMAGE_CREDITS.txt").write_text(
        "Section photos:\n" + "\n".join(sorted(credits, key=lambda x: x.lower())) + "\n",
        encoding="utf-8",
    )
    print("Section headers updated.")


if __name__ == "__main__":
    main()
