"""차트 이미지 생성 모듈 — 기술적 분석 라인 포함"""
import os
import numpy as np
import mplfinance as mpf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyArrowPatch
from datetime import datetime
import config

# Windows 한글 폰트 설정
_KR_FONT = None
_malgun_path = "C:/Windows/Fonts/malgun.ttf"
if os.path.exists(_malgun_path):
    fm.fontManager.addfont(_malgun_path)
    _KR_FONT = "Malgun Gothic"
    plt.rcParams["font.family"] = _KR_FONT
    plt.rcParams["axes.unicode_minus"] = False


def _find_support_resistance(highs, lows, closes, n_levels=3):
    """피봇 포인트 기반 지지/저항선 계산"""
    levels = []
    for i in range(2, len(closes) - 2):
        # 저항: 고가가 양쪽보다 높은 지점
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            levels.append(("resistance", i, highs[i]))
        # 지지: 저가가 양쪽보다 낮은 지점
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            levels.append(("support", i, lows[i]))

    # 비슷한 가격대 병합 (2% 이내)
    merged = []
    used = set()
    for i, (typ, idx, price) in enumerate(levels):
        if i in used:
            continue
        cluster = [price]
        for j, (_, _, p2) in enumerate(levels):
            if j != i and j not in used and abs(p2 - price) / price < 0.02:
                cluster.append(p2)
                used.add(j)
        merged.append((typ, idx, np.mean(cluster), len(cluster)))
        used.add(i)

    # 터치 횟수 + 최근성 기준 정렬
    merged.sort(key=lambda x: x[3], reverse=True)
    return merged[:n_levels * 2]


def _calc_trendline(indices, values, direction="up"):
    """선형 회귀 기반 추세선 계산"""
    if len(indices) < 2:
        return None, None
    x = np.array(indices, dtype=float)
    y = np.array(values, dtype=float)
    coeffs = np.polyfit(x, y, 1)
    return coeffs[0], coeffs[1]  # slope, intercept


def _find_trendline_points(highs, lows, closes, window=20):
    """상승/하락 추세선의 접점 찾기"""
    n = len(closes)
    if n < window:
        return [], []

    recent = slice(max(0, n - window), n)

    # 상승 추세선: 최근 저가들의 저점 연결
    low_vals = lows[recent]
    low_indices = list(range(recent.start, recent.stop))
    # 저점 2~3개 찾기
    low_pivots = []
    for i in range(1, len(low_vals) - 1):
        if low_vals[i] <= low_vals[i-1] and low_vals[i] <= low_vals[i+1]:
            low_pivots.append((low_indices[i], low_vals[i]))
    if len(low_pivots) < 2:
        low_pivots = [(low_indices[0], low_vals[0]), (low_indices[-1], low_vals[-1])]

    # 하락 추세선: 최근 고가들의 고점 연결
    high_vals = highs[recent]
    high_indices = list(range(recent.start, recent.stop))
    high_pivots = []
    for i in range(1, len(high_vals) - 1):
        if high_vals[i] >= high_vals[i-1] and high_vals[i] >= high_vals[i+1]:
            high_pivots.append((high_indices[i], high_vals[i]))
    if len(high_pivots) < 2:
        high_pivots = [(high_indices[0], high_vals[0]), (high_indices[-1], high_vals[-1])]

    return low_pivots, high_pivots


def generate_analysis_chart(df, ticker_name, timeframe="일봉", save_dir=None):
    """기술적 분석 라인이 포함된 고급 차트"""
    if df.empty or len(df) < 10:
        return None

    if save_dir is None:
        save_dir = os.path.join(config.OUTPUT_DIR, "charts")
    os.makedirs(save_dir, exist_ok=True)

    # 컬럼 변환
    df_c = df.rename(columns={
        "시가": "Open", "고가": "High", "저가": "Low",
        "종가": "Close", "거래량": "Volume"
    })
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df_c.columns:
            return None
    df_c = df_c[required].copy()

    closes = df_c["Close"].values
    highs = df_c["High"].values
    lows = df_c["Low"].values
    n = len(df_c)

    # ===== 추가 플롯 (addplot) =====
    addplots = []

    # 1) 볼린저밴드 (20일)
    if n >= 20:
        ma20 = df_c["Close"].rolling(20).mean()
        std20 = df_c["Close"].rolling(20).std()
        bb_upper = ma20 + 2 * std20
        bb_lower = ma20 - 2 * std20
        addplots.append(mpf.make_addplot(bb_upper, color="#ff9800", linestyle="--", width=0.8, label="BB Upper"))
        addplots.append(mpf.make_addplot(bb_lower, color="#ff9800", linestyle="--", width=0.8, label="BB Lower"))
        # 볼린저밴드 채우기용 — fill_between은 나중에 ax에서
        addplots.append(mpf.make_addplot(ma20, color="#ff9800", width=1.0, label="BB Mid"))

    # 2) RSI (별도 패널)
    if n >= 15:
        delta = df_c["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        addplots.append(mpf.make_addplot(rsi, panel=2, color="#e040fb", ylabel="RSI", width=1.2))
        # RSI 70/30 기준선
        rsi_70 = [70] * n
        rsi_30 = [30] * n
        addplots.append(mpf.make_addplot(rsi_70, panel=2, color="red", linestyle="--", width=0.5))
        addplots.append(mpf.make_addplot(rsi_30, panel=2, color="green", linestyle="--", width=0.5))

    # 3) MACD (별도 패널)
    if n >= 26:
        ema12 = df_c["Close"].ewm(span=12).mean()
        ema26 = df_c["Close"].ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_hist = macd_line - signal_line
        addplots.append(mpf.make_addplot(macd_line, panel=3, color="#2196f3", ylabel="MACD", width=1.0))
        addplots.append(mpf.make_addplot(signal_line, panel=3, color="#ff5722", width=1.0))
        hist_colors = ["#4caf50" if v >= 0 else "#f44336" for v in macd_hist.fillna(0)]
        addplots.append(mpf.make_addplot(macd_hist, panel=3, type="bar", color=hist_colors, width=0.7))

    # 스타일
    mc = mpf.make_marketcolors(up="r", down="b", inherit=True)
    rc_kwargs = {}
    if _KR_FONT:
        rc_kwargs["rc"] = {"font.family": _KR_FONT, "axes.unicode_minus": False}
    style = mpf.make_mpf_style(
        marketcolors=mc, gridstyle="-", gridcolor="#e8e8e8",
        facecolor="white", edgecolor="white", **rc_kwargs
    )

    # 이동평균
    mav = (5, 20, 60)
    if n < 60:
        mav = tuple(m for m in mav if m <= n)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ticker_name}_{timeframe}_분석_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)

    # 패널 비율
    panel_ratios = [4, 1]
    if n >= 15:
        panel_ratios.append(1)  # RSI
    if n >= 26:
        panel_ratios.append(1)  # MACD

    try:
        fig, axes = mpf.plot(
            df_c,
            type="candle",
            style=style,
            title=f"\n{ticker_name}  {timeframe} 기술적 분석",
            ylabel="",
            ylabel_lower="거래량",
            volume=True,
            mav=mav if mav else None,
            figsize=(16, 12),
            addplot=addplots if addplots else None,
            returnfig=True,
            panel_ratios=panel_ratios,
        )

        ax_price = axes[0]

        # ===== 지지/저항선 그리기 =====
        sr_levels = _find_support_resistance(highs, lows, closes)
        for typ, idx, price, count in sr_levels:
            color = "#e53935" if typ == "resistance" else "#43a047"
            ls = "--" if count <= 1 else "-"
            lw = 1.0 if count <= 1 else 1.5
            ax_price.axhline(y=price, color=color, linestyle=ls, linewidth=lw, alpha=0.6)
            label = f"저항 {int(price):,}" if typ == "resistance" else f"지지 {int(price):,}"
            ax_price.text(n - 1, price, f" {label}", fontsize=8, color=color,
                         va="bottom" if typ == "resistance" else "top", ha="left")

        # ===== 추세선 그리기 =====
        low_pivots, high_pivots = _find_trendline_points(highs, lows, closes, window=min(40, n))

        # 상승 추세선 (저점 연결)
        if len(low_pivots) >= 2:
            pts = low_pivots[:3]
            idxs = [p[0] for p in pts]
            vals = [p[1] for p in pts]
            slope, intercept = _calc_trendline(idxs, vals)
            if slope is not None:
                x_start = idxs[0]
                x_end = n - 1
                y_start = slope * x_start + intercept
                y_end = slope * x_end + intercept
                ax_price.plot([x_start, x_end], [y_start, y_end],
                            color="#1565c0", linewidth=1.5, linestyle="-", alpha=0.7)
                direction = "↗ 상승추세" if slope > 0 else "↘ 하락추세"
                ax_price.text(x_end, y_end, f" {direction}", fontsize=8, color="#1565c0", va="center")

        # 하락 추세선 (고점 연결)
        if len(high_pivots) >= 2:
            pts = high_pivots[:3]
            idxs = [p[0] for p in pts]
            vals = [p[1] for p in pts]
            slope, intercept = _calc_trendline(idxs, vals)
            if slope is not None:
                x_start = idxs[0]
                x_end = n - 1
                y_start = slope * x_start + intercept
                y_end = slope * x_end + intercept
                ax_price.plot([x_start, x_end], [y_start, y_end],
                            color="#c62828", linewidth=1.5, linestyle="-", alpha=0.7)

        # ===== 볼린저밴드 영역 채우기 =====
        if n >= 20:
            ma20_vals = df_c["Close"].rolling(20).mean().values
            std20_vals = df_c["Close"].rolling(20).std().values
            bb_up = ma20_vals + 2 * std20_vals
            bb_lo = ma20_vals - 2 * std20_vals
            x_range = range(n)
            ax_price.fill_between(x_range, bb_lo, bb_up, alpha=0.06, color="#ff9800")

        # ===== 현재가 수평선 =====
        current = closes[-1]
        ax_price.axhline(y=current, color="#333333", linestyle=":", linewidth=0.8, alpha=0.5)
        ax_price.text(0, current, f" 현재가 {int(current):,}", fontsize=8, color="#333", va="bottom")

        # ===== 범례 (이동평균) =====
        ma_labels = []
        colors_ma = ["#1f77b4", "#ff7f0e", "#2ca02c"]
        for i, m in enumerate(mav):
            if m <= n:
                ma_labels.append(f"MA{m}")
        legend_text = "  |  ".join(ma_labels + ["BB(20,2)", "지지선", "저항선", "추세선"])
        ax_price.set_title(f"{ticker_name}  {timeframe} 기술적 분석\n{legend_text}", fontsize=12, pad=10)

        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close("all")
        return filepath

    except Exception as e:
        print(f"분석 차트 생성 실패 [{ticker_name}]: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_chart(df, ticker_name, timeframe="daily", save_dir=None):
    """기본 캔들스틱 차트 (호환용)"""
    return generate_analysis_chart(df, ticker_name, timeframe, save_dir)


def generate_multi_timeframe_charts(df_daily, ticker_name, save_dir=None):
    """다중 타임프레임 분석 차트"""
    charts = {}

    path = generate_analysis_chart(df_daily, ticker_name, "일봉", save_dir)
    if path:
        charts["일봉"] = path

    if len(df_daily) >= 10:
        df_w = df_daily.rename(columns={"시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"})
        df_w = df_w[["Open", "High", "Low", "Close", "Volume"]]
        df_weekly = df_w.resample("W").agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum"
        }).dropna()
        df_weekly_kr = df_weekly.rename(columns={"Open": "시가", "High": "고가", "Low": "저가", "Close": "종가", "Volume": "거래량"})
        path = generate_analysis_chart(df_weekly_kr, ticker_name, "주봉", save_dir)
        if path:
            charts["주봉"] = path

    if len(df_daily) >= 30:
        df_m = df_daily.rename(columns={"시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"})
        df_m = df_m[["Open", "High", "Low", "Close", "Volume"]]
        df_monthly = df_m.resample("ME").agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum"
        }).dropna()
        df_monthly_kr = df_monthly.rename(columns={"Open": "시가", "High": "고가", "Low": "저가", "Close": "종가", "Volume": "거래량"})
        path = generate_analysis_chart(df_monthly_kr, ticker_name, "월봉", save_dir)
        if path:
            charts["월봉"] = path

    return charts
