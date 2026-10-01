#!/usr/bin/env python3
"""Thẻ ảnh Sugar. Nền sáng, chữ Việt, không phụ thuộc mạng."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

INK = (42, 24, 32)
MUTED = (120, 78, 90)
ROSE = (190, 18, 60)
CREAM = (255, 247, 244)
CARD = (255, 252, 251)
LINE = (244, 214, 220)
UP = (15, 122, 82)
DOWN = (190, 18, 60)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if draw.textlength(trial, font=face) <= width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def new_card() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1200, 675), CREAM)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((36, 36, 1164, 639), radius=28, fill=CARD, outline=LINE, width=2)
    draw.rectangle((36, 36, 52, 639), fill=ROSE)
    draw.text((80, 58), "SUGAR", font=font(22, True), fill=ROSE)
    return image, draw


def finish(image: Image.Image, draw: ImageDraw.ImageDraw, footer: str) -> bytes:
    draw.text((80, 590), footer[:90], font=font(20), fill=MUTED)
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def welcome_card() -> bytes:
    image, draw = new_card()
    draw.text((80, 130), "Sugar đã sẵn sàng", font=font(64, True), fill=INK)
    body = wrap(
        draw,
        "Bot nhóm. Chỉ lên tiếng khi có lệnh hoặc khi bạn bấm mục bên dưới.\nGiá, xếp hạng và ảnh chế đi kèm thẻ ảnh.",
        font(32),
        980,
    )
    y = 250
    for line in body:
        draw.text((80, y), line, font=font(32), fill=INK)
        y += 48
    return finish(image, draw, "Thuần Việt  ·  số liệu chỉ để tham khảo")


def price_card(name: str, symbol: str, usd: str, vnd: str, change: str, up: bool) -> bytes:
    image, draw = new_card()
    draw.text((80, 120), name, font=font(52, True), fill=INK)
    draw.text((80, 190), symbol.upper(), font=font(28), fill=MUTED)
    draw.text((80, 270), usd, font=font(72, True), fill=INK)
    draw.text((80, 370), vnd, font=font(36), fill=INK)
    color = UP if up else DOWN
    draw.text((80, 450), change, font=font(32, True), fill=color)
    return finish(image, draw, "Nguồn giá công khai  ·  không phải lời khuyên đầu tư")


def mood_card(score: int, label: str) -> bytes:
    image, draw = new_card()
    draw.text((80, 120), "Sợ hãi và tham lam", font=font(42, True), fill=INK)
    draw.text((80, 210), str(score), font=font(120, True), fill=ROSE if score < 50 else UP)
    draw.text((80, 360), label, font=font(40, True), fill=INK)
    draw.rounded_rectangle((80, 450, 1080, 486), radius=18, fill=LINE)
    fill_to = 80 + int(1000 * max(0, min(100, score)) / 100)
    draw.rounded_rectangle((80, 450, max(116, fill_to), 486), radius=18, fill=ROSE if score < 50 else UP)
    return finish(image, draw, "Thang 0–100  ·  0 là sợ hãi cực độ")


def meme_card(line: str) -> bytes:
    image, draw = new_card()
    draw.text((80, 120), "Ảnh chế", font=font(28, True), fill=ROSE)
    y = 200
    for row in wrap(draw, line, font(48, True), 980):
        draw.text((80, y), row, font=font(48, True), fill=INK)
        y += 68
    return finish(image, draw, "Sugar  ·  chế thị trường, không chế người")


def list_card(title: str, rows: list[str], footer: str) -> bytes:
    image, draw = new_card()
    draw.text((80, 110), title, font=font(42, True), fill=INK)
    y = 190
    face = font(28)
    for row in rows[:10]:
        draw.text((80, y), row[:70], font=face, fill=INK)
        y += 38
    return finish(image, draw, footer)


def save_samples(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "chao.png").write_bytes(welcome_card())
    (folder / "gia.png").write_bytes(
        price_card("Bitcoin", "BTC", "63.420 USD", "1.612.450.000 đ", "+2,4% trong 24 giờ", True)
    )
    (folder / "camxuc.png").write_bytes(mood_card(28, "Sợ hãi"))
    (folder / "anhche.png").write_bytes(meme_card("Vừa bảo dài hạn, vừa mở sổ lệnh mỗi bốn phút."))


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "mau"
    save_samples(out)
    print(out)
