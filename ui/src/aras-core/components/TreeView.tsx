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
  [key: string]: any;
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
        const items = res.data.items || [];
        
        // Build Tree
        const idMap: Record<string, TreeNode> = {};
        const roots: TreeNode[] = [];
        
        items.forEach((item: any) => {
          idMap[item.id] = { ...item, children: [] };
        });
        
        items.forEach((item: any) => {
          if (item.parent_id && idMap[item.parent_id]) {
            idMap[item.parent_id].children?.push(idMap[item.id]);
          } else {
            roots.push(idMap[item.id]);
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
          className={`flex items-center gap-2 py-2 px-3 hover:bg-slate-50 cursor-pointer rounded-lg transition-colors ${level === 0 ? 'font-bold' : ''}`}
          style={{ paddingLeft: `${level * 20 + 12}px` }}
          onClick={() => {
            if (hasChildren || node.is_group) toggleExpand(node.id);
            if (!node.is_group && onRowClick) onRowClick(node.id);
          }}
        >
          <div className="w-5 h-5 flex items-center justify-center text-slate-400">
            {hasChildren || node.is_group ? (
              isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
            ) : null}
          </div>
          <div className={node.is_group ? 'text-indigo-600' : 'text-slate-600'}>
            {node.is_group ? <Folder size={16} fill="currentColor" /> : <FileText size={16} />}
          </div>
          <div className="flex items-baseline gap-2">
            {node.code && <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1 rounded">{node.code}</span>}
            <span className="text-sm">{node.name}</span>
          </div>
        </div>
        {isExpanded && node.children && (
          <div className="border-l border-slate-100 ml-4">
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) return <div className="p-8 text-center text-slate-400 animate-pulse">Loading Tree...</div>;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-4">
      {data.length > 0 ? data.map(node => renderNode(node)) : <div className="p-8 text-center text-slate-400">No data found.</div>}
    </div>
  );
};

export default TreeView;
