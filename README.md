# 采购原材料价格监控平台

实时监控 20+ 种大宗商品原材料价格走势，支持采购决策分析。

## 📊 功能特性

- **总览仪表盘**：全部品种当前价格 + 52 周高低区间 + 采购建议 + 数据来源链接
- **分类详情**：铝系 / 贵金属 / 基础有色 / 电池材料 / 稀土包材，含走势图和供需分析
- **价格预判**：采购策略矩阵（价格上涨概率 × 供给紧张度）
- **鼠标悬停**：走势图上任意位置悬停显示当日价格
- **一键刷新**：点击「刷新数据」按钮重新加载最新数据

## 🔗 在线访问

部署后通过 GitHub Pages 访问：
```
https://panzongliangjl.github.io/material-monitor/
```

## 📁 文件结构

```
material-monitor/
├── index.html      # 主页面（UI + 图表逻辑）
├── data.json       # 价格数据源（唯一数据入口）
├── update_data.py  # 数据更新脚本
└── README.md       # 本文件
```

## 🔄 更新数据

### 方式一：手动编辑

直接编辑 `data.json`，修改对应品种的 `price`、`low52w`、`high52w` 等字段，然后提交推送。

### 方式二：运行更新脚本（推荐）

```bash
# 安装依赖
pip install requests beautifulsoup4

# 运行更新（从生意社获取最新基准价）
python update_data.py

# 提交并推送
git add data.json
git commit -m "update: $(date +%Y-%m-%d) 价格数据更新"
git push
```

### 更新频率建议

- **核心品种**（铝/铜/镍/锡/金银）：每日更新
- **稀土品种**：每周 2-3 次
- **电池材料**：每周 1-2 次
- **特种材料**（参考价）：按需更新

## 📡 数据来源

| 数据源 | 覆盖品种 | 链接 |
|--------|----------|------|
| 生意社基准价 | 铝/金银/铜/锡/镍/稀土/碳酸锂/瓦楞纸 | [100ppi.com](https://www.100ppi.com) |
| 南海有色网 | ADC12/A356 | [nanhai123.com](https://www.nanhai123.com) |
| 有色宝长江 | A356/铜棒/镍 | [ccmn.cn](https://www.ccmn.cn) |
| 上海金属网 | 紫铜棒 | [shmet.com](https://www.shmet.com) |
| 上海有色网 | 镨钕/铽/VC/NCM/电解液/石墨 | [smm.cn](https://www.smm.cn) |

⚠️ 标注「参考价」的品种为非生意社基准价覆盖品种，价格仅供参考。

## 🚀 部署到 GitHub Pages

1. Fork 或创建仓库：`material-monitor`
2. 推送代码：
   ```bash
   git init
   git add .
   git commit -m "init: 采购原材料价格监控平台"
   git remote add origin git@github.com:panzongliangjl/material-monitor.git
   git push -u origin main
   ```
3. 在 GitHub 仓库 Settings → Pages → Source 选择 `main` 分支
4. 等待几分钟后通过 `https://panzongliangjl.github.io/material-monitor/` 访问

## ⚠️ 免责声明

本平台数据仅供采购参考，不构成投资建议。价格存在一定延迟，请以各数据源平台官方数据为准。
