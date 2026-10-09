import React, { useState } from 'react';
import type { TestCase } from '../types';
import { EditTestCaseModal } from './EditTestCaseModal';
import {
  Download,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  Loader2,
  Cloud
} from 'lucide-react';

interface TestCaseTableProps {
  positiveCases: TestCase[];
  negativeCases: TestCase[];
  edgeCases: TestCase[];
  onUpdateTestCase: (category: string, updated: TestCase) => void;
  onDeleteTestCase: (category: string, id: string) => void;
  onExportExcel: () => void;
  onOpenPreview?: () => void;
  isExporting: boolean;
  onSyncAzureDevOps?: () => void;
  isSyncingAzure?: boolean;
  isAdoConnected?: boolean;
}

export const TestCaseTable: React.FC<TestCaseTableProps> = ({
  positiveCases,
  negativeCases,
  edgeCases,
  onUpdateTestCase,
  onDeleteTestCase,
  onExportExcel,
  onOpenPreview,
  isExporting,
  onSyncAzureDevOps,
  isSyncingAzure = false,
  isAdoConnected = false
}) => {
  const [activeTab, setActiveTab] = useState<'Positive' | 'Negative' | 'Edge'>('Positive');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  const getActiveList = () => {
    switch (activeTab) {
      case 'Positive':
        return positiveCases;
      case 'Negative':
        return negativeCases;
      case 'Edge':
        return edgeCases;
      default:
        return positiveCases;
    }
  };

  const filteredCases = getActiveList().filter((tc) => {
    return priorityFilter === 'ALL' || tc.priority.toUpperCase() === priorityFilter.toUpperCase();
  });

  const toggleRowExpanded = (id: string) => {
    setExpandedRowId(expandedRowId === id ? null : id);
  };

  const renderPriorityBadge = (priority: string) => {
    const p = priority.toUpperCase();
    if (p === 'HIGH') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-red-950/60 text-red-300 border border-red-800/60">
          High
        </span>
      );
    }
    if (p === 'LOW') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
          Low
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950/60 text-amber-300 border border-amber-800/60">
        Medium
      </span>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
      
      {/* Top Toolbar */}
      <div className="p-3 sm:px-4 sm:py-3 border-b border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        
        {/* Category Tabs */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded border border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('Positive')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${
              activeTab === 'Positive'
                ? 'bg-slate-800 text-emerald-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Positive</span>
            <span className="font-mono text-[11px] text-slate-400 ml-1">
              {positiveCases.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('Negative')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${
              activeTab === 'Negative'
                ? 'bg-slate-800 text-amber-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <XCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>Negative</span>
            <span className="font-mono text-[11px] text-slate-400 ml-1">
              {negativeCases.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('Edge')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${
              activeTab === 'Edge'
                ? 'bg-slate-800 text-purple-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-purple-400" />
            <span>Edge</span>
            <span className="font-mono text-[11px] text-slate-400 ml-1">
              {edgeCases.length}
            </span>
          </button>
        </div>

        {/* Action Controls & Sync */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          
          {/* Priority Filter */}
          <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 rounded px-2 py-1">
            <Filter className="w-3 h-3 text-slate-500" />
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Priorities</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          {/* Sync to Azure DevOps Button */}
          {onSyncAzureDevOps && (
            <button
              id="sync-azure-devops-btn"
              onClick={onSyncAzureDevOps}
              disabled={isSyncingAzure}
              type="button"
              title={isAdoConnected ? "Sync approved test cases to Azure DevOps" : "Connect Azure DevOps to sync"}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors disabled:opacity-50 cursor-pointer"
            >
              {isSyncingAzure ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Syncing...</span>
                </>
              ) : (
                <>
                  <Cloud className="w-3.5 h-3.5" />
                  <span>Sync to Azure DevOps</span>
                </>
              )}
            </button>
          )}

          {/* View Excel Button */}
          {onOpenPreview && (
            <button
              id="view-excel-btn"
              onClick={onOpenPreview}
              type="button"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-slate-400" />
              <span>View Excel</span>
            </button>
          )}

          {/* Download Excel Button */}
          <button
            id="export-excel-btn"
            onClick={onExportExcel}
            disabled={isExporting}
            type="button"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Exporting...</span>
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5 text-slate-400" />
                <span>Download Excel</span>
              </>
            )}
          </button>

        </div>

      </div>

      {/* Table View */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-950 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-2.5 px-2.5 w-8 text-center"></th>
              <th className="py-2.5 px-3 w-28">Test Case ID</th>
              <th className="py-2.5 px-3 w-24">ADO ID</th>
              <th className="py-2.5 px-3 w-28">Sync Status</th>
              <th className="py-2.5 px-3 w-24">Ref</th>
              <th className="py-2.5 px-3 w-24">Priority</th>
              <th className="py-2.5 px-3">Test Scenario</th>
              <th className="py-2.5 px-3">Expected Result</th>
              <th className="py-2.5 px-3 w-20 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70 text-slate-200">
            {filteredCases.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-8 text-slate-500">
                  No test cases match the selected filter.
                </td>
              </tr>
            ) : (
              filteredCases.map((tc) => {
                const isExpanded = expandedRowId === tc.id;
                const syncStatus = tc.sync_status || 'Not Synced';

                return (
                  <React.Fragment key={tc.id}>
                    <tr className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-2.5 text-center">
                        <button
                          type="button"
                          onClick={() => toggleRowExpanded(tc.id)}
                          className="text-slate-500 hover:text-slate-300"
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-blue-400">
                        {tc.id}
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        {tc.azure_test_case_id ? (
                          <span className="text-emerald-400 font-semibold">
                            #{tc.azure_test_case_id}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${
                            syncStatus === 'Synced'
                              ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60'
                              : syncStatus === 'Updated'
                              ? 'bg-blue-950/60 text-blue-300 border border-blue-800/60'
                              : syncStatus === 'Sync Failed'
                              ? 'bg-red-950/60 text-red-300 border border-red-800/60'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}
                        >
                          {syncStatus}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">
                        {tc.requirement_ref}
                      </td>
                      <td className="py-2.5 px-3">
                        {renderPriorityBadge(tc.priority)}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-slate-100 max-w-sm truncate">
                        {tc.scenario}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate">
                        {tc.expected_result}
                      </td>
                      <td className="py-2.5 px-3 text-right space-x-1">
                        <button
                          type="button"
                          onClick={() => setEditingCase(tc)}
                          className="p-1 rounded text-slate-400 hover:text-blue-400 hover:bg-slate-800 transition-colors"
                          title="Edit"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => onDeleteTestCase(activeTab, tc.id)}
                          className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Detail Drawer */}
                    {isExpanded && (
                      <tr className="bg-slate-950/60 border-b border-slate-800">
                        <td colSpan={9} className="p-4 space-y-3">
                          
                          {/* Traceability Metadata Bar */}
                          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 border-b border-slate-800 pb-2">
                            <div>
                              <span>Parent Work Item: </span>
                              <span className="font-mono font-medium text-blue-400">
                                {tc.azure_work_item_id ? `#${tc.azure_work_item_id}` : (tc.user_story || 'US-101')}
                              </span>
                            </div>
                            <div>
                              <span>Azure Test Case: </span>
                              {tc.azure_test_case_id ? (
                                <span className="font-mono font-medium text-emerald-400">
                                  #{tc.azure_test_case_id}
                                </span>
                              ) : (
                                <span className="text-slate-600">Not Synced</span>
                              )}
                            </div>
                            <div>
                              <span>Sync Status: </span>
                              <span className="font-medium text-slate-300">
                                {syncStatus}
                              </span>
                            </div>
                            {tc.sync_message && (
                              <div className="text-slate-500 italic">
                                ({tc.sync_message})
                              </div>
                            )}
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <div>
                              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                                Preconditions
                              </span>
                              <p className="bg-slate-900 p-2 rounded border border-slate-800 text-slate-300">
                                {tc.preconditions}
                              </p>
                            </div>
                            <div>
                              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                                Test Data
                              </span>
                              <p className="bg-slate-900 p-2 rounded border border-slate-800 text-slate-300 font-mono">
                                {tc.test_data}
                              </p>
                            </div>
                          </div>

                          {tc.application_page && (
                            <div className="text-xs">
                              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                                Application Page
                              </span>
                              <div className="bg-slate-900 p-2 rounded border border-slate-800 text-slate-300">
                                <span>{tc.application_page}</span>
                                {tc.application_link && (
                                  <span className="text-slate-500 font-mono text-[11px] block mt-0.5">{tc.application_link}</span>
                                )}
                              </div>
                            </div>
                          )}

                          <div className="text-xs">
                            <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                              Test Steps
                            </span>
                            <div className="bg-slate-900 p-2.5 rounded border border-slate-800 space-y-1">
                              {tc.test_steps.map((step, idx) => (
                                <p key={idx} className="text-slate-300 font-mono text-[11px]">
                                  {step}
                                </p>
                              ))}
                            </div>
                          </div>

                          <div className="text-xs">
                            <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                              Expected Outcome
                            </span>
                            <p className="bg-slate-900 p-2 rounded border border-slate-800 text-slate-300">
                              {tc.expected_result}
                            </p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {editingCase && (
        <EditTestCaseModal
          testCase={editingCase}
          onSave={(updated) => {
            onUpdateTestCase(activeTab, updated);
            setEditingCase(null);
          }}
          onClose={() => setEditingCase(null)}
        />
      )}

    </div>
  );
};
