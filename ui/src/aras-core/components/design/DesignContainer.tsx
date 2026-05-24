import React, { useState } from 'react'
import { useUIStore } from '../../../store/uiStore'
import { DesignElement } from './DesignElement'

interface DesignContainerProps {
  id: string;
  children?: React.ReactNode;
  className?: string;
}

export const DesignContainer: React.FC<DesignContainerProps> = ({ id, children, className = '' }) => {
  const { designMode, designData, updateElementOrder, updateCustomElement } = useUIStore()
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  // Retrieve custom order from store, or fallback to default React children order
  const customOrder = designData.orders[id] || []
  
  // Convert static children to an array
  const staticChildren = React.Children.toArray(children)

  // Convert custom elements to React nodes
  const customChildren = Object.values(designData.customElements || {})
    .filter(el => el.parentId === id)
    .map(el => {
      if (el.type === 'text') {
        return <DesignElement key={el.id} id={el.id}>{el.content || 'New Text'}</DesignElement>
      }
      if (el.type === 'button') {
        return <DesignElement key={el.id} id={el.id} tagName="button" className="px-4 py-2 bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] font-bold">{el.content || 'Button'}</DesignElement>
      }
      if (el.type === 'divider') {
        return <DesignElement key={el.id} id={el.id} tagName="hr" className="border-t border-[var(--aras-border)] my-4" />
      }
      if (el.type === 'container') {
        return (
          <DesignElement key={el.id} id={`${el.id}-wrapper`}>
             <DesignContainer id={el.id} className="min-h-[50px]" />
          </DesignElement>
        )
      }
      return null
    }).filter(Boolean)

  const allChildren = [...staticChildren, ...customChildren]
  
  // Sort all children based on customOrder
  const sortedChildren = allChildren.sort((a, b) => {
    if (!React.isValidElement(a) || !React.isValidElement(b)) return 0
    const idA = (a as any).props.id || (a as any).key
    const idB = (b as any).props.id || (b as any).key
    if (!idA || !idB) return 0
    const idxA = customOrder.indexOf(idA)
    const idxB = customOrder.indexOf(idB)
    if (idxA === -1 && idxB === -1) return 0
    if (idxA === -1) return 1
    if (idxB === -1) return -1
    return idxA - idxB
  })

  const handleDragOver = (e: React.DragEvent, index: number) => {
    if (!designMode) return
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'move'
    setDragOverIndex(index)
  }

  const handleDrop = (e: React.DragEvent, index: number) => {
    if (!designMode) return
    e.preventDefault()
    e.stopPropagation()
    setDragOverIndex(null)
    
    const draggedId = e.dataTransfer.getData('text/plain')
    if (!draggedId) return

    // Get current IDs in sorted order
    const currentIds = sortedChildren.map(child => React.isValidElement(child) ? ((child as any).props.id || (child as any).key) : null).filter(Boolean)
    
    const fromIndex = currentIds.indexOf(draggedId)
    const newOrder = [...currentIds]

    if (fromIndex !== -1) {
      // Reordering within the same container
      newOrder.splice(fromIndex, 1)
      const targetIndex = fromIndex < index ? index - 1 : index
      newOrder.splice(targetIndex, 0, draggedId)
    } else {
      // Element dropped from outside
      // If it's a custom element, update its parent
      if (designData.customElements && designData.customElements[draggedId]) {
         updateCustomElement(draggedId, { parentId: id })
      }
      newOrder.splice(index, 0, draggedId)
    }

    updateElementOrder(id, newOrder)
  }

  return (
    <div className={`relative ${className} ${designMode ? 'outline-dashed outline-2 outline-[var(--aras-border)]/50 min-h-[50px] p-1 transition-all' : ''} ${dragOverIndex !== null ? 'bg-[var(--aras-panel-soft)]' : ''}`}>
      {designMode && (
        <div
           className="absolute -top-4 -left-1 bg-[var(--aras-panel-soft)] text-[var(--aras-muted)] text-[8px] font-black px-1.5 rounded-[var(--aras-radius)] uppercase tracking-widest pointer-events-none z-10"
        >
          {id}
        </div>
      )}
      
      {sortedChildren.map((child, index) => {
        const childId = React.isValidElement(child) ? ((child as any).props.id || (child as any).key) : index;
        return (
          <React.Fragment key={childId}>
            {designMode && (
              <div 
                className={`h-2 transition-all ${dragOverIndex === index ? 'bg-pink-400 rounded mx-1 my-0.5' : 'bg-transparent'}`}
                onDragOver={(e) => handleDragOver(e, index)}
                onDrop={(e) => handleDrop(e, index)}
              />
            )}
            {child}
          </React.Fragment>
        )
      })}
      
      {designMode && (
        <div 
          className={`h-4 transition-all ${dragOverIndex === sortedChildren.length ? 'bg-pink-400 rounded mx-1 my-0.5' : 'bg-transparent'}`}
          onDragOver={(e) => handleDragOver(e, sortedChildren.length)}
          onDrop={(e) => handleDrop(e, sortedChildren.length)}
        />
      )}
    </div>
  )
}
