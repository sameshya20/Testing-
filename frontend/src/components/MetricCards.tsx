import React from 'react';
import type { CoverageSummary } from '../types';

interface MetricCardsProps {
  summary: CoverageSummary;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ summary }) => {
  const total = summary.total_count || 1;
  const posPct = Math.round(((summary.positive_count || 0) / total) * 100);
  const negPct = Math.round(((summary.negative_count || 0) / total) * 100);
  const edgePct = Math.max(0, 100 - posPct - negPct);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
      {/* Top Row: Title + Scope Metadata */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-3">
          <h2 className="text-sm font-semibold text-white">Generated Test Suite</h2>
          <span className="text-slate-700">|</span>
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span>
              {(summary.user_stories_count || summary.requirements_covered?.length || 1)}{' '}
              {(summary.user_stories_count || summary.requirements_covered?.length || 1) === 1 ? 'Story' : 'Stories'}
            </span>
            {summary.acceptance_criteria_count ? (
              <>
                <span className="text-slate-600">·</span>
                <span>{summary.acceptance_criteria_count} Criteria</span>
              </>
            ) : null}
            {summary.application_pages_count ? (
              <>
                <span className="text-slate-600">·</span>
                <span>{summary.application_pages_count} Page{summary.application_pages_count > 1 ? 's' : ''}</span>
              </>
            ) : null}
          </div>
        </div>

        {/* Inline KPI Badges */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-400">Total:</span>
            <span className="font-semibold text-white">{summary.total_count}</span>
          </div>
          <span className="text-slate-700">·</span>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-slate-400">Positive:</span>
            <span className="font-semibold text-emerald-400">{summary.positive_count}</span>
          </div>
          <span className="text-slate-700">·</span>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <span className="text-slate-400">Negative:</span>
            <span className="font-semibold text-amber-400">{summary.negative_count}</span>
          </div>
          <span className="text-slate-700">·</span>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
            <span className="text-slate-400">Edge:</span>
            <span className="font-semibold text-purple-400">{summary.edge_count}</span>
          </div>
        </div>
      </div>

      {/* Test Distribution Bar */}
      {summary.total_count > 0 && (
        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden flex">
          <div
            style={{ width: `${posPct}%` }}
            className="bg-emerald-500 transition-all"
            title={`Positive: ${summary.positive_count} (${posPct}%)`}
          />
          <div
            style={{ width: `${negPct}%` }}
            className="bg-amber-500 transition-all"
            title={`Negative: ${summary.negative_count} (${negPct}%)`}
          />
          <div
            style={{ width: `${edgePct}%` }}
            className="bg-purple-500 transition-all"
            title={`Edge: ${summary.edge_count} (${edgePct}%)`}
          />
        </div>
      )}
    </div>
  );
};
