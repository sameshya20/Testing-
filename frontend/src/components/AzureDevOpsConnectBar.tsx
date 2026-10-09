import React, { useState, useEffect } from 'react';
import type { AzureDevOpsProjectItem, AzureDevOpsConnectResponse } from '../types';
import {
  fetchAzureDevOpsConfig,
  connectAzureDevOps,
  fetchAzureDevOpsProjects
} from '../services/api';
import {
  Cloud,
  CheckCircle2,
  XCircle,
  Loader2,
  Lock,
  ChevronDown,
  ChevronUp,
  FolderGit2,
  Eye,
  EyeOff,
  RefreshCw,
  Building
} from 'lucide-react';

interface AzureDevOpsConnectBarProps {
  onConnectionChange: (connected: boolean, project: string | null, org: string | null, mode?: string) => void;
  isExpandedExternal?: boolean;
  onToggleExpanded?: () => void;
}

export const AzureDevOpsConnectBar: React.FC<AzureDevOpsConnectBarProps> = ({
  onConnectionChange,
  isExpandedExternal,
  onToggleExpanded
}) => {
  const [organization, setOrganization] = useState<string>('DemoOrganization');
  const [project, setProject] = useState<string>('TestCaseDemoProject');
  const [pat, setPat] = useState<string>('');
  const [showPat, setShowPat] = useState<boolean>(false);
  const [mode, setMode] = useState<string>('mock');

  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isPatConfigured, setIsPatConfigured] = useState<boolean>(false);
  const [projectsList, setProjectsList] = useState<AzureDevOpsProjectItem[]>([]);
  const [loadingProjects, setLoadingProjects] = useState<boolean>(false);

  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [internalExpanded, setInternalExpanded] = useState<boolean>(false);
  const isExpanded = isExpandedExternal !== undefined ? isExpandedExternal : internalExpanded;

  const toggleExpanded = () => {
    if (onToggleExpanded) {
      onToggleExpanded();
    } else {
      setInternalExpanded(!internalExpanded);
    }
  };

  const loadProjects = async () => {
    try {
      setLoadingProjects(true);
      const projs = await fetchAzureDevOpsProjects();
      setProjectsList(projs);
    } catch {
      setProjectsList([]);
    } finally {
      setLoadingProjects(false);
    }
  };

  // Check initial backend Azure DevOps config on load
  useEffect(() => {
    async function checkInitialConfig() {
      try {
        const config = await fetchAzureDevOpsConfig();
        if (config.organization) setOrganization(config.organization);
        if (config.project) setProject(config.project);
        if (config.mode) setMode(config.mode);
        setIsPatConfigured(config.is_pat_configured);
        setIsConnected(config.connected);
        onConnectionChange(config.connected, config.project || 'TestCaseDemoProject', config.organization || 'DemoOrganization', config.mode || 'mock');

        loadProjects();
      } catch {
        setIsConnected(false);
        onConnectionChange(false, null, null, 'mock');
      }
    }
    checkInitialConfig();
  }, []);

  const handleConnect = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);

    const cleanOrg = organization.trim() || 'DemoOrganization';
    const cleanProj = project.trim() || 'TestCaseDemoProject';

    try {
      setIsConnecting(true);
      const res: AzureDevOpsConnectResponse = await connectAzureDevOps({
        organization: cleanOrg,
        project: cleanProj,
        pat: pat.trim() || undefined
      });

      if (res.connected) {
        setIsConnected(true);
        if (res.mode) setMode(res.mode);
        setStatusMessage(res.message || 'Configuration saved successfully.');
        setErrorMessage(null);
        if (res.projects && res.projects.length > 0) {
          setProjectsList(res.projects);
          if (!project.trim()) {
            setProject(res.projects[0].name);
          }
        }
        onConnectionChange(true, cleanProj || (res.projects[0]?.name ?? null), res.organization, res.mode || mode);
        setInternalExpanded(false);
      } else {
        setIsConnected(false);
        setErrorMessage(res.message || 'Unable to update settings. Please check credentials.');
        setStatusMessage(null);
        onConnectionChange(false, null, null, mode);
        setInternalExpanded(true);
      }
    } catch (err: any) {
      setIsConnected(false);
      setErrorMessage(err.message || 'Unable to communicate with Azure DevOps.');
      setStatusMessage(null);
      onConnectionChange(false, null, null, mode);
      setInternalExpanded(true);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleProjectSelect = (selectedName: string) => {
    setProject(selectedName);
    onConnectionChange(isConnected, selectedName, organization, mode);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
      {/* Top Compact Integration Strip */}
      <div className="px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3 min-w-0">
          <div className="flex items-center space-x-2">
            <Cloud className="w-4 h-4 text-blue-400 shrink-0" />
            <span className="text-xs font-semibold text-white">Azure DevOps</span>
          </div>

          <span className="text-slate-700">|</span>

          {/* Org & Project Info */}
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span className="truncate">Org: <strong className="text-slate-200 font-medium">{organization || 'DemoOrganization'}</strong></span>
            <span className="text-slate-700">/</span>
            <span className="truncate">Project: <strong className="text-slate-200 font-medium">{project || 'TestCaseDemoProject'}</strong></span>
          </div>
        </div>

        {/* Right Action Controls */}
        <div className="flex items-center space-x-2 shrink-0">
          {/* Quick Project Dropdown */}
          <div className="flex items-center space-x-1.5 bg-slate-950 border border-slate-800 rounded px-2 py-1">
            <span className="text-[11px] text-slate-400">Project:</span>
            <select
              id="connected-project-dropdown"
              value={project}
              onChange={(e) => handleProjectSelect(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
            >
              {projectsList.length > 0 ? (
                projectsList.map((p) => (
                  <option key={p.id} value={p.name} className="bg-slate-900 text-white">
                    {p.name}
                  </option>
                ))
              ) : (
                <option value={project || 'TestCaseDemoProject'} className="bg-slate-900 text-white">
                  {project || 'TestCaseDemoProject'}
                </option>
              )}
            </select>
          </div>

          <button
            onClick={toggleExpanded}
            type="button"
            id="toggle-ado-settings-btn"
            className="flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition-colors cursor-pointer"
          >
            <span>{isExpanded ? 'Close Settings' : 'Settings'}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Expanded Configuration Drawer */}
      {isExpanded && (
        <div className="border-t border-slate-800 bg-slate-950/70 p-4 space-y-3">
          {errorMessage && (
            <div className="p-3 rounded-md bg-red-950/60 border border-red-800/60 text-red-300 text-xs flex items-center space-x-2">
              <XCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {statusMessage && (
            <div className="p-3 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          <form onSubmit={handleConnect} className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Field 1: Organization */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Building className="w-3.5 h-3.5 text-slate-400" />
                <span>Organization</span>
              </label>
              <input
                id="ado-org-input"
                type="text"
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="DemoOrganization"
                className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Field 2: Project */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <FolderGit2 className="w-3.5 h-3.5 text-slate-400" />
                <span>Project</span>
                {loadingProjects && <Loader2 className="w-3 h-3 animate-spin text-blue-400 ml-1" />}
              </label>

              {projectsList.length > 0 ? (
                <div className="flex items-center space-x-1.5">
                  <select
                    id="ado-project-select"
                    value={project}
                    onChange={(e) => handleProjectSelect(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    {projectsList.map((p) => (
                      <option key={p.id} value={p.name}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={loadProjects}
                    disabled={loadingProjects}
                    className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors cursor-pointer"
                    title="Refresh projects list"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loadingProjects ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              ) : (
                <input
                  id="ado-project-input"
                  type="text"
                  value={project}
                  onChange={(e) => setProject(e.target.value)}
                  placeholder="TestCaseDemoProject"
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              )}
            </div>

            {/* Field 3: PAT */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
                <span>Personal Access Token</span>
                {isPatConfigured && !pat ? (
                  <span className="text-[10px] text-emerald-400 font-normal ml-1">
                    (Configured)
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-500 font-normal ml-1">
                    (Optional for mock)
                  </span>
                )}
              </label>
              <div className="relative">
                <input
                  id="ado-pat-input"
                  type={showPat ? 'text' : 'password'}
                  value={pat}
                  onChange={(e) => setPat(e.target.value)}
                  placeholder="Leave empty for mock mode"
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 pr-8 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPat(!showPat)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                >
                  {showPat ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Submit Action Row */}
            <div className="md:col-span-3 flex items-center justify-end pt-2 border-t border-slate-800">
              <button
                id="connect-ado-btn"
                type="submit"
                disabled={isConnecting}
                className="flex items-center space-x-2 px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors disabled:opacity-50 cursor-pointer"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save Configuration</span>
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
