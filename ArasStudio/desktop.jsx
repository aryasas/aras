// Desktop ARC views.
// DesktopShell = global chrome (top bar + left nav strip).
// Three screens: Dashboard, List, Form. Each is a full 1280×800 artboard.

function DesktopShell({ active, children, title, breadcrumb }) {
  return (
    <div className="arc arc-bg arc-dotgrid" style={{
      width: '100%', height: '100%', display: 'flex',
      overflow: 'hidden',
    }}>
      {/* Left nav strip */}
      <div style={{
        width: 56, borderRight: '1px solid var(--line)',
        background: 'var(--bg-2)', display: 'flex', flexDirection: 'column',
        justifyContent: 'space-between', flexShrink: 0,
      }}>
        <div>
          <div style={{ height: 56, display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderBottom: '1px solid var(--line)' }}>
            <ArcMark size={20} />
          </div>
          <NavStrip active={active} />
        </div>
        <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
          <div style={{ color: 'var(--text-3)' }}><Ico name="bell" size={17} /></div>
          <Avatar id="NW" size={28} ring />
        </div>
      </div>

      {/* Main column */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Top bar */}
        <div style={{
          height: 56, display: 'flex', alignItems: 'center', gap: 16,
          padding: '0 22px', borderBottom: '1px solid var(--line)', flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', letterSpacing: '-.01em' }}>{title}</span>
            {breadcrumb && (
              <span style={{ fontSize: 12, color: 'var(--text-3)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Ico name="chevright" size={11} />
                {breadcrumb}
              </span>
            )}
          </div>
          <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
            <CommandBar width={460} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11.5, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 6, height: 6, borderRadius: 999, background: 'var(--accent)' }} />
              Live · 4 here
            </span>
            <AvatarStack ids={['AS', 'LP', 'KM', 'JT']} size={22} />
            <span style={{ width: 1, height: 22, background: 'var(--line)', margin: '0 4px' }} />
            <button className="arc-btn sm"><Ico name="plus" size={13} /> New</button>
          </div>
        </div>
        {/* Page */}
        <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
          {children}
        </div>
      </div>
    </div>
  );
}

/* ─────────────── Dashboard ─────────────────────────────────────────────── */
function DesktopDashboard() {
  return (
    <DesktopShell active="home" title="Home" breadcrumb="M4 Program">
      <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 22, height: '100%' }}>
        {/* Greeting + KPI strip */}
        <div>
          <div style={{ fontSize: 11.5, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', letterSpacing: '.14em', textTransform: 'uppercase', marginBottom: 4 }}>
            Tuesday · May 25 · 09:42
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 16 }}>
            <h1 style={{ margin: 0, fontSize: 26, fontWeight: 500, letterSpacing: '-.02em', color: 'var(--text)' }}>
              Good morning, Nadia.
              <span style={{ color: 'var(--text-3)' }}> Five things need you today.</span>
            </h1>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="arc-btn sm"><Ico name="filter" size={13} /> Focus: M4</button>
              <button className="arc-btn sm ghost"><Ico name="more" size={13} /></button>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            {ARC_KPIS.map((k, i) => (
              <KpiCard key={k.label} {...k} accent={i === 0} />
            ))}
          </div>
        </div>

        {/* Two-column: stream + inbox */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16, flex: 1, minHeight: 0 }}>
          {/* Stream */}
          <div className="arc-card" style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <SectionHeader kicker="01" title="Stream" right={
              <span style={{ fontSize: 11.5, color: 'var(--text-3)', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <span className="arc-chip active" style={{ height: 22 }}>Following</span>
                <span className="arc-chip" style={{ height: 22 }}>All</span>
              </span>
            } />
            <div className="arc-scroll" style={{ flex: 1, minHeight: 0 }}>
              {ARC_ACTIVITY.map((a, i) => <ActivityRow key={i} {...a} />)}
            </div>
          </div>

          {/* Inbox */}
          <div className="arc-card" style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <SectionHeader kicker="02" title="Awaiting you" right={
              <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>5 items · 2 high</span>
            } />
            <div className="arc-scroll" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ARC_INBOX.map((it) => <InboxRow key={it.id} item={it} />)}
            </div>
          </div>
        </div>

        {/* Pinned strip */}
        <div>
          <SectionHeader kicker="03" title="Pinned items" right={
            <span style={{ fontSize: 11.5, color: 'var(--text-3)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              Drag to reorder <Ico name="chevright" size={11} />
            </span>
          } />
          <div className="arc-scroll" style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 4 }}>
            {[ARC_ITEMS[0], ARC_ITEMS[2], ARC_ITEMS[4], ARC_ITEMS[7], ARC_ITEMS[9]].map((it) => (
              <ItemTile key={it.id} item={it} />
            ))}
          </div>
        </div>
      </div>
    </DesktopShell>
  );
}

/* ─────────────── List view ──────────────────────────────────────────────── */
function DesktopList() {
  const [selected, setSelected] = React.useState('PRT-04812');
  return (
    <DesktopShell active="items" title="Items" breadcrumb="All parts · M4 program">
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Filter row */}
        <div style={{
          padding: '14px 24px', borderBottom: '1px solid var(--line)',
          display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
        }}>
          <button className="arc-btn sm"><Ico name="filter" size={13} /> Filter</button>
          <span className="arc-chip active">Kind: Part <span className="x">×</span></span>
          <span className="arc-chip active">Status: any open <span className="x">×</span></span>
          <span className="arc-chip">Owner: anyone</span>
          <span className="arc-chip">Updated: 7d</span>
          <span style={{ width: 1, height: 18, background: 'var(--line)' }} />
          <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>
            <span className="arc-mono arc-tnum" style={{ color: 'var(--text-2)' }}>12</span> of 8,412
          </span>
          <div style={{ flex: 1 }} />
          <span className="arc-chip solid">Group: Status</span>
          <button className="arc-btn sm ghost"><Ico name="layers" size={13} /> Columns</button>
          <button className="arc-btn sm ghost"><Ico name="download" size={13} /></button>
        </div>

        {/* Table */}
        <div className="arc-scroll" style={{ flex: 1, minHeight: 0 }}>
          <table style={{
            width: '100%', borderCollapse: 'collapse', fontSize: 13,
            fontFeatureSettings: '"tnum","ss01"',
          }}>
            <thead>
              <tr style={{
                position: 'sticky', top: 0, zIndex: 1,
                background: 'var(--bg)', color: 'var(--text-3)',
                fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.14em',
                textTransform: 'uppercase',
              }}>
                <ListHeadCell w={26} />
                <ListHeadCell>Status</ListHeadCell>
                <ListHeadCell>ID</ListHeadCell>
                <ListHeadCell wide>Name</ListHeadCell>
                <ListHeadCell>Rev</ListHeadCell>
                <ListHeadCell>Classification</ListHeadCell>
                <ListHeadCell>Owner</ListHeadCell>
                <ListHeadCell>Updated</ListHeadCell>
                <ListHeadCell>Notes</ListHeadCell>
                <ListHeadCell w={40} />
              </tr>
            </thead>
            <tbody>
              {/* Group header */}
              <tr><td colSpan={10} style={{ padding: '14px 24px 6px', fontFamily: 'var(--font-mono)',
                fontSize: 10.5, letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--text-3)' }}>
                <Status value="progress" /> &nbsp; In progress · 4
              </td></tr>
              {ARC_ITEMS.filter((i) => i.status === 'progress').map((it) =>
                <ListRow key={it.id} item={it} selected={selected === it.id} onSelect={setSelected} />)}

              <tr><td colSpan={10} style={{ padding: '16px 24px 6px', fontFamily: 'var(--font-mono)',
                fontSize: 10.5, letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--text-3)' }}>
                <Status value="review" /> &nbsp; In review · 3
              </td></tr>
              {ARC_ITEMS.filter((i) => i.status === 'review').map((it) =>
                <ListRow key={it.id} item={it} selected={selected === it.id} onSelect={setSelected} />)}

              <tr><td colSpan={10} style={{ padding: '16px 24px 6px', fontFamily: 'var(--font-mono)',
                fontSize: 10.5, letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--text-3)' }}>
                <Status value="released" /> &nbsp; Released · 4
              </td></tr>
              {ARC_ITEMS.filter((i) => i.status === 'released').map((it) =>
                <ListRow key={it.id} item={it} selected={selected === it.id} onSelect={setSelected} />)}

              <tr><td colSpan={10} style={{ padding: '16px 24px 6px', fontFamily: 'var(--font-mono)',
                fontSize: 10.5, letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--text-3)' }}>
                <Status value="blocked" /> &nbsp; Blocked · 1
              </td></tr>
              {ARC_ITEMS.filter((i) => i.status === 'blocked').map((it) =>
                <ListRow key={it.id} item={it} selected={selected === it.id} onSelect={setSelected} />)}
            </tbody>
          </table>
        </div>

        {/* Status / footer */}
        <div style={{
          height: 36, borderTop: '1px solid var(--line)',
          display: 'flex', alignItems: 'center', padding: '0 24px',
          fontSize: 11.5, color: 'var(--text-3)', gap: 14,
        }}>
          <span><span className="arc-mono" style={{ color: 'var(--text-2)' }}>{selected}</span> selected</span>
          <span style={{ flex: 1 }} />
          <span>↑↓ navigate · Enter open · / search · ⌘K commands</span>
        </div>
      </div>
    </DesktopShell>
  );
}

function ListHeadCell({ children, w, wide }) {
  return (
    <th style={{
      textAlign: 'left', padding: '10px 12px', borderBottom: '1px solid var(--line)',
      fontWeight: 500, whiteSpace: 'nowrap',
      width: w, minWidth: wide ? 280 : undefined,
    }}>{children}</th>
  );
}

function ListRow({ item, selected, onSelect }) {
  return (
    <tr onClick={() => onSelect(item.id)}
        style={{
          cursor: 'pointer',
          background: selected ? 'color-mix(in oklch, var(--accent) 8%, transparent)' : 'transparent',
          color: 'var(--text)',
          position: 'relative',
        }}>
      <td style={{ width: 26, padding: '0 0 0 18px', position: 'relative' }}>
        {selected && <span style={{ position: 'absolute', left: 0, top: 4, bottom: 4, width: 2,
          background: 'var(--accent)' }} />}
        <input type="checkbox" defaultChecked={selected} style={{ accentColor: 'var(--accent)' }} />
      </td>
      <td style={{ padding: '10px 12px' }}><Status value={item.status} /></td>
      <td style={{ padding: '10px 12px' }}><MonoId id={item.id} /></td>
      <td style={{ padding: '10px 12px', color: 'var(--text)' }}>{item.name}</td>
      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-2)', fontSize: 12 }}>{item.rev}</td>
      <td style={{ padding: '10px 12px', color: 'var(--text-2)', fontSize: 12 }}>{item.classification}</td>
      <td style={{ padding: '10px 12px' }}><Avatar id={item.owner} size={22} /></td>
      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-2)' }}>{item.updated}</td>
      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 12, color: item.notes > 10 ? 'var(--text-2)' : 'var(--text-3)' }}>{item.notes}</td>
      <td style={{ padding: '10px 12px', color: 'var(--text-3)', textAlign: 'right' }}>
        <Ico name="more" size={14} />
      </td>
    </tr>
  );
}

/* ─────────────── Form / Item detail ─────────────────────────────────────── */
function DesktopForm() {
  const item = ARC_ITEMS[5]; // ECO-00471
  const [section, setSection] = React.useState('overview');
  const sections = [
    { key: 'overview', label: 'Overview',     n: '01' },
    { key: 'affected', label: 'Affected',     n: '02' },
    { key: 'reason',   label: 'Reason',       n: '03' },
    { key: 'flow',     label: 'Workflow',     n: '04' },
    { key: 'thread',   label: 'Thread',       n: '05' },
    { key: 'files',    label: 'Files',        n: '06' },
    { key: 'history',  label: 'History',      n: '07' },
  ];
  return (
    <DesktopShell active="items" title="Items"
      breadcrumb={<span><span style={{ color: 'var(--text-2)' }}>Changes</span> · {item.id}</span>}>
      <div style={{ display: 'flex', height: '100%' }}>
        {/* Section rail */}
        <div style={{
          width: 200, borderRight: '1px solid var(--line)',
          padding: '20px 14px', display: 'flex', flexDirection: 'column', gap: 2,
          flexShrink: 0, background: 'var(--bg-2)',
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
            textTransform: 'uppercase', color: 'var(--text-3)', padding: '0 8px 12px',
          }}>Sections</div>
          {sections.map((s) => {
            const on = s.key === section;
            return (
              <button key={s.key} onClick={() => setSection(s.key)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px', borderRadius: 'var(--radius)',
                  background: on ? 'var(--surface)' : 'transparent',
                  border: on ? '1px solid var(--line)' : '1px solid transparent',
                  color: on ? 'var(--text)' : 'var(--text-2)',
                  cursor: 'pointer', textAlign: 'left',
                  fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500,
                  position: 'relative',
                }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: on ? 'var(--accent)' : 'var(--text-3)' }}>{s.n}</span>
                <span>{s.label}</span>
                {on && <span style={{ marginLeft: 'auto', color: 'var(--accent)' }}>
                  <Ico name="chevright" size={11} />
                </span>}
              </button>
            );
          })}
        </div>

        {/* Main */}
        <div className="arc-scroll" style={{ flex: 1, minWidth: 0 }}>
          {/* Header */}
          <div style={{ padding: '24px 32px 18px', borderBottom: '1px solid var(--line)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 10.5, padding: '2px 8px',
                border: '1px solid var(--line)', borderRadius: 4, color: 'var(--text-2)',
                textTransform: 'uppercase', letterSpacing: '.14em',
              }}>Change · ECO</span>
              <Status value={item.status} label />
              <span className="arc-chip">M4 program</span>
              <span style={{ flex: 1 }} />
              <button className="arc-btn sm ghost"><Ico name="share" size={13} /></button>
              <button className="arc-btn sm ghost"><Ico name="link" size={13} /></button>
              <button className="arc-btn sm">Defer</button>
              <button className="arc-btn sm primary"><Ico name="check" size={13} /> Approve</button>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 22, color: 'var(--accent)', fontWeight: 500 }}>
                ARC<span style={{ color: 'var(--text-3)' }}>·</span>{item.id}
              </span>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 500, color: 'var(--text)', letterSpacing: '-.01em' }}>
                {item.name}
              </h2>
            </div>
            <div style={{ display: 'flex', gap: 18, marginTop: 14, fontSize: 12, color: 'var(--text-3)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Avatar id="NW" size={18} /> Owner Nadia W.</span>
              <span>Created <span className="arc-mono" style={{ color: 'var(--text-2)' }}>May 23</span></span>
              <span>Target rev <span className="arc-mono" style={{ color: 'var(--text-2)' }}>E</span></span>
              <span>Severity <span style={{ color: 'var(--warn)' }}>● High</span></span>
              <span>Cost impact <span className="arc-mono" style={{ color: 'var(--text-2)' }}>+$0.42 / unit</span></span>
              <span style={{ flex: 1 }} />
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: 'var(--accent)' }} />
                Arvid is viewing
              </span>
            </div>
          </div>

          {/* Section body — Overview block */}
          <div style={{ padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 28 }}>
            {/* Block: Summary */}
            <FormBlock n="01" title="Overview" subtitle="Why this change exists.">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14 }}>
                <Field label="Change type" value="Engineering — Material" mono />
                <Field label="Classification" value="Mechanical · Cost · Tooling" />
                <Field label="Linked assembly" mono>
                  <div className="arc-input mono" style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  }}>
                    <span><MonoId id="ASM-00214" /></span>
                    <Ico name="link" size={13} />
                  </div>
                </Field>
              </div>
              <Field label="Summary">
                <textarea className="arc-input" rows={3}
                  defaultValue="Move sensor-mount bracket L from PA-6 to 30% glass-filled nylon. Same supplier (Aril), same lead time. Stress margin improves 1.4× → 1.8× at the L1 boss. Cost +$0.42/unit at vol. Triggered by repeat fracture in the bench rig (event log: 2026-05-19, slot 7)."
                  style={{ resize: 'none', height: 'auto', padding: 12, lineHeight: 1.5 }} />
              </Field>
            </FormBlock>

            {/* Block: Affected items */}
            <FormBlock n="02" title="Affected items"
              right={<button className="arc-btn sm ghost"><Ico name="plus" size={13} /> Add</button>}>
              <div className="arc-card" style={{ padding: 0, overflow: 'hidden' }}>
                {[ARC_ITEMS[4], ARC_ITEMS[2], ARC_ITEMS[9]].map((it, i) => (
                  <div key={it.id} style={{
                    display: 'flex', alignItems: 'center', gap: 14,
                    padding: '11px 14px',
                    borderTop: i === 0 ? 'none' : '1px solid var(--line)',
                  }}>
                    <Status value={it.status} />
                    <MonoId id={it.id} />
                    <span style={{ flex: 1, fontSize: 13, color: 'var(--text)' }}>{it.name}</span>
                    <span className="arc-mono" style={{ fontSize: 11.5, color: 'var(--text-3)' }}>
                      rev {it.rev} → <span style={{ color: 'var(--accent)' }}>{String.fromCharCode(it.rev.charCodeAt(0) + 1)}</span>
                    </span>
                    <Avatar id={it.owner} size={20} />
                  </div>
                ))}
              </div>
            </FormBlock>

            {/* Block: Thread */}
            <FormBlock n="03" title="Thread"
              right={<span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{ARC_THREAD.length} posts · 4 people</span>}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {ARC_THREAD.slice(0, 3).map((p, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12 }}>
                    <Avatar id={p.who} size={28} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
                        <span style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500 }}>{ARC_USERS[p.who].name}</span>
                        <span className="arc-mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>{p.at} ago</span>
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.55 }}>{p.body}</div>
                    </div>
                  </div>
                ))}
                <div style={{
                  display: 'flex', gap: 12, alignItems: 'center',
                  padding: 12, border: '1px dashed var(--line-2)', borderRadius: 'var(--radius)',
                }}>
                  <Avatar id="NW" size={28} />
                  <span style={{ flex: 1, fontSize: 13, color: 'var(--text-3)' }}>Add to thread… use @ to mention</span>
                  <KBD>⌘</KBD><KBD>↵</KBD>
                </div>
              </div>
            </FormBlock>
          </div>
        </div>

        {/* Right meta rail */}
        <div style={{
          width: 252, borderLeft: '1px solid var(--line)', padding: '20px 18px',
          flexShrink: 0, background: 'var(--bg-2)',
          display: 'flex', flexDirection: 'column', gap: 22,
        }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
              textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 10 }}>Lifecycle</div>
            <Lifecycle steps={['Draft', 'Engineering', 'CCB', 'Released']} at={1} />
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
              textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 10 }}>Approvers</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { who: 'AS', role: 'Engineering', status: 'check' },
                { who: 'LP', role: 'Quality',     status: 'check' },
                { who: 'KM', role: 'Manufacturing', status: 'pending' },
                { who: 'JT', role: 'Cost',         status: 'pending' },
              ].map((a) => (
                <div key={a.who} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Avatar id={a.who} size={22} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12.5, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {ARC_USERS[a.who].name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{a.role}</div>
                  </div>
                  <span style={{ color: a.status === 'check' ? 'var(--accent)' : 'var(--text-3)' }}>
                    {a.status === 'check' ? <Ico name="check" size={14} /> : '○'}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
              textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 10 }}>Watching · 6</div>
            <AvatarStack ids={['AS','LP','KM','JT','RB','NW']} size={24} max={6} />
          </div>
        </div>
      </div>
    </DesktopShell>
  );
}

function FormBlock({ n, title, subtitle, right, children }) {
  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)', letterSpacing: '.14em' }}>{n}</span>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 500, color: 'var(--text)' }}>{title}</h3>
          {subtitle && <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{subtitle}</span>}
        </div>
        {right}
      </div>
      {children}
    </section>
  );
}

function Lifecycle({ steps, at }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {steps.map((s, i) => {
        const done = i < at;
        const cur = i === at;
        return (
          <div key={s} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 14, paddingTop: 2 }}>
              <span style={{
                width: 10, height: 10, borderRadius: 999,
                background: done ? 'var(--accent)' : cur ? 'transparent' : 'transparent',
                border: cur ? '2px solid var(--accent)' : done ? '2px solid var(--accent)' : '2px solid var(--line-2)',
              }} />
              {i < steps.length - 1 && <span style={{
                width: 2, flex: 1, minHeight: 22,
                background: done ? 'var(--accent)' : 'var(--line)',
              }} />}
            </div>
            <div style={{ paddingBottom: 14, paddingTop: 0 }}>
              <div style={{ fontSize: 12.5, fontWeight: cur ? 600 : 500,
                color: cur ? 'var(--text)' : done ? 'var(--text-2)' : 'var(--text-3)' }}>{s}</div>
              {cur && <div style={{ fontSize: 11, color: 'var(--text-3)' }}>2 of 4 approved · 1h</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

Object.assign(window, { DesktopShell, DesktopDashboard, DesktopList, DesktopForm });
