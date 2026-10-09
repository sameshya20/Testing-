import React, { useState, useMemo } from 'react';
import type { Area } from '../types';
import { ChevronRight, ChevronDown, Folder, FolderOpen, X } from 'lucide-react';

interface AreaTreeNode {
  area: Area;
  path: string;
  depth: number;
  children: AreaTreeNode[];
}

interface AreaSelectorProps {
  areas: Area[];
  selectedAreaId?: number | '';
  selectedAreaIds?: number[];
  onSelectArea?: (areaId: number) => void;
  onSelectAreas?: (areaIds: number[]) => void;
  isLoading?: boolean;
}

export const AreaSelector: React.FC<AreaSelectorProps> = ({
  areas,
  selectedAreaId,
  selectedAreaIds: propsSelectedAreaIds,
  onSelectArea,
  onSelectAreas,
  isLoading = false
}) => {
  const [expandedNodeIds, setExpandedNodeIds] = useState<Record<number, boolean>>({});

  // Compute normalized effective selected area IDs list
  const selectedAreaIds = useMemo(() => {
    if (propsSelectedAreaIds !== undefined) {
      return propsSelectedAreaIds;
    }
    if (selectedAreaId !== undefined && selectedAreaId !== '') {
      return [Number(selectedAreaId)];
    }
    return [];
  }, [propsSelectedAreaIds, selectedAreaId]);

  // Map of areas by ID
  const areaMap = useMemo(() => {
    const map = new Map<number, Area>();
    areas.forEach(a => map.set(a.id, a));
    return map;
  }, [areas]);

  // Compute full area path string (e.g. "Project / Finance / Payments")
  const getAreaPath = useMemo(() => {
    return (areaId: number): string => {
      const parts: string[] = [];
      let current: Area | undefined = areaMap.get(areaId);
      const visited = new Set<number>();

      while (current && !visited.has(current.id)) {
        visited.add(current.id);
        parts.unshift(current.name);
        if (current.parent_id) {
          current = areaMap.get(current.parent_id);
        } else {
          break;
        }
      }
      return parts.join(' / ');
    };
  }, [areaMap]);

  // Build tree node structure recursively
  const treeNodes = useMemo(() => {
    const buildNodes = (parentId: number | null, depth: number): AreaTreeNode[] => {
      const childrenAreas = areas.filter(a => (parentId === null ? !a.parent_id : a.parent_id === parentId));
      return childrenAreas.map(area => {
        const path = getAreaPath(area.id);
        return {
          area,
          path,
          depth,
          children: buildNodes(area.id, depth + 1)
        };
      });
    };
    return buildNodes(null, 0);
  }, [areas, getAreaPath]);

  const toggleExpand = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setExpandedNodeIds(prev => ({ ...prev, [id]: !(prev[id] ?? true) }));
  };

  const handleToggleArea = (areaId: number) => {
    let newSelected: number[];
    if (selectedAreaIds.includes(areaId)) {
      newSelected = selectedAreaIds.filter(id => id !== areaId);
    } else {
      newSelected = Array.from(new Set([...selectedAreaIds, areaId]));
    }

    if (onSelectAreas) {
      onSelectAreas(newSelected);
    }
    if (onSelectArea) {
      onSelectArea(newSelected.length > 0 ? newSelected[0] : ('' as any));
    }
  };

  const handleRemoveArea = (e: React.MouseEvent, areaId: number) => {
    e.stopPropagation();
    const newSelected = selectedAreaIds.filter(id => id !== areaId);
    if (onSelectAreas) {
      onSelectAreas(newSelected);
    }
    if (onSelectArea) {
      onSelectArea(newSelected.length > 0 ? newSelected[0] : ('' as any));
    }
  };

  const handleClearAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onSelectAreas) {
      onSelectAreas([]);
    }
    if (onSelectArea) {
      onSelectArea('' as any);
    }
  };

  const renderTreeNode = (node: AreaTreeNode) => {
    const hasChildren = node.children.length > 0;
    const isExpanded = expandedNodeIds[node.area.id] ?? true;
    const isSelected = selectedAreaIds.includes(node.area.id);

    return (
      <div key={node.area.id} className="select-none">
        <div
          onClick={() => handleToggleArea(node.area.id)}
          className={`flex items-center space-x-2 py-1 px-2 rounded text-xs cursor-pointer transition-colors ${
            isSelected
              ? 'bg-blue-950/60 text-blue-200 font-medium border border-blue-800/60'
              : 'hover:bg-slate-800/60 text-slate-300'
          }`}
          style={{ paddingLeft: `${node.depth * 1 + 0.35}rem` }}
        >
          {hasChildren ? (
            <button
              type="button"
              onClick={(e) => toggleExpand(e, node.area.id)}
              className="p-0.5 hover:bg-slate-700/60 rounded text-slate-400 hover:text-slate-200 transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-blue-400" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              )}
            </button>
          ) : (
            <span className="w-3.5 inline-block" />
          )}

          {hasChildren ? (
            isExpanded ? (
              <FolderOpen className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            ) : (
              <Folder className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            )
          ) : null}

          <span className="truncate flex-1">{node.area.name}</span>

          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => {}}
            className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5 cursor-pointer"
          />
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l border-slate-800/80 ml-3 pl-1 space-y-0.5">
            {node.children.map(child => renderTreeNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-2">
      {/* Header Label */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
          <span>Area Selection</span>
          {selectedAreaIds.length > 0 && (
            <span className="text-[11px] font-normal text-slate-400">
              ({selectedAreaIds.length} selected)
            </span>
          )}
        </label>

        {selectedAreaIds.length > 0 && (
          <button
            type="button"
            onClick={handleClearAll}
            className="text-[11px] text-slate-400 hover:text-red-400 transition-colors"
          >
            Clear Selection
          </button>
        )}
      </div>

      {/* Selected chips bar (if any) */}
      {selectedAreaIds.length > 0 && (
        <div className="flex flex-wrap gap-1.5 p-2 bg-slate-950 border border-slate-800 rounded">
          {selectedAreaIds.map(id => (
            <span
              key={id}
              className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-blue-950/70 border border-blue-800/60 text-blue-200 text-xs font-mono"
            >
              <span className="truncate max-w-xs">{getAreaPath(id) || `Area #${id}`}</span>
              <button
                type="button"
                onClick={(e) => handleRemoveArea(e, id)}
                className="hover:text-red-300 text-blue-300 ml-1"
                title="Remove"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Hierarchical Area Tree Panel */}
      <div className="bg-slate-950 border border-slate-800 rounded p-2.5 max-h-56 overflow-y-auto space-y-0.5">
        {isLoading ? (
          <div className="py-4 text-center text-xs text-slate-400">
            Loading areas...
          </div>
        ) : treeNodes.length === 0 ? (
          <div className="py-4 text-center text-xs text-slate-500">
            No areas available
          </div>
        ) : (
          treeNodes.map(node => renderTreeNode(node))
        )}
      </div>
    </div>
  );
};
