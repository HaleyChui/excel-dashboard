# 🏢 Trading Terminal 戰情表設計規範

> **來源：** https://github.com/HaleyChui/open-design (design-systems/trading-terminal/)
> **風格：** Bloomberg 風格金融交易終端 — 深色、數據密集、cyan/coral 買賣訊號
> **適用場景：** 戰情表、監控儀表板、數據密集型的即時看板

---

## 1. 視覺風格

- **色調：** 深色基底（Dark-only），降低長時間觀看的眼睛疲勞
- **風格關鍵字：** 專業、數據優先、高資訊密度
- **參考產品：** Bloomberg Terminal, TradingView Pro, Refinitiv Eikon

## 2. 色彩系統

### 表面色階

| Token | Hex | 用途 |
|-------|-----|------|
| Background | `#0D0D0D` | 頁面主底色 |
| Surface | `#141414` | 卡片 / 面板 |
| Surface Hover | `#1A1A1A` | 懸停狀態 |
| Border | `#2A2A2A` | 面板分隔線 |

### 資料色階

| Token | Hex | 用途 |
|-------|-----|------|
| Primary（上漲/買入） | `#00D4AA` | 正值、買入訊號、成功 |
| Loss（下跌/賣出） | `#FF4757` | 負值、賣出訊號 |
| Warning | `#FFB800` | 警告、保證金通知 |
| Neutral | `#808086` | 未變動、次要資料 |
| Text Primary | `#FFFFFF` | 高對比主文字 |
| Text Secondary | `#AAAAAA` | 標籤、中繼資料 |
| Text Tertiary | `#828282` | 時間戳、格線標籤 |

### CSS Token

```css
:root {
  --terminal-bg: #0D0D0D;
  --terminal-surface: #141414;
  --terminal-surface-hover: #1A1A1A;
  --terminal-border: #2A2A2A;
  --terminal-gain: #00D4AA;
  --terminal-loss: #FF4757;
  --terminal-warning: #FFB800;
  --terminal-text: #FFFFFF;
  --terminal-text-secondary: #AAAAAA;
  --terminal-text-tertiary: #828282;
}
```

## 3. 排版

- **內文字型：** `'Inter', system-ui, sans-serif`
- **數據字型：** `'JetBrains Mono', 'Fira Code', monospace`（monospace 確保數字對齊）
- **字級縮放：** 10/12/14/16/20/24/32/48
- **數字格式：** 千分位逗號、小數點後兩位、正負號前綴

## 4. 佈局原則

- **資訊密度最大化**：減少裝飾性留白，讓資料說話
- **格線對齊**：所有區塊貼齊 4px 網格
- **可掃視性**：最重要的數字放在左上角（F-pattern）
- **顏色只代表意義**：不要為了好看而亂加顏色

## 5. 資料呈現規範

- **KPI 數字必須有 delta（增減 %）**，綠色漲紅色跌
- **圖表盡量 compact**，不要過大的留白
- **多圖表時保持 Y 軸範圍一致**，方便比較
- **Tooltip 顯示完整資訊**：數值、變動%、日期時間

## 6. 戰情表典型佈局

```
┌────────────────────────────────────────────────────┐
│  🔍 標題列       日期範圍 [2024-01 ~ 2024-12]      │
├─────────────┬──────────────────────────────────────┤
│  📂 來源    │  核心 KPI 列（4-6 張卡片）            │
│  業績報表    │  +12.3%     -2.1%    +5.7%    +8.2%  │
│  客戶滿意度  ├──────────┬───────────────────────────┤
│             │  圖表 A   │  圖表 B                   │
│  KPI 篩選   │  (折線)   │  (長條)                   │
│  ☑ 營收     ├──────────┴───────────────────────────┤
│  ☑ 成長率   │  資料表格（可排序、sticky header）     │
│  ☑ 客戶數   ├──────────────────────────────────────┤
│             │  💡 洞察                              │
│  📌 版本    │  • 營收較上月 +12.3%，主要來自...     │
│  v1 v2 v3   │  • 客戶滿意度連續三月下滑...           │
└─────────────┴──────────────────────────────────────┘
```