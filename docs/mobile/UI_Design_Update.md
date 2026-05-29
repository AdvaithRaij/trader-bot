# TRADINGBOT MOBILE — COMPLETE UI/UX REDESIGN SPECIFICATION
# Version 2.0 — Production-Grade Design Document

---

## TABLE OF CONTENTS
1. Critical Context & Problems with Current Build
2. Design Philosophy & Principles
3. Design System (Colors, Typography, Spacing, Elevation, Icons)
4. Component Library — Pixel-Level Specifications
5. Tab Bar Design
6. Screen 1: Dashboard — Complete Specification
7. Screen 2: News — Complete Specification
8. Screen 3: Analysis — Complete Specification
9. Screen 4: Stock Detail — Complete Specification (navigated from Analysis)
10. Screen 5: Predictions — Complete Specification
11. Screen 6: Alerts — Complete Specification
12. Animation & Interaction Specifications
13. Mock Data File
14. Implementation Task Order

---

## 1. CRITICAL CONTEXT & PROBLEMS WITH CURRENT BUILD

### What's Wrong Now:
- **Empty shells everywhere**: Every screen is 2-3 hollow cards that say "Coming soon" or "No data". This is unacceptable.
- **90% wasted screen space**: The bottom 60-70% of every screen is dead empty dark space. Nothing fills it.
- **No visual hierarchy**: All cards look identical — same size, same style, same boring layout. Nothing draws the eye.
- **No data density**: A trading app's #1 job is to show data. These screens show zero data points.
- **No charts or graphs**: A financial app without a single chart is worthless visually.
- **Floating gear button**: Looks like a default template widget. Unprofessional.
- **Tab bar is flat and dead**: No glassmorphic effect, no glow on active tab, looks like default React Navigation.
- **No icons within content**: Cards have tiny icons in circles but the content itself has no iconography.
- **Font hierarchy is weak**: Everything looks the same weight and size.
- **No color variation**: Everything is the same shade of dark blue. No accent pops, no gradient highlights, no semantic coloring.

### What It Must Become:
- Every screen scrolls with rich content
- Data is king — numbers, percentages, charts, badges everywhere
- Visual hierarchy guides the eye: big hero numbers → section cards → detail rows
- Color is semantic: green = profit/bullish, red = loss/bearish, purple = AI/accent, blue = info, amber = warning
- Charts and graphs fill space meaningfully — sparklines, bar charts, gauge meters, progress bars
- Glass cards have depth — varying levels of transparency, some with gradient borders, some with colored glow
- The app should feel like opening a Bloomberg terminal on your phone, but beautiful
- Compare with: Groww, Zerodha Kite, Robinhood, TradingView mobile, Webull

---

## 2. DESIGN PHILOSOPHY & PRINCIPLES

### Principle 1: Information Density Over Emptiness
Every visible area of the screen must communicate data. If there's empty space, fill it with a relevant widget: a mini chart, a stat row, a market ticker, a trending stock badge. The user should feel overwhelmed (in a good way) with the amount of information available at a glance.

### Principle 2: Visual Hierarchy Through Scale & Color
- **Hero metrics** (portfolio value, stock price): Largest text on screen, 28-32px, bold, white
- **Section headers**: 17-18px, semibold, white
- **Key data points** (P&L, change %): 15-16px, colored (green/red), semibold
- **Labels**: 11-12px, uppercase, letter-spaced, muted gray
- **Secondary info**: 13px, regular, slate-400 gray

### Principle 3: Depth Through Layering
Stack visual layers:
- Layer 0: Deep dark background gradient
- Layer 1: Slightly lighter section backgrounds
- Layer 2: Glass cards with blur and border
- Layer 3: Elevated elements (active states, modals, tooltips)
- Layer 4: Floating elements (FAB, toast notifications)

### Principle 4: Motion Creates Life
- Numbers should animate when they change (count up/flash)
- Cards should enter the screen with staggered fade-in + slide-up
- Tab transitions should crossfade
- Pull-to-refresh should have a custom animation
- Charts should animate their drawing on mount

### Principle 5: Touch Targets & Feedback
- Every interactive element: minimum 44x44px touch target
- Haptic feedback on: tab changes, button presses, pull-to-refresh
- Press states: scale(0.97) + slight darken
- Active states: glow border, elevated shadow

---

## 3. DESIGN SYSTEM

### 3A. Color Palette

```typescript
// src/theme/colors.ts

export const Colors = {
  // === BACKGROUND LAYERS ===
  bg: {
    primary: '#05070E',          // Deepest — screen background
    secondary: '#0A0F1E',        // Section backgrounds, header areas
    tertiary: '#0F1628',         // Card interiors, elevated containers
    quaternary: '#151D30',       // Nested card backgrounds
  },

  // === GLASS CARD SYSTEM ===
  glass: {
    bg: 'rgba(15, 22, 40, 0.75)',           // Standard glass card
    bgLight: 'rgba(25, 35, 60, 0.60)',      // Lighter glass variation
    bgDark: 'rgba(8, 12, 24, 0.85)',        // Darker glass variation
    border: 'rgba(148, 163, 184, 0.10)',     // Default border
    borderLight: 'rgba(148, 163, 184, 0.06)', // Subtle border
    borderMedium: 'rgba(148, 163, 184, 0.15)', // Visible border
    borderAccent: 'rgba(139, 92, 246, 0.25)',  // Purple accent border
    borderGreen: 'rgba(16, 185, 129, 0.25)',   // Green accent border
    borderRed: 'rgba(239, 68, 68, 0.25)',      // Red accent border
  },

  // === GRADIENTS (arrays for LinearGradient) ===
  gradient: {
    purple: ['#7C3AED', '#A855F7'],
    purpleDark: ['#5B21B6', '#7C3AED'],
    blue: ['#2563EB', '#3B82F6'],
    cyan: ['#0891B2', '#06B6D4'],
    green: ['#059669', '#10B981'],
    greenBright: ['#10B981', '#34D399'],
    red: ['#DC2626', '#EF4444'],
    redBright: ['#EF4444', '#F87171'],
    gold: ['#D97706', '#F59E0B'],
    pink: ['#DB2777', '#EC4899'],
    indigo: ['#4F46E5', '#6366F1'],
    mixed: ['#6366F1', '#8B5CF6', '#A855F7'],
    // Background gradients
    screenBg: ['#05070E', '#0A0F1E', '#0F1628'],
    cardShine: ['rgba(255,255,255,0.05)', 'rgba(255,255,255,0.0)'], // Top-to-bottom shine
    // Overlay gradients (for cards with colored tints)
    greenTint: ['rgba(16,185,129,0.08)', 'rgba(16,185,129,0.02)'],
    redTint: ['rgba(239,68,68,0.08)', 'rgba(239,68,68,0.02)'],
    purpleTint: ['rgba(139,92,246,0.10)', 'rgba(139,92,246,0.02)'],
    blueTint: ['rgba(59,130,246,0.08)', 'rgba(59,130,246,0.02)'],
  },

  // === SEMANTIC COLORS ===
  bullish: '#10B981',
  bullishLight: '#34D399',
  bullishBg: 'rgba(16, 185, 129, 0.10)',
  bullishBgStrong: 'rgba(16, 185, 129, 0.18)',

  bearish: '#EF4444',
  bearishLight: '#F87171',
  bearishBg: 'rgba(239, 68, 68, 0.10)',
  bearishBgStrong: 'rgba(239, 68, 68, 0.18)',

  warning: '#F59E0B',
  warningLight: '#FBBF24',
  warningBg: 'rgba(245, 158, 11, 0.10)',

  info: '#3B82F6',
  infoLight: '#60A5FA',
  infoBg: 'rgba(59, 130, 246, 0.10)',

  neutral: '#64748B',
  neutralLight: '#94A3B8',
  neutralBg: 'rgba(100, 116, 139, 0.10)',

  accent: '#8B5CF6',        // Primary accent (violet)
  accentLight: '#A855F7',
  accentBg: 'rgba(139, 92, 246, 0.10)',

  // === TEXT ===
  text: {
    primary: '#F1F5F9',       // Slate-100 — headings, hero numbers
    secondary: '#CBD5E1',     // Slate-300 — body text, descriptions
    tertiary: '#94A3B8',      // Slate-400 — labels, timestamps
    muted: '#64748B',         // Slate-500 — disabled, hints
    disabled: '#475569',      // Slate-600 — disabled text
    inverse: '#0F172A',       // For text on light backgrounds
  },

  // === CHART SPECIFIC ===
  chart: {
    line: '#8B5CF6',
    lineFill: 'rgba(139, 92, 246, 0.12)',
    greenLine: '#10B981',
    greenFill: 'rgba(16, 185, 129, 0.12)',
    redLine: '#EF4444',
    redFill: 'rgba(239, 68, 68, 0.12)',
    grid: 'rgba(148, 163, 184, 0.05)',
    axis: 'rgba(148, 163, 184, 0.15)',
    tooltip: 'rgba(15, 23, 42, 0.95)',
    crosshair: 'rgba(148, 163, 184, 0.30)',
    bar1: '#8B5CF6',     // Primary bar color
    bar2: '#06B6D4',     // Secondary bar color
    bar3: '#F59E0B',     // Tertiary bar color
  },
} as const;
3B. Typography System
typescript
Run Code
Copy code
// src/theme/typography.ts
import { Platform, TextStyle } from 'react-native';

const monoFont = Platform.select({
  ios: 'Menlo',
  android: 'monospace',
  default: 'monospace',
});

export const Typography = {
  // === DISPLAY — Hero numbers, portfolio value ===
  displayLarge: {
    fontSize: 34,
    fontWeight: '800',
    letterSpacing: -1.0,
    lineHeight: 40,
    color: Colors.text.primary,
  } as TextStyle,

  displayMedium: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.8,
    lineHeight: 34,
    color: Colors.text.primary,
  } as TextStyle,

  displaySmall: {
    fontSize: 24,
    fontWeight: '700',
    letterSpacing: -0.5,
    lineHeight: 30,
    color: Colors.text.primary,
  } as TextStyle,

  // === HEADINGS — Section titles ===
  h1: {
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: -0.3,
    lineHeight: 28,
    color: Colors.text.primary,
  } as TextStyle,

  h2: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 24,
    color: Colors.text.primary,
  } as TextStyle,

  h3: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 22,
    color: Colors.text.primary,
  } as TextStyle,

  // === BODY — General text ===
  bodyLarge: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
    color: Colors.text.secondary,
  } as TextStyle,

  body: {
    fontSize: 14,
    fontWeight: '400',
    lineHeight: 20,
    color: Colors.text.secondary,
  } as TextStyle,

  bodySmall: {
    fontSize: 13,
    fontWeight: '400',
    lineHeight: 18,
    color: Colors.text.tertiary,
  } as TextStyle,

  // === LABELS & CAPTIONS ===
  label: {
    fontSize: 13,
    fontWeight: '500',
    lineHeight: 18,
    color: Colors.text.tertiary,
  } as TextStyle,

  labelSmall: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.8,
    lineHeight: 16,
    textTransform: 'uppercase',
    color: Colors.text.muted,
  } as TextStyle,

  caption: {
    fontSize: 12,
    fontWeight: '400',
    lineHeight: 16,
    color: Colors.text.tertiary,
  } as TextStyle,

  // === FINANCIAL NUMBERS — Prices, P&L, percentages ===
  priceLarge: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
    fontFamily: monoFont,
    fontVariant: ['tabular-nums'],
    color: Colors.text.primary,
  } as TextStyle,

  priceMedium: {
    fontSize: 18,
    fontWeight: '600',
    fontFamily: monoFont,
    fontVariant: ['tabular-nums'],
    color: Colors.text.primary,
  } as TextStyle,

  priceSmall: {
    fontSize: 14,
    fontWeight: '600',
    fontFamily: monoFont,
    fontVariant: ['tabular-nums'],
    color: Colors.text.primary,
  } as TextStyle,

  priceTiny: {
    fontSize: 12,
    fontWeight: '500',
    fontFamily: monoFont,
    fontVariant: ['tabular-nums'],
    color: Colors.text.secondary,
  } as TextStyle,

  // === BADGE TEXT ===
  badge: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.3,
    lineHeight: 14,
  } as TextStyle,

  // === TAB BAR ===
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.3,
  } as TextStyle,
};
3C. Spacing & Layout System
typescript
Run Code
Copy code
// src/theme/spacing.ts

export const Spacing = {
  // Base unit: 4px
  xxs: 2,
  xs: 4,
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  xxl: 20,
  xxxl: 24,
  huge: 32,
  massive: 40,

  // Semantic spacing
  screen: {
    paddingHorizontal: 16,
    paddingTop: 8,        // Below safe area
    paddingBottom: 8,
  },

  card: {
    padding: 14,           // Internal card padding
    paddingSmall: 10,
    paddingLarge: 18,
    gap: 10,               // Gap between cards in a list
    gapSmall: 8,
    borderRadius: 16,
    borderRadiusSmall: 12,
    borderRadiusLarge: 20,
  },

  section: {
    gap: 20,               // Between major sections
    gapSmall: 14,
    headerMarginBottom: 10,
  },

  row: {
    gap: 8,                // Between items in a horizontal row
    gapSmall: 6,
    gapLarge: 12,
  },

  list: {
    itemGap: 8,            // Between list items
    itemGapSmall: 6,
  },
};
3D. Shadow & Elevation System
typescript
Run Code
Copy code
// src/theme/shadows.ts
import { Platform, ViewStyle } from 'react-native';

export const Shadows = {
  none: {} as ViewStyle,

  sm: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
    },
    android: { elevation: 2 },
  }) as ViewStyle,

  md: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.20,
      shadowRadius: 8,
    },
    android: { elevation: 4 },
  }) as ViewStyle,

  lg: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.25,
      shadowRadius: 16,
    },
    android: { elevation: 8 },
  }) as ViewStyle,

  // Colored glows for accent elements
  glow: {
    purple: Platform.select({
      ios: {
        shadowColor: '#8B5CF6',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.30,
        shadowRadius: 12,
      },
      android: { elevation: 6 },
    }) as ViewStyle,

    green: Platform.select({
      ios: {
        shadowColor: '#10B981',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.25,
        shadowRadius: 12,
      },
      android: { elevation: 6 },
    }) as ViewStyle,

    red: Platform.select({
      ios: {
        shadowColor: '#EF4444',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.25,
        shadowRadius: 12,
      },
      android: { elevation: 6 },
    }) as ViewStyle,
  },
};
3E. Icon System
Use @expo/vector-icons — specifically Ionicons and MaterialCommunityIcons. Here is the icon mapping for the entire app:

typescript
Run Code
Copy code
// src/theme/icons.ts

export const Icons = {
  // Tab bar
  tabs: {
    dashboard: { lib: 'Ionicons', name: 'grid', activeColor: Colors.accent },
    news: { lib: 'Ionicons', name: 'newspaper', activeColor: Colors.info },
    analysis: { lib: 'MaterialCommunityIcons', name: 'chart-line', activeColor: Colors.accent },
    predictions: { lib: 'MaterialCommunityIcons', name: 'target', activeColor: Colors.warning },
    alerts: { lib: 'Ionicons', name: 'notifications', activeColor: Colors.bullish },
  },

  // Navigation & Actions
  back: 'chevron-back',
  settings: 'settings-outline',
  search: 'search-outline',
  filter: 'filter',
  refresh: 'refresh-outline',
  share: 'share-outline',
  bookmark: 'bookmark-outline',
  bookmarkFilled: 'bookmark',
  add: 'add-circle-outline',
  close: 'close',
  chevronRight: 'chevron-forward',
  chevronDown: 'chevron-down',
  chevronUp: 'chevron-up',
  more: 'ellipsis-horizontal',

  // Status & Indicators
  arrowUp: 'arrow-up',
  arrowDown: 'arrow-down',
  trendUp: 'trending-up',
  trendDown: 'trending-down',
  checkCircle: 'checkmark-circle',
  alertCircle: 'alert-circle',
  infoCircle: 'information-circle',
  clock: 'time-outline',
  eye: 'eye-outline',
  flash: 'flash',

  // Domain-specific
  portfolio: 'wallet-outline',
  trade: 'swap-vertical',
  bot: 'hardware-chip-outline',
  candle: 'bar-chart-outline',
  news: 'newspaper-outline',
  bell: 'notifications-outline',
  target: 'locate-outline',
  ai: 'sparkles',
  shield: 'shield-checkmark-outline',
  fire: 'flame',
  rocket: 'rocket-outline',
  lightbulb: 'bulb-outline',
  pulse: 'pulse',
  analytics: 'analytics',
  globe: 'globe-outline',
  building: 'business-outline',
  people: 'people-outline',
};
4. COMPONENT LIBRARY — PIXEL-LEVEL SPECIFICATIONS
Build each component in src/components/ui/. Every component must be self-contained with its own styles.
4A. GlassCard.tsx
Purpose: The foundational card component used EVERYWHERE.

less
Copy code
Props:
  children: ReactNode
  variant?: 'default' | 'elevated' | 'accent' | 'success' | 'danger'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  borderRadius?: 'sm' | 'md' | 'lg'
  onPress?: () => void
  gradient?: boolean          // Apply subtle gradient overlay
  glowColor?: string          // Add colored shadow glow
  style?: ViewStyle
  animated?: boolean          // FadeInUp entrance animation
  animationDelay?: number     // Stagger delay in ms

Visual Specification:
  DEFAULT variant:
    - backgroundColor: Colors.glass.bg
    - borderWidth: 1
    - borderColor: Colors.glass.border
    - borderRadius: Spacing.card.borderRadius (16)
    - overflow: 'hidden'
    - If gradient=true: overlay LinearGradient from top-left to bottom-right
      using Colors.gradient.cardShine (white 5% → transparent)

  ELEVATED variant:
    - Same as default but backgroundColor: Colors.glass.bgLight
    - borderColor: Colors.glass.borderMedium
    - Apply Shadows.md

  ACCENT variant:
    - borderColor: Colors.glass.borderAccent (purple tint)
    - Apply subtle purple glow shadow
    - Gradient overlay using Colors.gradient.purpleTint

  SUCCESS variant:
    - borderColor: Colors.glass.borderGreen
    - Gradient overlay using Colors.gradient.greenTint

  DANGER variant:
    - borderColor: Colors.glass.borderRed
    - Gradient overlay using Colors.gradient.redTint

  If onPress provided:
    - Wrap in Pressable
    - On press: Animated scale to 0.98, opacity to 0.9
    - On release: Spring back
    - Trigger Haptics.impactAsync(ImpactFeedbackStyle.Light)

  If animated=true:
    - Use Reanimated entering={FadeInUp.delay(animationDelay).duration(400).springify()}
4B. SparklineChart.tsx
Purpose: Tiny inline chart for showing price trends in watchlist/ticker items.

typescript
Run Code
Copy code
Props:
  data: number[]              // Array of prices
  width: number               // Chart width in pixels
  height: number              // Chart height in pixels
  color?: string              // Line color (auto: green if last > first, red if last < first)
  fillOpacity?: number        // Area fill opacity (default 0.1)
  strokeWidth?: number        // Line thickness (default 1.5)
  showDots?: boolean          // Show dot on last point
  animated?: boolean          // Animate drawing

Visual Specification:
  - Use react-native-svg to draw a smooth Path
  - Line is a smooth cubic bezier interpolation of the data points
  - Below the line: filled area with gradient from lineColor at top → transparent at bottom
  - Color logic:
    if data[last] > data[0] → color = Colors.bullish, fill = Colors.bullishBg
    if data[last] < data[0] → color = Colors.bearish, fill = Colors.bearishBg
    if equal → color = Colors.neutral
  - If showDots: render a small circle (r=2.5) at the last data point with matching color
  - No axes, no labels, no grid. Just the pure line + fill.
  - If animated: animate the path drawing from left to right over 600ms with easing
4C. PriceChangeText.tsx
Purpose: Displays a price change with proper color, arrow, and formatting.

typescript
Run Code
Copy code
Props:
  value: number               // The change amount (+15.40 or -11.55)
  percentage?: number         // Change percentage (+1.11 or -0.65)
  size?: 'xs' | 'sm' | 'md' | 'lg'
  showArrow?: boolean
  showSign?: boolean
  showBrackets?: boolean      // Wrap percentage in brackets like (+1.11%)
  variant?: 'text' | 'badge'  // Text or colored badge background

Visual Specification:
  SIZE xs: fontSize 11
  SIZE sm: fontSize 12
  SIZE md: fontSize 14
  SIZE lg: fontSize 16

  COLOR: value >= 0 → Colors.bullish : Colors.bearish
  ARROW: value >= 0 → '↑' or Ionicons 'caret-up' : '↓' or 'caret-down'

  TEXT variant example: "↑ +15.40 (+1.11%)" in green
  BADGE variant: Same text but with colored background pill
    - backgroundColor: value >= 0 ? Colors.bullishBg : Colors.bearishBg
    - paddingHorizontal: 8, paddingVertical: 3
    - borderRadius: 6

  Font: monospace/tabularNums for consistent digit width
4D. SectionHeader.tsx
Purpose: Consistent section title with optional action button.

yaml
Copy code
Props:
  title: string
  subtitle?: string
  action?: { label: string, onPress: () => void }
  icon?: string              // Ionicons icon name
  iconColor?: string

Visual Specification:
  Layout: Row — [Icon?] [Title Column] [Spacer] [Action Button?]

  Icon (if provided):
    - 18x18, color: iconColor || Colors.accent
    - marginRight: 8

  Title: Typography.h3, color: Colors.text.primary
  Subtitle (if provided): Typography.caption, color: Colors.text.muted, marginTop: 2

  Action button (if provided):
    - Text: Typography.label, color: Colors.accent
    - Touchable with opacity
    - Text like "See All →"

  Bottom margin: Spacing.section.headerMarginBottom (10)
4E. ProgressRangeBar.tsx
Purpose: Shows a value's position within a range (like Groww's price range bars).

sql
Copy code
Props:
  low: number
  high: number
  current: number
  lowLabel?: string           // e.g., "Today's Low"
  highLabel?: string          // e.g., "Today's High"
  showLabels?: boolean
  height?: number
  colors?: { track: string, fill: string, marker: string }

Visual Specification:
  Layout (vertical stack):
    Row 1 (if showLabels): [lowLabel, left-aligned] ... [highLabel, right-aligned]
      - Typography.caption, Colors.text.muted

    Row 2: [low value, left] ... [high value, right]
      - Typography.priceSmall

    Row 3: THE BAR
      - Full width track: height 4px, borderRadius 2, backgroundColor rgba(255,255,255,0.06)
      - Filled portion: From left edge to marker position, gradient from Colors.bearish → Colors.warning → Colors.bullish
      - Marker: Triangle (▲) pointing down, positioned at ((current - low) / (high - low) * 100)%
        - Triangle: 8px wide, 6px tall, color Colors.text.primary
        - Positioned with absolute positioning, centered on the percentage point
        - Below the triangle: small vertical line (1px wide, 8px tall) connecting to the track

  The percentage position is clamped between 2% and 98% to prevent edge overflow
4F. AnimatedCounter.tsx
Purpose: Numbers that animate/count up when they change.

vbnet
Copy code
Props:
  value: number
  prefix?: string             // '₹'
  suffix?: string             // '%', 'Cr'
  decimals?: number           // decimal places
  duration?: number           // animation duration ms
  style?: TextStyle
  colorize?: boolean          // Flash green/red on change

Implementation:
  - Use useSharedValue + useAnimatedProps from reanimated
  - When value changes, animate from old → new over duration (default 500ms)
  - If colorize: briefly flash the text color to green (if increased) or red (if decreased) for 300ms then back to the style color
  - Format with Indian number system (lakhs/crores) if large
  - Always use tabularNums font variant
4G. Badge.tsx
Purpose: Small labeled pill for status, sentiment, category.

yaml
Copy code
Props:
  text: string
  variant: 'bullish' | 'bearish' | 'neutral' | 'warning' | 'info' | 'accent' | 'custom'
  size?: 'sm' | 'md'
  icon?: string               // Small icon before text
  customColor?: string
  customBg?: string

Visual Specification:
  SM: paddingH 6, paddingV 2, fontSize 10, borderRadius 4
  MD: paddingH 8, paddingV 3, fontSize 11, borderRadius 6

  VARIANT COLORS:
    bullish: { bg: Colors.bullishBg, text: Colors.bullish, border: 'rgba(16,185,129,0.20)' }
    bearish: { bg: Colors.bearishBg, text: Colors.bearish, border: 'rgba(239,68,68,0.20)' }
    neutral: { bg: Colors.neutralBg, text: Colors.neutral, border: 'rgba(100,116,139,0.20)' }
    warning: { bg: Colors.warningBg, text: Colors.warning, border: 'rgba(245,158,11,0.20)' }
    info: { bg: Colors.infoBg, text: Colors.info, border: 'rgba(59,130,246,0.20)' }
    accent: { bg: Colors.accentBg, text: Colors.accent, border: 'rgba(139,92,246,0.20)' }
    borderWidth: 1
  borderColor: matching border from variant
  fontWeight: '700'
  letterSpacing: 0.3
  textTransform: 'uppercase'

  If icon provided: render 10px icon (sm) or 12px icon (md) before text with 3px gap
4H. SearchBar.tsx
Purpose: Glassmorphic search input used on Analysis and News screens.

less
Copy code
Props:
  placeholder?: string
  value: string
  onChangeText: (text: string) => void
  onFocus?: () => void
  onBlur?: () => void
  autoFocus?: boolean
  rightIcon?: ReactNode

Visual Specification:
  Container:
    - height: 44
    - backgroundColor: Colors.glass.bgDark
    - borderRadius: 12
    - borderWidth: 1
    - borderColor: Colors.glass.border (on focus: Colors.glass.borderAccent — animated transition)
    - flexDirection: 'row'
    - alignItems: 'center'
    - paddingHorizontal: 12

  Search Icon:
    - Ionicons 'search-outline', size 18, color Colors.text.muted
    - marginRight: 8

  Input:
    - flex: 1
    - Typography.body
    - color: Colors.text.primary
    - placeholderTextColor: Colors.text.disabled
    - selectionColor: Colors.accent

  Clear Button (when value.length > 0):
    - Ionicons 'close-circle', size 18, color Colors.text.muted
    - Pressable, marginLeft: 8
    - Animate: FadeIn.duration(200)

  Focus Animation:
    - Border color transitions from glass.border → glass.borderAccent over 200ms
    - Very subtle scale(1.01) on the container
4I. TabSelector.tsx
Purpose: Horizontal scrollable tab bar used inside screens (like Overview | Technicals | F&O | News).

yaml
Copy code
Props:
  tabs: Array<{ key: string, label: string, badge?: number }>
  activeTab: string
  onTabChange: (key: string) => void
  variant?: 'underline' | 'pill'
  scrollable?: boolean

Visual Specification:

  UNDERLINE variant (like Groww's tabs):
    - Horizontal ScrollView (scrollable=true) or Row
    - Each tab item:
      - paddingHorizontal: 16, paddingVertical: 10
      - Text: Typography.h3 size but weight depends on active:
        Active: fontWeight 600, color Colors.text.primary
        Inactive: fontWeight 400, color Colors.text.muted
      - Active indicator: 2px height bar at bottom, full tab width
        Color: gradient from Colors.gradient.purple[0] to Colors.gradient.purple[1]
        borderRadius: 1
        Animated position (slides left/right using Reanimated layoutAnimation)
      - If badge > 0: small red dot (6px) at top-right of tab label

  PILL variant (for filter chips like Quarterly/Yearly):
    - Horizontal row with 6px gap
    - Each pill:
      Active:
        - backgroundColor: Colors.accent
        - borderRadius: 20
        - paddingH: 14, paddingV: 6
        - Text: fontSize 12, fontWeight 600, color: Colors.text.primary
      Inactive:
        - backgroundColor: Colors.glass.bg
        - borderWidth: 1
        - borderColor: Colors.glass.border
        - borderRadius: 20
        - paddingH: 14, paddingV: 6
        - Text: fontSize 12, fontWeight 500, color: Colors.text.tertiary
    - Haptic feedback on tab change
4J. SentimentGauge.tsx
Purpose: The bearish/neutral/bullish visual bar from Groww's Technicals tab.

yaml
Copy code
Props:
  bearishCount: number
  neutralCount: number
  bullishCount: number
  overallLabel: string          // "Moderately Bearish"
  overallScore: number          // 1-10 (1=very bearish, 10=very bullish)

Visual Specification:
  Container: GlassCard variant="default"

  Title Row: "Summary" + info icon (ℹ️), right side: "Based on 1D data" caption
  
  Overall Label:
    - Typography.h2, color based on score:
      1-3: Colors.bearish
      4-6: Colors.warning  
      7-10: Colors.bullish
    - e.g., "Moderately Bearish" in red

  THE GAUGE BAR:
    - Full width, height 28px
    - Divided into individual vertical bars (like Groww screenshot):
      Total bars = bearishCount + neutralCount + bullishCount (e.g., 13 total)
      Each bar: width = (containerWidth / totalBars) - 2px gap
      Height: 28px, borderRadius: 2
      Colors:
        First bearishCount bars: Colors.bearish
        Next neutralCount bars: Colors.neutral  
        Last bullishCount bars: Colors.bullish
      Between bars: 2px gap (transparent)

    - Marker triangle: positioned at overallScore percentage
      Triangle pointing up from below the bar
      Size: 10w × 7h
      Color: Colors.text.primary

  Bottom Labels Row:
    Three columns evenly spaced:
    LEFT: Small colored bar (3px × 12px, Colors.bearish) + "Bearish" label + count below
    CENTER: Small colored bar (Colors.neutral) + "Neutral" label + count
    RIGHT: Small colored bar (Colors.bullish) + "Bullish" label + count
    
    Label: Typography.caption, color Colors.text.tertiary
    Count: Typography.h3, color Colors.text.primary
4K. IndicatorRow.tsx
Purpose: Single row in indicators table (RSI, MACD, Beta, etc.).

sql
Copy code
Props:
  name: string
  value: number | string
  verdict: string
  verdictType: 'bullish' | 'bearish' | 'neutral' | 'warning'

Visual Specification:
  Layout: Row with three columns
    Column 1 (40% width): name — Typography.body, color Colors.text.secondary
    Column 2 (25% width): value — Typography.priceSmall, color Colors.text.primary, right-aligned
    Column 3 (35% width): verdict — Typography.label, color based on verdictType, right-aligned
      bullish: Colors.bullish
      bearish: Colors.bearish
      neutral: Colors.text.tertiary
      warning: Colors.warning

  Row: paddingVertical 12, borderBottomWidth 1, borderBottomColor Colors.glass.borderLight
  Last row: no border
4L. SupportResistanceCard.tsx
Purpose: Visualizes S1/S2/S3 and R1/R2/R3 with price position (like Groww screenshot).

sql
Copy code
Props:
  levels: {
    r3: number, r2: number, r1: number,
    pivot: number,
    s1: number, s2: number, s3: number,
  }
  currentPrice: number

Visual Specification:
  Container: GlassCard

  Title: "Support and Resistance" + info icon

  THE TABLE/VISUAL:
    Vertical layout, each row represents a level
    Rows ordered top-to-bottom: R3, R2, R1, PIVOT, S1, S2, S3

    Each row:
      Layout: [Label left] ——— line ——— [Value right]
      Height: 36px
      
    Label column (left, 40px wide):
      "R3", "R2", "R1" in Colors.bearish (resistance = hard to break up, shown in red)
      "S1", "S2", "S3" in Colors.bullish (support = floor, shown in green)
      Typography.label, fontWeight 600

    Value column (right):
      Typography.priceSmall, color Colors.text.primary

    Between rows: thin dashed line, color Colors.glass.borderLight

    CURRENT PRICE indicator:
      - Positioned vertically between the appropriate levels (where currentPrice falls)
      - Horizontal pill/badge: 
        backgroundColor: Colors.accent
        borderRadius: 12
        paddingH: 12, paddingV: 4
        Text: "PRICE " + currentPrice, fontSize 11, fontWeight 700, color white
        Full width centered
      - Two horizontal lines extending left and right from the badge to screen edges
        color: Colors.accent, opacity 0.5, dashArray [4,4]

    PIVOT indicator:
      - Similar pill but:
        backgroundColor: Colors.text.muted
        Text: "PIVOT " + pivot value
        Smaller: paddingH: 10, paddingV: 3, fontSize 10
4M. BarChart.tsx (Wrapper around gifted-charts)
Purpose: Beautiful bar chart for Financials section (Revenue, Profit, Net Worth).

yaml
Copy code
Props:
  data: Array<{ label: string, value: number }>
  barColor?: string | string[]    // Single color or gradient
  height?: number
  showValues?: boolean
  formatValue?: (val: number) => string
  animated?: boolean

Visual Specification:
  - Use react-native-gifted-charts BarChart
  - Configuration:
    barWidth: 36
    spacing: 20
    barBorderRadius: 4 (top only — barBorderTopLeftRadius, barBorderTopRightRadius)
    frontColor: Colors.bullish (or prop barColor)
    gradientColor: Colors.bullishLight (lighter shade at top)
    isThreeD: false
    showGradient: true
    
  - Y-axis: hidden (we show values on top of bars instead)
  - X-axis labels: Typography.caption, color Colors.text.muted, rotate 0
  - Grid lines: horizontal, color Colors.chart.grid, dashWidth 4, dashGap 4
  
  - Value labels on top of each bar:
    Typography.priceTiny, color Colors.text.secondary
    Format: formatValue(val) — e.g., "2,93,043"
    Position: centered above bar, 4px gap

  - Background: transparent
  - No outer borders
  
  - Animation: bars grow from height 0 to full height over 600ms with easeOut
4N. MiniStockRow.tsx
Purpose: Compact stock row used in watchlists, similar stocks, top gainers/losers.

yaml
Copy code
Props:
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  sparkline?: number[]
  onPress?: () => void
  showSparkline?: boolean
  rank?: number               // Optional rank number on the left

Visual Specification:
  Container: Pressable row, paddingVertical 10, paddingHorizontal 0
  Border: borderBottomWidth 1, borderBottomColor Colors.glass.borderLight (except last)

  Layout: Row
    [Rank?] [SymbolColumn] [Spacer] [SparklineChart?] [PriceColumn]

  Rank (if provided):
    - Circle: 22x22, backgroundColor Colors.glass.bg, borderRadius 11
    - Text: rank number, fontSize 11, fontWeight 600, color Colors.text.muted, centered

  SymbolColumn (left, flex: 1):
    Row 1: symbol — Typography.h3, fontSize 14, fontWeight 600, color Colors.text.primary
    Row 2: name — Typography.caption, color Colors.text.muted, numberOfLines 1

  SparklineChart (if showSparkline, center):
    - Width: 60, Height: 28
    - Color auto-determined by data trend
    - marginHorizontal: 12

  PriceColumn (right, alignItems 'flex-end'):
    Row 1: price — Typography.priceSmall, color Colors.text.primary
    Row 2: PriceChangeText component
      - value: change, percentage: changePercent
      - size: 'xs'
      - showSign: true, showBrackets: true

  Press state: opacity 0.7 + haptic
4O. NewsCard.tsx
Purpose: Individual news article card with rich visual treatment.

sql
Copy code
Props:
  title: string
  summary?: string
  source: string
  timestamp: Date
  sentiment: 'positive' | 'negative' | 'neutral'
  importance: 'high' | 'medium' | 'low'
  relatedStocks: string[]
  onPress?: () => void
  variant?: 'compact' | 'full'  // compact for lists, full for featured

Visual Specification:

  COMPACT variant (used in lists):
    Container: Pressable, paddingVertical: 14
    Border: borderBottomWidth 1, borderBottomColor Colors.glass.borderLight

    Layout: Column

    Row 1 (Meta row): 
      [Sentiment dot] [Source] [•] [Time ago] [Spacer] [Importance badge?]
      
      Sentiment dot: 6px circle
        positive: Colors.bullish
        negative: Colors.bearish
        neutral: Colors.neutral
      Source: Typography.caption, fontWeight 600, color Colors.text.tertiary
      Separator: "•", color Colors.text.disabled
      Time: Typography.caption, color Colors.text.disabled
      Importance badge (if high): Badge variant="warning", text="HIGH", size="sm"

    Row 2 (Title): marginTop 6
      Typography.h3, fontSize 15, color Colors.text.primary, lineHeight 21
      numberOfLines: 3

    Row 3 (Summary, if exists): marginTop 4
      Typography.bodySmall, color Colors.text.muted, numberOfLines 2

    Row 4 (Related stocks, if any): marginTop 8
      Horizontal row of stock symbol badges:
      Each: Badge variant="accent", text=symbol, size="sm"
      Gap: 6px between badges
      ScrollView horizontal if more than 4

  FULL variant (used for featured/breaking):
    Container: GlassCard variant="accent", gradient=true

    TOP ROW: 
      [⚡ flash icon, Colors.warning] [" BREAKING", Typography.labelSmall, Colors.warning]
      Only if importance === 'high'

    Title: Typography.h2, color Colors.text.primary, marginTop 8

    Summary: Typography.body, color Colors.text.secondary, marginTop 6, numberOfLines 3

    Bottom row: marginTop 10
      [Source badge] [Time] [Spacer] [Stock chips]
4P. PredictionCard.tsx
Purpose: Rich card showing an AI prediction with targets, stop loss, confidence.

yaml
Copy code
Props:
  symbol: string
  name: string
  currentPrice: number
  direction: 'bullish' | 'bearish'
  entryPrice: number
  targets: Array<{ level: string, price: number, status: 'hit' | 'pending' | 'missed' }>
  stopLoss: number
  confidence: number           // 0-100
  timeframe: string
  riskReward: string
  verdict: string              // "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
  createdAt: Date
  onPress?: () => void

Visual Specification:
  Container: GlassCard, 
    variant = direction === 'bullish' ? 'success' : 'danger'
    gradient = true

  === HEADER SECTION ===
  Row 1: [Direction arrow icon + Badge] [Spacer] [Verdict badge]
    Direction: 
      bullish: ↑ icon + Badge "BULLISH" variant="bullish"
      bearish: ↓ icon + Badge "BEARISH" variant="bearish"
    Verdict badge:
      "Strong Buy": Badge variant="bullish" with glow
      "Buy": Badge variant="bullish"
      "Hold": Badge variant="warning"
      "Sell": Badge variant="bearish"
      "Strong Sell": Badge variant="bearish" with glow

  Row 2: marginTop 10
    Symbol: Typography.h2, color Colors.text.primary
    Name: Typography.bodySmall, color Colors.text.muted

  Row 3: marginTop 4
    Current price: Typography.priceLarge, fontSize 22
    PriceChangeText: from entry to current

  === TARGET LEVELS VISUAL ===
  marginTop 14

  Vertical track visualization:
    Left column (labels + prices):
      For each target (T3 at top, T2, T1, Entry, StopLoss at bottom):
        Row: [Level label] [Price] [Status icon]
    
    Right column (vertical line with nodes):
      Vertical line from StopLoss to T3
      Line color: gradient from Colors.bearish (bottom) → Colors.bullish (top)
      Nodes at each level: 
        Circle 8px
        T-levels: Colors.bullish (pending: hollow, hit: filled + checkmark)
        Entry: Colors.accent (filled)
        StopLoss: Colors.bearish (filled)
      
      Current price: horizontal dashed line crossing the track
      Filled region: from Entry to currentPrice
        bullish direction going up: green fill
        bearish direction going down: red fill

  === METRICS ROW ===
  marginTop 14
  Three metrics in a row, each in a mini glass card:
    
    Metric 1: Confidence
      CircularProgress: ring showing confidence%
      Ring color: 
        0-40: Colors.bearish
        40-70: Colors.warning
        70-100: Colors.bullish
      Center text: confidence + "%"
      Label below: "Confidence"

    Metric 2: Risk:Reward
      Icon: ⚖️ (or shield icon)
      Value: Typography.priceMedium, e.g., "1:2.8"
      Label below: "Risk:Reward"

    Metric 3: Timeframe
      Icon: 🕐 (clock)
      Value: Typography.label, e.g., "Swing (5-7 days)"
      Label below: "Timeframe"

  === AI REASONING (expandable) ===
  marginTop 12
  Row: [AI sparkle icon, Colors.accent] ["AI Analysis", Typography.label]
  Expandable text (collapsed shows 2 lines, tap to expand):
    Typography.bodySmall, color Colors.text.secondary
    The aiReasoning text

  === FOOTER ===
  marginTop 10
  Row: [Clock icon] ["Created " + timeAgo(createdAt)] [Spacer] [Share icon button]
  Typography.caption, color Colors.text.disabled
4Q. AlertCard.tsx
Purpose: Individual alert card showing status, target, stock info.

sql
Copy code
Props:
  symbol: string
  stockName: string
  type: 'price_above' | 'price_below' | 'target_hit' | 'stop_loss_hit' | 'percentage_change'
  targetValue: number
  currentPrice: number
  status: 'active' | 'triggered' | 'expired'
  createdAt: Date
  triggeredAt?: Date
  note?: string
  onPress?: () => void
  onDelete?: () => void

Visual Specification:
  Container: GlassCard
    If status === 'triggered': variant="success", animated subtle pulse glow
    If status === 'active': variant="default"
    If status === 'expired': variant="default", opacity 0.6

  Layout: Column

  === TOP ROW ===
  Row: [Status indicator] [Type icon + label] [Spacer] [Delete button]

  Status indicator:
    active: pulsing green dot (6px, animated opacity 0.4→1→0.4)
    triggered: solid checkmark in green circle
    expired: gray circle with dash

  Type label:
    price_above: "Price Above" with ↑ icon
    price_below: "Price Below" with ↓ icon
    target_hit: "Target Hit" with 🎯 icon
    stop_loss_hit: "Stop Loss" with 🛑 icon
    percentage_change: "% Change" with 📊 icon
    Typography.labelSmall, color Colors.text.tertiary

  Delete button: Ionicons 'trash-outline', size 16, color Colors.text.disabled
    Only show on active/expired. Not on triggered.

  === STOCK INFO ROW ===
  marginTop 10
  Row: [Symbol + Name column] [Spacer] [Current price column]
  
  Symbol: Typography.h3, color Colors.text.primary
  Name: Typography.caption, color Colors.text.muted
  Current price: Typography.priceMedium, color Colors.text.primary
  Below price: PriceChangeText (current vs target)

  === PROGRESS TO TARGET ===
  marginTop 12
  
  ProgressRangeBar showing:
    For price_above: low = price when set, high = targetValue, current = currentPrice
    For price_below: low = targetValue, high = price when set, current = currentPrice
  
  Below bar:
    Row: ["Target: ₹" + targetValue] [Spacer] ["Distance: " + distancePercent + "%"]
    Typography.caption, Colors.text.tertiary

  === TRIGGERED INFO (if triggered) ===
  marginTop 10
  GlassCard nested, variant="success", padding="sm"
    Row: [Checkmark icon, green] ["Triggered at ₹X on {date}"]
    Typography.bodySmall, color Colors.bullish

  === NOTE (if exists) ===
  marginTop 8
  Row: [Note icon] [note text]
  Typography.bodySmall, color Colors.text.muted, numberOfLines 2

  === FOOTER ===
  marginTop 8
  Row: [Clock icon] ["Set " + timeAgo(createdAt)]
  Typography.caption, color Colors.text.disabled
4R. CircularProgress.tsx
Purpose: Ring/donut chart showing a percentage value.

less
Copy code
Props:
  value: number               // 0-100
  size: number                // Diameter in pixels
  strokeWidth?: number        // Ring thickness (default 6)
  color?: string              // Auto-color based on value if not provided
  bgColor?: string            // Track color
  centerContent?: ReactNode   // What to render in the center
  animated?: boolean

Visual Specification:
  Use react-native-svg:
    Background circle: full 360° arc, color Colors.glass.border
    Value circle: arc from 0 to (value/100 * 360)°
      strokeLinecap: 'round'
      Color auto-logic:
        0-30: Colors.bearish
        30-60: Colors.warning
        60-100: Colors.bullish
    
  Rotation: start from top (rotate -90°)
  
  Center: centerContent rendered absolutely centered
    Default (if no centerContent): value + "%" in Typography.priceMedium

  If animated: animate the arc from 0 to target value over 800ms with spring easing
4S. ShareholdingBar.tsx
Purpose: Horizontal stacked bar showing shareholding pattern percentages.

yaml
Copy code
Props:
  data: Array<{ label: string, value: number, color: string }>

Visual Specification:
  Layout: Column

  THE BAR:
    - Single horizontal bar, full width, height 10px, borderRadius 5
    - Divided into segments proportional to each data item's value
    - Each segment colored with its respective color
    - No gaps between segments
    - First segment: borderTopLeftRadius + borderBottomLeftRadius: 5
    - Last segment: borderTopRightRadius + borderBottomRightRadius: 5

  LEGEND (below bar, marginTop 12):
    Vertical list of rows, each:
      Row: [Color dot 8px] [Label] [Spacer] [Horizontal mini bar] [Value%]
      
      Color dot: circle, backgroundColor matching segment
      Label: Typography.body, color Colors.text.secondary
      Mini bar: width proportional to value (maxWidth: 120px), height 6px, borderRadius 3
        backgroundColor: matching color at 60% opacity
      Value: Typography.priceSmall, color Colors.text.primary
      
      Gap between rows: 10px
5. TAB BAR DESIGN
File to modify: Tab navigator layout

yaml
Copy code
Visual Specification:

  Container:
    position: 'absolute', bottom: 0, left: 0, right: 0
    height: 80 (including safe area bottom)
    
  Background:
    BlurView with intensity 80, tint 'dark'
    On top of blur: LinearGradient
      colors: ['rgba(5,7,14,0.85)', 'rgba(5,7,14,0.95)']
      Top border: 1px, color Colors.glass.borderLight

  Layout: Row, 5 equal columns, centered content

  INACTIVE TAB:
    Icon: 22px, color Colors.text.disabled (slate-600)
    Label: hidden on inactive (or show with Typography.tabLabel, color Colors.text.disabled)
    
  ACTIVE TAB:
    Icon container: 
      width: 44, height: 44, borderRadius: 14
      backgroundColor: matching tab's accent color at 12% opacity
      Centered icon: 22px, color: matching tab's accent color
      Subtle glow shadow matching accent color
    
    Label: Typography.tabLabel, color matching accent color, marginTop 2

  Tab accent colors:
    Dashboard: '#8B5CF6' (violet)
    News: '#3B82F6' (blue)
    Analysis: '#06B6D4' (cyan)
    Predictions: '#F59E0B' (amber)
    Alerts: '#10B981' (emerald)

  NOTIFICATION BADGE on Alerts:
    Small red circle (16px diameter) at top-right of icon
    Position: top: -2, right: -2 (relative to icon container)
    Text: white, fontSize 9, fontWeight 700
    backgroundColor: Colors.bearish
    borderWidth: 2, borderColor: Colors.bg.primary (creates cutout effect)
    Show count of unread triggered alerts

  Animation:
    Active tab icon: subtle bounceIn when switching
    Haptic: light impact on tab change
6. SCREEN 1: DASHBOARD — Complete Specification
File: app/(tabs)/dashboard.tsx
This is the most important screen. It's the first thing users see.

less
Copy code
OVERALL LAYOUT:
  ScrollView, vertical
  backgroundColor: transparent (screen background gradient applied in layout)
  contentContainerStyle: { paddingBottom: 100 } // Space for tab bar

  SCREEN BACKGROUND:
    LinearGradient absolute fill
    colors: Colors.gradient.screenBg ['#05070E', '#0A0F1E', '#0F1628']

  SECTIONS (top to bottom):
    1. Header (non-scrolling, sticky)
    2. Portfolio Hero Card
    3. Market Indices Ticker
    4. Active Trades Section
    5. Watchlist Section
    6. Bot Status Card
    7. Hot News Carousel
    8. Top Movers (Gainers + Losers tabs)
    9. P&L Performance Chart
Section 6.1: Dashboard Header
less
Copy code
Position: SafeAreaView top, not inside ScrollView (or ScrollView sticky header)
Height: 52px
paddingHorizontal: Spacing.screen.paddingHorizontal

Layout: Row
  LEFT: 
    "TradingBot" — Typography.h1, color Colors.text.primary
    Small dot indicator next to it:
      If market open: green pulsing dot + "LIVE" text, Colors.bullish
      If market closed: gray dot + "CLOSED" text, Colors.text.muted
    
  RIGHT:
    Row of icon buttons, gap: 12px
    [Search icon] [Bell icon with badge] [Settings gear icon]
    Each: 
      width: 36, height: 36, borderRadius: 10
      backgroundColor: Colors.glass.bg
      borderWidth: 1, borderColor: Colors.glass.borderLight
      Icon: 18px, color Colors.text.tertiary
    Bell icon: show notification count badge (red dot, same as tab bar style)
Section 6.2: Portfolio Hero Card
vbnet
Copy code
marginTop: 8
marginHorizontal: Spacing.screen.paddingHorizontal

Container: GlassCard variant="elevated" gradient=true
  Additional: gradient overlay using Colors.gradient.purpleTint for subtle purple wash

LAYOUT inside card:

  ROW 1 (Label):
    "Portfolio Value" — Typography.labelSmall, color Colors.text.muted
    Right side: Badge "LIVE" variant="bullish" size="sm" (if market open)

  ROW 2 (Hero Value): marginTop 4
    AnimatedCounter: value=₹2,87,543.50
    Typography.displayMedium (28px, bold, white)
    This is THE biggest text on the entire screen

  ROW 3 (P&L Today): marginTop 6
    Row:
      [Arrow up icon, 14px, Colors.bullish]
      "+₹3,247.80 (+1.14%)" — Typography.priceMedium, color Colors.bullish
      [Spacer]
      "Today" — Typography.caption, color Colors.text.muted

  DIVIDER: marginVertical 12
    Thin gradient line: Colors.glass.borderLight

  ROW 4 (Stats grid): 2x2 grid of mini stat cells
    Each cell:
      Label: Typography.labelSmall, color Colors.text.muted
      Value: Typography.priceSmall, color Colors.text.primary (or colored)
    
    Grid contents:
    ┌──────────────────┬──────────────────┐
    │ Invested          │ Overall P&L      │
    │ ₹2,50,000        │ +₹37,543 (15.0%) │
    │ (white)          │ (green)           │
    ├──────────────────┼──────────────────┤
    │ Win Rate          │ Active Trades     │
    │ 73.5%            │ 3                 │
    │ (bullish)        │ (accent)          │
    └──────────────────┴──────────────────┘

    Each cell: 
      flex: 1 in a 2-column row
      paddingVertical: 8, paddingHorizontal: 10
      Separated by thin vertical/horizontal dividers (Colors.glass.borderLight)
Section 6.3: Market Indices Ticker
yaml
Copy code
marginTop: Spacing.section.gapSmall (14)

NO section header. This should feel like a seamless ticker strip.

Horizontal ScrollView, showsHorizontalScrollIndicator: false
paddingHorizontal: Spacing.screen.paddingHorizontal
contentContainerStyle: { gap: 10 }

Each Index Card:
  width: 148, height: 80
  GlassCard padding="sm" borderRadius="sm"

  Layout: Column
    Row 1: Index name — Typography.labelSmall (11px, uppercase, muted)
    Row 2: marginTop 4
      Value — Typography.priceMedium (18px, bold, white)
    Row 3: marginTop 2
      PriceChangeText: value=change, percentage=changePercent, size="xs"
    Row 4: marginTop 4
      SparklineChart: 
        data: sparkline array
        width: 120, height: 24
        strokeWidth: 1.5

  The sparkline should fill the bottom portion of the card, creating a nice visual
  Make the card slightly taller if needed to fit the sparkline nicely

Cards: NIFTY 50, SENSEX, BANK NIFTY, NIFTY IT
  Auto-scroll animation: slow continuous scroll if more than 2.5 cards visible

marginTop: Spacing.section.gap (20)
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader: 
  title: "Active Trades"
  icon: "swap-vertical" (Ionicons), iconColor: Colors.bullish
  action: { label: "View All →", onPress: navigate to pipeline }

Content: Vertical list of trade cards

EACH TRADE CARD:
  GlassCard padding="md" animated=true (stagger delay per card index * 100ms)

  Layout: Column

  === ROW 1: Header ===
  Row:
    LEFT:
      Badge: type === 'BUY' ? variant="bullish" text="BUY" : variant="bearish" text="SELL"
      size="sm"
    
    Adjacent to badge:
      Symbol — Typography.h3, color Colors.text.primary, marginLeft 8
      Name — Typography.caption, color Colors.text.muted, marginLeft 8

    RIGHT:
      Time — Typography.caption, color Colors.text.disabled
      "10:34 AM"

  === ROW 2: Price & P&L === marginTop 10
  Row:
    LEFT column:
      Label: "Entry" — Typography.labelSmall
      Value: "₹1,385.20" — Typography.priceSmall

    CENTER column:
      Label: "Current" — Typography.labelSmall
      Value: "₹1,404.80" — Typography.priceMedium, fontWeight 700
      (This is slightly bigger than entry to emphasize current)

    RIGHT column (aligned right):
      Label: "P&L" — Typography.labelSmall
      Value: "+₹196.00" — Typography.priceSmall, color Colors.bullish
      Below: "(+1.41%)" — Typography.caption, color Colors.bullish

  === ROW 3: Target & Stop Loss Visual === marginTop 10
  
  A single horizontal progress bar showing the trade range:
    
    Full range: from stopLoss to target
    Track: height 6px, borderRadius 3, backgroundColor Colors.glass.border
    
    Entry marker: small vertical line (1px × 10px) at entry position, color Colors.text.muted
    Current price: filled region from entry to current
      If profit: gradient green fill from entry to current
      If loss: gradient red fill from entry to current
    Target marker: small vertical tick at target position, color Colors.bullish
    StopLoss marker: small vertical tick at stopLoss position, color Colors.bearish
    
    Below bar (Row):
      LEFT: "SL: ₹1,360" — Typography.caption, color Colors.bearish
      CENTER: small dot showing progress percentage
      RIGHT: "T: ₹1,450" — Typography.caption, color Colors.bullish

  === ROW 4: Qty === marginTop 6
  Row:
    "Qty: 10" — Typography.caption, color Colors.text.muted
    [Spacer]
    "Invested: ₹13,852" — Typography.caption, color Colors.text.muted

  CARD BORDER:
    If trade is in profit: borderLeftWidth 3, borderLeftColor Colors.bullish
    If trade is in loss: borderLeftWidth 3, borderLeftColor Colors.bearish
    This creates a colored accent bar on the left edge

  Gap between trade cards: Spacing.card.gap (10)
Section 6.5: Watchlist Section
vbnet
Copy code
marginTop: Spacing.section.gap (20)
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title: "Watchlist"
  icon: "eye-outline" (Ionicons), iconColor: Colors.accent
  action: { label: "Edit", onPress: ... }

Content: GlassCard containing a list of MiniStockRow components

Inside the GlassCard:
  - No extra padding on sides (card padding handles it)
  - List of MiniStockRow components with showSparkline=true
  - Show first 6 stocks from MOCK_WATCHLIST
  - Each row is pressable → navigates to stock/[symbol]
  
  After the list:
    If more than 6 stocks: 
      "View all 8 stocks →" — centered text
      Typography.label, color Colors.accent
      Pressable with opacity

  Separator between rows: 1px, Colors.glass.borderLight
Section 6.6: Bot Status Card
less
Copy code
marginTop: Spacing.section.gap (20)
paddingHorizontal: Spacing.screen.paddingHorizontal

GlassCard variant="accent" gradient=true

Layout: Row (main content left, visual right)

LEFT SIDE (flex: 1):
  Row 1:
    [Robot/chip icon, Colors.accent, 20px] 
    "Trading Bot" — Typography.h3, marginLeft 8
    
  Row 2: marginTop 8
    Status indicator:
      Row: [Pulsing dot, green] ["Running" — Typography.label, Colors.bullish]
      OR: [Static dot, red] ["Stopped" — Typography.label, Colors.bearish]
    
  Row 3: marginTop 6
    Stats in a mini column:
      "Mode: Paper" — Typography.caption, Colors.text.tertiary
      "Trades Today: 3" — Typography.caption, Colors.text.tertiary  
      "Day P&L: +₹1,247" — Typography.caption, Colors.bullish

RIGHT SIDE (width: 80):
  CircularProgress:
    value: 73.5 (win rate)
    size: 64
    strokeWidth: 5
    color: Colors.bullish
    centerContent: 
      "73.5%" — Typography.priceSmall, fontSize 13
    Below circle:
      "Win Rate" — Typography.caption, color Colors.text.muted, textAlign center
Section 6.7: Hot News Carousel
less
Copy code
marginTop: Spacing.section.gap (20)

SectionHeader (with screen padding):
  title: "Market Pulse"
  icon: "flash" (Ionicons), iconColor: Colors.warning
  action: { label: "All News →", onPress: navigate to News tab }

Horizontal ScrollView:
  paddingLeft: Spacing.screen.paddingHorizontal
  contentContainerStyle: { paddingRight: Spacing.screen.paddingHorizontal, gap: 12 }
  showsHorizontalScrollIndicator: false
  snapToInterval: cardWidth + 12  // Snappy scroll
  decelerationRate: 'fast'

EACH NEWS CARD in carousel:
  width: screenWidth * 0.78 (so next card peeks)
  GlassCard gradient=true

  Layout: Column

  TOP: Importance indicator
    If high: Row with [⚡ icon, amber] ["BREAKING" — Typography.labelSmall, Colors.warning]
    If medium: Row with [📰 icon, blue] ["TRENDING" — Typography.labelSmall, Colors.info]
    If low: nothing

  TITLE: marginTop 6
    Typography.h3, color Colors.text.primary
    numberOfLines: 2

  SUMMARY: marginTop 4
    Typography.bodySmall, color Colors.text.tertiary
    numberOfLines: 2

  BOTTOM ROW: marginTop 10
    Row:
      [Source — Typography.caption, fontWeight 600, Colors.text.muted]
      [•]
      [timeAgo — Typography.caption, Colors.text.disabled]
      [Spacer]
      Sentiment badge: 
        positive: Badge "Positive" variant="bullish" size="sm"
        negative: Badge "Negative" variant="bearish" size="sm"
        neutral: Badge "Neutral" variant="neutral" size="sm"

  STOCK CHIPS: marginTop 6 (if relatedStocks.length > 0)
    Row of small stock symbol chips:
      Each: paddingH 6, paddingV 2, borderRadius 4
      backgroundColor: Colors.glass.bg
      borderWidth: 1, borderColor: Colors.glass.borderLight
      Text: Typography.caption, fontWeight 600, color Colors.accent

  Show 4-5 news cards. First one should be the highest importance.
Section 6.8: Top Movers (Gainers + Losers)
vbnet
Copy code
marginTop: Spacing.section.gap (20)
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title: "Top Movers"
  icon: "trending-up" (Ionicons), iconColor: Colors.bullish

TabSelector variant="pill":
  tabs: ["Gainers", "Losers"]
  Inline, right side of section header (or below it)

Content (changes based on active tab):

  GlassCard:
    GAINERS tab:
      List of MiniStockRow components for MOCK_TOP_GAINERS
      Each row has rank number (1-4) on left
      showSparkline: false (keep it compact)
      PriceChangeText on right side is green

    LOSERS tab:
      List of MiniStockRow for MOCK_TOP_LOSERS
      rank numbers
      PriceChangeText is red

  Rows separated by thin divider
  No extra bottom padding needed
Section 6.9: P&L Performance Chart
less
Copy code
marginTop: Spacing.section.gap (20)
paddingHorizontal: Spacing.screen.paddingHorizontal
marginBottom: Spacing.massive (40) // Extra space above tab bar

SectionHeader:
  title: "Performance"
  icon: "analytics" (Ionicons), iconColor: Colors.info

TabSelector variant="pill":
  tabs: ["1W", "1M", "3M", "6M", "1Y"]
  (Right side of header or below)

GlassCard:
  CHART:
    Line chart using react-native-gifted-charts LineChart
    height: 180
    
    Data: 30 data points representing daily P&L over the selected period
    Mock data: generate an upward trending line with realistic fluctuations
      Example for 1M: start at 240000, end at 287543, with daily variations of ±1-2%
    
    Line configuration:
      color: Colors.chart.line (#8B5CF6)
      thickness: 2
      curved: true (bezier)
      
    Area fill:
      areaChart: true
      startFillColor: Colors.chart.lineFill
      endFillColor: 'transparent'
      startOpacity: 0.3
      endOpacity: 0.0
      
    Grid:
      hideYAxisText: true (we show it differently)
      hideRules: false
      rulesColor: Colors.chart.grid
      rulesType: 'dashed'
      dashWidth: 3
      dashGap: 3
      
    X-axis:
      Show only 5 labels evenly spaced
      Typography.caption, color Colors.text.disabled
      rotateLabel: false
      
    No Y-axis labels
    
    Pointer/tooltip on press:
      Show a vertical dashed line at touch point
      Tooltip: glass card showing date + value
      
    Background: transparent

  BELOW CHART (inside same card): marginTop 12
    Row of 3 mini stats:
      "Best Day" | "+₹4,520" | Colors.bullish
      "Worst Day" | "-₹2,180" | Colors.bearish
      "Avg Daily" | "+₹890" | Colors.accent

    Each stat:
      Column, flex 1, alignItems center
      Label: Typography.labelSmall, Colors.text.muted
      Value: Typography.priceSmall, colored appropriately
7. SCREEN 2: NEWS — Complete Specification
File: app/(tabs)/news.tsx

markdown
Copy code
OVERALL LAYOUT:
  LinearGradient background (same as dashboard)
  
  SECTIONS:
    1. Header
    2. Breaking News Banner (if any high-importance news)
    3. Category Filter Tabs
    4. News Feed List

  The entire screen should feel like a premium news reader.
  Think: Bloomberg's mobile app news section.
Section 7.1: News Header
sql
Copy code
SafeAreaView top
Height: 52px
paddingHorizontal: Spacing.screen.paddingHorizontal

Layout: Row
  LEFT:
    "Market News" — Typography.h1
    Below: "AI-powered analysis" — Typography.caption, Colors.text.muted
    
  RIGHT:
    Row:
      [Search icon button] [Filter icon button]
      Same glass button style as dashboard header
      
    Filter button: if any filter active, show small accent dot on button
Section 7.2: Breaking News Banner
sql
Copy code
marginTop: 8
paddingHorizontal: Spacing.screen.paddingHorizontal

ONLY show if there is a news item with importance === 'high' from last 2 hours

Container:
  GlassCard variant="accent" gradient=true
  Additional: animated gradient border effect (subtle pulsing border opacity)

Layout: Column

  TOP ROW:
    [⚡ flash icon, animated pulse, Colors.warning] 
    ["BREAKING NEWS" — Typography.labelSmall, Colors.warning, letterSpacing 1.5]
    [Spacer]
    [Timestamp — Typography.caption, Colors.text.disabled]

  TITLE: marginTop 8
    Typography.h2, color Colors.text.primary
    Full text (no truncation)

  SUMMARY: marginTop 4
    Typography.body, color Colors.text.secondary
    numberOfLines: 3

  BOTTOM ROW: marginTop 10
    Row:
      Badge for source (e.g., "CNBC TV18" variant="info")
      [Spacer]
      Row of related stock chips
      [→ arrow icon, Colors.accent] // Tap to read more

  The flash icon should have a subtle glow animation:
    Reanimated loop: opacity 0.5 → 1 → 0.5 over 2 seconds
Section 7.3: Category Filter Tabs
css
Copy code
marginTop: 14

Horizontal ScrollView:
  paddingHorizontal: Spacing.screen.paddingHorizontal

TabSelector variant="pill":
  tabs: [
    { key: 'all', label: 'All' },
    { key: 'market', label: '📈 Market' },
    { key: 'economy', label: '🏛️ Economy' },
    { key: 'sector', label: '🏭 Sector' },
    { key: 'global', label: '🌍 Global' },
    { key: 'regulatory', label: '⚖️ Regulatory' },
  ]

  Include emoji in the pill text for visual flair
  Scrollable since they may overflow
Section 7.4: News Feed List
vbnet
Copy code
marginTop: 14
paddingHorizontal: Spacing.screen.paddingHorizontal

FlatList with NewsCard components (compact variant)

Configuration:
  ItemSeparatorComponent: null (NewsCard compact has its own bottom border)
  contentContainerStyle: { paddingBottom: 100 }
  showsVerticalScrollIndicator: false
  
  Pull-to-refresh: enabled
    Refresh indicator color: Colors.accent

Sort: by timestamp descending (newest first)

Filter: based on selected category tab

Total items shown: all MOCK_NEWS items + add more to fill the screen (minimum 8-10 items)

BETWEEN every 4th news item: insert a "Trending Stock" inline card:
  GlassCard variant="default" padding="sm"
  Row: [📊 icon] ["Trending: RELIANCE is up 1.11% today"] [Spacer] [→]
  Typography.bodySmall, color Colors.text.secondary
  Pressable → navigate to stock detail

At the bottom of the list (ListFooterComponent):
  "You're all caught up! ✅" 
  Typography.body, color Colors.text.muted, textAlign center
  marginVertical: 20

Each NewsCard is pressable:
  On press: could expand for full summary, or navigate to a detail view
  For now: just show press opacity feedback
8. SCREEN 3: ANALYSIS — Complete Specification
File: app/(tabs)/analysis.tsx

sql
Copy code
PURPOSE: This is the stock discovery and search screen. Users search for stocks
or browse from categorized lists. Tapping a stock navigates to the full
Stock Detail screen (Screen 4).

OVERALL LAYOUT:
  LinearGradient background
  
  SECTIONS:
    1. Header with search
    2. Search Results (when searching)
    3. Market Overview Cards (when not searching)
    4. Sector Performance Heatmap
    5. Trending Stocks Grid
    6. Stock Categories (NIFTY 50 list, Sector lists)
Section 8.1: Analysis Header + Search
sql
Copy code
SafeAreaView top
paddingHorizontal: Spacing.screen.paddingHorizontal

ROW 1:
  "Stock Analysis" — Typography.h1
  Below: subtitle hidden (search takes priority)

ROW 2: marginTop 10
  SearchBar component (full width)
    placeholder: "Search stocks, sectors, indices..."
    
  When search is focused:
    - The rest of the screen dims slightly (opacity overlay 0.3)
    - Search results appear below in an absolute-positioned list
    - Cancel button appears right of search bar
Section 8.2: Search Results Overlay
less
Copy code
ONLY visible when searchBar has text and is focused

Container:
  Position: absolute, below search bar
  backgroundColor: Colors.bg.secondary
  borderRadius: 16
  borderWidth: 1
  borderColor: Colors.glass.border
  maxHeight: screenHeight * 0.5
  Shadow: Shadows.lg
  zIndex: 100
  marginHorizontal: Spacing.screen.paddingHorizontal

Results List:
  FlatList of search result rows

  EACH ROW:
    Pressable, paddingVertical 12, paddingHorizontal 14
    Border: bottom 1px Colors.glass.borderLight

    Layout: Row
      LEFT (flex 1):
        Symbol: Typography.h3, color Colors.text.primary
        Below: Full name — Typography.caption, color Colors.text.muted
      
      RIGHT:
        Price: Typography.priceSmall, color Colors.text.primary
        Below: PriceChangeText, size="xs"

    On press: navigate to stock/[symbol], dismiss search

  If no results:
    Centered:
      [Search icon, 40px, Colors.text.disabled]
      "No stocks found" — Typography.body, Colors.text.muted
      marginVertical: 30

  Recent searches section (if search empty but focused):
    SectionHeader: "Recent Searches", icon "time-outline"
    List of recently searched stock symbols as chips
    Horizontal row of pills
Section 8.3: Market Overview Cards (Default State)
less
Copy code
ONLY visible when search is NOT focused

marginTop: 16
paddingHorizontal: Spacing.screen.paddingHorizontal

Row of 2 cards side by side, gap: 10

CARD 1: Market Mood Index
  GlassCard, flex: 1, height: 140
  
  Content:
    Label: "Market Mood" — Typography.labelSmall, Colors.text.muted
    
    Semi-circular gauge (half donut):
      Use react-native-svg to draw a 180° arc
      Width: fill card, height: ~70px
      Track: gray
      Fill: gradient from red (left) through yellow (center) to green (right)
      Needle/pointer at current mood position
      
    Below gauge:
      "Greed" or "Fear" or "Neutral" — Typography.h3
      Color: based on mood (greed=green, fear=red, neutral=yellow)
      Score: "67/100" — Typography.caption

CARD 2: Market Status
  GlassCard, flex: 1, height: 140
  
  Content:
    Label: "Market Status" — Typography.labelSmall
    
    Row:
      [Green pulsing dot] ["Open" — Typography.h2, Colors.bullish]
    
    Stats column, marginTop 8:
      "Advances: 1,247" — Typography.bodySmall, Colors.bullish
      "Declines: 832" — Typography.bodySmall, Colors.bearish
      "Unchanged: 156" — Typography.bodySmall, Colors.text.muted
    
    Mini advance/decline bar:
      Horizontal stacked bar, 4px height
      Green portion (advances), Red portion (declines), Gray (unchanged)
Section 8.4: Sector Performance Heatmap
less
Copy code
marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title: "Sector Performance"
  icon: "pie-chart-outline" (Ionicons), iconColor: Colors.info

Container: Flex wrap row of sector tiles

EACH SECTOR TILE:
  width: (screenWidth - 32 - 8) / 2  (two columns with gap)
  height: 56
  borderRadius: 12
  marginBottom: 8

  backgroundColor depends on performance:
    Positive: Colors.bullishBg (at varying opacity based on magnitude)
    Negative: Colors.bearishBg (at varying opacity)
    The stronger the change, the more intense the color

  Layout: Row, paddingHorizontal 12, centered vertically
    LEFT:
      Sector name — Typography.label, color Colors.text.primary
    RIGHT:
      Change% — Typography.priceSmall, color (green/red)

  SECTOR DATA (mock):
    IT: +1.28%
    Banking: -0.44%
    Pharma: +0.72%
    Auto: +1.85%
    Energy: +0.33%
    FMCG: -0.18%
    Metals: -1.12%
    Realty: +2.34%

  On press: could filter stock list by sector (future feature)
Section 8.5: Trending Stocks Grid
yaml
Copy code
marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title: "Trending Today"
  icon: "flame" (Ionicons), iconColor: Colors.warning
  action: { label: "See All →" }

Horizontal ScrollView:
  gap: 10
  snapToInterval: cardWidth + 10

EACH TRENDING STOCK CARD:
  width: 155, height: 130
  GlassCard padding="md"

  Layout: Column
    Row 1:
      Symbol initial in colored circle:
        28x28 circle, backgroundColor: hash(symbol) generates a unique pastel color
        Letter: first letter of symbol, white, fontSize 14, fontWeight 700
      
      Adjacent:
        Symbol — Typography.h3, fontSize 13
        Name — Typography.caption, fontSize 10, numberOfLines 1

    Row 2: marginTop 8
      Price — Typography.priceMedium
      PriceChangeText — size "xs", badge variant

    Row 3: marginTop 6
      SparklineChart: data, width: full card width - padding, height: 30

  Show 6-8 trending stocks
Section 8.6: Stock Category Lists
yaml
Copy code
marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title: "NIFTY 50"
  icon: "bar-chart-outline" (Ionicons), iconColor: Colors.accent
  action: { label: "View All →" }

GlassCard:
  List of MiniStockRow components
  Show first 8 stocks from MOCK_WATCHLIST (extended with more stocks)
  showSparkline: true
  Each pressable → navigate to stock/[symbol]

After NIFTY 50 section, add another:

SectionHeader:
  title: "Bank NIFTY"
  icon: "business-outline", iconColor: Colors.info
  action: { label: "View All →" }

GlassCard:
  Another list of 5-6 banking stocks
  HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK, INDUSINDBK

marginBottom: Spacing.massive (for tab bar space)
9. SCREEN 4: STOCK DETAIL — Complete Specification
File: app/stock/[symbol].tsx

vbnet
Copy code
PURPOSE: Deep dive into a single stock. This is the most content-rich screen.
Navigated to from Analysis tab when a stock is tapped.
This screen MUST match the Groww app screenshots in data density and layout.

OVERALL LAYOUT:
  Stack navigation screen (not tab)
  Custom header with back button
  ScrollView with many sections
  Tabbed content: Overview | Technicals | News

  SECTIONS:
    1. Custom Header (back, stock name, price, actions)
    2. Mini Price Chart
    3. Time Period Selector (1D, 1W, 1M, 3M, 6M, 1Y, All)
    4. Tab Selector (Overview, Technicals, News)
    5. TAB CONTENT — varies by selected tab
Section 9.1: Stock Detail Header
sql
Copy code
Custom header (not default navigation header):
  backgroundColor: transparent (gradient background continues)
  SafeAreaView top
  paddingHorizontal: Spacing.screen.paddingHorizontal
  
  ROW 1:
    [Back chevron button] [Spacer] [Bookmark icon] [Share icon] [Search icon]
    
    Back button:
      Ionicons 'chevron-back', size 24, color Colors.text.primary
      Touch target: 44x44
      Haptic on press
    
    Right icons: same glass button style, 32x32 each, gap 8

  ROW 2: marginTop 8
    Stock name — Typography.h1, color Colors.text.primary
      e.g., "Reliance Industries"
    
  ROW 3: marginTop 4
    Row:
      Price — Typography.displaySmall (24px, bold, mono)
        "₹1,404.80"
      PriceChangeText — marginLeft 10, size="md"
        "+15.40 (+1.11%)" in green
Section 9.2: Mini Price Chart
yaml
Copy code
marginTop: 12
Full width (no horizontal padding — chart goes edge to edge)
Height: 180

Line chart:
  Data: MOCK_STOCK_DETAIL.priceHistory (20+ data points)
  
  Configuration:
    curved: true
    color: determined by overall change (green if positive, red if negative)
    thickness: 2
    hideDataPoints: true
    areaChart: true
    startFillColor: matching color at 20% opacity
    endFillColor: transparent
    startOpacity: 0.25
    endOpacity: 0
    hideYAxisText: true
    hideAxesAndRules: true
    adjustToWidth: true
    width: screenWidth
    
  Optional: dashed horizontal line at the open/prevClose price
    dashWidth: 4, dashGap: 4
    color: Colors.text.disabled

  On long press: show crosshair with date + price tooltip
    Vertical dashed line from top to bottom at touch X
    Tooltip card above: small glass card with price + date
    Haptic on initial press
Section 9.3: Time Period Selector
yaml
Copy code
marginTop: 8
paddingHorizontal: Spacing.screen.paddingHorizontal

Horizontal row of period buttons:
  ["1D", "1W", "1M", "3M", "6M", "1Y", "5Y", "All"]

  Each button:
    Active:
      backgroundColor: Colors.glass.bgLight
      borderRadius: 16
      paddingH: 12, paddingV: 6
      Text: Typography.label, fontWeight 600, color Colors.text.primary
      borderWidth: 1, borderColor: Colors.glass.borderMedium
      
    Inactive:
      backgroundColor: transparent
      paddingH: 12, paddingV: 6
      Text: Typography.label, color Colors.text.muted
      
  Gap: 4 between buttons
  Centered or ScrollView horizontal if overflow
Section 9.4: Content Tab Selector
makefile
Copy code
marginTop: 14
paddingHorizontal: Spacing.screen.paddingHorizontal

TabSelector variant="underline":
  tabs: ["Overview", "Technicals", "News"]
  
Animated underline indicator that slides between tabs
Section 9.5: OVERVIEW TAB CONTENT
sql
Copy code
Visible when "Overview" tab is active.
All sections below, stacked vertically with Spacing.section.gap between them.
paddingHorizontal: Spacing.screen.paddingHorizontal
9.5A: Performance Section
yaml
Copy code
SectionHeader: title="Performance", icon="pulse"

Content: Column

  === TODAY'S RANGE ===
  ProgressRangeBar:
    lowLabel: "Today's Low"
    highLabel: "Today's High"
    low: 1390.30
    high: 1424.30
    current: 1404.80
    showLabels: true

  marginTop: 14

  === 52-WEEK RANGE ===
  ProgressRangeBar:
    lowLabel: "52 Week Low"
    highLabel: "52 Week High"
    low: 1114.85
    high: 1611.80
    current: 1404.80
    showLabels: true

  marginTop: 14

  === KEY METRICS ROW ===
  2x3 grid (2 columns, 3 rows):

  Row 1: Open | Prev. Close
  Row 2: Volume | Avg. Volume
  Row 3: Lower Circuit | Upper Circuit

  Each cell:
    Label — Typography.labelSmall, Colors.text.muted
    Value — Typography.priceSmall, Colors.text.primary
    
  Cells arranged in 2-column row:
    Left cell: paddingRight 12
    Right cell: paddingLeft 12, alignItems 'flex-end'
    Row: paddingVertical 8, borderBottomWidth 1, borderColor Colors.glass.borderLight
  
  Mock values:
    Open: 1,396.50 | Prev. Close: 1,389.40
    Volume: 1,93,11,971 | Avg. Volume: 1,45,00,000
    Lower Circuit: 1,250.50 | Upper Circuit: 1,528.30
9.5B: Fundamentals Section
less
Copy code
SectionHeader: title="Fundamentals", icon="grid-outline"

GlassCard:
  2-column grid of fundamental metrics
  Each row has 2 metrics side by side

  LAYOUT for each metric pair:
    Row:
      LEFT (flex 1):
        Label — Typography.bodySmall, Colors.text.tertiary
        Value — Typography.priceSmall, Colors.text.primary, marginTop 2
      RIGHT (flex 1, alignItems flex-end):
        Label — Typography.bodySmall, Colors.text.tertiary
        Value — Typography.priceSmall, Colors.text.primary, marginTop 2
    paddingVertical: 10
    borderBottom: 1px Colors.glass.borderLight (except last row)

  Rows:
    Mkt Cap: ₹18,80,746Cr   |   ROE: 9.47%
    P/E Ratio(TTM): 19.24   |   EPS(TTM): 72.25
    P/B Ratio: 2.14          |   Div Yield: 0.40%
    Industry P/E: 15.03      |   Book Value: 648.28
  



--- continue from here

## CONTINUATION — ALL REMAINING SCREENS & SECTIONS

---

## 9. SCREEN 4: STOCK DETAIL (Continued)

### Section 9.5B: Fundamentals Section (continued)

yaml
Copy code
Debt to Equity: 0.43     |   Face Value: 10
TOTAL: 5 rows × 2 columns = 10 data points
Exactly like the Groww screenshot attached — clean two-column key-value pairs

yaml
Copy code

---

#### 9.5C: Financials Section

marginTop: Spacing.section.gap

SectionHeader:
title="Financials"
subtitle="All values are in Cr"
icon="bar-chart-outline"

TabSelector variant="pill" (inline, below header):
Row 1 - Data type: ["Revenue", "Profit", "Net Worth"]
Row 2 - Period: ["Quarterly", "Yearly"]

Both rows of pills. First row selects WHICH metric.
Second row selects the TIME period.

Layout:
Row 1: Three pill buttons for metric selection, marginBottom 10
Row 2: Two pill buttons for period, marginBottom 14

CHART: BarChart component
height: 200

Data source:
Based on selected metric + period combination from MOCK_STOCK_DETAIL.financials
e.g., if Revenue + Quarterly selected → financials.revenue.quarterly

Bar configuration:
barWidth: 40
spacing: 24
barBorderTopLeftRadius: 6
barBorderTopRightRadius: 6
frontColor: Colors.bullish
gradientColor: Colors.bullishLight
showGradient: true

Value labels on top of each bar:
Typography.priceTiny
Formatted: e.g., "2,93,043"
color: Colors.text.secondary

X-axis labels: period names (Q1 FY25, Q2 FY25, etc.)
Typography.caption, fontSize 10
color: Colors.text.disabled

Background: transparent
No Y-axis
Animated bar growth on mount and when switching metric/period

Below chart: marginTop 8
Row showing growth:
"QoQ Growth: +3.7%" — Typography.bodySmall, Colors.bullish (if positive)
OR "YoY Growth: +18.0%"

yaml
Copy code

---

#### 9.5D: About Company Section

marginTop: Spacing.section.gap

SectionHeader:
title="About Company"
icon="business-outline"
Collapsible: chevron icon on right, toggles expand/collapse

GlassCard:
KEY-VALUE rows (single column, full width each):

yaml
Copy code
Each row:
  Row layout: [Label left] [Spacer] [Value right]
  paddingVertical: 10
  borderBottom: 1px Colors.glass.borderLight
  
  Label: Typography.body, Colors.text.tertiary
  Value: Typography.body, fontWeight 600, Colors.text.primary

Rows:
  MD/CEO         →  Mukesh D. Ambani
  Founded in     →  1973
  NSE Symbol     →  RELIANCE
DESCRIPTION: marginTop 12
Typography.bodySmall, color Colors.text.tertiary, lineHeight 20
Show first 3 lines with "Read more" link

vbnet
Copy code
"Read more" link:
  Typography.bodySmall, fontWeight 600, color Colors.accent
  textDecorationLine: 'underline', dotted style
  On press: expand to full text with animated height transition
  Changes to "Read less" when expanded
Collapsed state: show only the key-value rows
Expanded state (default): show key-value rows + description

yaml
Copy code

---

#### 9.5E: Shareholding Pattern Section

marginTop: Spacing.section.gap

SectionHeader:
title="Shareholding Pattern"
icon="people-outline"
Collapsible chevron

TabSelector variant="pill" (period selection):
tabs: ["Dec '25", "Sep '25", "Jun '25", "Mar '25", "Dec '24"]
Scrollable horizontal
Default: first (latest)

ShareholdingBar component:
data: [
{ label: 'Promoters', value: 50.01, color: Colors.bullish },
{ label: 'FIIs', value: 19.09, color: Colors.info },
{ label: 'Retail', value: 10.73, color: Colors.accent },
{ label: 'DIIs', value: 10.66, color: Colors.warning },
{ label: 'Others', value: 9.51, color: Colors.neutral },
]

Shows:
1. Horizontal stacked bar (full width, 10px height, colored segments)
2. Legend rows below with:
[Color dot] [Label] [Spacer] [Proportional mini bar] [Percentage]

When user switches period tab:
Bar segments animate to new proportions
Use Reanimated withTiming for smooth width transitions

Mock data for different periods (slight variations):
Dec '25: Promoters 50.01, FIIs 19.09, Retail 10.73, DIIs 10.66, Others 9.51
Sep '25: Promoters 50.05, FIIs 18.85, Retail 10.92, DIIs 10.48, Others 9.70
Jun '25: Promoters 50.09, FIIs 18.62, Retail 11.05, DIIs 10.34, Others 9.90

yaml
Copy code

---

#### 9.5F: Similar Stocks Section

marginTop: Spacing.section.gap
marginBottom: Spacing.massive (bottom spacing for scroll)

SectionHeader:
title="Similar Stocks"
icon="layers-outline"

GlassCard:
FlatList/map of MiniStockRow components
Data: MOCK_STOCK_DETAIL.similarStocks

Each row:
LEFT: stock logo circle (first letter of company in colored circle, 32x32)
backgroundColor: generated from symbol hash (pastel colors)
Letter: white, fontSize 14, fontWeight 700

vbnet
Copy code
CENTER (flex 1, marginLeft 10):
  Company name — Typography.body, Colors.text.primary
  (Full name, not just symbol)

RIGHT:
  Price — Typography.priceSmall, Colors.text.primary
  PriceChangeText — size "xs"
  
Each row: paddingVertical 12
Separator: 1px Colors.glass.borderLight

Each row pressable → navigate to stock/[thatSymbol]
Haptic feedback on press

yaml
Copy code

---

### Section 9.6: TECHNICALS TAB CONTENT

Visible when "Technicals" tab is active.
All sections below stacked vertically.
paddingHorizontal: Spacing.screen.paddingHorizontal

shell
Copy code

#### 9.6A: Technical Summary (Sentiment Gauge)

marginTop: Spacing.section.gap

SentimentGauge component:
bearishCount: 9
neutralCount: 1
bullishCount: 3
overallLabel: "Moderately Bearish"
overallScore: 3.2

Full implementation as described in Component 4J above.

Additional detail below the gauge (inside same card):
marginTop 12
Row:
"Based on 1D data" — Typography.caption, Colors.text.disabled
[Spacer]
Info icon button: onPress shows a tooltip explaining the gauge

Animation:
On mount: bars appear one by one from left to right (stagger 30ms each)
The triangle marker slides in from left to its position over 600ms

yaml
Copy code

---

#### 9.6B: Technical Indicators Table

marginTop: Spacing.section.gap

SectionHeader:
title="Indicators"
icon="analytics"
Right side: info icon (ℹ️) button

GlassCard:
TABLE HEADER ROW:
Three columns:
"INDICATOR" — Typography.labelSmall, Colors.text.disabled, left-aligned
"VALUE" — Typography.labelSmall, Colors.text.disabled, center-aligned
"VERDICT" — Typography.labelSmall, Colors.text.disabled, right-aligned
paddingBottom: 8
borderBottom: 1px Colors.glass.borderMedium

TABLE BODY:
Map of IndicatorRow components for each indicator:

sql
Copy code
Row 1: RSI (14)     |  +47.54  |  Neutral        (Colors.text.tertiary)
Row 2: MACD (12,26,9)| -2.19   |  Bearish        (Colors.bearish)
Row 3: Beta          |  +1.25  |  Highly volatile (Colors.warning)
Row 4: ADX (14)      |  22.30  |  Weak trend     (Colors.text.tertiary)
Row 5: ATR (14)      |  28.45  |  Moderate       (Colors.text.tertiary)
Row 6: CCI (20)      |  -85.30 |  Bearish        (Colors.bearish)

Each row uses IndicatorRow component (spec 4K)
Values should be in mono font for alignment
Verdict text color matches verdictType:
'bullish' → Colors.bullish
'bearish' → Colors.bearish
'neutral' → Colors.text.tertiary
'warning' → Colors.warning

yaml
Copy code

---

#### 9.6C: Support and Resistance

marginTop: Spacing.section.gap

SupportResistanceCard component (spec 4L):
levels: MOCK_STOCK_DETAIL.technicals.supportResistance
currentPrice: 1404.80

EXACT LAYOUT matching Groww screenshot:

GlassCard:
Title: "Support and Resistance" + ℹ️ icon

yaml
Copy code
VISUAL TABLE:
  Vertical list from top to bottom:
  
  R3 ────────────────────── 1,409.36
  
  ┌─────────────────────────────────┐
  │     PRICE 1,404.80              │  ← Green/accent pill, full width
  └─────────────────────────────────┘
  
  R2 ────────────────────── 1,381.18
  R1 ────────────────────── 1,363.36
  
  ┌─────────────────────────────────┐
  │     PIVOT 1,335.18              │  ← Gray pill, full width
  └─────────────────────────────────┘
  
  S1 ────────────────────── 1,317.36
  S2 ────────────────────── 1,289.18
  S3 ────────────────────── 1,271.36

Each level row:
  Row: [Label left, 30px] [Dashed line expanding] [Value right]
  Label: Typography.label, fontWeight 700
    R-levels: color Colors.bearish (resistance is ceiling)
    S-levels: color Colors.bullish (support is floor)
  Dashed line: flex 1, borderBottomWidth 1, borderStyle 'dashed', Colors.glass.borderLight
  Value: Typography.priceSmall, Colors.text.primary
  
  paddingVertical: 10

PRICE pill (positioned between correct levels):
  Determine where currentPrice falls among the levels
  Insert the pill at that vertical position
  Pill: 
    backgroundColor: Colors.accent (or Colors.bullish)
    paddingVertical: 5
    borderRadius: 4
    Text: "PRICE 1,404.80" — Typography.labelSmall, fontWeight 800, white, centered
    Full width
    marginVertical: 4
  
  Horizontal lines extending from pill edges (left and right)
    Color: Colors.accent at 40% opacity
    Style: solid

PIVOT pill:
  Similar to PRICE but:
    backgroundColor: Colors.text.muted
    Smaller text
    Text: "PIVOT 1,335.18"
yaml
Copy code

---

#### 9.6D: Moving Averages Table

marginTop: Spacing.section.gap

SectionHeader:
title="Moving Averages"
icon="trending-up"
ℹ️ info icon

GlassCard:
TABLE HEADER:
Three columns:
"PERIOD" — Typography.labelSmall, Colors.text.disabled, left
"MA" — Typography.labelSmall, Colors.text.disabled, center
"EMA" — Typography.labelSmall, Colors.text.disabled, right
paddingBottom: 8
borderBottom: 1px Colors.glass.borderMedium

TABLE BODY (each row):
Period | MA value | EMA value

yaml
Copy code
10D  |  1,397.26  |  1,395.47
20D  |  1,419.58  |  1,408.82
50D  |  1,447.21  |  1,437.20
100D |  1,478.04  |  1,449.27
200D |  1,449.39  |  1,435.79

Period: Typography.body, Colors.text.secondary

MA/EMA values COLOR LOGIC:
  If value < currentPrice (1,404.80): Colors.bullish (price above MA = bullish)
  If value > currentPrice: Colors.bearish (price below MA = bearish)

So for this data:
  10D MA: 1,397.26 < 1,404.80 → GREEN (bullish, price is above)
  20D MA: 1,419.58 > 1,404.80 → RED (bearish, price is below)
  50D MA: 1,447.21 > 1,404.80 → RED
  100D MA: 1,478.04 > 1,404.80 → RED
  200D MA: 1,449.39 > 1,404.80 → RED
  
Same logic for EMA column

Typography.priceSmall for values
Each row: paddingVertical 12, borderBottom 1px Colors.glass.borderLight
yaml
Copy code

---

#### 9.6E: Delivery Volume Section

marginTop: Spacing.section.gap
marginBottom: Spacing.massive

SectionHeader:
title="Delivery Volume"
icon="layers-outline"
ℹ️ info icon

TabSelector variant="pill":
tabs: ["Daily", "Weekly", "Monthly"]
Default: Daily

GlassCard:
Header label: "LAST 5 DAYS" — Typography.labelSmall, Colors.text.disabled

Stats column, marginTop 10:
Each stat row:
Row: [Color dot] [Label] [Spacer] [Value]
paddingVertical: 6

vbnet
Copy code
Row 1: 
  [Purple dot 6px] 
  "Total traded volume" — Typography.body, Colors.text.secondary
  "11,86,74,525" — Typography.priceSmall, Colors.text.primary

Row 2:
  [Blue dot 6px]
  "Delivery volume" — Typography.body, Colors.text.secondary
  "5,89,88,677" — Typography.priceSmall, Colors.text.primary
Divider: dashed line, marginVertical 10

Delivery percentage:
Row:
"Delivery percentage" — Typography.body, Colors.text.secondary
[Spacer]
"49.71%" — Typography.priceMedium, fontWeight 700, Colors.text.primary

Visual bar below:
Full width, height 8px, borderRadius 4
Track: Colors.glass.border
Fill: 49.71% width, gradient from Colors.info to Colors.infoLight
Animated fill width on mount

yaml
Copy code

---

### Section 9.7: NEWS TAB CONTENT (Stock-specific)

Visible when "News" tab is active.
paddingHorizontal: Spacing.screen.paddingHorizontal

Shows news filtered for this specific stock.

FlatList of NewsCard components (compact variant):
Data: MOCK_NEWS filtered to items where relatedStocks includes current symbol

If filtered list is short (< 3 items), also add general market news

Sort: by timestamp descending

ListEmptyComponent:
Centered:
[Newspaper icon, 48px, Colors.text.disabled]
"No recent news for {symbol}" — Typography.body, Colors.text.muted
"Check back later" — Typography.caption, Colors.text.disabled
marginVertical: 40

Each news item shows:
- Source with colored dot (sentiment)
- Timestamp as "X hours ago"
- Title (2-3 lines)
- Summary snippet (2 lines)
- Related stock badges (other stocks mentioned)

Exactly matching the Groww News tab screenshot

Pull-to-refresh enabled

marginBottom: Spacing.massive

yaml
Copy code

---

## 10. SCREEN 5: PREDICTIONS — Complete Specification

**File: `app/(tabs)/predictions.tsx`**

PURPOSE: Shows AI-generated trade predictions with targets, stop losses,
confidence scores, and AI reasoning. This is the intelligence layer of the app.

OVERALL LAYOUT:
LinearGradient background
ScrollView vertical

SECTIONS:
1. Header
2. Prediction Summary Stats
3. Active Predictions (main list)
4. Historical Performance Section
5. Prediction Accuracy Card

yaml
Copy code

---

### Section 10.1: Predictions Header

SafeAreaView top
paddingHorizontal: Spacing.screen.paddingHorizontal
Height: 56

Layout: Row
LEFT:
Row:
[Target/crosshair icon, 24px, Colors.warning]
marginLeft 8:
"AI Predictions" — Typography.h1
Below:
"Powered by AI analysis" — Typography.caption, Colors.text.muted

RIGHT:
[Filter icon button] [Settings icon button]
Glass button style

sql
Copy code
Filter: shows a bottom sheet with filters (Bullish only, Bearish only, 
High confidence only, Timeframe filter)
yaml
Copy code

---

### Section 10.2: Prediction Summary Stats

marginTop: 12
paddingHorizontal: Spacing.screen.paddingHorizontal

Horizontal ScrollView of stat cards (3 cards, peek-able):
gap: 10
Card width: (screenWidth - 32 - 20) / 2.5  (shows 2.5 cards)

CARD 1: Active Predictions
GlassCard variant="accent" padding="md"

Icon: target icon inside a gradient circle (28x28)
gradient: Colors.gradient.purple
Icon: white, 16px

Value: "5" — Typography.displaySmall, Colors.text.primary
Label: "Active" — Typography.labelSmall, Colors.text.muted

Mini detail: "3 Bullish · 2 Bearish" — Typography.caption
"3 Bullish" in Colors.bullish, "2 Bearish" in Colors.bearish

CARD 2: Success Rate
GlassCard variant="success" padding="md"

CircularProgress:
value: 72
size: 48
strokeWidth: 4
color: Colors.bullish
centerContent: "72%" in Typography.priceSmall

Label: "Success Rate" — Typography.labelSmall
Detail: "Last 30 days" — Typography.caption, Colors.text.disabled

CARD 3: Avg Return
GlassCard variant="default" padding="md"

Icon: trending-up icon, Colors.bullish

Value: "+4.8%" — Typography.displaySmall, Colors.bullish
Label: "Avg Return" — Typography.labelSmall
Detail: "Per prediction" — Typography.caption, Colors.text.disabled

yaml
Copy code

---

### Section 10.3: Active Predictions List

marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
title="Active Predictions"
icon="bulb-outline", iconColor: Colors.warning
action: { label: "History →", onPress: scroll to history section }

TabSelector variant="pill" (below header):
tabs: ["All", "Bullish 📈", "Bearish 📉", "High Conf."]
Filters the prediction list

PREDICTION CARDS LIST:
Map of PredictionCard components (spec 4P)
Gap: Spacing.card.gap (10) between cards

Each card uses the FULL PredictionCard specification from Section 4P:
- Header with direction badge + verdict badge
- Stock name and current price
- Target levels vertical track visualization
- Metrics row (Confidence ring, Risk:Reward, Timeframe)
- AI reasoning expandable
- Footer with timestamp

Data: MOCK_PREDICTIONS array (provide at least 4-5 predictions)

Add these additional mock predictions to fill the screen:

Prediction 3: HDFCBANK — Bearish
currentPrice: 1768.45
entryPrice: 1790.00
targets: [T1: 1740, T2: 1700, T3: 1650]
stopLoss: 1820
confidence: 65
timeframe: "Intraday"
riskReward: "1:1.8"
verdict: "Sell"
aiReasoning: "Bank Nifty showing weakness at resistance. HDFC Bank
failing to hold above 200-DMA. Increasing selling pressure from FIIs.
RSI divergence on 4H chart suggests downside momentum building."

Prediction 4: BAJFINANCE — Bullish
currentPrice: 7234.50
entryPrice: 7150.00
targets: [T1: 7400, T2: 7600, T3: 7900]
stopLoss: 7000
confidence: 71
timeframe: "Swing (3-5 days)"
riskReward: "1:3.5"
verdict: "Buy"
aiReasoning: "Strong volume breakout above consolidation zone.
Consumer lending growth robust. Technical pattern: Cup and handle
formation on daily chart. MACD crossover confirmed."

Prediction 5: INFY — Bullish
currentPrice: 1892.60
entryPrice: 1870.00
targets: [T1: 1950, T2: 2020, T3: 2100]
stopLoss: 1830
confidence: 85
timeframe: "Positional (2-4 weeks)"
riskReward: "1:3.0"
verdict: "Strong Buy"
aiReasoning: "IT sector in strong uptrend post Fed commentary.
Infosys deal wins accelerating. Revenue guidance raised. Price
breaking above multiple moving averages with volume. Sector
rotation clearly favoring tech."

EACH CARD animated with stagger: index * 150ms delay

yaml
Copy code

---

### Section 10.4: Historical Performance Section

marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
title="Prediction History"
icon="time-outline", iconColor: Colors.info

TabSelector variant="pill":
tabs: ["All", "Hits ✅", "Misses ❌"]

GlassCard:
LIST of past predictions (compact format):

Each historical item:
Row layout, paddingVertical 12, borderBottom 1px

sql
Copy code
LEFT section:
  Row 1: [Direction badge sm] [Symbol — Typography.h3] [Spacer] [Outcome badge]
    Outcome badges:
      Hit: Badge "TARGET HIT" variant="bullish" size="sm"
      Miss: Badge "SL HIT" variant="bearish" size="sm"
      Partial: Badge "PARTIAL" variant="warning" size="sm"
  
  Row 2: marginTop 4
    "Entry: ₹4,100 → Exit: ₹4,250" — Typography.bodySmall, Colors.text.tertiary
  
  Row 3: marginTop 2
    Row:
      "Return: +3.7%" — Typography.priceSmall, Colors.bullish (or bearish)
      [Spacer]
      "Dec 15, 2025" — Typography.caption, Colors.text.disabled
MOCK HISTORICAL DATA (at least 6 entries):
1. TCS — BUY — Entry 3950 → Exit 4180 — +5.8% — Hit ✅ — Nov 28
2. RELIANCE — BUY — Entry 1420 → Exit 1380 — -2.8% — SL Hit ❌ — Nov 25
3. HDFCBANK — SELL — Entry 1800 → Exit 1745 — +3.1% — Hit ✅ — Nov 22
4. INFY — BUY — Entry 1780 → Exit 1870 — +5.1% — Hit ✅ — Nov 18
5. ICICIBANK — BUY — Entry 1310 → Exit 1340 — +2.3% — Partial 🟡 — Nov 14
6. WIPRO — SELL — Entry 320 → Exit 335 — -4.7% — SL Hit ❌ — Nov 10
7. TATAMOTORS — BUY — Entry 690 → Exit 745 — +7.9% — Hit ✅ — Nov 5
8. SBIN — BUY — Entry 810 → Exit 842 — +3.9% — Hit ✅ — Oct 30

yaml
Copy code

---

### Section 10.5: Prediction Accuracy Card

marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal
marginBottom: Spacing.massive

GlassCard variant="elevated" gradient=true

Title: "AI Performance" — Typography.h2
Subtitle: "Last 30 predictions" — Typography.caption, Colors.text.muted

Layout: 3-column stat row + chart

STAT ROW: marginTop 14
Three columns, equal width, center-aligned:

Column 1:
Value: "72%" — Typography.displaySmall, Colors.bullish
Label: "Accuracy" — Typography.labelSmall

Column 2:
Value: "22" — Typography.displaySmall, Colors.bullish

Label: "Wins" — Typography.labelSmall

Column 3:
Value: "8" — Typography.displaySmall, Colors.bearish
Label: "Losses" — Typography.labelSmall

Separated by thin vertical dividers (1px, Colors.glass.borderLight, full column height)

CHART: marginTop 16
Horizontal bar showing win/loss ratio visually:
Full width, height 12px, borderRadius 6
Green portion: 72% (wins) — gradient Colors.gradient.green
Red portion: 28% (losses) — gradient Colors.gradient.red
Small gap (2px) between green and red

ADDITIONAL STATS: marginTop 14
2-column grid:
"Avg Win: +4.2%" | "Avg Loss: -2.1%"
"Best: +12.3% (TATAMOTORS)" | "Worst: -5.8% (COALINDIA)"
"Avg Duration: 6.2 days" | "Risk:Reward: 1:2.4"

Same styling as fundamentals grid (label + value rows)
Win values in green, loss values in red

yaml
Copy code

---

## 11. SCREEN 6: ALERTS — Complete Specification

**File: `app/(tabs)/alerts.tsx`**

PURPOSE: Manage price alerts. See active alerts, triggered alerts,
create new ones. Push notifications fire when alerts are triggered.

OVERALL LAYOUT:
LinearGradient background
ScrollView vertical (or SectionList)

SECTIONS:
1. Header
2. Alert Summary Stats
3. Triggered Alerts (recent)
4. Active Alerts List
5. Expired Alerts (collapsible)
6. FAB: Create New Alert

yaml
Copy code

---

### Section 11.1: Alerts Header

SafeAreaView top
paddingHorizontal: Spacing.screen.paddingHorizontal

Layout: Row
LEFT:
Row:
[Bell icon, 24px, Colors.bullish]
marginLeft 8:
"Alerts" — Typography.h1
Below:
"Price alerts & notifications" — Typography.caption, Colors.text.muted

RIGHT:
[Add/Plus icon button — primary action to create alert]
This button stands out more than other header buttons:
GradientButton variant="primary" size="sm"
Icon: "add" + text "New"
OR just a gradient circle with + icon

yaml
Copy code

---

### Section 11.2: Alert Summary Stats

marginTop: 12
paddingHorizontal: Spacing.screen.paddingHorizontal

Row of 3 mini stat cards (equal width, gap 8):

CARD 1: Active
GlassCard padding="sm"

Row: [Pulsing green dot] [Count]
Value: "5" — Typography.displaySmall, Colors.bullish
Label: "Active" — Typography.labelSmall
backgroundColor tint: Colors.bullishBg

CARD 2: Triggered (today)
GlassCard padding="sm"

Row: [Check icon, amber] [Count]
Value: "2" — Typography.displaySmall, Colors.warning
Label: "Triggered" — Typography.labelSmall
backgroundColor tint: Colors.warningBg

CARD 3: Total
GlassCard padding="sm"

Value: "23" — Typography.displaySmall, Colors.text.primary
Label: "All Time" — Typography.labelSmall

yaml
Copy code

---

### Section 11.3: Recently Triggered Alerts

marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
title="Recently Triggered"
icon="checkmark-circle", iconColor: Colors.bullish
Badge next to title: "2 new" variant="warning" size="sm"

List of triggered AlertCard components:

MOCK DATA — TRIGGERED ALERTS:

Alert 1:
symbol: "RELIANCE"
stockName: "Reliance Industries"
type: "price_above"
targetValue: 1400.00
currentPrice: 1404.80
status: "triggered"
createdAt: 2 days ago
triggeredAt: 45 minutes ago
note: "Breakout above resistance"

Alert 2:
symbol: "TCS"
stockName: "Tata Consultancy Services"
type: "target_hit"
targetValue: 4180.00
currentPrice: 4185.30
status: "triggered"
createdAt: 5 days ago
triggeredAt: 2 hours ago
note: "AI prediction target T1"

Each card uses the FULL Alert

Continuing from the Triggered Alerts section:

markdown
Copy code
Each card uses the FULL AlertCard specification from Section 4Q:
  - Status indicator (triggered = green check)
  - Type icon + label
  - Stock info + current price
  - Progress bar showing target was reached
  - Triggered info banner ("Triggered at ₹1,400 on...")
  - Note if exists
  - Timestamp footer
  
  ADDITIONAL VISUAL for triggered cards:
    The entire card has a very subtle pulsing glow effect:
      Reanimated loop:
        borderColor opacity: 0.15 → 0.35 → 0.15 over 2 seconds
        borderColor: Colors.bullish
    This draws attention to newly triggered alerts
    
  Gap between cards: Spacing.card.gap
Section 11.4: Active Alerts List
yaml
Copy code
marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title="Active Alerts"
  icon="notifications-outline", iconColor: Colors.accent
  action: { label: "Clear All", onPress: confirmation dialog }

List of active AlertCard components:

MOCK DATA — ACTIVE ALERTS:

  Alert 3:
    symbol: "HDFCBANK"
    stockName: "HDFC Bank"
    type: "price_below"
    targetValue: 1740.00
    currentPrice: 1768.45
    status: "active"
    createdAt: 1 day ago
    note: "Support zone watch — AI prediction target"

  Alert 4:
    symbol: "INFY"
    stockName: "Infosys"
    type: "price_above"
    targetValue: 1950.00
    currentPrice: 1892.60
    status: "active"
    createdAt: 3 days ago
    note: "Breakout confirmation level"

  Alert 5:
    symbol: "BAJFINANCE"
    stockName: "Bajaj Finance"
    type: "percentage_change"
    targetValue: 5.00  // 5% move
    currentPrice: 7234.50
    status: "active"
    createdAt: 12 hours ago
    note: "Volatility alert — earnings day"

  Alert 6:
    symbol: "SBIN"
    stockName: "State Bank of India"
    type: "price_above"
    targetValue: 860.00
    currentPrice: 842.30
    status: "active"
    createdAt: 4 days ago
    note: null

  Alert 7:
    symbol: "TATAMOTORS"
    stockName: "Tata Motors"
    type: "stop_loss_hit"
    targetValue: 720.00
    currentPrice: 745.20
    status: "active"
    createdAt: 2 days ago
    note: "Protective stop for swing trade"

Each active card:
  - Pulsing green dot for status
  - Shows progress bar: how close current price is to target
  - Distance percentage displayed (e.g., "3.2% away")
  - Swipe-to-delete gesture (react-native-gesture-handler Swipeable):
    Swipe left reveals red "Delete" button
    backgroundColor: Colors.bearish
    Icon: trash icon, white
    On complete swipe: haptic + remove with animated collapse
    
  - Long press: shows context menu with options:
    "Edit Alert", "Disable", "Delete"
    
  Gap between cards: Spacing.card.gap
Section 11.5: Expired Alerts (Collapsible)
less
Copy code
marginTop: Spacing.section.gap
paddingHorizontal: Spacing.screen.paddingHorizontal

SectionHeader:
  title="Expired"
  icon="time-outline", iconColor: Colors.text.muted
  Right side: Chevron (up/down) — toggles section visibility
  action: { label: "Clear", onPress: clear all expired }
  
  Collapsed by default. Tap header row to expand.

When expanded:
  List of expired AlertCard components with opacity 0.6

MOCK DATA — EXPIRED ALERTS:

  Alert 8:
    symbol: "WIPRO"
    stockName: "Wipro"
    type: "price_above"
    targetValue: 330.00
    currentPrice: 312.45
    status: "expired"
    createdAt: 2 weeks ago
    note: "Recovery play — didn't hit"

  Alert 9:
    symbol: "COALINDIA"
    stockName: "Coal India"
    type: "price_below"
    targetValue: 400.00
    currentPrice: 412.30
    status: "expired"
    createdAt: 10 days ago
    note: null

  Each expired card:
    - Gray circle with dash icon for status
    - Overall opacity: 0.55
    - No progress bar animation
    - Delete button visible directly (no need to swipe)

  Animate expand/collapse:
    Reanimated layout animation: height from 0 → auto
    FadeIn for content
    Duration: 300ms
Section 11.6: Create New Alert Modal/Bottom Sheet
yaml
Copy code
TRIGGERED BY: 
  - Header "New" button
  - "Create New Alert" FAB (if we add one)
  - "Add Alert" from stock detail screen

PRESENTATION: Bottom Sheet (react-native-bottom-sheet or custom)
  Slides up from bottom
  Height: ~70% of screen
  Backdrop: semi-transparent dark overlay
  Handle bar at top: 36px wide, 4px tall, Colors.glass.borderMedium, centered
  Background: Colors.bg.tertiary with glass border at top
  borderTopLeftRadius: 24, borderTopRightRadius: 24

CONTENT LAYOUT:

  === HEADER ===
  paddingHorizontal: 20, paddingTop: 20
  
  Row:
    "Create Alert" — Typography.h1
    [Spacer]
    [Close X button — 32x32, glass style]

  === STOCK SELECTOR === marginTop: 20
  Label: "Stock" — Typography.labelSmall, Colors.text.muted
  
  SearchBar (or a pressable row that opens stock search):
    If no stock selected:
      Placeholder: "Search and select a stock..."
    If stock selected:
      Row: [Stock initial circle] [Symbol + Name] [Price] [Change button]
      
  === ALERT TYPE === marginTop: 20
  Label: "Alert Type" — Typography.labelSmall, Colors.text.muted, marginBottom 8
  
  Grid of type options (2x2):
    Each option: GlassCard padding="sm"
      Active: variant="accent", borderColor accent
      Inactive: variant="default"
      
    Option 1: [↑ icon] "Price Above"
    Option 2: [↓ icon] "Price Below"
    Option 3: [📊 icon] "% Change"
    Option 4: [🎯 icon] "Target Hit"
    
    Gap: 8 between cards
    Each: width 50% - gap, height: 56
    Icon + text centered vertically

  === TARGET VALUE === marginTop: 20
  Label: "Target Price" — Typography.labelSmall
  
  Input field:
    GlassCard style input
    height: 56
    Large font: Typography.priceLarge, fontSize 24
    Prefix: "₹" in Colors.text.muted
    Placeholder: "0.00"
    keyboardType: 'decimal-pad'
    
  Below input: 
    "Current price: ₹1,404.80 | Distance: 3.2%" 
    Typography.caption, Colors.text.tertiary
    
  Quick adjust buttons row:
    ["-5%"] ["-2%"] ["-1%"] ["+1%"] ["+2%"] ["+5%"]
    Each: small pill button
      paddingH: 10, paddingV: 4, borderRadius: 12
      backgroundColor: Colors.glass.bg
      borderWidth: 1, borderColor: Colors.glass.border
      Text: Typography.caption, Colors.text.secondary
    On press: adjusts target value relative to current price
    Active state: accent border

  === NOTE (optional) === marginTop: 16
  Label: "Note (optional)" — Typography.labelSmall
  
  TextInput:
    GlassCard style, multiline
    height: 72
    placeholder: "Add a note..."
    Typography.body
    maxLength: 200
    Character counter bottom-right: "0/200"

  === SUBMIT BUTTON === marginTop: 24, marginBottom: safeAreaBottom + 16
  
  GradientButton:
    variant="primary"
    fullWidth: true
    size="lg" (height 52)
    title: "Create Alert"
    icon: "notifications-outline"
    
    Disabled state if no stock selected or no target value
    
  On press:
    Haptic: notificationAsync(NotificationFeedbackType.Success)
    Add alert to store
    Dismiss bottom sheet with animation
    Show toast: "Alert created for {SYMBOL} at ₹{target}"
    
    Toast design:
      Position: top of screen, below safe area
      GlassCard variant="success" padding="sm"
      Row: [Check icon, green] [Toast message text]
      Auto-dismiss after 3 seconds
      Animated: slide down from top + fade in, slide up + fade out
12. ANIMATION & INTERACTION SPECIFICATIONS
12A. Screen Entrance Animations
less
Copy code
EVERY screen uses staggered entrance animations:

When a tab is selected and screen mounts:
  1. Header: FadeIn.duration(200)
  2. First section: FadeInDown.delay(50).duration(300).springify()
  3. Second section: FadeInDown.delay(100).duration(300).springify()
  4. Third section: FadeInDown.delay(150).duration(300).springify()
  ...continuing with 50ms increments

Within sections containing lists:
  Each item staggers with 80ms delay
  Animation: FadeInRight.delay(index * 80).duration(250).springify()

CARDS:
  Use Reanimated entering prop on each GlassCard:
    entering={FadeInUp.delay(animationDelay).duration(350).springify().damping(15)}
12B. Number Animations
vbnet
Copy code
ALL financial numbers should animate on mount and on data change:

AnimatedCounter behavior:
  - On mount: count up from 0 to target value over 800ms
  - On value change: 
    1. Flash background briefly (green if increase, red if decrease) — 150ms
    2. Animate number from old to new value over 400ms
    3. Ease: Easing.out(Easing.cubic)

Price Ticker (in dashboard indices strip):
  - When price changes, briefly flash the price text:
    Green flash for increase: text color → Colors.bullish for 200ms → back to normal
    Red flash for decrease: text color → Colors.bearish for 200ms → back to normal
  - Use useAnimatedStyle with a color interpolation
12C. Chart Animations
sql
Copy code
ALL charts animate on mount:

SparklineChart:
  - Path draws from left to right over 600ms
  - Use SVG animated strokeDasharray technique:
    Start: strokeDashoffset = totalPathLength
    End: strokeDashoffset = 0
    Duration: 600ms, Easing.out

BarChart:
  - Each bar grows from 0 height to final height
  - Stagger: each bar starts 50ms after the previous
  - Duration per bar: 400ms
  - Easing: spring with damping 12

CircularProgress:
  - Arc animates from 0° to target angle
  - Duration: 800ms
  - Easing: spring

Line Chart (P&L, stock detail):
  - Same path drawing animation as sparkline but slower (1000ms)
  - Area fill fades in after path completes: FadeIn.delay(800).duration(300)

SentimentGauge bars:
  - Each bar appears one by one from left to right
  - Stagger: 30ms per bar
  - Animation: ScaleY from 0 to 1 (grow from bottom)
  - Duration: 200ms per bar
12D. Interaction Feedback
yaml
Copy code
PRESSABLE elements:

Buttons (GradientButton):
  Press in: scale(0.97), opacity(0.9) — spring animation, duration 100ms
  Release: scale(1.0), opacity(1.0) — spring animation, damping 10
  Haptic: ImpactFeedbackStyle.Medium

Cards (GlassCard with onPress):
  Press in: scale(0.985), opacity(0.85) — timing 80ms
  Release: spring back, damping 15
  Haptic: ImpactFeedbackStyle.Light

Tab changes:
  Haptic: ImpactFeedbackStyle.Light
  Active indicator: layout animation with spring

Pull-to-refresh:
  Custom refresh control:
    Animated rotation of a custom loader (gradient ring)
    Ring: SVG circle with rotating gradient
    Haptic: ImpactFeedbackStyle.Medium when refresh triggers

Alert triggered notification (in-app):
  Haptic: NotificationFeedbackType.Success
  Banner slides down from top with spring animation
  Auto-dismiss after 4 seconds with fade-up

Long press on stock row:
  Haptic: ImpactFeedbackStyle.Heavy after 500ms
  Show context menu (preview card with quick actions)

Swipe to delete (alerts):
  Haptic: ImpactFeedbackStyle.Light when swipe threshold reached
  Haptic: NotificationFeedbackType.Warning on delete confirmation
12E. Transition Animations
sql
Copy code
Tab switching (bottom tabs):
  Cross-fade between tab content
  Duration: 200ms
  No horizontal slide (feels more premium with fade)

Stack navigation (to stock detail):
  Push: slide from right with slight fade
  Custom: card-style presentation on iOS (modal feel)
  Duration: 300ms

Bottom sheet (create alert):
  Slide up from bottom with spring
  Backdrop fades in: opacity 0 → 0.5
  Spring config: damping 20, stiffness 200

Tab content switch (Overview/Technicals/News within stock detail):
  Content: FadeIn.duration(200) when switching
  Tab indicator: animated translateX using withSpring
13. ADDITIONAL MOCK DATA
Add to src/data/mockData.ts:

typescript
Run Code
Copy code
// === P&L CHART DATA ===
export const MOCK_PNL_HISTORY = {
  '1W': generatePnLData(7, 280000, 287543),
  '1M': generatePnLData(30, 265000, 287543),
  '3M': generatePnLData(90, 252000, 287543),
  '6M': generatePnLData(180, 230000, 287543),
  '1Y': generatePnLData(365, 200000, 287543),
};

function generatePnLData(days: number, startValue: number, endValue: number) {
  const data = [];
  const dailyReturn = (endValue - startValue) / days;
  let current = startValue;
  
  for (let i = 0; i < days; i++) {
    // Add realistic noise: random daily variation of ±0.5-1.5%
    const noise = current * (Math.random() * 0.03 - 0.015);
    current += dailyReturn + noise;
    
    const date = new Date();
    date.setDate(date.getDate() - (days - i));
    
    data.push({
      value: Math.round(current * 100) / 100,
      date: date.toISOString().split('T')[0],
      label: i % Math.floor(days / 5) === 0 ? 
        date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '',
    });
  }
  return data;
}

// === SECTOR PERFORMANCE ===
export const MOCK_SECTORS = [
  { name: 'IT', change: 1.28, color: '#3B82F6' },
  { name: 'Banking', change: -0.44, color: '#8B5CF6' },
  { name: 'Pharma', change: 0.72, color: '#10B981' },
  { name: 'Auto', change: 1.85, color: '#F59E0B' },
  { name: 'Energy', change: 0.33, color: '#EF4444' },
  { name: 'FMCG', change: -0.18, color: '#EC4899' },
  { name: 'Metals', change: -1.12, color: '#64748B' },
  { name: 'Realty', change: 2.34, color: '#06B6D4' },
];

// === MARKET MOOD ===
export const MOCK_MARKET_MOOD = {
  score: 67,
  label: 'Greed',
  previousScore: 62,
  change: 5,
};

// === MARKET BREADTH ===
export const MOCK_MARKET_BREADTH = {
  advances: 1247,
  declines: 832,
  unchanged: 156,
  total: 2235,
};

// === EXTENDED STOCK LIST (for NIFTY 50 browsing) ===
export const MOCK_NIFTY50_STOCKS = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', price: 1404.80, change: 15.40, changePercent: 1.11, sparkline: [1389, 1392, 1395, 1390, 1398, 1402, 1400, 1404] },
  { symbol: 'TCS', name: 'Tata Consultancy', price: 4185.30, change: 64.80, changePercent: 1.57, sparkline: [4120, 4130, 4145, 4140, 4160, 4170, 4180, 4185] },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 1768.45, change: -11.55, changePercent: -0.65, sparkline: [1780, 1778, 1775, 1772, 1770, 1773, 1769, 1768] },
  { symbol: 'INFY', name: 'Infosys', price: 1892.60, change: 28.40, changePercent: 1.52, sparkline: [1864, 1868, 1872, 1875, 1880, 1885, 1890, 1892] },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', price: 1345.75, change: 8.25, changePercent: 0.62, sparkline: [1337, 1338, 1340, 1339, 1342, 1344, 1345, 1345] },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever', price: 2456.30, change: -18.70, changePercent: -0.76, sparkline: [2475, 2472, 2468, 2465, 2460, 2458, 2457, 2456] },
  { symbol: 'SBIN', name: 'State Bank of India', price: 842.30, change: 12.70, changePercent: 1.53, sparkline: [830, 832, 835, 837, 838, 840, 841, 842] },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel', price: 1687.90, change: 23.50, changePercent: 1.41, sparkline: [1664, 1668, 1672, 1675, 1680, 1683, 1685, 1687] },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', price: 1834.20, change: -5.80, changePercent: -0.32, sparkline: [1840, 1839, 1837, 1836, 1835, 1834, 1835, 1834] },
  { symbol: 'ITC', name: 'ITC Limited', price: 467.85, change: 3.25, changePercent: 0.70, sparkline: [464, 465, 466, 465, 467, 467, 468, 467] },
  { symbol: 'LT', name: 'Larsen & Toubro', price: 3567.40, change: 45.60, changePercent: 1.29, sparkline: [3520, 3530, 3540, 3535, 3550, 3555, 3560, 3567] },
  { symbol: 'AXISBANK', name: 'Axis Bank', price: 1178.90, change: 14.30, changePercent: 1.23, sparkline: [1164, 1166, 1168, 1170, 1172, 1175, 1177, 1178] },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance', price: 7234.50, change: 198.60, changePercent: 2.82, sparkline: [7035, 7060, 7100, 7120, 7150, 7180, 7210, 7234] },
  { symbol: 'MARUTI', name: 'Maruti Suzuki', price: 12456.70, change: -234.50, changePercent: -1.85, sparkline: [12690, 12670, 12620, 12580, 12540, 12500, 12470, 12456] },
  { symbol: 'TATAMOTORS', name: 'Tata Motors', price: 745.20, change: 24.80, changePercent: 3.44, sparkline: [720, 724, 728, 730, 735, 738, 742, 745] },
  { symbol: 'SUNPHARMA', name: 'Sun Pharma', price: 1823.45, change: 15.30, changePercent: 0.85, sparkline: [1808, 1810, 1812, 1815, 1818, 1820, 1822, 1823] },
  { symbol: 'WIPRO', name: 'Wipro', price: 312.45, change: -4.30, changePercent: -1.36, sparkline: [317, 316, 315, 314, 313, 312, 313, 312] },
  { symbol: 'HCLTECH', name: 'HCL Technologies', price: 1945.80, change: 32.60, changePercent: 1.70, sparkline: [1913, 1918, 1923, 1928, 1932, 1938, 1942, 1945] },
  { symbol: 'ADANIENT', name: 'Adani Enterprises', price: 2456.80, change: 89.50, changePercent: 3.78, sparkline: [2367, 2380, 2395, 2410, 2425, 2440, 2450, 2456] },
  { symbol: 'NTPC', name: 'NTPC', price: 367.40, change: -11.20, changePercent: -2.96, sparkline: [379, 377, 375, 373, 371, 370, 368, 367] },
];

// === BANK NIFTY STOCKS ===
export const MOCK_BANKNIFTY_STOCKS = [
  { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 1768.45, change: -11.55, changePercent: -0.65, sparkline: [1780, 1778, 1775, 1772, 1770, 1773, 1769, 1768] },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', price: 1345.75, change: 8.25, changePercent: 0.62, sparkline: [1337, 1338, 1340, 1339, 1342, 1344, 1345, 1345] },
  { symbol: 'SBIN', name: 'State Bank of India', price: 842.30, change: 12.70, changePercent: 1.53, sparkline: [830, 832, 835, 837, 838, 840, 841, 842] },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', price: 1834.20, change: -5.80, changePercent: -0.32, sparkline: [1840, 1839, 1837, 1836, 1835, 1834, 1835, 1834] },
  { symbol: 'AXISBANK', name: 'Axis Bank', price: 1178.90, change: 14.30, changePercent: 1.23, sparkline: [1164, 1166, 1168, 1170, 1172, 1175, 1177, 1178] },
  { symbol: 'INDUSINDBK', name: 'IndusInd Bank', price: 987.60, change: -23.40, changePercent: -2.31, sparkline: [1011, 1008, 1004, 1000, 996, 992, 989, 987] },
];

// === FULL PREDICTION MOCK DATA ===
export const MOCK_PREDICTIONS = [
  {
    id: '1',
    symbol: 'RELIANCE',
    name: 'Reliance Industries',
    currentPrice: 1404.80,
    entryPrice: 1395.00,
    targets: [
      { level: 'T1', price: 1440.00, status: 'pending' as const },
      { level: 'T2', price: 1480.00, status: 'pending' as const },
      { level: 'T3', price: 1530.00, status: 'pending' as const },
    ],
    stopLoss: 1355.00,
    confidence: 78,
    direction: 'bullish' as const,
    timeframe: 'Swing (5-7 days)',
    riskReward: '1:2.8',
    aiReasoning: 'Strong support at 1380 with RSI recovering from oversold zone. FII buying trend positive. Sector rotation favoring energy. MACD showing potential crossover on daily chart. Volume profile supports upward move.',
    createdAt: new Date(Date.now() - 86400000),
    verdict: 'Buy' as const,
  },
  {
    id: '2',
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    currentPrice: 4185.30,
    entryPrice: 4100.00,
    targets: [
      { level: 'T1', price: 4250.00, status: 'pending' as const },
      { level: 'T2', price: 4350.00, status: 'pending' as const },
      { level: 'T3', price: 4500.00, status: 'pending' as const },
    ],
    stopLoss: 4020.00,
    confidence: 82,
    direction: 'bullish' as const,
    timeframe: 'Positional (2-3 weeks)',
    riskReward: '1:3.2',
    aiReasoning: 'IT sector momentum strong post US Fed dovish stance. Q3 results beat estimates. Deal pipeline robust with \$12.2B TCV. Moving above 50-DMA with volume confirmation.',
    createdAt: new Date(Date.now() - 172800000),
    verdict: 'Strong Buy' as const,
  },
  {
    id: '3',
    symbol: 'HDFCBANK',
    name: 'HDFC Bank',
    currentPrice: 1768.45,
    entryPrice: 1790.00,
    targets: [
      { level: 'T1', price: 1740.00, status: 'pending' as const },
      { level: 'T2', price: 1700.00, status: 'pending' as const },
      { level: 'T3', price: 1650.00, status: 'pending' as const },
    ],
    stopLoss: 1820.00,
    confidence: 65,
    direction: 'bearish' as const,
    timeframe: 'Intraday',
    riskReward: '1:1.8',
    aiReasoning: 'Bank Nifty showing weakness at resistance. HDFC Bank failing to hold above 200-DMA. Increasing selling pressure from FIIs. RSI divergence on 4H chart suggests downside momentum building.',
    createdAt: new Date(Date.now() - 43200000),
    verdict: 'Sell' as const,
  },
  {
    id: '4',
    symbol: 'BAJFINANCE',
    name: 'Bajaj Finance',
    currentPrice: 7234.50,
    entryPrice: 7150.00,
    targets: [
      { level: 'T1', price: 7400.00, status: 'pending' as const },
      { level: 'T2', price: 7600.00, status: 'pending' as const },
      { level: 'T3', price: 7900.00, status: 'pending' as const },
    ],
    stopLoss: 7000.00,
    confidence: 71,
    direction: 'bullish' as const,
    timeframe: 'Swing (3-5 days)',
    riskReward: '1:3.5',
    aiReasoning: 'Strong volume breakout above consolidation zone. Consumer lending growth robust. Technical pattern: Cup and handle formation on daily chart. MACD crossover confirmed.',
    createdAt: new Date(Date.now() - 259200000),
    verdict: 'Buy' as const,
  },
  {
    id: '5',
    symbol: 'INFY',
    name: 'Infosys',
    currentPrice: 1892.60,
    entryPrice: 1870.00,
    targets: [
      { level: 'T1', price: 1950.00, status: 'pending' as const },
      { level: 'T2', price: 2020.00, status: 'pending' as const },
      { level: 'T3', price: 2100.00, status: 'pending' as const },
    ],
    stopLoss: 1830.00,
    confidence: 85,
    direction: 'bullish' as const,
    timeframe: 'Positional (2-4 weeks)',
    riskReward: '1:3.0',
    aiReasoning: 'IT sector in strong uptrend post Fed commentary. Infosys deal wins accelerating. Revenue guidance raised. Price breaking above multiple moving averages with volume. Sector rotation clearly favoring tech.',
    createdAt: new Date(Date.now() - 345600000),
    verdict: 'Strong Buy' as const,
  },
];

// === PREDICTION HISTORY ===
export const MOCK_PREDICTION_HISTORY = [
  { symbol: 'TCS', direction: 'bullish', entryPrice: 3950, exitPrice: 4180, returnPercent: 5.8, outcome: 'hit', date: '2025-11-28' },
  { symbol: 'RELIANCE', direction: 'bullish', entryPrice: 1420, exitPrice: 1380, returnPercent: -2.8, outcome: 'miss', date: '2025-11-25' },
  { symbol:




Continuing from the prediction history:

markdown
Copy code
  { symbol: 'HDFCBANK', direction: 'bearish', entryPrice: 1800, exitPrice: 1745, returnPercent: 3.1, outcome: 'hit', date: '2025-11-22' },
  { symbol: 'INFY', direction: 'bullish', entryPrice: 1780, exitPrice: 1870, returnPercent: 5.1, outcome: 'hit', date: '2025-11-18' },
  { symbol: 'ICICIBANK', direction: 'bullish', entryPrice: 1310, exitPrice: 1340, returnPercent: 2.3, outcome: 'partial', date: '2025-11-14' },
  { symbol: 'WIPRO', direction: 'bearish', entryPrice: 320, exitPrice: 335, returnPercent: -4.7, outcome: 'miss', date: '2025-11-10' },
  { symbol: 'TATAMOTORS', direction: 'bullish', entryPrice: 690, exitPrice: 745, returnPercent: 7.9, outcome: 'hit', date: '2025-11-05' },
  { symbol: 'SBIN', direction: 'bullish', entryPrice: 810, exitPrice: 842, returnPercent: 3.9, outcome: 'hit', date: '2025-10-30' },
  { symbol: 'ADANIENT', direction: 'bullish', entryPrice: 2300, exitPrice: 2456, returnPercent: 6.8, outcome: 'hit', date: '2025-10-25' },
  { symbol: 'BAJFINANCE', direction: 'bullish', entryPrice: 7000, exitPrice: 6850, returnPercent: -2.1, outcome: 'miss', date: '2025-10-20' },
];

// === ALERTS MOCK DATA ===
export const MOCK_ALERTS_TRIGGERED = [
  {
    id: 'a1',
    symbol: 'RELIANCE',
    stockName: 'Reliance Industries',
    type: 'price_above' as const,
    targetValue: 1400.00,
    currentPrice: 1404.80,
    status: 'triggered' as const,
    createdAt: new Date(Date.now() - 172800000),
    triggeredAt: new Date(Date.now() - 2700000), // 45 min ago
    note: 'Breakout above resistance',
  },
  {
    id: 'a2',
    symbol: 'TCS',
    stockName: 'Tata Consultancy Services',
    type: 'target_hit' as const,
    targetValue: 4180.00,
    currentPrice: 4185.30,
    status: 'triggered' as const,
    createdAt: new Date(Date.now() - 432000000),
    triggeredAt: new Date(Date.now() - 7200000), // 2 hours ago
    note: 'AI prediction target T1',
  },
];

export const MOCK_ALERTS_ACTIVE = [
  {
    id: 'a3',
    symbol: 'HDFCBANK',
    stockName: 'HDFC Bank',
    type: 'price_below' as const,
    targetValue: 1740.00,
    currentPrice: 1768.45,
    status: 'active' as const,
    createdAt: new Date(Date.now() - 86400000),
    note: 'Support zone watch — AI prediction target',
  },
  {
    id: 'a4',
    symbol: 'INFY',
    stockName: 'Infosys',
    type: 'price_above' as const,
    targetValue: 1950.00,
    currentPrice: 1892.60,
    status: 'active' as const,
    createdAt: new Date(Date.now() - 259200000),
    note: 'Breakout confirmation level',
  },
  {
    id: 'a5',
    symbol: 'BAJFINANCE',
    stockName: 'Bajaj Finance',
    type: 'percentage_change' as const,
    targetValue: 5.00,
    currentPrice: 7234.50,
    status: 'active' as const,
    createdAt: new Date(Date.now() - 43200000),
    note: 'Volatility alert — earnings day',
  },
  {
    id: 'a6',
    symbol: 'SBIN',
    stockName: 'State Bank of India',
    type: 'price_above' as const,
    targetValue: 860.00,
    currentPrice: 842.30,
    status: 'active' as const,
    createdAt: new Date(Date.now() - 345600000),
    note: null,
  },
  {
    id: 'a7',
    symbol: 'TATAMOTORS',
    stockName: 'Tata Motors',
    type: 'stop_loss_hit' as const,
    targetValue: 720.00,
    currentPrice: 745.20,
    status: 'active' as const,
    createdAt: new Date(Date.now() - 172800000),
    note: 'Protective stop for swing trade',
  },
];

export const MOCK_ALERTS_EXPIRED = [
  {
    id: 'a8',
    symbol: 'WIPRO',
    stockName: 'Wipro',
    type: 'price_above' as const,
    targetValue: 330.00,
    currentPrice: 312.45,
    status: 'expired' as const,
    createdAt: new Date(Date.now() - 1209600000),
    note: 'Recovery play — didn\'t hit',
  },
  {
    id: 'a9',
    symbol: 'COALINDIA',
    stockName: 'Coal India',
    type: 'price_below' as const,
    targetValue: 400.00,
    currentPrice: 412.30,
    status: 'expired' as const,
    createdAt: new Date(Date.now() - 864000000),
    note: null,
  },
];

// === ADDITIONAL STOCK DETAILS (for other stocks if navigated to) ===
export const MOCK_STOCK_DETAILS: Record<string, typeof MOCK_STOCK_DETAIL> = {
  'RELIANCE': MOCK_STOCK_DETAIL, // Already defined above
  'TCS': {
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    price: 4185.30,
    change: 64.80,
    changePercent: 1.57,
    performance: {
      todayLow: 4128.50,
      todayHigh: 4210.80,
      currentInRange: 0.69,
      weekLow52: 3311.05,
      weekHigh52: 4592.25,
      currentIn52Range: 0.68,
      open: 4135.00,
      prevClose: 4120.50,
      volume: 4523891,
      lowerCircuit: 3708.45,
      upperCircuit: 4532.55,
    },
    fundamentals: {
      mktCap: '15,12,456',
      roe: 48.82,
      peRatio: 33.12,
      eps: 126.38,
      pbRatio: 15.27,
      divYield: 1.24,
      industryPE: 30.45,
      bookValue: 274.02,
      debtToEquity: 0.07,
      faceValue: 1,
    },
    financials: {
      revenue: {
        quarterly: [
          { period: 'Q1 FY25', value: 62613 },
          { period: 'Q2 FY25', value: 64259 },
          { period: 'Q3 FY25', value: 63973 },
          { period: 'Q4 FY25', value: 65497 },
          { period: 'Q1 FY26', value: 67841 },
        ],
        yearly: [
          { period: 'FY21', value: 164177 },
          { period: 'FY22', value: 191754 },
          { period: 'FY23', value: 225458 },
          { period: 'FY24', value: 240893 },
          { period: 'FY25', value: 256342 },
        ],
      },
      profit: {
        quarterly: [
          { period: 'Q1 FY25', value: 11909 },
          { period: 'Q2 FY25', value: 12040 },
          { period: 'Q3 FY25', value: 12380 },
          { period: 'Q4 FY25', value: 12735 },
          { period: 'Q1 FY26', value: 13120 },
        ],
        yearly: [
          { period: 'FY21', value: 33388 },
          { period: 'FY22', value: 38327 },
          { period: 'FY23', value: 42147 },
          { period: 'FY24', value: 45908 },
          { period: 'FY25', value: 49064 },
        ],
      },
      netWorth: {
        quarterly: [
          { period: 'Q1 FY25', value: 88450 },
          { period: 'Q2 FY25', value: 90230 },
          { period: 'Q3 FY25', value: 92100 },
          { period: 'Q4 FY25', value: 94500 },
          { period: 'Q1 FY26', value: 96800 },
        ],
        yearly: [
          { period: 'FY21', value: 72042 },
          { period: 'FY22', value: 79800 },
          { period: 'FY23', value: 84126 },
          { period: 'FY24', value: 88450 },
          { period: 'FY25', value: 96800 },
        ],
      },
    },
    about: {
      ceo: 'K Krithivasan',
      founded: 1968,
      nseSymbol: 'TCS',
      description: 'Tata Consultancy Services is an Indian multinational information technology services and consulting company headquartered in Mumbai. It is a subsidiary of the Tata Group and operates in 150 locations across 46 countries. TCS is the second-largest Indian company by market capitalization.',
    },
    shareholding: {
      current: 'Dec \'25',
      periods: ['Dec \'25', 'Sep \'25', 'Jun \'25', 'Mar \'25', 'Dec \'24'],
      data: { promoters: 72.30, fiis: 12.45, retail: 6.82, diis: 5.43, others: 3.00 },
    },
    technicals: {
      summary: { bearishCount: 4, neutralCount: 3, bullishCount: 6, overall: 'Moderately Bullish', overallScore: 6.8 },
      indicators: [
        { name: 'RSI (14)', value: 58.32, verdict: 'Neutral', verdictColor: 'neutral' },
        { name: 'MACD (12,26,9)', value: 15.67, verdict: 'Bullish', verdictColor: 'bullish' },
        { name: 'Beta', value: 0.65, verdict: 'Low volatile', verdictColor: 'neutral' },
        { name: 'ADX (14)', value: 28.50, verdict: 'Trending', verdictColor: 'bullish' },
        { name: 'ATR (14)', value: 65.20, verdict: 'Moderate', verdictColor: 'neutral' },
        { name: 'CCI (20)', value: 42.10, verdict: 'Neutral', verdictColor: 'neutral' },
      ],
      supportResistance: {
        r3: 4280.50, r2: 4232.90, r1: 4209.10,
        pivot: 4161.50,
        s1: 4137.70, s2: 4090.10, s3: 4066.30,
        currentPrice: 4185.30,
      },
      movingAverages: [
        { period: '10D', ma: 4152.30, ema: 4160.45 },
        { period: '20D', ma: 4098.70, ema: 4110.20 },
        { period: '50D', ma: 4025.40, ema: 4045.80 },
        { period: '100D', ma: 3920.15, ema: 3960.30 },
        { period: '200D', ma: 3845.60, ema: 3890.40 },
      ],
      deliveryVolume: { totalTraded: 22567890, delivery: 13540734, deliveryPercent: 60.00 },
    },
    similarStocks: [
      { symbol: 'INFY', name: 'Infosys', price: 1892.60, change: 28.40, changePercent: 1.52 },
      { symbol: 'WIPRO', name: 'Wipro', price: 312.45, change: -4.30, changePercent: -1.36 },
      { symbol: 'HCLTECH', name: 'HCL Technologies', price: 1945.80, change: 32.60, changePercent: 1.70 },
      { symbol: 'LTIM', name: 'LTIMindtree', price: 5890.30, change: 145.70, changePercent: 2.53 },
      { symbol: 'TECHM', name: 'Tech Mahindra', price: 1678.90, change: 18.40, changePercent: 1.11 },
    ],
    priceHistory: [4050, 4060, 4075, 4070, 4090, 4100, 4095, 4110, 4120, 4115, 4130, 4135, 4140, 4145, 4150, 4155, 4160, 4170, 4175, 4185],
  },
};
14. IMPLEMENTATION TASK ORDER
Execute these tasks IN THIS EXACT ORDER. Each task must be FULLY COMPLETE before moving on. Every file must compile, every component must render, every screen must look pixel-perfect.

TASK 1: Foundation Setup
Priority: CRITICAL
Estimated components: 8 files

sql
Copy code
Files to create/modify:
  1. Clean up package.json — ensure all dependencies installed:
     expo-blur, expo-linear-gradient, expo-haptics, react-native-reanimated,
     react-native-gesture-handler, react-native-svg, 
     react-native-gifted-charts, @expo/vector-icons, date-fns

  2. src/theme/colors.ts — FULL color system (Section 3A above)
  3. src/theme/typography.ts — FULL typography system (Section 3B)
  4. src/theme/spacing.ts — FULL spacing system (Section 3C)
  5. src/theme/shadows.ts — FULL shadow system (Section 3D)
  6. src/theme/icons.ts — FULL icon mapping (Section 3E)
  7. src/theme/index.ts — Re-export everything:
     export * from './colors';
     export * from './typography';
     export * from './spacing';
     export * from './shadows';
     export * from './icons';
  8. src/data/mockData.ts — ALL mock data from Section 13 above
  9. src/utils/formatters.ts:
     - formatCurrency(value: number): string → ₹1,404.80
     - formatLargeNumber(value: number): string → 18,80,746
     - formatPercentage(value: number, showSign?: boolean): string → +1.11%
     - formatVolume(value: number): string → 1.93Cr
     - timeAgo(date: Date): string → "4 hours ago", "2 days ago"
     - formatCompact(value: number): string → 18.8L Cr
     All formatted in Indian number system (lakhs, crores)

  10. app/_layout.tsx — Root layout:
      - SafeAreaProvider
      - StatusBar: style="light", translucent, backgroundColor transparent
      - Background: LinearGradient using Colors.gradient.screenBg
      - Load fonts if needed

ACCEPTANCE CRITERIA:
  - All theme files import without errors
  - Mock data file imports correctly
  - Formatters return correct strings:
    formatCurrency(1404.80) → "₹1,404.80"
    formatLargeNumber(1880746) → "18,80,746"
    formatPercentage(1.11, true) → "+1.11%"
    timeAgo(30 min ago) → "30 min ago"
  - App opens to a dark gradient screen
TASK 2: Core UI Component Library
Priority: CRITICAL
Estimated components: 12 files

markdown
Copy code
Build every component in src/components/ui/ following the EXACT specifications 
from Section 4 above. Each component self-contained with embedded StyleSheet.

Files to create:
  1. src/components/ui/GlassCard.tsx (Section 4A)
  2. src/components/ui/SparklineChart.tsx (Section 4B)
  3. src/components/ui/PriceChangeText.tsx (Section 4C)
  4. src/components/ui/SectionHeader.tsx (Section 4D)
  5. src/components/ui/ProgressRangeBar.tsx (Section 4E)
  6. src/components/ui/AnimatedCounter.tsx (Section 4F)
  7. src/components/ui/Badge.tsx (Section 4G)
  8. src/components/ui/SearchBar.tsx (Section 4H)
  9. src/components/ui/TabSelector.tsx (Section 4I)
  10. src/components/ui/SentimentGauge.tsx (Section 4J)
  11. src/components/ui/CircularProgress.tsx (Section 4R)
  12. src/components/ui/MiniStockRow.tsx (Section 4N)
  13. src/components/ui/index.ts — Re-export all

ACCEPTANCE CRITERIA:
  - Create a temporary test screen that renders each component with mock data
  - GlassCard renders with visible blur, border, and correct padding for each variant
  - SparklineChart draws a smooth colored line with area fill from mock sparkline data
  - PriceChangeText shows green arrow + green text for positive, red for negative
  - SectionHeader shows icon + title + "See All →" action
  - ProgressRangeBar renders the track with triangle marker at correct position
  - AnimatedCounter counts up from 0 on mount
  - Badge renders colored pills for each variant
  - SearchBar shows glass input with focus border animation
  - TabSelector shows underline and pill variants with animated indicator
  - SentimentGauge shows the individual colored bars with triangle marker
  - CircularProgress shows animated ring filling up
  - MiniStockRow shows symbol, name, sparkline, price, change in a compact row
TASK 3: Extended UI Components
Priority: HIGH
Estimated components: 8 files

markdown
Copy code
Files to create:
  1. src/components/ui/IndicatorRow.tsx (Section 4K)
  2. src/components/ui/SupportResistanceCard.tsx (Section 4L)
  3. src/components/ui/BarChartWidget.tsx (Section 4M) — wrapper around gifted-charts
  4. src/components/ui/NewsCard.tsx (Section 4O)
  5. src/components/ui/PredictionCard.tsx (Section 4P)
  6. src/components/ui/AlertCard.tsx (Section 4Q)
  7. src/components/ui/ShareholdingBar.tsx (Section 4S)
  8. src/components/ui/GradientButton.tsx — Pressable with LinearGradient bg:
      Props: title, onPress, variant (primary/success/danger), size (sm/md/lg),
             icon?, loading?, disabled?, fullWidth?
      Gradient colors from variant
      Scale animation on press (0.97)
      Haptic feedback
      Loading spinner state

  Update: src/components/ui/index.ts — add new exports

ACCEPTANCE CRITERIA:
  - IndicatorRow renders three-column layout with colored verdict text
  - SupportResistanceCard renders the full S1-S3, R1-R3 visual with PRICE and PIVOT pills
  - BarChartWidget renders colored bars with value labels on top, animated growth
  - NewsCard compact variant shows sentiment dot, source, time, title, summary, stock chips
  - PredictionCard shows full layout: direction badge, targets track, confidence ring, AI reasoning
  - AlertCard shows status dot, type icon, progress bar, triggered info if applicable
  - ShareholdingBar shows stacked colored bar with legend rows below
  - GradientButton renders gradient background with press animation
TASK 4: Tab Bar Redesign
Priority: HIGH
Estimated files: 2

yaml
Copy code
Files to modify:
  1. app/(tabs)/_layout.tsx — Complete tab navigator redesign

IMPLEMENTATION:
  Follow Section 5 specification exactly.
  
  - Use @react-navigation/bottom-tabs with custom tabBar component
  - Create src/components/navigation/CustomTabBar.tsx:
  
  Custom tab bar component:
    Container:
      position: 'absolute', bottom: 0, left: 0, right: 0
      BlurView: intensity 80, tint 'dark'
      Overlay: LinearGradient from rgba(5,7,14,0.85) to rgba(5,7,14,0.95)
      Top border: 1px, Colors.glass.borderLight
      Height: 80 + SafeAreaInsets.bottom
      paddingBottom: SafeAreaInsets.bottom
    
    5 tab items in equal-width row:
    
    Each tab:
      Pressable, flex: 1, centered
      
      INACTIVE:
        Icon: 22px, Colors.text.disabled
        No label
        
      ACTIVE:
        Icon container:
          width: 42, height: 42, borderRadius: 13
          backgroundColor: tab accent color at 12% opacity
          Centered icon: 22px, tab accent color
          Glow shadow matching accent
        Label: Typography.tabLabel, tab accent color, marginTop: 2
        
    Tab accent colors:
      Dashboard: '#8B5CF6'
      News: '#3B82F6'
      Analysis: '#06B6D4'
      Predictions: '#F59E0B'
      Alerts: '#10B981'
    
    Alerts tab: notification badge
      Count badge: 16px red circle, white text "2"
      Position: top-right of icon container
      
    Animation:
      Active icon: entering bounceIn
      Haptic: light impact on tab press

  Tab screens configuration:
    tabBarActiveTintColor: Colors.accent
    headerShown: false (we use custom headers on each screen)
    tabBarStyle: { position: 'absolute' } // For transparency

  REMOVE: The floating gear/settings FAB from ALL screens

ACCEPTANCE CRITERIA:
  - Tab bar has blur background with gradient overlay
  - Active tab shows icon in colored container with glow
  - Inactive tabs show muted icons only
  - Each tab has a different accent color
  - Alerts tab shows red count badge
  - Haptic fires on tab change
  - Tab bar is translucent — screen content scrolls behind it
  - No floating settings button visible anywhere
TASK 5: Dashboard Screen — Complete Build
Priority: CRITICAL
Estimated files: 10+

javascript
Run Code
Copy code
Build the entire dashboard following Section 6 specification.

Files to create:
  1. src/components/dashboard/DashboardHeader.tsx (Section 6.1)
  2. src/components/dashboard/PortfolioHeroCard.tsx (Section 6.2)
  3. src/components/dashboard/MarketIndicesTicker.tsx (Section 6.3)
  4. src/components/dashboard/ActiveTradesSection.tsx (Section 6.4)
     — includes individual TradeCard subcomponent
  5. src/components/dashboard/WatchlistSection.tsx (Section 6.5)
  6. src/components/dashboard/BotStatusCard.tsx (Section 6.6)
  7. src/components/dashboard/HotNewsCarousel.tsx (Section 6.7)
  8. src/components/dashboard/TopMoversSection.tsx (Section 6.8)
  9. src/components/dashboard/PnLChart.tsx (Section 6.9)

  10. app/(tabs)/dashboard.tsx — Main screen assembling all components

SCREEN ASSEMBLY (dashboard.tsx):
  LinearGradient background (fullscreen, absolute)
  ScrollView:
    showsVerticalScrollIndicator: false
    contentContainerStyle: { paddingBottom: 120 } // Space for tab bar
    
  Component order (top to bottom):
    <DashboardHeader />                    // Sticky or in scroll
    <PortfolioHeroCard />                  // marginTop 8
    <MarketIndicesTicker />                // marginTop 14
    <ActiveTradesSection />                // marginTop 20
    <WatchlistSection />                   // marginTop 20
    <BotStatusCard />                      // marginTop 20
    <HotNewsCarousel />                    // marginTop 20
    <TopMoversSection />                   // marginTop 20
    <PnLChart />                           // marginTop 20, marginBottom 40

  All data from MOCK_DATA imports
  All cards use staggered entrance animations
  
ACCEPTANCE CRITERIA:
  - Screen is PACKED with content — user must scroll to see everything
  - Portfolio hero shows large ₹2,87,543.50 with green P&L
  - Market indices ticker scrolls horizontally with sparklines
  - Active trades show 3 trades with colored left borders and progress bars
  - Watchlist shows 6+ stocks with sparklines
  - Bot status shows circular progress ring (win rate)
  - News carousel snaps between cards, showing breaking news
  - Top movers switches between Gainers/Losers tabs
  - P&L chart renders animated line with area fill
  - ZERO empty space. ZERO placeholder text. Every pixel has content.
  - Scrollable content extends well below the fold
TASK 6: News Screen — Complete Build
Priority: HIGH
Estimated files: 5+

sql
Copy code
Build the entire news screen following Section 7 specification.

Files to create:
  1. src/components/news/NewsHeader.tsx (Section 7.1)
  2. src/components/news/BreakingNewsBanner.tsx (Section 7.2)
  3. src/components/news/CategoryFilterTabs.tsx (Section 7.3)
  4. src/components/news/NewsFeed.tsx (Section 7.4)
     — Uses NewsCard component from ui library
  
  5. app/(tabs)/news.tsx — Main screen assembly

SCREEN ASSEMBLY (news.tsx):
  LinearGradient background
  
  <NewsHeader />                           // SafeArea top
  <BreakingNewsBanner />                   // marginTop 8 (conditional)
  <CategoryFilterTabs />                   // marginTop 14
  <NewsFeed />                             // marginTop 14, flex 1

  NewsFeed is a FlatList:
    Data: MOCK_NEWS filtered by active category
    renderItem: NewsCard compact variant
    Pull-to-refresh enabled
    ListFooterComponent: "You're all caught up! ✅"
    
    Between every 4th item: inject trending stock inline card
    
  Category filter changes which news items are shown:
    'all': show all
    'market': filter where category === 'market'
    'economy': filter where category === 'economy'
    etc.

ACCEPTANCE CRITERIA:
  - Breaking news banner shows at top with pulsing flash icon
  - Category pills scroll horizontally with emoji
  - News feed shows 8+ news items with rich formatting
  - Each news item shows sentiment dot, source, time, title, summary
  - Related stock chips shown per news item
  - HIGH importance items show amber "HIGH" badge
  - Trending stock inline cards appear between news items
  - Pull-to-refresh works with custom indicator
  - Screen is information-dense, no empty space
TASK 7: Analysis Screen — Complete Build
Priority: HIGH
Estimated files: 7+

typescript
Run Code
Copy code
Build the analysis/discovery screen following Section 8 specification.

Files to create:
  1. src/components/analysis/AnalysisHeader.tsx (Section 8.1)
  2. src/components/analysis/SearchOverlay.tsx (Section 8.2)
  3. src/components/analysis/MarketOverviewCards.tsx (Section 8.3)
  4. src/components/analysis/SectorHeatmap.tsx (Section 8.4)
  5. src/components/analysis/TrendingStocksGrid.tsx (Section 8.5)
  6. src/components/analysis/StockCategoryList.tsx (Section 8.6)
  
  7. app/(tabs)/analysis.tsx — Main screen assembly

SCREEN ASSEMBLY (analysis.tsx):
  LinearGradient background
  
  STATE:
    isSearchFocused: boolean
    searchQuery: string
    
  LAYOUT:
    <AnalysisHeader with SearchBar />       // Top
    
    {isSearchFocused && searchQuery ? (
      <SearchOverlay query={searchQuery} />  // Absolute positioned overlay
    ) : (
      <ScrollView>
        <MarketOverviewCards />              // 2-column: Mood + Status
        <SectorHeatmap />                    // Grid of colored sector tiles
        <TrendingStocksGrid />              // Horizontal scroll of stock cards
        <StockCategoryList title="NIFTY 50" /> // Vertical stock list
        <StockCategoryList title="Bank NIFTY" /> // Another list
      </ScrollView>
    )}

  Navigation:
    When a stock is tapped (from any list/search/trending):
      router.push(`/stock/${symbol}`)
      This navigates to the Stock Detail screen (TASK 8)

ACCEPTANCE CRITERIA:
  - Search bar is prominent at top
  - Market mood gauge renders semi-circular meter
  - Market breadth shows advance/decline bar
  - Sector heatmap shows colored tiles (green for positive, red for negative)
  - Trending stocks show horizontal scrollable cards with sparklines
  - NIFTY 50 list shows 8+ stocks with sparklines and prices
  - Bank NIFTY list shows 6 banking stocks
  - Search overlay appears on focus with filtered results
  - Tapping any stock navigates to stock detail
  - Dense layout, lots of data visible
TASK 8: Stock Detail Screen — Complete Build
Priority: CRITICAL
Estimated files: 15+

markdown
Copy code
This is the most complex screen. Build following Sections 9.1-9.7.

Files to create:
  1. src/components/stockDetail/StockDetailHeader.tsx (Section 9.1)
  2. src/components/stockDetail/MiniPriceChart.tsx (Section 9.2)
  3. src/components/stockDetail/TimePeriodSelector.tsx (Section 9.3)
  4. src/components/stockDetail/PerformanceSection.tsx (Section 9.5A)
  5. src/components/stockDetail/FundamentalsSection.tsx (Section 9.5B)
  6. src/
   6. src/components/stockDetail/FinancialsSection.tsx (Section 9.5C)
  7. src/components/stockDetail/AboutCompanySection.tsx (Section 9.5D)
  8. src/components/stockDetail/ShareholdingSection.tsx (Section 9.5E)
  9. src/components/stockDetail/SimilarStocksSection.tsx (Section 9.5F)
  10. src/components/stockDetail/TechnicalSummarySection.tsx (Section 9.6A)
  11. src/components/stockDetail/IndicatorsSection.tsx (Section 9.6B)
  12. src/components/stockDetail/SupportResistanceSection.tsx (Section 9.6C)
  13. src/components/stockDetail/MovingAveragesSection.tsx (Section 9.6D)
  14. src/components/stockDetail/DeliveryVolumeSection.tsx (Section 9.6E)
  15. src/components/stockDetail/StockNewsSection.tsx (Section 9.7)

  16. app/stock/[symbol].tsx — Main stock detail screen

SCREEN ASSEMBLY ([symbol].tsx):
  
  ROUTE PARAMS:
    const { symbol } = useLocalSearchParams<{ symbol: string }>();
    Look up stock data from MOCK_STOCK_DETAILS[symbol] || MOCK_STOCK_DETAIL (fallback to RELIANCE)

  STATE:
    activeTab: 'Overview' | 'Technicals' | 'News'
    activePeriod: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | '5Y' | 'All'
    financialMetric: 'revenue' | 'profit' | 'netWorth'
    financialPeriod: 'quarterly' | 'yearly'
    shareholdingPeriod: string (one of the period options)
    aboutExpanded: boolean
    
  LAYOUT:
    LinearGradient background
    
    <StockDetailHeader />                       // Custom header with back button
    
    <ScrollView>
      <MiniPriceChart />                        // Edge-to-edge line chart
      <TimePeriodSelector />                    // 1D, 1W, 1M... row
      
      <TabSelector 
        variant="underline"
        tabs={['Overview', 'Technicals', 'News']}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      
      {activeTab === 'Overview' && (
        <>
          <PerformanceSection />                // Today + 52W range bars
          <FundamentalsSection />               // 2-column key-value grid
          <FinancialsSection />                 // Bar chart with metric/period toggles
          <AboutCompanySection />               // Company info + expandable description
          <ShareholdingSection />               // Stacked bar + legend
          <SimilarStocksSection />              // Stock rows with logos
        </>
      )}
      
      {activeTab === 'Technicals' && (
        <>
          <TechnicalSummarySection />           // Sentiment gauge
          <IndicatorsSection />                 // RSI, MACD, Beta table
          <SupportResistanceSection />          // S/R levels visual
          <MovingAveragesSection />             // MA + EMA table
          <DeliveryVolumeSection />             // Volume stats + bar
        </>
      )}
      
      {activeTab === 'News' && (
        <StockNewsSection symbol={symbol} />    // Filtered news list
      )}
    </ScrollView>

  NAVIGATION:
    Back button: router.back()
    Similar stock tap: router.push(`/stock/${tappedSymbol}`)
    Bookmark: toggle saved state (local state for now)

INDIVIDUAL COMPONENT DETAILS:

  StockDetailHeader.tsx:
    - Row: [Back chevron] [Spacer] [Bookmark] [Share] [Search]
    - Stock name: Typography.h1
    - Price + change: large mono font + PriceChangeText
    - All from mock data based on symbol param

  MiniPriceChart.tsx:
    - Full width, height 180
    - Use react-native-gifted-charts LineChart
    - Data: stockData.priceHistory
    - Color: green if positive change, red if negative
    - Area fill with gradient
    - Dashed horizontal line at prevClose
    - No axes, no grid — clean minimal chart
    - Animated path drawing on mount

  TimePeriodSelector.tsx:
    - Row of period buttons
    - Active: glass bg with border
    - Inactive: transparent
    - On change: would update chart data (for now just visual state change)

  PerformanceSection.tsx:
    - Two ProgressRangeBar components
    - First: Today's Low/High with current position marker
    - Second: 52-Week Low/High with current position marker
    - Below: 2x3 grid of key metrics (Open, Prev Close, Volume, Avg Volume, Lower/Upper Circuit)
    - Grid uses alternating row with subtle dividers
    
  FundamentalsSection.tsx:
    - GlassCard wrapping a 2-column key-value grid
    - 5 rows × 2 columns = 10 fundamental metrics
    - Each pair: label (muted) + value (white bold)
    - Exactly matching Groww screenshot layout
    
  FinancialsSection.tsx:
    - State: selectedMetric ('revenue'|'profit'|'netWorth'), selectedPeriod ('quarterly'|'yearly')
    - Two rows of TabSelector pill variants
    - BarChartWidget below with data sourced from:
      stockData.financials[selectedMetric][selectedPeriod]
    - Bars are green with gradient
    - Values displayed on top of each bar
    - Growth rate shown below chart
    - Animated bars when switching metric/period
    
  AboutCompanySection.tsx:
    - Collapsible section (chevron toggle)
    - Key-value rows: CEO, Founded, NSE Symbol
    - Description text with "Read more"/"Read less" toggle
    - Animated height expansion for description
    
  ShareholdingSection.tsx:
    - Period selector (pills): Dec '25, Sep '25, etc.
    - ShareholdingBar component with promoters, FIIs, retail, DIIs, others
    - Animated segment width transitions when period changes
    - Legend with mini horizontal bars and percentages
    
  SimilarStocksSection.tsx:
    - List of MiniStockRow variants with company logo circles
    - Logo circles: colored circle with first letter of company name
    - Each row pressable → navigates to that stock's detail page
    - Shows 5 similar stocks from mock data
    
  TechnicalSummarySection.tsx:
    - SentimentGauge component
    - Shows "Moderately Bearish" (or whatever the data says)
    - Individual colored bar segments with triangle marker
    - Bearish/Neutral/Bullish counts below
    - "Based on 1D data" footnote
    
  IndicatorsSection.tsx:
    - Table header: INDICATOR | VALUE | VERDICT
    - 6 rows of IndicatorRow components
    - RSI, MACD, Beta, ADX, ATR, CCI
    - Values in mono font
    - Verdict colored: bearish=red, neutral=gray, warning=amber, bullish=green
    
  SupportResistanceSection.tsx:
    - Full SupportResistanceCard component
    - Shows R3, R2, R1, Pivot, S1, S2, S3
    - PRICE pill positioned at current price level
    - PIVOT pill positioned at pivot level
    - R-labels in red, S-labels in green
    - Connecting dashed lines
    
  MovingAveragesSection.tsx:
    - Table: PERIOD | MA | EMA
    - 5 rows: 10D, 20D, 50D, 100D, 200D
    - MA/EMA values colored:
      Green if price is above that MA (bullish signal)
      Red if price is below that MA (bearish signal)
    
  DeliveryVolumeSection.tsx:
    - Period toggle: Daily / Weekly / Monthly
    - Stats: Total traded volume, Delivery volume, Delivery %
    - Colored dots before each stat
    - Dashed divider
    - Large delivery percentage with horizontal progress bar
    - Bar animated fill on mount
    
  StockNewsSection.tsx:
    - FlatList of NewsCard compact
    - Filtered from MOCK_NEWS where relatedStocks includes current symbol
    - If less than 3 results, also show general market news with a "Related Market News" header
    - Empty state: newspaper icon + "No recent news" message

ACCEPTANCE CRITERIA:
  - Navigate from Analysis tab to Stock Detail and back without crashes
  - Header shows correct stock name + price from mock data
  - Price chart renders with correct color (green/red based on change direction)
  - Period selector visually toggles active state
  - Tab selector switches between Overview, Technicals, News content
  - Overview tab: performance bars + fundamentals grid + bar chart + about + shareholding + similar stocks
  - Technicals tab: sentiment gauge + indicators table + S/R card + MA table + delivery volume
  - News tab: filtered news list for the stock
  - Financials bar chart animates when switching between Revenue/Profit/Net Worth
  - Shareholding bar animates when switching periods
  - Support/Resistance shows PRICE and PIVOT pills at correct positions
  - Moving average values are colored correctly (green above price, red below)
  - Every section is information-dense, matching Groww screenshot density
  - Content extends well below fold — lots of scrolling content
  - Back navigation works correctly
  - Tapping a similar stock navigates to that stock's detail page
TASK 9: Predictions Screen — Complete Build
Priority: HIGH
Estimated files: 6+

sql
Copy code
Build the entire predictions screen following Section 10 specification.

Files to create:
  1. src/components/predictions/PredictionsHeader.tsx (Section 10.1)
  2. src/components/predictions/PredictionSummaryStats.tsx (Section 10.2)
  3. src/components/predictions/ActivePredictionsList.tsx (Section 10.3)
     — Uses PredictionCard from UI library
  4. src/components/predictions/PredictionHistorySection.tsx (Section 10.4)
  5. src/components/predictions/PredictionAccuracyCard.tsx (Section 10.5)
  
  6. app/(tabs)/predictions.tsx — Main screen assembly

SCREEN ASSEMBLY (predictions.tsx):
  LinearGradient background
  ScrollView

  STATE:
    activeFilter: 'All' | 'Bullish 📈' | 'Bearish 📉' | 'High Conf.'
    historyFilter: 'All' | 'Hits ✅' | 'Misses ❌'

  LAYOUT:
    <PredictionsHeader />                       // Top
    <ScrollView>
      <PredictionSummaryStats />                // Horizontal scroll of 3 stat cards
      <ActivePredictionsList />                 // Filter tabs + PredictionCard list
      <PredictionHistorySection />              // Compact history rows
      <PredictionAccuracyCard />                // Win/loss visual + stats
    </ScrollView>

INDIVIDUAL COMPONENT DETAILS:

  PredictionsHeader.tsx:
    - Target icon + "AI Predictions" title
    - "Powered by AI analysis" subtitle
    - Right: filter + settings icon buttons
    
  PredictionSummaryStats.tsx:
    - Horizontal ScrollView with 3 glassmorphic stat cards
    - Card 1: "5 Active" with mini detail "3 Bullish · 2 Bearish"
      Gradient icon circle with target icon
    - Card 2: "72% Success Rate" with CircularProgress ring
      Ring colored by rate: green for >60%
    - Card 3: "+4.8% Avg Return" with trend-up icon
    - Cards slightly overlapping/peeking to indicate scroll
    - Each card: GlassCard, ~140px wide, 120px height
    
  ActivePredictionsList.tsx:
    - TabSelector pill variant: ["All", "Bullish 📈", "Bearish 📉", "High Conf."]
    - Below: List of PredictionCard components
    - Filter logic:
      'All': show all MOCK_PREDICTIONS
      'Bullish 📈': filter direction === 'bullish'
      'Bearish 📉': filter direction === 'bearish'
      'High Conf.': filter confidence >= 75
    - 5 prediction cards with full detail:
      RELIANCE Buy (78% conf)
      TCS Strong Buy (82% conf)
      HDFCBANK Sell (65% conf)
      BAJFINANCE Buy (71% conf)
      INFY Strong Buy (85% conf)
    - Each card shows:
      Direction badge + verdict badge
      Stock name + current price with change
      Target levels vertical track with T1/T2/T3 + entry + stop loss
      Confidence ring + Risk:Reward + Timeframe metrics
      AI reasoning (expandable)
      Timestamp footer
    - Staggered entrance animations: each card delays 150ms
    - Cards pressable → navigate to stock/[symbol]
    
  PredictionHistorySection.tsx:
    - SectionHeader: "Prediction History" with clock icon
    - TabSelector pill: ["All", "Hits ✅", "Misses ❌"]
    - GlassCard containing compact history rows
    - Each row:
      [Direction badge sm] [Symbol] [Spacer] [Outcome badge]
      "Entry: ₹4,100 → Exit: ₹4,250"
      "Return: +3.7%" (colored) | "Nov 28, 2025"
    - 10 historical entries from MOCK_PREDICTION_HISTORY
    - Filter logic:
      'All': show all
      'Hits ✅': outcome === 'hit'
      'Misses ❌': outcome === 'miss'
    - Rows separated by thin divider
    
  PredictionAccuracyCard.tsx:
    - GlassCard elevated with gradient
    - Title: "AI Performance" | Subtitle: "Last 30 predictions"
    - 3-column stat row: Accuracy (72%) | Wins (22) | Losses (8)
      Separated by thin vertical dividers
    - Win/loss ratio bar: full width, green 72% / red 28%
    - 2-column stats grid below:
      Avg Win: +4.2% | Avg Loss: -2.1%
      Best: +12.3% (TATAMOTORS) | Worst: -5.8% (COALINDIA)
      Avg Duration: 6.2 days | Risk:Reward: 1:2.4

ACCEPTANCE CRITERIA:
  - Summary stats show 3 scrollable cards with data and icons
  - Active predictions show 5 rich PredictionCard components
  - Each prediction card has visible target track, confidence ring, metrics
  - Filter pills correctly filter the prediction list
  - History section shows 10 past predictions with colored outcomes
  - History filter works (Hits/Misses)
  - Accuracy card shows win/loss bar and detailed stats
  - AI reasoning text is expandable on each prediction card
  - Screen has substantial scroll content — no empty space
  - Entrance animations stagger correctly
TASK 10: Alerts Screen — Complete Build
Priority: HIGH
Estimated files: 7+

sql
Copy code
Build the entire alerts screen following Section 11 specification.

Files to create:
  1. src/components/alerts/AlertsHeader.tsx (Section 11.1)
  2. src/components/alerts/AlertSummaryStats.tsx (Section 11.2)
  3. src/components/alerts/TriggeredAlertsSection.tsx (Section 11.3)
  4. src/components/alerts/ActiveAlertsSection.tsx (Section 11.4)
  5. src/components/alerts/ExpiredAlertsSection.tsx (Section 11.5)
  6. src/components/alerts/CreateAlertSheet.tsx (Section 11.6)
  
  7. app/(tabs)/alerts.tsx — Main screen assembly

SCREEN ASSEMBLY (alerts.tsx):
  LinearGradient background
  ScrollView (or SectionList for structured sections)

  STATE:
    showCreateSheet: boolean
    expiredExpanded: boolean
    selectedStock: Stock | null (for create sheet)
    alertType: AlertType (for create sheet)
    targetValue: string (for create sheet)
    note: string (for create sheet)

  LAYOUT:
    <AlertsHeader onCreatePress={() => setShowCreateSheet(true)} />
    <ScrollView>
      <AlertSummaryStats />                    // 3 stat cards in a row
      <TriggeredAlertsSection />               // Recently triggered alerts
      <ActiveAlertsSection />                  // Active monitoring alerts
      <ExpiredAlertsSection                    // Collapsible expired alerts
        expanded={expiredExpanded}
        onToggle={() => setExpiredExpanded(!expiredExpanded)}
      />
    </ScrollView>
    
    <CreateAlertSheet
      visible={showCreateSheet}
      onDismiss={() => setShowCreateSheet(false)}
      onSubmit={handleCreateAlert}
    />

INDIVIDUAL COMPONENT DETAILS:

  AlertsHeader.tsx:
    - Bell icon + "Alerts" title
    - "Price alerts & notifications" subtitle
    - Right: GradientButton "New" with + icon (primary variant, sm size)
    - On press of "New": opens CreateAlertSheet
    
  AlertSummaryStats.tsx:
    - Row of 3 equal-width mini GlassCards, gap 8
    - Card 1: Active — green pulsing dot + "5" large + "Active" label
      backgroundColor tint: Colors.bullishBg
    - Card 2: Triggered — check icon amber + "2" large + "Triggered" label
      backgroundColor tint: Colors.warningBg
    - Card 3: Total — "23" large + "All Time" label
      Default background
    - Each card: compact, ~80px height
    
  TriggeredAlertsSection.tsx:
    - SectionHeader: "Recently Triggered" with check-circle icon
    - Badge "2 new" next to title (variant warning, sm)
    - List of 2 triggered AlertCard components:
      RELIANCE price_above ₹1400 — triggered 45 min ago
      TCS target_hit ₹4180 — triggered 2 hours ago
    - Each card has:
      Pulsing green glow border animation
      Green check status indicator
      "Triggered at ₹X on..." info banner inside card
      Note text if exists
    - Cards: marginBottom Spacing.card.gap between them
    
  ActiveAlertsSection.tsx:
    - SectionHeader: "Active Alerts" with notifications icon
    - Action: "Clear All" (pressable text, Colors.bearish)
    - List of 5 active AlertCard components:
      HDFCBANK price_below ₹1740
      INFY price_above ₹1950
      BAJFINANCE percentage_change 5%
      SBIN price_above ₹860
      TATAMOTORS stop_loss_hit ₹720
    - Each card has:
      Pulsing green dot for active status
      Progress bar showing distance to target
      Distance percentage text
      Swipe-to-delete gesture:
        Use react-native-gesture-handler Swipeable
        Swipe left reveals red delete panel:
          backgroundColor: Colors.bearish at 20%
          Icon: trash, white, centered
          Width: 80px
        On full swipe: animate row collapse (height to 0), remove from list
        Haptic on threshold + on delete
      Note text if exists
    - Cards: marginBottom Spacing.card.gap
    
  ExpiredAlertsSection.tsx:
    - SectionHeader: "Expired" with time icon
    - Chevron icon toggles expanded/collapsed
    - "Clear" action text
    - Default state: COLLAPSED (show only header)
    - Expanded state: shows 2 expired AlertCard components
      WIPRO price_above ₹330 — expired
      COALINDIA price_below ₹400 — expired
    - Expired cards:
      Opacity: 0.55
      Gray dash status indicator
      No swipe gesture (just direct delete button visible)
    - Expand/collapse animation:
      Reanimated: animated height from 0 → measured content height
      Content fades in: FadeIn.delay(100)
      Duration: 300ms
    
  CreateAlertSheet.tsx:
    - Bottom sheet implementation
    - Use a Modal with animated translateY or a custom bottom sheet
    - Slides up from bottom covering ~70% of screen
    - Dark backdrop (opacity 0.5)
    - Handle bar at top: centered, 36px × 4px, rounded
    - Border radius: 24 on top corners
    - Background: Colors.bg.tertiary
    
    CONTENT:
    
    Header row: "Create Alert" title + Close X button
    
    Stock selector: marginTop 20
      Label: "Stock"
      SearchBar or pressable field
      When stock selected: show stock row (initial circle + symbol + name + price)
      For mock: pre-select RELIANCE by default
      
    Alert type: marginTop 20
      Label: "Alert Type"
      2×2 grid of option cards:
        [↑ Price Above] [↓ Price Below]
        [📊 % Change]   [🎯 Target Hit]
      Each: GlassCard sm, 50% width - gap, height 56
      Active: accent border, slightly elevated
      Inactive: default border
      Haptic on selection
      
    Target value: marginTop 20
      Label: "Target Price"
      Large glass input field, height 56
      Prefix "₹" in muted color
      Large mono font for the value
      Below: "Current price: ₹1,404.80 | Distance: X.X%"
      Quick adjust buttons row: [-5%] [-2%] [-1%] [+1%] [+2%] [+5%]
        Each: small pill, glass bg, pressable
        On press: calculate target = currentPrice * (1 + percentage)
        
    Note: marginTop 16
      Label: "Note (optional)"
      Multiline glass input, height 72
      Placeholder: "Add a note..."
      Character counter: "0/200"
      
    Submit: marginTop 24
      GradientButton fullWidth, size lg, variant primary
      Title: "Create Alert"
      Icon: notifications icon
      Disabled if no stock or no target
      On press:
        Haptic: Success notification
        Log the new alert (console.log for now)
        Dismiss sheet
        Show toast: "Alert created for RELIANCE at ₹1,440"
        
    Toast component:
      Position: top, below safe area, absolute
      GlassCard variant success, padding sm
      Row: [check icon green] [message text]
      Animated: slideDown + fadeIn on show, slideUp + fadeOut after 3s
      Use Reanimated for the toast animation

ACCEPTANCE CRITERIA:
  - Summary stats show 3 colored stat cards with correct numbers
  - Triggered section shows 2 alerts with pulsing green glow borders
  - Active section shows 5 alerts with progress bars and distance %
  - Swipe-to-delete works with red reveal panel and haptic feedback
  - Expired section is collapsed by default, expands with animation
  - Expired alerts show at reduced opacity
  - "New" button opens the create sheet
  - Create sheet slides up smoothly with dark backdrop
  - Stock selector shows pre-selected stock
  - Alert type grid allows selection with accent border
  - Target input accepts numbers with ₹ prefix
  - Quick adjust buttons calculate correct percentage offsets
  - Note input works with character counter
  - Submit button creates alert, dismisses sheet, shows toast
  - Toast appears at top and auto-dismisses
  - Screen has rich content with NO empty space
  - All entrance animations work correctly
TASK 11: Polish, Animations & Final Integration
Priority: MEDIUM
Estimated effort: Cross-cutting

markdown
Copy code
This task is about going through EVERY screen and polishing.

CHECKLIST:

1. ENTRANCE ANIMATIONS:
   Go through every screen and verify staggered FadeInUp animations:
   - Dashboard: each section staggers by 50ms
   - News: banner + filter + news items stagger
   - Analysis: overview cards + sector tiles + trending cards + stock lists
   - Stock Detail: header + chart + each section
   - Predictions: stats + each prediction card (150ms stagger)
   - Alerts: stats + each alert card
   
   Fix any animation that feels janky or is missing.

2. HAPTIC FEEDBACK AUDIT:
   Verify haptics fire on:
   - Every tab bar tap: ImpactFeedbackStyle.Light
   - Every button press: ImpactFeedbackStyle.Medium
   - Every card tap: ImpactFeedbackStyle.Light
   - Pull-to-refresh trigger: ImpactFeedbackStyle.Medium
   - Alert swipe threshold: ImpactFeedbackStyle.Light
   - Alert delete: NotificationFeedbackType.Warning
   - Create alert submit: NotificationFeedbackType.Success
   - Tab selector change: ImpactFeedbackStyle.Light
   
   Add missing haptics.

3. CHART ANIMATIONS:
   Verify all charts animate on mount:
   - Dashboard sparklines in indices ticker
   - Dashboard P&L line chart
   - Stock detail mini price chart
   - Stock detail financials bar chart
   - Prediction confidence circular progress
   - Alert progress bars
   - Shareholding stacked bar
   - Delivery volume progress bar
   - Market mood semi-circular gauge
   
   Fix any static chart that should animate.

4. SCROLL PERFORMANCE:
   - Add removeClippedSubviews={true} to FlatLists
   - Use React.memo on list item components
   - Use getItemLayout where possible for fixed-height items
   - Test scrolling on both Dashboard (many sections) and Stock Detail (many sections)
   - Ensure tab bar blur doesn't cause scroll jank
   
5. DARK MODE CONSISTENCY:
   Check every screen for:
   - No white or light backgrounds leaking through
   - All text uses theme colors (no hardcoded colors)
   - All borders use theme colors
   - Status bar is light content everywhere
   - Input field cursor and selection colors are accent
   - Keyboard appearance is 'dark' on all TextInputs
   
6. SAFE AREA HANDLING:
   - Top safe area: handled in every screen header
   - Bottom safe area: tab bar accounts for it
   - ScrollView content has enough bottom padding (120px) to clear tab bar
   - Bottom sheet respects bottom safe area
   
7. RESPONSIVE SIZING:
   - Test on iPhone SE (small), iPhone 15 (medium), iPhone 15 Pro Max (large)
   - Cards should not overflow on small screens
   - Text should not truncate unexpectedly
   - Charts should fill available width correctly
   - Grid columns should adapt (2 columns should work on all sizes)
   
8. EMPTY STATE REMOVAL:
   Do a FINAL audit of every screen:
   - Search for any text containing "Coming soon", "Loading", "No data", "No active"
   - Replace ALL such text with actual rendered mock data
   - If a section could theoretically be empty but has mock data, show the mock data
   - The ONLY acceptable empty state is the search overlay when search query has no matches

9. VISUAL POLISH:
   - Verify all GlassCard borders are visible but subtle
   - Verify gradient overlays are not too strong (should be barely perceptible)
   - Verify colored glow shadows render on iOS (may need tweaking on Android)
   - Verify all icons are correctly sourced from @expo/vector-icons
   - Verify badge notification count renders correctly on tab bar
   - Verify all number formatting uses Indian system (lakhs/crores)
   - Verify all date/time formatting uses timeAgo utility

ACCEPTANCE CRITERIA:
  - Smooth 60fps scrolling on all screens
  - All animations play correctly
  - All haptics fire at the right moments
  - All charts animate
  - No white backgrounds, no hardcoded colors
  - No "Coming soon" or "Loading" text anywhere
  - Safe areas handled correctly on all screens
  - App looks production-ready with rich mock data
  - Every screen is dense with information
  - The app feels premium, modern, and competitive with Groww/Robinhood
TASK 12: Navigation Flow & Final Wiring
Priority: MEDIUM
Estimated files: 3-4

sql
Copy code
Ensure all navigation flows work correctly:

1. TAB NAVIGATION:
   Dashboard ↔ News ↔ Analysis ↔ Predictions ↔ Alerts
   Tab state preserved when switching between tabs
   Scroll position preserved per tab

2. STACK NAVIGATION (from Analysis):
   Analysis tab → tap stock → Stock Detail screen (push)
   Stock Detail → tap similar stock → Stock Detail for that stock (push again)
   Stock Detail → back → returns to previous screen
   Stock Detail → back → back → returns to Analysis tab

3. CROSS-TAB NAVIGATION:
   Dashboard → tap "View All" on Active Trades → (future: pipeline screen)
   Dashboard → tap "All News →" → switches to News tab
   Dashboard → tap stock in watchlist → Stock Detail (push from dashboard stack)
   Dashboard → tap news card in carousel → (for now: log, future: news detail)
   News → tap related stock chip → Stock Detail
   Predictions → tap prediction card → Stock Detail for that stock
   Alerts → tap alert card → Stock Detail for that stock

4. MODAL/SHEET NAVIGATION:
   Alerts → "New" button → Create Alert bottom sheet (modal)
   Create Alert → Close/Submit → dismisses sheet
   
5. Verify:
   - No navigation loops
   - Back button always works
   - Tab bar visible on all tab screens, hidden on stack screens (Stock Detail)
   - Stock Detail has custom back button that works
   - Deep link support: /stock/RELIANCE should open Stock Detail

ACCEPTANCE CRITERIA:
  - All navigation paths work without crashes
  - Tab preservation works (scroll position maintained)
  - Stock detail push/pop works from multiple entry points
  - Bottom sheet opens and closes smoothly
  - Back gestures work on iOS (swipe from left edge)
  - Tab bar is properly hidden on Stock Detail screen
  - All cross-tab links navigate correctly
15. FINAL QUALITY CHECKLIST
Before considering this complete, verify EVERY item:

sql
Copy code
VISUAL:
  □ Dashboard: 9+ sections of rich content, all rendering with mock data
  □ News: Breaking banner + category filters + 8+ news cards
  □ Analysis: Search + market overview + sectors + trending + stock lists
  □ Stock Detail: Chart + 3 tabs each with 4+ sections of data
  □ Predictions: Stats + 5 prediction cards + history + accuracy card
  □ Alerts: Stats + 2 triggered + 5 active + 2 expired + create sheet
  □ Tab bar: Glassmorphic, 5 tabs, colored active states, notification badge
  □ All numbers formatted in Indian number system
  □ All dates/times show "X hours ago" format
  □ Green = bullish/profit, Red = bearish/loss, Purple = accent/AI
  □ No empty space, no placeholder text, no "Coming soon"
  □ Glass cards visible with borders and subtle depth
  □ Charts render with correct colors and animations
  □ Typography hierarchy is clear: big hero → section header → body → caption

INTERACTION:
  □ All pressable elements have visual feedback (scale + opacity)
  □ Haptic feedback fires on all interactions
  □ Pull-to-refresh works on scrollable screens
  □ Tab switching is smooth with crossfade
  □ Bottom sheet slides up/down smoothly
  □ Swipe-to-delete works on alert cards
  □ Expandable sections animate smoothly (about company, expired alerts)
  □ Search overlay appears/disappears correctly

ANIMATION:
  □ All screens have staggered entrance animations
  □ Charts animate on mount (line drawing, bar growing, ring filling)
  □ Numbers animate/count up on mount
  □ Tab indicator slides smoothly between tabs
  □ Sentiment gauge bars appear one by one
  □ Toast notifications slide in/