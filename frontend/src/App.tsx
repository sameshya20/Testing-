import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { LoginPage } from './components/LoginPage';
import { AzureDevOpsConnectBar } from './components/AzureDevOpsConnectBar';
import { ApplicationForm } from './components/ApplicationForm';
import { MetricCards } from './components/MetricCards';
import { TestCaseTable } from './components/TestCaseTable';
import { ExcelPreviewModal } from './components/ExcelPreviewModal';
import type {
  TestCaseGenerationRequest,
  TestCaseGenerationResponse,
  TestCase,
  User,
  AzureDevOpsSyncResponse
} from './types';
import {
  generateTestCases,
  exportExcelWorkbook,
  fetchCurrentUser,
  logoutUser,
  setSessionExpiredHandler,
  syncTestCasesToAzureDevOps,
  fetchAzureDevOpsConfig
} from './services/api';
import { AlertCircle, Loader2, CheckCircle2, Download, FileSpreadsheet, X, Cloud } from 'lucide-react';

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

  // Azure DevOps Integration State
  const [isAdoConnected, setIsAdoConnected] = useState<boolean>(false);
  const [adoProject, setAdoProject] = useState<string | null>(null);
  const [adoOrg, setAdoOrg] = useState<string | null>(null);
  const [adoMode, setAdoMode] = useState<string>('mock');
  const [isSyncingAzure, setIsSyncingAzure] = useState<boolean>(false);
  const [lastSyncedTime, setLastSyncedTime] = useState<string | null>(null);
  const [syncStatusBanner, setSyncStatusBanner] = useState<{
    type: 'success' | 'error' | 'warning';
    message: string;
    createdCount?: number;
    updatedCount?: number;
    failedCount?: number;
  } | null>(null);
  const [selectedStoryId, setSelectedStoryId] = useState<string | undefined>(undefined);
  const [selectedAreaPath, setSelectedAreaPath] = useState<string | undefined>(undefined);

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
      } catch {
        setCurrentUser(null);
      } finally {
        setCheckingAuth(false);
      }
    }
    checkExistingSession();
  }, []);

  // Fetch Azure DevOps configuration silently from backend
  useEffect(() => {
    async function loadBackendAdoConfig() {
      try {
        const config = await fetchAzureDevOpsConfig();
        setIsAdoConnected(Boolean(config.connected));
        setAdoProject(config.project || 'TestCaseDemoProject');
        setAdoOrg(config.organization || 'DemoOrganization');
        if (config.mode) setAdoMode(config.mode);
      } catch {
        setIsAdoConnected(false);
        setAdoProject(null);
        setAdoOrg(null);
      }
    }
    if (currentUser) {
      loadBackendAdoConfig();
    }
  }, [currentUser]);

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
      setSyncStatusBanner(null);

      const refText = payload.user_story_ids && payload.user_story_ids.length > 0
        ? payload.user_story_ids.join(', ')
        : (payload.requirement_identifiers.length > 0
            ? payload.requirement_identifiers.join(', ')
            : (payload.requirement_identifier || 'US-101'));
      setCurrentReqRef(refText);

      if (payload.user_story_ids && payload.user_story_ids.length > 0) {
        setSelectedStoryId(payload.user_story_ids[0]);
      }
      if (payload.services && payload.services.length > 0) {
        setSelectedAreaPath(payload.services[0]);
      }

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

  const handleSyncAzureDevOps = async () => {
    if (!isAdoConnected) {
      setSyncStatusBanner({
        type: 'error',
        message: 'Azure DevOps is not configured. Please configure your credentials.'
      });
      return;
    }

    const allCases = [...positiveCases, ...negativeCases, ...edgeCases];
    if (allCases.length === 0) {
      setSyncStatusBanner({
        type: 'warning',
        message: 'No test cases available to synchronize.'
      });
      return;
    }

    try {
      setIsSyncingAzure(true);
      setSyncStatusBanner(null);

      const workItemId = selectedStoryId || allCases[0]?.azure_work_item_id;
      const response: AzureDevOpsSyncResponse = await syncTestCasesToAzureDevOps(
        allCases,
        workItemId,
        selectedAreaPath,
        adoProject || undefined
      );

      const syncMap = new Map((response.test_cases || []).map(s => [s.id, s]));

      const updateList = (list: TestCase[]) =>
        list.map(tc => {
          const match = syncMap.get(tc.id);
          if (match) {
            return {
              ...tc,
              azure_test_case_id: match.azure_test_case_id ?? tc.azure_test_case_id,
              sync_status: match.sync_status || 'Synced',
              sync_message: match.sync_message
            };
          }
          return tc;
        });

      setPositiveCases(updateList(positiveCases));
      setNegativeCases(updateList(negativeCases));
      setEdgeCases(updateList(edgeCases));

      const totalSuccess = (response.synced_count || 0) + (response.updated_count || 0);
      if (response.failed_count === 0 && totalSuccess > 0) {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        setLastSyncedTime(timeStr);
        setSyncStatusBanner({
          type: 'success',
          message: `Synchronized ${totalSuccess} test cases to Azure DevOps (${response.synced_count} created, ${response.updated_count} updated).`,
          createdCount: response.synced_count,
          updatedCount: response.updated_count,
          failedCount: response.failed_count
        });
      } else if (totalSuccess > 0 && response.failed_count > 0) {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        setLastSyncedTime(timeStr);
        setSyncStatusBanner({
          type: 'warning',
          message: `Partially synchronized: ${response.synced_count} created, ${response.updated_count} updated, ${response.failed_count} failed.`,
          createdCount: response.synced_count,
          updatedCount: response.updated_count,
          failedCount: response.failed_count
        });
      } else {
        setSyncStatusBanner({
          type: 'error',
          message: response.message || 'Synchronization to Azure DevOps failed. Please check permissions.',
          createdCount: response.synced_count,
          updatedCount: response.updated_count,
          failedCount: response.failed_count
        });
      }
    } catch (err: any) {
      setSyncStatusBanner({
        type: 'error',
        message: err.message || 'Failed to sync test cases to Azure DevOps.'
      });
    } finally {
      setIsSyncingAzure(false);
    }
  };

  const totalCount = positiveCases.length + negativeCases.length + edgeCases.length;

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center font-sans">
        <div className="flex items-center space-x-2 text-slate-400 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span>Loading application...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div>
        {sessionExpiredMsg && (
          <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-sm w-full px-4">
            <div className="p-3 rounded bg-amber-950/90 border border-amber-800 text-amber-200 text-xs font-medium shadow-lg flex items-center space-x-2">
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
      <Header
        user={currentUser}
        onLogout={handleLogout}
        integrationStatus={{
          connected: isAdoConnected,
          mode: adoMode,
          project: adoProject,
          organization: adoOrg,
          isSyncing: isSyncingAzure,
          lastSyncedTime: lastSyncedTime,
          syncFailed: syncStatusBanner?.type === 'error'
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 space-y-4">
        
        {/* Azure DevOps Project & Integration Toolbar */}
        <AzureDevOpsConnectBar
          onConnectionChange={(connected, proj, org, mode) => {
            setIsAdoConnected(connected);
            setAdoProject(proj);
            setAdoOrg(org);
            if (mode) setAdoMode(mode);
          }}
        />

        {/* Primary QA Workflow Form */}
        <ApplicationForm
          onSubmit={handleGenerate}
          isLoading={isLoading}
          isAdoConnected={isAdoConnected}
          adoProject={adoProject}
          adoOrg={adoOrg}
        />

        {/* Global Error Alert */}
        {errorMsg && (
          <div className="p-3 rounded-md bg-red-950/60 border border-red-800/60 flex items-center space-x-2.5 text-red-300 text-xs">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Generation Results Section */}
        {generationResult && (
          <div className="space-y-4">
            
            {/* Test Suite Summary */}
            <MetricCards
              summary={{
                ...generationResult.coverage_summary,
                total_count: totalCount,
                positive_count: positiveCases.length,
                negative_count: negativeCases.length,
                edge_count: edgeCases.length
              }}
            />

            {/* Azure DevOps Sync Status Notification */}
            {syncStatusBanner && (
              <div
                className={`p-3 rounded-md border flex items-center justify-between gap-3 text-xs ${
                  syncStatusBanner.type === 'success'
                    ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-200'
                    : syncStatusBanner.type === 'warning'
                    ? 'bg-amber-950/60 border-amber-800/60 text-amber-200'
                    : 'bg-red-950/60 border-red-800/60 text-red-200'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Cloud className="w-4 h-4 shrink-0" />
                  <span>{syncStatusBanner.message}</span>
                </div>
                <button
                  onClick={() => setSyncStatusBanner(null)}
                  type="button"
                  className="p-1 rounded opacity-70 hover:opacity-100 transition-opacity"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Excel Ready Banner */}
            {exportedFileInfo && (
              <div className="bg-emerald-950/60 border border-emerald-800/60 rounded-md p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="text-emerald-200">
                    Excel file <strong className="font-mono text-emerald-300">{exportedFileInfo.fileName}</strong> ready for download.
                  </span>
                </div>
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => setShowExcelPreview(true)}
                    type="button"
                    className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                    <span>View</span>
                  </button>
                  <button
                    onClick={handleExportExcel}
                    disabled={isExporting}
                    type="button"
                    className="flex items-center space-x-1 px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                  <button
                    onClick={() => setExportedFileInfo(null)}
                    type="button"
                    className="p-1 rounded text-emerald-400 hover:text-white transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            {/* Export Error Alert */}
            {exportError && (
              <div className="bg-red-950/60 border border-red-800/60 rounded-md p-3 flex items-center justify-between text-red-200 text-xs">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                  <span>{exportError}</span>
                </div>
                <button
                  onClick={() => setExportError(null)}
                  type="button"
                  className="p-1 rounded text-red-400 hover:text-white"
                >
                  <X className="w-3.5 h-3.5" />
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
              onSyncAzureDevOps={handleSyncAzureDevOps}
              isSyncingAzure={isSyncingAzure}
              isAdoConnected={isAdoConnected}
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
      <footer className="bg-slate-900 border-t border-slate-800 py-3 text-center text-xs text-slate-500">
        <p>Test Case Generator &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}

export default App;
