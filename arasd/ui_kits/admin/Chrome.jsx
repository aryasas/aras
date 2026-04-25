// Aras admin chrome: Sidebar, TopBar, MenuBar, PageTitleStrip
const C = {
  brand: '#1f2a44', brandDeep: '#141b2d',
  ink: '#313b3d', ink2: '#6c757d', ink3: '#9aacb8', ink4: '#8a9bb0',
  line: '#eef0f2', line2: '#dde3e7', surface: '#fff', surfaceAlt: '#f4f6f8',
  bg: '#f8f9fa', primary: '#5a6fd6',
};

function Sidebar({ active, onNav }) {
  const items = [
    { id: 'dashboard', icon: 'ti-home', label: 'Dashboard' },
    { id: 'users', icon: 'fa fa-users', label: 'Users' },
    { id: 'apps', icon: 'ti-layout-grid2', label: 'App Builder' },
    { id: 'database', icon: 'ti-server', label: 'Database' },
    { id: 'notes', icon: 'fa fa-file-text-o', label: 'Notes' },
  ];
  return (
    <aside style={{ width: 220, background: C.brand, color: '#fff', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
      <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(255,255,255,.08)' }}>
        <a onClick={() => onNav('dashboard')} style={{ fontFamily: '"Libre Baskerville", "Iowan Old Style", Georgia, serif', fontWeight: 700, fontSize: 40, color: '#fff', letterSpacing: '-0.025em', lineHeight: 1, cursor: 'pointer' }}>aras</a>
      </div>
      <nav style={{ padding: '12px 0', flex: 1 }}>
        {items.map(it => (
          <a key={it.id} onClick={() => onNav(it.id)}
            style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 24px', color: active === it.id ? '#fff' : 'rgba(255,255,255,.85)', background: active === it.id ? C.brandDeep : 'transparent', fontSize: 13, cursor: 'pointer', textDecoration: 'none' }}>
            <i className={it.icon.startsWith('fa') ? it.icon : it.icon} style={{ width: 16, textAlign: 'center', fontSize: 14 }} />
            <span>{it.label}</span>
          </a>
        ))}
        <div style={{ margin: '10px 24px', borderTop: '1px solid rgba(255,255,255,.1)' }} />
        <a onClick={() => onNav('settings')}
          style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 24px', color: active === 'settings' ? '#fff' : 'rgba(255,255,255,.75)', background: active === 'settings' ? C.brandDeep : 'transparent', fontSize: 13, cursor: 'pointer' }}>
          <i className="ti-settings" style={{ width: 16, textAlign: 'center', fontSize: 14 }} />
          <span>Settings</span>
        </a>
      </nav>
    </aside>
  );
}

function TopBar({ title, crumb, onLogout }) {
  return (
    <div style={{ background: '#fff', borderBottom: `1px solid ${C.line}`, padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <button style={{ background: 'none', border: 'none', color: C.ink2, fontSize: 16, cursor: 'pointer' }}><i className="ti-menu" /></button>
        <button style={{ background: C.surfaceAlt, border: `1px solid ${C.line2}`, borderRadius: 4, color: C.ink2, padding: '4px 8px', fontSize: 12, cursor: 'pointer' }}><i className="fa fa-chevron-left" /></button>
        <button style={{ background: C.surfaceAlt, border: `1px solid ${C.line2}`, borderRadius: 4, color: C.ink2, padding: '4px 8px', fontSize: 12, cursor: 'pointer' }}><i className="fa fa-chevron-right" /></button>
        <div style={{ lineHeight: 1.2 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: C.ink }}>{title}</div>
          <div style={{ fontSize: 12, color: C.ink3 }}>Home{crumb ? ` / ${crumb}` : ''}</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <i className="ti-fullscreen" style={{ color: C.ink2, fontSize: 16 }} />
        <span style={{ position: 'relative', color: C.ink2, fontSize: 16 }}>
          <i className="ti-bell" />
          <span style={{ position: 'absolute', top: -6, right: -6, background: '#dc3545', color: '#fff', fontSize: 9, padding: '0 4px', borderRadius: 8 }}>3</span>
        </span>
        <i className="fa fa-envelope-o" style={{ color: C.ink2, fontSize: 16 }} />
        <i className="ti-settings" style={{ color: C.ink2, fontSize: 16 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: C.ink }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'linear-gradient(135deg,#5a6fd6,#1f2a44)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: 12 }}>JD</div>
          <span>jdoe</span>
          <a onClick={onLogout} style={{ color: '#dc3545', cursor: 'pointer', fontSize: 12, marginLeft: 4 }}>Logout</a>
        </div>
      </div>
    </div>
  );
}

function MenuBar({ onNav }) {
  const apps = [
    { icon: 'fa fa-users', title: 'Users', id: 'users' },
    { icon: 'ti-layout-grid2', title: 'App Builder', id: 'apps' },
    { icon: 'ti-server', title: 'Database', id: 'database' },
    { icon: 'fa fa-file-text-o', title: 'Notes', id: 'notes' },
  ];
  return (
    <div style={{ background: '#fff', borderBottom: `1px solid ${C.line}`, padding: '0 24px', display: 'flex', alignItems: 'center', gap: 2, minHeight: 36 }}>
      <a onClick={() => onNav('dashboard')} style={{ display: 'inline-flex', alignItems: 'center', padding: '6px 10px', fontSize: 12, color: C.ink2, cursor: 'pointer', borderRadius: 3 }}>
        <i className="ti-home" />
      </a>
      <span style={{ color: C.line2, fontSize: 12 }}>|</span>
      {apps.map(a => (
        <a key={a.id} onClick={() => onNav(a.id)} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 12px', fontSize: 12, color: C.ink, cursor: 'pointer', fontWeight: 500, borderRadius: 3 }}>
          <i className={a.icon} style={{ fontSize: 11 }} />
          {a.title}
        </a>
      ))}
    </div>
  );
}

function PageTitleStrip({ tabs, active, onPick }) {
  return (
    <div style={{ padding: '0 30px', borderBottom: `1px solid ${C.line}`, background: '#fff' }}>
      <nav style={{ display: 'flex', gap: 0 }}>
        {tabs.map(t => {
          const on = t.id === active;
          return (
            <a key={t.id} onClick={() => onPick(t.id)} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '10px 18px', fontSize: 13,
              color: on ? C.ink : C.ink2, fontWeight: on ? 600 : 400,
              textDecoration: 'none', cursor: 'pointer',
              borderBottom: `2px solid ${on ? C.primary : 'transparent'}`,
            }}>
              <i className={t.icon} /> {t.label}
            </a>
          );
        })}
      </nav>
    </div>
  );
}

Object.assign(window, { Sidebar, TopBar, MenuBar, PageTitleStrip, ARAS_C: C });
