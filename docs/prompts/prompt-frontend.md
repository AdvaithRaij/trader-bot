Build a modern, dark-themed trading admin dashboard using **React (with Vite)**, **TailwindCSS**, and **ShadCN UI**. The design should be sleek, futuristic, and glassmorphic — focused on day traders managing their AI-assisted bot.

🧠 DESIGN STYLE:
- **Dark mode** by default
- Fonts: Use **Space Grotesk** or **Plus Jakarta Sans**
- Components: Rounded (`rounded-2xl`), with **glassmorphism** (`backdrop-blur-xl`), soft shadows
- Gradients: **Indigo ➜ Purple ➜ Blue**
- Accent glow effects for gains, losses, and active elements
- Smooth transitions using **Framer Motion**

📦 TECH STACK:
- React + Vite + TypeScript
- TailwindCSS (extended theme)
- ShadCN UI (for Cards, Dialogs, Tabs, CMD+K, etc.)
- Recharts or ApexCharts for charting
- Framer Motion for animations

📚 PAGES (Sidebar Layout):
1. **Home**:
   - Daily Summary Banner (yesterday’s P&L, today’s market plan, monthly stats)
   - Auto-scrolling news ticker (pause on hover, styled like a trading terminal)
   - Featured rotating news card with AI summary and sentiment icon
   - Mini trade health dashboard (active trades, win%, MTM)

2. **Screener**:
   - Grid of AI-selected stocks (Score, Tags, Sentiment)
   - Stock card opens full-page view: Candle chart, indicators, news, AI breakdown
   - Filter by sector, score, volume spike

3. **Trade Logs**:
   - Table of past trades (stock, date, entry/exit, result, strategy)
   - Calendar P&L heatmap
   - Per-trade AI reasoning
   - Filters: strategy, outcome, confidence score

4. **News**:
   - AI-written summary of market headlines
   - Full feed of tagged, filterable stock news
   - Search by keyword, sentiment, or ticker
   - Timeline of historical news impact

5. **Strategy Center**:
   - View, toggle, and compare predefined strategies (VWAP bounce, news breakout)
   - Backtest charts, R:R, P&L curves, avg win/loss
   - Compare 2–4 strategies side-by-side
   - Strategy editor for rule-tuning (SL, entry filters)

6. **Risk Manager**:
   - Live exposure stats
   - Max drawdown tracker
   - Trade blocker triggers + thresholds (editable)
   - Daily risk log with action timestamps

7. **Settings**:
   - Broker APIs, model selection, Telegram bot
   - Theme switch (default dark), notification config

🧠🔎 CMD + K SPOTLIGHT SEARCH:
Build a **command palette** like Spotlight/Raycast using ShadCN’s `CommandDialog`.

🔹 Requirements:
- Trigger: `Cmd + K` or `Ctrl + K` globally
- Appearance:
  - Centered modal with `backdrop-blur-xl`, `bg-black/60`
  - Rounded (`rounded-xl`) with gradient border (`from-indigo-500 to-blue-500`)
  - Glowing input on focus
- Suggestions:
  - Fuzzy-searchable list (modules, stocks, metrics)
  - Show `label`, `type`, `keywords`, `route`
  - Match as user types; navigate on selection using `react-router-dom` or `next/router`
- Navigation:
  - Keyboard arrow support (Up/Down/Enter)
  - Close on ESC or outside click
- Bonus:
  - Animate open/close with Framer Motion
  - Icons for suggestions using `lucide-react`
  - Group by categories like “Modules”, “Stocks”, “Strategies”

📂 COMPONENT STRUCTURE:
- `Sidebar.tsx`, `Topbar.tsx`, `Layout.tsx`
- `SummaryBanner.tsx`, `TickerScroller.tsx`, `NewsCard.tsx`
- `TradeTable.tsx`, `StrategyComparison.tsx`
- `CommandPalette.tsx` for spotlight search
- `searchIndex.ts` for fuzzy search (manual list of suggestions)

🎨 THEME COLORS:
- Base: `#0e0e12` or `#111827`
- Gradients: `from-indigo-600 via-purple-600 to-blue-500`
- Green glow: `text-green-400/90`, Red: `text-red-400/90`

Start by building the full **layout** (sidebar + topbar + content area) and add the **CommandPalette** component with modal overlay. Style with full dark mode glass UI and route-to-page support.
