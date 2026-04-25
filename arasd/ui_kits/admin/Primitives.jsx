// Aras primitive components
const P_C = window.ARAS_C;

function Card({ children, style }) {
  return (
    <div style={{ background: '#fff', borderRadius: 6, boxShadow: '0 1px 2px rgba(20,27,45,.06)', ...style }}>
      {children}
    </div>
  );
}

function CardBody({ children, style }) {
  return <div style={{ padding: '20px 24px', ...style }}>{children}</div>;
}

function Button({ variant = 'primary', size = 'md', icon, children, onClick, type = 'button' }) {
  const variants = {
    primary: { background: '#5a6fd6', color: '#fff', border: '1px solid transparent' },
    outline: { background: '#fff', color: '#6c757d', border: '1px solid #dde3e7' },
    danger: { background: '#dc3545', color: '#fff', border: '1px solid transparent' },
    success: { background: '#fff', color: '#28a745', border: '1px solid #28a745' },
    warning: { background: '#fff', color: '#ffc107', border: '1px solid #ffc107' },
  };
  const sizes = {
    xs: { padding: '3px 8px', fontSize: 11 },
    sm: { padding: '5px 10px', fontSize: 12 },
    md: { padding: '8px 14px', fontSize: 13 },
    lg: { padding: '10px 18px', fontSize: 14 },
  };
  return (
    <button type={type} onClick={onClick} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, borderRadius: 4, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit', ...variants[variant], ...sizes[size] }}>
      {icon && <i className={icon} />}
      {children}
    </button>
  );
}

function Badge({ variant = 'secondary', children }) {
  const v = {
    success: { background: '#e6f6ea', color: '#1f7a36' },
    warning: { background: '#fff4cf', color: '#8a6d0b' },
    danger: { background: '#fbe4e6', color: '#b52633' },
    info: { background: '#e1f4f7', color: '#0e7585' },
    secondary: { background: '#f1f3f5', color: '#6c757d' },
    light: { background: '#fff', color: '#6c757d', border: '1px solid #eef0f2' },
    dark: { background: '#313b3d', color: '#fff' },
  };
  return <span style={{ display: 'inline-block', padding: '3px 8px', fontSize: 11, fontWeight: 500, borderRadius: 3, lineHeight: 1.2, ...v[variant] }}>{children}</span>;
}

function Input({ icon, label, error, ...rest }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: 'block', fontSize: 12, color: '#313b3d', fontWeight: 500, marginBottom: 6 }}>{label}</label>}
      <div style={{ position: 'relative' }}>
        {icon && <i className={icon} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9aacb8', fontSize: 14 }} />}
        <input {...rest} style={{ width: '100%', height: 40, padding: icon ? '8px 12px 8px 36px' : '8px 12px', border: `1px solid ${error ? '#dc3545' : '#dde3e7'}`, borderRadius: 4, fontFamily: 'inherit', fontSize: 13, color: '#313b3d', boxSizing: 'border-box', background: '#fff' }} />
      </div>
      {error && <div style={{ fontSize: 11, color: '#dc3545', marginTop: 4 }}>{error}</div>}
    </div>
  );
}

function Avatar({ name, size = 32 }) {
  const initials = (name || '?').split(/\s|\./).map(s => s[0] || '').join('').slice(0, 2).toUpperCase();
  return (
    <div style={{ width: size, height: size, borderRadius: '50%', background: 'linear-gradient(135deg,#5a6fd6,#1f2a44)', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: size * 0.4, flexShrink: 0 }}>
      {initials}
    </div>
  );
}

function SectionHeader({ title, count, children }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
      <h4 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#313b3d' }}>
        {title} {count != null && <Badge variant="secondary">{count}</Badge>}
      </h4>
      <div style={{ display: 'flex', gap: 6 }}>{children}</div>
    </div>
  );
}

Object.assign(window, { Card, CardBody, Button, Badge, Input, Avatar, SectionHeader });
