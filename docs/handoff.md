# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-24
> Feature: Mobile App — Metadata-Driven Expo

---

## Context
Build a metadata-driven Expo mobile app that consumes the existing FastAPI backend; `MobileDynamicForm` and `MobileListView` render any resource dynamically from `/metadata` endpoints so no per-module UI code is needed.

---

## Backend Tasks
No backend changes needed. All endpoints already exist.

---

## Frontend Tasks
- NEW FILE `mobile/src/lib/api.ts` — API client: base URL config, auth token storage (SecureStore), typed `get/post/patch/delete` wrappers, `getMetadata(resource)` helper
- NEW FILE `mobile/src/lib/types.ts` — shared TypeScript types: `FieldMeta`, `ResourceMetadata`, `ApiResponse`, `ListResponse`
- NEW FILE `mobile/src/store/authStore.ts` — Zustand store: `token`, `user`, `login()`, `logout()`
- NEW FILE `mobile/src/screens/LoginScreen.tsx` — email/password login form, calls `/api/v1/auth/login`, stores token via SecureStore
- NEW FILE `mobile/src/components/MobileDynamicForm.tsx` — fetches `/metadata`, renders fields by `ui_type`: text→TextInput, select→Picker, boolean→Switch, lookup→searchable modal, date→DateTimePicker; handles create/edit/save
- NEW FILE `mobile/src/components/MobileListView.tsx` — fetches list endpoint with pagination, search, pull-to-refresh; taps open MobileDynamicForm
- NEW FILE `mobile/src/screens/AppHomeScreen.tsx` — fetches `/api/v1/admin/apps` to list installed apps dynamically
- NEW FILE `mobile/src/screens/ResourceScreen.tsx` — receives `app` + `resource` params, renders MobileListView
- NEW FILE `mobile/src/navigation/AppNavigator.tsx` — React Navigation stack: Login → AppHome → Resource → Form
- UPDATE `mobile/App.js` → `mobile/App.tsx` — mount AppNavigator, wrap with auth context

## Dependencies to install (mobile/)
```
npx expo install @react-navigation/native @react-navigation/stack react-native-screens react-native-safe-area-context expo-secure-store zustand @react-native-picker/picker @react-native-community/datetimepicker
```

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run multi_agent.py -->
<!-- Delete this section if APPROVED -->


---
## Agent Reports (revision (2026-05-24))

### Backend (Gemini (gemini-2.5-flash))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: mobile/src/lib/api.ts, mobile/src/lib/types.ts, mobile/src/store/authStore.ts, mobile/src/screens/LoginScreen.tsx, mobile/src/components/MobileDynamicForm.tsx, mobile/src/components/MobileListView.tsx, mobile/src/screens/AppHomeScreen.tsx, mobile/src/screens/ResourceScreen.tsx, mobile/src/navigation/AppNavigator.tsx, mobile/App.tsx
- features_added: Metadata-driven Expo mobile app shell with auth, dynamic app/resource navigation, dynamic list view, and dynamic create/edit form rendering
- fixes_applied: Replaced starter App.js with App.tsx entry component
- framework_changes: none
- issues: Requested mobile dependencies are not installed in package.json and worker rules forbid installing them; no local TypeScript compiler was available for a no-install type check

## Claude Review
- verdict: NEEDS-FIX
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-24
- notes: All 10 files exist and code quality is good. Critical blocker: all required dependencies missing from mobile/package.json — app cannot run. Codex correctly flagged this but did not fix it.

## Revision Tasks
- UPDATE `mobile/package.json` — add all missing dependencies: `@react-navigation/native`, `@react-navigation/stack`, `react-native-screens`, `react-native-safe-area-context`, `expo-secure-store`, `zustand`, `@react-native-picker/picker`, `@react-native-community/datetimepicker` with correct versions compatible with Expo SDK 56 / React Native 0.85
- After updating package.json, run `cd mobile && npm install` to lock versions
