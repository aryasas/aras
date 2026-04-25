// Aras data table — canonical admin look: uppercase thead on bg-light, hairline rows
function DataTable({ columns, rows, actions }) {
  return (
    <div style={{ background: '#fff', borderRadius: 6, boxShadow: '0 1px 2px rgba(20,27,45,.06)', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead style={{ background: '#f8f9fa' }}>
          <tr>
            {columns.map(c => (
              <th key={c.key} style={{ textTransform: 'uppercase', letterSpacing: '.6px', fontSize: 10, color: '#6c757d', padding: '10px 14px', textAlign: 'left', fontWeight: 600, borderBottom: '1px solid #eef0f2' }}>{c.label}</th>
            ))}
            {actions && <th style={{ textTransform: 'uppercase', letterSpacing: '.6px', fontSize: 10, color: '#6c757d', padding: '10px 14px', textAlign: 'right', fontWeight: 600, borderBottom: '1px solid #eef0f2' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr><td colSpan={columns.length + (actions ? 1 : 0)} style={{ padding: 24, textAlign: 'center', color: '#6c757d' }}>No rows.</td></tr>
          )}
          {rows.map((r, i) => (
            <tr key={i} style={{ borderTop: i === 0 ? 'none' : '1px solid #eef0f2' }}
                onMouseEnter={e => e.currentTarget.style.background = '#f4f6f8'}
                onMouseLeave={e => e.currentTarget.style.background = '#fff'}>
              {columns.map(c => (
                <td key={c.key} style={{ padding: '10px 14px', color: '#313b3d', verticalAlign: 'middle' }}>
                  {c.render ? c.render(r) : r[c.key]}
                </td>
              ))}
              {actions && (
                <td style={{ padding: '8px 14px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                  {actions(r, i)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

Object.assign(window, { DataTable });
