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


def estimate_slippage_from_book(order_book: Dict, side: str, qty: float) -> Dict:
    """Order-book derinliğini yürüyerek GERÇEKÇİ slippage tahmin eder.
    Sabit %0.05 yerine: emir boyutu likiditeyi tüketince fill kötüleşir (market impact).
    BUY → asks yürür, SELL → bids yürür. Döner: {fill_price, slippage_pct, filled, partial}."""
    levels = order_book.get("asks" if side.upper() == "BUY" else "bids", [])
    if not levels or qty <= 0:
        return {"fill_price": 0.0, "slippage_pct": 0.0, "filled": 0.0, "partial": True}
    try:
        best = float(levels[0][0])
    except (IndexError, ValueError, TypeError):
        return {"fill_price": 0.0, "slippage_pct": 0.0, "filled": 0.0, "partial": True}

    remaining = qty
    cost = 0.0
    filled = 0.0
    for lvl in levels:
        try:
            price = float(lvl[0]); avail = float(lvl[1])
        except (IndexError, ValueError, TypeError):
            continue
        take = min(remaining, avail)
        cost += take * price
        filled += take
        remaining -= take
        if remaining <= 1e-12:
            break

    if filled <= 0:
        return {"fill_price": best, "slippage_pct": 0.0, "filled": 0.0, "partial": True}
    vwap = cost / filled
    slip = (vwap - best) / best if side.upper() == "BUY" else (best - vwap) / best
    return {
        "fill_price": round(vwap, 6),
        "slippage_pct": round(slip * 100, 4),
        "filled": round(filled, 6),
        "partial": remaining > 1e-9,  # kitap emri tam karşılayamadı (büyük emir)
    }


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


# ──────────────────────────────────────────────────────────────────────────
# UNICORN'U AŞMA KATMANI — portföy + hayatta-kalma + adaptasyon (P1-P4)
# ──────────────────────────────────────────────────────────────────────────

def portfolio_risk_check(open_positions: List[Dict], balance_usd: float,
                         new_risk_usd: float = 0.0, new_beta: float = 1.0,
                         max_heat_pct: float = 0.06, max_beta_exposure: float = 2.0) -> Dict:
    """P1 — Portföy-seviye risk. Tek işlem değil TOPLAM riske bakar.
    open_positions: [{risk_usd, beta}] (beta: BTC'ye duyarlılık, ~1 altcoin).
    portfolio_heat = toplam risk / sermaye (max %6). beta_exposure = Σ(risk×beta)/sermaye.
    Kriptoda her şey BTC-beta → 5 'çeşitli' long = tek dev BTC bahsi. Bunu engeller."""
    total_risk = sum(float(p.get("risk_usd", 0)) for p in open_positions) + max(0.0, new_risk_usd)
    beta_risk = sum(float(p.get("risk_usd", 0)) * float(p.get("beta", 1.0)) for p in open_positions)
    beta_risk += max(0.0, new_risk_usd) * new_beta
    bal = balance_usd if balance_usd > 0 else 1e-9
    heat = total_risk / bal
    beta_exp = beta_risk / bal
    reasons = []
    if heat > max_heat_pct:
        reasons.append(f"Portföy ısısı %{heat*100:.1f} > limit %{max_heat_pct*100:.0f}")
    if beta_exp > max_beta_exposure:
        reasons.append(f"BTC-beta maruziyeti {beta_exp:.2f}x > limit {max_beta_exposure:.1f}x (korelasyon kümelenmesi)")
    return {
        "approved": len(reasons) == 0,
        "portfolio_heat_pct": round(heat * 100, 2),
        "beta_exposure_x": round(beta_exp, 2),
        "rejection_reasons": reasons,
    }


def tail_risk_check(recent_closes: List[float], asset: str = "",
                    crash_pct: float = 0.15, peg_target: float = 1.0) -> Dict:
    """P2 — Tail-risk / black-swan kill-switch. LUNA senaryosu: $80→$0 düşerken almaya devam = felaket.
    Son mumlarda ani çöküş (crash_pct) veya stablecoin depeg tespit edince DURDUR."""
    halt = False
    reasons = []
    if len(recent_closes) >= 5:
        recent = recent_closes[-5:]
        peak = max(recent)
        drop = (peak - recent_closes[-1]) / peak if peak > 0 else 0.0
        if drop >= crash_pct:
            halt = True
            reasons.append(f"Ani çöküş %{drop*100:.0f} (son 5 mum) — kademe-likidasyon riski")
        # volatilite patlaması
        rets = [abs(recent[i] / recent[i-1] - 1) for i in range(1, len(recent)) if recent[i-1] > 0]
        if rets and max(rets) >= 0.10:
            halt = True
            reasons.append(f"Volatilite patlaması %{max(rets)*100:.0f}/mum")
    # stablecoin depeg — BASE asset stablecoin mı (BTCUSDT'nin quote'u USDT, base BTC değil)
    sym = (asset or "").upper()
    is_stable = any(sym.startswith(s) for s in ["USDC", "DAI", "BUSD", "TUSD", "USDT"])
    if is_stable and recent_closes:
        depeg = abs(recent_closes[-1] - peg_target) / peg_target
        if depeg >= 0.02:
            halt = True
            reasons.append(f"Stablecoin DEPEG %{depeg*100:.1f} — çıkış yap")
    return {"halt": halt, "reasons": reasons}


def alpha_decay_check(live_win_rate: float, backtest_win_rate: float,
                      live_trades: int, min_trades: int = 20) -> Dict:
    """P3 — Alpha-decay monitörü. Canlı win-rate backtest'in çok altındaysa edge bozuluyor.
    Rejim değişimi: '2025 kârlı bot 2026 obsolete'. Edge bitince stratejiyi emekli et."""
    if live_trades < min_trades:
        return {"decaying": False, "action": "izle", "note": f"Yetersiz canlı veri ({live_trades}/{min_trades})"}
    ratio = (live_win_rate / backtest_win_rate) if backtest_win_rate > 0 else 1.0
    if ratio < 0.6:
        return {"decaying": True, "action": "EMEKLİ ET", "note": f"Canlı win-rate backtest'in %{ratio*100:.0f}'ı — edge öldü"}
    if ratio < 0.8:
        return {"decaying": True, "action": "küçült/yeniden-optimize", "note": f"Edge zayıflıyor (%{ratio*100:.0f})"}
    return {"decaying": False, "action": "devam", "note": f"Edge sağlam (%{ratio*100:.0f})"}


def select_strategy(regime: str) -> Dict:
    """P4a — Rejim-adaptif strateji. Tespit yetmez; trend'de momentum, range'de mean-reversion."""
    if regime == "trend":
        return {"strategy": "momentum", "note": "Trend rejimi → kırılım/momentum (MA crossover, trend-takip)"}
    if regime == "range":
        return {"strategy": "mean_reversion", "note": "Range rejimi → ortalamaya dönüş (Bollinger uçları, RSI aşırı)"}
    return {"strategy": "bekle", "note": "Geçiş rejimi → düşük güven, pozisyon küçült veya bekle"}


def twap_slices(total_qty: float, n_slices: int = 4) -> List[float]:
    """P4b — TWAP execution: büyük emri eşit dilimlere böl (market impact minimize)."""
    if n_slices < 1 or total_qty <= 0:
        return [total_qty] if total_qty > 0 else []
    base = round(total_qty / n_slices, 8)
    slices = [base] * (n_slices - 1)
    slices.append(round(total_qty - base * (n_slices - 1), 8))  # kalan son dilime
    return slices


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
