"""Captura o grafo verde da DAG de retreino (FASE 6) na UI do Airflow local.

Requer ``playwright`` e um navegador Chromium do sistema (Edge/Chrome). Ex.:

    AIRFLOW_ADMIN_PASSWORD=... python scripts/capture_dag.py

A senha do admin do ``airflow standalone`` fica em
``docker compose -f docker-compose.airflow.yml exec airflow cat
/opt/airflow/standalone_admin_password.txt``.
"""

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://localhost:8080")
USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
PASSWORD = os.getenv("AIRFLOW_ADMIN_PASSWORD", "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/dag_execucao.png"))
    parser.add_argument("--dag", default="retrain_triagem_dag")
    parser.add_argument(
        "--channel", default="msedge", help="Navegador do sistema (msedge ou chrome)"
    )
    args = parser.parse_args()

    if not PASSWORD:
        parser.error("Defina AIRFLOW_ADMIN_PASSWORD com a senha do admin do Airflow")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()

        # Login na UI (Flask-AppBuilder).
        page.goto(f"{AIRFLOW_URL}/login/")
        page.fill("input[name='username']", USERNAME)
        page.fill("input[name='password']", PASSWORD)
        page.click("input[type='submit']")
        page.wait_for_url(lambda url: "/login" not in url, timeout=20000)
        page.wait_for_load_state("networkidle")

        # Aba Graph da DAG (topologia ingest -> train -> save com bordas verdes).
        page.goto(f"{AIRFLOW_URL}/dags/{args.dag}/graph")
        page.get_by_text("ingest", exact=True).first.wait_for(timeout=30000)
        page.get_by_text("save", exact=True).first.wait_for(timeout=30000)
        page.wait_for_timeout(3000)  # aguarda as bordas verdes renderizarem

        args.output.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(args.output), full_page=True)
        browser.close()

    print(args.output)


if __name__ == "__main__":
    main()
