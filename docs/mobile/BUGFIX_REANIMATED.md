# 🐛 Bug Fix: React Native Reanimated Babel Plugin Error

## Problem

When starting the Metro bundler, encountered the following error:

```
ERROR  Error: [BABEL]: Cannot find module 'react-native-worklets/plugin'
Require stack:
- .../node_modules/react-native-reanimated/plugin/index.js
```

## Root Cause

The `react-native-reanimated` version 4.2.1 requires `react-native-worklets/plugin`, but this package doesn't exist. The plugin file (`node_modules/react-native-reanimated/plugin/index.js`) contains:

```javascript
const plugin = require('react-native-worklets/plugin');
module.exports = plugin;
```

This is a **version incompatibility** between:
- `react-native-reanimated@4.2.1` (requires `react-native-worklets`)
- Expo SDK 55 (which works with Reanimated 3.x)

## Solution

### Step 1: Downgrade Reanimated to Compatible Version

```bash
npx expo install react-native-reanimated@~3.10.1
```

This installs Reanimated 3.10.1, which is compatible with Expo SDK 55 and doesn't require the `react-native-worklets` package.

### Step 2: Fix Babel Plugin Order

Updated `babel.config.js` to ensure `react-native-reanimated/plugin` is the **last** plugin:

**Before (❌ Incorrect):**
```javascript
plugins: [
  'react-native-reanimated/plugin',  // ❌ Should be last!
  [
    'module-resolver',
    { /* ... */ }
  ],
],
```

**After (✅ Correct):**
```javascript
plugins: [
  [
    'module-resolver',
    { /* ... */ }
  ],
  'react-native-reanimated/plugin',  // ✅ Must be last!
],
```

### Step 3: Clear Cache and Restart

```bash
npx expo start --clear
```

## Why This Works

### Version Compatibility

| Package | Version | Status |
|---------|---------|--------|
| Expo SDK | 55.0.0 | ✅ |
| React Native | 0.83.2 | ✅ |
| React | 19.2.0 | ✅ |
| Reanimated | 3.10.1 | ✅ Compatible |
| ~~Reanimated~~ | ~~4.2.1~~ | ❌ Incompatible |

Reanimated 4.x introduced a new architecture that requires `react-native-worklets` package, which is not yet stable with Expo SDK 55. Reanimated 3.10.1 is the recommended version for Expo SDK 55.

### Plugin Order

From the [React Native Reanimated documentation](https://docs.swmansion.com/react-native-reanimated/docs/fundamentals/installation):

> **The Reanimated plugin has to be listed last.**

The Reanimated Babel plugin transforms worklet functions and must run after all other transformations.

## Verification

After applying the fix:
- ✅ Metro bundler starts successfully
- ✅ No Babel errors
- ✅ App runs on iOS simulator
- ✅ All UI components with Reanimated animations work correctly

## Related Files

- `babel.config.js` - Babel configuration
- `package.json` - Dependencies (Reanimated downgraded to 3.10.1)
- `src/components/ui/*` - Components using Reanimated

## Final Dependencies

```json
{
  "react-native-reanimated": "~3.10.1",
  "react-native-worklets-core": "^1.6.3"
}
```

## Key Takeaways

1. **Use Reanimated 3.10.1 with Expo SDK 55**, not 4.x
2. **Always** put `react-native-reanimated/plugin` as the **last** plugin in the Babel plugins array
3. Use `npx expo install` for Expo-compatible versions
4. Clear Metro cache after dependency or Babel config changes
5. Check Expo SDK compatibility before upgrading major versions

## Commands Summary

```bash
# 1. Downgrade Reanimated to compatible version
npx expo install react-native-reanimated@~3.10.1

# 2. Clear cache and restart
npx expo start --clear
```

---

**Status**: ✅ **RESOLVED**
**Date**: 2026-03-06
**Solution**: Downgraded `react-native-reanimated` from 4.2.1 to 3.10.1

