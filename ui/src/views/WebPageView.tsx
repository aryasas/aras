import { useEffect, useMemo, useState } from 'react'
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

function sanitizeHtml(html: string) {
  if (typeof window === 'undefined') return ''

  const doc = new DOMParser().parseFromString(html, 'text/html')
  const blockedTags = new Set(['script', 'style', 'iframe', 'object', 'embed', 'link', 'meta', 'base', 'form'])
  doc.body.querySelectorAll('*').forEach((node) => {
    const element = node as HTMLElement
    if (blockedTags.has(element.tagName.toLowerCase())) {
      element.remove()
      return
    }

    Array.from(element.attributes).forEach((attr) => {
      const name = attr.name.toLowerCase()
      const value = attr.value.trim().toLowerCase()
      if (name.startsWith('on') || value.startsWith('javascript:') || value.startsWith('data:text/html')) {
        element.removeAttribute(attr.name)
      }
    })
  })
  return doc.body.innerHTML
}

export default function WebPageView() {
  const { slug } = useParams()
  const [page, setPage] = useState<WebPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const safeContent = useMemo(() => sanitizeHtml(page?.content || ''), [page?.content])

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
        dangerouslySetInnerHTML={{ __html: safeContent }}
      />
    </main>
  )
}
