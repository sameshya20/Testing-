import React, { useState, useEffect } from 'react';
import type { TestCase } from '../types';
import {
  fetchAndParseExcelWorkbook,
  type ParsedWorkbookResult
} from '../services/api';
import {
  X,
  Download,
  FileSpreadsheet,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Copy,
  Check,
  Filter,
  Loader2
} from 'lucide-react';

interface ExcelPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  positiveCases: TestCase[];
  negativeCases: TestCase[];
  edgeCases: TestCase[];
  onExportExcel: () => void;
  isExporting: boolean;
  fileName?: string;
  appName?: string;
  reqRef?: string;
}

export const ExcelPreviewModal: React.FC<ExcelPreviewModalProps> = ({
  isOpen,
  onClose,
  positiveCases,
  negativeCases,
  edgeCases,
  onExportExcel,
  isExporting,
  fileName = 'Test_Suite.xlsx',
  appName = 'Enterprise Application',
  reqRef = 'US-101'
}) => {
  const [activeSheet, setActiveSheet] = useState<'Positive' | 'Negative' | 'Edge' | 'All'>('Positive');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [copied, setCopied] = useState(false);
  const [parsedData, setParsedData] = useState<ParsedWorkbookResult | null>(null);
  const [isLoadingWorkbook, setIsLoadingWorkbook] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setParsedData(null);
      setParseError(null);
      return;
    }

    let isMounted = true;
    async function loadRealXlsx() {
      try {
        setIsLoadingWorkbook(true);
        setParseError(null);
        const result = await fetchAndParseExcelWorkbook(
          positiveCases,
          negativeCases,
          edgeCases,
          appName,
          reqRef
        );
        if (isMounted) {
          setParsedData(result);
        }
      } catch {
        if (isMounted) {
          setParseError('Unable to open the Excel file. Please try downloading it again.');
        }
      } finally {
        if (isMounted) {
          setIsLoadingWorkbook(false);
        }
      }
    }

    loadRealXlsx();
    return () => {
      isMounted = false;
    };
  }, [isOpen, positiveCases, negativeCases, edgeCases, appName, reqRef]);

  if (!isOpen) return null;

  interface DisplayRow {
    id: string;
    user_story: string;
    acceptance_criteria: string;
    application_page: string;
    application_link: string;
    scenario: string;
    description: string;
    preconditions: string;
    test_data: string;
    test_steps: string;
    expected_result: string;
    priority: string;
    category: string;
  }

  const getSheetRows = (): DisplayRow[] => {
    if (parsedData && parsedData.sheets.length > 0) {
      const convertRow = (row: (string | number)[], defaultCat: string): DisplayRow => ({
        id: String(row[0] || ''),
        user_story: String(row[1] || 'US-101'),
        acceptance_criteria: String(row[2] || ''),
        application_page: String(row[3] || 'N/A'),
        application_link: String(row[4] || 'N/A'),
        scenario: String(row[5] || ''),
        description: String(row[6] || ''),
        preconditions: String(row[7] || 'N/A'),
        test_data: String(row[8] || 'N/A'),
        test_steps: String(row[9] || ''),
        expected_result: String(row[10] || ''),
        priority: String(row[11] || 'Medium'),
        category: String(row[12] || defaultCat)
      });

      if (activeSheet === 'All') {
        const allRows: DisplayRow[] = [];
        parsedData.sheets.forEach(sh => {
          sh.rows.forEach(r => {
            if (r.length > 0 && String(r[0] || '').trim() && !String(r[0] || '').startsWith('No ')) {
              allRows.push(convertRow(r, sh.name));
            }
          });
        });
        return allRows;
      }

      const targetSheet = parsedData.sheets.find(s => s.name.toLowerCase() === activeSheet.toLowerCase());
      if (targetSheet) {
        return targetSheet.rows
          .filter(r => r.length > 0 && String(r[0] || '').trim() && !String(r[0] || '').startsWith('No '))
          .map(r => convertRow(r, targetSheet.name));
      }
    }

    const fallbackList =
      activeSheet === 'Positive' ? positiveCases :
      activeSheet === 'Negative' ? negativeCases :
      activeSheet === 'Edge' ? edgeCases :
      [...positiveCases, ...negativeCases, ...edgeCases];

    return fallbackList.map(tc => ({
      id: tc.id,
      user_story: tc.user_story || 'US-101',
      acceptance_criteria: tc.acceptance_criteria || tc.requirement_ref,
      application_page: tc.application_page || 'N/A',
      application_link: tc.application_link || 'N/A',
      scenario: tc.scenario,
      description: tc.description || '',
      preconditions: tc.preconditions || 'N/A',
      test_data: tc.test_data || 'N/A',
      test_steps: Array.isArray(tc.test_steps) ? tc.test_steps.join('\n') : (tc.test_steps || ''),
      expected_result: tc.expected_result,
      priority: tc.priority,
      category: tc.category
    }));
  };

  const currentDisplayRows = getSheetRows();

  const filteredRows = currentDisplayRows.filter((row) => {
    const matchesPriority =
      priorityFilter === 'ALL' || row.priority.toUpperCase() === priorityFilter.toUpperCase();
    if (!matchesPriority) return false;

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      row.id.toLowerCase().includes(q) ||
      row.user_story.toLowerCase().includes(q) ||
      row.acceptance_criteria.toLowerCase().includes(q) ||
      row.scenario.toLowerCase().includes(q) ||
      row.expected_result.toLowerCase().includes(q) ||
      row.test_data.toLowerCase().includes(q)
    );
  });

  const handleCopyTsv = () => {
    const headers = [
      'Test Case ID',
      'User Story',
      'Acceptance Criteria',
      'Application Page',
      'Application Link',
      'Test Scenario',
      'Test Description',
      'Preconditions',
      'Test Data',
      'Test Steps',
      'Expected Result',
      'Priority',
      'Category'
    ];

    const rows = filteredRows.map((r) => [
      r.id,
      r.user_story,
      r.acceptance_criteria,
      r.application_page,
      r.application_link,
      r.scenario,
      r.description,
      r.preconditions,
      r.test_data,
      r.test_steps.replace(/\n/g, '; '),
      r.expected_result,
      r.priority,
      r.category
    ]);

    const tsvContent = [
      headers.join('\t'),
      ...rows.map((r) => r.map((c) => String(c).replace(/[\t\r\n]+/g, ' ')).join('\t'))
    ].join('\n');

    navigator.clipboard.writeText(tsvContent).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const totalCount = positiveCases.length + negativeCases.length + edgeCases.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-xs">
      <div className="bg-slate-900 border border-slate-800 rounded-lg shadow-2xl w-full max-w-[95vw] h-[90vh] flex flex-col overflow-hidden">
        
        {/* Modal Header */}
        <div className="px-5 py-3 border-b border-slate-800 bg-slate-950 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-white">Excel Preview</span>
                <span className="font-mono text-xs text-slate-400">
                  ({parsedData?.fileName || fileName})
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handleCopyTsv}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              type="button"
              onClick={onExportExcel}
              disabled={isExporting}
              className="flex items-center space-x-1.5 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors disabled:opacity-50 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExporting ? 'Downloading...' : 'Download Excel'}</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-1 cursor-pointer"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Toolbar & Sheet Tabs */}
        <div className="px-5 py-2.5 border-b border-slate-800 bg-slate-900 flex flex-wrap items-center justify-between gap-2.5">
          {/* Sheet Tabs */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded border border-slate-800">
            <button
              type="button"
              onClick={() => setActiveSheet('Positive')}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                activeSheet === 'Positive'
                  ? 'bg-slate-800 text-emerald-300'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Positive</span>
              <span className="font-mono text-[10px] text-slate-400 ml-1">
                {positiveCases.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveSheet('Negative')}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                activeSheet === 'Negative'
                  ? 'bg-slate-800 text-amber-300'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <XCircle className="w-3 h-3 text-amber-400" />
              <span>Negative</span>
              <span className="font-mono text-[10px] text-slate-400 ml-1">
                {negativeCases.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveSheet('Edge')}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                activeSheet === 'Edge'
                  ? 'bg-slate-800 text-purple-300'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <AlertTriangle className="w-3 h-3 text-purple-400" />
              <span>Edge</span>
              <span className="font-mono text-[10px] text-slate-400 ml-1">
                {edgeCases.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveSheet('All')}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
                activeSheet === 'All'
                  ? 'bg-slate-800 text-blue-300'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileSpreadsheet className="w-3 h-3 text-blue-400" />
              <span>All</span>
              <span className="font-mono text-[10px] text-slate-400 ml-1">
                {totalCount}
              </span>
            </button>
          </div>

          {/* Search & Priority Filter */}
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="pl-8 pr-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-44 sm:w-56"
              />
            </div>

            <div className="flex items-center space-x-1 bg-slate-950 border border-slate-700 rounded px-2 py-1">
              <Filter className="w-3 h-3 text-slate-500" />
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-300 focus:outline-none cursor-pointer"
              >
                <option value="ALL">All Priorities</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Spreadsheet Table View */}
        <div className="flex-1 overflow-auto bg-slate-950">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="sticky top-0 z-10">
              <tr className="bg-slate-900 border-b border-slate-700 text-slate-300 uppercase tracking-wider font-semibold text-[11px]">
                <th className="py-2 px-2.5 border-r border-slate-800 text-center w-8">#</th>
                <th className="py-2 px-2.5 border-r border-slate-800 w-24">ID</th>
                <th className="py-2 px-2.5 border-r border-slate-800 w-24">Story</th>
                <th className="py-2 px-2.5 border-r border-slate-800 w-32">Criteria</th>
                <th className="py-2 px-2.5 border-r border-slate-800 w-28">Page</th>
                <th className="py-2 px-2.5 border-r border-slate-800 min-w-[180px]">Scenario</th>
                <th className="py-2 px-2.5 border-r border-slate-800 min-w-[150px]">Preconditions</th>
                <th className="py-2 px-2.5 border-r border-slate-800 min-w-[130px]">Test Data</th>
                <th className="py-2 px-2.5 border-r border-slate-800 min-w-[180px]">Steps</th>
                <th className="py-2 px-2.5 border-r border-slate-800 min-w-[180px]">Expected Result</th>
                <th className="py-2 px-2.5 border-r border-slate-800 text-center w-16">Priority</th>
                <th className="py-2 px-2.5 text-center w-16">Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {isLoadingWorkbook && filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={12} className="text-center py-12 text-slate-400">
                    <div className="flex items-center justify-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                      <span>Loading test cases...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={12} className="text-center py-10 text-slate-500">
                    {parseError ? (
                      <span className="text-red-400">{parseError}</span>
                    ) : (
                      'No matching test cases found.'
                    )}
                  </td>
                </tr>
              ) : (
                filteredRows.map((row, idx) => (
                  <tr key={row.id + '-' + idx} className="hover:bg-slate-900/60 transition-colors">
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-center text-slate-500 font-mono text-[11px]">
                      {idx + 1}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 font-mono font-medium text-blue-400">
                      {row.id}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 font-mono text-slate-400">
                      {row.user_story || 'US-101'}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-slate-300">
                      {row.acceptance_criteria}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-slate-400">
                      {row.application_page || 'N/A'}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-slate-200">
                      {row.scenario}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-slate-400">
                      {row.preconditions || 'N/A'}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 font-mono text-slate-400 text-[11px]">
                      {row.test_data || 'N/A'}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-slate-300 whitespace-pre-line text-[11px]">
                      {row.test_steps}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-slate-300">
                      {row.expected_result}
                    </td>
                    <td className="py-1.5 px-2.5 border-r border-slate-800 text-center">
                      <span className="text-[11px] text-slate-300 font-medium">
                        {row.priority}
                      </span>
                    </td>
                    <td className="py-1.5 px-2.5 text-center">
                      <span className="text-[11px] text-slate-300 font-medium">
                        {row.category}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-2.5 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <strong className="text-white">{filteredRows.length}</strong> of <strong className="text-white">{currentDisplayRows.length}</strong> test cases
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
