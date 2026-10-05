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
  Loader2,
  ShieldCheck
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

  // Step 7 requirement: For "View Excel Sheets", verify the frontend receives the correct XLSX binary
  // and parse workbook sheets (Positive, Negative, Edge) using SheetJS/xlsx
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
      } catch (err: any) {
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

    // Fallback to React state test cases if parsedData not yet ready
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
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const totalCount = positiveCases.length + negativeCases.length + edgeCases.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl w-full max-w-[95vw] h-[90vh] flex flex-col overflow-hidden">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white tracking-tight">Excel Preview</h3>
                <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {parsedData?.fileName || fileName}
                </span>
                {parsedData ? (
                  <span className="hidden sm:inline-flex items-center space-x-1 font-mono text-[11px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-700/60">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    <span>Excel File Ready</span>
                  </span>
                ) : isLoadingWorkbook ? (
                  <span className="hidden sm:inline-flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-700/60">
                    <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
                    <span>Loading test cases...</span>
                  </span>
                ) : parseError ? (
                  <span className="hidden sm:inline-flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded-full bg-red-950 text-red-300 border border-red-700/60">
                    <AlertTriangle className="w-3 h-3 text-red-400" />
                    <span>Unable to load test cases</span>
                  </span>
                ) : null}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {totalCount} Total Test Cases &bull; Positive, Negative, Edge
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              onClick={handleCopyTsv}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
              title="Copy test cases to clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copied ? 'Copied!' : 'Copy Table'}</span>
            </button>

            <button
              onClick={onExportExcel}
              disabled={isExporting}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isExporting ? 'Downloading...' : 'Download Excel'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-2"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>


        {/* Toolbar & Sheet Tabs */}
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-900/90 flex flex-wrap items-center justify-between gap-3">
          {/* Excel-style Sheet Tabs */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveSheet('Positive')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSheet === 'Positive'
                  ? 'bg-emerald-600/25 text-emerald-400 border border-emerald-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Positive</span>
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-emerald-950 text-emerald-300 text-[10px] font-bold">
                {positiveCases.length}
              </span>
            </button>

            <button
              onClick={() => setActiveSheet('Negative')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSheet === 'Negative'
                  ? 'bg-amber-600/25 text-amber-400 border border-amber-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <XCircle className="w-3.5 h-3.5 text-amber-400" />
              <span>Negative</span>
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-amber-950 text-amber-300 text-[10px] font-bold">
                {negativeCases.length}
              </span>
            </button>

            <button
              onClick={() => setActiveSheet('Edge')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSheet === 'Edge'
                  ? 'bg-purple-600/25 text-purple-400 border border-purple-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-purple-400" />
              <span>Edge</span>
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-purple-950 text-purple-300 text-[10px] font-bold">
                {edgeCases.length}
              </span>
            </button>

            <button
              onClick={() => setActiveSheet('All')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeSheet === 'All'
                  ? 'bg-blue-600/25 text-blue-400 border border-blue-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400" />
              <span>All</span>
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-blue-950 text-blue-300 text-[10px] font-bold">
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
                placeholder="Search test cases..."
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-48 sm:w-64"
              />
            </div>

            <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5">
              <Filter className="w-3 h-3 text-slate-500" />
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
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
              <tr className="bg-slate-900 border-b border-slate-700 text-slate-300 uppercase tracking-wider font-semibold">
                <th className="py-2.5 px-3 border-r border-slate-800 text-center w-10">#</th>
                <th className="py-2.5 px-3 border-r border-slate-800 w-28">Test Case ID</th>
                <th className="py-2.5 px-3 border-r border-slate-800 w-28">User Story</th>
                <th className="py-2.5 px-3 border-r border-slate-800 w-36">Acceptance Criteria</th>
                <th className="py-2.5 px-3 border-r border-slate-800 w-32">App Page</th>
                <th className="py-2.5 px-3 border-r border-slate-800 min-w-[200px]">Test Scenario</th>
                <th className="py-2.5 px-3 border-r border-slate-800 min-w-[180px]">Preconditions</th>
                <th className="py-2.5 px-3 border-r border-slate-800 min-w-[160px]">Test Data</th>
                <th className="py-2.5 px-3 border-r border-slate-800 min-w-[220px]">Test Steps</th>
                <th className="py-2.5 px-3 border-r border-slate-800 min-w-[220px]">Expected Result</th>
                <th className="py-2.5 px-3 border-r border-slate-800 text-center w-20">Priority</th>
                <th className="py-2.5 px-3 text-center w-20">Category</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-200">
              {isLoadingWorkbook && filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={12} className="text-center py-16 text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                      <span className="text-sm font-medium">Loading test cases...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={12} className="text-center py-12 text-slate-500">
                    {parseError ? (
                      <div className="flex flex-col items-center space-y-2 text-red-400">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        <span>{parseError}</span>
                      </div>
                    ) : (
                      'No matching test cases found.'
                    )}
                  </td>
                </tr>
              ) : (
                filteredRows.map((row, idx) => (
                  <tr key={row.id + '-' + idx} className="hover:bg-slate-900/60 transition-colors">
                    <td className="py-2 px-3 border-r border-slate-800/80 text-center text-slate-500 font-mono">
                      {idx + 1}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 font-mono font-bold text-blue-400">
                      {row.id}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 font-mono text-slate-300">
                      {row.user_story || 'US-101'}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 text-slate-300">
                      {row.acceptance_criteria}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 text-purple-300">
                      {row.application_page || 'N/A'}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 font-medium text-slate-100">
                      {row.scenario}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 text-slate-300">
                      {row.preconditions || 'N/A'}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 font-mono text-slate-300">
                      {row.test_data || 'N/A'}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 text-slate-300 whitespace-pre-line">
                      {row.test_steps}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 text-slate-300">
                      {row.expected_result}
                    </td>
                    <td className="py-2 px-3 border-r border-slate-800/80 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          row.priority.toUpperCase() === 'HIGH'
                            ? 'bg-red-950 text-red-300 border border-red-800/50'
                            : row.priority.toUpperCase() === 'MEDIUM'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800/50'
                            : 'bg-blue-950 text-blue-300 border border-blue-800/50'
                        }`}
                      >
                        {row.priority}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          row.category === 'Positive'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/50'
                            : row.category === 'Negative'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800/50'
                            : 'bg-purple-950 text-purple-300 border border-purple-800/50'
                        }`}
                      >
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
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-4">
            <span>Showing <strong className="text-white">{filteredRows.length}</strong> of <strong className="text-white">{currentDisplayRows.length}</strong> test cases</span>
            <span>&bull;</span>
            <span className="text-slate-400">
              Excel Format
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
