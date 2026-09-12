"""Verifica estatísticas e impede uso acidental do fallback como baseline."""

import sys

import httpx
import pytest

from scripts import benchmark


def test_percentile_interpolates_known_distribution():
    assert benchmark.percentile([40, 10, 30, 20], 50) == 25
    assert benchmark.percentile([40, 10, 30, 20], 95) == pytest.approx(38.5)
    assert benchmark.percentile([5], 99) == 5


def test_mock_rejected_before_any_prediction(monkeypatch, tmp_path):
    def handler(request):
        assert request.url.path == "/health"
        return httpx.Response(200, json={"status": "ok", "model": "mock"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(benchmark.httpx, "Client", lambda **kwargs: client)
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", ["benchmark", "--output", str(output)])
    with pytest.raises(SystemExit) as exc:
        benchmark.main()
    assert exc.value.code == 2
    assert not output.exists()


def test_http_error_does_not_create_success_report(monkeypatch, tmp_path):
    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "model": "loaded"})
        return httpx.Response(500, json={"detail": "failure"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(benchmark.httpx, "Client", lambda **kwargs: client)
    output = tmp_path / "result.json"
    monkeypatch.setattr(
        sys, "argv", ["benchmark", "--n", "1", "--warmup", "0", "--output", str(output)]
    )
    with pytest.raises(httpx.HTTPStatusError):
        benchmark.main()
    assert not output.exists()
