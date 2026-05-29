// # gemini-pro

interface SkeletonRowProps {
  columns?: number;
  className?: string;
  variant?: 'table' | 'grid';
  gridTemplateColumns?: string;
}

/**
 * A skeleton row for table or grid loading states.
 * Consolidates duplicate pulse animations across ListView and ArasTable.
 */
export function SkeletonRow({ 
  columns = 5, 
  className = '', 
  variant = 'table',
  gridTemplateColumns
}: SkeletonRowProps) {
  if (variant === 'grid') {
    return (
      <div 
        className={`animate-pulse border-b border-[var(--line)] grid items-center ${className}`}
        style={{ gridTemplateColumns }}
      >
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className="px-3 py-2.5">
            <div className="h-4 bg-[var(--line)] rounded w-full opacity-50" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <tr className={`animate-pulse border-b border-[var(--line)] ${className}`}>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-[var(--line)] rounded w-full opacity-50" />
        </td>
      ))}
    </tr>
  );
}
