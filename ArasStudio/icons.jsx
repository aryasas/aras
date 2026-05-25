// Minimal stroke-based icon set for ARC. 16×16 viewport, single path each,
// inherits currentColor. Keep these simple — no detail icons.

const Icon = ({ d, size = 16, stroke = 1.6, fill = 'none' }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill={fill} stroke="currentColor"
       strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={d} />
  </svg>
);

const ICONS = {
  home:     'M2.5 7.5 8 3l5.5 4.5V13a1 1 0 0 1-1 1H3.5a1 1 0 0 1-1-1V7.5Z',
  cube:     'M8 2 14 5v6l-6 3-6-3V5l6-3Z M2 5l6 3 6-3 M8 8v6',
  flow:     'M3 4h4 M9 4h4 M3 8h4 M9 8h4 M3 12h4 M9 12h4 M5 4v4 M11 4v4 M5 8v4 M11 8v4',
  thread:   'M3 4h10 M3 8h7 M3 12h5',
  insights: 'M3 13V8 M7 13V5 M11 13v-6',
  search:   'M7 12.5a5.5 5.5 0 1 1 0-11 5.5 5.5 0 0 1 0 11Zm4-1.5 3 3',
  filter:   'M2.5 3.5h11l-4 5v4l-3 1.5v-5.5l-4-5Z',
  plus:     'M8 3.5v9 M3.5 8h9',
  back:     'M10 3 5 8l5 5',
  forward:  'M6 3l5 5-5 5',
  more:     'M3.2 8h.01 M8 8h.01 M12.8 8h.01',
  check:    'M3 8.5 6.5 12l7-8',
  close:    'M4 4l8 8 M12 4l-8 8',
  bell:     'M4 11h8l-1-2V6a3 3 0 0 0-6 0v3l-1 2Z M7 13a1 1 0 0 0 2 0',
  pin:      'M9.5 2.5 13.5 6.5 11 9l1 4-4-2.5-3 3 .5-4L3 7.5l4-1 2.5-4Z',
  link:     'M6 10.5a2.5 2.5 0 0 1 0-3.5l1.5-1.5a2.5 2.5 0 0 1 3.5 3.5L10 10 M10 5.5a2.5 2.5 0 0 1 0 3.5l-1.5 1.5a2.5 2.5 0 0 1-3.5-3.5L6 6',
  download: 'M8 2.5v8 M4.5 7 8 10.5 11.5 7 M3 13h10',
  share:    'M11 4a2 2 0 1 1 0 .01 M5 8a2 2 0 1 1 0 .01 M11 12a2 2 0 1 1 0 .01 M6.7 7 9.3 5 M6.7 9l2.6 2',
  chevdown: 'M3.5 6 8 10.5 12.5 6',
  chevright:'M6 3.5 10.5 8 6 12.5',
  layers:   'M8 2.5 2 5.5l6 3 6-3-6-3Z M2 9l6 3 6-3',
  command:  'M5 5h6v6H5z M5 5a2 2 0 1 1-2 2h2v-2Zm6 0a2 2 0 1 1 2 2h-2v-2Zm0 6a2 2 0 1 1 2-2v2h-2Zm-6 0a2 2 0 1 1-2-2h2v2Z',
  bolt:     'M9 1.5 3.5 9h4l-1 5.5L13 7h-4l1-5.5Z',
  build:    'M2.5 13 8 7.5 13.5 13 M5.5 13V9.5l2.5-2.5 2.5 2.5V13 M11 4.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z',
  doc:      'M4 2h5l3 3v9H4V2Z M9 2v3h3',
  asm:      'M3 4l5-2 5 2v8l-5 2-5-2V4Z M8 8 3 4 M8 8l5-4 M8 8v8',
  change:   'M3 8a5 5 0 0 1 8.5-3.5L13 6 M13 8a5 5 0 0 1-8.5 3.5L3 10 M11 3v3h3 M2 13v-3h3',
};

const Ico = ({ name, ...rest }) => <Icon d={ICONS[name] || ICONS.home} {...rest} />;

// Mark / wordmark for ARC.
const ArcMark = ({ size = 18, color = 'var(--accent)' }) => (
  <svg width={size * 1.4} height={size} viewBox="0 0 28 20" aria-hidden="true">
    <path d="M3 18 A 11 11 0 0 1 25 18" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round"/>
    <circle cx="14" cy="6.4" r="1.4" fill={color}/>
  </svg>
);

const ArcWordmark = ({ color = 'var(--text)', size = 14 }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
    <ArcMark size={size + 4} />
    <span style={{
      fontFamily: 'var(--font-mono)', fontSize: size, fontWeight: 600,
      letterSpacing: '.16em', color,
    }}>ARC</span>
  </span>
);

Object.assign(window, { Ico, Icon, ICONS, ArcMark, ArcWordmark });
