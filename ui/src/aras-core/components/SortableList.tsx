// claude-opus-4-7
// Reusable vertical sortable list built on @dnd-kit.
// Pass `items` (objects with stable `id`) + `renderItem` + `onReorder(nextItems)`.
// Drag handle: render the exported <DragHandle /> inside renderItem, or set
// `wholeItemDraggable` to make the entire row a drag source.
import React from 'react';
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';

export interface SortableListItem {
  id: string | number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface SortableListProps<T extends SortableListItem> {
  items: T[];
  onReorder: (next: T[]) => void;
  renderItem: (item: T, ctx: { isDragging: boolean }) => React.ReactNode;
  wholeItemDraggable?: boolean;
  className?: string;
  itemClassName?: string;
  overlayClassName?: string;
}

interface RowProps<T extends SortableListItem> {
  item: T;
  render: SortableListProps<T>['renderItem'];
  wholeItemDraggable: boolean;
  itemClassName?: string;
}

function SortableRow<T extends SortableListItem>({ item, render, wholeItemDraggable, itemClassName }: RowProps<T>) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: item.id });
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };
  return (
    <SortableRowCtx.Provider value={{ listeners: listeners ?? {}, attributes }}>
      <div
        ref={setNodeRef}
        style={style}
        className={`arc-dnd-item ${isDragging ? 'is-dragging' : ''} ${itemClassName ?? ''}`}
        {...(wholeItemDraggable ? attributes : {})}
        {...(wholeItemDraggable ? listeners : {})}
      >
        {render(item, { isDragging })}
      </div>
    </SortableRowCtx.Provider>
  );
}

const SortableRowCtx = React.createContext<{
  listeners: any;
  attributes: any;
}>({ listeners: {}, attributes: {} });

export const DragHandle: React.FC<{ className?: string; label?: string }> = ({ className, label = 'Drag to reorder' }) => {
  const { listeners, attributes } = React.useContext(SortableRowCtx);
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`arc-dnd-handle inline-flex items-center justify-center ${className ?? ''}`}
      {...attributes}
      {...listeners}
    >
      <GripVertical size={16} />
    </button>
  );
};

export function SortableList<T extends SortableListItem>({
  items,
  onReorder,
  renderItem,
  wholeItemDraggable = false,
  className,
  itemClassName,
  overlayClassName,
}: SortableListProps<T>) {
  const [activeId, setActiveId] = React.useState<string | number | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleStart = (event: DragStartEvent) => setActiveId(event.active.id);
  const handleEnd = (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = items.findIndex((it) => it.id === active.id);
    const newIndex = items.findIndex((it) => it.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    onReorder(arrayMove(items, oldIndex, newIndex));
  };

  const active = activeId != null ? items.find((it) => it.id === activeId) ?? null : null;

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragStart={handleStart} onDragEnd={handleEnd}>
      <SortableContext items={items.map((it) => it.id)} strategy={verticalListSortingStrategy}>
        <div className={`flex flex-col gap-2 ${className ?? ''}`}>
          {items.map((item) => (
            <SortableRow
              key={item.id}
              item={item}
              render={renderItem}
              wholeItemDraggable={wholeItemDraggable}
              itemClassName={itemClassName}
            />
          ))}
        </div>
      </SortableContext>
      <DragOverlay>
        {active ? (
          <div className={`arc-dnd-overlay ${overlayClassName ?? ''}`}>
            {renderItem(active, { isDragging: true })}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

export default SortableList;
