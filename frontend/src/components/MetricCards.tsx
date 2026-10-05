import React from 'react';
import type { CoverageSummary } from '../types';
import { CheckCircle2, XCircle, AlertTriangle, Layers, FileText } from 'lucide-react';

interface MetricCardsProps {
  summary: CoverageSummary;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ summary }) => {
  return (
    <div className="space-y-4">
      {/* Top Banner Summary */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Test Cases Generated</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Requirements: <span className="text-blue-400 font-semibold">
              {(summary.user_stories_count || summary.requirements_covered?.length || 1)}{' '}
              {(summary.user_stories_count || summary.requirements_covered?.length || 1) === 1 ? 'User Story' : 'User Stories'}
            </span>
            {summary.acceptance_criteria_count ? (
              <> | <span className="text-emerald-400 font-semibold">{summary.acceptance_criteria_count} Acceptance Criteria</span></>
            ) : null}
            {summary.application_pages_count ? (
              <> | <span className="text-purple-400 font-semibold">{summary.application_pages_count} Application Page{summary.application_pages_count > 1 ? 's' : ''}</span></>
            ) : null}
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800">
          <FileText className="w-4 h-4 text-blue-400" />
          <span className="text-xs text-slate-400 font-medium">Total Test Cases:</span>
          <span className="text-lg font-bold text-white">{summary.total_count}</span>
        </div>
      </div>

      {/* Grid Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        
        {/* Total */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-md">
          <div>
            <p className="text-xs font-medium text-slate-400">Total Cases</p>
            <p className="text-2xl font-bold text-white mt-1">{summary.total_count}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center border border-blue-500/20">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        {/* Positive */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-md">
          <div>
            <p className="text-xs font-medium text-slate-400">Positive</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{summary.positive_count}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        {/* Negative */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-md">
          <div>
            <p className="text-xs font-medium text-slate-400">Negative</p>
            <p className="text-2xl font-bold text-amber-400 mt-1">{summary.negative_count}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
            <XCircle className="w-5 h-5" />
          </div>
        </div>

        {/* Edge */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-md">
          <div>
            <p className="text-xs font-medium text-slate-400">Edge</p>
            <p className="text-2xl font-bold text-purple-400 mt-1">{summary.edge_count}</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

      </div>
    </div>
  );
};
