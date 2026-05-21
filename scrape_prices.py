#!/usr/bin/env python3
"""
生意社价格自动抓取脚本
从 100ppi.com 抓取基准价、52周统计数据，更新 data.json

运行方式:
  python3 scrape_prices.py            # 抓取并更新 data.json
  python3 scrape_prices.py --dry-run  # 仅打印结果，不写入文件
"""

import json
import re
import sys
import time
from datetime import date
from urllib.parse import urljoin

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip3 install cloudscraper beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://www.100ppi.com"
DATA_FILE = "data.json"

# 物料 → 生意社 vane 页面映射 (统一使用 vane，rawmex 无新闻链接)
MATERIAL_SOURCES = {
    "alum":   {"id": 482,  "name_zh": "铝"},
    "gold":   {"id": 551,  "name_zh": "黄金"},
    "silver": {"id": 544,  "name_zh": "白银"},
    "copper": {"id": 524,  "name_zh": "铜"},
    "tin":    {"id": 492,  "name_zh": "锡"},
    "nickel": {"id": 432,  "name_zh": "镍"},
    "pnd":    {"id": 310,  "name_zh": "镨钕合金"},
    "pndOx":  {"id": 711,  "name_zh": "镨钕氧化物"},
    "li":     {"id": 1162, "name_zh": "碳酸锂"},
    "paper":  {"id": 1250, "name_zh": "瓦楞原纸"},
}

# 共享 cloudscraper 实例（复用连接池和 cookie）
_scraper = None

def get_scraper():
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "darwin", "mobile": False},
            delay=10,
        )
    return _scraper


def fetch_page(url, retries=3):
    """获取页面 HTML（自动绕过 JS 挑战）"""
    scraper = get_scraper()
    for attempt in range(retries):
        try:
            resp = scraper.get(url, timeout=30)
            resp.encoding = "utf-8"
            if resp.status_code == 200 and len(resp.text) > 1000:
                return resp.text
            if resp.status_code == 200:
                print(f"  ⚠️  页面内容过短 ({len(resp.text)} 字符)，可能被拦截")
            else:
                print(f"  HTTP {resp.status_code}, attempt {attempt+1}")
        except Exception as e:
            print(f"  请求异常: {e}, attempt {attempt+1}")
        time.sleep(3 * (attempt + 1))
    return None


def find_benchmark_link(html, name_zh):
    """从 vane 页面找到最新基准价新闻链接"""
    soup = BeautifulSoup(html, "html.parser")

    # 搜索所有带「基准价为」文本的 <a> 标签
    for a in soup.find_all("a", href=True):
        text = a.text.strip()
        if "基准价为" in text and "生意社" in text:
            href = a["href"]
            if href.startswith("/news/"):
                return urljoin(BASE_URL, href), text

    return None, None


def parse_price_from_link(text):
    """从「5月21日生意社铝基准价为24210.00元/吨」提取价格和单位"""
    m = re.search(r"基准价为\s*([\d,]+\.?\d*)\s*元/([^\s<,，]+)", text)
    if m:
        price = float(m.group(1).replace(",", ""))
        unit = f"元/{m.group(2)}"
        return price, unit
    return None, None


def parse_news_detail(html):
    """从新闻详情页解析完整价格数据（使用 BeautifulSoup get_text）"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    data = {
        "price": None,
        "unit": None,
        "date": None,
        "daily_change_pct": None,
        "monthly_change_pct": None,
        "low52w": None,
        "high52w": None,
    }

    # 1. 日期
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        data["date"] = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"

    # 2. 基准价与单位
    m = re.search(r"基准价为\s*([\d,]+\.?\d*)\s*元/([^\s\n<,，]+)", text)
    if m:
        data["price"] = float(m.group(1).replace(",", ""))
        data["unit"] = f"元/{m.group(2)}"

    # 3. 日涨幅（「日涨幅 0.00%」或「日涨幅 -0.76%」）
    m = re.search(r"日涨幅\s*\n*\s*([\d.-]+)\s*%", text)
    if m:
        data["daily_change_pct"] = float(m.group(1))

    # 4. 月涨幅（「与本月初...相比，上涨/下降了 X.XX%」）
    m = re.search(r"(?:与本月初|较月初).*?(?:上涨|下降|下跌)了?\s*([\d.]+)\s*%", text)
    if m:
        pct = float(m.group(1))
        if re.search(r"(?:与本月初|较月初).*?(?:下降|下跌)", text):
            pct = -pct
        data["monthly_change_pct"] = pct

    # 5. 52周统计（从年度统计表格）
    # 格式：最小值\n\n\nXXXXX\n\n\n最大值\n\n\nXXXXX\n...
    for label, key in [("最小值", "low52w"), ("最大值", "high52w")]:
        m = re.search(rf"{label}\s*\n+\s*([\d,]+\.?\d*)", text)
        if m:
            data[key] = float(m.group(1).replace(",", ""))

    return data


def fetch_material(material_id, source):
    """抓取单个物料的价格数据"""
    name_zh = source["name_zh"]
    vane_url = f"{BASE_URL}/vane/detail-{source['id']}.html"

    # Step 1: vane 页面 → 找新闻链接
    html = fetch_page(vane_url)
    if not html:
        return None

    news_url, link_text = find_benchmark_link(html, name_zh)
    if not news_url:
        return None

    # 从链接文本快速提取价格
    link_price, link_unit = parse_price_from_link(link_text)

    # Step 2: 新闻详情页 → 完整数据
    news_html = fetch_page(news_url)
    if not news_html:
        # 至少有链接中的价格
        if link_price:
            return {"price": link_price, "unit": link_unit}
        return None

    data = parse_news_detail(news_html)

    # 新闻页没解析到价格则用链接文本的
    if data["price"] is None and link_price is not None:
        data["price"] = link_price
        data["unit"] = link_unit

    return data


def generate_suggestion(price, low52w, high52w, monthly_pct):
    """根据价格在52周区间的位置和月趋势生成采购建议"""
    if None in (price, low52w, high52w):
        return "观望", "flat"
    rng = high52w - low52w
    if rng <= 0:
        return "观望", "flat"
    pos = (price - low52w) / rng

    if monthly_pct is not None and monthly_pct > 3:
        if pos > 0.7: return "高位观望", "down"
        if pos < 0.3: return "择机买入", "up"
    if monthly_pct is not None and monthly_pct < -3:
        if pos < 0.3: return "底部关注", "up"
        if pos > 0.7: return "暂缓采购", "down"

    if pos > 0.85:   return "暂缓采购", "down"
    if pos > 0.7:    return "高位观望", "flat"
    if pos < 0.15:   return "择机买入", "up"
    if pos < 0.3:    return "底部关注", "up"
    return "观望", "flat"


def update_data_json(results):
    """更新 data.json"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    updated = 0
    today_str = date.today().isoformat()

    for mat in config["materials"]:
        mid = mat["id"]
        if mid not in results or not results[mid]:
            continue
        r = results[mid]

        if r.get("price") is not None:
            new_price = int(round(r["price"]))
            print(f"  {mat['name']}: {mat['price']} → {new_price} {r.get('unit', mat['unit'])}")
            mat["price"] = new_price
        else:
            print(f"  {mat['name']}: 保持 {mat['price']}")

        if r.get("unit"):
            mat["unit"] = r["unit"]
        if r.get("low52w") is not None:
            mat["low52w"] = int(round(r["low52w"]))
        if r.get("high52w") is not None:
            mat["high52w"] = int(round(r["high52w"]))

        mat["sourceName"] = "生意社"
        mat["sourceUrl"] = "https://www.100ppi.com"

        sug, sug_type = generate_suggestion(
            mat["price"], mat["low52w"], mat["high52w"],
            r.get("monthly_change_pct")
        )
        mat["suggestion"] = sug
        mat["suggestionType"] = sug_type

        if r.get("monthly_change_pct") is not None:
            mat["chartTrend"] = round(r["monthly_change_pct"] / 100, 4)

        updated += 1

    config["meta"]["updateDate"] = today_str
    return config, updated


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"{'='*60}")
    print(f"生意社价格自动抓取  {date.today().isoformat()}")
    print(f"{'='*60}\n")

    results = {}
    for mid, src in MATERIAL_SOURCES.items():
        name = src["name_zh"]
        print(f"[{mid}] {name} ", end="", flush=True)
        try:
            data = fetch_material(mid, src)
            results[mid] = data
            if data and data.get("price"):
                print(f"✅ {data['price']} {data.get('unit','')}", end="")
                if data.get("daily_change_pct") is not None:
                    print(f"  日涨{data['daily_change_pct']:+.2f}%", end="")
                print()
            else:
                print("⚠️  未获取到")
        except Exception as e:
            print(f"❌ {e}")
            results[mid] = None
        time.sleep(2)

    if dry_run:
        print(f"\n{'='*60}")
        print("🔍 Dry-run — 对比当前 data.json vs 抓取结果:")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        for mat in config["materials"]:
            mid = mat["id"]
            if mid in results and results[mid] and results[mid].get("price"):
                old = mat["price"]
                new = int(round(results[mid]["price"]))
                if old != new:
                    print(f"  {mat['name']}: {old} → ⚡ {new} ({new-old:+d})")
        print(f"\n未写入文件。去掉 --dry-run 参数以实际更新。")
    else:
        print(f"\n{'='*60}")
        print("写入 data.json ...")
        config, count = update_data_json(results)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 完成！更新 {count}/{len(MATERIAL_SOURCES)} 个品种")
        print(f"数据日期: {config['meta']['updateDate']}")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
