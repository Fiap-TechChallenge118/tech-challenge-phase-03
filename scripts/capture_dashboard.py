"""Captura reproduzível do Grafana local; requer playwright e chromium instalados."""

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/grafana_dashboard.png")
    )
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        response = context.request.post(
            "http://127.0.0.1:3000/login",
            data={
                "user": "admin",
                "password": os.getenv("GRAFANA_ADMIN_PASSWORD", "admin"),
            },
        )
        if not response.ok:
            raise RuntimeError(f"Login Grafana falhou: {response.status}")
        page = context.new_page()
        page.goto("http://127.0.0.1:3000/d/triagem?from=now-15m&to=now&kiosk")
        page.get_by_text("Predições realizadas", exact=True).wait_for()
        page.get_by_text("Predições por classe", exact=True).wait_for()
        page.wait_for_timeout(5000)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(args.output), full_page=True)
        browser.close()
    print(args.output)


if __name__ == "__main__":
    main()
