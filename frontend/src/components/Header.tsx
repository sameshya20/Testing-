import React, { useState, useRef, useEffect } from 'react';
import { Layers, ChevronDown, User as UserIcon, LogOut, RefreshCw } from 'lucide-react';
import type { User } from '../types';

export interface IntegrationStatusInfo {
  connected: boolean;
  mode?: string;
  project?: string | null;
  organization?: string | null;
  isSyncing?: boolean;
  syncSuccess?: boolean;
  syncFailed?: boolean;
  lastSyncedTime?: string | null;
}

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
  integrationStatus?: IntegrationStatusInfo;
  onOpenSettings?: () => void;
  activeNav?: string;
  onSelectNav?: (nav: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onLogout,
  integrationStatus,
  onOpenSettings,
  activeNav = 'Test Cases',
  onSelectNav
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const initial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : (user?.email ? user.email.charAt(0).toUpperCase() : 'U');

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Transient sync status only (no connection/disconnected badges)
  const renderStatusBadge = () => {
    if (!integrationStatus) return null;

    if (integrationStatus.isSyncing) {
      return (
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-950/60 text-blue-300 border border-blue-800/60">
          <RefreshCw className="w-3 h-3 animate-spin text-blue-400" />
          <span>Syncing</span>
        </div>
      );
    }

    return null;
  };

  const navItems = ['Dashboard', 'Projects', 'User Stories', 'Test Cases', 'Integrations', 'Settings'];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          
          {/* Brand & Main Nav */}
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2.5">
              <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center shadow-xs">
                <Layers className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-white tracking-tight">
                Test Case Generator
              </span>
            </div>

            {/* Navigation Tabs - Clean, no subtitles or definitions under icons */}
            {user && (
              <nav className="hidden md:flex items-center space-x-1" aria-label="Main Navigation">
                {navItems.map((item) => {
                  const isActive = activeNav === item;
                  return (
                    <button
                      key={item}
                      type="button"
                      onClick={() => onSelectNav && onSelectNav(item)}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-slate-800 text-white'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                      }`}
                    >
                      {item}
                    </button>
                  );
                })}
              </nav>
            )}
          </div>

          {/* Right section: Integration Status + User Profile */}
          <div className="flex items-center space-x-3">
            {/* Discreet Integration Status Badge */}
            {user && (
              <div className="hidden sm:flex items-center" title="Azure DevOps Integration Status">
                {renderStatusBadge()}
              </div>
            )}

            {/* User Profile Area */}
            {user && (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsOpen(!isOpen)}
                  className="flex items-center space-x-2 p-1 rounded-md hover:bg-slate-800 border border-slate-800 transition-colors focus:outline-none"
                  aria-label="User Profile Menu"
                >
                  <div className="w-6 h-6 rounded bg-slate-800 text-blue-400 font-semibold text-xs flex items-center justify-center border border-slate-700">
                    {initial}
                  </div>
                  <span className="hidden sm:inline text-xs font-medium text-slate-300">
                    {user.full_name || user.email.split('@')[0]}
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {/* Dropdown Menu */}
                {isOpen && (
                  <div className="absolute right-0 mt-1.5 w-52 bg-slate-900 border border-slate-800 rounded-lg shadow-xl py-1 z-50 divide-y divide-slate-800">
                    <div className="px-3 py-2">
                      <p className="text-xs font-semibold text-white truncate">{user.full_name || 'QA Engineer'}</p>
                      <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
                    </div>

                    <div className="py-1">
                      <button
                        type="button"
                        onClick={() => {
                          setIsOpen(false);
                          if (onOpenSettings) onOpenSettings();
                        }}
                        className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 flex items-center space-x-2 transition-colors"
                      >
                        <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                        <span>Profile & Settings</span>
                      </button>
                    </div>

                    <div className="py-1">
                      <button
                        type="button"
                        onClick={() => {
                          setIsOpen(false);
                          onLogout();
                        }}
                        className="w-full text-left px-3 py-1.5 text-xs text-red-400 hover:bg-slate-800 flex items-center space-x-2 transition-colors"
                      >
                        <LogOut className="w-3.5 h-3.5 text-red-400" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
};
