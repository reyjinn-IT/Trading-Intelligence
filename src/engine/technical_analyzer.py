"""Technical Analyzer for 40% Trend & Market Structure scoring."""
import numpy as np
import pandas as pd
from typing import Dict, Any, List


class TechnicalAnalyzer:
    def __init__(self):
        pass

    def compute_indicators(self, candles: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert candles to DataFrame and calculate EMAs, RSI, and MACD."""
        df = pd.DataFrame(candles)
        if len(df) < 14:
            return df

        # EMAs (18, 50, 200)
        df["ema18"] = df["close"].ewm(span=18, adjust=False).mean()
        df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
        df["ema200"] = df["close"].ewm(span=min(200, len(df)), adjust=False).mean()

        # RSI (14)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        return df

    def analyze(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze Trend & Market Structure (40% of total confluence).
        Returns trend_score (0 - 100), direction ('BULLISH', 'BEARISH', 'SIDEWAYS'), and detailed text.
        """
        if not candles or len(candles) < 10:
            return {
                "score": 50.0,
                "direction": "SIDEWAYS",
                "trend_state": "DATA_LIMITED",
                "summary": "Data candlestick terbatas; tren netral / konsolidasi."
            }

        df = self.compute_indicators(candles)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        close = float(last["close"])
        ema18 = float(last.get("ema18", close))
        ema50 = float(last.get("ema50", close))
        ema200 = float(last.get("ema200", close))
        rsi = float(last.get("rsi", 50.0))
        macd_hist = float(last.get("macd_hist", 0.0))

        # 1. Trend Direction Scoring
        score = 50.0
        direction = "SIDEWAYS"
        structure_desc = "Konsolidasi di sekitar moving average."

        # Detect EMA alignment (18, 50, 200)
        is_uptrend = close > ema18 and ema18 > ema50 and ema50 >= ema200
        is_downtrend = close < ema18 and ema18 < ema50 and ema50 <= ema200

        # Highs and Lows for Market Structure (BOS / CHoCH)
        recent_highs = df["high"].iloc[-20:].values
        recent_lows = df["low"].iloc[-20:].values
        is_higher_high = recent_highs[-1] >= np.max(recent_highs[:-1])
        is_lower_low = recent_lows[-1] <= np.min(recent_lows[:-1])

        if is_uptrend or (close > ema50 and is_higher_high):
            direction = "BULLISH"
            score = 75.0
            if is_higher_high:
                score += 15.0
                structure_desc = "Konfirmasi Bullish Break of Structure (BOS), Higher High tercapai."
            else:
                structure_desc = "Struktur Uptrend solid (Harga > EMA 18 > EMA 50 > EMA 200)."

            # Momentum additions
            if 50.0 <= rsi <= 70.0:
                score += 10.0
            elif rsi > 78.0:
                score -= 10.0  # Overbought penalty
                structure_desc += " Waspada kondisi RSI Overbought."
            if macd_hist > 0:
                score += 5.0

        elif is_downtrend or (close < ema50 and is_lower_low):
            direction = "BEARISH"
            score = 25.0
            if is_lower_low:
                score -= 15.0
                structure_desc = "Konfirmasi Bearish Break of Structure (BOS), Lower Low terbentuk."
            else:
                structure_desc = "Struktur Downtrend dominan (Harga < EMA 18 < EMA 50 < EMA 200)."

            if 30.0 <= rsi <= 50.0:
                score -= 5.0
            elif rsi < 22.0:
                score += 10.0  # Oversold bounce possibility
                structure_desc += " Kondisi RSI Oversold ekstrem."
            if macd_hist < 0:
                score -= 5.0

        score = max(5.0, min(98.0, score))

        summary = (
            f"Arah Tren: {direction} ({structure_desc}) | "
            f"RSI(14): {rsi:.1f}, EMA18: {ema18:,.2f}, EMA50: {ema50:,.2f}, "
            f"MACD Hist: {macd_hist:+.2f}"
        )

        return {
            "score": round(score, 2),
            "direction": direction,
            "close": close,
            "ema18": ema18,
            "ema50": ema50,
            "ema200": ema200,
            "rsi": round(rsi, 2),
            "macd_hist": round(macd_hist, 4),
            "structure_desc": structure_desc,
            "summary": summary
        }


technical_analyzer = TechnicalAnalyzer()
