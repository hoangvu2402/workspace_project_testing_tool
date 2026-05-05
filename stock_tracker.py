"""
Stock Tracker App - Theo doi co phieu tu FireAnt.vn
Su dung Ichimoku Kinko Hyo de du doan xu huong co phieu.
Quet du lieu dinh ky moi 1 phut.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from datetime import datetime, timedelta


# ============================================================
# DATA LAYER - FireAnt SVR2 public API
# ============================================================

QUOTE_URL = "https://svr2.fireant.vn/api/Data/Markets/Quotes"
HIST_URL = "https://svr2.fireant.vn/api/Data/Markets/HistoricalQuotes"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def fetch_realtime_quote(symbol: str) -> dict | None:
    """Lay du lieu realtime cua co phieu tu FireAnt."""
    try:
        resp = requests.get(
            QUOTE_URL,
            params={"symbols": symbol.upper()},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
    except Exception as e:
        print(f"[ERROR] fetch_realtime_quote({symbol}): {e}")
    return None


def fetch_historical_quotes(symbol: str, days: int = 120) -> list[dict]:
    """Lay du lieu lich su de tinh Ichimoku (can >= 52 phien)."""
    end = datetime.now()
    start = end - timedelta(days=days * 2)
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
        print(f"[ERROR] fetch_historical_quotes({symbol}): {e}")
    return []


# ============================================================
# ICHIMOKU KINKO HYO
# ============================================================

def _period_high_low(highs, lows, period, idx):
    s = max(0, idx - period + 1)
    h = max(highs[s: idx + 1]) if idx >= 0 else 0
    lo = min(lows[s: idx + 1]) if idx >= 0 else 0
    return h, lo


def compute_ichimoku(hist: list[dict]) -> dict | None:
    """
    Tinh cac duong Ichimoku va dua ra tin hieu du doan.
    Tenkan-sen (9), Kijun-sen (26), Senkou A/B, Chikou Span.
    """
    if len(hist) < 52:
        return None

    highs = [d.get("High", 0) for d in hist]
    lows = [d.get("Low", 0) for d in hist]
    closes = [d.get("Close", 0) for d in hist]
    n = len(hist)
    idx = n - 1

    h9, l9 = _period_high_low(highs, lows, 9, idx)
    tenkan = (h9 + l9) / 2

    h26, l26 = _period_high_low(highs, lows, 26, idx)
    kijun = (h26 + l26) / 2

    senkou_a = (tenkan + kijun) / 2

    h52, l52 = _period_high_low(highs, lows, 52, idx)
    senkou_b = (h52 + l52) / 2

    idx_past = idx - 26
    if idx_past >= 26:
        h9p, l9p = _period_high_low(highs, lows, 9, idx_past)
        h26p, l26p = _period_high_low(highs, lows, 26, idx_past)
        senkou_a_current = ((h9p + l9p) / 2 + (h26p + l26p) / 2) / 2
    else:
        senkou_a_current = senkou_a

    if idx_past >= 52:
        h52p, l52p = _period_high_low(highs, lows, 52, idx_past)
        senkou_b_current = (h52p + l52p) / 2
    else:
        senkou_b_current = senkou_b

    chikou = closes[idx]
    price_26_ago = closes[idx - 26] if idx >= 26 else closes[0]
    current_price = closes[idx]

    signals = []
    trend = "TRUNG TINH"

    kumo_top = max(senkou_a_current, senkou_b_current)
    kumo_bottom = min(senkou_a_current, senkou_b_current)

    if current_price > kumo_top:
        signals.append("Gia TREN may Kumo -> XU HUONG TANG")
        trend = "TANG"
    elif current_price < kumo_bottom:
        signals.append("Gia DUOI may Kumo -> XU HUONG GIAM")
        trend = "GIAM"
    else:
        signals.append("Gia TRONG may Kumo -> DI NGANG / CHUA RO")

    if tenkan > kijun:
        signals.append("Tenkan > Kijun -> Tin hieu MUA (TK Cross)")
    elif tenkan < kijun:
        signals.append("Tenkan < Kijun -> Tin hieu BAN (TK Cross)")
    else:
        signals.append("Tenkan = Kijun -> Chua co tin hieu cross")

    if chikou > price_26_ago:
        signals.append("Chikou > Gia 26 phien truoc -> Xac nhan TANG")
    elif chikou < price_26_ago:
        signals.append("Chikou < Gia 26 phien truoc -> Xac nhan GIAM")

    if senkou_a > senkou_b:
        signals.append("Senkou A > B -> May tuong lai XANH (Tang)")
    else:
        signals.append("Senkou A < B -> May tuong lai DO (Giam)")

    bullish = sum(1 for s in signals if "TANG" in s or "MUA" in s or "XANH" in s)
    bearish = sum(1 for s in signals if "GIAM" in s or "BAN" in s or "DO" in s)

    if bullish >= 3:
        prediction = "DU DOAN: XU HUONG TANG MANH"
    elif bullish > bearish:
        prediction = "DU DOAN: NGHIENG VE TANG"
    elif bearish >= 3:
        prediction = "DU DOAN: XU HUONG GIAM MANH"
    elif bearish > bullish:
        prediction = "DU DOAN: NGHIENG VE GIAM"
    else:
        prediction = "DU DOAN: TRUNG TINH / DI NGANG"

    return {
        "tenkan": tenkan,
        "kijun": kijun,
        "senkou_a": senkou_a,
        "senkou_b": senkou_b,
        "senkou_a_cur": senkou_a_current,
        "senkou_b_cur": senkou_b_current,
        "chikou": chikou,
        "kumo_top": kumo_top,
        "kumo_bottom": kumo_bottom,
        "trend": trend,
        "signals": signals,
        "prediction": prediction,
    }


# ============================================================
# ALERT SOUND
# ============================================================

def _play_alert():
    try:
        import subprocess
        subprocess.Popen(
            ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print("\a")


# ============================================================
# FORMAT HELPERS
# ============================================================

def fmt_price(val):
    """Format gia co phieu: API tra ve don vi VND.
    Hien thi theo kieu FireAnt (chia 1000), vd 19050 -> 19.05"""
    if not val:
        return "--"
    return f"{val / 1000:,.2f}"


def fmt_vol(val):
    if not val:
        return "--"
    return f"{int(val):,}"


# ============================================================
# TKINTER GUI
# ============================================================

class StockTrackerApp:
    SCAN_INTERVAL_MS = 60_000  # 1 phut

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Stock Tracker - FireAnt.vn | Ichimoku Kinko Hyo")
        self.root.geometry("1100x850")
        self.root.minsize(950, 720)

        self._tracking_symbol = None
        self._scan_job = None
        self._alert_upper = None
        self._alert_lower = None
        self._alerted_upper = False
        self._alerted_lower = False

        style = ttk.Style()
        style.theme_use("clam")

        self._build_ui()

    def _build_ui(self):
        # --- Top: input ---
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Ma co phieu:", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        self.entry_symbol = ttk.Entry(top, width=12, font=("Arial", 12))
        self.entry_symbol.pack(side=tk.LEFT, padx=6)
        self.entry_symbol.bind("<Return>", lambda e: self._on_track())

        self.btn_track = ttk.Button(top, text="Theo doi", command=self._on_track)
        self.btn_track.pack(side=tk.LEFT, padx=4)

        self.btn_stop = ttk.Button(top, text="Dung", command=self._on_stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.lbl_status = ttk.Label(top, text="Chua theo doi", foreground="gray", font=("Arial", 10))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # --- Price headline ---
        price_frame = ttk.Frame(self.root, padding=(8, 2))
        price_frame.pack(fill=tk.X)
        self.lbl_price_headline = ttk.Label(
            price_frame,
            text="---",
            font=("Arial", 18, "bold"),
            foreground="#333",
        )
        self.lbl_price_headline.pack(side=tk.LEFT)
        self.lbl_price_change = ttk.Label(
            price_frame,
            text="",
            font=("Arial", 13),
        )
        self.lbl_price_change.pack(side=tk.LEFT, padx=12)
        self.lbl_update_time = ttk.Label(
            price_frame, text="", font=("Arial", 9), foreground="gray"
        )
        self.lbl_update_time.pack(side=tk.RIGHT)

        # --- Alert ---
        alert_frame = ttk.LabelFrame(self.root, text="Nguong gia canh bao (don vi: x1000 VND, vd 19.5 = 19,500 VND)", padding=8)
        alert_frame.pack(fill=tk.X, padx=8, pady=(0, 4))

        ttk.Label(alert_frame, text="Chan tren:").pack(side=tk.LEFT)
        self.entry_upper = ttk.Entry(alert_frame, width=10, font=("Arial", 11))
        self.entry_upper.pack(side=tk.LEFT, padx=4)

        ttk.Label(alert_frame, text="Chan duoi:").pack(side=tk.LEFT, padx=(16, 0))
        self.entry_lower = ttk.Entry(alert_frame, width=10, font=("Arial", 11))
        self.entry_lower.pack(side=tk.LEFT, padx=4)

        self.btn_set_alert = ttk.Button(alert_frame, text="Dat nguong", command=self._on_set_alert)
        self.btn_set_alert.pack(side=tk.LEFT, padx=10)

        self.lbl_alert_status = ttk.Label(alert_frame, text="Chua dat", foreground="gray")
        self.lbl_alert_status.pack(side=tk.LEFT, padx=10)

        # --- Tabs ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        tab_overview = ttk.Frame(notebook, padding=8)
        notebook.add(tab_overview, text="  Tong Quan  ")
        self._build_overview_tab(tab_overview)

        tab_orders = ttk.Frame(notebook, padding=8)
        notebook.add(tab_orders, text="  So Lenh Mua/Ban  ")
        self._build_orders_tab(tab_orders)

        tab_ichimoku = ttk.Frame(notebook, padding=8)
        notebook.add(tab_ichimoku, text="  Ichimoku Kinko Hyo  ")
        self._build_ichimoku_tab(tab_ichimoku)

        # --- Log ---
        log_frame = ttk.LabelFrame(self.root, text="Nhat ky", padding=4)
        log_frame.pack(fill=tk.X, padx=8, pady=(0, 6))
        self.txt_log = tk.Text(log_frame, height=4, font=("Consolas", 9), state=tk.DISABLED, bg="#f5f5f5")
        self.txt_log.pack(fill=tk.X)

    def _build_overview_tab(self, parent):
        cols = [("Chi so", 250), ("Gia tri", 200)]
        self.tree_overview = ttk.Treeview(parent, columns=[c[0] for c in cols], show="headings", height=18)
        for name, w in cols:
            self.tree_overview.heading(name, text=name)
            self.tree_overview.column(name, width=w, anchor=tk.W if name == "Chi so" else tk.E)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_overview.yview)
        self.tree_overview.configure(yscrollcommand=scrollbar.set)
        self.tree_overview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_orders_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(parent, text="LENH MUA (BID)", padding=6)
        paned.add(left, weight=1)
        buy_cols = [("Gia (x1000)", 120), ("Khoi luong", 120)]
        self.tree_buy = ttk.Treeview(left, columns=[c[0] for c in buy_cols], show="headings", height=6)
        for name, w in buy_cols:
            self.tree_buy.heading(name, text=name)
            self.tree_buy.column(name, width=w, anchor=tk.E)
        self.tree_buy.pack(fill=tk.BOTH, expand=True)

        right = ttk.LabelFrame(parent, text="LENH BAN (ASK)", padding=6)
        paned.add(right, weight=1)
        sell_cols = [("Gia (x1000)", 120), ("Khoi luong", 120)]
        self.tree_sell = ttk.Treeview(right, columns=[c[0] for c in sell_cols], show="headings", height=6)
        for name, w in sell_cols:
            self.tree_sell.heading(name, text=name)
            self.tree_sell.column(name, width=w, anchor=tk.E)
        self.tree_sell.pack(fill=tk.BOTH, expand=True)

        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill=tk.X, pady=(8, 0))

        self.lbl_buy_summary = ttk.Label(summary_frame, text="KL Mua chu dong: --", font=("Arial", 10, "bold"), foreground="#2e7d32")
        self.lbl_buy_summary.pack(side=tk.LEFT, padx=8)

        self.lbl_sell_summary = ttk.Label(summary_frame, text="KL Ban chu dong: --", font=("Arial", 10, "bold"), foreground="#c62828")
        self.lbl_sell_summary.pack(side=tk.LEFT, padx=20)

        self.lbl_total_vol = ttk.Label(summary_frame, text="Tong KL: --", font=("Arial", 10))
        self.lbl_total_vol.pack(side=tk.LEFT, padx=20)

        self.lbl_total_val = ttk.Label(summary_frame, text="Tong GT: --", font=("Arial", 10))
        self.lbl_total_val.pack(side=tk.LEFT, padx=20)

    def _build_ichimoku_tab(self, parent):
        vals_frame = ttk.LabelFrame(parent, text="Cac duong Ichimoku (gia tri x1000 VND)", padding=8)
        vals_frame.pack(fill=tk.X, pady=(0, 6))

        ichi_cols = [("Duong", 240), ("Gia tri", 160)]
        self.tree_ichi = ttk.Treeview(vals_frame, columns=[c[0] for c in ichi_cols], show="headings", height=7)
        for name, w in ichi_cols:
            self.tree_ichi.heading(name, text=name)
            self.tree_ichi.column(name, width=w, anchor=tk.W if name == "Duong" else tk.E)
        self.tree_ichi.pack(fill=tk.BOTH, expand=True)

        sig_frame = ttk.LabelFrame(parent, text="Tin hieu & Du doan", padding=8)
        sig_frame.pack(fill=tk.BOTH, expand=True)

        self.txt_signals = tk.Text(sig_frame, height=10, font=("Consolas", 10), state=tk.DISABLED, bg="#fffde7", wrap=tk.WORD)
        self.txt_signals.pack(fill=tk.BOTH, expand=True)

    # --- Helpers ---

    def _log(self, msg):
        self.txt_log.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{ts}] {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    # --- Event handlers ---

    def _on_track(self):
        symbol = self.entry_symbol.get().strip().upper()
        if not symbol:
            messagebox.showwarning("Loi", "Vui long nhap ma co phieu!")
            return
        self._tracking_symbol = symbol
        self.btn_track.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text=f"Dang theo doi: {symbol}", foreground="green")
        self._alerted_upper = False
        self._alerted_lower = False
        self._log(f"Bat dau theo doi: {symbol}")
        self._do_scan()

    def _on_stop(self):
        self._tracking_symbol = None
        if self._scan_job:
            self.root.after_cancel(self._scan_job)
            self._scan_job = None
        self.btn_track.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="Da dung theo doi", foreground="gray")
        self._log("Da dung theo doi.")

    def _on_set_alert(self):
        upper_txt = self.entry_upper.get().strip()
        lower_txt = self.entry_lower.get().strip()
        self._alert_upper = None
        self._alert_lower = None
        self._alerted_upper = False
        self._alerted_lower = False
        msgs = []
        if upper_txt:
            try:
                self._alert_upper = float(upper_txt.replace(",", ""))
                msgs.append(f"Tren: {self._alert_upper:,.2f}")
            except ValueError:
                messagebox.showerror("Loi", "Nguong tren khong hop le!")
                return
        if lower_txt:
            try:
                self._alert_lower = float(lower_txt.replace(",", ""))
                msgs.append(f"Duoi: {self._alert_lower:,.2f}")
            except ValueError:
                messagebox.showerror("Loi", "Nguong duoi khong hop le!")
                return
        if msgs:
            self.lbl_alert_status.config(text=" | ".join(msgs), foreground="blue")
            self._log(f"Dat nguong: {' | '.join(msgs)}")
        else:
            self.lbl_alert_status.config(text="Chua dat", foreground="gray")

    # --- Scan logic ---

    def _do_scan(self):
        if not self._tracking_symbol:
            return
        symbol = self._tracking_symbol
        self._log(f"Quet du lieu {symbol}...")

        def worker():
            quote = fetch_realtime_quote(symbol)
            hist = fetch_historical_quotes(symbol, days=120)
            ichimoku = compute_ichimoku(hist) if hist else None
            self.root.after(0, lambda: self._update_ui(quote, ichimoku))

        threading.Thread(target=worker, daemon=True).start()
        self._scan_job = self.root.after(self.SCAN_INTERVAL_MS, self._do_scan)

    def _update_ui(self, quote, ichimoku):
        if quote is None:
            self._log("Khong lay duoc du lieu!")
            return

        symbol = quote.get("Symbol", "")
        name = quote.get("Name", "")
        price_current = quote.get("PriceCurrent", 0)
        price_change = quote.get("PriceChange", 0)
        pct_change = quote.get("PricePercentChange", 0)

        # --- Headline ---
        self.lbl_price_headline.config(text=f"{symbol}  {fmt_price(price_current)}")
        change_text = f"{price_change / 1000:+,.2f}  ({pct_change * 100:+.2f}%)"
        if price_change > 0:
            color = "#2e7d32"
        elif price_change < 0:
            color = "#c62828"
        else:
            color = "#f9a825"
        self.lbl_price_change.config(text=change_text, foreground=color)
        self.lbl_update_time.config(text=f"Cap nhat: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")

        # --- Overview ---
        self.tree_overview.delete(*self.tree_overview.get_children())
        rows = [
            ("Ten cong ty", name),
            ("San giao dich", quote.get("Exchange", "--")),
            ("Nganh (ICB)", quote.get("IndustryCode", "--")),
            ("", ""),
            ("Gia hien tai (x1000)", fmt_price(price_current)),
            ("Thay doi", f"{price_change / 1000:+,.2f}  ({pct_change * 100:+.2f}%)"),
            ("Gia tham chieu", fmt_price(quote.get("PriceBasic", 0))),
            ("Gia mo cua", fmt_price(quote.get("PriceOpen", 0))),
            ("Gia cao nhat", fmt_price(quote.get("PriceHigh", 0))),
            ("Gia thap nhat", fmt_price(quote.get("PriceLow", 0))),
            ("Gia tran", fmt_price(quote.get("PriceCeiling", 0))),
            ("Gia san", fmt_price(quote.get("PriceFloor", 0))),
            ("Gia trung binh", fmt_price(quote.get("PriceAverage", 0))),
            ("", ""),
            ("Tong khoi luong", fmt_vol(quote.get("TotalVolume", 0))),
            ("Tong gia tri (trieu)", f"{quote.get('TotalValue', 0) / 1_000_000:,.1f}"),
            ("KL mua chu dong", fmt_vol(quote.get("TotalActiveBuyVolume", 0))),
            ("KL ban chu dong", fmt_vol(quote.get("TotalActiveSellVolume", 0))),
            ("", ""),
            ("NN Mua (KL)", fmt_vol(quote.get("BuyForeignQuantity", 0))),
            ("NN Ban (KL)", fmt_vol(quote.get("SellForeignQuantity", 0))),
            ("Room NN con lai", fmt_vol(quote.get("CurrentForeignRoom", 0))),
        ]
        for label, value in rows:
            self.tree_overview.insert("", tk.END, values=(label, value))

        # --- Orders ---
        self.tree_buy.delete(*self.tree_buy.get_children())
        self.tree_sell.delete(*self.tree_sell.get_children())

        for i in range(1, 4):
            bp = quote.get(f"PriceBid{i}", 0)
            bq = quote.get(f"QuantityBid{i}", 0)
            ap = quote.get(f"PriceAsk{i}", 0)
            aq = quote.get(f"QuantityAsk{i}", 0)
            self.tree_buy.insert("", tk.END, values=(fmt_price(bp), fmt_vol(bq)))
            self.tree_sell.insert("", tk.END, values=(fmt_price(ap), fmt_vol(aq)))

        active_buy = quote.get("TotalActiveBuyVolume", 0)
        active_sell = quote.get("TotalActiveSellVolume", 0)
        total_vol = quote.get("TotalVolume", 0)
        total_val = quote.get("TotalValue", 0)

        self.lbl_buy_summary.config(text=f"KL Mua chu dong: {fmt_vol(active_buy)}")
        self.lbl_sell_summary.config(text=f"KL Ban chu dong: {fmt_vol(active_sell)}")
        self.lbl_total_vol.config(text=f"Tong KL: {fmt_vol(total_vol)}")
        self.lbl_total_val.config(text=f"Tong GT: {total_val / 1_000_000_000:,.2f} ty")

        # --- Ichimoku ---
        self.tree_ichi.delete(*self.tree_ichi.get_children())
        self.txt_signals.config(state=tk.NORMAL)
        self.txt_signals.delete("1.0", tk.END)

        if ichimoku:
            ichi_rows = [
                ("Tenkan-sen (Conversion 9)", fmt_price(ichimoku["tenkan"])),
                ("Kijun-sen (Base 26)", fmt_price(ichimoku["kijun"])),
                ("Senkou Span A (tuong lai)", fmt_price(ichimoku["senkou_a"])),
                ("Senkou Span B (tuong lai)", fmt_price(ichimoku["senkou_b"])),
                ("Senkou A hien tai (Kumo)", fmt_price(ichimoku["senkou_a_cur"])),
                ("Senkou B hien tai (Kumo)", fmt_price(ichimoku["senkou_b_cur"])),
                ("Chikou Span (Lagging)", fmt_price(ichimoku["chikou"])),
            ]
            for label, value in ichi_rows:
                self.tree_ichi.insert("", tk.END, values=(label, value))

            self.txt_signals.insert(tk.END, f"{'=' * 50}\n")
            self.txt_signals.insert(tk.END, f"  XU HUONG HIEN TAI: {ichimoku['trend']}\n")
            self.txt_signals.insert(tk.END, f"{'=' * 50}\n\n")
            for sig in ichimoku["signals"]:
                self.txt_signals.insert(tk.END, f"  >> {sig}\n")
            self.txt_signals.insert(tk.END, f"\n{'=' * 50}\n")
            self.txt_signals.insert(tk.END, f"  {ichimoku['prediction']}\n")
            self.txt_signals.insert(tk.END, f"{'=' * 50}\n")
        else:
            self.txt_signals.insert(tk.END, "Khong du du lieu lich su de tinh Ichimoku (can >= 52 phien).\n")

        self.txt_signals.config(state=tk.DISABLED)

        # --- Alerts ---
        self._check_alerts(price_current)

        self._log(f"OK: {symbol} = {fmt_price(price_current)}")

    def _check_alerts(self, price_raw):
        price_k = price_raw / 1000  # x1000 VND

        if self._alert_upper and not self._alerted_upper:
            if price_k >= self._alert_upper:
                self._alerted_upper = True
                msg = f"GIA CHAM NGUONG TREN!\n{self._tracking_symbol}: {price_k:,.2f} >= {self._alert_upper:,.2f}"
                self._log(f"CANH BAO: {msg}")
                _play_alert()
                messagebox.showwarning("Canh bao nguong gia", msg)

        if self._alert_lower and not self._alerted_lower:
            if price_k <= self._alert_lower:
                self._alerted_lower = True
                msg = f"GIA CHAM NGUONG DUOI!\n{self._tracking_symbol}: {price_k:,.2f} <= {self._alert_lower:,.2f}"
                self._log(f"CANH BAO: {msg}")
                _play_alert()
                messagebox.showwarning("Canh bao nguong gia", msg)


# ============================================================
# MAIN
# ============================================================

def main():
    root = tk.Tk()
    StockTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
