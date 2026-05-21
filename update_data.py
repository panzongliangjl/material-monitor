#!/usr/bin/env python3
"""
采购原材料价格监控平台 - 数据更新脚本

功能：从生意社（100ppi.com）获取最新基准价，更新 data.json
数据源：https://m1.100ppi.com/Rawmex/{code}
"""

import json
import sys
from datetime import datetime

# 生意社品种代码映射
SHSL_CODES = {
    "alum": 513,     # 铝
    "gold": 2061,    # 黄金
    "silver": 2059,  # 白银
    "copper": 524,   # 铜
    "tin": 1181,     # 锡
    "nickel": 785,   # 镍
    "pndOx": 10294,  # 氧化镨钕
    "pnd": 1635,     # 镨钕金属
    "dyfe": 1639,    # 镝铁合金
    "paper": 584,    # 瓦楞原纸
    "li": 10380,     # 碳酸锂
}

# 品种单位
UNITS = {
    "gold": "元/克",
    "silver": "元/千克",
    "paper": "元/吨",
    "default": "元/吨",
}

def load_data():
    """加载现有数据"""
    with open('data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    """保存数据"""
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_timestamp(data):
    """更新时间戳"""
    data['meta']['updateDate'] = datetime.now().strftime('%Y-%m-%d')
    return data

def print_summary(data):
    """打印更新摘要"""
    print(f"\n{'='*60}")
    print(f"  数据更新完成 - {data['meta']['updateDate']}")
    print(f"{'='*60}")
    print(f"\n{'品种':<18} {'当前价格':>12} {'单位':<10} {'52周区间'}")
    print(f"{'-'*60}")
    for m in data['materials']:
        price = f"{m['price']:,}"
        unit = m['unit']
        range_str = f"{m['low52w']:,} - {m['high52w']:,}"
        print(f"  {m['name']:<16} {price:>12} {unit:<10} {range_str}")
    print()

def main():
    """
    主流程：加载 → 尝试更新 → 保存
    """
    print("📊 采购原材料价格监控 - 数据更新工具")
    print(f"   运行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   数据来源：生意社基准价 (100ppi.com)\n")
    
    # 加载现有数据
    data = load_data()
    
    # 尝试更新价格（当前版本：更新时间戳，价格保持手动更新）
    # 未来实现：通过 API/爬虫获取生意社实时基准价
    print("ℹ️  自动化数据抓取功能开发中...")
    print("   当前版本：手动编辑 data.json 或通过 neodata API 辅助获取\n")
    print("   数据源页面列表：")
    for name, code in SHSL_CODES.items():
        url = f"https://m1.100ppi.com/Rawmex/{code}"
        print(f"     {name:<10} → {url}")
    
    # 更新时间戳
    data = update_timestamp(data)
    
    # 保存
    save_data(data)
    print_summary(data)
    
    print("✅ data.json 已更新！")
    print("📝 下一步：git add data.json && git commit && git push")

if __name__ == '__main__':
    main()
