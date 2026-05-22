import React from 'react'
import { useUIStore } from '../../../store/uiStore'

interface DesignElementProps {
  id: string;
  children?: React.ReactNode;
  className?: string;
  tagName?: any;
  style?: React.CSSProperties;
  onClick?: (e: React.MouseEvent) => void;
}

export const DesignElement: React.FC<DesignElementProps> = ({ id, children, className = '', tagName = 'div', style = {}, onClick }) => {
  const { designMode, activeElementId, setActiveDesignElement, designData } = useUIStore()

  const elementStyles = designData.styles[id] || {}

  const mergedStyle = {
    ...style,
    marginTop: elementStyles.marginTop,
    marginBottom: elementStyles.marginBottom,
    paddingTop: elementStyles.paddingTop,
    paddingBottom: elementStyles.paddingBottom,
    textAlign: elementStyles.textAlign as any,
    backgroundColor: elementStyles.backgroundColor,
    color: elementStyles.textColor,
    border: elementStyles.border,
    borderRadius: elementStyles.borderRadius,
  }

  const isActive = designMode && activeElementId === id

  const handleClick = (e: React.MouseEvent) => {
    if (designMode) {
      e.stopPropagation()
      e.preventDefault()
      setActiveDesignElement(id)
    } else if (onClick) {
      onClick(e)
    }
  }

  const handleDragStart = (e: React.DragEvent) => {
    if (!designMode) return
    e.dataTransfer.setData('text/plain', id)
    e.dataTransfer.effectAllowed = 'move'
    setActiveDesignElement(id)
  }

  const Tag = tagName as any

  return (
    <Tag
      id={`design-el-${id}`}
      className={`
        ${className}
        ${elementStyles.customClasses || ''}
        ${designMode ? 'cursor-pointer hover:outline hover:outline-2 hover:outline-pink-400 hover:outline-offset-2 transition-all relative' : ''}
        ${isActive ? 'outline outline-2 outline-pink-600 outline-offset-2 z-50 ring-4 ring-pink-500/20' : ''}
      `}
      style={mergedStyle}
      onClick={handleClick}
      draggable={designMode}
      onDragStart={handleDragStart}
    >
      {isActive && (
        <div className="absolute -top-6 left-0 bg-pink-600 text-white text-[10px] font-black px-2 py-0.5 rounded shadow-lg uppercase tracking-widest pointer-events-none whitespace-nowrap">
          {id}
        </div>
      )}
      {children}
    </Tag>
  )
}
