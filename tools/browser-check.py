"""Run browser smoke tests against a local preview and save review evidence."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", default="http://localhost:8080/")
parser.add_argument("--channel", help="Installed Chromium channel, e.g. msedge")
args = parser.parse_args()
assert urlsplit(args.base).hostname in {"localhost", "127.0.0.1", "::1"}
out = Path(".devkit/artifacts")
out.mkdir(parents=True, exist_ok=True)
projects = json.loads(Path("projects.json").read_text(encoding="utf-8"))
by_id = {project["id"]: project for project in projects}
origin = args.base.rstrip("/")
featured = sorted((p for p in projects if "featured" in p), key=lambda p: p["featured"])
lead_project = featured[0]

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel=args.channel)
    for width, height in [(1440, 900), (1920, 1080), (768, 1024), (390, 844), (320, 800)]:
        page = browser.new_page(viewport={"width": width, "height": height}, has_touch=width <= 390)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda request: errors.append(f"Failed: {request.url}"))
        page.on("response", lambda response: errors.append(f"{response.status}: {response.url}") if not response.ok else None)
        assert page.goto(args.base).ok
        expect(page.locator("#filters")).to_be_visible()
        expect(page.get_by_role("listitem")).to_have_count(len(projects))
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        expect(page.locator(".feature img")).to_have_count(sum("preview" in p for p in featured))
        for img in page.locator(".feature img").all():
            img.scroll_into_view_if_needed()
            expect(img).to_have_js_property("complete", True)
            assert img.evaluate("(image) => image.naturalWidth > 0")
        page.evaluate("scrollTo(0, 0)")
        page.screenshot(path=out / f"after-{width}.png")
        if width == 1440:
            page.locator(".lead").hover()
            page.screenshot(path=out / "hover-1440.png")
        if width in (1440, 390):
            page.locator(".masthead").get_by_role("link", name="Project index").click()
            expect(page).to_have_url(f"{origin}/#index")
            page.screenshot(path=out / f"index-{width}.png")
        assert not errors, errors
        page.close()

    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(args.base)
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("main")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name=lead_project["title"], exact=True).first).to_be_focused()
    page.screenshot(path=out / "focus-1440.png")
    search = page.get_by_role("searchbox", name="Search")
    category = page.get_by_label("Category")
    topic = page.get_by_label("Topic")
    view = page.get_by_label("View")
    reset = page.get_by_role("button", name="Reset filters")
    rows = page.get_by_role("listitem")
    search.fill("drawing paths")
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text("Overland Map Maker")
    search.fill("ashénmere")
    expect(rows).to_have_count(1)
    expect(rows).to_contain_text("Waymark Atlas")
    category.select_option("experiments")
    expect(rows).to_have_count(0)
    expect(page.get_by_text("No matches")).to_be_visible()
    page.locator("#index").scroll_into_view_if_needed()
    page.locator("#index").evaluate("(index) => index.scrollIntoView()")
    page.screenshot(path=out / "empty-1440.png")
    reset.click()
    expect(search).to_be_focused()
    expect(rows).to_have_count(len(projects))
    category.select_option("experiments")
    topic.select_option("Worldbuilding")
    expect(rows).to_have_count(2)
    page.reload()
    expect(rows).to_have_count(2)
    expect(topic).to_have_value("Worldbuilding")
    page.locator("#index").evaluate("(index) => index.scrollIntoView()")
    page.screenshot(path=out / "filtered-1440.png")
    rows.first.get_by_role("button", name="Worldbuilding").click()
    expect(topic).to_be_focused()
    expect(topic).to_have_value("")
    expect(page).to_have_url(f"{origin}/?category=experiments#main")
    reset.click()
    view.select_option("featured")
    expect(rows).to_have_count(len(featured))
    expect(rows.first).to_contain_text(featured[0]["title"])
    view.select_option("recent")
    recent = sorted((p for p in projects if "update" in p), key=lambda p: p["update"]["date"], reverse=True)
    expect(rows).to_have_count(len(recent))
    assert page.locator("li:not([hidden]) time").all_text_contents() == [p["update"]["date"] for p in recent]
    reset.click()
    flow = rows.filter(has=page.get_by_role("heading", name="Flowboard"))
    source = flow.get_by_role("link", name="Source for Flowboard")
    expect(source).to_have_attribute("href", by_id["flowboard"]["source"])
    expect(flow.get_by_role("link", name="Flowboard", exact=True)).to_have_attribute("href", by_id["flowboard"]["launch"])
    tag = flow.get_by_role("button", name="Diagrams")
    tag.click()
    expect(topic).to_have_value("Diagrams")
    reset.click()

    def mock_navigation(route):
        route.fulfill(status=200, content_type="text/plain", body="Navigation intercepted by smoke test")

    for destination in [by_id["flowboard"]["launch"], by_id["flowboard"]["source"], lead_project["launch"]]:
        page.route(destination, mock_navigation)
    source.click()
    expect(page).to_have_url(by_id["flowboard"]["source"])
    page.go_back()
    row_copy = flow.locator(".row-description p")
    row_copy.scroll_into_view_if_needed()
    box = row_copy.bounding_box()
    page.mouse.click(box["x"] + 10, box["y"] + box["height"] / 2)
    expect(page).to_have_url(by_id["flowboard"]["launch"])
    page.go_back()
    lead = page.locator(".lead img")
    lead.scroll_into_view_if_needed()
    box = lead.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(page).to_have_url(lead_project["launch"])

    page = browser.new_page(reduced_motion="reduce")
    page.route(f"**/{lead_project['preview']['path']}", lambda route: route.abort())
    page.goto(args.base)
    expect(page.locator(".lead img")).to_be_hidden()
    expect(page.locator(".lead .preview-type")).to_be_visible()
    assert page.locator(".lead").evaluate("(feature) => getComputedStyle(feature).transitionDuration") == "0s"
    page.screenshot(path=out / "fallback-1440.png")

    page = browser.new_page(java_script_enabled=False)
    page.goto(args.base)
    expect(page.get_by_role("listitem")).to_have_count(len(projects))
    expect(page.locator("#filters")).to_be_hidden()
    expect(page.get_by_role("link", name="Waymark Atlas", exact=True).first).to_have_attribute("href", by_id["waymark-atlas"]["launch"])
    browser.close()

print("Browser checks passed at five viewport widths. Evidence:", out.resolve())
