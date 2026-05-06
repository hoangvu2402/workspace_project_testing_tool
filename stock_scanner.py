"""
Stock Scanner - Quet toan bo co phieu tren san HOSE/HNX.
Phan tich da phuong phap va xep hang top 100 co phieu tiem nang.

Cac phuong phap phan tich:
  1. Ichimoku Kinko Hyo
  2. RSI (Relative Strength Index)
  3. MACD (Moving Average Convergence Divergence)
  4. Bollinger Bands
  5. Moving Average (SMA 20/50/200)
  6. Volume trend analysis
  7. Price momentum (ROC - Rate of Change)
"""
import math
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

QUOTE_URL = "https://svr2.fireant.vn/api/Data/Markets/Quotes"
HIST_URL = "https://svr2.fireant.vn/api/Data/Markets/HistoricalQuotes"
SYMBOLS_URL = "https://wifeed.vn/api/thong-tin-co-phieu/danh-sach-ma-chung-khoan"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


# ============================================================
# DATA FETCHING
# ============================================================

def fetch_all_symbols(exchanges=("HOSE", "HNX")) -> list[str]:
    """Lay danh sach tat ca ma co phieu tren san."""
    try:
        resp = requests.get(SYMBOLS_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        symbols = [
            d["code"]
            for d in data
            if d.get("san") in exchanges and d.get("loaidn") in (1, 2)
        ]
        return sorted(symbols)
    except Exception as e:
        print(f"[ERROR] fetch_all_symbols: {e}")
        return []


def fetch_batch_quotes(symbols: list[str]) -> list[dict]:
    """Lay du lieu realtime cho nhieu ma cung luc (toi da 30/batch)."""
    results = []
    batch_size = 30
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        try:
            resp = requests.get(
                QUOTE_URL,
                params={"symbols": ",".join(batch)},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                results.extend(data)
        except Exception as e:
            print(f"[ERROR] fetch_batch_quotes batch {i}: {e}")
        time.sleep(0.3)
    return results


def fetch_historical(symbol: str, days: int = 400) -> list[dict]:
    """Lay du lieu lich su (can nhieu du lieu cho SMA200, Ichimoku, v.v.)."""
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        resp = requests.get(
            HIST_URL,
            params={
                "symbol": symbol.upper(),
                "startDate": start.strftime("%Y-%m-%d"),
                "endDate": end.strftime("%Y-%m-%d"),
            },
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            data.sort(key=lambda x: x.get("Date", ""))
            return data
    except Exception as e:
        print(f"[ERROR] fetch_historical({symbol}): {e}")
    return []


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def _sma(values: list[float], period: int) -> list[float]:
    """Simple Moving Average."""
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1 : i + 1]) / period)
    return result


def _ema(values: list[float], period: int) -> list[float]:
    """Exponential Moving Average."""
    result = []
    k = 2 / (period + 1)
    for i, v in enumerate(values):
        if i == 0:
            result.append(v)
        else:
            result.append(v * k + result[-1] * (1 - k))
    return result


def calc_rsi(closes: list[float], period: int = 14) -> float | None:
    """RSI (Relative Strength Index). Tra ve gia tri RSI hien tai."""
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd(closes: list[float]) -> dict | None:
    """MACD (12, 26, 9). Tra ve macd_line, signal, histogram."""
    if len(closes) < 35:
        return None
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd_line = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
    signal = _ema(macd_line[25:], 9)
    if not signal:
        return None
    macd_val = macd_line[-1]
    signal_val = signal[-1]
    histogram = macd_val - signal_val

    prev_macd = macd_line[-2] if len(macd_line) >= 2 else macd_val
    prev_signal = signal[-2] if len(signal) >= 2 else signal_val
    cross_up = prev_macd <= prev_signal and macd_val > signal_val
    cross_down = prev_macd >= prev_signal and macd_val < signal_val

    return {
        "macd": macd_val,
        "signal": signal_val,
        "histogram": histogram,
        "cross_up": cross_up,
        "cross_down": cross_down,
    }


def calc_bollinger(closes: list[float], period: int = 20, num_std: float = 2.0) -> dict | None:
    """Bollinger Bands."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    sma = sum(window) / period
    variance = sum((x - sma) ** 2 for x in window) / period
    std = math.sqrt(variance)
    upper = sma + num_std * std
    lower = sma - num_std * std
    current = closes[-1]

    pct_b = (current - lower) / (upper - lower) if upper != lower else 0.5
    bandwidth = (upper - lower) / sma if sma else 0

    return {
        "upper": upper,
        "middle": sma,
        "lower": lower,
        "pct_b": pct_b,
        "bandwidth": bandwidth,
        "price_position": "TREN" if current > upper else ("DUOI" if current < lower else "TRONG"),
    }


def calc_moving_averages(closes: list[float]) -> dict:
    """SMA 20, 50, 200 va tin hieu."""
    result = {}
    current = closes[-1] if closes else 0
    for period in (20, 50, 200):
        if len(closes) >= period:
            sma_val = sum(closes[-period:]) / period
            result[f"sma{period}"] = sma_val
            result[f"above_sma{period}"] = current > sma_val
        else:
            result[f"sma{period}"] = None
            result[f"above_sma{period}"] = None

    if result.get("sma50") and result.get("sma200"):
        result["golden_cross"] = result["sma50"] > result["sma200"]
    else:
        result["golden_cross"] = None

    return result


def calc_volume_trend(volumes: list[float], period: int = 20) -> dict | None:
    """Phan tich xu huong khoi luong."""
    if len(volumes) < period:
        return None
    avg_vol = sum(volumes[-period:]) / period
    current_vol = volumes[-1]
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1

    recent_avg = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else current_vol
    older_avg = sum(volumes[-period : -5]) / max(period - 5, 1) if len(volumes) >= period else avg_vol
    vol_trend = recent_avg / older_avg if older_avg > 0 else 1

    return {
        "avg_volume": avg_vol,
        "current_volume": current_vol,
        "vol_ratio": vol_ratio,
        "vol_trend": vol_trend,
        "high_volume": vol_ratio > 1.5,
    }


def calc_roc(closes: list[float], period: int = 10) -> float | None:
    """Rate of Change (momentum)."""
    if len(closes) <= period:
        return None
    old_price = closes[-period - 1]
    if old_price == 0:
        return None
    return ((closes[-1] - old_price) / old_price) * 100


def calc_ichimoku_signal(hist: list[dict]) -> dict | None:
    """Ichimoku signal cho scanner (don gian hoa)."""
    if len(hist) < 52:
        return None

    highs = [d.get("High", 0) for d in hist]
    lows = [d.get("Low", 0) for d in hist]
    closes = [d.get("Close", 0) for d in hist]
    n = len(hist)
    idx = n - 1

    def _hl(period, i):
        s = max(0, i - period + 1)
        return max(highs[s : i + 1]), min(lows[s : i + 1])

    h9, l9 = _hl(9, idx)
    tenkan = (h9 + l9) / 2
    h26, l26 = _hl(26, idx)
    kijun = (h26 + l26) / 2

    senkou_a = (tenkan + kijun) / 2
    h52, l52 = _hl(52, idx)
    senkou_b = (h52 + l52) / 2

    idx_past = idx - 26
    if idx_past >= 26:
        h9p, l9p = _hl(9, idx_past)
        h26p, l26p = _hl(26, idx_past)
        sa_cur = ((h9p + l9p) / 2 + (h26p + l26p) / 2) / 2
    else:
        sa_cur = senkou_a
    if idx_past >= 52:
        h52p, l52p = _hl(52, idx_past)
        sb_cur = (h52p + l52p) / 2
    else:
        sb_cur = senkou_b

    current = closes[idx]
    kumo_top = max(sa_cur, sb_cur)
    kumo_bottom = min(sa_cur, sb_cur)

    score = 0
    if current > kumo_top:
        score += 2
    elif current < kumo_bottom:
        score -= 2

    if tenkan > kijun:
        score += 1
    elif tenkan < kijun:
        score -= 1

    chikou = closes[idx]
    price_26_ago = closes[idx - 26] if idx >= 26 else closes[0]
    if chikou > price_26_ago:
        score += 1
    elif chikou < price_26_ago:
        score -= 1

    if senkou_a > senkou_b:
        score += 1
    else:
        score -= 1

    return {"score": score, "max_score": 5}


# ============================================================
# COMPOSITE SCORING & EXPECTED PRICE
# ============================================================

def analyze_stock(symbol: str, hist: list[dict]) -> dict | None:
    """Phan tich toan dien 1 co phieu, tra ve diem va gia ky vong."""
    if len(hist) < 60:
        return None

    closes = [d.get("Close", 0) for d in hist]
    highs = [d.get("High", 0) for d in hist]
    lows = [d.get("Low", 0) for d in hist]
    volumes = [d.get("Volume", 0) for d in hist]
    current_price = closes[-1]

    if current_price <= 0:
        return None

    # ---- Calculate all indicators ----
    rsi = calc_rsi(closes)
    macd = calc_macd(closes)
    boll = calc_bollinger(closes)
    ma = calc_moving_averages(closes)
    vol = calc_volume_trend(volumes)
    roc = calc_roc(closes)
    ichi = calc_ichimoku_signal(hist)

    # ---- Scoring system (0-100) ----
    score = 50  # baseline

    # 1. RSI (weight: 15)
    if rsi is not None:
        if 30 <= rsi <= 45:
            score += 12  # oversold recovery zone
        elif 45 < rsi <= 60:
            score += 8   # healthy momentum
        elif rsi < 30:
            score += 5   # deeply oversold (potential bounce)
        elif 60 < rsi <= 70:
            score += 3   # strong but nearing overbought
        elif rsi > 70:
            score -= 5   # overbought

    # 2. MACD (weight: 15)
    if macd:
        if macd["cross_up"]:
            score += 15
        elif macd["histogram"] > 0:
            score += 8
        elif macd["cross_down"]:
            score -= 10
        elif macd["histogram"] < 0:
            score -= 5

    # 3. Bollinger (weight: 10)
    if boll:
        if boll["price_position"] == "DUOI":
            score += 10  # below lower band -> potential bounce
        elif boll["pct_b"] < 0.3:
            score += 6
        elif boll["price_position"] == "TREN":
            score -= 3

    # 4. Moving Averages (weight: 20)
    if ma.get("above_sma20"):
        score += 5
    if ma.get("above_sma50"):
        score += 5
    if ma.get("above_sma200"):
        score += 5
    if ma.get("golden_cross") is True:
        score += 5
    elif ma.get("golden_cross") is False:
        score -= 5

    # 5. Volume (weight: 10)
    if vol:
        if vol["high_volume"] and roc and roc > 0:
            score += 10  # high volume + price up
        elif vol["vol_trend"] > 1.2:
            score += 5
        elif vol["vol_trend"] < 0.7:
            score -= 3

    # 6. Momentum/ROC (weight: 10)
    if roc is not None:
        if roc > 5:
            score += 8
        elif roc > 0:
            score += 4
        elif roc < -10:
            score -= 8
        elif roc < 0:
            score -= 3

    # 7. Ichimoku (weight: 20)
    if ichi:
        ichi_normalized = (ichi["score"] / ichi["max_score"]) * 20
        score += ichi_normalized

    score = max(0, min(100, score))

    # ---- Expected price calculation ----
    # Combine multiple methods for price targets
    avg_return_3m = _estimate_return(closes, months=3)
    avg_return_6m = _estimate_return(closes, months=6)
    avg_return_12m = _estimate_return(closes, months=12)

    # Adjust expected return based on score
    score_multiplier = (score - 30) / 70  # -0.43 to 1.0
    score_multiplier = max(-0.3, min(1.5, score_multiplier))

    # SMA trend-based target
    sma50 = ma.get("sma50", current_price)
    sma200 = ma.get("sma200", current_price)

    def _target(base_return, months):
        trend_adj = base_return * (1 + score_multiplier * 0.5)
        # Blend with SMA targets
        if sma50 and sma200:
            sma_target = (sma50 * 0.3 + sma200 * 0.7) * (1 + trend_adj / 100)
            blend = current_price * (1 + trend_adj / 100) * 0.6 + sma_target * 0.4
        else:
            blend = current_price * (1 + trend_adj / 100)
        return max(blend, current_price * 0.5)

    price_3m = _target(avg_return_3m, 3)
    price_6m = _target(avg_return_6m, 6)
    price_12m = _target(avg_return_12m, 12)

    return {
        "symbol": symbol,
        "current_price": current_price,
        "score": round(score, 1),
        "rsi": round(rsi, 1) if rsi else None,
        "macd_signal": "MUA" if (macd and macd["histogram"] > 0) else "BAN" if macd else "--",
        "bollinger": boll["price_position"] if boll else "--",
        "ma_trend": "TANG" if ma.get("golden_cross") else ("GIAM" if ma.get("golden_cross") is False else "--"),
        "volume_signal": "CAO" if (vol and vol["high_volume"]) else "BT" if vol else "--",
        "ichimoku_score": ichi["score"] if ichi else 0,
        "roc": round(roc, 1) if roc else None,
        "price_3m": round(price_3m, 0),
        "price_6m": round(price_6m, 0),
        "price_12m": round(price_12m, 0),
        "upside_3m": round((price_3m / current_price - 1) * 100, 1) if current_price > 0 else 0,
        "upside_6m": round((price_6m / current_price - 1) * 100, 1) if current_price > 0 else 0,
        "upside_12m": round((price_12m / current_price - 1) * 100, 1) if current_price > 0 else 0,
    }


def _estimate_return(closes: list[float], months: int) -> float:
    """Uoc tinh loi nhuan ky vong dua tren du lieu lich su."""
    trading_days = months * 22
    if len(closes) < trading_days:
        trading_days = len(closes) - 1
    if trading_days <= 0:
        return 0
    old = closes[-trading_days - 1] if len(closes) > trading_days else closes[0]
    if old <= 0:
        return 0
    return ((closes[-1] / old) - 1) * 100


# ============================================================
# MAIN SCANNER
# ============================================================

def scan_all_stocks(progress_callback=None, exchanges=("HOSE", "HNX")) -> list[dict]:
    """
    Quet toan bo co phieu, phan tich va xep hang.
    progress_callback(current, total, symbol) duoc goi sau moi co phieu.
    Tra ve danh sach da sap xep theo score giam dan.
    """
    symbols = fetch_all_symbols(exchanges)
    if not symbols:
        return []

    total = len(symbols)
    results = []
    errors = 0

    def process_symbol(sym):
        try:
            hist = fetch_historical(sym, days=400)
            if not hist or len(hist) < 60:
                return None
            return analyze_stock(sym, hist)
        except Exception as e:
            print(f"[ERROR] process {sym}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_symbol, sym): sym for sym in symbols}
        done_count = 0
        for future in as_completed(futures):
            sym = futures[future]
            done_count += 1
            try:
                result = future.result()
                if result:
                    results.append(result)
                else:
                    errors += 1
            except Exception:
                errors += 1
            if progress_callback:
                progress_callback(done_count, total, sym)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_top_stocks(results: list[dict], top_n: int = 100, sort_by: str = "score") -> list[dict]:
    """Lay top N co phieu tu ket qua scan."""
    if sort_by == "upside_3m":
        results.sort(key=lambda x: x.get("upside_3m", 0), reverse=True)
    elif sort_by == "upside_6m":
        results.sort(key=lambda x: x.get("upside_6m", 0), reverse=True)
    elif sort_by == "upside_12m":
        results.sort(key=lambda x: x.get("upside_12m", 0), reverse=True)
    else:
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results[:top_n]
