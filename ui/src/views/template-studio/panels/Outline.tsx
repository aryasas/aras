import { useMemo, useState, type ReactElement } from 'react'
import { useEditor } from '@craftjs/core'
import { ChevronDown, ChevronRight, Search } from 'lucide-react'

function inferLabel(node: { data: { displayName: string; props: Record<string, unknown> } }) {
  const props = node.data.props
  return String(
    props.label
    ?? props.title
    ?? props.text
    ?? props.brand
    ?? props.userName
    ?? node.data.displayName,
  )
}

export function Outline() {
  const { nodes, selectedId, actions } = useEditor((state, query) => ({
    nodes: query.getNodes(),
    selectedId: Array.from(state.events.selected)[0] ?? null,
  }))
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    ROOT: true,
  })

  const normalizedSearch = search.trim().toLowerCase()

  const filteredIds = useMemo(() => {
    if (!normalizedSearch) return null
    const keep = new Set<string>()

    const visit = (id: string): boolean => {
      const node = nodes[id]
      if (!node) return false
      const label = inferLabel(node).toLowerCase()
      const matches = label.includes(normalizedSearch) || node.data.displayName.toLowerCase().includes(normalizedSearch)
      const childMatches = node.data.nodes.some((childId) => visit(childId))
      if (matches || childMatches) keep.add(id)
      return matches || childMatches
    }

    visit('ROOT')
    return keep
  }, [nodes, normalizedSearch])

  const renderNode = (id: string, depth = 0): ReactElement | null => {
    const node = nodes[id]
    if (!node) return null
    if (filteredIds && !filteredIds.has(id)) return null

    const hasChildren = node.data.nodes.length > 0
    const isExpanded = expanded[id] ?? depth < 2
    const label = inferLabel(node)

    return (
      <div key={id}>
        <button
          type="button"
          onClick={() => actions.selectNode(id)}
          className={[
            'flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-left text-sm transition-colors',
            selectedId === id
              ? 'bg-[rgba(20,184,166,0.12)] text-[var(--ts-brand-700)]'
              : 'text-[var(--ts-surface-700)] hover:bg-[var(--ts-surface-50)]',
          ].join(' ')}
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
        >
          {hasChildren ? (
            <span
              onClick={(event) => {
                event.stopPropagation()
                setExpanded((current) => ({ ...current, [id]: !isExpanded }))
              }}
              className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-md"
            >
              {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            </span>
          ) : (
            <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--ts-surface-300)]" />
            </span>
          )}
          <span className="truncate font-medium">{label}</span>
          <span className="ml-auto rounded-full bg-[var(--ts-surface-100)] px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--ts-surface-500)]">
            {node.data.displayName}
          </span>
        </button>
        {hasChildren && isExpanded ? (
          <div>
            {node.data.nodes.map((childId) => renderNode(childId, depth + 1))}
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <div className="space-y-3 p-4">
      <div>
        <p className="text-[11px] font-black uppercase tracking-[0.24em] text-[var(--ts-surface-500)]">
          Outline
        </p>
        <p className="mt-1 text-xs text-[var(--ts-surface-500)]">
          Search the Craft tree and jump selection directly to any node.
        </p>
      </div>
      <label className="relative block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ts-surface-400)]" />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Find node"
          className="w-full rounded-2xl border border-[var(--ts-surface-200)] bg-white py-2.5 pl-9 pr-3 text-sm text-[var(--ts-surface-800)] outline-none"
        />
      </label>
      <div className="max-h-[420px] overflow-y-auto">
        {renderNode('ROOT')}
      </div>
    </div>
  )
}

export default Outline
