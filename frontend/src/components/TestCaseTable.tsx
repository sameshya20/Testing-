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
  Loader2
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
}

export const TestCaseTable: React.FC<TestCaseTableProps> = ({
  positiveCases,
  negativeCases,
  edgeCases,
  onUpdateTestCase,
  onDeleteTestCase,
  onExportExcel,
  onOpenPreview,
  isExporting
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
    const matchesPriority =
      priorityFilter === 'ALL' || tc.priority.toUpperCase() === priorityFilter.toUpperCase();

    return matchesPriority;
  });

  const toggleRowExpanded = (id: string) => {
    setExpandedRowId(expandedRowId === id ? null : id);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-xl overflow-hidden">
      
      {/* Top Toolbar */}
      <div className="p-4 sm:p-6 border-b border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        
        {/* Tabs */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('Positive')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'Positive'
                ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Positive</span>
            <span className="ml-1.5 px-2 py-0.5 text-xs rounded-full bg-emerald-950 text-emerald-300 font-bold">
              {positiveCases.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('Negative')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'Negative'
                ? 'bg-amber-600/20 text-amber-400 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <XCircle className="w-4 h-4 text-amber-400" />
            <span>Negative</span>
            <span className="ml-1.5 px-2 py-0.5 text-xs rounded-full bg-amber-950 text-amber-300 font-bold">
              {negativeCases.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('Edge')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'Edge'
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="w-4 h-4 text-purple-400" />
            <span>Edge</span>
            <span className="ml-1.5 px-2 py-0.5 text-xs rounded-full bg-purple-950 text-purple-300 font-bold">
              {edgeCases.length}
            </span>
          </button>
        </div>

        {/* Filter & Export */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          
          {/* Priority Filter */}
          <div className="flex items-center space-x-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Priorities</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          {/* View Excel Sheets Button */}
          {onOpenPreview && (
            <button
              id="view-excel-btn"
              onClick={onOpenPreview}
              type="button"
              className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 shadow-md transition-all cursor-pointer"
              title="View Excel"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>View Excel</span>
            </button>
          )}

          {/* Export Excel */}
          <button
            id="export-excel-btn"
            onClick={onExportExcel}
            disabled={isExporting}
            type="button"
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-50 cursor-pointer"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Downloading Excel...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Download Excel</span>
              </>
            )}
          </button>

        </div>

      </div>

      {/* Table View */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-950 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-4 w-12 text-center">#</th>
              <th className="py-3 px-4 w-32">Test Case ID</th>
              <th className="py-3 px-4 w-28">Ref</th>
              <th className="py-3 px-4 w-24">Priority</th>
              <th className="py-3 px-4">Test Scenario</th>
              <th className="py-3 px-4">Expected Result</th>
              <th className="py-3 px-4 w-28 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-sm text-slate-200">
            {filteredCases.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-slate-500 text-sm">
                  No matching test cases found for the selected filters.
                </td>
              </tr>
            ) : (
              filteredCases.map((tc) => {
                const isExpanded = expandedRowId === tc.id;
                return (
                  <React.Fragment key={tc.id}>
                    <tr className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => toggleRowExpanded(tc.id)}
                          className="text-slate-500 hover:text-slate-300"
                        >
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs font-bold text-blue-400">
                        {tc.id}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-400">
                        {tc.requirement_ref}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            tc.priority.toUpperCase() === 'HIGH'
                              ? 'bg-red-950 text-red-300 border border-red-800/50'
                              : tc.priority.toUpperCase() === 'MEDIUM'
                              ? 'bg-amber-950 text-amber-300 border border-amber-800/50'
                              : 'bg-blue-950 text-blue-300 border border-blue-800/50'
                          }`}
                        >
                          {tc.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-100">
                        {tc.scenario}
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-300 max-w-xs truncate">
                        {tc.expected_result}
                      </td>
                      <td className="py-3 px-4 text-right space-x-2">
                        <button
                          onClick={() => setEditingCase(tc)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-blue-400 hover:bg-slate-800 transition-colors"
                          title="Edit Test Case"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onDeleteTestCase(activeTab, tc.id)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
                          title="Delete Test Case"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Detail Drawer */}
                    {isExpanded && (
                      <tr className="bg-slate-950/70 border-b border-slate-800">
                        <td colSpan={7} className="p-4 sm:p-6 space-y-3">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                                Preconditions
                              </p>
                              <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                                {tc.preconditions}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                                Test Data
                              </p>
                              <p className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800 font-mono">
                                {tc.test_data}
                              </p>
                            </div>
                          </div>

                          {tc.application_page && (
                            <div>
                              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                                Application Page
                              </p>
                              <p className="text-xs text-purple-300 bg-purple-950/30 p-2.5 rounded-lg border border-purple-900/40">
                                <span className="font-semibold">{tc.application_page}</span>
                                {tc.application_link && (
                                  <span className="text-slate-400 font-mono block text-[11px] mt-0.5">{tc.application_link}</span>
                                )}
                              </p>
                            </div>
                          )}

                          <div>
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                              Step-by-Step Test Steps
                            </p>
                            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 space-y-1">
                              {tc.test_steps.map((step, idx) => (
                                <p key={idx} className="text-xs text-slate-200 font-mono">
                                  {step}
                                </p>
                              ))}
                            </div>
                          </div>

                          <div>
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                              Full Expected Outcome
                            </p>
                            <p className="text-xs text-emerald-300 bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-900/40">
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
