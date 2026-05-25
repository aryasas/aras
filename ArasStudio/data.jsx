// Sample data for ARC framework prototype.
// PLM/ERP-style items, threads, workflow inbox. Original data — no Aras
// dataset is referenced.

const ARC_ITEMS = [
  { id: 'PRT-04812', kind: 'Part',     name: 'Drive shaft, primary',          rev: 'C',   status: 'released', owner: 'NW', updated: '2h',    classification: 'Mechanical',  notes: 12 },
  { id: 'PRT-04813', kind: 'Part',     name: 'Housing, upper rear',           rev: 'B.2', status: 'progress', owner: 'AS', updated: '17m',   classification: 'Mechanical',  notes: 4 },
  { id: 'ASM-00214', kind: 'Assembly', name: 'Transmission, M4 platform',     rev: 'A',   status: 'review',   owner: 'NW', updated: '1d',    classification: 'Powertrain',  notes: 31 },
  { id: 'DOC-09984', kind: 'Document', name: 'Acceptance test plan — M4',     rev: '02',  status: 'draft',    owner: 'LP', updated: '3d',    classification: 'Quality',     notes: 2 },
  { id: 'PRT-04788', kind: 'Part',     name: 'Bracket, sensor mount L',       rev: 'D',   status: 'released', owner: 'KM', updated: '5h',    classification: 'Mechanical',  notes: 7 },
  { id: 'ECO-00471', kind: 'Change',   name: 'Move bracket to glass-filled',  rev: '—',   status: 'review',   owner: 'NW', updated: '11m',   classification: 'Change',      notes: 18 },
  { id: 'PRT-04719', kind: 'Part',     name: 'Cap, fluid reservoir',          rev: 'A',   status: 'blocked',  owner: 'AS', updated: '2d',    classification: 'Mechanical',  notes: 9 },
  { id: 'ASM-00198', kind: 'Assembly', name: 'Cooling loop',                  rev: 'B',   status: 'released', owner: 'JT', updated: '6d',    classification: 'Thermal',     notes: 5 },
  { id: 'DOC-09812', kind: 'Document', name: 'Supplier qualification — Aril', rev: '03',  status: 'progress', owner: 'LP', updated: '3h',    classification: 'Quality',     notes: 14 },
  { id: 'PRT-04602', kind: 'Part',     name: 'Wire harness, main loom',       rev: 'F.1', status: 'review',   owner: 'KM', updated: '4d',    classification: 'Electrical',  notes: 22 },
  { id: 'PRT-04601', kind: 'Part',     name: 'Connector, 12-pin pwr',         rev: 'B',   status: 'released', owner: 'KM', updated: '8h',    classification: 'Electrical',  notes: 3 },
  { id: 'ECO-00468', kind: 'Change',   name: 'Re-route harness around bay 3', rev: '—',   status: 'progress', owner: 'NW', updated: '22m',   classification: 'Change',      notes: 41 },
];

const ARC_USERS = {
  NW: { name: 'Nadia Worthing',  color: '#E89B6C' },
  AS: { name: 'Arvid Selin',     color: '#7AB6FF' },
  LP: { name: 'Leila Pak',       color: '#F2C56C' },
  KM: { name: 'Kenji Mori',      color: '#FF9F7A' },
  JT: { name: 'June Tavares',    color: '#C49BFF' },
  RB: { name: 'Rasheed Bayo',    color: '#9BC4D9' },
};

const ARC_INBOX = [
  { id: 'ECO-00471', kind: 'change',  title: 'Approve material swap — bracket L',  from: 'NW', age: '11m',  priority: 'high'   },
  { id: 'ASM-00214', kind: 'review',  title: 'Engineering review — M4 transmission', from: 'AS', age: '2h',   priority: 'normal' },
  { id: 'DOC-09812', kind: 'sign',    title: 'Sign-off supplier qual report',      from: 'LP', age: '3h',   priority: 'normal' },
  { id: 'PRT-04602', kind: 'review',  title: 'Harness layout — bay 3 re-route',    from: 'KM', age: '5h',   priority: 'high'   },
  { id: 'ECO-00468', kind: 'change',  title: 'Cost approval — harness ECO',        from: 'NW', age: '1d',   priority: 'normal' },
];

const ARC_ACTIVITY = [
  { who: 'AS', verb: 'opened',     obj: 'PRT-04813',  detail: 'Housing, upper rear',         at: '4m'  },
  { who: 'NW', verb: 'submitted',  obj: 'ECO-00471',  detail: 'for engineering review',     at: '11m' },
  { who: 'LP', verb: 'commented',  obj: 'DOC-09812',  detail: '"Need updated CpK from line 2."', at: '23m' },
  { who: 'KM', verb: 'released',   obj: 'PRT-04788',  detail: 'rev D',                       at: '1h'  },
  { who: 'JT', verb: 'attached',   obj: 'ASM-00198',  detail: 'CFD-run 2026-05-23.zip',     at: '2h'  },
  { who: 'AS', verb: 'blocked',    obj: 'PRT-04719',  detail: 'waiting on supplier confirm', at: '3h'  },
  { who: 'NW', verb: 'pinned',     obj: 'ASM-00214',  detail: 'to your watch list',          at: '5h'  },
];

const ARC_BOM = [
  { lvl: 0, id: 'ASM-00214', name: 'Transmission, M4 platform', qty: 1, rev: 'A',  status: 'review',   open: true },
  { lvl: 1, id: 'PRT-04812', name: 'Drive shaft, primary',      qty: 1, rev: 'C',  status: 'released', open: false },
  { lvl: 1, id: 'PRT-04813', name: 'Housing, upper rear',       qty: 1, rev: 'B.2',status: 'progress', open: true },
  { lvl: 2, id: 'PRT-04788', name: 'Bracket, sensor mount L',   qty: 2, rev: 'D',  status: 'released', open: false },
  { lvl: 2, id: 'PRT-04601', name: 'Connector, 12-pin pwr',     qty: 4, rev: 'B',  status: 'released', open: false },
  { lvl: 1, id: 'ASM-00198', name: 'Cooling loop',              qty: 1, rev: 'B',  status: 'released', open: false },
  { lvl: 1, id: 'PRT-04719', name: 'Cap, fluid reservoir',      qty: 2, rev: 'A',  status: 'blocked',  open: false },
];

const ARC_THREAD = [
  { who: 'NW', at: '2d',  body: 'Moving to glass-filled nylon. Confirmed with Aril — same lead time, +8% unit cost. Updated drawing rev D.' },
  { who: 'AS', at: '1d',  body: 'Stress analysis re-ran clean. Margin 1.8× at the L1 boss. Approved for prototype build.' },
  { who: 'LP', at: '17h', body: 'Need to refresh the FAI plan to call out the new material on §3.2.' },
  { who: 'KM', at: '4h',  body: 'Updated the harness routing to clear the new boss. PRT-04602 rev F.1.' },
  { who: 'NW', at: '11m', body: 'Submitting ECO-00471 for engineering review now. Tagging @Arvid, @Leila for sign-off.' },
];

const ARC_KPIS = [
  { label: 'In your inbox',      val: 5,    delta: '+2 today',   tone: 'warn' },
  { label: 'Changes you own',    val: 12,   delta: '4 awaiting', tone: 'normal' },
  { label: 'Items released wk',  val: 23,   delta: '+11 vs. last', tone: 'good' },
  { label: 'Build readiness',    val: '94%',delta: 'M4 program',  tone: 'good' },
];

const STATUS_LABEL = {
  released:  { glyph: '●', label: 'Released'    },
  progress:  { glyph: '◐', label: 'In progress' },
  draft:     { glyph: '○', label: 'Draft'       },
  review:    { glyph: '△', label: 'In review'   },
  blocked:   { glyph: '✕', label: 'Blocked'     },
};

Object.assign(window, {
  ARC_ITEMS, ARC_USERS, ARC_INBOX, ARC_ACTIVITY, ARC_BOM, ARC_THREAD, ARC_KPIS, STATUS_LABEL,
});
