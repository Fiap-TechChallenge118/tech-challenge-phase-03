"""Benchmark HTTP sequencial; recusa mock por padrão e preserva amostras brutas."""

import argparse
import json
import math
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx

TEXTS = [
    "Patient presents with acute chest pain and shortness of breath.",
    "Neurological examination shows progressive weakness and headache.",
    "Routine examination with no significant pathological findings.",
]


def percentile(samples, value):
    ordered = sorted(samples)
    position = (len(ordered) - 1) * value / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--url", default="http://localhost:8000/predict")
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--output", type=Path, default=Path("docs/benchmark_raw.json"))
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()
    if args.n < 1 or args.warmup < 0 or args.timeout <= 0:
        parser.error("--n e --timeout devem ser positivos; --warmup >= 0")
    parts = urlsplit(args.url)
    health_url = urlunsplit((parts.scheme, parts.netloc, "/health", "", ""))
    with httpx.Client(timeout=args.timeout, trust_env=False) as client:
        health = client.get(health_url)
        health.raise_for_status()
        model = health.json().get("model")
        if model != "loaded" and not (args.allow_mock and model == "mock"):
            parser.error("Modelo real não carregado; --allow-mock só para smoke test")

        def request(index):
            start = time.perf_counter()
            response = client.post(args.url, json={"texto": TEXTS[index % len(TEXTS)]})
            elapsed = (time.perf_counter() - start) * 1000
            response.raise_for_status()
            body = response.json()
            if (
                body.get("classe") not in {"normal", "atenção", "urgente"}
                or not 0 <= body.get("confianca", -1) <= 1
                or body.get("tempo_ms", -1) < 0
            ):
                raise ValueError(f"Resposta inválida: {body}")
            return {"latency_ms": elapsed, "response": body}

        for i in range(args.warmup):
            request(i)
        start = time.perf_counter()
        samples = [request(i) for i in range(args.n)]
        total = time.perf_counter() - start
        final_health = client.get(health_url)
        final_health.raise_for_status()
        if final_health.json().get("model") != model:
            raise RuntimeError("Modo do modelo mudou durante a medição")
    latencies = [s["latency_ms"] for s in samples]
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "url": args.url,
        "model_status": model,
        "purpose": "smoke_only" if model == "mock" else "model_baseline",
        "platform": platform.platform(),
        "n": args.n,
        "warmup": args.warmup,
        "texts": TEXTS,
        "summary": {
            **{f"p{p}_ms": percentile(latencies, p) for p in (50, 95, 99)},
            "throughput_rps": args.n / total,
            "total_seconds": total,
        },
        "samples": samples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))


if __name__ == "__main__":
    main()
