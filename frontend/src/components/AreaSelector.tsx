import React, { useState, useMemo, useEffect } from 'react';
import type { Area } from '../types';
import { ChevronRight, ChevronDown, Layers, Folder, FolderOpen, Check, X, Trash2 } from 'lucide-react';

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
  const [isOpen, setIsOpen] = useState<boolean>(true);
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

  // Automatically expand parent nodes on initial load
  useEffect(() => {
    if (areas.length > 0) {
      const defaultExpanded: Record<number, boolean> = {};
      areas.forEach(a => {
        if (!a.parent_id || areas.some(child => child.parent_id === a.id)) {
          defaultExpanded[a.id] = true;
        }
      });
      setExpandedNodeIds(defaultExpanded);
    }
  }, [areas]);

  const toggleExpand = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setExpandedNodeIds(prev => ({ ...prev, [id]: !prev[id] }));
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
    const isExpanded = !!expandedNodeIds[node.area.id];
    const isSelected = selectedAreaIds.includes(node.area.id);

    return (
      <div key={node.area.id} className="select-none">
        <div
          onClick={() => handleToggleArea(node.area.id)}
          className={`flex items-center space-x-2 py-1.5 px-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
            isSelected
              ? 'bg-blue-900/60 border border-blue-500/80 text-blue-100 font-semibold shadow-sm'
              : 'hover:bg-slate-800/70 text-slate-300'
          }`}
          style={{ paddingLeft: `${node.depth * 1.25 + 0.5}rem` }}
        >
          {hasChildren ? (
            <button
              type="button"
              onClick={(e) => toggleExpand(e, node.area.id)}
              className="p-0.5 hover:bg-slate-700/60 rounded text-slate-400 hover:text-slate-200 transition-colors"
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-blue-400" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              )}
            </button>
          ) : (
            <span className="w-4 h-4 inline-flex items-center justify-center text-slate-500 font-mono text-[10px]">
              ○
            </span>
          )}

          {hasChildren ? (
            isExpanded ? (
              <FolderOpen className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            ) : (
              <Folder className="w-3.5 h-3.5 text-amber-400/80 shrink-0" />
            )
          ) : null}

          <span className="truncate flex-1 font-medium">{node.area.name}</span>

          <div className="flex items-center space-x-1 shrink-0">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => {}} // Handled by parent click
              className="rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500 h-3.5 w-3.5"
            />
            {isSelected && (
              <span className="flex items-center space-x-1 text-[11px] text-blue-400 font-bold ml-1">
                <Check className="w-3.5 h-3.5 text-blue-400 stroke-[3]" />
              </span>
            )}
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l border-slate-800/80 ml-4 pl-1 space-y-0.5">
            {node.children.map(child => renderTreeNode(child))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Header Label */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-slate-200 font-semibold text-sm">
          <div className="w-6 h-6 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 text-xs font-bold">
            1
          </div>
          <Layers className="w-4 h-4 text-blue-400" />
          <span>Area Selection</span>
        </div>

        {selectedAreaIds.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-blue-400 font-mono font-medium">
              {selectedAreaIds.length} Area{selectedAreaIds.length > 1 ? 's' : ''} Selected
            </span>
            {selectedAreaIds.length > 1 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-[11px] text-slate-400 hover:text-red-400 font-medium transition-colors flex items-center space-x-1"
                title="Clear all selected areas"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear All</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Selector Trigger Box */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full bg-slate-950 border rounded-xl px-4 py-3 cursor-pointer flex items-center justify-between transition-all ${
          isOpen ? 'border-blue-500 shadow-md ring-1 ring-blue-500/30' : 'border-slate-800 hover:border-slate-700'
        }`}
      >
        <div className="min-w-0 flex-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Selected Area(s)
          </span>
          {selectedAreaIds.length === 0 ? (
            <div className="text-sm font-medium text-slate-400 truncate mt-0.5">
              Select an area
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5 mt-1.5 max-h-24 overflow-y-auto pr-1">
              {selectedAreaIds.map(id => (
                <span
                  key={id}
                  className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-blue-950/80 border border-blue-700/80 text-blue-200 text-xs font-mono font-medium shadow-sm"
                >
                  <span>{getAreaPath(id) || `Area #${id}`}</span>
                  <button
                    type="button"
                    onClick={(e) => handleRemoveArea(e, id)}
                    className="p-0.5 hover:bg-blue-800/80 rounded text-blue-300 hover:text-red-300 transition-colors"
                    title="Remove area"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2 shrink-0 ml-3 self-start mt-1">
          <span className="text-xs text-blue-400 hover:underline font-medium">
            {isOpen ? 'Collapse' : 'Expand'}
          </span>
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-blue-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {/* Selected Area Paths Detail List */}
      {selectedAreaIds.length > 0 && (
        <div className="p-3 bg-blue-950/40 border border-blue-800/60 rounded-xl space-y-2">
          <div className="flex items-center justify-between border-b border-blue-900/60 pb-1.5">
            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider">
              Selected Areas ({selectedAreaIds.length}):
            </span>
            <button
              type="button"
              onClick={handleClearAll}
              className="text-[11px] text-slate-400 hover:text-red-400 font-medium transition-colors"
            >
              Clear All
            </button>
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
            {selectedAreaIds.map(id => (
              <div
                key={id}
                className="text-xs font-bold text-slate-100 font-mono tracking-wide flex items-center justify-between bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800/80"
              >
                <div className="flex items-center space-x-1.5 truncate mr-2">
                  <span className="text-blue-400">▼</span>
                  <span className="truncate">{getAreaPath(id) || `Area #${id}`}</span>
                </div>
                <button
                  type="button"
                  onClick={(e) => handleRemoveArea(e, id)}
                  className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-red-400 transition-colors shrink-0"
                  title="Remove this area"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hierarchical Area Tree Panel */}
      {isOpen && (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 max-h-72 overflow-y-auto space-y-1 shadow-inner">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-2.5 pb-2 border-b border-slate-800/60 mb-2 flex items-center justify-between">
            <span>Application Areas</span>
            <span className="text-[10px] text-slate-500 font-normal">Select one or more areas</span>
          </div>

          {isLoading ? (
            <div className="py-6 text-center text-xs text-slate-400 italic">
              Loading areas...
            </div>
          ) : treeNodes.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-400 italic">
              No areas available.
            </div>
          ) : (
            treeNodes.map(node => renderTreeNode(node))
          )}
        </div>
      )}
    </div>
  );
};

