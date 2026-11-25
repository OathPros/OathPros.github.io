"""Stage an optimized screenshot of an editorially approved public URL."""
import argparse
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url")
parser.add_argument("output", type=Path, help="Staging filename ending in .webp")
parser.add_argument("--channel", help="Installed Chromium channel, e.g. msedge")
parser.add_argument("--selector", help="Capture an element instead of the viewport")
parser.add_argument("--scroll", type=int, default=0, help="Vertical offset in CSS pixels")
parser.add_argument("--crop", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
parser.add_argument("--width", type=int, default=1440)
parser.add_argument("--height", type=int, default=900)
args = parser.parse_args()


def public_https(url):
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname and not parts.username and not parts.password


if not public_https(args.url) or args.output.suffix != ".webp":
    parser.error("Enter a public HTTPS URL and a .webp staging filename.")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel=args.channel)
    page = browser.new_page(
        viewport={"width": args.width, "height": args.height},
        reduced_motion="reduce",
    )
    try:
        response = page.goto(args.url, wait_until="domcontentloaded", timeout=25000)
        if not response or not response.ok or not public_https(page.url):
            raise SystemExit(f"Destination failed: {page.url}")
        page.evaluate("document.fonts.ready")
        if args.scroll:
            page.evaluate("(y) => window.scrollTo(0, y)", args.scroll)
        page.wait_for_timeout(1200)
        target = page.locator(args.selector).first if args.selector else page
        screenshot = target.screenshot(animations="disabled", timeout=12000)
        with Image.open(BytesIO(screenshot)) as preview:
            if args.crop:
                left, top, right, bottom = args.crop
                if not (0 <= left < right <= preview.width and 0 <= top < bottom <= preview.height):
                    parser.error("Crop must fit inside the capture.")
                preview = preview.crop(args.crop)
            preview.thumbnail((1440, 1050), Image.Resampling.LANCZOS)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            preview.convert("RGB").save(args.output, "WEBP", quality=84, method=6)
        print(f"{page.title()} | {page.url} | {args.output}")
    finally:
        browser.close()
