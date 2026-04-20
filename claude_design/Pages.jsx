// Aras admin — page views wired into App
function PageDashboard({ onNav }) {
  const widgets = [
    {
      title: "Total Users",
      value: "128",
      icon: "fa fa-users",
      color: "primary",
      link: "View users",
    },
    {
      title: "Active Apps",
      value: "7",
      icon: "fa fa-cubes",
      color: "success",
      link: "App builder",
    },
    {
      title: "Tables",
      value: "32",
      icon: "fa fa-table",
      color: "info",
      link: "Database",
    },
    {
      title: "Pending",
      value: "4",
      icon: "fa fa-bell",
      color: "warning",
      link: "Activities",
    },
  ];
  const notes = [
    {
      who: "Ayu Hapsari",
      when: "7 minutes ago",
      body: "Prepared the Q2 inventory reconciliation script — please review before Monday.",
    },
    {
      who: "Rashed Kabir",
      when: "1 hour ago",
      body: "Added a new HR table for contract templates. Fields are ready to wire into the app.",
    },
    {
      who: "jdoe",
      when: "yesterday",
      body: "Database backup succeeded. Logs pushed to the activity feed.",
    },
  ];
  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <DashboardWidgets widgets={widgets} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <Card>
          <CardBody>
            <h4 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 600 }}>
              Notes
            </h4>
            <hr
              style={{
                border: 0,
                borderTop: "1px solid #eef0f2",
                margin: "12px 0",
              }}
            />
            {notes.map((n, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: 12,
                  padding: "10px 0",
                  borderBottom:
                    i < notes.length - 1 ? "1px solid #f0f3f5" : "none",
                }}
              >
                <Avatar name={n.who} size={40} />
                <div style={{ flex: 1 }}>
                  <div
                    style={{ fontSize: 13, fontWeight: 500, color: "#313b3d" }}
                  >
                    {n.who}
                  </div>
                  <div
                    style={{ fontSize: 11, color: "#9aacb8", marginBottom: 4 }}
                  >
                    Last seen: {n.when}
                  </div>
                  <div style={{ fontSize: 12, color: "#313b3d" }}>{n.body}</div>
                </div>
              </div>
            ))}
            <a
              onClick={() => onNav("notes")}
              style={{
                fontSize: 12,
                color: "#5a6fd6",
                display: "inline-block",
                marginTop: 10,
                cursor: "pointer",
              }}
            >
              Explore More →
            </a>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <h4 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 600 }}>
              Post
            </h4>
            <hr
              style={{
                border: 0,
                borderTop: "1px solid #eef0f2",
                margin: "12px 0",
              }}
            />
            <form onSubmit={(e) => e.preventDefault()}>
              <textarea
                placeholder="Say something to the team…"
                style={{
                  width: "100%",
                  minHeight: 80,
                  border: "1px solid #dde3e7",
                  borderRadius: 4,
                  padding: 10,
                  fontFamily: "inherit",
                  fontSize: 13,
                  color: "#313b3d",
                  resize: "vertical",
                  boxSizing: "border-box",
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginTop: 10,
                }}
              >
                <Button size="sm">Submit</Button>
              </div>
            </form>
            <hr
              style={{
                border: 0,
                borderTop: "1px solid #eef0f2",
                margin: "14px 0",
              }}
            />
            <div style={{ display: "flex", gap: 12, padding: "6px 0" }}>
              <Avatar name="Rashed Kabir" size={40} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>
                  Rashed Kabir
                </div>
                <div
                  style={{ fontSize: 11, color: "#9aacb8", marginBottom: 4 }}
                >
                  Last seen: lll
                </div>
                <div style={{ fontSize: 12 }}>
                  Sed ut perspiciatis unde omnis iste — posted 2 hours ago.
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function PageUsers({ users, onToggle }) {
  const cols = [
    { key: "id", label: "#" },
    {
      key: "avatar",
      label: "Avatar",
      render: (r) => <Avatar name={r.username} />,
    },
    { key: "username", label: "Username" },
    { key: "email", label: "Email" },
    {
      key: "role",
      label: "Role",
      render: (r) =>
        r.admin ? (
          <Badge variant="danger">Admin</Badge>
        ) : (
          <Badge variant="secondary">User</Badge>
        ),
    },
    {
      key: "status",
      label: "Status",
      render: (r) =>
        r.active ? (
          <Badge variant="success">Active</Badge>
        ) : (
          <Badge variant="secondary">Inactive</Badge>
        ),
    },
    { key: "joined", label: "Joined" },
  ];
  return (
    <div style={{ padding: 24 }}>
      <Card>
        <CardBody>
          <SectionHeader title="All Users" count={users.length}>
            <Button size="sm" icon="fa fa-plus">
              Add User
            </Button>
            <Button variant="outline" size="sm" icon="fa fa-download">
              Export CSV
            </Button>
          </SectionHeader>
          <DataTable
            columns={cols}
            rows={users}
            actions={(r) => (
              <div style={{ display: "inline-flex", gap: 4 }}>
                <Button size="xs" variant="outline">
                  View
                </Button>
                <Button
                  size="xs"
                  variant={r.active ? "warning" : "success"}
                  onClick={() => onToggle(r.id)}
                >
                  {r.active ? "Deactivate" : "Activate"}
                </Button>
              </div>
            )}
          />
        </CardBody>
      </Card>
    </div>
  );
}

function PageApps({ apps, onToggle, onDelete }) {
  const cols = [
    { key: "id", label: "#" },
    {
      key: "name",
      label: "Name",
      render: (r) => (
        <code
          style={{
            fontFamily: "SFMono-Regular, Menlo, monospace",
            background: "#f1f3f5",
            padding: "1px 6px",
            borderRadius: 3,
            fontSize: 11,
          }}
        >
          {r.name}
        </code>
      ),
    },
    { key: "title", label: "Title" },
    {
      key: "url",
      label: "URL",
      render: (r) => (
        <code
          style={{
            fontFamily: "SFMono-Regular, Menlo, monospace",
            background: "#f1f3f5",
            padding: "1px 6px",
            borderRadius: 3,
            fontSize: 11,
          }}
        >
          {r.url}
        </code>
      ),
    },
    {
      key: "tables",
      label: "Tables",
      render: (r) => <Badge variant="info">{r.tables} table(s)</Badge>,
    },
    {
      key: "active",
      label: "Active",
      render: (r) =>
        r.active ? (
          <Badge variant="success">Yes</Badge>
        ) : (
          <Badge variant="secondary">No</Badge>
        ),
    },
    {
      key: "sidebar",
      label: "Sidebar",
      render: (r) =>
        r.sidebar ? (
          <Badge variant="info">Yes</Badge>
        ) : (
          <Badge variant="light">No</Badge>
        ),
    },
    { key: "created", label: "Created" },
  ];
  return (
    <div style={{ padding: 24 }}>
      <Card>
        <CardBody>
          <SectionHeader title="App Manager" count={apps.length}>
            <Button variant="outline" size="sm" icon="fa fa-upload">
              Install from File
            </Button>
            <Button size="sm" icon="fa fa-plus">
              New App
            </Button>
          </SectionHeader>
          <DataTable
            columns={cols}
            rows={apps}
            actions={(r) => (
              <div style={{ display: "inline-flex", gap: 4 }}>
                <Button size="xs" variant="outline" icon="fa fa-columns" />
                <Button size="xs" variant="outline" icon="fa fa-edit" />
                <Button
                  size="xs"
                  variant={r.active ? "warning" : "success"}
                  icon={r.active ? "fa fa-pause" : "fa fa-play"}
                  onClick={() => onToggle(r.id)}
                />
                <Button
                  size="xs"
                  variant="danger"
                  icon="fa fa-trash"
                  onClick={() => {
                    if (window.confirm(`Delete app ${r.title}?`))
                      onDelete(r.id);
                  }}
                />
              </div>
            )}
          />
        </CardBody>
      </Card>
    </div>
  );
}

function PageSettings() {
  const [panel, setPanel] = React.useState("general");
  const items = [
    { id: "general", icon: "ti-settings", label: "General" },
    { id: "apps", icon: "ti-layout-grid2", label: "App Manager" },
    { id: "users", icon: "ti-user", label: "Users" },
    { id: "database", icon: "ti-server", label: "Database" },
    { id: "roles", icon: "ti-shield", label: "Roles & Permissions" },
  ];
  return (
    <div style={{ padding: 24 }}>
      <div
        style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 24 }}
      >
        <Card style={{ alignSelf: "start" }}>
          <div>
            {items.map((it, i) => (
              <div
                key={it.id}
                onClick={() => setPanel(it.id)}
                style={{
                  padding: "12px 16px",
                  cursor: "pointer",
                  borderTop: i === 0 ? "none" : "1px solid #eef0f2",
                  background: panel === it.id ? "#eef1fb" : "transparent",
                  color: panel === it.id ? "#4a5ec2" : "#313b3d",
                  fontWeight: panel === it.id ? 600 : 400,
                  fontSize: 13,
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <i
                  className={it.icon}
                  style={{
                    width: 16,
                    textAlign: "center",
                    color: panel === it.id ? "#5a6fd6" : "#8a9bb0",
                  }}
                />
                <span style={{ flex: 1 }}>{it.label}</span>
                {it.id === "roles" && <Badge variant="warning">Soon</Badge>}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardBody>
            {panel === "general" && (
              <>
                <h5 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
                  General Settings
                </h5>
                <p style={{ color: "#6c757d", fontSize: 12 }}>
                  Configure general application settings.
                </p>
                <hr
                  style={{
                    border: 0,
                    borderTop: "1px solid #eef0f2",
                    margin: "12px 0",
                  }}
                />
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 12,
                    fontSize: 13,
                  }}
                >
                  <div>
                    <b>App Name:</b> Aras
                  </div>
                  <div>
                    <b>Environment:</b> production
                  </div>
                  <div>
                    <b>Locale:</b> id-ID · en
                  </div>
                  <div>
                    <b>Version:</b> 0.9.2
                  </div>
                </div>
              </>
            )}
            {panel === "apps" && (
              <>
                <h5 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
                  App Manager
                </h5>
                <p style={{ color: "#6c757d", fontSize: 12 }}>
                  Apps are built dynamically and saved to the database.
                </p>
                <hr
                  style={{
                    border: 0,
                    borderTop: "1px solid #eef0f2",
                    margin: "12px 0",
                  }}
                />
                <p style={{ fontSize: 12 }}>
                  Switch to the <b>App Manager</b> page for the full CRUD view.
                </p>
              </>
            )}
            {panel === "users" && (
              <>
                <h5 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
                  Users
                </h5>
                <hr
                  style={{
                    border: 0,
                    borderTop: "1px solid #eef0f2",
                    margin: "12px 0",
                  }}
                />
                <p style={{ fontSize: 12 }}>
                  See the Users page for the full list.
                </p>
              </>
            )}
            {panel === "database" && (
              <>
                <h5 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
                  <i className="ti-server" style={{ marginRight: 6 }} />
                  Database
                </h5>
                <hr
                  style={{
                    border: 0,
                    borderTop: "1px solid #eef0f2",
                    margin: "12px 0",
                  }}
                />
                <div style={{ fontSize: 12, marginBottom: 12 }}>
                  <b>Connection:</b>{" "}
                  <code
                    style={{
                      background: "#f1f3f5",
                      padding: "1px 6px",
                      borderRadius: 3,
                    }}
                  >
                    postgresql://aras@db:5432/aras
                  </code>
                </div>
                <h6
                  style={{
                    margin: "4px 0 8px",
                    fontSize: 12,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: ".6px",
                    color: "#9aacb8",
                  }}
                >
                  Tables
                </h6>
                <DataTable
                  columns={[
                    {
                      key: "name",
                      label: "Table",
                      render: (r) => <code>{r.name}</code>,
                    },
                    {
                      key: "cols",
                      label: "Columns",
                      render: (r) => (
                        <small style={{ color: "#6c757d" }}>{r.cols}</small>
                      ),
                    },
                  ]}
                  rows={[
                    {
                      name: "users",
                      cols: "id, username, email, is_admin, is_active, created_at",
                    },
                    {
                      name: "apps",
                      cols: "id, name, title, url, is_active, in_sidebar, created_at",
                    },
                    {
                      name: "notes",
                      cols: "id, title, body, created_by_id, created_at",
                    },
                  ]}
                  actions={() => (
                    <Button variant="outline" size="xs" icon="fa fa-magic">
                      Generate View
                    </Button>
                  )}
                />
              </>
            )}
            {panel === "roles" && (
              <div style={{ textAlign: "center", padding: "40px 0" }}>
                <i
                  className="ti-shield"
                  style={{ fontSize: 48, color: "#dc3545", opacity: 0.4 }}
                />
                <h5
                  style={{ marginTop: 12, color: "#6c757d", fontWeight: 500 }}
                >
                  Roles &amp; Permissions — Coming Soon
                </h5>
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function PageNotes() {
  const rows = [
    {
      id: 1,
      title: "Q2 inventory reconciliation",
      created_by: "Ayu Hapsari",
      created_at: "12 Apr 2026",
    },
    {
      id: 2,
      title: "HR contract template fields",
      created_by: "Rashed Kabir",
      created_at: "10 Apr 2026",
    },
    {
      id: 3,
      title: "Database backup runbook",
      created_by: "jdoe",
      created_at: "02 Apr 2026",
    },
    {
      id: 4,
      title: "Sales app v2 migration plan",
      created_by: "jdoe",
      created_at: "28 Mar 2026",
    },
  ];
  return (
    <div style={{ padding: 24 }}>
      <Card>
        <CardBody>
          <SectionHeader title="Notes" count={rows.length}>
            <Button size="sm" icon="fa fa-plus">
              Add Note
            </Button>
          </SectionHeader>
          <DataTable
            columns={[
              { key: "id", label: "#" },
              { key: "title", label: "Title" },
              { key: "created_by", label: "Created by" },
              { key: "created_at", label: "Created at" },
            ]}
            rows={rows}
            actions={() => (
              <div style={{ display: "inline-flex", gap: 4 }}>
                <Button size="xs" variant="outline" icon="fa fa-edit" />
                <Button size="xs" variant="danger" icon="fa fa-trash" />
              </div>
            )}
          />
        </CardBody>
      </Card>
    </div>
  );
}

function PageDatabase() {
  return PageSettings.call(null); // reuse
}

Object.assign(window, {
  PageDashboard,
  PageUsers,
  PageApps,
  PageSettings,
  PageNotes,
});
