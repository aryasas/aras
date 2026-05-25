// Shared ARC UI primitives. All consume the CSS custom properties set on
// :root by ThemeApplier so density/radius/theme tweaks flow through.

// Mono ID label like "ARC·PRT-04812". The prefix is the brand token.
function MonoId({ id, prefix = 'ARC', size }) {
  return (
    <span className="arc-id" style={{ fontSize: size }}>
      <b>{prefix}</b><span style={{ opacity: .5, margin: '0 2px' }}>·</span>{id}
    </span>
  );
}

// Status glyph + optional label.
function Status({ value, label = false }) {
  const meta = STATUS_LABEL[value] || STATUS_LABEL.draft;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
      <span className={`arc-stat s-${value}`}>{meta.glyph}</span>
      {label && <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{meta.label}</span>}
    </span>
  );
}

// 24px avatar pulled from ARC_USERS. Initials look right in mono.
function Avatar({ id, size = 24, ring = false }) {
  const u = ARC_USERS[id] || { name: id, color: '#888' };
  const initials = id;
  return (
    <span
      className="arc-av"
      title={u.name}
      style={{
        width: size, height: size, fontSize: size * 0.42,
        background: `color-mix(in oklch, ${u.color} 22%, var(--surface))`,
        color: u.color,
        boxShadow: ring ? `0 0 0 1.5px var(--accent), 0 0 0 3px var(--bg)` : undefined,
        borderColor: 'var(--bg)',
      }}
    >{initials}</span>
  );
}

function AvatarStack({ ids, size = 22, max = 4 }) {
  const shown = ids.slice(0, max);
  const extra = ids.length - shown.length;
  return (
    <span style={{ display: 'inline-flex' }}>
      {shown.map((id, i) => (
        <span key={id + i} style={{ marginLeft: i === 0 ? 0 : -6 }}>
          <Avatar id={id} size={size} />
        </span>
      ))}
      {extra > 0 && (
        <span className="arc-av" style={{
          width: size, height: size, fontSize: size * 0.4,
          marginLeft: -6, background: 'var(--surface-2)', color: 'var(--text-2)',
        }}>+{extra}</span>
      )}
    </span>
  );
}

// Keyboard hint, e.g. <KBD>⌘K</KBD>
const KBD = ({ children }) => <span className="arc-kbd">{children}</span>;

// Big top command bar. Visual centerpiece — no traditional tree sidebar.
function CommandBar({ placeholder = 'Find an item, command, or person…', width = 520 }) {
  return (
    <div className="arc-cmd" style={{ width }}>
      <span style={{ color: 'var(--text-3)', display: 'flex' }}>
        <Ico name="search" size={14} />
      </span>
      <span style={{ flex: 1, color: 'var(--text-3)', fontSize: 13 }}>{placeholder}</span>
      <span style={{ display: 'flex', gap: 4 }}>
        <KBD>⌘</KBD><KBD>K</KBD>
      </span>
    </div>
  );
}

// Section header used inside dashboard cards.
function SectionHeader({ title, kicker, right }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
      padding: '0 0 12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        {kicker && (
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.16em',
            color: 'var(--text-3)', textTransform: 'uppercase',
          }}>{kicker}</span>
        )}
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{title}</h3>
      </div>
      <div>{right}</div>
    </div>
  );
}

// Tiny KPI card.
function KpiCard({ label, val, delta, tone = 'normal', accent = false }) {
  const toneColor = {
    good: 'var(--accent)', warn: 'var(--warn)', bad: 'var(--danger)', normal: 'var(--text-2)',
  }[tone] || 'var(--text-2)';
  return (
    <div className="arc-card" style={{
      padding: '14px 16px 16px',
      display: 'flex', flexDirection: 'column', gap: 4,
      minWidth: 0, flex: 1,
      background: accent ? 'color-mix(in oklch, var(--accent) 10%, var(--surface))' : undefined,
      borderColor: accent ? 'color-mix(in oklch, var(--accent) 35%, var(--line))' : undefined,
    }}>
      <div style={{ fontSize: 11.5, color: 'var(--text-2)' }}>{label}</div>
      <div style={{
        fontSize: 28, lineHeight: 1.1, fontWeight: 500,
        color: 'var(--text)', fontFamily: 'var(--font-mono)',
        fontVariantNumeric: 'tabular-nums', letterSpacing: '-.01em',
      }}>{val}</div>
      <div style={{ fontSize: 11, color: toneColor, marginTop: 2 }}>{delta}</div>
    </div>
  );
}

// Activity stream row.
function ActivityRow({ who, verb, obj, detail, at }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '8px 0' }}>
      <Avatar id={who} size={22} />
      <div style={{ minWidth: 0, flex: 1, fontSize: 12.5, lineHeight: 1.45, color: 'var(--text-2)' }}>
        <span style={{ color: 'var(--text)' }}>{ARC_USERS[who]?.name.split(' ')[0] || who}</span>
        <span> {verb} </span>
        <span className="arc-mono" style={{ color: 'var(--text)', fontSize: 11.5 }}>{obj}</span>
        <span style={{ display: 'block', color: 'var(--text-3)', fontSize: 12 }}>{detail}</span>
      </div>
      <div className="arc-mono" style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>{at}</div>
    </div>
  );
}

// Inbox card with priority bar.
function InboxRow({ item }) {
  const hi = item.priority === 'high';
  return (
    <div className="arc-card" style={{
      padding: '12px 14px', display: 'flex', gap: 12, alignItems: 'center',
      borderColor: hi ? 'color-mix(in oklch, var(--warn) 40%, var(--line))' : 'var(--line)',
      position: 'relative', cursor: 'pointer',
    }}>
      {hi && <span style={{
        position: 'absolute', left: 0, top: 8, bottom: 8, width: 2,
        background: 'var(--warn)', borderRadius: 2,
      }} />}
      <Avatar id={item.from} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          fontSize: 12, marginBottom: 3, color: 'var(--text-2)',
        }}>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 10.5, padding: '1px 6px',
            border: '1px solid var(--line)', borderRadius: 4, color: 'var(--text-2)',
            textTransform: 'uppercase', letterSpacing: '.08em',
          }}>{item.kind}</span>
          <MonoId id={item.id} />
        </div>
        <div style={{ fontSize: 13, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.title}
        </div>
      </div>
      <div className="arc-mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>{item.age}</div>
    </div>
  );
}

// Item card used in pinned/recent strips.
function ItemTile({ item, width = 200 }) {
  return (
    <div className="arc-card" style={{
      padding: '12px 14px', width, flexShrink: 0,
      display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <MonoId id={item.id} />
        <Status value={item.status} />
      </div>
      <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.35 }}>{item.name}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
        <Avatar id={item.owner} size={20} />
        <span className="arc-mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>rev {item.rev} · {item.updated}</span>
      </div>
    </div>
  );
}

// Tiny labeled field for form layouts. Read-only flavor uses dim background.
function Field({ label, value, mono = false, hint, readOnly = false, children, width }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, width }}>
      <label style={{
        fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '.14em',
        color: 'var(--text-3)', textTransform: 'uppercase',
      }}>{label}</label>
      {children || (
        <div className={'arc-input ' + (mono ? 'mono' : '')}
             style={{
               display: 'flex', alignItems: 'center',
               background: readOnly ? 'transparent' : 'var(--surface)',
               borderColor: readOnly ? 'transparent' : 'var(--line)',
               paddingLeft: readOnly ? 0 : 12,
               color: 'var(--text)',
             }}>{value}</div>
      )}
      {hint && <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{hint}</span>}
    </div>
  );
}

// Top icon nav strip — five glyphs, current state highlighted.
function NavStrip({ active = 'home', vertical = true }) {
  const items = [
    { key: 'home',     icon: 'home',     label: 'Home'     },
    { key: 'items',    icon: 'cube',     label: 'Items'    },
    { key: 'flow',     icon: 'flow',     label: 'Workflow' },
    { key: 'thread',   icon: 'thread',   label: 'Threads'  },
    { key: 'insights', icon: 'insights', label: 'Insights' },
  ];
  return (
    <div style={{
      display: 'flex', flexDirection: vertical ? 'column' : 'row',
      gap: 4, padding: vertical ? '14px 8px' : '8px 14px',
    }}>
      {items.map((it) => {
        const on = it.key === active;
        return (
          <div key={it.key}
            title={it.label}
            style={{
              width: 38, height: 38, display: 'flex', alignItems: 'center', justifyContent: 'center',
              borderRadius: 'var(--radius)', cursor: 'pointer', position: 'relative',
              color: on ? 'var(--text)' : 'var(--text-3)',
              background: on ? 'var(--surface-2)' : 'transparent',
              border: on ? '1px solid var(--line)' : '1px solid transparent',
            }}>
            <Ico name={it.icon} size={17} />
            {on && (
              <span style={{
                position: 'absolute', left: -8, top: 8, bottom: 8, width: 2,
                background: 'var(--accent)', borderRadius: 2,
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// Pill-style filter chip with optional remove.
function FilterChip({ children, active = false, onRemove }) {
  return (
    <span className={'arc-chip ' + (active ? 'active' : '')}>
      {children}
      {onRemove && <span className="x">×</span>}
    </span>
  );
}

// Tabs (anchor-style) — works on both desktop and mobile.
function Tabs({ items, value, onChange, size = 'md' }) {
  return (
    <div style={{
      display: 'flex', gap: size === 'sm' ? 6 : 18,
      borderBottom: '1px solid var(--line)',
      padding: '0 0',
    }}>
      {items.map((t) => {
        const on = t.key === value;
        return (
          <button key={t.key} onClick={() => onChange && onChange(t.key)}
            style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              color: on ? 'var(--text)' : 'var(--text-2)',
              fontFamily: 'var(--font-sans)', fontSize: size === 'sm' ? 12 : 13, fontWeight: 500,
              padding: size === 'sm' ? '8px 6px' : '12px 2px',
              borderBottom: on ? '2px solid var(--accent)' : '2px solid transparent',
              marginBottom: -1,
            }}>{t.label}</button>
        );
      })}
    </div>
  );
}

Object.assign(window, {
  MonoId, Status, Avatar, AvatarStack, KBD, CommandBar, SectionHeader,
  KpiCard, ActivityRow, InboxRow, ItemTile, Field, NavStrip, FilterChip, Tabs,
});
