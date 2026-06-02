export const DEV_CORE = '/dev'
export const DEV_APP = '/dev/dev'

export const devApi = {
  activityHeatmap: `${DEV_APP}/activity-heatmap`,
  appsStatus: `${DEV_APP}/apps-status`,
  config: `${DEV_APP}/config`,
  errors: `${DEV_APP}/errors`,
  errorsTail: `${DEV_APP}/errors/tail`,
  fieldReorder: `${DEV_APP}/field-reorder`,
  handoffRuns: `${DEV_CORE}/dev_handoff_runs`,
  info: `${DEV_CORE}/info`,
  inspectModels: `${DEV_CORE}/inspect/models`,
  inspectRoutes: `${DEV_CORE}/inspect/routes`,
  metadataFlush: `${DEV_CORE}/metadata/flush`,
  metrics: `${DEV_APP}/metrics`,
  migrations: `${DEV_APP}/migrations`,
  permissionsMatrix: `${DEV_APP}/permissions-matrix`,
  permissionsSimulate: `${DEV_CORE}/permissions/simulate`,
  relations: (name: string) => `${DEV_APP}/relations/${encodeURIComponent(name)}`,
  scaffold: `${DEV_APP}/scaffold`,
  schemaDiff: `${DEV_APP}/schema-diff`,
  sql: `${DEV_APP}/sql`,
  stats: `${DEV_CORE}/stats`,
  styleOverrides: `${DEV_APP}/style-overrides`,
  sync: `${DEV_CORE}/sync`,
  systemInfo: `${DEV_APP}/system-info`,
  impersonate: `${DEV_APP}/impersonate`,
}

export function withQuery(path: string, query: Record<string, string | number | boolean | null | undefined>) {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') params.set(key, String(value))
  })
  const search = params.toString()
  return search ? `${path}?${search}` : path
}
