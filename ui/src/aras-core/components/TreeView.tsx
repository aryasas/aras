import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, FileText, Folder } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';

interface TreeNode {
  id: number | string;
  name: string;
  code?: string;
  is_group: boolean;
  children?: TreeNode[];
  parent_id?: number | string | null;
  [key: string]: unknown;
}

interface TreeViewProps {
  resource: string;
  onRowClick?: (id: number | string) => void;
}

export const TreeView: React.FC<TreeViewProps> = ({ resource, onRowClick }) => {
  const [data, setData] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const cleanResource = cleanResourcePath(resource);
        // We assume the API can return a tree or we fetch all and build it
        // For COA, usually we fetch all and build hierarchy based on parent_id
        const res = await api.get(`/${cleanResource}?limit=1000`);
        const items = Array.isArray(res.data.items) ? res.data.items as TreeNode[] : [];
        
        // Build Tree
        const idMap: Record<string, TreeNode> = {};
        const roots: TreeNode[] = [];
        
        items.forEach((item) => {
          idMap[String(item.id)] = { ...item, children: [] };
        });
        
        items.forEach((item) => {
          const id = String(item.id);
          const parentId = item.parent_id == null ? null : String(item.parent_id);
          if (parentId && idMap[parentId]) {
            idMap[parentId].children?.push(idMap[id]);
          } else {
            roots.push(idMap[id]);
          }
        });
        
        setData(roots);
      } catch (err) {
        console.error("Failed to fetch tree data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [resource]);

  const toggleExpand = (id: string | number) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const renderNode = (node: TreeNode, level: number = 0) => {
    const isExpanded = expanded[node.id];
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div key={node.id} className="select-none">
        <div 
          className={`flex items-center gap-2 py-2 px-3 hover:bg-[var(--aras-panel-soft)] cursor-pointer rounded-[var(--aras-radius)] transition-colors ${level === 0 ? 'font-bold' : ''}`}
          style={{ paddingLeft: `${level * 20 + 12}px` }}
          onClick={() => {
            if (hasChildren || node.is_group) toggleExpand(node.id);
            if (!node.is_group && onRowClick) onRowClick(node.id);
          }}
        >
          <div className="w-5 h-5 flex items-center justify-center text-[var(--aras-muted)]">
            {hasChildren || node.is_group ? (
              isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
            ) : null}
          </div>
          <div className={node.is_group ? 'text-[var(--aras-accent)]' : 'text-[var(--aras-muted)]'}>
            {node.is_group ? <Folder size={16} fill="currentColor" /> : <FileText size={16} />}
          </div>
          <div className="flex items-baseline gap-2">
            {node.code && <span className="text-[10px] font-mono text-[var(--aras-muted)] bg-[var(--aras-panel-soft)] px-1 rounded-[var(--aras-radius)]">{node.code}</span>}
            <span className="text-sm">{node.name}</span>
          </div>
        </div>
        {isExpanded && node.children && (
          <div className="border-l border-[var(--aras-border)] ml-4">
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) return <div className="p-8 text-center text-[var(--aras-muted)] animate-pulse">Loading Tree...</div>;

  return (
    <div className="bg-[var(--aras-panel)] rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)] shadow-sm overflow-hidden p-4">
      {data.length > 0 ? data.map(node => renderNode(node)) : <div className="p-8 text-center text-[var(--aras-muted)]">No data found.</div>}
    </div>
  );
};

export default TreeView;
