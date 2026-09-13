"""Captura reproduzível do Grafana local; requer playwright e chromium instalados."""

import argparse
import json
import math
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def wait_for_metrics(context, timeout):
    """Exige amostras finitas nos quatro painéis antes de abrir o dashboard."""
    dashboard = Path(__file__).resolve().parents[1] / "monitoring/dashboard.json"
    panels = json.loads(dashboard.read_text())["panels"]
    deadline = time.monotonic() + timeout
    while True:
        missing = []
        for panel in panels:
            for target in panel["targets"]:
                expression = target["expr"].replace("$__rate_interval", "1m")
                response = context.request.get(
                    "http://127.0.0.1:9090/api/v1/query",
                    params={"query": expression},
                )
                if not response.ok:
                    raise RuntimeError(f"Prometheus falhou: {response.status}")
                payload = response.json()
                samples = payload.get("data", {}).get("result", [])
                if payload.get("status") != "success" or not samples or not all(
                    math.isfinite(float(sample["value"][1])) for sample in samples
                ):
                    missing.append(panel["title"])
                    continue
                if panel["type"] == "timeseries":
                    now = time.time()
                    history = context.request.get(
                        "http://127.0.0.1:9090/api/v1/query_range",
                        params={
                            "query": expression,
                            "start": now - 120,
                            "end": now,
                            "step": 15,
                        },
                    )
                    if not history.ok:
                        raise RuntimeError(f"Prometheus falhou: {history.status}")
                    series = history.json().get("data", {}).get("result", [])
                    if not series or not all(
                        sum(
                            math.isfinite(float(value))
                            for _, value in item["values"]
                        ) >= 3
                        for item in series
                    ):
                        missing.append(panel["title"])
        if not missing:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Painéis sem dados: {missing}. Gere tráfego real e tente novamente."
            )
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/grafana_dashboard.png")
    )
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout deve ser positivo")
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
        wait_for_metrics(context, args.timeout)
        page = context.new_page()
        page.goto("http://127.0.0.1:3000/d/triagem?from=now-5m&to=now&kiosk")
        page.get_by_text("Predições realizadas", exact=True).wait_for()
        page.get_by_text("Predições por classe", exact=True).wait_for()
        page.wait_for_load_state("networkidle")
        page.get_by_text("No data", exact=True).first.wait_for(
            state="hidden", timeout=args.timeout * 1000
        )
        page.wait_for_timeout(2000)
        if page.get_by_text("No data", exact=True).count():
            raise RuntimeError("Grafana ainda exibe No data; captura cancelada")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(args.output), full_page=True)
        browser.close()
    print(args.output)


if __name__ == "__main__":
    main()
