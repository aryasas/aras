# Aras Design System

A UI foundation extracted from the **Aras** web application — a Flask/Jinja admin dashboard / internal-tool framework with a dynamic **App Builder** (define apps, tables, fields and CRUD views from the browser), a **Notes** module, user/auth flows, settings, and a lightweight marketing shell (`web_base.html`).

**Visual stack:** Bootstrap 4 + Font Awesome 4 + Themify Icons, with a dark-ink sidebar, bright grey page canvas, and Bootstrap `card` as the primary content container. Brand lockup is set in **Libre Baskerville italic 700** — a serif wordmark against the otherwise sans-serif admin UI gives Aras a more editorial, less generic feel. Black** at 300% size on the sidebar.

---

## Sources

- Codebase (read-only, mounted): `templates/`
  - `templates/admin/*` — authenticated dashboard, sidebar, top bar, dashboards, users, apps, settings
  - `templates/auth/*` — login, register, password reset (uses `auth/_auth_layout.html`)
  - `templates/app_manager/*` — dynamic app/table/field builder
  - `templates/notes/*` — notes module (DataTables-powered)
  - `templates/web_base.html` — public/marketing shell
  - `templates/_macros.html` — form rendering helpers (WTForms)
- Referenced but not provided: `static/admin/assets/css/{bootstrap.min.css, font-awesome.min.css, themify-icons.css, metisMenu.css, typography.css, default-css.css, styles.css, responsive.css}`, `static/admin/assets/js/*`, `static/admin/assets/images/icon/favicon.ico`, `loading.gif`. Values here were lifted from the **inline styles** in the templates, which are highly specific (colors, spacing, radii, shadows).

---

## Index

| File / folder                | Purpose                                                       |
|------------------------------|---------------------------------------------------------------|
| `README.md`                  | This file                                                     |
| `SKILL.md`                   | Agent-Skill entry point (Claude Code compatible)              |
| `colors_and_type.css`        | CSS variables + semantic base styles                          |
| `assets/logo-aras.svg`       | Wordmark (dark on deep-ink tile, matches sidebar)             |
| `assets/logo-aras-light.svg` | Wordmark (dark ink on white)                                  |
| `preview/*.html`             | Design-system preview cards (registered in Design System tab) |
| `ui_kits/admin/`             | Admin dashboard UI kit — core JSX components + `index.html`   |

---

## Content fundamentals

Aras copy is **utilitarian admin English** with a sprinkle of Indonesian in the App Manager (e.g. *"Apps dibuat secara dinamis, tersimpan di database."*, *"Belum ada app."*) — the project reads as **Indonesian-built, English-first UI**.

**Tone & voice**
- Direct, second-person imperative on actions: `Add User`, `Generate View`, `Export CSV`, `Deactivate`, `Install from File`.
- Polite on auth screens: *"Please sign in"*, *"Don't have an account? Create Account"*.
- Confirm destructive actions with `confirm()` prompts: *"Delete app {{ title }}?"*, *"Toggle admin for {{ username }}?"*.
- Empty states use muted text + a single link: *"No apps defined yet."* / *"Belum ada app. [Buat sekarang.]"*.
- Roadmap states inline rather than hiding them: *"Roles & Permissions — Coming Soon"* with a faded shield icon and a `Soon` badge.

**Casing**
- **Title Case** for page titles, card headers, primary button labels (`App Builder`, `New App`, `Add User`).
- **Sentence case** for body copy, tooltips, inline help.
- **UPPERCASE with 0.6px tracking** for sub-menu group labels (`GROUP HEADER` inside dropdowns) and table `thead` (`.bg-light`-filled rows with `text-uppercase`).

**Pronouns & POV**
- "You" for the user, "We" is rare. Auth: *"Please sign in"*. Logs: *"Last seen:"*. Profile: *"Member since"*, *"Last updated"*.
- Admin actions speak about entities in 3rd person: *"Deactivate {username}?"*.

**Emoji & punctuation**
- **No emoji anywhere in the UI.** Iconography is exclusively Font Awesome 4 (`fa fa-...`) + Themify (`ti-...`).
- Em-dash (`—`) used as the null/empty placeholder in tables (`{{ date or '—' }}`).
- Ampersand kept in section names (*"Roles & Permissions"*).
- Right arrow `→` (`&rarr;`) after "view more" links (*"View all log &rarr;"*, *"Explore More"*).

**Examples (verbatim)**
- `App Builder` · `Apps dibuat secara dinamis, tersimpan di database.`
- `All Users` + count badge (`All Users [12]`)
- `Please sign in` / `Don't have an account?`
- `Ooops! Something went wrong .` (404 page, note the trailing space before period — quirky)
- `© Copyright 2018. All right reserved. App by Aras.` (classic footer)
- Dashboard widget labels are **UPPERCASE** with a bold value below (*"TOTAL USERS"* → `128`).

---

## Visual foundations

### Palette
A two-tier system: a deep-ink dashboard chrome + a very bright, almost white working surface. **No gradients, no glassmorphism, no neon.**

- **Brand / chrome**: `#1f2a44` sidebar background, `#141b2d` hover deeps, white logo on top.
- **Ink** (text): `#313b3d` primary, `#6c757d` secondary/muted, `#9aacb8` tertiary (breadcrumb, soft labels), `#8a9bb0` for submenu icons.
- **Lines**: `#eef0f2` hairline divider (most borders), `#dde3e7` button border, `#f0f3f5` softest divider.
- **Surfaces**: `#ffffff` card, `#f4f6f8` hover fill, `#f8f9fa` page, `#f1f3f5` deep fill.
- **Primary action**: `#5a6fd6` (indigo-blue — this is the literal value in `settings.html`'s `--primary-color` fallback). Matches Bootstrap 4's `btn-primary` feel.
- **Semantic**: standard Bootstrap 4 — success `#28a745`, warning `#ffc107`, danger `#dc3545`, info `#17a2b8`. Badges pair a **tinted 50 background** with the strong color as text (e.g. success `#e6f6ea` bg + `#28a745` text).

### Type
- **Display / wordmark:** **Libre Baskerville** (italic 700). The wordmark is set lowercase in the italic cut — the curved `a` and sloped terminals give Aras its visual signature. Used anywhere the brand needs gravitas: the sidebar lockup, login screen, hero titles, pull-quotes.
- **UI / body:** Bootstrap 4's native stack — system fonts (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, ...`). Sans handles all chrome, nav, tables, forms, and long-form body copy.
- **Mono:** implicit via `<code>` (SFMono / Menlo fallback) — used heavily for `{{ app.name }}`, `{{ app.url }}`, db table names.
- **Pairing rule:** serif display is reserved for **one element per view** — the page's headline moment. Everything else is sans. Mixing serif mid-paragraph looks noisy.
- **Sizes in the wild:** `10–11px` for icons/mini labels, `12px` for submenu items, `13px` for nav and body, `15px` for page titles, `16px` for top-bar icons, `22–44px` for serif editorial moments.
- **Weight:** `500` for nav, `600` for sans titles, `700` for serif display.

> **Font file shipped:** `fonts/LibreBaskerville-VariableFont_wght.ttf` (weights 400–700, upright + italic via `font-style`). Served via `@font-face` in `colors_and_type.css`. The Avenir assumption from the original templates has been fully replaced — the brand now leans editorial, not techy.

### Spacing
Bootstrap 4 scale is followed strictly: `4 / 8 / 12 / 16 / 24 / 32 / 48`. The templates favour `mt-4`/`mt-5` (24/48px) to space cards down from the content header, and 24px (`padding:0 24px`) for the top-level menu bar gutter.

### Cards & elevation
- **Corner radii:** `3–4px` (`.dropdown`, buttons, code pills) and `6–8px` (cards, container wrappers). Nothing is pill-rounded except avatars (always `border-radius:50%`).
- **Shadows:** extremely restrained — the only shadow in the templates is the dropdown shadow `0 4px 12px rgba(0,0,0,.1)`. Cards rely on a single hairline border / no shadow.
- **Borders:** 1px `#eef0f2` hairlines separate the sidebar, the menu bar, the page-title strip, and the cards' `thead.bg-light`.

### Backgrounds & imagery
- Page background is a single flat `#f8f9fa`. **No textures, no patterns, no hero images in the app shell.**
- Auth screens (`auth/_auth_layout.html`) expect a "login-area login-s2" from `styles.css` — presumably a full-bleed coloured panel, *not* a photo.
- Avatars: Gravatar URLs (`user.gravatar(28|32|50|128)`), always circular.

### Motion & state
- Hover on menu items toggles `background: '#f4f6f8'` inline — a subtle light fill, no scale/translate.
- Hover on tabs shifts text from `#6c757d` → `#313b3d`.
- Active tab: `border-bottom: 2px solid var(--primary-color, #5a6fd6)` + ink text + `font-weight:600`.
- Transitions are **150ms** on nav items (`transition: background .15s`). No bouncy/elastic easing, no long fades.
- Press state: no explicit scale/shadow — relies on Bootstrap's `:active` defaults. Sidebar close button has a 10% white inner fill (`rgba(255,255,255,.1)`).
- No reveal animations, no skeletons. A `<div id="preloader"><div class="loader"/></div>` exists in layout bases (commented-out in the admin base).

### Layout rules
- Fixed **sidebar** (dark), fixed **top bar** (white with hairline bottom), scrolling **content**.
- Content max-width is implicit via Bootstrap grid (`.col-12` inside a non-fluid container); public `web_base.html` pins to `max-width: 1100px`.
- The top bar's breadcrumb is `Home / {title}` in `#9aacb8` on one line.
- **Submenu strip**: tab bar (`.page-title-area`) can appear directly under the top bar, padded `0 30px` with a single hairline bottom — used by Settings, Dashboard, etc.

### Transparency / blur
- Alpha used only in the sidebar: `rgba(255,255,255,.75–.85)` for nav labels, `rgba(255,255,255,.1)` for the close-button fill and the sidebar divider. **No backdrop-filter blurs.**

### Corner radii summary
| Element                 | Radius |
|-------------------------|--------|
| Buttons, inputs         | 4px    |
| Badges, code pills      | 3px    |
| Menu-items in dropdowns | 3–4px  |
| Cards, modals           | 6–8px  |
| Avatars                 | 50%    |

---

## Iconography

Aras uses **two** icon systems from CDN-equivalents, both loaded as webfonts:

1. **Font Awesome 4** — `fa fa-...` classes. Used heavily: `fa-plus`, `fa-edit`, `fa-trash`, `fa-download`, `fa-play`, `fa-pause`, `fa-columns`, `fa-envelope`, `fa-facebook`, `fa-google`, `fa-check`, `fa-times`, `fa-magic`, `fa-cog`, `fa-table`, `fa-caret-down`, `fa-chevron-left/right`.
2. **Themify Icons** — `ti-...` classes. Used for the "modern" admin chrome: `ti-home`, `ti-settings`, `ti-user`, `ti-email`, `ti-lock`, `ti-name`, `ti-bell`, `ti-arrow-right`, `ti-close`, `ti-time`, `ti-trash`, `ti-menu`, `ti-fullscreen`, `ti-zoom-out`, `ti-power-off`, `ti-signal`, `ti-server`, `ti-shield`, `ti-layout-grid2`.

Rules of thumb observed in the code:
- **Themify** is preferred for **sidebar + top-bar + auth-form** icons (the "shell").
- **Font Awesome** is preferred for **actions and data** — CRUD toolbar icons (`fa-edit`, `fa-trash`), status icons (`fa-check`, `fa-pause`), social auth (`fa-facebook`, `fa-google`).
- Icons are typically `11–14px` in the UI, `16px` in the top bar, `2rem` (`fa-2x`) for dashboard widget accents.
- Colour for inline icons in submenus is `#8a9bb0` (dedicated slate) or `#6c757d` (muted).
- **No SVG icons, no emoji, no unicode pictograms.** The only unicode used are `&laquo;` / `&raquo;` for pagination and `&rarr;` for "more" links.

**CDN links used by this design system (drop-in):**
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@icon/themify-icons/themify-icons.css"/>
```

No custom SVGs were present in `templates/` (no `<svg>` tags anywhere). If you need a logo or a hero asset, use `assets/logo-aras.svg` (wordmark in Libre Baskerville italic 700).

---

## What's missing

- **Static assets**: CSS bundles, JS, `favicon.ico`, `loading.gif`, any images referenced by `styles.css`/`default-css.css` were **not** provided. If you have the original `static/admin/assets/` folder, drop it in — several visual details (exact auth-page panel colour, the "login-s2" backdrop, the `preloader` animation) are parameterised there.
- **Brand photography, illustrations, or iconography beyond Font Awesome / Themify** — none shipped. If Aras has proper brand art, drop it in `assets/` and update this list.

---

## How to use this system

1. **Include the tokens**: `<link rel="stylesheet" href="colors_and_type.css"/>` — then consume via CSS variables (e.g. `background: var(--aras-surface); color: var(--aras-ink);`).
2. **Copy components**: grab JSX from `ui_kits/admin/` (Sidebar, TopBar, MenuBar, Card, Table, Button, Badge, UserRow, LoginCard...).
3. **Icons**: use Font Awesome 4 + Themify — don't mix in Lucide/Heroicons (breaks visual cohesion).
4. **Density**: this is a **dense dashboard** — keep font sizes on 11–13px and action buttons on `btn-sm` (4px × 10px padding) unless you're on a marketing page.
