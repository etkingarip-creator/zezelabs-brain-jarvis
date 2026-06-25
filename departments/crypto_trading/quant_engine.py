"""
Quant Engine — crypto_trading için ileri kantitatif araçlar (unicorn-seviye).

Saf, deterministik, test edilebilir fonksiyonlar (LLM/ağ gerektirmez). Gerçek para
kararlarının matematiksel temeli: volatilite-tabanlı stop, rejim tespiti, optimal
pozisyon boyutu, risk/ödül zorunluluğu.
"""
from __future__ import annotations
import math
from typing import List, Dict


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Average True Range — volatilite ölçer. ATR-tabanlı stop-loss için temel."""
    n = min(len(highs), len(lows), len(closes))
    if n < 2:
        return 0.0
    trs = []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    if not trs:
        return 0.0
    p = min(period, len(trs))
    return round(sum(trs[-p:]) / p, 6)


def adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Average Directional Index — trend gücü. >25 trend, <20 range/chop (işlem yapma)."""
    n = min(len(highs), len(lows), len(closes))
    if n < period + 1:
        return 0.0
    plus_dm, minus_dm, trs = [], [], []
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if (up > down and up > 0) else 0.0)
        minus_dm.append(down if (down > up and down > 0) else 0.0)
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    atr_sum = sum(trs[-period:]) or 1e-9
    plus_di = 100 * (sum(plus_dm[-period:]) / atr_sum)
    minus_di = 100 * (sum(minus_dm[-period:]) / atr_sum)
    denom = (plus_di + minus_di) or 1e-9
    dx = 100 * abs(plus_di - minus_di) / denom
    return round(dx, 2)


def market_regime(adx_value: float) -> str:
    """ADX'ten piyasa rejimi: trend / geçiş / range (range'de momentum işlemi riskli)."""
    if adx_value >= 25:
        return "trend"
    if adx_value <= 20:
        return "range"
    return "gecis"


def kelly_fraction(win_rate: float, win_loss_ratio: float, fraction: float = 0.5) -> float:
    """Kelly kriteri ile optimal sermaye oranı. fraction=0.5 → yarım-Kelly (güvenli).
    win_rate 0-1, win_loss_ratio = ortalama_kazanç/ortalama_kayıp. 0-0.25 arası kırpılır."""
    if win_loss_ratio <= 0:
        return 0.0
    p = max(0.0, min(1.0, win_rate))
    k = p - (1 - p) / win_loss_ratio
    k = max(0.0, k) * fraction
    return round(min(k, 0.25), 4)  # tek işlemde max %25 sermaye


def risk_reward(entry: float, stop: float, target: float) -> float:
    """Risk/Ödül oranı. Long: target>entry>stop. Reddet eşiği genelde < 1.5."""
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return 0.0
    return round(reward / risk, 2)


def position_size(balance_usd: float, risk_pct: float, entry: float, stop: float) -> Dict[str, float]:
    """Risk-tabanlı pozisyon boyutu: sermayenin risk_pct'i kadar RİSK alınır (kayıp = bu kadar).
    qty = (balance*risk_pct) / |entry-stop|. Sabit-tutar değil, risk-eşitlenmiş."""
    risk_per_unit = abs(entry - stop)
    if risk_per_unit <= 0 or entry <= 0:
        return {"qty": 0.0, "notional_usd": 0.0, "risk_usd": 0.0}
    risk_usd = balance_usd * max(0.0, min(0.1, risk_pct))  # max %10 risk
    qty = risk_usd / risk_per_unit
    return {
        "qty": round(qty, 6),
        "notional_usd": round(qty * entry, 2),
        "risk_usd": round(risk_usd, 2),
    }


def atr_stop_loss(entry: float, atr_value: float, side: str = "BUY", mult: float = 2.0) -> float:
    """Volatilite-tabanlı (ATR) stop-loss. Sabit % yerine piyasa volatilitesine uyar."""
    if side.upper() == "BUY":
        return round(entry - mult * atr_value, 6)
    return round(entry + mult * atr_value, 6)


def funding_signal(funding_rate: float) -> Dict:
    """Perpetual funding rate yorumu — kriptonun yapısal edge'i.
    funding_rate: anlık fonlama oranı (örn 0.0001 = %0.01/8saat).
      + : long'lar short'lara öder → piyasa long-ağırlıklı (aşırıysa squeeze riski)
      - : short'lar long'lara öder → piyasa short-ağırlıklı (long fırsatı olabilir)
    Yıllık ~= rate * 3 * 365 (8 saatte bir)."""
    annualized = round(funding_rate * 3 * 365 * 100, 2)
    abs_r = abs(funding_rate)
    if funding_rate > 0.0005:        # %0.05+ /8h → aşırı ısınmış long
        bias = "aşırı long (squeeze riski)"
        note = "Long açma riskli; delta-nötr funding-arb (spot al + perp short) cazip."
    elif funding_rate > 0.00005:
        bias = "long-ağırlıklı"
        note = "Hafif long baskısı; trend long ise dikkatli devam."
    elif funding_rate < -0.0005:     # aşırı negatif → short ısınmış
        bias = "aşırı short (sıkışma fırsatı)"
        note = "Short kalabalık; long squeeze/reversal fırsatı olabilir."
    elif funding_rate < -0.00005:
        bias = "short-ağırlıklı"
        note = "Hafif short baskısı; reversal long aranabilir."
    else:
        bias = "nötr"
        note = "Funding dengeli; yön sinyali zayıf."
    return {"funding_rate": funding_rate, "annualized_pct": annualized, "bias": bias, "note": note}


def evaluate_setup(entry: float, stop: float, target: float, balance_usd: float,
                   win_rate: float, adx_value: float, risk_pct: float = 0.01) -> Dict:
    """Tam setup değerlendirme — unicorn quant özeti. Reddetme kuralları dahil."""
    rr = risk_reward(entry, stop, target)
    regime = market_regime(adx_value)
    wl = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0.0
    kelly = kelly_fraction(win_rate, wl)
    sizing = position_size(balance_usd, risk_pct, entry, stop)

    reasons = []
    if rr < 1.5:
        reasons.append(f"R:R {rr} < 1.5 (yetersiz ödül)")
    if regime == "range":
        reasons.append(f"Rejim 'range' (ADX {adx_value}) — momentum işlemi riskli")
    if stop == entry:
        reasons.append("Stop-loss tanımsız")
    approved = len(reasons) == 0

    return {
        "approved": approved,
        "risk_reward": rr,
        "regime": regime,
        "kelly_fraction": kelly,
        "position": sizing,
        "rejection_reasons": reasons,
    }
