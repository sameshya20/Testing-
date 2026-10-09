export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApplicationLinkPayload {
  name?: string;
  url: string;
  requirement_ref?: string;
}

export interface Application {
  id: number;
  name: string;
  code: string;
  domain: string;
  description?: string;
  default_url?: string;
  business_rules?: string;
  user_roles?: string;
  key_modules?: string;
  available_links?: ApplicationLinkPayload[];
}

export interface Area {
  id: number;
  name: string;
  code: string;
  description?: string;
  application_id?: number;
  parent_id?: number | null;
  path?: string;
}

export interface UserStory {
  id: string;
  title: string;
  description?: string;
  state?: string;
  assigned_to?: string;
  area_id?: number;
  area_path?: string;
}

export interface AcceptanceCriteriaRead {
  id: string;
  user_story_id: string;
  criteria_number: number;
  text: string;
}

export interface DevOpsWorkItem {
  id: string;
  title: string;
  work_item_type: string;
  description?: string;
  acceptance_criteria?: string;
  state?: string;
  assigned_to?: string;
  area_path?: string;
  iteration_path?: string;
  tags?: string[];
}

export interface AcceptanceCriteriaItem {
  id: string;
  work_item_id: string;
  user_story_title: string;
  criteria_number: number;
  text: string;
}

export interface TestCase {
  id: string;
  requirement_ref: string;
  user_story?: string;
  azure_work_item_id?: string;
  azure_test_case_id?: number;
  sync_status?: 'Not Synced' | 'Synced' | 'Updated' | 'Sync Failed' | string;
  sync_message?: string;
  acceptance_criteria?: string;
  application_page?: string;
  application_link?: string;
  category: 'Positive' | 'Negative' | 'Edge' | string;
  priority: 'High' | 'Medium' | 'Low' | string;
  scenario: string;
  description: string;
  preconditions: string;
  test_data: string;
  test_steps: string[];
  expected_result: string;
}

export interface TestCaseGenerationRequest {
  application_id: number;
  requirement_source: 'USER_STORY' | 'ACCEPTANCE_CRITERIA';
  requirement_identifiers: string[];
  requirement_identifier?: string;
  user_story_ids?: string[];
  custom_requirement_text?: string;
  application_links?: ApplicationLinkPayload[];
  application_url?: string;
  area_ids?: number[];
  area_id?: number;
  services?: string[];
  service?: string;
}

export interface CoverageSummary {
  total_count: number;
  positive_count: number;
  negative_count: number;
  edge_count: number;
  user_stories_count?: number;
  acceptance_criteria_count?: number;
  application_pages_count?: number;
  application_links_analyzed?: string[];
  requirements_covered: string[];
  coverage_quality: string;
}

export interface TestCaseGenerationResponse {
  positive_test_cases: TestCase[];
  negative_test_cases: TestCase[];
  edge_test_cases: TestCase[];
  coverage_summary: CoverageSummary;
  analysis_summary: string;
  url_context_analyzed: boolean;
  url_analysis_message?: string;
}

// Azure DevOps Real Integration Types
export interface AzureDevOpsProjectItem {
  id: string;
  name: string;
  description?: string;
  state?: string;
}

export interface AzureDevOpsConnectRequest {
  organization?: string;
  project?: string;
  pat?: string;
}

export interface AzureDevOpsConnectResponse {
  connected: boolean;
  organization: string;
  project?: string;
  message: string;
  projects: AzureDevOpsProjectItem[];
  mode?: 'mock' | 'real' | string;
}

export interface AzureDevOpsConfigResponse {
  organization: string;
  project: string;
  is_pat_configured: boolean;
  connected: boolean;
  mode?: 'mock' | 'real' | string;
}

export interface AzureDevOpsAreaItem {
  id: number;
  name: string;
  path: string;
  has_children?: boolean;
  children?: AzureDevOpsAreaItem[];
  parent_id?: number | null;
}

export interface AzureDevOpsSyncRequest {
  test_cases: TestCase[] | any[];
  work_item_id?: string;
  area_path?: string;
  project?: string;
}

export interface AzureDevOpsSyncResponse {
  success: boolean;
  message: string;
  synced_count: number;
  updated_count: number;
  failed_count: number;
  test_cases: TestCase[];
}
