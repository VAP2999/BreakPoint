from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    from pathlib import Path
    import os
    from urllib.parse import urlsplit
    root = Path(os.environ.get("BREAKPOINT_FIXTURE_DIR", "dist")).resolve()
    files = {"/": "index.html", "/app.js": "app.js", "/cart.js": "cart.js"}
    def serve(route):
        name = files.get(urlsplit(route.request.url).path)
        route.fulfill(path=str(root / name)) if name else route.fulfill(status=404, body="Not found")
    page.route("**/*", serve)
    page.goto("http://localhost:8000/?mode=buggy")
    page.get_by_role("button", name="Add item", exact=True).click()
    page.get_by_role("button", name="Remove item", exact=True).click()
    page.get_by_role("button", name="Remove item", exact=True).click()
    expect(page.get_by_test_id("quantity")).to_have_text("0")
    expect(page.get_by_test_id("total")).to_have_text("$0.00")
    browser.close()
