"""SDK Python para el motor Trongkai.

Cliente liviano para consumir los 18+ endpoints REST desde notebooks, scripts
o agentes Claude. Auto-detecta DEFAULT_API_KEY y entorno (local/prod).

Uso:
    from trongkai_sdk import Trongkai
    t = Trongkai()  # auto-detecta https://trongkai-engine.fly.dev

    # Plan financiero
    plan = t.plan()
    print(f"TIR: {plan['kpis']['tir_proyecto_anual']*100:.2f}%")

    # Monte Carlo integrado con clima
    mc = t.monte_carlo_integrado(n_runs=2000)
    print(f"TIR P50 con clima: {mc['tir_p50']*100:.1f}%")

    # Riesgo regulatorio
    rep = t.rep_calendar()
    print(f"Costo compliance 5y: ${rep['costo_compliance_5y_clp']['total_clp']/1e6:.0f}M")

    # SLB simulación
    slb = t.slb_simulation(monto_clp=5_000_000_000, tasa_base=0.085)
    print(f"Precio ESG: ${slb['incentivo_esg_clp']/1e9:.2f}B")
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - fallback a urllib
    httpx = None
    import json as _json
    from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://trongkai-engine.fly.dev"


class Trongkai:
    """Cliente sync para el motor Trongkai.

    Args:
        base_url: URL del motor. Default: producción Fly.io.
        api_key: X-API-Key si el motor está en modo lock.
        timeout: timeout HTTP en segundos.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or os.environ.get("TRONGKAI_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key or os.environ.get("TRONGKAI_API_KEY")
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {"content-type": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if httpx:
            r = httpx.request(method, url, json=json, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        # urllib fallback
        body = _json.dumps(json).encode("utf-8") if json else None
        req = Request(url, data=body, method=method, headers=self._headers())
        with urlopen(req, timeout=self.timeout) as resp:
            return _json.loads(resp.read().decode("utf-8"))

    # ---- meta ----
    def health(self) -> dict:
        return self._request("GET", "/health")

    # ---- balance de masa ----
    def mass_balance(self, mmpp_codigo: str, humedad: float, ms: float, **kwargs) -> dict:
        return self._request("POST", "/mass-balance", json={
            "mmpp_codigo": mmpp_codigo,
            "humedad_inicial_pct": humedad,
            "materia_solida_pct": ms,
            "input_ton": kwargs.get("input_ton", 100),
            "mode": kwargs.get("mode", "A"),
            "aceite_extraible_pct": kwargs.get("aceite_extraible_pct", 0),
            "licopeno_pct": kwargs.get("licopeno_pct", 0),
            "pectina_pct": kwargs.get("pectina_pct", 0),
        })

    # ---- operación ----
    def bottleneck(self, capacidades: list[dict], tiempo_descomposicion_h: float, **kwargs) -> dict:
        return self._request("POST", "/bottleneck", json={
            "capacidades": capacidades,
            "tiempo_descomposicion_h": tiempo_descomposicion_h,
            **kwargs,
        })

    def agenda(self, ano: int, capacidades: list[dict], temporadas: list[dict], suppliers: list[dict]) -> dict:
        return self._request("POST", "/agenda", json={
            "ano": ano,
            "capacidades": capacidades,
            "temporadas": temporadas,
            "suppliers": suppliers,
        })

    # ---- plan financiero ----
    def plan(self, **kwargs) -> dict:
        return self._request("POST", "/plan", json=kwargs)

    def plan_export(self, **kwargs) -> bytes:
        """Descarga el Excel del Plan 5 Años. Devuelve bytes."""
        url = f"{self.base_url}/plan/export"
        if httpx:
            r = httpx.post(url, json=kwargs, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            return r.content
        raise RuntimeError("plan_export requiere httpx instalado.")

    def tornado(self, **kwargs) -> dict:
        return self._request("POST", "/plan/tornado", json=kwargs)

    def escenarios_estrategicos(self) -> dict:
        return self._request("GET", "/plan/escenarios-estrategicos")

    def valuation(self, **kwargs) -> dict:
        return self._request("POST", "/plan/valuation", json=kwargs)

    def monte_carlo(self, n_runs: int = 1_000, seed: int = 42, **base) -> dict:
        return self._request("POST", "/plan/monte-carlo", json={
            "n_runs": n_runs, "seed": seed, "base": base,
        })

    def monte_carlo_integrado(self, n_runs: int = 1_000, incluir_clima: bool = True, seed: int = 42, **base) -> dict:
        return self._request("POST", "/plan/monte-carlo-integrado", json={
            "n_runs": n_runs, "seed": seed, "incluir_clima": incluir_clima, "base": base,
        })

    def depreciation(self, metodo: str = "NORMAL", regimen: str = "GENERAL", **base) -> dict:
        return self._request("POST", "/plan/depreciation", json={
            "metodo": metodo, "regimen": regimen, "base": base,
        })

    def learning_curve(self, learning_rate: float = 0.90, **base) -> dict:
        return self._request("POST", "/plan/learning-curve", json={
            "learning_rate": learning_rate, "base": base,
        })

    def financing(self, deuda_pct: float = 0.50, tasa: float = 0.095, **kwargs) -> dict:
        return self._request("POST", "/plan/financing", json={
            "deuda_pct": deuda_pct, "tasa_deuda_anual": tasa, **kwargs,
        })

    def slb_simulation(self, monto_clp: float = 5e9, tasa_base: float = 0.085, plazo: int = 7) -> dict:
        return self._request("POST", "/plan/slb-simulation", json={
            "monto_clp": monto_clp, "tasa_base_anual": tasa_base, "plazo_anos": plazo,
        })

    def climate_risk(self, n_runs: int = 1_000, seed: int = 42, **base) -> dict:
        return self._request("POST", "/plan/climate-risk", json={
            "n_runs": n_runs, "seed": seed, "base": base,
        })

    # ---- compliance ----
    def rep_calendar(self) -> dict:
        return self._request("GET", "/compliance/rep-calendar")

    # ---- what-if ----
    def whatif(self, escenarios: list[dict], **base) -> dict:
        return self._request("POST", "/whatif", json={"escenarios": escenarios, "base": base})


def demo():
    """Demo rápido del SDK. Corre todo end-to-end con un pretty-print."""
    t = Trongkai()
    print(f"Trongkai engine: {t.base_url}")
    print(f"Health: {t.health()}")
    print()

    # Plan base
    plan = t.plan()
    k = plan["kpis"]
    print("=== Plan Base ===")
    print(f"  TIR: {k['tir_proyecto_anual']*100:.2f}% | VAN: ${k['van']/1e9:.2f}B")
    print(f"  Payback: {k['payback_meses']}m | EBITDA margin: {k['ebitda_margin_promedio']*100:.1f}%")
    print()

    # Monte Carlo integrado
    print("=== Monte Carlo con clima (500 corridas) ===")
    mc = t.monte_carlo_integrado(n_runs=500)
    print(f"  TIR P5/P50/P95: {mc['tir_p5']*100:.1f}% / {mc['tir_p50']*100:.1f}% / {mc['tir_p95']*100:.1f}%")
    print(f"  Prob TIR > WACC: {mc['prob_tir_supera_wacc']*100:.1f}%")
    print(f"  Años críticos clima promedio: {mc['promedio_anos_critico_por_corrida']:.2f}/5")
    print()

    # Valuation
    val = t.valuation()
    print(f"=== Valoración exit ===")
    print(f"  EV base: ${val['ev_clp_base']/1e9:.1f}B | MOIC: {val['moic_estimado']:.1f}x")
    print()

    # Compliance
    rep = t.rep_calendar()
    print(f"=== Compliance ===")
    print(f"  Hitos: {rep['total_hitos']} | Próximo: {rep['proximos'][0]['nombre'][:60]} ({rep['proximos'][0]['fecha_vigor']})")
    print(f"  Costo 5y: ${rep['costo_compliance_5y_clp']['total_clp']/1e6:.0f}M CLP")


if __name__ == "__main__":
    demo()
