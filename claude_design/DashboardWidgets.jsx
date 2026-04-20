// Aras dashboard stat widgets — colored left border, soft ghost icon
function StatWidget({ title, value, icon, color = 'primary', link }) {
  const c = { primary: '#5a6fd6', success: '#28a745', info: '#17a2b8', warning: '#8a6d0b', danger: '#dc3545' }[color];
  return (
    <div style={{ background: '#fff', borderRadius: 6, boxShadow: '0 1px 2px rgba(20,27,45,.06)', padding: '16px 18px', borderLeft: `4px solid ${c}`, position: 'relative', minHeight: 96 }}>
      <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.6px', color: c, marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: '#313b3d' }}>{value}</div>
      <i className={icon} style={{ position: 'absolute', top: 16, right: 16, fontSize: 28, color: '#e5e7eb' }} />
      {link && <a style={{ fontSize: 11, color: c, display: 'block', marginTop: 8, cursor: 'pointer' }}>{link} →</a>}
    </div>
  );
}

function DashboardWidgets({ widgets }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
      {widgets.map((w, i) => <StatWidget key={i} {...w} />)}
    </div>
  );
}

Object.assign(window, { StatWidget, DashboardWidgets });
