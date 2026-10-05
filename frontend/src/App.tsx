import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { LoginPage } from './components/LoginPage';
import { ApplicationForm } from './components/ApplicationForm';
import { MetricCards } from './components/MetricCards';
import { TestCaseTable } from './components/TestCaseTable';
import { ExcelPreviewModal } from './components/ExcelPreviewModal';
import type {
  TestCaseGenerationRequest,
  TestCaseGenerationResponse,
  TestCase,
  User
} from './types';
import {
  generateTestCases,
  exportExcelWorkbook,
  fetchCurrentUser,
  logoutUser,
  setSessionExpiredHandler
} from './services/api';
import { AlertCircle, Loader2, CheckCircle2, Download, FileSpreadsheet, X } from 'lucide-react';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState<boolean>(true);
  const [sessionExpiredMsg, setSessionExpiredMsg] = useState<string | null>(null);

  const [generationResult, setGenerationResult] = useState<TestCaseGenerationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showExcelPreview, setShowExcelPreview] = useState<boolean>(false);
  const [exportedFileInfo, setExportedFileInfo] = useState<{ fileName: string; size: number } | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Editable local state
  const [positiveCases, setPositiveCases] = useState<TestCase[]>([]);
  const [negativeCases, setNegativeCases] = useState<TestCase[]>([]);
  const [edgeCases, setEdgeCases] = useState<TestCase[]>([]);
  const [currentReqRef, setCurrentReqRef] = useState<string>('');

  useEffect(() => {
    // Configure global session expiration handler
    setSessionExpiredHandler(() => {
      setCurrentUser(null);
      setGenerationResult(null);
      setSessionExpiredMsg('Your session has expired. Please sign in again.');
    });

    async function checkExistingSession() {
      try {
        setCheckingAuth(true);
        const user = await fetchCurrentUser();
        setCurrentUser(user);
      } catch (err) {
        setCurrentUser(null);
      } finally {
        setCheckingAuth(false);
      }
    }
    checkExistingSession();
  }, []);

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    setSessionExpiredMsg(null);
    setErrorMsg(null);
  };

  const handleLogout = async () => {
    await logoutUser();
    setCurrentUser(null);
    setGenerationResult(null);
    setSessionExpiredMsg(null);
  };

  const handleGenerate = async (payload: TestCaseGenerationRequest) => {
    try {
      setIsLoading(true);
      setErrorMsg(null);

      const refText = payload.user_story_ids && payload.user_story_ids.length > 0
        ? payload.user_story_ids.join(', ')
        : (payload.requirement_identifiers.length > 0
            ? payload.requirement_identifiers.join(', ')
            : (payload.requirement_identifier || 'US-101'));
      setCurrentReqRef(refText);

      const result = await generateTestCases(payload);
      setGenerationResult(result);

      setPositiveCases(result.positive_test_cases);
      setNegativeCases(result.negative_test_cases);
      setEdgeCases(result.edge_test_cases);
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to generate test cases. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateTestCase = (category: string, updated: TestCase) => {
    if (category === 'Positive') {
      setPositiveCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } else if (category === 'Negative') {
      setNegativeCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } else {
      setEdgeCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    }
  };

  const handleDeleteTestCase = (category: string, id: string) => {
    if (category === 'Positive') {
      setPositiveCases((prev) => prev.filter((c) => c.id !== id));
    } else if (category === 'Negative') {
      setNegativeCases((prev) => prev.filter((c) => c.id !== id));
    } else {
      setEdgeCases((prev) => prev.filter((c) => c.id !== id));
    }
  };

  const handleExportExcel = async () => {
    try {
      setIsExporting(true);
      setExportError(null);
      const result = await exportExcelWorkbook(
        positiveCases,
        negativeCases,
        edgeCases,
        "Enterprise Application",
        currentReqRef || "US-101"
      );
      setExportedFileInfo({ fileName: result.fileName, size: result.size });
    } catch (err: any) {
      setExportError(err.message || 'Unable to download the Excel file. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const totalCount = positiveCases.length + negativeCases.length + edgeCases.length;

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center font-sans">
        <div className="flex items-center space-x-3 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-sm font-medium">Loading application...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div>
        {sessionExpiredMsg && (
          <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-md w-full px-4">
            <div className="p-3.5 rounded-xl bg-amber-950/90 border border-amber-800 text-amber-200 text-xs font-medium shadow-2xl flex items-center space-x-2.5">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{sessionExpiredMsg}</span>
            </div>
          </div>
        )}
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header user={currentUser} onLogout={handleLogout} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        
        {/* Application & Multi-Requirement Form */}
        <ApplicationForm onSubmit={handleGenerate} isLoading={isLoading} />

        {/* Error Message Alert */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-red-950/50 border border-red-800/60 flex items-center space-x-3 text-red-300 text-sm">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Generation Results Section */}
        {generationResult && (
          <div className="space-y-6">
            
            {/* Metrics Dashboard */}
            <MetricCards
              summary={{
                ...generationResult.coverage_summary,
                total_count: totalCount,
                positive_count: positiveCases.length,
                negative_count: negativeCases.length,
                edge_count: edgeCases.length
              }}
            />

            {/* Excel Download Success Banner */}
            {exportedFileInfo && (
              <div className="bg-emerald-950/80 border border-emerald-500/40 rounded-xl p-4 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                      <span>Excel File Ready</span>
                      <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-emerald-900/90 text-emerald-300 border border-emerald-700/60">
                        {exportedFileInfo.fileName}
                      </span>
                    </h4>
                    <p className="text-xs text-emerald-300/80 mt-0.5">
                      Your test cases are ready to download.
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => setShowExcelPreview(true)}
                    type="button"
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-800/70 hover:bg-emerald-700/70 text-white text-xs font-medium border border-emerald-600/50 transition-colors cursor-pointer"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-300" />
                    <span>View Excel</span>
                  </button>
                  <button
                    onClick={handleExportExcel}
                    disabled={isExporting}
                    type="button"
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Excel</span>
                  </button>
                  <button
                    onClick={() => setExportedFileInfo(null)}
                    type="button"
                    className="p-1 rounded-lg text-emerald-400 hover:text-white hover:bg-emerald-900/50 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Export Error Banner */}
            {exportError && (
              <div className="bg-red-950/80 border border-red-800 rounded-xl p-4 shadow-xl flex items-center justify-between text-red-200 text-sm">
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                  <span>{exportError}</span>
                </div>
                <button
                  onClick={() => setExportError(null)}
                  type="button"
                  className="p-1 rounded-lg text-red-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Test Case Table */}
            <TestCaseTable
              positiveCases={positiveCases}
              negativeCases={negativeCases}
              edgeCases={edgeCases}
              onUpdateTestCase={handleUpdateTestCase}
              onDeleteTestCase={handleDeleteTestCase}
              onExportExcel={handleExportExcel}
              onOpenPreview={() => setShowExcelPreview(true)}
              isExporting={isExporting}
            />

            {/* In-App Excel Workbook Viewer Modal */}
            <ExcelPreviewModal
              isOpen={showExcelPreview}
              onClose={() => setShowExcelPreview(false)}
              positiveCases={positiveCases}
              negativeCases={negativeCases}
              edgeCases={edgeCases}
              onExportExcel={handleExportExcel}
              isExporting={isExporting}
              fileName={exportedFileInfo?.fileName || `Test_Suite_${currentReqRef || 'US-101'}.xlsx`}
              appName="Enterprise Application"
              reqRef={currentReqRef || 'US-101'}
            />

          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-4 text-center text-xs text-slate-500">
        <p>Test Case Generator &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}

export default App;
