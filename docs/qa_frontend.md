# Frontend QA - Half C
## Summary
- critical: 0 | high: 5 | medium: 6 | low: 5

## Critical
- none

## High
- [ui/src/aras-core/components/ListView.tsx:521] `npm run build` is blocked by unused `idValue`.
- [ui/src/aras-core/components/ListView.tsx:523] `npm run build` is blocked by unused `primaryValue`.
- [ui/src/aras-core/components/ListView.tsx:524] `npm run build` is blocked by unused `statusValue`.
- [ui/src/views/CustomerPortalSetup.tsx:2] `npm run build` is blocked by `FormEvent` being imported as a runtime value while `verbatimModuleSyntax` requires `import type`.
- [ui/src/aras-core/components/DynamicForm.tsx:70] `DynamicForm` no longer renders metadata model actions at all, and there is no `display_token` handling or copyable modal. `Subscription.approve()` relies on a returned `{display_token: ...}` setup link, so the admin user will not see the generated setup link from this form.

## Medium
- [ui/src/views/CustomerSignup.tsx:29] Plans loading failures are silently treated as an empty plan list; no error state is rendered for failed plan load.
- [ui/src/views/PublicLanding.tsx:25] Landing and public plans fetch failures are silently swallowed; the page renders empty/fallback content without an error state.
- [ui/src/views/CustomerSignup.tsx:52] Signup success does not read either `subscription_id` or the old `signup_id`. This avoids the renamed-field bug, but also discards the backend response entirely.
- [ui/src/views/CustomerPortal.tsx:61] Portal subscription response is consumed as raw JSON. If the backend switches this public endpoint to the standard `{success, data, message, error}` envelope, this page will drift.
- [mobile/src/screens/ResourceListScreen.tsx:28] Mobile converts resource paths with `resourceName.replace(/\//g, '_')`, then calls `/${clean}`. For normal menu resources like `stock/items`, this becomes `/stock_items`, but backend routes are `/stock/items`; list/detail/create/update will 404 for nested app resources.
- [mobile/src/screens/ResourceFormScreen.tsx:28] Mobile form uses the same slash-to-underscore route conversion for get/patch/post, so edits and creates also drift from backend routes.

## Low
- [ui/src/store/uiStore.ts:107] Default `accentColor` is hardcoded `#4F46E5`. This is acceptable as a persisted theme default, but it is a hardcoded hex.
- [ui/src/views/CustomerSignup.tsx:1] Uses legacy `var(--app-*)` tokens and hardcoded red/indigo Tailwind colors instead of newer `var(--bg)`, `var(--text)`, and `var(--accent)` tokens.
- [ui/src/views/CustomerPortal.tsx:1] Uses legacy `var(--app-*)` tokens and hardcoded status colors.
- [ui/src/views/CustomerPortalSetup.tsx:2] Uses legacy `var(--app-*)` tokens and hardcoded status/focus colors.
- [mobile/src/screens/LoginScreen.tsx:59] "Forgot?" button has no handler, so the mobile forgot-password path is a dead UI affordance.

## Routes Audit
All imported view files referenced by `ui/src/App.tsx` exist:
- `/login` -> `ui/src/views/Login.tsx`
- `/organization` -> `ui/src/views/OrganizationPicker.tsx`
- `/forgot-password` -> `ui/src/views/ForgotPassword.tsx`
- `/reset-password` -> `ui/src/views/ResetPassword.tsx`
- `/p/:slug` -> `ui/src/views/WebPageView.tsx`
- `/contact` -> `ui/src/views/ContactView.tsx`
- `/welcome` -> `ui/src/views/PublicLanding.tsx`
- `/signup` -> `ui/src/views/CustomerSignup.tsx`
- `/portal` -> `ui/src/views/CustomerPortal.tsx`
- `/portal/setup` -> `ui/src/views/CustomerPortalSetup.tsx`
- `/` index and `/dashboard` -> `ui/src/views/Home.tsx`
- `/settings` -> `ui/src/views/Settings.tsx`
- `/settings/dashboard` -> `ui/src/views/DashboardSettings.tsx`
- `/settings/global` -> `ui/src/views/GlobalSettings.tsx`
- `/settings/audit` -> `ui/src/views/AuditLogs.tsx`
- `/settings/rbac` -> `ui/src/views/RBACManager.tsx`
- `/admin/license` -> `ui/src/views/LicenseStatus.tsx`
- `/preview/:slug` -> `ui/src/views/WebPageView.tsx`
- `/config/user-access` -> `ui/src/views/ErpUserAccess.tsx`
- `/dev` -> `ui/src/views/DevTools.tsx`
- `/dev/template-builder` -> `ui/src/views/TemplateBuilder.tsx`
- `/dev/health` -> `ui/src/views/HealthIntegrity.tsx`
- `/dev/routes` -> `ui/src/views/InspectRoutes.tsx`
- `/admin/tenants` -> `ui/src/views/TenantAdmin.tsx`
- `/dev/help` -> `ui/src/views/HelpDev.tsx`
- `/help` -> `ui/src/views/HelpUser.tsx`
- `/dev/table/:app/:model` and `/:id` -> `ui/src/views/DynamicView.tsx`
- `/apps` -> `ui/src/views/AppManager.tsx`
- `/profile` -> `ui/src/views/Profile.tsx`
- `/reports` -> `ui/src/views/ReportCenter.tsx`
- `/archive/*` -> `ui/src/views/ArchivedView.tsx`
- `/pot/pos` and `/pot/sessions/:id/pos` -> `ui/src/views/PosView.tsx`
- `/:segment1/*` -> `ui/src/views/SmartDispatcher.tsx`
- catch-all -> `ui/src/views/NotFound.tsx`

## Sidebar
- [ui/src/layouts/components/Sidebar.tsx:139] `iconRailCollapsed` sets the 56px rail width to `0`, removes the border, and hides overflow.
- [ui/src/layouts/components/Sidebar.tsx:211] the 200px section panel is gated by `!iconRailCollapsed`, so it hides with the rail.
- [ui/src/layouts/components/Sidebar.tsx:101] `handleAppClick` calls `navigate(target, { replace: true, state: { _t: Date.now() } })` when `target === currentPath`, forcing same-path re-navigation.
- [ui/src/layouts/MainLayout.tsx:75] floating restore button renders only when `iconRailCollapsed` is true.

## Customer Portal Flow
- URLs in the four audited views match the specified backend endpoints: `/api/v1/saas/signup`, `/api/v1/saas/plans/public`, `/api/v1/saas/portal/login`, `/api/v1/saas/portal/setup`, `/api/v1/saas/portal/subscription`, and `/api/v1/web/landing`.
- `CustomerSignup.tsx` does not read the removed `signup_id` field. It also does not read the replacement `subscription_id`.
- Error/loading states exist for submit/login/setup/subscription load, but public landing and public plan fetch failures are silent.

## Theme / Dark Mode
- [ui/src/store/uiStore.ts:132] `toggleDarkMode` toggles the `dark` class and updates `themeMode` to `dark` or `normal`; `setThemeMode` also keeps `darkMode` in sync.
- Spot-checks:
- `PublicLanding.tsx`: mostly uses `var(--bg)`, `var(--text)`, `var(--accent)`.
- `AppHome.tsx`: mostly uses `var(--bg-2)`, `var(--text)`, `var(--accent)`.
- `DashboardView.tsx`: uses tokens, but has hardcoded `#10b981` and `#a78bfa`.
- `Profile.tsx`: uses tokens, but has hardcoded `#10B981`.
- `Settings.tsx`: uses tokenized colors.

## Mobile App
- Screens: `LoginScreen`, `AppHomeScreen`, `AppMenuScreen`, `ResourceListScreen`, `ResourceFormScreen`, `SettingsScreen`.
- Backend endpoint references:
- `mobile/src/store/useAuthStore.ts`: `/auth/token`, `/auth/me`.
- `mobile/src/screens/AppHomeScreen.tsx`: `/sidebar`.
- `mobile/src/screens/AppMenuScreen.tsx`: `/app-menu/{appName}`.
- `mobile/src/screens/ResourceListScreen.tsx`: `/metadata/{resourceName}`, then `/${resourceName.replace(/\//g, '_')}`.
- `mobile/src/screens/ResourceFormScreen.tsx`: `/${resourceName.replace(/\//g, '_')}/{id}`, PATCH/POST to the same transformed route.
- Because worker rules prohibit git commands, I did not run `git status`; drift noted here is from reading current `mobile/src/...` files only.

## Imports & collection output
Build command:
```text
cd ui && npm run build 2>&1 | tail -80
```

Output:
```text
npm warn using --force Recommended protections disabled.

> ui@0.0.0 build
> tsc -b && vite build

src/aras-core/components/ListView.tsx(521,29): error TS6133: 'idValue' is declared but its value is never read.
src/aras-core/components/ListView.tsx(523,29): error TS6133: 'primaryValue' is declared but its value is never read.
src/aras-core/components/ListView.tsx(524,29): error TS6133: 'statusValue' is declared but its value is never read.
src/views/CustomerPortalSetup.tsx(2,10): error TS1484: 'FormEvent' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
```

Type-check command:
```text
cd ui && npx tsc -p tsconfig.json --noEmit 2>&1 | tail -80
```

Output:
```text
npm warn using --force Recommended protections disabled.
```
