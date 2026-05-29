import api from '../../lib/api'

export async function exportCsv(resourceApiPath: string, filename: string) {
  const res = await api.get(`/${resourceApiPath}/export`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function importCsv(resourceApiPath: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  await api.post(`/${resourceApiPath}/import`, formData)
}

export async function bulkDelete(resourceApiPath: string, ids: Array<string | number>) {
  await api.post(`/${resourceApiPath}/batch-delete`, { ids })
}

export async function bulkArchive(resourceApiPath: string, ids: Array<string | number>) {
  await api.post(`/${resourceApiPath}/batch-archive`, { ids })
}
