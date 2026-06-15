import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
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

function pageChrome(template?: string | null) {
  if (template === 'landing') {
    return {
      outer: 'arc arc-bg min-h-screen',
      inner: 'mx-auto max-w-none',
      body: 'px-0 py-0',
      content: 'w-full',
    }
  }
  if (template === 'full_width') {
    return {
      outer: 'arc arc-bg min-h-screen',
      inner: 'mx-auto max-w-6xl px-6 py-14',
      body: 'arc-card overflow-hidden bg-[var(--surface)] p-8 shadow-[var(--shadow-premium)]',
      content: 'cms-content max-w-none',
    }
  }
  return {
    outer: 'arc arc-bg min-h-screen',
    inner: 'mx-auto max-w-4xl px-6 py-14',
    body: 'arc-card overflow-hidden bg-[var(--surface)] p-8 shadow-[var(--shadow-premium)]',
    content: 'cms-content prose prose-slate max-w-none',
  }
}

export default function WebPageView() {
  const { slug } = useParams()
  const [page, setPage] = useState<WebPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const safeContent = useMemo(() => sanitizeHtml(page?.content || ''), [page?.content])
  const chrome = pageChrome(page?.template)

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

  useEffect(() => {
    if (!page) return
    document.title = page.meta_title || page.title || 'Aras'

    let meta = document.querySelector('meta[name="description"]') as HTMLMetaElement | null
    if (!meta) {
      meta = document.createElement('meta')
      meta.name = 'description'
      document.head.appendChild(meta)
    }
    meta.content = page.meta_description || ''
  }, [page])

  if (loading) {
    return (
      <main className="arc arc-bg min-h-screen">
        <div className="mx-auto max-w-4xl px-6 py-14 text-sm text-[var(--app-muted)]">Loading…</div>
      </main>
    )
  }

  if (notFound || !page) {
    return (
      <main className="arc arc-bg min-h-screen">
        <section className="mx-auto max-w-3xl px-6 py-14">
          <div className="arc-card bg-[var(--surface)] p-8 text-center shadow-[var(--shadow-premium)]">
            <p className="arc-id"><b>arc</b>/cms/<b>page</b></p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[var(--text)]">Page not found</h1>
            <p className="mt-3 text-sm leading-6 text-[var(--text-2)]">This CMS page is not published or the link is no longer available.</p>
            <Link to="/welcome" className="arc-btn primary mt-6 inline-flex">Back to home</Link>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className={chrome.outer}>
      <section className={chrome.inner}>
        {page.template === 'landing' ? null : (
          <div className="mb-8">
            <p className="arc-id"><b>arc</b>/cms/<b>{page.slug}</b></p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-[var(--text)]">{page.title}</h1>
            {page.meta_description ? <p className="mt-3 max-w-2xl text-base leading-7 text-[var(--text-2)]">{page.meta_description}</p> : null}
          </div>
        )}
        <div className={chrome.body}>
          <div
            className={chrome.content}
            dangerouslySetInnerHTML={{ __html: safeContent }}
          />
        </div>
      </section>
    </main>
  )
}
