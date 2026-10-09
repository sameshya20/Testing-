import React, { useState, useEffect, useRef } from 'react';
import type {
  Area,
  UserStory,
  AcceptanceCriteriaRead,
  Application,
  TestCaseGenerationRequest,
  ApplicationLinkPayload,
  DevOpsWorkItem
} from '../types';
import {
  fetchAreas,
  fetchUserStoriesByAreas,
  fetchAcceptanceCriteriaByStories,
  fetchApplications,
  fetchAzureDevOpsAreas,
  fetchAzureDevOpsWorkItems,
  fetchAzureDevOpsWorkItem
} from '../services/api';
import { AreaSelector } from './AreaSelector';
import {
  Loader2,
  Plus,
  X,
  Edit2,
  Globe,
  AlertCircle,
  User,
  FolderGit2,
  Calendar
} from 'lucide-react';

interface SelectedLinkItem {
  id: string;
  name: string;
  url: string;
}

interface ApplicationFormProps {
  onSubmit: (payload: TestCaseGenerationRequest) => void;
  isLoading: boolean;
  isAdoConnected?: boolean;
  adoProject?: string | null;
  adoOrg?: string | null;
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

export const ApplicationForm: React.FC<ApplicationFormProps> = ({
  onSubmit,
  isLoading,
  isAdoConnected = false,
  adoProject = null
}) => {
  // Database Data States
  const [areas, setAreas] = useState<Area[]>([]);
  const [userStories, setUserStories] = useState<UserStory[]>([]);
  const [acceptanceCriteriaList, setAcceptanceCriteriaList] = useState<AcceptanceCriteriaRead[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);

  // Azure DevOps Work Items state
  const [adoWorkItems, setAdoWorkItems] = useState<DevOpsWorkItem[]>([]);
  const [activeStoryDetails, setActiveStoryDetails] = useState<DevOpsWorkItem | null>(null);
  const [loadingStoryDetails, setLoadingStoryDetails] = useState<boolean>(false);

  // Selection States
  const [selectedAreaIds, setSelectedAreaIds] = useState<number[]>([]);
  const [selectedStoryIds, setSelectedStoryIds] = useState<string[]>([]);
  const [selectedCriteriaIds, setSelectedCriteriaIds] = useState<string[]>([]);

  const previousStoryIdsRef = useRef<string[]>([]);

  // Application Link State
  const [selectedLinks, setSelectedLinks] = useState<SelectedLinkItem[]>([
    {
      id: 'default-amazon-link',
      name: 'Amazon Storefront',
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

  // 1. Initial Load: Fetch Areas from Azure DevOps or Database
  useEffect(() => {
    async function loadAreasAndApps() {
      try {
        setLoadingAreas(true);
        setValidationError(null);
        setSelectedAreaIds([]);
        setUserStories([]);
        setSelectedStoryIds([]);
        setAcceptanceCriteriaList([]);
        setSelectedCriteriaIds([]);
        setActiveStoryDetails(null);

        let areaList: Area[] = [];
        let appList: Application[] = [];

        if (isAdoConnected) {
          try {
            areaList = await fetchAzureDevOpsAreas(adoProject || undefined);
          } catch {
            areaList = await fetchAreas().catch(() => []);
          }
          appList = await fetchApplications().catch(() => []);
        } else {
          const [dbAreas, dbApps] = await Promise.all([
            fetchAreas().catch(() => []),
            fetchApplications().catch(() => [])
          ]);
          areaList = dbAreas;
          appList = dbApps;
        }

        setAreas(areaList);
        setApplications(appList);
      } catch {
        setValidationError('Unable to load area information. Please try again.');
      } finally {
        setLoadingAreas(false);
      }
    }
    loadAreasAndApps();
  }, [isAdoConnected, adoProject]);

  // 2. Load User Stories when selected Area(s) change
  useEffect(() => {
    if (selectedAreaIds.length === 0) {
      previousStoryIdsRef.current = [];
      setUserStories([]);
      setSelectedStoryIds([]);
      setAcceptanceCriteriaList([]);
      setSelectedCriteriaIds([]);
      setActiveStoryDetails(null);
      return;
    }

    async function loadStories() {
      try {
        setLoadingStories(true);
        previousStoryIdsRef.current = [];
        setSelectedStoryIds([]);
        setAcceptanceCriteriaList([]);
        setSelectedCriteriaIds([]);
        setActiveStoryDetails(null);
        setValidationError(null);

        if (isAdoConnected) {
          const selectedAreaObj = areas.find(a => a.id === selectedAreaIds[0]);
          const areaPath = selectedAreaObj?.path || selectedAreaObj?.name;
          const adoItems = await fetchAzureDevOpsWorkItems(areaPath, adoProject || undefined);

          if (adoItems && adoItems.length > 0) {
            setAdoWorkItems(adoItems);
            const mappedStories: UserStory[] = adoItems.map(item => ({
              id: item.id.replace(/^#/, ''),
              title: item.title,
              description: item.description || '',
              application_id: selectedAreaObj?.application_id || 1,
              area_id: selectedAreaObj?.id || 1,
              state: item.state || 'Active'
            }));
            setUserStories(mappedStories);

            const firstId = mappedStories[0].id;
            setSelectedStoryIds([firstId]);
            setActiveStoryDetails(adoItems[0]);
            return;
          }
        }

        const stories = await fetchUserStoriesByAreas(selectedAreaIds);
        setUserStories(stories);

        if (stories.length > 0) {
          setSelectedStoryIds([stories[0].id]);
        }
      } catch {
        try {
          const stories = await fetchUserStoriesByAreas(selectedAreaIds);
          setUserStories(stories);
          if (stories.length > 0) {
            setSelectedStoryIds([stories[0].id]);
          }
        } catch {
          setUserStories([]);
        }
      } finally {
        setLoadingStories(false);
      }
    }
    loadStories();
  }, [selectedAreaIds, isAdoConnected, adoProject, areas]);

  // Load complete Azure DevOps Story details on story selection
  useEffect(() => {
    if (!isAdoConnected || selectedStoryIds.length === 0) {
      if (!isAdoConnected) setActiveStoryDetails(null);
      return;
    }

    const currentId = selectedStoryIds[0];
    const cached = adoWorkItems.find(w => w.id.replace(/^#/, '') === currentId.replace(/^#/, ''));
    if (cached && cached.description && cached.acceptance_criteria) {
      setActiveStoryDetails(cached);
    } else {
      setLoadingStoryDetails(true);
      fetchAzureDevOpsWorkItem(currentId, adoProject || undefined)
        .then(item => {
          setActiveStoryDetails(item);
        })
        .catch(() => {
          if (cached) setActiveStoryDetails(cached);
        })
        .finally(() => {
          setLoadingStoryDetails(false);
        });
    }
  }, [selectedStoryIds, isAdoConnected, adoProject, adoWorkItems]);

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

        let effectiveCriteria = criteria;
        if (effectiveCriteria.length === 0 && isAdoConnected) {
          const fallbackAcs: AcceptanceCriteriaRead[] = [];
          selectedStoryIds.forEach(sid => {
            const item = adoWorkItems.find(w => w.id.replace(/^#/, '') === sid.replace(/^#/, ''));
            if (item && item.acceptance_criteria) {
              const lines = item.acceptance_criteria.split('\n').map(l => l.trim()).filter(Boolean);
              lines.forEach((line, idx) => {
                fallbackAcs.push({
                  id: `${sid}-AC-${idx + 1 < 10 ? '0' : ''}${idx + 1}`,
                  user_story_id: sid,
                  criteria_number: idx + 1,
                  text: line
                });
              });
            }
          });
          if (fallbackAcs.length > 0) {
            effectiveCriteria = fallbackAcs;
          }
        }

        const uniqueCriteria: AcceptanceCriteriaRead[] = [];
        const seenIds = new Set<string>();
        for (const c of effectiveCriteria) {
          const upperId = c.id.toUpperCase();
          if (!seenIds.has(upperId)) {
            seenIds.add(upperId);
            uniqueCriteria.push(c);
          }
        }
        setAcceptanceCriteriaList(uniqueCriteria);

        const prevUpper = previousStoryIdsRef.current.map(s => s.toUpperCase());
        const newlyAddedStories = selectedStoryIds.filter(
          id => !prevUpper.includes(id.toUpperCase())
        );
        previousStoryIdsRef.current = selectedStoryIds;

        setSelectedCriteriaIds(prev => {
          const validPrev = prev.filter(id =>
            uniqueCriteria.some(c => c.id.toUpperCase() === id.toUpperCase())
          );
          const newItems = uniqueCriteria
            .filter(c =>
              newlyAddedStories.some(sid => sid.toUpperCase() === c.user_story_id.toUpperCase()) &&
              !validPrev.includes(c.id)
            )
            .map(c => c.id);
          return Array.from(new Set([...validPrev, ...newItems]));
        });
      } catch {
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
  }, [selectedStoryIds, isAdoConnected, adoWorkItems]);

  const selectedArea = selectedAreaIds.length > 0 ? areas.find(a => a.id === selectedAreaIds[0]) : null;

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
      setLinkValidationError('This link has already been added.');
      return;
    }

    const finalName = newLinkName.trim()
      ? newLinkName.trim()
      : `Application Link ${selectedLinks.length + 1}`;

    const newItem: SelectedLinkItem = {
      id: `link-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (selectedAreaIds.length === 0) {
      setValidationError('Please select an area to continue.');
      return;
    }

    if (selectedStoryIds.length === 0) {
      setValidationError('Please select at least one user story to continue.');
      return;
    }

    if (selectedCriteriaIds.length === 0) {
      setValidationError('No acceptance criteria selected. Please select at least one acceptance criterion to continue.');
      return;
    }

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
    <div className="bg-slate-900 rounded-lg border border-slate-800 p-5 space-y-5">
      <form onSubmit={handleSubmit} className="space-y-5">

        {/* Global Validation Error */}
        {validationError && (
          <div className="p-3 rounded-md bg-red-950/60 border border-red-800/60 flex items-center space-x-2.5 text-red-300 text-xs font-medium">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {/* 1. AREA SELECTION */}
        <div>
          <AreaSelector
            areas={areas}
            selectedAreaIds={selectedAreaIds}
            onSelectAreas={(ids) => {
              setSelectedAreaIds(ids);
              setValidationError(null);
            }}
            isLoading={loadingAreas}
          />
        </div>

        {/* 2. USER STORIES */}
        <div className="space-y-2 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center space-x-2">
              <label className="text-xs font-semibold text-slate-200">User Stories</label>
              {isAdoConnected && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/60">
                  Azure DevOps
                </span>
              )}
            </div>

            {userStories.length > 0 && (
              <div className="flex items-center space-x-2 text-xs">
                <span id="selected-stories-count" className="text-slate-400 font-mono">
                  {selectedStoryIds.length} of {userStories.length} selected
                </span>
                <span className="text-slate-700">|</span>
                <button
                  type="button"
                  id="select-all-stories-btn"
                  onClick={handleSelectAllStories}
                  className="text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Select All
                </button>
                <span className="text-slate-700">·</span>
                <button
                  type="button"
                  id="deselect-all-stories-btn"
                  onClick={handleDeselectAllStories}
                  className="text-slate-400 hover:text-slate-200 transition-colors"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {loadingStories ? (
            <div className="flex items-center space-x-2 py-3 text-slate-400 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span>Loading user stories...</span>
            </div>
          ) : userStories.length === 0 ? (
            <div className="p-3 bg-slate-950 border border-slate-800 rounded text-slate-500 text-xs">
              Select an area to view user stories.
            </div>
          ) : (
            <div className="bg-slate-950 border border-slate-800 rounded divide-y divide-slate-800/80 max-h-56 overflow-y-auto">
              {userStories.map((story) => {
                const isSelected = selectedStoryIds.includes(story.id);
                return (
                  <div
                    key={story.id}
                    id={`story-row-${story.id}`}
                    onClick={() => handleToggleStory(story.id)}
                    className={`px-3 py-2 text-xs flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-950/40 text-blue-100'
                        : 'hover:bg-slate-900/60 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5 min-w-0 flex-1 mr-2">
                      <span className="font-mono font-semibold text-blue-400 shrink-0">
                        #{story.id.replace(/^#/, '')}
                      </span>
                      <span className="truncate">{story.title}</span>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      {story.state && (
                        <span className="px-1.5 py-0.5 text-[10px] rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {story.state}
                        </span>
                      )}
                      <input
                        id={`story-checkbox-${story.id}`}
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleToggleStory(story.id);
                        }}
                        className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5 cursor-pointer"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* WORK ITEM DETAILS DRAWER (IF CONNECTED & SELECTED) */}
        {isAdoConnected && (activeStoryDetails || loadingStoryDetails) && (
          <div className="bg-slate-950 border border-slate-800 rounded p-3 space-y-2 text-xs">
            {loadingStoryDetails ? (
              <div className="flex items-center space-x-2 py-1 text-slate-400 text-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                <span>Loading requirement details...</span>
              </div>
            ) : activeStoryDetails ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-blue-400">
                      #{activeStoryDetails.id.replace(/^#/, '')}
                    </span>
                    <span className="font-medium text-white truncate max-w-md">
                      {activeStoryDetails.title}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {activeStoryDetails.state && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                        {activeStoryDetails.state}
                      </span>
                    )}
                    {activeStoryDetails.assigned_to && (
                      <span className="text-slate-400 text-[11px] flex items-center space-x-1">
                        <User className="w-3 h-3 text-slate-500" />
                        <span>{activeStoryDetails.assigned_to}</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-400">
                  {activeStoryDetails.area_path && (
                    <div className="flex items-center space-x-1.5 truncate">
                      <FolderGit2 className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="text-slate-500">Area:</span>
                      <span className="text-slate-300 font-mono truncate">{activeStoryDetails.area_path}</span>
                    </div>
                  )}
                  {activeStoryDetails.iteration_path && (
                    <div className="flex items-center space-x-1.5 truncate">
                      <Calendar className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="text-slate-500">Iteration:</span>
                      <span className="text-slate-300 font-mono truncate">{activeStoryDetails.iteration_path}</span>
                    </div>
                  )}
                </div>

                {activeStoryDetails.description && (
                  <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/80 text-slate-300 text-xs leading-relaxed max-h-28 overflow-y-auto whitespace-pre-line">
                    {activeStoryDetails.description}
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}

        {/* 3. ACCEPTANCE CRITERIA */}
        <div className="space-y-2 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <label className="text-xs font-semibold text-slate-200">Acceptance Criteria</label>

            {acceptanceCriteriaList.length > 0 && (
              <div className="flex items-center space-x-2 text-xs">
                <span id="selected-criteria-count" className="text-slate-400 font-mono">
                  {selectedCriteriaIds.length} of {acceptanceCriteriaList.length} selected
                </span>
                <span className="text-slate-700">|</span>
                <button
                  type="button"
                  id="select-all-criteria-btn"
                  onClick={handleSelectAllCriteria}
                  className="text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {selectedCriteriaIds.length === acceptanceCriteriaList.length ? 'Clear All' : 'Select All'}
                </button>
              </div>
            )}
          </div>

          {loadingCriteria ? (
            <div className="flex items-center space-x-2 py-3 text-slate-400 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span>Loading acceptance criteria...</span>
            </div>
          ) : selectedStoryIds.length === 0 ? (
            <div className="p-3 bg-slate-950 border border-slate-800 rounded text-slate-500 text-xs">
              Select a user story to view acceptance criteria.
            </div>
          ) : acceptanceCriteriaList.length === 0 ? (
            <div className="p-3 bg-slate-950 border border-slate-800 rounded text-slate-500 text-xs">
              No acceptance criteria found for the selected user story.
            </div>
          ) : (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {groupedCriteria.map((group) => {
                const groupSelectedCount = group.criteria.filter(c => selectedCriteriaIds.includes(c.id)).length;
                const isAllGroupSelected = groupSelectedCount === group.criteria.length;

                return (
                  <div
                    key={group.storyId}
                    id={`criteria-group-${group.storyId}`}
                    className="bg-slate-950 border border-slate-800 rounded overflow-hidden"
                  >
                    <div className="bg-slate-900 px-3 py-2 border-b border-slate-800 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2 min-w-0 flex-1 mr-2">
                        <span className="font-mono font-semibold text-blue-400">
                          #{group.storyId}
                        </span>
                        <span className="text-slate-300 truncate font-medium">
                          {group.storyTitle}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 shrink-0">
                        <span className="text-slate-400 text-[11px] font-mono">
                          {groupSelectedCount}/{group.criteria.length}
                        </span>
                        <button
                          type="button"
                          id={`toggle-group-btn-${group.storyId}`}
                          onClick={() => handleToggleGroupCriteria(group.criteria)}
                          className="text-[11px] text-blue-400 hover:text-blue-300"
                        >
                          {isAllGroupSelected ? 'Deselect' : 'Select'}
                        </button>
                      </div>
                    </div>

                    <div className="divide-y divide-slate-800/70">
                      {group.criteria.map((crit) => {
                        const isChecked = selectedCriteriaIds.includes(crit.id);
                        const acCode = `AC-${crit.criteria_number < 10 ? `0${crit.criteria_number}` : crit.criteria_number}`;
                        const cleanText = crit.text.replace(/^(?:AC-?[0-9]+[\s:-]*|[0-9]+[.)]\s*)+/i, '').trim();

                        return (
                          <div
                            key={crit.id}
                            id={`criteria-row-${crit.id}`}
                            onClick={() => handleToggleCriteria(crit.id)}
                            className={`flex items-start space-x-2.5 p-2.5 cursor-pointer text-xs transition-colors ${
                              isChecked
                                ? 'bg-blue-950/20 text-slate-200'
                                : 'hover:bg-slate-900/40 text-slate-400'
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
                              className="mt-0.5 rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5 cursor-pointer shrink-0"
                            />
                            <div className="flex-1 space-y-0.5">
                              <div className="flex items-center space-x-2 font-mono text-[11px]">
                                <span className="font-semibold text-blue-400">{acCode}</span>
                                <span className="text-slate-500">{crit.id}</span>
                              </div>
                              <p className="text-slate-300 leading-normal">
                                {cleanText || crit.text}
                              </p>
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

        {/* 4. APPLICATION LINKS */}
        <div className="space-y-2 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-200">Application Links</label>
            <span className="text-[11px] text-slate-400">
              {selectedLinks.length} configured
            </span>
          </div>

          {linkValidationError && (
            <div className="p-2 rounded bg-red-950/60 border border-red-800/60 text-red-300 text-xs">
              {linkValidationError}
            </div>
          )}

          {/* Existing Links List */}
          {selectedLinks.length > 0 && (
            <div className="border border-slate-800 rounded divide-y divide-slate-800/80 bg-slate-950 overflow-hidden">
              {selectedLinks.map((link) => (
                <div key={link.id} className="p-2.5 text-xs">
                  {editingLinkId === link.id ? (
                    <div className="space-y-2 bg-slate-900 p-2.5 rounded border border-blue-600/40">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <input
                          type="text"
                          value={editLinkName}
                          onChange={(e) => setEditLinkName(e.target.value)}
                          placeholder="Link Name"
                          className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-100"
                        />
                        <input
                          type="text"
                          value={editLinkUrl}
                          onChange={(e) => setEditLinkUrl(e.target.value)}
                          placeholder="https://example.com"
                          className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-100"
                        />
                      </div>
                      <div className="flex justify-end space-x-2">
                        <button
                          type="button"
                          onClick={() => setEditingLinkId(null)}
                          className="px-2 py-1 text-xs text-slate-400 hover:text-white"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSaveEditLink(link.id)}
                          className="px-2.5 py-1 bg-blue-600 text-white rounded text-xs font-medium"
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center space-x-2 min-w-0 flex-1">
                        <Globe className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="font-medium text-slate-200 shrink-0">{link.name}</span>
                        <span className="text-slate-500">·</span>
                        <span className="text-slate-400 font-mono truncate">{link.url}</span>
                      </div>
                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleStartEditLink(link)}
                          className="p-1 text-slate-400 hover:text-slate-200"
                          title="Edit"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveLink(link.id)}
                          className="p-1 text-slate-400 hover:text-red-400"
                          title="Delete"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Add Link Row */}
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                type="text"
                value={newLinkName}
                onChange={(e) => setNewLinkName(e.target.value)}
                placeholder="Link Name (e.g. Checkout Page)"
                className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 text-xs focus:outline-none focus:border-blue-500"
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
                className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 text-xs focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
            <button
              type="button"
              onClick={handleAddCustomLink}
              className="bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 px-2.5 py-1 rounded text-xs font-medium flex items-center space-x-1 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Link</span>
            </button>
          </div>
        </div>

        {/* 5. GENERATE ACTION BUTTON */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || loadingAreas}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-md flex items-center justify-center space-x-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm cursor-pointer"
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
