# ArasStudio — agent guide for Claude Code

This is a static HTML + in-browser Babel project. There is **no build step** and there will not be one. The design surface is a custom drag-and-drop canvas (`design-canvas.jsx`). Edits must preserve canvas compatibility and the ARC visual system. Read this file fully before changing anything.

---

## Run locally

Two processes, two terminals:

```bash
# terminal 1 — frontend
npm run dev
# → http://localhost:5173

# terminal 2 — backend API
python3 api/main.py
# → http://0.0.0.0:8000  (FastAPI / uvicorn)
```

The dev server (frontend) is already set up — just `npm run dev` from the repo root. Vite serves the static files; the `.jsx` files are still transpiled in-browser by `@babel/standalone` (see `<script type="text/babel" src="...">` in `index.html`), **not** by Vite's pipeline. So even though `npm` is involved, the code-level constraints below still apply: no ES module `import`/`export`, no JSX bundling, no TypeScript. Vite is just a smarter `http.server` here.

**Backend scope for this guide:** the FastAPI app in `api/` is out of scope for the UI rules below. When working on the frontend, treat the API as a stable contract — don't restructure backend code as a side-effect of a UI task. If a UI change needs a new endpoint, call it out separately rather than fixing both in one pass.

To open the Tweaks panel locally, paste this in DevTools console:

```js
window.postMessage({type: '__activate_edit_mode'}, '*')
```

Persistence (`__edit_mode_set_keys`) and the `.design-canvas.state.json` writer no-op without the host bridge — that's expected; the in-page UI still works.

---

## File map (load order in `index.html`)

```
react / react-dom / @babel/standalone   (UMD, pinned, integrity-hashed — DO NOT CHANGE)
design-canvas.jsx       ← the DnD canvas. Exports DesignCanvas, DCSection, DCArtboard, DCPostIt to window.
tweaks-panel.jsx        ← TweaksPanel + TweakSection/TweakRadio/TweakColor/TweakToggle/TweakSelect/TweakSlider/TweakButton + useTweaks
browser-window.jsx      ← desktop browser chrome (unused-by-default but available)
ios-frame.jsx           ← <IOSDevice> bezel used by NativeFrame
data.jsx                ← ARC_USERS, STATUS_LABEL, sample records, copy
icons.jsx               ← <Ico name="..." /> SVG icon set
primitives.jsx          ← ARC atoms: MonoId, Status, Avatar, AvatarStack, KBD, CommandBar, …
desktop.jsx             ← DesktopDashboard, DesktopList, DesktopForm
mobile.jsx              ← MobileDashboard, MobileList, MobileForm
app.jsx                 ← TWEAK_DEFAULTS, ACCENTS/BG_TONES/FONTSETS/DENSITY/RADII, ThemeApplier, MobileWebFrame, NativeFrame, App, ReactDOM.createRoot(...).render(<App />)
```

When you add a new `.jsx` file, you **must** add a `<script type="text/babel" src="...">` tag to `index.html` in the right place (after its dependencies, before its consumers). The current order matters: `data` → `icons` → `primitives` → screens → `app`.

---

## The three hard compatibility rules

These three are where Opus keeps getting it wrong. **Memorize them.**

### Rule 1 — Stable, unique IDs on every Section and Artboard

Every `<DCSection>` and `<DCArtboard>` needs an `id` prop. The canvas keys persisted state (order, renames, deletions, focus) by these IDs. Renaming an id silently throws away the user's saved state for that node.

✅ Correct (from `app.jsx`):
```jsx
<DCSection id="desktop" title="Desktop · Web App" subtitle="...">
  <DCArtboard id="d-home" label="01 · Dashboard" width={1280} height={800}>
    <DesktopDashboard />
  </DCArtboard>
  <DCArtboard id="d-list" label="02 · ListView" width={1280} height={800}>
    <DesktopList />
  </DCArtboard>
</DCSection>
```

❌ Forbidden:
- Reusing an existing id for a different artboard
- Renaming `id` to "improve clarity" — change `label` (visible) or `title` (visible) instead
- Omitting `id` (the canvas falls back to `label` but you lose stability on label edits)
- Using duplicate ids across sections (the focus key is `${sectionId}/${artboardId}`, so cross-section dupes are technically allowed — but don't, it's confusing)

When **adding** an artboard, pick a fresh id following the existing convention: `d-*` for desktop, `m-*` for mobile-web, `n-*` for native. Examples in use: `d-home`, `d-list`, `d-form`, `m-home`, `m-list`, `m-form`, `n-home`, `n-list`, `n-form`.

When **deleting** an artboard from source: just remove the JSX. Do not touch `.design-canvas.state.json` — the canvas reconciles via its `srcKey` mechanism.

### Rule 2 — Artboards are static frames with explicit `width` and `height`

```jsx
<DCArtboard id="..." label="..." width={1280} height={800}>  // ← both required
  <YourScreen />
</DCArtboard>
```

Inside an artboard:
- **Never** use `height: 100%` on a child combined with `overflow: auto` or `overflow: scroll`. Artboards are not scrollable viewports — they are pixel-exact frames captured by the PNG/HTML export pipeline.
- Size the artboard to fit its content. If the content grew, bump the `height={...}` number — don't add an inner scroll region.
- The current canonical sizes are `1280×800` (desktop), `390×800` (mobile web), `402×874` (native iOS). Stick to these unless you have a specific reason; mismatched widths make the side-by-side comparison ugly.

### Rule 3 — No wrappers between DesignCanvas → DCSection → DCArtboard

`design-canvas.jsx` walks **direct children** (with `React.Fragment` flattened). It does **not** descend through arbitrary wrappers, divs, maps that return non-DCSection elements, or HOCs.

✅ Correct:
```jsx
<DesignCanvas>
  <DCSection id="a" title="A">
    <DCArtboard id="a1" .../>
    <DCArtboard id="a2" .../>
  </DCSection>
  <DCSection id="b" title="B">
    <DCArtboard id="b1" .../>
  </DCSection>
</DesignCanvas>
```

✅ Also fine (fragments are flattened):
```jsx
<DCSection id="a" title="A">
  <>
    <DCArtboard id="a1" .../>
    <DCArtboard id="a2" .../>
  </>
</DCSection>
```

❌ Broken — these artboards will not render at all:
```jsx
<DCSection id="a" title="A">
  <div>                              // ← wrapper hides children from the walker
    <DCArtboard id="a1" .../>
  </div>
</DCSection>

<DCSection id="a" title="A">
  {items.map(it => <Card>           // ← Card is not DCArtboard
    <DCArtboard id={it.id} .../>
  </Card>)}
</DCSection>
```

If you must conditionally include artboards, do it inline:
```jsx
<DCSection id="a" title="A">
  <DCArtboard id="a1" .../>
  {showExperimental && <DCArtboard id="a2" .../>}
</DCSection>
```

---

## Visual system rules (the "style match" problem)

The ARC system is driven entirely by **CSS custom properties** set on `:root` by `ThemeApplier` (in `app.jsx`) from the current tweak state. **Never hardcode a color, font, radius, or spacing value** that the system already exposes as a variable. Hardcoded values won't react when the user toggles theme/density/radius/accent, which is the whole point of the project.

### Use these tokens, not literals

Defined in `index.html` `:root` (and overridden in `:root[data-theme="light"]`):

| Use for | Token |
|---|---|
| Page background | `var(--bg)`, `var(--bg-2)` |
| Card/panel surface | `var(--surface)`, `var(--surface-2)` |
| Borders / dividers | `var(--line)`, `var(--line-2)` |
| Body text | `var(--text)` |
| Secondary text | `var(--text-2)` |
| Tertiary / placeholders | `var(--text-3)` |
| Muted fills | `var(--mute)` |
| Brand accent | `var(--accent)` |
| Text on accent fill | `var(--accent-d)` |
| Warn / danger / info | `var(--warn)`, `var(--danger)`, `var(--info)` |
| Border radius | `var(--radius)`, `var(--radius-sm)`, `var(--radius-lg)` |
| Row height (density) | `var(--row-h)` |
| Inner padding | `var(--pad)`, `var(--pad-sm)`, `var(--pad-lg)` |
| Sans font | `var(--font-sans)` |
| Mono font | `var(--font-mono)` |
| Dot-grid texture color | `var(--grid)` |

When introducing a token, add it to **both** the dark `:root` block and the `:root[data-theme="light"]` override in `index.html`. Tokens that don't change across themes (e.g. accent — applied per-theme by `ThemeApplier`) only need the dark block.

### Use the `.arc-*` utility classes

Defined in `index.html`. **Prefer these to inline styles for atoms** — they already wire density/theme/radius correctly:

- `.arc-btn`, `.arc-btn.primary`, `.arc-btn.ghost`, `.arc-btn.sm`
- `.arc-input`, `.arc-input.mono`
- `.arc-chip`, `.arc-chip.active`, `.arc-chip.solid`
- `.arc-card`
- `.arc-id`, `.arc-mono`, `.arc-tnum`, `.arc-dim`, `.arc-dim2`
- `.arc-stat.s-released | .s-progress | .s-draft | .s-review | .s-blocked`
- `.arc-av`, `.arc-cmd`, `.arc-kbd`
- `.arc-bg`, `.arc-surface`, `.arc-divider`
- `.arc-scroll` (custom scrollbar)
- `.arc-dotgrid` (texture)

### Reuse `primitives.jsx` and `icons.jsx`

Before inventing a new atom, check what already exists:

- `MonoId({id, prefix})` → renders `ARC·PRT-04812` style identifier
- `Status({value, label})` → status glyph + optional label
- `Avatar({id, size, ring})` → 24px initials avatar from `ARC_USERS`
- `AvatarStack({ids, size, max})` → overlapping avatars
- `KBD` → keyboard hint chip
- `CommandBar({placeholder, width})` → top command-bar pattern
- `Ico({name, size})` → SVG icon set (open `icons.jsx` to see the names)

If something is needed in 2+ screens, factor it into `primitives.jsx`. Don't duplicate.

### Style object naming (Babel global-scope gotcha)

All `.jsx` files share a single global scope after Babel transpiles them — they are not modules. **Never** write `const styles = {...}` at the top level of a component file; the second file to load will clobber the first. Name your style objects after the component:

✅ `const desktopDashboardStyles = { ... }`
❌ `const styles = { ... }`

Or just use inline styles, which is what most of this codebase does already.

### Export shared components to `window`

If you need a component from one `.jsx` file in another, add it to `window` at the bottom of the defining file (see the last line of `design-canvas.jsx`):

```jsx
Object.assign(window, { MyComponent, MyOtherComponent });
```

`primitives.jsx`, `data.jsx`, and `icons.jsx` define top-level globals that consumers reference directly without an explicit export — that works because Babel hoists `function`/`const` declarations to the shared global. Either pattern is fine; just be consistent within a file.

---

## Tweaks panel

There is **exactly one** Tweaks panel, defined inside `<App>` in `app.jsx`. Do not add a second one. Extend the existing one.

The `useTweaks(TWEAK_DEFAULTS)` hook returns `[t, setTweak]`. Call `setTweak('key', value)` and the change persists via the host bridge.

`TWEAK_DEFAULTS` is wrapped in `/*EDITMODE-BEGIN*/.../*EDITMODE-END*/` markers — the JSON between them must stay valid (double-quoted keys/strings). The host rewrites this block when persisting tweaks. **Don't add comments inside the markers and don't reformat as JS-style object literals — it must parse as JSON.**

When adding a tweak:
1. Add the default key/value to `TWEAK_DEFAULTS` (valid JSON).
2. Add a `<TweakRadio|TweakColor|TweakToggle|TweakSelect|TweakSlider|TweakButton>` inside an existing `<TweakSection>` (or a new one) in the JSX.
3. If the tweak should affect CSS variables, extend `ThemeApplier` to translate the new key.
4. Otherwise, read `t.yourKey` directly inside the consuming component (you'll need to thread it through props or expose `t` via context — currently it's only used inside `App`).

---

## Canvas state file — `.design-canvas.state.json`

Holds per-section `{ order, title, labels, hidden, srcKey }`. **Do not hand-edit.** The canvas reconciles automatically when you add/remove artboards in source. If you genuinely need to reset the viewport (pan/zoom), bump the `SEED_V` constant in `index.html`:

```js
var SEED_V = 'arc-seed-v3';  // bump to 'arc-seed-v4' to force a re-seed
```

Commit `.design-canvas.state.json` if you want teammates to see your reorder/renames. Git-ignore it if each developer should have their own.

---

## Adding a new screen — checklist

1. Decide the surface: desktop (`desktop.jsx`), mobile web (`mobile.jsx`), or native (also `mobile.jsx` — pass `native` prop).
2. Compose the screen using `.arc-*` classes, primitives from `primitives.jsx`, and icons from `icons.jsx`. Pull sample copy from `data.jsx`. **No new colors, no new fonts, no hardcoded `#hex` — use `var(--...)`.**
3. Export the component on `window` if it lives in a new file, or just declare it at top level in the existing screen file.
4. In `app.jsx`, register it as a new `<DCArtboard>` inside the matching `<DCSection>`. Pick a fresh stable id following convention. Use the canonical width/height for that surface.
5. For mobile web, wrap in `<MobileWebFrame>`. For native, wrap in `<NativeFrame>`. Desktop is bare.
6. Refresh the browser. Pan to the new artboard. Verify it renders, the artboard header (grip / label / kebab / expand) appears, drag-reorder works, and focus mode opens with ←/→/Esc.

---

## Preserving DOM contract attributes

Some elements carry `data-comment-anchor="..."` — leave it in place across edits, even if you restructure the element. It pins user review comments to that node. Same goes for `data-dc-slot`, `data-dc-section`, `data-omelette-chrome` — these are read by the canvas and the host; do not invent new values or duplicate them.

---

## Anti-patterns Claude Code keeps reaching for

Do not do any of these:

- ❌ Add a build pipeline that processes `.jsx` files (Vite's React plugin, Webpack, esbuild, swc). Vite is here only as a static dev server — the `.jsx` files must keep being transpiled in-browser by `@babel/standalone`.
- ❌ Add TypeScript. The files are `.jsx`, transpiled in-browser. No types, no `tsconfig`.
- ❌ Replace `<script type="text/babel" src>` with ES modules / `import` / `export`. Babel-standalone doesn't process modules here.
- ❌ Replace inline-Babel React with a React Server Components/Next.js setup.
- ❌ Add Tailwind, styled-components, emotion, CSS modules. The system is CSS variables + `.arc-*` classes + occasional inline styles.
- ❌ Hardcode `#hex` colors, `px` font sizes outside the `var(--row-h)`/`var(--pad)` scale, or font families.
- ❌ Introduce `<DCArtboard>` without `width`+`height`+`id`.
- ❌ Wrap artboards in divs or render them via `.map()` returning a non-`DCArtboard` element.
- ❌ Add a `package.json` with dependencies. There are none. Don't install any.
- ❌ Modify `.design-canvas.state.json` directly.
- ❌ Add a second `TweaksPanel`.
- ❌ Use `const styles = {}` at the top of a `.jsx` file — collides across Babel scripts.
- ❌ Use `scrollIntoView` anywhere.
- ❌ Add filler content. If a section feels empty, fix the layout, don't invent fake stats/icons/testimonials.

---

## Quick sanity check before committing

```
1. Page loads at http://localhost:5173 with no console errors.
2. Every <DCArtboard> in app.jsx has unique id + width + height.
3. Every new color/spacing/font uses var(--...) — grep for new "#" hex in your diff.
4. Tweaks panel opens (postMessage above) and all controls still function.
5. TWEAK_DEFAULTS between EDITMODE markers is valid JSON.
6. Drag-reorder works on any new artboard; focus mode opens with the expand button.
7. No new <script> tag in index.html points to a file that doesn't exist.
8. New .jsx file's <script> tag is positioned AFTER its dependencies in index.html.
```

If any of those fail, you broke something — fix before handing back.
