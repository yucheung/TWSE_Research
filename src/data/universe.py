"""Taiwan Stock Universe definition and liquidity filters."""
from typing import List, Dict

BENCHMARK_SYMBOL = "0050.TW"

# Representative liquid universe across major TWSE/TPEx sectors (approx 120 liquid leaders)
UNIVERSE_SYMBOLS: List[Dict[str, str]] = [
    # Benchmark
    {"symbol": "0050.TW", "name": "元大台灣50", "sector": "ETF"},

    # Semiconductors & IC Design
    {"symbol": "2330.TW", "name": "台積電", "sector": "半導體"},
    {"symbol": "2454.TW", "name": "聯發科", "sector": "IC設計"},
    {"symbol": "2303.TW", "name": "聯電", "sector": "半導體"},
    {"symbol": "3034.TW", "name": "聯詠", "sector": "IC設計"},
    {"symbol": "3443.TW", "name": "創意", "sector": "IC設計/IP"},
    {"symbol": "3661.TW", "name": "世芯-KY", "sector": "IC設計/ASIC"},
    {"symbol": "2379.TW", "name": "瑞昱", "sector": "IC設計"},
    {"symbol": "6415.TW", "name": "矽力*-KY", "sector": "IC設計"},
    {"symbol": "3035.TW", "name": "智原", "sector": "IC設計/IP"},
    {"symbol": "3711.TW", "name": "日月光投控", "sector": "半導體封測"},
    {"symbol": "2449.TW", "name": "京元電子", "sector": "半導體封測"},
    {"symbol": "6239.TW", "name": "力成", "sector": "半導體封測"},
    {"symbol": "2408.TW", "name": "南亞科", "sector": "記憶體"},
    {"symbol": "8299.TWO", "name": "群聯", "sector": "記憶體/IC設計"},
    {"symbol": "6488.TWO", "name": "環球晶", "sector": "矽晶圓"},
    {"symbol": "3529.TWO", "name": "力旺", "sector": "IC設計/IP"},
    {"symbol": "5347.TWO", "name": "世界", "sector": "晶圓代工"},

    # AI Server, Computers & Electronics Assembly
    {"symbol": "2317.TW", "name": "鴻海", "sector": "電子代工/EMS"},
    {"symbol": "2382.TW", "name": "廣達", "sector": "AI伺服器/代工"},
    {"symbol": "3231.TW", "name": "緯創", "sector": "AI伺服器/代工"},
    {"symbol": "6669.TW", "name": "緯穎", "sector": "雲端伺服器"},
    {"symbol": "2356.TW", "name": "英業達", "sector": "AI伺服器/代工"},
    {"symbol": "2376.TW", "name": "技嘉", "sector": "伺服器/板卡"},
    {"symbol": "2377.TW", "name": "微星", "sector": "電競/板卡"},
    {"symbol": "4938.TW", "name": "和碩", "sector": "電子代工"},
    {"symbol": "2357.TW", "name": "華碩", "sector": "品牌PC/板卡"},
    {"symbol": "2395.TW", "name": "研華", "sector": "工業電腦"},
    {"symbol": "2301.TW", "name": "光寶科", "sector": "電源供應/伺服器"},

    # Thermal, Components & Connectors
    {"symbol": "3017.TW", "name": "奇鋐", "sector": "散熱模組"},
    {"symbol": "3324.TWO", "name": "雙鴻", "sector": "散熱模組"},
    {"symbol": "3653.TWO", "name": "健策", "sector": "散熱導線架"},
    {"symbol": "2308.TW", "name": "台達電", "sector": "電源/散熱/儲能"},
    {"symbol": "2327.TW", "name": "國巨", "sector": "被動元件"},
    {"symbol": "2492.TW", "name": "華新科", "sector": "被動元件"},
    {"symbol": "2458.TW", "name": "義隆", "sector": "觸控IC"},
    {"symbol": "3533.TW", "name": "嘉澤", "sector": "伺服器連接器"},

    # Optical & Camera
    {"symbol": "3008.TW", "name": "大立光", "sector": "光學鏡頭"},
    {"symbol": "3406.TW", "name": "玉晶光", "sector": "光學鏡頭"},
    {"symbol": "2474.TW", "name": "可成", "sector": "機殼/精密製造"},

    # PCB & CCL (Carrier Board / Copper Clad Laminate)
    {"symbol": "3037.TW", "name": "欣興", "sector": "ABF載板/PCB"},
    {"symbol": "8046.TW", "name": "南電", "sector": "ABF載板"},
    {"symbol": "3189.TW", "name": "景碩", "sector": "載板/PCB"},
    {"symbol": "2368.TW", "name": "金像電", "sector": "伺服器PCB"},
    {"symbol": "6274.TWO", "name": "台燿", "sector": "銅箔基板(CCL)"},
    {"symbol": "2383.TW", "name": "台光電", "sector": "銅箔基板(CCL)"},
    {"symbol": "6213.TWO", "name": "聯茂", "sector": "銅箔基板(CCL)"},

    # Networking & Communications
    {"symbol": "2345.TW", "name": "智邦", "sector": "網通/交換器"},
    {"symbol": "5388.TWO", "name": "中磊", "sector": "網通設備"},
    {"symbol": "4906.TW", "name": "正文", "sector": "網通設備"},
    {"symbol": "3596.TW", "name": "智易", "sector": "網通設備"},

    # Heavy Electrical & Green Energy
    {"symbol": "1513.TW", "name": "中興電", "sector": "重電設備/氫能"},
    {"symbol": "1519.TW", "name": "華城", "sector": "變壓器/重電外銷"},
    {"symbol": "1504.TW", "name": "東元", "sector": "重電馬達"},
    {"symbol": "1514.TW", "name": "亞力", "sector": "變壓器/配電盤"},
    {"symbol": "6806.TW", "name": "森崴能源", "sector": "綠能電廠"},
    {"symbol": "9958.TW", "name": "世紀鋼", "sector": "離岸風電水下基礎"},

    # Shipping & Transportation
    {"symbol": "2603.TW", "name": "長榮", "sector": "貨櫃航運"},
    {"symbol": "2609.TW", "name": "陽明", "sector": "貨櫃航運"},
    {"symbol": "2615.TW", "name": "萬海", "sector": "貨櫃航運"},
    {"symbol": "2618.TW", "name": "長榮航", "sector": "航空客貨運"},
    {"symbol": "2610.TW", "name": "華航", "sector": "航空客貨運"},
    {"symbol": "2605.TW", "name": "新興", "sector": "散裝航運"},

    # Automotive & EV
    {"symbol": "2201.TW", "name": "裕隆", "sector": "汽車製造/EV"},
    {"symbol": "2207.TW", "name": "和泰車", "sector": "汽車代理與銷售"},
    {"symbol": "1319.TW", "name": "東陽", "sector": "汽車AM塑膠件"},
    {"symbol": "6271.TWO", "name": "同欣電", "sector": "CIS車用封測"},

    # Traditional Industries: Steel & Petrochemical
    {"symbol": "2002.TW", "name": "中鋼", "sector": "鋼鐵龍頭"},
    {"symbol": "2014.TW", "name": "中鴻", "sector": "鋼鐵板材"},
    {"symbol": "2027.TW", "name": "大成鋼", "sector": "不銹鋼/鋁捲板"},
    {"symbol": "1301.TW", "name": "台塑", "sector": "塑化龍頭"},
    {"symbol": "1303.TW", "name": "南亞", "sector": "塑膠/電子材料"},
    {"symbol": "1326.TW", "name": "台化", "sector": "石化纖維"},
    {"symbol": "6505.TW", "name": "台塑化", "sector": "煉油石化"},
    {"symbol": "1101.TW", "name": "台泥", "sector": "水泥/儲能轉換"},
    {"symbol": "1102.TW", "name": "亞泥", "sector": "水泥製造"},

    # Financial Sector
    {"symbol": "2881.TW", "name": "富邦金", "sector": "金控龍頭"},
    {"symbol": "2882.TW", "name": "國泰金", "sector": "金控壽險"},
    {"symbol": "2891.TW", "name": "中信金", "sector": "金控銀行"},
    {"symbol": "2886.TW", "name": "兆豐金", "sector": "公股官股金控"},
    {"symbol": "2884.TW", "name": "玉山金", "sector": "民營消金金控"},
    {"symbol": "2892.TW", "name": "第一金", "sector": "公股銀行金控"},
    {"symbol": "5880.TW", "name": "合庫金", "sector": "公股銀行金控"},
    {"symbol": "2880.TW", "name": "華南金", "sector": "公股銀行金控"},
    {"symbol": "2885.TW", "name": "元大金", "sector": "證券金控龍頭"},
    {"symbol": "2887.TW", "name": "台新金", "sector": "民營金控"},
    {"symbol": "2890.TW", "name": "永豐金", "sector": "民營金控"},

    # Healthcare & Biotech
    {"symbol": "6446.TWO", "name": "藥華藥", "sector": "生技新藥"},
    {"symbol": "6472.TWO", "name": "保瑞", "sector": "CDMO製藥"},
    {"symbol": "1795.TW", "name": "美時", "sector": "學名藥外銷"},

    # Retail & Consumer
    {"symbol": "2912.TW", "name": "統一超", "sector": "零售超商"},
    {"symbol": "1216.TW", "name": "統一", "sector": "食品龍頭"},
    {"symbol": "9910.TW", "name": "豐泰", "sector": "運動鞋代工"},
    {"symbol": "9921.TW", "name": "巨大", "sector": "自行車品牌"},
]


def get_twse_universe() -> List[Dict[str, str]]:
    """Return the defined liquid TWSE universe."""
    return UNIVERSE_SYMBOLS


def build_yearly_membership(
    prices_dict: "dict",
    top_n: int = 80,
    lookback_days: int = 60,
    exclude: "set | None" = None,
) -> "dict[int, list]":
    """Rule-based yearly universe reconstitution (no look-ahead).

    For each calendar year Y in the data range, rank all pool symbols by
    mean daily Turnover over the last `lookback_days` sessions on or before
    Dec 31 of year Y-1, and keep the top_n. The first year with data keeps
    the full pool (warm-up, no ranking history available).

    Returns {year: [symbols]} — membership valid for the whole year.
    """
    import pandas as pd

    exclude = set(exclude or [])
    # Collect all session dates across pool (exclude benchmark later via `exclude`)
    all_dates = set()
    for sym, df in prices_dict.items():
        if sym in exclude:
            continue
        idx = df.index.tz_localize(None) if hasattr(df.index, "tz") and df.index.tz is not None else df.index
        all_dates.update(idx)
    all_dates = sorted(all_dates)
    if not all_dates:
        return {}
    years = sorted({d.year for d in all_dates})
    first_year = years[0]
    membership = {first_year: sorted([s for s in prices_dict if s not in exclude])}

    for year in years[1:]:
        cutoff = pd.Timestamp(year - 1, 12, 31)
        scores = []
        for sym, df in prices_dict.items():
            if sym in exclude:
                continue
            idx = df.index.tz_localize(None) if hasattr(df.index, "tz") and df.index.tz is not None else df.index
            hist = df[idx <= cutoff].tail(lookback_days)
            if hist.empty or "Turnover" not in hist.columns:
                continue
            scores.append((sym, float(hist["Turnover"].mean())))
        scores.sort(key=lambda x: x[1], reverse=True)
        membership[year] = [s for s, _ in scores[:top_n]]
    return membership
