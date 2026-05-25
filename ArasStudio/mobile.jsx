// Mobile ARC views (used by both Mobile Web and Native App artboards).
// MobileShell handles top bar + bottom tab bar. Native variant tightens
// the chrome (rounded sheet, slightly more glass) so it feels iOS-native.

function MobileShell({ active, title, children, headerRight, native = false, hideTopBar = false }) {
  return (
    <div className="arc arc-bg" style={{
      width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
      overflow: 'hidden', position: 'relative',
    }}>
      {/* Top bar */}
      {!hideTopBar && (
        <div style={{
          flexShrink: 0,
          padding: native ? '8px 16px 10px' : '14px 16px 12px',
          borderBottom: native ? 'none' : '1px solid var(--line)',
          display: 'flex', alignItems: 'center', gap: 10,
          background: native ? 'transparent' : 'var(--bg-2)',
        }}>
          <ArcMark size={18} />
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 11.5, fontWeight: 600,
            letterSpacing: '.16em', color: 'var(--text)',
          }}>ARC</span>
          <span style={{ flex: 1, fontSize: 13, color: 'var(--text-2)', textAlign: 'center' }}>{title}</span>
          {headerRight || (
            <>
              <span style={{ color: 'var(--text-3)' }}><Ico name="bell" size={17} /></span>
              <Avatar id="NW" size={26} />
            </>
          )}
        </div>
      )}

      {/* Body */}
      <div className="arc-scroll" style={{ flex: 1, minHeight: 0 }}>
        {children}
      </div>

      {/* Bottom tab bar */}
      <div style={{
        flexShrink: 0,
        margin: native ? '0 12px 14px' : 0,
        borderTop: native ? 'none' : '1px solid var(--line)',
        borderRadius: native ? 22 : 0,
        background: native
          ? 'color-mix(in oklch, var(--surface) 80%, transparent)'
          : 'var(--bg-2)',
        backdropFilter: native ? 'blur(24px) saturate(160%)' : undefined,
        border: native ? '1px solid color-mix(in oklch, var(--text) 8%, transparent)' : undefined,
        boxShadow: native ? '0 8px 30px rgba(0,0,0,.4)' : 'none',
        height: 60,
        display: 'flex', alignItems: 'center', justifyContent: 'space-around',
        padding: '0 8px',
      }}>
        {[
          { key: 'home',   icon: 'home',   label: 'Home'   },
          { key: 'items',  icon: 'cube',   label: 'Items'  },
          { key: 'flow',   icon: 'flow',   label: 'Inbox'  },
          { key: 'thread', icon: 'thread', label: 'Threads' },
          { key: 'you',    icon: 'insights', label: 'You'  },
        ].map((t) => {
          const on = t.key === active;
          return (
            <div key={t.key} style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
              padding: '6px 12px', borderRadius: 12,
              color: on ? 'var(--text)' : 'var(--text-3)',
              background: on ? 'var(--surface-2)' : 'transparent',
              minWidth: 56,
            }}>
              <Ico name={t.icon} size={17} />
              <span style={{ fontSize: 10, fontWeight: 500 }}>{t.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─────────────── Mobile Dashboard ───────────────────────────────────────── */
function MobileDashboard({ native = false }) {
  return (
    <MobileShell active="home" title="Home" native={native}>
      <div style={{ padding: '14px 16px 18px', display: 'flex', flexDirection: 'column', gap: 18 }}>
        {/* Greeting */}
        <div>
          <div style={{ fontSize: 10.5, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', letterSpacing: '.14em', textTransform: 'uppercase', marginBottom: 4 }}>
            TUE · MAY 25
          </div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 500, color: 'var(--text)', letterSpacing: '-.02em', lineHeight: 1.25 }}>
            Morning, Nadia.
            <span style={{ color: 'var(--text-3)', display: 'block' }}>Five things need you.</span>
          </h1>
        </div>

        {/* KPI grid 2×2 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {ARC_KPIS.map((k, i) => (
            <MobileKpi key={k.label} {...k} accent={i === 0} />
          ))}
        </div>

        {/* Awaiting you */}
        <div>
          <SectionHeader kicker="01" title="Awaiting you" right={
            <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>5 · 2 high</span>
          } />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {ARC_INBOX.slice(0, 3).map((it) => <InboxRow key={it.id} item={it} />)}
            <button className="arc-btn ghost" style={{ width: '100%', justifyContent: 'center' }}>
              See all 5 · <Ico name="chevright" size={12} />
            </button>
          </div>
        </div>

        {/* Pinned items strip */}
        <div>
          <SectionHeader kicker="02" title="Pinned" right={
            <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>Swipe →</span>
          } />
          <div style={{ display: 'flex', gap: 10, overflowX: 'auto', margin: '0 -16px', padding: '0 16px', scrollbarWidth: 'none' }}>
            {[ARC_ITEMS[0], ARC_ITEMS[2], ARC_ITEMS[4], ARC_ITEMS[7]].map((it) => (
              <ItemTile key={it.id} item={it} width={170} />
            ))}
          </div>
        </div>

        {/* Stream preview */}
        <div className="arc-card" style={{ padding: '14px 14px 10px' }}>
          <SectionHeader kicker="03" title="Stream" right={
            <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>Following</span>
          } />
          {ARC_ACTIVITY.slice(0, 3).map((a, i) => <ActivityRow key={i} {...a} />)}
        </div>
      </div>
    </MobileShell>
  );
}

function MobileKpi({ label, val, delta, tone = 'normal', accent }) {
  const toneColor = { good: 'var(--accent)', warn: 'var(--warn)', bad: 'var(--danger)', normal: 'var(--text-2)' }[tone];
  return (
    <div className="arc-card" style={{
      padding: '12px 14px',
      background: accent ? 'color-mix(in oklch, var(--accent) 10%, var(--surface))' : undefined,
      borderColor: accent ? 'color-mix(in oklch, var(--accent) 35%, var(--line))' : undefined,
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-2)' }}>{label}</div>
      <div style={{
        fontSize: 22, lineHeight: 1.1, fontWeight: 500, marginTop: 2,
        fontFamily: 'var(--font-mono)', color: 'var(--text)', fontVariantNumeric: 'tabular-nums',
      }}>{val}</div>
      <div style={{ fontSize: 10.5, color: toneColor, marginTop: 4 }}>{delta}</div>
    </div>
  );
}

/* ─────────────── Mobile List ────────────────────────────────────────────── */
function MobileList({ native = false }) {
  return (
    <MobileShell active="items" title="Items" native={native} headerRight={
      <>
        <span style={{ color: 'var(--text-3)' }}><Ico name="filter" size={17} /></span>
        <span style={{ color: 'var(--text-3)' }}><Ico name="plus" size={17} /></span>
      </>
    }>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Search */}
        <div style={{ padding: '12px 16px 6px' }}>
          <div className="arc-cmd" style={{ width: '100%', height: 36 }}>
            <span style={{ color: 'var(--text-3)', display: 'flex' }}><Ico name="search" size={14} /></span>
            <span style={{ flex: 1, color: 'var(--text-3)', fontSize: 13 }}>Find by ID, name, or owner</span>
            <KBD>⌘K</KBD>
          </div>
        </div>

        {/* Filter chips */}
        <div className="arc-scroll" style={{
          padding: '8px 16px 10px', display: 'flex', gap: 6, overflowX: 'auto',
          borderBottom: '1px solid var(--line)',
        }}>
          <span className="arc-chip active" style={{ whiteSpace: 'nowrap' }}>Open</span>
          <span className="arc-chip" style={{ whiteSpace: 'nowrap' }}>Mine</span>
          <span className="arc-chip" style={{ whiteSpace: 'nowrap' }}>Parts</span>
          <span className="arc-chip" style={{ whiteSpace: 'nowrap' }}>Changes</span>
          <span className="arc-chip" style={{ whiteSpace: 'nowrap' }}>M4 program</span>
          <span className="arc-chip" style={{ whiteSpace: 'nowrap' }}>Last 7d</span>
        </div>

        {/* Sticky-ish group + items */}
        <MobileGroup label="In progress · 4" status="progress">
          {ARC_ITEMS.filter((i) => i.status === 'progress').map((it) =>
            <MobileItemRow key={it.id} item={it} />)}
        </MobileGroup>

        <MobileGroup label="In review · 3" status="review">
          {ARC_ITEMS.filter((i) => i.status === 'review').map((it) =>
            <MobileItemRow key={it.id} item={it} />)}
        </MobileGroup>

        <MobileGroup label="Released · 4" status="released">
          {ARC_ITEMS.filter((i) => i.status === 'released').slice(0, 3).map((it) =>
            <MobileItemRow key={it.id} item={it} />)}
        </MobileGroup>
      </div>
    </MobileShell>
  );
}

function MobileGroup({ label, status, children }) {
  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '14px 16px 6px',
        fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
        textTransform: 'uppercase', color: 'var(--text-3)',
      }}>
        <Status value={status} />
        {label}
      </div>
      <div style={{ borderTop: '1px solid var(--line)' }}>
        {children}
      </div>
    </div>
  );
}

function MobileItemRow({ item }) {
  return (
    <div style={{
      padding: '12px 16px',
      borderBottom: '1px solid var(--line)',
      display: 'flex', gap: 12, alignItems: 'center',
    }}>
      <Status value={item.status} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
          <MonoId id={item.id} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--text-3)' }}>rev {item.rev}</span>
        </div>
        <div style={{ fontSize: 13.5, color: 'var(--text)', lineHeight: 1.3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.name}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 5 }}>
          <Avatar id={item.owner} size={18} />
          <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{item.classification} · {item.updated}</span>
        </div>
      </div>
      <span style={{ color: 'var(--text-3)' }}><Ico name="chevright" size={13} /></span>
    </div>
  );
}

/* ─────────────── Mobile Form (item detail) ──────────────────────────────── */
function MobileForm({ native = false }) {
  const item = ARC_ITEMS[5]; // ECO-00471
  const [tab, setTab] = React.useState('overview');
  return (
    <MobileShell active="items" title="" native={native} headerRight={
      <>
        <span style={{ color: 'var(--text-3)' }}><Ico name="share" size={17} /></span>
        <span style={{ color: 'var(--text-3)' }}><Ico name="more" size={17} /></span>
      </>
    }>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{
          padding: '8px 16px 18px',
          borderBottom: '1px solid var(--line)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 10.5, padding: '2px 8px',
              border: '1px solid var(--line)', borderRadius: 4, color: 'var(--text-2)',
              textTransform: 'uppercase', letterSpacing: '.14em',
            }}>Change · ECO</span>
            <Status value={item.status} label />
          </div>
          <div style={{ marginBottom: 8 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, color: 'var(--accent)', fontWeight: 500, marginBottom: 4 }}>
              ARC<span style={{ color: 'var(--text-3)' }}>·</span>{item.id}
            </div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 500, color: 'var(--text)', letterSpacing: '-.01em', lineHeight: 1.3 }}>
              {item.name}
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text-3)', flexWrap: 'wrap' }}>
            <Avatar id="NW" size={18} />
            <span>Nadia W.</span>
            <span>·</span>
            <span>Severity <span style={{ color: 'var(--warn)' }}>● High</span></span>
            <span>·</span>
            <span>+$0.42/u</span>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ padding: '0 16px', borderBottom: '1px solid var(--line)' }}>
          <Tabs
            value={tab}
            onChange={setTab}
            size="sm"
            items={[
              { key: 'overview', label: 'Overview' },
              { key: 'affected', label: 'Affected · 3' },
              { key: 'thread',   label: 'Thread · 5' },
              { key: 'flow',     label: 'Flow' },
              { key: 'history',  label: 'History' },
            ]}
          />
        </div>

        {/* Body */}
        <div style={{ padding: '16px 16px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          <Field label="Summary">
            <div style={{ fontSize: 13.5, color: 'var(--text-2)', lineHeight: 1.55 }}>
              Move sensor-mount bracket L from PA-6 to 30% glass-filled nylon. Same supplier
              (Aril), same lead time. Stress margin improves 1.4× → 1.8× at the L1 boss.
              Triggered by repeat fracture in bench rig on 2026-05-19.
            </div>
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <Field label="Type" value="Material" mono readOnly />
            <Field label="Target rev" value="C → D" mono readOnly />
            <Field label="Cost impact" value="+$0.42/u" mono readOnly />
            <Field label="Lead time" value="No change" mono readOnly />
          </div>

          {/* Lifecycle compact */}
          <div className="arc-card" style={{ padding: 14 }}>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
              textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 10,
            }}>Lifecycle</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {['Draft','Eng','CCB','Released'].map((s, i) => (
                <React.Fragment key={s}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <span style={{
                      width: 10, height: 10, borderRadius: 999,
                      background: i < 1 ? 'var(--accent)' : 'transparent',
                      border: i === 1 ? '2px solid var(--accent)' : `2px solid ${i < 1 ? 'var(--accent)' : 'var(--line-2)'}`,
                    }} />
                    <span style={{ fontSize: 10.5, color: i === 1 ? 'var(--text)' : 'var(--text-3)', fontWeight: i === 1 ? 600 : 400 }}>{s}</span>
                  </div>
                  {i < 3 && <span style={{ flex: 1, height: 2, background: i < 1 ? 'var(--accent)' : 'var(--line)' }} />}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Affected items snippet */}
          <div>
            <SectionHeader kicker="02" title="Affected items" right={
              <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>3</span>
            } />
            <div className="arc-card" style={{ padding: 0, overflow: 'hidden' }}>
              {[ARC_ITEMS[4], ARC_ITEMS[2]].map((it, i) => (
                <div key={it.id} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '11px 14px',
                  borderTop: i === 0 ? 'none' : '1px solid var(--line)',
                }}>
                  <Status value={it.status} />
                  <MonoId id={it.id} />
                  <span style={{ flex: 1 }} />
                  <Avatar id={it.owner} size={20} />
                </div>
              ))}
            </div>
          </div>

          {/* Thread snippet */}
          <div>
            <SectionHeader kicker="03" title="Thread" right={
              <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>5 posts</span>
            } />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {ARC_THREAD.slice(0, 2).map((p, i) => (
                <div key={i} style={{ display: 'flex', gap: 10 }}>
                  <Avatar id={p.who} size={24} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 2 }}>
                      <span style={{ fontSize: 12.5, color: 'var(--text)', fontWeight: 500 }}>{ARC_USERS[p.who].name.split(' ')[0]}</span>
                      <span className="arc-mono" style={{ fontSize: 10.5, color: 'var(--text-3)' }}>{p.at}</span>
                    </div>
                    <div style={{ fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.55 }}>{p.body}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sticky action bar */}
        <div style={{
          position: 'sticky', bottom: 0,
          padding: '12px 16px',
          background: native
            ? 'color-mix(in oklch, var(--bg) 80%, transparent)'
            : 'var(--bg-2)',
          backdropFilter: native ? 'blur(20px)' : undefined,
          borderTop: '1px solid var(--line)',
          display: 'flex', gap: 10,
        }}>
          <button className="arc-btn" style={{ flex: 1, justifyContent: 'center' }}>Defer</button>
          <button className="arc-btn primary" style={{ flex: 2, justifyContent: 'center' }}>
            <Ico name="check" size={14} /> Approve
          </button>
        </div>
      </div>
    </MobileShell>
  );
}

Object.assign(window, { MobileShell, MobileDashboard, MobileList, MobileForm });
