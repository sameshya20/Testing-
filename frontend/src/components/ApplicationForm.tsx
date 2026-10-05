import React, { useState, useEffect, useRef } from 'react';
import type {
  Area,
  UserStory,
  AcceptanceCriteriaRead,
  Application,
  TestCaseGenerationRequest,
  ApplicationLinkPayload
} from '../types';
import {
  fetchAreas,
  fetchUserStoriesByAreas,
  fetchAcceptanceCriteriaByStories,
  fetchApplications
} from '../services/api';
import { AreaSelector } from './AreaSelector';
import { Loader2, Plus, X, Edit2, Globe, AlertCircle, FileText, CheckSquare } from 'lucide-react';

interface SelectedLinkItem {
  id: string;
  name: string;
  url: string;
}

interface ApplicationFormProps {
  onSubmit: (payload: TestCaseGenerationRequest) => void;
  isLoading: boolean;
}

function normalizeUrl(url: string): string {
  let clean = url.trim();
  if (!clean.toLowerCase().startsWith('http://') && !clean.toLowerCase().startsWith('https://')) {
    clean = 'https://' + clean;
  }
  return clean.toLowerCase().replace(/\/+$/, '');
}

function isBlockedScheme(url: string): boolean {
  const lowered = url.trim().toLowerCase();
  return (
    lowered.startsWith('javascript:') ||
    lowered.startsWith('data:') ||
    lowered.startsWith('file:') ||
    lowered.startsWith('vbscript:')
  );
}

const DEFAULT_APPLICATION_LINK = 'https://www.amazon.in/';

export const ApplicationForm: React.FC<ApplicationFormProps> = ({ onSubmit, isLoading }) => {
  // Database Data States
  const [areas, setAreas] = useState<Area[]>([]);
  const [userStories, setUserStories] = useState<UserStory[]>([]);
  const [acceptanceCriteriaList, setAcceptanceCriteriaList] = useState<AcceptanceCriteriaRead[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);

  // Selection States (Support multiple service selections & multiple user stories)
  const [selectedAreaIds, setSelectedAreaIds] = useState<number[]>([]);
  const [selectedStoryIds, setSelectedStoryIds] = useState<string[]>([]);
  const [selectedCriteriaIds, setSelectedCriteriaIds] = useState<string[]>([]);

  // Track previously selected stories to only auto-select criteria for newly added stories
  const previousStoryIdsRef = useRef<string[]>([]);

  // Application Link State (Default set to https://www.amazon.in/)
  const [selectedLinks, setSelectedLinks] = useState<SelectedLinkItem[]>([
    {
      id: 'default-amazon-link',
      name: 'Amazon India Storefront',
      url: DEFAULT_APPLICATION_LINK
    }
  ]);
  const [newLinkName, setNewLinkName] = useState<string>('');
  const [newLinkUrl, setNewLinkUrl] = useState<string>('');
  const [linkValidationError, setLinkValidationError] = useState<string | null>(null);

  // Edit Link State
  const [editingLinkId, setEditingLinkId] = useState<string | null>(null);
  const [editLinkName, setEditLinkName] = useState<string>('');
  const [editLinkUrl, setEditLinkUrl] = useState<string>('');

  // Status & Validation Error States
  const [loadingAreas, setLoadingAreas] = useState<boolean>(true);
  const [loadingStories, setLoadingStories] = useState<boolean>(false);
  const [loadingCriteria, setLoadingCriteria] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // 1. Initial Load: Fetch Areas from Database
  useEffect(() => {
    async function loadAreasAndApps() {
      try {
        setLoadingAreas(true);
        setValidationError(null);
        const [areaList, appList] = await Promise.all([
          fetchAreas().catch(() => []),
          fetchApplications().catch(() => [])
        ]);
        setAreas(areaList);
        setApplications(appList);
      } catch (err: any) {
        setValidationError('Unable to load area information. Please try again.');
      } finally {
        setLoadingAreas(false);
      }
    }
    loadAreasAndApps();
  }, []);

  // 2. Load User Stories when selected Area(s) change
  useEffect(() => {
    if (selectedAreaIds.length === 0) {
      previousStoryIdsRef.current = [];
      setUserStories([]);
      setSelectedStoryIds([]);
      setAcceptanceCriteriaList([]);
      setSelectedCriteriaIds([]);
      return;
    }

    async function loadStories() {
      try {
        setLoadingStories(true);
        previousStoryIdsRef.current = [];
        setSelectedStoryIds([]);
        setAcceptanceCriteriaList([]);
        setSelectedCriteriaIds([]);
        setValidationError(null);

        const stories = await fetchUserStoriesByAreas(selectedAreaIds);
        setUserStories(stories);

        if (stories.length > 0) {
          // Pre-select the first story by default (single-story workflow out of the box)
          setSelectedStoryIds([stories[0].id]);
        }
      } catch (err) {
        setUserStories([]);
      } finally {
        setLoadingStories(false);
      }
    }
    loadStories();
  }, [selectedAreaIds]);

  // 3. Load Acceptance Criteria when selected User Stories change
  useEffect(() => {
    if (selectedStoryIds.length === 0) {
      previousStoryIdsRef.current = [];
      setAcceptanceCriteriaList([]);
      setSelectedCriteriaIds([]);
      return;
    }

    let isCurrent = true;
    async function loadCriteria() {
      try {
        setLoadingCriteria(true);
        setValidationError(null);

        const criteria = await fetchAcceptanceCriteriaByStories(selectedStoryIds);
        if (!isCurrent) return;

        // Deduplicate criteria
        const uniqueCriteria: AcceptanceCriteriaRead[] = [];
        const seenIds = new Set<string>();
        for (const c of criteria) {
          const upperId = c.id.toUpperCase();
          if (!seenIds.has(upperId)) {
            seenIds.add(upperId);
            uniqueCriteria.push(c);
          }
        }
        setAcceptanceCriteriaList(uniqueCriteria);

        // Compute newly added stories compared to previously tracked selection
        const prevUpper = previousStoryIdsRef.current.map(s => s.toUpperCase());
        const newlyAddedStories = selectedStoryIds.filter(
          id => !prevUpper.includes(id.toUpperCase())
        );
        previousStoryIdsRef.current = selectedStoryIds;

        // Pre-select criteria for newly added stories while preserving existing user selections
        setSelectedCriteriaIds(prev => {
          // Keep existing selections that belong to the current unique criteria
          const validPrev = prev.filter(id =>
            uniqueCriteria.some(c => c.id.toUpperCase() === id.toUpperCase())
          );
          // Auto-select criteria belonging to newly added stories
          const newItems = uniqueCriteria
            .filter(c =>
              newlyAddedStories.some(sid => sid.toUpperCase() === c.user_story_id.toUpperCase()) &&
              !validPrev.includes(c.id)
            )
            .map(c => c.id);
          return Array.from(new Set([...validPrev, ...newItems]));
        });
      } catch (err) {
        if (!isCurrent) return;
        setAcceptanceCriteriaList([]);
        setSelectedCriteriaIds([]);
      } finally {
        if (isCurrent) {
          setLoadingCriteria(false);
        }
      }
    }
    loadCriteria();
    return () => {
      isCurrent = false;
    };
  }, [selectedStoryIds]);

  const selectedArea = selectedAreaIds.length > 0 ? areas.find(a => a.id === selectedAreaIds[0]) : null;

  // Handlers for User Stories selection
  const handleToggleStory = (storyId: string) => {
    setValidationError(null);
    setSelectedStoryIds(prev =>
      prev.includes(storyId) ? prev.filter(id => id !== storyId) : [...prev, storyId]
    );
  };

  const handleSelectAllStories = () => {
    setValidationError(null);
    setSelectedStoryIds(userStories.map(s => s.id));
  };

  const handleDeselectAllStories = () => {
    setValidationError(null);
    setSelectedStoryIds([]);
  };

  // Handlers for Acceptance Criteria selection
  const handleToggleCriteria = (id: string) => {
    setValidationError(null);
    setSelectedCriteriaIds(prev =>
      prev.includes(id) ? prev.filter(cId => cId !== id) : [...prev, id]
    );
  };

  const handleSelectAllCriteria = () => {
    setValidationError(null);
    if (selectedCriteriaIds.length === acceptanceCriteriaList.length) {
      setSelectedCriteriaIds([]);
    } else {
      setSelectedCriteriaIds(acceptanceCriteriaList.map(c => c.id));
    }
  };

  const handleToggleGroupCriteria = (groupCriteria: AcceptanceCriteriaRead[]) => {
    setValidationError(null);
    const groupIds = groupCriteria.map(c => c.id);
    const allSelected = groupIds.every(id => selectedCriteriaIds.includes(id));
    if (allSelected) {
      setSelectedCriteriaIds(prev => prev.filter(id => !groupIds.includes(id)));
    } else {
      setSelectedCriteriaIds(prev => Array.from(new Set([...prev, ...groupIds])));
    }
  };

  // Group Acceptance Criteria by User Story
  const groupedCriteria = React.useMemo(() => {
    const groups: {
      storyId: string;
      storyTitle: string;
      criteria: AcceptanceCriteriaRead[];
    }[] = [];

    selectedStoryIds.forEach(storyId => {
      const story = userStories.find(s => s.id.toUpperCase() === storyId.toUpperCase());
      const title = story ? story.title : storyId;
      const storyCriteria = acceptanceCriteriaList.filter(
        c => c.user_story_id.toUpperCase() === storyId.toUpperCase()
      );
      if (storyCriteria.length > 0) {
        groups.push({
          storyId,
          storyTitle: title,
          criteria: storyCriteria
        });
      }
    });

    // Fallback: criteria whose storyId is not in selectedStoryIds
    const addedIds = new Set(groups.map(g => g.storyId.toUpperCase()));
    const remaining = acceptanceCriteriaList.filter(
      c => !addedIds.has(c.user_story_id.toUpperCase())
    );
    if (remaining.length > 0) {
      const remMap = new Map<string, AcceptanceCriteriaRead[]>();
      remaining.forEach(c => {
        const list = remMap.get(c.user_story_id) || [];
        list.push(c);
        remMap.set(c.user_story_id, list);
      });
      remMap.forEach((crits, sid) => {
        const story = userStories.find(s => s.id.toUpperCase() === sid.toUpperCase());
        groups.push({
          storyId: sid,
          storyTitle: story ? story.title : sid,
          criteria: crits
        });
      });
    }

    return groups;
  }, [selectedStoryIds, userStories, acceptanceCriteriaList]);

  // Add custom manual application link
  const handleAddCustomLink = () => {
    setLinkValidationError(null);
    if (!newLinkUrl.trim()) {
      setLinkValidationError('Please enter a valid URL.');
      return;
    }

    if (isBlockedScheme(newLinkUrl)) {
      setLinkValidationError('Please enter a valid web address starting with http:// or https://');
      return;
    }

    const normUrl = normalizeUrl(newLinkUrl);
    const duplicate = selectedLinks.find(l => normalizeUrl(l.url) === normUrl);
    if (duplicate) {
      setLinkValidationError('This application link has already been added.');
      return;
    }

    const finalName = newLinkName.trim()
      ? newLinkName.trim()
      : `Application Link ${selectedLinks.length + 1}`;

    const newItem: SelectedLinkItem = {
      id: `link-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      name: finalName,
      url: newLinkUrl.trim()
    };

    setSelectedLinks([...selectedLinks, newItem]);
    setNewLinkName('');
    setNewLinkUrl('');
  };

  const handleRemoveLink = (id: string) => {
    setSelectedLinks(selectedLinks.filter(l => l.id !== id));
    if (editingLinkId === id) {
      setEditingLinkId(null);
    }
  };

  const handleStartEditLink = (link: SelectedLinkItem) => {
    setEditingLinkId(link.id);
    setEditLinkName(link.name);
    setEditLinkUrl(link.url);
    setLinkValidationError(null);
  };

  const handleSaveEditLink = (id: string) => {
    setLinkValidationError(null);
    if (!editLinkUrl.trim()) {
      setLinkValidationError('Please enter a valid URL.');
      return;
    }

    if (isBlockedScheme(editLinkUrl)) {
      setLinkValidationError('Please enter a valid web address starting with http:// or https://');
      return;
    }

    const normUrl = normalizeUrl(editLinkUrl);
    const duplicate = selectedLinks.find(l => l.id !== id && normalizeUrl(l.url) === normUrl);
    if (duplicate) {
      setLinkValidationError('Another link already uses this URL.');
      return;
    }

    setSelectedLinks(selectedLinks.map(l => {
      if (l.id === id) {
        return {
          ...l,
          name: editLinkName.trim() ? editLinkName.trim() : l.name,
          url: editLinkUrl.trim()
        };
      }
      return l;
    }));

    setEditingLinkId(null);
  };

  // Form Submission Handler with Strict Validations
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validation 1: Area / Service Selection
    if (selectedAreaIds.length === 0) {
      setValidationError('Please select an area to continue.');
      return;
    }

    // Validation 2: User Story Selection (Single or Multiple)
    if (selectedStoryIds.length === 0) {
      setValidationError('Please select at least one user story to continue.');
      return;
    }

    // Validation 3: Acceptance Criteria Selection (CRITICAL REQUIRED BEHAVIOR)
    if (selectedCriteriaIds.length === 0) {
      setValidationError('No acceptance criteria selected. Please select at least one acceptance criterion to continue.');
      return;
    }

    // Resolve underlying application_id from selected Area or default app
    let appId = selectedArea?.application_id;
    if (!appId && applications.length > 0) {
      appId = applications[0].id;
    }

    const formattedLinks: ApplicationLinkPayload[] = selectedLinks.map(l => ({
      name: l.name,
      url: l.url
    }));

    const selectedServiceNames = selectedAreaIds
      .map(id => areas.find(a => a.id === id)?.name)
      .filter((name): name is string => Boolean(name));

    onSubmit({
      application_id: appId || 1,
      requirement_source: 'ACCEPTANCE_CRITERIA',
      requirement_identifiers: Array.from(new Set(selectedCriteriaIds)),
      requirement_identifier: selectedCriteriaIds[0],
      user_story_ids: selectedStoryIds,
      application_links: formattedLinks,
      application_url: formattedLinks.length > 0 ? formattedLinks[0].url : DEFAULT_APPLICATION_LINK,
      area_ids: selectedAreaIds,
      area_id: selectedAreaIds.length > 0 ? selectedAreaIds[0] : undefined,
      services: selectedServiceNames,
      service: selectedServiceNames.length > 0 ? selectedServiceNames[0] : undefined
    });
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-2xl space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">

        {/* Global Validation Alert Banner */}
        {validationError && (
          <div className="p-4 rounded-xl bg-red-950/80 border border-red-800/80 flex items-center space-x-3 text-red-200 text-sm font-medium animate-pulse shadow-lg">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {/* STEP 1: SELECT AREA / SERVICE (AZURE DEVOPS-STYLE HIERARCHY) */}
        <AreaSelector
          areas={areas}
          selectedAreaIds={selectedAreaIds}
          onSelectAreas={(ids) => {
            setSelectedAreaIds(ids);
            setValidationError(null);
          }}
          isLoading={loadingAreas}
        />

        {/* STEP 2: DISPLAY & SELECT USER STORIES */}
        <div className="space-y-2.5 pt-2 border-t border-slate-800/60">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center space-x-2 text-slate-200 font-semibold text-sm">
              <div className="w-6 h-6 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 text-xs">
                2
              </div>
              <FileText className="w-4 h-4 text-blue-400" />
              <span>User Stories</span>
            </div>

            {userStories.length > 0 && (
              <div className="flex items-center space-x-3">
                <span id="selected-stories-count" className="text-xs text-blue-400 font-mono font-medium">
                  {selectedStoryIds.length} User Stor{selectedStoryIds.length === 1 ? 'y' : 'ies'} selected
                </span>
                <span className="text-slate-600 text-xs">|</span>
                <button
                  type="button"
                  id="select-all-stories-btn"
                  onClick={handleSelectAllStories}
                  className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors cursor-pointer"
                >
                  Select All
                </button>
                <span className="text-slate-600 text-xs">·</span>
                <button
                  type="button"
                  id="deselect-all-stories-btn"
                  onClick={handleDeselectAllStories}
                  className="text-xs text-slate-400 hover:text-slate-200 font-medium transition-colors cursor-pointer"
                >
                  Deselect All
                </button>
              </div>
            )}
          </div>

          {loadingStories ? (
            <div className="flex items-center space-x-2.5 py-4 text-slate-400 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span>Loading user stories...</span>
            </div>
          ) : userStories.length === 0 ? (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 text-xs italic">
              Please select an area to view available user stories.
            </div>
          ) : (
            /* Azure DevOps Tree / Work Item Style Selection */
            <div className="bg-slate-950 border border-slate-800 rounded-lg divide-y divide-slate-800/60 overflow-hidden">
              <div className="bg-slate-900/60 px-4 py-2 text-[11px] font-semibold text-slate-400 tracking-wider uppercase flex items-center justify-between">
                <span>Area: {selectedArea?.name || 'Selected Area'}</span>
                <span className="text-[10px] text-slate-500 font-normal">Select one or more user stories</span>
              </div>
              {userStories.map((story) => {
                const isSelected = selectedStoryIds.includes(story.id);
                return (
                  <div
                    key={story.id}
                    id={`story-row-${story.id}`}
                    onClick={() => handleToggleStory(story.id)}
                    className={`w-full text-left px-4 py-3 transition-all flex items-center justify-between cursor-pointer group ${
                      isSelected
                        ? 'bg-blue-950/40 border-l-4 border-blue-500 text-blue-100 font-medium'
                        : 'hover:bg-slate-900/60 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center space-x-3 min-w-0 flex-1 mr-3">
                      <span className="text-slate-500 font-mono text-xs shrink-0">├──</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono shrink-0 ${
                        isSelected
                          ? 'bg-blue-900/80 border border-blue-600 text-blue-200'
                          : 'bg-slate-800 border border-slate-700 text-slate-400'
                      }`}>
                        {story.id}
                      </span>
                      <span className="text-xs font-medium truncate">
                        {story.title}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      <input
                        id={`story-checkbox-${story.id}`}
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleToggleStory(story.id);
                        }}
                        className="rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500 h-4 w-4 cursor-pointer"
                      />
                      {isSelected && (
                        <span className="text-[11px] text-blue-400 font-semibold font-mono hidden sm:inline">
                          Selected
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* STEP 3: DISPLAY & SELECT ACCEPTANCE CRITERIA */}
        <div className="space-y-2.5 pt-2 border-t border-slate-800/60">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center space-x-2 text-slate-200 font-semibold text-sm">
              <div className="w-6 h-6 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 text-xs">
                3
              </div>
              <CheckSquare className="w-4 h-4 text-blue-400" />
              <span>Acceptance Criteria</span>
            </div>

            {acceptanceCriteriaList.length > 0 && (
              <div className="flex items-center space-x-3">
                <span id="selected-criteria-count" className="text-xs text-emerald-400 font-mono font-medium">
                  {selectedCriteriaIds.length} of {acceptanceCriteriaList.length} selected
                </span>
                <span className="text-slate-600 text-xs">|</span>
                <button
                  type="button"
                  id="select-all-criteria-btn"
                  onClick={handleSelectAllCriteria}
                  className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors cursor-pointer"
                >
                  {selectedCriteriaIds.length === acceptanceCriteriaList.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
            )}
          </div>

          {selectedStoryIds.length === 1 && (
            <div className="text-xs text-slate-300 bg-slate-950/80 px-3.5 py-2 rounded-lg border border-slate-800/80 font-medium flex items-center justify-between">
              <div>
                User Story: <span className="font-bold text-blue-400">{selectedStoryIds[0]}</span>
                {userStories.find(s => s.id === selectedStoryIds[0]) ? (
                  <span> – {userStories.find(s => s.id === selectedStoryIds[0])?.title}</span>
                ) : null}
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                {acceptanceCriteriaList.length} criteria
              </span>
            </div>
          )}

          {selectedStoryIds.length > 1 && (
            <div className="text-xs text-slate-300 bg-slate-950/80 px-3.5 py-2 rounded-lg border border-slate-800/80 font-medium flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center space-x-2">
                <span className="text-slate-400">Selected User Stories ({selectedStoryIds.length}):</span>
                <div className="flex flex-wrap gap-1">
                  {selectedStoryIds.map(id => (
                    <span key={id} className="px-1.5 py-0.5 rounded bg-blue-950 border border-blue-700/80 text-blue-300 font-mono text-[11px] font-bold">
                      {id}
                    </span>
                  ))}
                </div>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                {acceptanceCriteriaList.length} total criteria across {selectedStoryIds.length} stories
              </span>
            </div>
          )}

          {loadingCriteria ? (
            <div className="flex items-center space-x-2.5 py-4 text-slate-400 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span>Loading acceptance criteria...</span>
            </div>
          ) : selectedStoryIds.length === 0 ? (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 text-xs italic">
              Please select at least one user story to view its acceptance criteria.
            </div>
          ) : acceptanceCriteriaList.length === 0 ? (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-slate-400 text-xs italic">
              No acceptance criteria found for the selected user stories.
            </div>
          ) : (
            <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
              {groupedCriteria.map((group) => {
                const groupSelectedCount = group.criteria.filter(c => selectedCriteriaIds.includes(c.id)).length;
                const isAllGroupSelected = groupSelectedCount === group.criteria.length;

                return (
                  <div
                    key={group.storyId}
                    id={`criteria-group-${group.storyId}`}
                    className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-sm"
                  >
                    {/* Story Group Header */}
                    <div className="bg-slate-900/90 px-3.5 py-2.5 border-b border-slate-800 flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center space-x-2 min-w-0 flex-1 mr-2">
                        <span className="font-bold text-blue-400 font-mono text-xs px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800/80 shrink-0">
                          {group.storyId}
                        </span>
                        <span className="text-slate-400 text-xs shrink-0">–</span>
                        <span className="font-semibold text-slate-200 text-xs truncate">
                          {group.storyTitle}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2.5 shrink-0">
                        <span className="text-[11px] text-slate-400 font-mono">
                          {groupSelectedCount}/{group.criteria.length} selected
                        </span>
                        <button
                          type="button"
                          id={`toggle-group-btn-${group.storyId}`}
                          onClick={() => handleToggleGroupCriteria(group.criteria)}
                          className="text-[11px] text-blue-400 hover:text-blue-300 font-medium transition-colors hover:underline cursor-pointer"
                        >
                          {isAllGroupSelected ? 'Deselect Group' : 'Select Group'}
                        </button>
                      </div>
                    </div>

                    {/* Criteria List for this Story */}
                    <div className="divide-y divide-slate-800/60">
                      {group.criteria.map((crit) => {
                        const isChecked = selectedCriteriaIds.includes(crit.id);
                        const acCode = `AC-${crit.criteria_number < 10 ? `0${crit.criteria_number}` : crit.criteria_number}`;
                        const cleanText = crit.text.replace(/^(?:AC-?[0-9]+[\s:-]*|[0-9]+[\.\)]\s*)+/i, '').trim();

                        return (
                          <div
                            key={crit.id}
                            id={`criteria-row-${crit.id}`}
                            onClick={() => handleToggleCriteria(crit.id)}
                            className={`flex items-start space-x-3 p-3 cursor-pointer transition-all ${
                              isChecked
                                ? 'bg-emerald-950/20 text-emerald-200'
                                : 'bg-slate-950 text-slate-400 hover:bg-slate-900/50'
                            }`}
                          >
                            <input
                              id={`criteria-checkbox-${crit.id}`}
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                e.stopPropagation();
                                handleToggleCriteria(crit.id);
                              }}
                              className="mt-0.5 rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500 shrink-0 h-4 w-4 cursor-pointer"
                            />
                            <div className="space-y-0.5 text-xs flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="font-bold text-emerald-400 font-mono text-xs px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/80">
                                  {acCode}
                                </span>
                                <span className="text-[11px] text-slate-500 font-mono">
                                  {crit.id}
                                </span>
                              </div>
                              <span className="text-slate-200 leading-relaxed block mt-1">
                                {cleanText || crit.text}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* STEP 4: APPLICATION LINK (DEFAULT: https://www.amazon.in/) */}
        <div className="space-y-3 pt-2 border-t border-slate-800/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-slate-200 font-semibold text-sm">
              <div className="w-6 h-6 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 text-xs">
                4
              </div>
              <Globe className="w-4 h-4 text-blue-400" />
              <span>Application Link</span>
            </div>
            {selectedLinks.length > 0 && (
              <span className="text-xs text-slate-400 font-medium">
                {selectedLinks.length} link{selectedLinks.length > 1 ? 's' : ''} set
              </span>
            )}
          </div>

          {/* Validation Error Message for Link */}
          {linkValidationError && (
            <div className="p-2.5 rounded-lg bg-red-950/50 border border-red-800/60 text-red-300 text-xs">
              {linkValidationError}
            </div>
          )}

          {/* Selected Links List */}
          {selectedLinks.length > 0 && (
            <div className="border border-slate-800 rounded-lg divide-y divide-slate-800/60 bg-slate-950 overflow-hidden">
              {selectedLinks.map((link) => (
                <div key={link.id} className="p-3">
                  {editingLinkId === link.id ? (
                    /* EDIT MODE */
                    <div className="space-y-2 bg-slate-900 p-3 rounded-lg border border-blue-500/40">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="text-[11px] text-slate-400 font-medium block mb-1">Link Name</label>
                          <input
                            type="text"
                            value={editLinkName}
                            onChange={(e) => setEditLinkName(e.target.value)}
                            placeholder="e.g. Amazon Storefront"
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] text-slate-400 font-medium block mb-1">URL</label>
                          <input
                            type="text"
                            value={editLinkUrl}
                            onChange={(e) => setEditLinkUrl(e.target.value)}
                            placeholder="https://www.amazon.in/"
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-100"
                          />
                        </div>
                      </div>

                      <div className="flex items-center justify-end space-x-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setEditingLinkId(null)}
                          className="px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSaveEditLink(link.id)}
                          className="px-3 py-1 bg-blue-600 text-white rounded text-xs font-semibold"
                        >
                          Save Changes
                        </button>
                      </div>
                    </div>
                  ) : (
                    /* DISPLAY MODE */
                    <div className="flex items-center justify-between gap-3">
                      <div className="space-y-0.5 min-w-0 flex-1">
                        <span className="font-semibold text-slate-200 text-xs truncate block">
                          {link.name}
                        </span>
                        <div className="text-xs text-blue-400 truncate flex items-center space-x-1.5 font-mono">
                          <Globe className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                          <span className="truncate">{link.url}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleStartEditLink(link)}
                          className="p-1.5 text-slate-400 hover:text-slate-200 transition-colors rounded hover:bg-slate-900"
                          title="Edit link"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveLink(link.id)}
                          className="p-1.5 text-slate-400 hover:text-red-400 transition-colors rounded hover:bg-slate-900"
                          title="Remove link"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Add New Link Control */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                type="text"
                value={newLinkName}
                onChange={(e) => setNewLinkName(e.target.value)}
                placeholder="Link Name (e.g. Checkout Page)"
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="text"
                value={newLinkUrl}
                onChange={(e) => setNewLinkUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddCustomLink();
                  }
                }}
                placeholder="URL (e.g. https://www.amazon.in/)"
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="button"
              onClick={handleAddCustomLink}
              className="bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Link</span>
            </button>
          </div>
        </div>

        {/* STEP 5: GENERATE TEST CASES ACTION */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || loadingAreas}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 rounded-xl shadow-lg flex items-center justify-center space-x-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Generating Test Cases...</span>
              </>
            ) : (
              <span>Generate Test Cases</span>
            )}
          </button>
        </div>

      </form>
    </div>
  );
};
