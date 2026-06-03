# Handoff: Mobile Production Readiness — Round 2 (14 Issues)
> run_id: 107
> run_id: 108

**Author**: Claude Sonnet 4.6 (spec only — no code written)
**Run with**: `python tools/multi_agent.py --frontend-only`

## Context
Aras mobile app (Expo 56 / RN 0.85 / React 19). Follow-up to run 107. Fixes 14 remaining customer-facing production blockers: splash screen, dark mode, login autofill, secure-store plugin, POS skeleton + change amount, workspace URL normalization, unsaved-changes guard, logout confirmation, new arch flag, cart qty cap, axios timeout, time-aware greeting, and profile endpoint field mismatch.

All files in `mobile/`. Attribution tag `// claude-sonnet-4-6` on every new function. No new npm dependencies.

**Key backend fact**: profile update endpoint is `PUT /auth/me` (not PATCH), body `{ name: string, email: string }`. Backend returns `name` not `full_name`. The mobile `User` type and all display code must use `name` not `full_name`.

---

## Frontend Tasks

### 1. UPDATE `mobile/app.json` — splash screen + dark mode + expo-secure-store plugin + new arch

```json
// Replace the entire app.json with:
{
  "expo": {
    "name": "aras-mobile",
    "slug": "aras-mobile",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "scheme": "aras",
    "userInterfaceStyle": "automatic",
    "newArchEnabled": true,
    "splash": {
      "image": "./assets/splash-icon.png",
      "resizeMode": "contain",
      "backgroundColor": "#0f1319"
    },
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.aras.mobile"
    },
    "android": {
      "package": "com.aras.mobile",
      "adaptiveIcon": {
        "backgroundColor": "#0f1319",
        "foregroundImage": "./assets/android-icon-foreground.png",
        "backgroundImage": "./assets/android-icon-background.png",
        "monochromeImage": "./assets/android-icon-monochrome.png"
      }
    },
    "web": {
      "favicon": "./assets/favicon.png"
    },
    "plugins": [
      "expo-font",
      "expo-secure-store"
    ]
  }
}
```

Changes from current: added `splash`, changed `userInterfaceStyle` to `"automatic"`, added `newArchEnabled: true`, added `"expo-secure-store"` to plugins, updated android `backgroundColor` to dark.

### 2. UPDATE `mobile/App.tsx` — fix StatusBar style

```tsx
// Change: <StatusBar style="dark" />
// To:     <StatusBar style="auto" />
```

### 3. UPDATE `mobile/src/screens/LoginScreen.tsx` — autofill + returnKey chain + workspace URL normalization

**Autofill (textContentType + autoComplete):**
```tsx
// Workspace URL TextInput — add:
//   textContentType="URL"
//   autoComplete="url"
//   returnKeyType="next"
//   onSubmitEditing={() => usernameRef.current?.focus()}

// Username TextInput — add:
//   textContentType="username"
//   autoComplete="username"
//   returnKeyType="next"
//   onSubmitEditing={() => passwordRef.current?.focus()}

// Password TextInput — add:
//   textContentType="password"
//   autoComplete="current-password"
//   returnKeyType="go"
//   onSubmitEditing={submit}

// Add refs at top of component:
// const usernameRef = useRef<TextInput>(null);
// const passwordRef = useRef<TextInput>(null);
// import { useRef } from 'react'
// import { TextInput as RNTextInput } from 'react-native' — use ref type RNTextInput
```

**Workspace URL normalization — fix `setApiBaseUrl` call:**
```ts
// In submit(), before calling setApiBaseUrl(workspaceUrl):
// Normalize: if workspaceUrl is set and does not start with 'http://' or 'https://', prepend 'https://'
// const normalizedUrl = workspaceUrl && !/^https?:\/\//i.test(workspaceUrl)
//   ? `https://${workspaceUrl}`
//   : workspaceUrl;
// Then: if (normalizedUrl) { setWorkspaceUrl(normalizedUrl); await setApiBaseUrl(normalizedUrl); }
// Also persist normalizedUrl to SecureStore (replace workspaceUrl with normalizedUrl)
```

### 4. UPDATE `mobile/src/store/useAuthStore.ts` — fix User type field mismatch

Backend returns `name`, not `full_name`. All auth store code must use `name`.

```ts
// claude-sonnet-4-6
// In User interface: change `full_name?: string` to `name?: string`
// (email field already correct)
// No other changes needed — display code in screens uses user?.full_name which will be fixed in Task 5+6
```

### 5. UPDATE `mobile/src/screens/SettingsScreen.tsx` — fix profile endpoint + field names

```tsx
// claude-sonnet-4-6
// Replace all user?.full_name → user?.name
// Replace setFullName(user?.full_name || '') → setFullName(user?.name || '')
// Replace useEffect dep user?.full_name → user?.name

// Fix saveProfile:
// Change: api.patch('/auth/me', { full_name: fullName.trim() })
// To:     api.put('/auth/me', { name: fullName.trim(), email: user?.email || '' })
// On success: useAuthStore.setState((s) => ({ user: s.user ? { ...s.user, name: fullName.trim() } : s.user }))

// Fix initials/display:
// Change initialsSource: (user?.full_name || user?.username || 'User') → (user?.name || user?.username || 'User')
// Change profileName text: user?.full_name → user?.name

// Add state for email editing:
// const [email, setEmail] = useState(user?.email || '');
// Add email TextInput to profile modal alongside name TextInput
// Pass both to PUT /auth/me: { name: fullName.trim(), email: email.trim() }
```

**Add logout confirmation:**
```tsx
// claude-sonnet-4-6
// Replace handleLogout body:
// Alert.alert(
//   'Sign out',
//   'Are you sure you want to sign out?',
//   [
//     { text: 'Cancel', style: 'cancel' },
//     { text: 'Sign out', style: 'destructive', onPress: async () => { try { await logout('manual'); } catch {} } },
//   ]
// );
```

### 6. UPDATE `mobile/src/screens/AppHomeScreen.tsx` — time-aware greeting

```tsx
// claude-sonnet-4-6
// Replace the hardcoded "Morning, {firstName}" with a time-aware greeting:
// function getGreeting(): string {
//   const h = new Date().getHours();
//   if (h < 12) return 'Morning';
//   if (h < 17) return 'Afternoon';
//   return 'Evening';
// }
// Usage: <Text style={s.h1}>{getGreeting()}, {firstName}.</Text>

// Also fix: user?.full_name → user?.name (from Task 4 field rename)
// Change: const firstName = (user?.full_name || user?.username || 'there').split(' ')[0];
// To:     const firstName = (user?.name || user?.username || 'there').split(' ')[0];
```

### 7. UPDATE `mobile/src/lib/api.ts` — axios timeout

```ts
// claude-sonnet-4-6
// Add timeout to the axios.create() call:
// const api = axios.create({
//   baseURL: API_BASE_URL,
//   timeout: 15000,
// });
```

### 8. UPDATE `mobile/src/screens/PosScreen.tsx` — skeleton loading + change_amount in invoice alert + cart qty cap

**Skeleton loading in product grid:**
```tsx
// claude-sonnet-4-6
// When loadingCatalog === true, instead of ActivityIndicator, render a FlatList or View of 6 skeleton tiles:
// Each skeleton tile: same dimensions as product tile, backgroundColor: C.surface2, borderRadius: 10, margin: 4, flex: 1
// Use Animated pulse (opacity 0.4 → 0.8 → 0.4 loop) or plain static grey — static is acceptable
// Render: numColumns={2}, columnWrapperStyle={{ paddingHorizontal: 12 }}, 6 placeholder items

// claude-sonnet-4-6
// Skeleton tile component — above PosScreen:
// const SkeletonTile = () => (
//   <View style={{ flex: 1, margin: 4, borderRadius: 10, backgroundColor: C.surface2, height: 90 }} />
// );
// Render when loadingCatalog: [...Array(6)].map((_, i) => <SkeletonTile key={i} />)
// Wrap in: <View style={{ flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12 }}>
```

**Change amount in invoice success alert:**
```tsx
// claude-sonnet-4-6
// In submitInvoice success handler, extract change_amount from response:
// const { invoice_number, change_amount } = response.data?.data || response.data || {};
// const changeText = change_amount > 0 ? `\nChange: ${formatRp(change_amount)}` : '';
// Alert.alert(
//   'Invoice Created',
//   `${invoice_number || 'Invoice'}${changeText}`,
//   [{ text: 'OK' }]
// );
```

**Cart quantity cap at stock:**
```tsx
// claude-sonnet-4-6
// In addToCart: before incrementing, check if existing.qty >= getProductStock(product)
// If at stock limit: haptic.error() and return without incrementing
// const addToCart = (product: ProductRecord) => {
//   haptic.light();
//   setCart((current) => {
//     const key = cartItemKey(product);
//     const existing = current.find((entry) => cartItemKey(entry.item) === key);
//     if (existing) {
//       if (existing.qty >= getProductStock(product)) return current; // at stock limit
//       return current.map((entry) =>
//         cartItemKey(entry.item) === key ? { ...entry, qty: entry.qty + 1 } : entry
//       );
//     }
//     return [...current, { item: product, qty: 1 }];
//   });
// };
// Also cap in changeQty(+1 direction): if entry.qty >= getProductStock, return entry unchanged
```

### 9. UPDATE `mobile/src/screens/ResourceFormScreen.tsx` — unsaved-changes guard

```tsx
// claude-sonnet-4-6
// Add dirty state tracking:
// const [isDirty, setIsDirty] = useState(false);
// In setField(): also call setIsDirty(true)
// (setField is the field change handler — wrap it to set dirty flag)

// Add navigation listener to intercept back:
// useEffect(() => {
//   const unsubscribe = navigation.addListener('beforeRemove', (e: any) => {
//     if (!isDirty || saving) return;
//     e.preventDefault();
//     Alert.alert(
//       'Discard changes?',
//       'You have unsaved changes. Leave without saving?',
//       [
//         { text: 'Keep editing', style: 'cancel' },
//         { text: 'Discard', style: 'destructive', onPress: () => navigation.dispatch(e.data.action) },
//       ]
//     );
//   });
//   return unsubscribe;
// }, [navigation, isDirty, saving]);

// Reset dirty flag after successful save:
// In save() success path: setIsDirty(false); before navigation.goBack()
```

---

## Notes for implementor

- `mobile/app.json` — full replacement is correct; do NOT keep old keys that are removed
- `mobile/App.tsx` — only change is `StatusBar style="dark"` → `style="auto"`
- `PUT /auth/me` body must include both `name` AND `email` — backend validates both fields (see `UpdateProfileRequest`)
- `user?.name` is the correct field after Task 4 fix; `full_name` no longer exists on the User type
- `expo-secure-store` plugin in app.json only affects native builds (EAS); no JS changes needed
- `newArchEnabled: true` is a build-time flag; no JS changes needed
- Cart qty cap: `getProductStock()` already exists in PosScreen — use it directly
- Skeleton tiles: static grey is fine, no animation required
- All new functions: `// claude-sonnet-4-6` tag on line above `const/function/class`
- Targeted edits only — do not rewrite entire files unless explicitly stated

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports

### Backend (Gemini)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

### Frontend (Codex GPT)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->


---
## Agent Reports (2026-06-03)

### Backend (Gemini (gemini-3-flash-preview))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: mobile/app.json, mobile/App.tsx, mobile/src/lib/api.ts, mobile/src/store/useAuthStore.ts, mobile/src/screens/LoginScreen.tsx, mobile/src/screens/SettingsScreen.tsx, mobile/src/screens/AppHomeScreen.tsx, mobile/src/screens/PosScreen.tsx, mobile/src/screens/ResourceFormScreen.tsx, docs/reports.json
- features_added: automatic dark-mode app config, secure-store plugin registration, login autofill and workspace URL normalization, time-aware home greeting, POS skeleton loading and invoice change display, unsaved-changes protection
- fixes_applied: updated profile persistence to PUT /auth/me with name and email, renamed auth state to name, enabled StatusBar auto, added axios timeout, capped POS cart quantities at stock, added logout confirmation
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code
- date: 2026-06-03
- notes: All 14 issues verified. app.json: splash+dark mode automatic+newArchEnabled+expo-secure-store plugin ✓. StatusBar style="auto" ✓. axios timeout 15s ✓. Login: usernameRef/passwordRef refs, textContentType+returnKeyType chain, normalizedUrl https prepend ✓. User.name field (not full_name) in store+all screens ✓. SettingsScreen: PUT /auth/me with name+email, logout Alert confirmation, user.name display ✓. AppHomeScreen: getGreeting() time-aware, user.name ✓. PosScreen: SkeletonTile, change_amount in invoice alert, addToCart+changeQty qty cap at stock ✓. ResourceFormScreen: isDirty+beforeRemove unsaved-changes guard ✓.
