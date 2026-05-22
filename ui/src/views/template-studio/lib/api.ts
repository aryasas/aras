import type { SerializedNodes } from '@craftjs/core'
import api from '../../../lib/api'
import { cloneDefaultTree } from './defaultTree'
import type { Breakpoint } from './breakpoints'

export interface TemplateNotePayload {
  node_id: string
  node_kind: string
  node_label: string | null
  breakpoint: Breakpoint
  comment: string
  status: 'pending' | 'applied' | 'rejected'
  tree_json?: SerializedNodes
}

export async function loadTree(name: string): Promise<SerializedNodes> {
  try {
    const response = await api.get(`/dev/dev_template_trees?template_name=${encodeURIComponent(name)}`)
    const tree = response.data?.tree_json
    if (tree && typeof tree === 'object') {
      return tree as SerializedNodes
    }
  } catch (error) {
    console.warn('TemplateStudio: failed to load tree', error)
  }

  return cloneDefaultTree()
}

export async function saveTree(name: string, tree: SerializedNodes) {
  try {
    await api.post('/dev/dev_template_trees', {
      template_name: name,
      tree_json: tree,
    })
  } catch (error) {
    console.warn('TemplateStudio: failed to save tree', error)
  }
}

export async function flushNotes(
  name: string,
  notes: TemplateNotePayload[],
) {
  const results = await Promise.allSettled(
    notes.map((note) => api.post('/dev/dev_template_annotations', {
      template_name: name,
      node_id: note.node_id,
      node_kind: note.node_kind,
      node_label: note.node_label,
      breakpoint: note.breakpoint,
      comment: note.comment,
      status: note.status,
      tree_json: note.tree_json,
    })),
  )

  results.forEach((result) => {
    if (result.status === 'rejected') {
      console.warn('TemplateStudio: failed to flush annotation', result.reason)
    }
  })
}
