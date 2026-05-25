import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../lib/api'

interface WebPage {
  id: number
  slug: string
  title: string
  content: string
  meta_title?: string | null
  meta_description?: string | null
  template?: string | null
}

export default function WebPageView() {
  const { slug } = useParams()
  const [page, setPage] = useState<WebPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!slug) return

    const fetchPage = async () => {
      setLoading(true)
      setNotFound(false)
      try {
        const response = await api.get(`/web/pages/${slug}`)
        setPage(response.data)
      } catch (err: any) {
        if (err.response?.status === 404) {
          setNotFound(true)
        } else {
          setNotFound(true)
        }
      } finally {
        setLoading(false)
      }
    }

    fetchPage()
  }, [slug])

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-12 text-sm text-[var(--app-muted)]">
        Loading...
      </main>
    )
  }

  if (notFound || !page) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-2xl font-bold text-[var(--app-text)]">Page not found</h1>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-bold text-[var(--app-text)]">{page.title}</h1>
      <div
        className="prose prose-slate mt-8 max-w-none"
        dangerouslySetInnerHTML={{ __html: page.content }}
      />
    </main>
  )
}
