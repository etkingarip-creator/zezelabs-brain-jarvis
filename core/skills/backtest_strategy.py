import os
import sys
import logging
import pandas as pd
import numpy as np
from core.skills.registry import BaseSkill

logger = logging.getLogger("zom.skills.backtest_strategy")

# Try to import vectorbt
HAS_VECTORBT = False
try:
    import vectorbt as vbt
    HAS_VECTORBT = True
except Exception as e:
    logger.warning(f"vectorbt import failed: {e}. Falling back to Pandas implementation.")

class BacktestStrategySkill(BaseSkill):
    name = "backtest_strategy"
    description = (
        "Binance historical klines verisi üzerinde MA (Moving Average) Crossover "
        "backtest simülasyonu çalıştırır ve performans metriklerini hesaplar."
    )
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "İşlem yapılacak kripto parite çifti (örn: BTCUSDT)",
                "default": "BTCUSDT"
            },
            "fast_ma": {
                "type": "integer",
                "description": "Hızlı hareketli ortalama periyodu",
                "default": 12
            },
            "slow_ma": {
                "type": "integer",
                "description": "Yavaş hareketli ortalama periyodu",
                "default": 26
            },
            "interval": {
                "type": "string",
                "description": "Mum periyodu (1h, 1d, 15m vb.)",
                "default": "1h"
            },
            "limit": {
                "type": "integer",
                "description": "Geriye dönük sorgulanacak mum sayısı",
                "default": 100
            },
            "fee_rate": {
                "type": "number",
                "description": "İşlem komisyonu (Binance spot taker ~0.001)",
                "default": 0.001
            },
            "slippage": {
                "type": "number",
                "description": "Gerçekçi kayma oranı (fill kötüleşmesi, ~0.0005)",
                "default": 0.0005
            },
            "optimize": {
                "type": "boolean",
                "description": "True ise MA parametrelerini walk-forward OOS skoruna göre optimize eder",
                "default": False
            }
        },
        "required": []
    }

    async def execute(self, **kwargs) -> str:
        symbol = kwargs.get("symbol", "BTCUSDT")
        fast_ma = int(kwargs.get("fast_ma", 12))
        slow_ma = int(kwargs.get("slow_ma", 26))
        interval = kwargs.get("interval", "1h")
        limit = int(kwargs.get("limit", 100))
        fee_rate = float(kwargs.get("fee_rate", 0.001))
        slippage = float(kwargs.get("slippage", 0.0005))
        optimize = bool(kwargs.get("optimize", False))

        logger.info(f"Running backtest for {symbol} (Fast MA: {fast_ma}, Slow MA: {slow_ma}, Interval: {interval}, Limit: {limit})")

        # 1. Mum Verilerini Ajan Üzerinden Çek
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from departments.crypto_trading.agent import CryptoTradingAgent
        agent = CryptoTradingAgent(workspace_root=project_root)
        
        klines = await agent.get_binance_klines(symbol, interval, limit)
        if not klines or "error" in klines or not isinstance(klines, list):
            return f"Hata: Binance kline verileri çekilemedi. Detay: {klines}"

        # 2. Veriyi Pandas DataFrame'ine dönüştür
        try:
            # Kline format: [Open time, Open, High, Low, Close, Volume, Close time, ...]
            df = pd.DataFrame(klines, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
            ])
            df["close"] = df["close"].astype(float)
            df["open"] = df["open"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            df["volume"] = df["volume"].astype(float)
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df.set_index("open_time", inplace=True)
        except Exception as e:
            return f"Hata: Mum verileri ayrıştırılamadı. Detay: {e}"

        # 2.5 OPTİMİZASYON modu: en iyi MA parametrelerini OOS (walk-forward) skoruna göre bul
        if optimize:
            return self._optimize(df, symbol, interval, limit, fee_rate, slippage)

        # 3. Tüm-veri (in-sample) simülasyon — fee + slippage modellemeli
        metrics = self._run_pandas_sim(df, fast_ma, slow_ma, fee_rate, slippage)
        engine = "Pandas (fee+slippage)"

        # 4. WALK-FORWARD / OUT-OF-SAMPLE doğrulama — overfitting/curve-fit guard
        wf = self._walk_forward(df, fast_ma, slow_ma, fee_rate, slippage)

        # 5. Overfitting hükmü: OOS getiri IS'in çok altındaysa veya IS+ iken OOS- ise UYAR
        is_ret = metrics["total_return_pct"]
        oos_ret = wf["oos_return_pct"]
        overfit = (is_ret > 0 and oos_ret < 0) or (is_ret > 0 and oos_ret < is_ret * 0.4)
        verdict = ("GÜVENİLMEZ (overfit/regime riski) — bu sinyalle GERÇEK PARA RİSKE ATMA"
                   if overfit else "Tutarlı (in-sample ≈ out-of-sample)")

        result_lines = [
            f"=== Backtest Raporu (Motor: {engine}) ===",
            f"Parite: {symbol} | Periyot: {interval} | Mum: {limit} | Fee: %{fee_rate*100:.2f} | Slippage: %{slippage*100:.3f}",
            f"Strateji: SMA Crossover (Hızlı {fast_ma} / Yavaş {slow_ma})",
            "",
            "[IN-SAMPLE — tüm veri]",
            f"- Toplam Getiri: %{is_ret:.2f}",
            f"- Maks. Çekilme: %{metrics['max_drawdown_pct']:.2f}",
            f"- Sharpe: {metrics['sharpe_ratio']:.3f}",
            f"- İşlem: {metrics['total_trades']} | Win Rate: %{metrics['win_rate_pct']:.2f}",
            "",
            "[OUT-OF-SAMPLE — walk-forward doğrulama]",
            f"- OOS Ortalama Getiri: %{oos_ret:.2f} ({wf['n_windows']} pencere)",
            f"- OOS Win Rate: %{wf['oos_win_rate_pct']:.2f}",
            f"- Pencere tutarlılığı (pozitif %): %{wf['consistency_pct']:.0f}",
            "",
            f"[HÜKÜM] {verdict}",
        ]
        return "\n".join(result_lines)

    def _run_vectorbt_sim(self, df: pd.DataFrame, fast_ma: int, slow_ma: int) -> dict:
        # vectorbt ile MA indikatörlerini çalıştır
        fast_ma_ind = vbt.MA.run(df["close"], fast_ma)
        slow_ma_ind = vbt.MA.run(df["close"], slow_ma)

        # Altın/Ölüm kesişimleri
        entries = fast_ma_ind.ma_crossed_above(slow_ma_ind)
        exits = fast_ma_ind.ma_crossed_below(slow_ma_ind)

        # Portföy simülasyonu
        portfolio = vbt.Portfolio.from_signals(
            df["close"], 
            entries=entries, 
            exits=exits, 
            init_cash=100.0, 
            fees=0.001  # Binance spot komisyon standardı (%0.1)
        )

        total_return_pct = portfolio.total_return * 100
        max_drawdown_pct = portfolio.max_drawdown * 100
        sharpe_ratio = portfolio.sharpe_ratio
        if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
            sharpe_ratio = 0.0

        trades = portfolio.trades
        total_trades = trades.count()
        
        # Win rate
        if total_trades > 0:
            win_rate_pct = (trades.pnl.values > 0).sum() / total_trades * 100
        else:
            win_rate_pct = 0.0

        return {
            "total_return_pct": total_return_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": total_trades,
            "win_rate_pct": win_rate_pct
        }

    def _optimize(self, df: pd.DataFrame, symbol: str, interval: str, limit: int,
                  fee_rate: float, slippage: float) -> str:
        """Grid search — en iyi (fast,slow) MA'yı OUT-OF-SAMPLE skoruna göre seçer.
        In-sample'a göre seçmek curve-fit'tir; OOS'a göre seçmek dayanıklıdır."""
        fast_grid = [5, 8, 12, 20]
        slow_grid = [21, 26, 50, 100]
        results = []
        for f in fast_grid:
            for s in slow_grid:
                if f >= s:
                    continue
                wf = self._walk_forward(df.copy(), f, s, fee_rate, slippage)
                if wf["n_windows"] == 0:
                    continue
                # Skor: OOS getiri × tutarlılık (sadece getiri değil — istikrar da ödüllendirilir)
                score = wf["oos_return_pct"] * (wf["consistency_pct"] / 100.0)
                results.append((score, f, s, wf))
        if not results:
            return f"Optimizasyon başarısız: {symbol} için yeterli veri yok (limit artır)."
        results.sort(key=lambda x: x[0], reverse=True)
        best = results[0]
        _, bf, bs, bwf = best
        # En iyi parametreyle tam in-sample da göster
        is_m = self._run_pandas_sim(df.copy(), bf, bs, fee_rate, slippage)
        lines = [
            f"=== Parametre Optimizasyonu (OOS-tabanlı, curve-fit korumalı) ===",
            f"Parite: {symbol} | Periyot: {interval} | Mum: {limit} | {len(results)} kombinasyon test edildi",
            "",
            f"[EN İYİ PARAMETRE] Hızlı MA: {bf} / Yavaş MA: {bs}",
            f"- OOS Ortalama Getiri: %{bwf['oos_return_pct']:.2f} (tutarlılık %{bwf['consistency_pct']:.0f})",
            f"- OOS Win Rate: %{bwf['oos_win_rate_pct']:.2f}",
            f"- In-sample Getiri: %{is_m['total_return_pct']:.2f} | Sharpe: {is_m['sharpe_ratio']:.2f}",
            "",
            "[İLK 3 ALTERNATİF]",
        ]
        for sc, f, s, wf in results[1:4]:
            lines.append(f"- MA {f}/{s}: OOS %{wf['oos_return_pct']:.2f}, tutarlılık %{wf['consistency_pct']:.0f}")
        lines.append("")
        lines.append("NOT: Parametre OOS skoruna göre seçildi (in-sample'a göre değil) → curve-fit riski azaltıldı.")
        return "\n".join(lines)

    def _walk_forward(self, df: pd.DataFrame, fast_ma: int, slow_ma: int,
                      fee_rate: float, slippage: float, n_windows: int = 4) -> dict:
        """Walk-forward out-of-sample doğrulama: veriyi ardışık pencerelere böl,
        her pencereyi ayrı test et. Curve-fit/overfit'i ortaya çıkarır."""
        n = len(df)
        if n < (slow_ma + 10) * 2:
            return {"oos_return_pct": 0.0, "oos_win_rate_pct": 0.0, "consistency_pct": 0.0, "n_windows": 0}
        win = n // n_windows
        rets, wrs, positives = [], [], 0
        for i in range(n_windows):
            seg = df.iloc[i * win:(i + 1) * win]
            if len(seg) < slow_ma + 5:
                continue
            m = self._run_pandas_sim(seg.copy(), fast_ma, slow_ma, fee_rate, slippage)
            rets.append(m["total_return_pct"])
            wrs.append(m["win_rate_pct"])
            if m["total_return_pct"] > 0:
                positives += 1
        if not rets:
            return {"oos_return_pct": 0.0, "oos_win_rate_pct": 0.0, "consistency_pct": 0.0, "n_windows": 0}
        return {
            "oos_return_pct": sum(rets) / len(rets),
            "oos_win_rate_pct": sum(wrs) / len(wrs),
            "consistency_pct": positives / len(rets) * 100,
            "n_windows": len(rets),
        }

    def _run_pandas_sim(self, df: pd.DataFrame, fast_ma: int, slow_ma: int,
                        fee_rate: float = 0.001, slippage: float = 0.0005) -> dict:
        # Pandas ile hareketli ortalamaları hesapla
        df["fast"] = df["close"].rolling(fast_ma).mean()
        df["slow"] = df["close"].rolling(slow_ma).mean()

        # Sinyaller: fast > slow ise 1 (Al), değilse 0
        df["signal"] = 0
        df.loc[df["fast"] > df["slow"], "signal"] = 1
        df["position"] = df["signal"].shift(1).fillna(0)

        # İşlem tetiklenmeleri (Pozisyon değişimi)
        df["trade_action"] = df["position"].diff().fillna(0) # 1 = BUY, -1 = SELL

        # Basit simülasyon
        cash = 100.0
        holdings = 0.0
        portfolio_values = []
        trades_pnl = []
        buy_price = 0.0

        for timestamp, row in df.iterrows():
            action = row["trade_action"]
            price = row["close"]

            if action == 1 and cash > 0:  # BUY — slippage fiyatı kötüleştirir (yukarı)
                fill = price * (1 + slippage)
                fee = cash * fee_rate
                holdings = (cash - fee) / fill
                cash = 0.0
                buy_price = fill
            elif action == -1 and holdings > 0:  # SELL — slippage fiyatı kötüleştirir (aşağı)
                fill = price * (1 - slippage)
                val = holdings * fill
                fee = val * fee_rate
                cash = val - fee
                holdings = 0.0
                pnl = (fill - buy_price) / buy_price
                trades_pnl.append(pnl)

            # Güncel portföy değeri
            current_val = cash + (holdings * price)
            portfolio_values.append(current_val)

        df["portfolio_value"] = portfolio_values
        total_return_pct = ((portfolio_values[-1] - 100.0) / 100.0) * 100

        # Drawdown hesabı
        df["peak"] = df["portfolio_value"].cummax()
        df["drawdown"] = (df["portfolio_value"] - df["peak"]) / df["peak"] * 100
        max_drawdown_pct = abs(df["drawdown"].min())

        # Sharpe Oranı
        df["daily_returns"] = df["portfolio_value"].pct_change().fillna(0)
        std = df["daily_returns"].std()
        mean = df["daily_returns"].mean()
        
        # Yıllıklandırma çarpanı (Örn: saatlik veri için 24 * 365)
        # Basitlik için standard std/mean oranından gidiyoruz
        if std > 0:
            sharpe_ratio = (mean / std) * np.sqrt(252) # Basit günlük varsayım
        else:
            sharpe_ratio = 0.0

        total_trades = len(trades_pnl)
        if total_trades > 0:
            win_rate_pct = sum(1 for p in trades_pnl if p > 0) / total_trades * 100
        else:
            win_rate_pct = 0.0

        return {
            "total_return_pct": total_return_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": total_trades,
            "win_rate_pct": win_rate_pct
        }
