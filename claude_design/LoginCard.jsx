// Login card — white on brand, Libre Baskerville serif lockup
function LoginCard({ onLogin }) {
  const [u, setU] = React.useState('jdoe');
  const [p, setP] = React.useState('••••••••');
  return (
    <div style={{ minHeight: '100%', background: '#1f2a44', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
      <form onSubmit={(e) => { e.preventDefault(); onLogin(u); }}
        style={{ width: 380, background: '#fff', borderRadius: 8, padding: '32px 32px 24px', boxShadow: '0 8px 24px rgba(0,0,0,.22)' }}>
        <div style={{ fontFamily: '"Libre Baskerville", "Iowan Old Style", Georgia, serif', fontWeight: 700, fontSize: 42, color: '#0f1b2d', textAlign: 'center', lineHeight: 1, letterSpacing: '-0.025em' }}>aras</div>
        <div style={{ textAlign: 'center', color: '#6c757d', fontSize: 13, margin: '8px 0 20px' }}>Please sign in</div>

        <Input label="Email or Username" icon="ti-email" value={u} onChange={e => setU(e.target.value)} />
        <Input label="Password" icon="ti-lock" type="password" value={p} onChange={e => setP(e.target.value)} />

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#6c757d', marginBottom: 16 }}>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <input type="checkbox" defaultChecked /> Remember Me
          </label>
          <a style={{ color: '#5a6fd6', cursor: 'pointer' }}>Forgot Password?</a>
        </div>

        <button type="submit" style={{ width: '100%', height: 42, background: '#5a6fd6', color: '#fff', border: 0, borderRadius: 4, fontWeight: 500, fontSize: 14, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6, cursor: 'pointer', fontFamily: 'inherit' }}>
          Login <i className="ti-arrow-right" />
        </button>

        <div style={{ textAlign: 'center', fontSize: 12, color: '#6c757d', marginTop: 16 }}>
          Don't have an account? <a style={{ color: '#5a6fd6', cursor: 'pointer' }}>Create Account</a>
        </div>
      </form>
    </div>
  );
}

Object.assign(window, { LoginCard });
