# UI Components Library 🎨

All base UI components have been created with glassmorphism design and smooth animations.

## ✅ Available Components

### 1. GlassCard
Glassmorphic card with blur effect.

```tsx
import { GlassCard } from '@/components/ui';

<GlassCard padding={20} borderRadius={16}>
  <Text>Content</Text>
</GlassCard>
```

**Props:**
- `padding?: number` - Inner padding (default: 16)
- `borderRadius?: number` - Border radius (default: 16)
- `blurIntensity?: number` - Blur intensity (default: 20)
- `style?: ViewStyle` - Additional styles

---

### 2. GradientButton
Button with gradient background and haptic feedback.

```tsx
import { GradientButton } from '@/components/ui';

<GradientButton
  onPress={() => console.log('Pressed')}
  variant="primary"
>
  Click Me
</GradientButton>
```

**Props:**
- `onPress: () => void` - Press handler
- `variant?: 'primary' | 'secondary' | 'success' | 'danger'` - Color variant
- `size?: 'small' | 'medium' | 'large'` - Button size
- `disabled?: boolean` - Disabled state
- `loading?: boolean` - Loading state with spinner
- `fullWidth?: boolean` - Full width button

---

### 3. GradientText
Text with gradient overlay.

```tsx
import { GradientText } from '@/components/ui';

<GradientText
  colors={['#6C5CE7', '#A855F7']}
  fontSize={24}
>
  Gradient Text
</GradientText>
```

**Props:**
- `colors: string[]` - Gradient colors
- `fontSize?: number` - Font size
- `fontWeight?: string` - Font weight
- `style?: TextStyle` - Additional styles

---

### 4. AnimatedNumber
Smoothly animating number display.

```tsx
import { AnimatedNumber } from '@/components/ui';

<AnimatedNumber
  value={1234.56}
  format="currency"
  duration={500}
/>
```

**Props:**
- `value: number` - Number to display
- `format?: 'number' | 'currency' | 'percentage'` - Format type
- `duration?: number` - Animation duration (default: 500)
- `style?: TextStyle` - Additional styles

---

### 5. Badge
Status/sentiment badge.

```tsx
import { Badge } from '@/components/ui';

<Badge variant="success" size="medium">
  Bullish
</Badge>
```

**Props:**
- `variant?: 'primary' | 'success' | 'danger' | 'warning' | 'neutral'`
- `size?: 'small' | 'medium' | 'large'`
- `style?: ViewStyle` - Additional styles

---

### 6. Skeleton
Loading skeleton with shimmer effect.

```tsx
import { Skeleton } from '@/components/ui';

<Skeleton width="100%" height={20} borderRadius={8} />
```

**Props:**
- `width?: number | string` - Width (default: '100%')
- `height?: number` - Height (default: 20)
- `borderRadius?: number` - Border radius (default: 8)

---

### 7. Divider
Section divider.

```tsx
import { Divider } from '@/components/ui';

<Divider orientation="horizontal" spacing={16} />
```

**Props:**
- `orientation?: 'horizontal' | 'vertical'` - Orientation
- `thickness?: number` - Line thickness (default: 1)
- `color?: string` - Line color
- `spacing?: number` - Margin spacing (default: 16)

---

### 8. SearchBar
Stock search input with clear button.

```tsx
import { SearchBar } from '@/components/ui';

<SearchBar
  value={searchQuery}
  onChangeText={setSearchQuery}
  placeholder="Search stocks..."
/>
```

**Props:**
- `value: string` - Input value
- `onChangeText: (text: string) => void` - Change handler
- `placeholder?: string` - Placeholder text
- `onClear?: () => void` - Clear handler
- `autoFocus?: boolean` - Auto focus

---

### 9. PriceTicker
Live price ticker with animated changes.

```tsx
import { PriceTicker } from '@/components/ui';

<PriceTicker
  symbol="RELIANCE"
  price={2450.50}
  change={25.30}
  changePercent={1.04}
  size="medium"
/>
```

**Props:**
- `symbol: string` - Stock symbol
- `price: number` - Current price
- `change: number` - Price change
- `changePercent: number` - Percentage change
- `size?: 'small' | 'medium' | 'large'` - Display size

---

### 10. ProgressBar
Animated progress bar with gradient.

```tsx
import { ProgressBar } from '@/components/ui';

<ProgressBar
  progress={75}
  variant="success"
  height={8}
/>
```

**Props:**
- `progress: number` - Progress value (0-100)
- `height?: number` - Bar height (default: 8)
- `variant?: 'primary' | 'success' | 'danger' | 'warning'`
- `showGradient?: boolean` - Show gradient (default: true)

---

### 11. SentimentGauge
Circular sentiment/confidence gauge.

```tsx
import { SentimentGauge } from '@/components/ui';

<SentimentGauge
  value={85}
  size={120}
  label="Confidence"
  showValue={true}
/>
```

**Props:**
- `value: number` - Gauge value (0-100)
- `size?: number` - Gauge size (default: 120)
- `strokeWidth?: number` - Stroke width (default: 12)
- `label?: string` - Label text
- `showValue?: boolean` - Show percentage (default: true)

---

### 12. TabSelector
Horizontal tab selector.

```tsx
import { TabSelector } from '@/components/ui';

<TabSelector
  tabs={[
    { id: '1d', label: '1D' },
    { id: '1w', label: '1W', count: 5 },
  ]}
  activeTab={activeTab}
  onTabChange={setActiveTab}
/>
```

**Props:**
- `tabs: Tab[]` - Array of tabs
- `activeTab: string` - Active tab ID
- `onTabChange: (tabId: string) => void` - Tab change handler

**Tab Interface:**
```tsx
interface Tab {
  id: string;
  label: string;
  count?: number; // Optional badge count
}
```

---

### 13. PullToRefresh
Pull-to-refresh wrapper.

```tsx
import { PullToRefresh } from '@/components/ui';

<PullToRefresh
  onRefresh={handleRefresh}
  refreshing={isRefreshing}
>
  <View>{/* Content */}</View>
</PullToRefresh>
```

**Props:**
- `onRefresh: () => void` - Refresh handler
- `refreshing: boolean` - Refreshing state
- All ScrollView props

---

## 🎨 Design System

All components follow the glassmorphism dark theme:

**Colors:**
- Background: `#0A0E1A` → `#0F1629` → `#131B2E`
- Primary: `#6C5CE7` → `#A855F7`
- Success: `#00E676`
- Danger: `#FF5252`
- Warning: `#FFD740`

**Effects:**
- Blur intensity: 20
- Border radius: 12-16px
- Smooth animations with Reanimated
- Haptic feedback on interactions

---

## 📦 Usage

Import components from the central export:

```tsx
import {
  GlassCard,
  GradientButton,
  PriceTicker,
  SentimentGauge,
} from '@/components/ui';
```

---

## ✨ Features

- ✅ Glassmorphism design
- ✅ Smooth animations with Reanimated
- ✅ Haptic feedback
- ✅ TypeScript support
- ✅ Consistent theming
- ✅ Responsive sizing
- ✅ Accessibility ready

---

**All components are ready to use in your screens!** 🚀

