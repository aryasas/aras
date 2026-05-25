// ARC main app — wires DesignCanvas (Desktop / Mobile Web / Native App
// sections) + Tweaks panel. ThemeApplier translates tweak state to CSS
// custom properties on :root so every primitive reflows from one source.

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#E89B6C",
  "strength": "bold",
  "theme": "dark",
  "tone": "neutral",
  "density": "balanced",
  "radius": "soft",
  "fontset": "geist",
  "dotgrid": true,
  "presence": true,
  "mono_ids": true
}/*EDITMODE-END*/;

// Curated, non-green palette. All hues sit at roughly the same oklch
// lightness so swapping between them doesn't shift hierarchy.
const ACCENTS = {
  '#E89B6C': { name: 'coral',  onAccent: '#1A120C' },
  '#F2C56C': { name: 'amber',  onAccent: '#1A1408' },
  '#7AB6FF': { name: 'azure',  onAccent: '#08111F' },
  '#C49BFF': { name: 'violet', onAccent: '#150C24' },
  '#F08FA8': { name: 'rose',   onAccent: '#1F0A12' },
  '#9BC4D9': { name: 'sky',    onAccent: '#0A141C' },
  '#A0485A': { name: 'burgundy', onAccent: '#FBEEF1' },
};

// Background tone shifts the neutral hue WITHOUT changing the accent.
// Each entry sets every surface variable for both dark + light themes.
const BG_TONES = {
  dark: {
    cool:    { bg:'#0C1117', bg2:'#10151D', surface:'#151B26', surface2:'#1B2331', line:'#252E3D', line2:'#323C4E' },
    neutral: { bg:'#0E1116', bg2:'#11151B', surface:'#161B23', surface2:'#1C2330', line:'#262E3B', line2:'#323B4B' },
    warm:    { bg:'#100F0C', bg2:'#15130F', surface:'#1B1814', surface2:'#221E18', line:'#2D2820', line2:'#3A3429' },
  },
  light: {
    cool:    { bg:'#F7F8FA', bg2:'#EFF1F5', surface:'#FFFFFF', surface2:'#F2F4F8', line:'#E2E5EC', line2:'#CDD2DC' },
    neutral: { bg:'#FBFAF7', bg2:'#F4F2EC', surface:'#FFFFFF', surface2:'#F7F5EF', line:'#E7E3D9', line2:'#D3CEC0' },
    warm:    { bg:'#FAF6EF', bg2:'#F2EDE1', surface:'#FFFCF5', surface2:'#F6F0E2', line:'#E8E0CC', line2:'#D4C9AC' },
  },
};

const FONTSETS = {
  geist:   { sans: '"Geist", "Manrope", system-ui, sans-serif',          mono: '"Geist Mono", "JetBrains Mono", ui-monospace, monospace' },
  manrope: { sans: '"Manrope", system-ui, sans-serif',                   mono: '"JetBrains Mono", ui-monospace, monospace'              },
  space:   { sans: '"Space Grotesk", "Manrope", system-ui, sans-serif',  mono: '"JetBrains Mono", ui-monospace, monospace'              },
};

const DENSITY = {
  compact:  { rowH: 30, pad: 9,  padSm: 6,  padLg: 14 },
  balanced: { rowH: 36, pad: 12, padSm: 8,  padLg: 18 },
  spacious: { rowH: 44, pad: 16, padSm: 11, padLg: 22 },
};

const RADII = {
  sharp: { base: 2,  sm: 1,  lg: 4  },
  soft:  { base: 8,  sm: 5,  lg: 14 },
  round: { base: 14, sm: 8,  lg: 22 },
};

// Sets CSS variables on :root from current tweaks. Runs in a useEffect so
// every artboard picks up the change in one place.
function ThemeApplier({ t }) {
  React.useEffect(() => {
    const r = document.documentElement;
    r.dataset.theme = t.theme;
    r.dataset.strength = t.strength;

    const accent = t.accent;
    const onAccent = (ACCENTS[accent] || ACCENTS['#E89B6C']).onAccent;
    r.style.setProperty('--accent', accent);
    r.style.setProperty('--accent-d', t.theme === 'light' ? '#FFFFFF' : onAccent);

    // Surface tones (dark + light each have cool / neutral / warm variants).
    const tones = BG_TONES[t.theme] || BG_TONES.dark;
    const tone = tones[t.tone] || tones.neutral;
    r.style.setProperty('--bg',        tone.bg);
    r.style.setProperty('--bg-2',      tone.bg2);
    r.style.setProperty('--surface',   tone.surface);
    r.style.setProperty('--surface-2', tone.surface2);
    r.style.setProperty('--line',      tone.line);
    r.style.setProperty('--line-2',    tone.line2);

    const f = FONTSETS[t.fontset] || FONTSETS.geist;
    r.style.setProperty('--font-sans', f.sans);
    r.style.setProperty('--font-mono', f.mono);

    const d = DENSITY[t.density] || DENSITY.balanced;
    r.style.setProperty('--row-h',  d.rowH  + 'px');
    r.style.setProperty('--pad',    d.pad   + 'px');
    r.style.setProperty('--pad-sm', d.padSm + 'px');
    r.style.setProperty('--pad-lg', d.padLg + 'px');

    const rad = RADII[t.radius] || RADII.soft;
    r.style.setProperty('--radius',    rad.base + 'px');
    r.style.setProperty('--radius-sm', rad.sm   + 'px');
    r.style.setProperty('--radius-lg', rad.lg   + 'px');

    r.style.setProperty('--grid', t.dotgrid
      ? (t.theme === 'light' ? 'rgba(0,0,0,.05)' : 'rgba(255,255,255,.035)')
      : 'transparent');
  }, [t.accent, t.strength, t.theme, t.tone, t.density, t.radius, t.fontset, t.dotgrid]);
  return null;
}

/* ─────────────── Frames ──────────────────────────────────────────────── */

// Slim mobile browser chrome around web mobile artboards — communicates
// "running in a phone browser" without consuming much vertical space.
function MobileWebFrame({ children, url = 'app.arc.dev', title = 'ARC' }) {
  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: '#000', borderRadius: 18, overflow: 'hidden' }}>
      <div style={{
        height: 44, background: '#11151B', flexShrink: 0,
        display: 'flex', alignItems: 'center', padding: '0 12px', gap: 10,
        borderBottom: '1px solid #1F2530',
      }}>
        <span style={{ color: '#5A6373', fontSize: 16 }}>‹</span>
        <div style={{
          flex: 1, height: 28, background: '#0E1116', borderRadius: 8,
          display: 'flex', alignItems: 'center', gap: 8, padding: '0 12px',
          border: '1px solid #1F2530',
        }}>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: 'var(--accent)', flexShrink: 0 }} />
          <span style={{ fontFamily: '"Geist Mono", ui-monospace, monospace', fontSize: 11.5, color: '#8B95A6', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {url}
          </span>
        </div>
        <span style={{ color: '#5A6373', fontSize: 14 }}>⋯</span>
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>{children}</div>
    </div>
  );
}

// Native iOS frame wrapper: reserves status bar + home-indicator areas so
// our app chrome doesn't paint into them.
function NativeFrame({ children }) {
  return (
    <IOSDevice width={402} height={874} dark>
      <div style={{
        height: '100%', display: 'flex', flexDirection: 'column',
        paddingTop: 50, paddingBottom: 34, boxSizing: 'border-box',
        background: 'var(--bg)',
      }}>
        {children}
      </div>
    </IOSDevice>
  );
}

/* ─────────────── App ─────────────────────────────────────────────────── */

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  return (
    <>
      <ThemeApplier t={t} />
      <DesignCanvas minScale={0.1} maxScale={2}>
        {/* SECTION 1 — Desktop */}
        <DCSection id="desktop" title="Desktop · Web App"
          subtitle="1280×800 — full SaaS workspace. Command-bar nav, mono IDs, status as glyph.">
          <DCArtboard id="d-home"  label="01 · Dashboard" width={1280} height={800}>
            <DesktopDashboard />
          </DCArtboard>
          <DCArtboard id="d-list"  label="02 · ListView"  width={1280} height={800}>
            <DesktopList />
          </DCArtboard>
          <DCArtboard id="d-form"  label="03 · Form / Item detail" width={1280} height={800}>
            <DesktopForm />
          </DCArtboard>
        </DCSection>

        {/* SECTION 2 — Mobile Web */}
        <DCSection id="mweb" title="Mobile Web · Responsive"
          subtitle="390×800 — same product, smaller surface. Runs in Safari, Chrome, etc.">
          <DCArtboard id="m-home" label="01 · Dashboard" width={390} height={800}>
            <MobileWebFrame><MobileDashboard /></MobileWebFrame>
          </DCArtboard>
          <DCArtboard id="m-list" label="02 · ListView"  width={390} height={800}>
            <MobileWebFrame><MobileList /></MobileWebFrame>
          </DCArtboard>
          <DCArtboard id="m-form" label="03 · Form / Item detail" width={390} height={800}>
            <MobileWebFrame><MobileForm /></MobileWebFrame>
          </DCArtboard>
        </DCSection>

        {/* SECTION 3 — Native App */}
        <DCSection id="native" title="Native App · iOS / Android"
          subtitle="402×874 — packaged app. Glassy tab bar, sheet detail, system gestures.">
          <DCArtboard id="n-home" label="01 · Dashboard" width={402} height={874}>
            <NativeFrame><MobileDashboard native /></NativeFrame>
          </DCArtboard>
          <DCArtboard id="n-list" label="02 · ListView"  width={402} height={874}>
            <NativeFrame><MobileList native /></NativeFrame>
          </DCArtboard>
          <DCArtboard id="n-form" label="03 · Form / Item detail" width={402} height={874}>
            <NativeFrame><MobileForm native /></NativeFrame>
          </DCArtboard>
        </DCSection>
      </DesignCanvas>

      <TweaksPanel title="ARC · Tweaks">
        <TweakSection label="Accent">
          <TweakColor
            label="Color"
            value={t.accent}
            options={Object.keys(ACCENTS)}
            onChange={(v) => setTweak('accent', v)} />
          <TweakRadio
            label="Strength"
            value={t.strength}
            options={[
              { value: 'bold',   label: 'Bold'   },
              { value: 'subtle', label: 'Subtle' },
            ]}
            onChange={(v) => setTweak('strength', v)} />
        </TweakSection>

        <TweakSection label="Surface">
          <TweakRadio
            label="Theme"
            value={t.theme}
            options={[{ value: 'dark', label: 'Dark' }, { value: 'light', label: 'Light' }]}
            onChange={(v) => setTweak('theme', v)} />
          <TweakRadio
            label="Tone"
            value={t.tone}
            options={[
              { value: 'cool',    label: 'Cool'    },
              { value: 'neutral', label: 'Neutral' },
              { value: 'warm',    label: 'Warm'    },
            ]}
            onChange={(v) => setTweak('tone', v)} />
          <TweakToggle  label="Dot-grid texture"   value={t.dotgrid}   onChange={(v) => setTweak('dotgrid', v)} />
        </TweakSection>

        <TweakSection label="System">
          <TweakRadio
            label="Density"
            value={t.density}
            options={[
              { value: 'compact',  label: 'Compact' },
              { value: 'balanced', label: 'Balanced' },
              { value: 'spacious', label: 'Spacious' },
            ]}
            onChange={(v) => setTweak('density', v)} />
          <TweakRadio
            label="Radius"
            value={t.radius}
            options={[
              { value: 'sharp', label: 'Sharp' },
              { value: 'soft',  label: 'Soft'  },
              { value: 'round', label: 'Round' },
            ]}
            onChange={(v) => setTweak('radius', v)} />
          <TweakSelect
            label="Type"
            value={t.fontset}
            options={[
              { value: 'geist',   label: 'Geist · Geist Mono' },
              { value: 'manrope', label: 'Manrope · JetBrains Mono' },
              { value: 'space',   label: 'Space Grotesk · JetBrains Mono' },
            ]}
            onChange={(v) => setTweak('fontset', v)} />
        </TweakSection>

        <TweakSection label="Details">
          <TweakToggle  label="Live presence dots"  value={t.presence} onChange={(v) => setTweak('presence', v)} />
          <TweakToggle  label="Mono IDs everywhere" value={t.mono_ids} onChange={(v) => setTweak('mono_ids', v)} />
        </TweakSection>

        <TweakSection label="">
          <TweakButton
            label="Reset to defaults"
            secondary
            onClick={() => {
              Object.entries(TWEAK_DEFAULTS).forEach(([k, v]) => setTweak(k, v));
            }} />
        </TweakSection>
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
