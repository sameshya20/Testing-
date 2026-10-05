import type {
  Application,
  DevOpsWorkItem,
  AcceptanceCriteriaItem,
  TestCaseGenerationRequest,
  TestCaseGenerationResponse,
  TestCase,
  User,
  LoginResponse
} from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1';

let authToken: string | null = localStorage.getItem('auth_token');
let sessionExpiredHandler: (() => void) | null = null;

export function setSessionExpiredHandler(handler: () => void) {
  sessionExpiredHandler = handler;
}

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function getAuthToken(): string | null {
  return authToken || localStorage.getItem('auth_token');
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponseStatus(response: Response) {
  if (response.status === 401) {
    setAuthToken(null);
    if (sessionExpiredHandler) {
      sessionExpiredHandler();
    }
    throw new Error('Your session has expired. Please sign in again.');
  }
}

export async function loginUser(email: string, password: string): Promise<LoginResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
  } catch (err) {
    throw new Error('Unable to sign in. Please try again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Invalid email or password.' }));
    throw new Error(errorData.detail || 'Invalid email or password. Please try again.');
  }

  const data: LoginResponse = await response.json();
  setAuthToken(data.access_token);
  return data;
}

export async function fetchCurrentUser(): Promise<User | null> {
  const token = getAuthToken();
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders()
    });
    if (!response.ok) {
      setAuthToken(null);
      return null;
    }
    return await response.json();
  } catch (err) {
    return null;
  }
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
  } catch (err) {
    // Ignore network error during logout
  } finally {
    setAuthToken(null);
  }
}

export async function fetchApplications(): Promise<Application[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/applications`, {
      headers: getAuthHeaders()
    });
  } catch (err) {
    throw new Error('Unable to load applications. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    throw new Error('Unable to load applications. Please try again.');
  }

  return response.json();
}

export async function fetchAreas(): Promise<import('../types').Area[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/devops/areas`, {
      headers: getAuthHeaders()
    });
  } catch (err) {
    throw new Error('Unable to load areas. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    throw new Error('Unable to load areas. Please try again.');
  }

  return response.json();
}

export async function fetchUserStoriesByArea(areaId: number): Promise<import('../types').UserStory[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/devops/areas/${areaId}/user-stories`, {
      headers: getAuthHeaders()
    });
  } catch (err) {
    throw new Error('Unable to load user stories. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    throw new Error('Unable to load user stories. Please try again.');
  }

  return response.json();
}

export async function fetchUserStoriesByAreas(areaIds: number[]): Promise<import('../types').UserStory[]> {
  if (!areaIds || areaIds.length === 0) return [];
  if (areaIds.length === 1) {
    return fetchUserStoriesByArea(areaIds[0]);
  }

  try {
    const query = areaIds.map(id => `area_ids=${id}`).join('&');
    const response = await fetch(`${API_BASE_URL}/devops/areas/multi/user-stories?${query}`, {
      headers: getAuthHeaders()
    });
    await handleResponseStatus(response);
    if (!response.ok) {
      const storyArrays = await Promise.all(areaIds.map(id => fetchUserStoriesByArea(id).catch(() => [])));
      const combined = storyArrays.flat();
      const uniqueMap = new Map<string, import('../types').UserStory>();
      combined.forEach(s => uniqueMap.set(s.id, s));
      return Array.from(uniqueMap.values());
    }
    return response.json();
  } catch (err) {
    const storyArrays = await Promise.all(areaIds.map(id => fetchUserStoriesByArea(id).catch(() => [])));
    const combined = storyArrays.flat();
    const uniqueMap = new Map<string, import('../types').UserStory>();
    combined.forEach(s => uniqueMap.set(s.id, s));
    return Array.from(uniqueMap.values());
  }
}

export async function fetchAcceptanceCriteriaByStory(storyId: string): Promise<import('../types').AcceptanceCriteriaRead[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/devops/user-stories/${encodeURIComponent(storyId)}/acceptance-criteria`, {
      headers: getAuthHeaders()
    });
  } catch (err) {
    throw new Error('Unable to load acceptance criteria. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    throw new Error('Unable to load acceptance criteria. Please try again.');
  }

  return response.json();
}

export async function fetchAcceptanceCriteriaByStories(
  storyIds: string[]
): Promise<import('../types').AcceptanceCriteriaRead[]> {
  if (!storyIds || storyIds.length === 0) return [];
  if (storyIds.length === 1) {
    return fetchAcceptanceCriteriaByStory(storyIds[0]);
  }

  try {
    const query = storyIds.map(id => `story_ids=${encodeURIComponent(id)}`).join('&');
    const response = await fetch(`${API_BASE_URL}/devops/user-stories/multi/acceptance-criteria?${query}`, {
      headers: getAuthHeaders()
    });
    await handleResponseStatus(response);
    if (!response.ok) {
      throw new Error('Unable to load acceptance criteria. Please try again.');
    }
    const data: import('../types').AcceptanceCriteriaRead[] = await response.json();
    const uniqueMap = new Map<string, import('../types').AcceptanceCriteriaRead>();
    data.forEach(c => uniqueMap.set(c.id, c));
    return Array.from(uniqueMap.values());
  } catch (err) {
    // Concurrently fetch each story's criteria
    const criteriaArrays = await Promise.all(
      storyIds.map(id => fetchAcceptanceCriteriaByStory(id).catch(() => []))
    );
    const combined = criteriaArrays.flat();
    const uniqueMap = new Map<string, import('../types').AcceptanceCriteriaRead>();
    combined.forEach(c => uniqueMap.set(c.id, c));
    return Array.from(uniqueMap.values());
  }
}

export async function fetchAcceptanceCriteria(): Promise<AcceptanceCriteriaItem[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/devops/acceptance-criteria`, {
      headers: getAuthHeaders()
    });
  } catch (err) {
    throw new Error('Unable to load acceptance criteria. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    throw new Error('Unable to load acceptance criteria. Please try again.');
  }

  return response.json();
}

export async function searchWorkItems(query: string = ''): Promise<DevOpsWorkItem[]> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/devops/search?q=${encodeURIComponent(query)}`, {
      headers: getAuthHeaders()
    });
  } catch (err) {
    throw new Error('Unable to search items. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    throw new Error('Unable to search items. Please try again.');
  }

  return response.json();
}

export async function generateTestCases(
  payload: TestCaseGenerationRequest
): Promise<TestCaseGenerationResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/generation/create`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
  } catch (err) {
    throw new Error('Unable to generate test cases. Please try again.');
  }

  await handleResponseStatus(response);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unable to generate test cases. Please try again.' }));
    throw new Error(errorData.detail || 'Unable to generate test cases. Please try again.');
  }

  return response.json();
}

import axios from 'axios';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

export interface ExportExcelResult {
  fileName: string;
  size: number;
  blobUrl: string;
  sheets: string[];
}

export interface ParsedSheetData {
  name: string;
  headers: string[];
  rows: (string | number)[][];
}

export interface ParsedWorkbookResult {
  fileName: string;
  size: number;
  sheets: ParsedSheetData[];
  blobUrl: string;
  rawBlob: Blob;
}

/**
 * Validates the raw binary buffer of an XLSX file:
 * 1. Checks buffer size > 0
 * 2. Checks ZIP / OOXML magic bytes: PK\x03\x04 (0x50, 0x4B, 0x03, 0x04)
 * 3. Parses workbook with SheetJS (xlsx)
 * 4. Ensures "Positive", "Negative", "Edge" sheets are all present
 */
export function validateXLSXBinary(arrayBuffer: ArrayBuffer): XLSX.WorkBook {
  if (!arrayBuffer || arrayBuffer.byteLength < 4) {
    throw new Error('Unable to open the Excel file. Please try downloading it again.');
  }

  const bytes = new Uint8Array(arrayBuffer.slice(0, 4));
  const isZip = bytes[0] === 0x50 && bytes[1] === 0x4B && bytes[2] === 0x03 && bytes[3] === 0x04;
  if (!isZip) {
    throw new Error('Unable to open the Excel file. Please try downloading it again.');
  }

  let workbook: XLSX.WorkBook;
  try {
    workbook = XLSX.read(arrayBuffer, { type: 'array' });
  } catch (err: any) {
    throw new Error('Unable to open the Excel file. Please try downloading it again.');
  }

  const sheetNames = workbook.SheetNames || [];
  const requiredSheets = ['Positive', 'Negative', 'Edge'];
  const missingSheets = requiredSheets.filter((s) => !sheetNames.includes(s));
  if (missingSheets.length > 0) {
    throw new Error('Unable to open the Excel file. Please try downloading it again.');
  }

  return workbook;
}

/**
 * Extracts and normalizes the filename from Content-Disposition header.
 * Enforces safe naming and STRICTLY guarantees a .xlsx extension (never .xls).
 */
export function normalizeExcelFilename(dispositionHeader: string | null | undefined, fallbackRef: string): string {
  let fileName = '';
  if (dispositionHeader) {
    const utf8Match = dispositionHeader.match(/filename\*=UTF-8''([^;\s]+)/i);
    if (utf8Match && utf8Match[1]) {
      try { fileName = decodeURIComponent(utf8Match[1]); } catch { fileName = utf8Match[1]; }
    } else {
      const standardMatch = dispositionHeader.match(/filename=["']?([^"';\n]+)["']?/i);
      if (standardMatch && standardMatch[1]) {
        fileName = standardMatch[1].trim();
      }
    }
  }

  if (!fileName) {
    const tokens = (fallbackRef || '').split(/[,;\s]+/).map(s => s.trim().replace(/[^a-zA-Z0-9_\-]/g, '_')).filter(Boolean);
    const refPart = tokens.slice(0, 3).join('_');
    fileName = `Test_Suite_${refPart || 'US-101'}.xlsx`;
  }

  // Step 5 requirement: Never leave .xls or create Test_Suite_US-101_US-001.xls
  let baseName = fileName.replace(/\.(xlsx|xls)$/i, '');
  baseName = baseName.replace(/[^a-zA-Z0-9_\-]/g, '_').replace(/_+/g, '_').replace(/^_+|_+$/g, '');
  if (!baseName) {
    baseName = 'Test_Suite';
  }
  baseName = baseName.substring(0, 60);

  return `${baseName}.xlsx`;
}

/**
 * Core export API call using Axios with responseType: "blob".
 * Strictly keeps binary response as a Blob, never converts to text or JSON.
 */
export async function exportExcelWorkbook(
  positiveCases: TestCase[],
  negativeCases: TestCase[],
  edgeCases: TestCase[],
  appName: string,
  reqRef: string
): Promise<ExportExcelResult> {
  const authHeaders = getAuthHeaders();
  const payload = {
    positive_test_cases: positiveCases,
    negative_test_cases: negativeCases,
    edge_test_cases: edgeCases,
    application_name: appName,
    requirement_ref: reqRef
  };

  let response: any;
  try {
    // Step 4 requirement: Axios POST request with responseType: "blob"
    response = await axios.post(`${API_BASE_URL}/export/excel`, payload, {
      responseType: 'blob',
      headers: {
        ...authHeaders,
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream, */*'
      }
    });
  } catch (err: any) {
    if (err.response?.status === 401) {
      setAuthToken(null);
      if (sessionExpiredHandler) sessionExpiredHandler();
      throw new Error('Your session has expired. Please sign in again.');
    }
    throw new Error('Unable to download the Excel file. Please try again.');
  }

  // Verify response status
  if (response.status !== 200) {
    throw new Error('Unable to download the Excel file. Please try again.');
  }

  // Step 4 requirement: Binary response is preserved as Blob (response.data)
  const blob = response.data;
  if (!blob || blob.size === 0) {
    throw new Error('Unable to download the Excel file. Please try again.');
  }

  // Extract and normalize filename (never .xls)
  const disposition = response.headers?.['content-disposition'] || response.headers?.['Content-Disposition'];
  const finalFileName = normalizeExcelFilename(disposition, reqRef);

  // Read binary as ArrayBuffer for in-browser verification
  const arrayBuffer = await blob.arrayBuffer();

  // Step 10 requirement: DO NOT TRUST THE SUCCESS MESSAGE
  // Only proceed if workbook passes binary signature & sheet validation
  const workbook = validateXLSXBinary(arrayBuffer);

  // Create download blob and File with exact XLSX MIME type and name
  const xlsxBlob = new Blob([arrayBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  });

  const file = new File([arrayBuffer], finalFileName, {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  });

  // Support msSaveOrOpenBlob for legacy Edge/IE
  if ((window.navigator as any)?.msSaveOrOpenBlob) {
    (window.navigator as any).msSaveOrOpenBlob(xlsxBlob, finalFileName);
    return {
      fileName: finalFileName,
      size: xlsxBlob.size,
      blobUrl: '',
      sheets: workbook.SheetNames
    };
  }

  // Save using FileSaver with File and Blob fallback for guaranteed filename
  try {
    saveAs(file, finalFileName);
  } catch {
    saveAs(xlsxBlob, finalFileName);
  }

  return {
    fileName: finalFileName,
    size: xlsxBlob.size,
    blobUrl: '',
    sheets: workbook.SheetNames
  };
}

/**
 * Step 7 requirement: Fetches and parses the real XLSX binary from the backend
 * and extracts worksheet rows & columns using SheetJS for the "View Excel Sheets" feature.
 */
export async function fetchAndParseExcelWorkbook(
  positiveCases: TestCase[],
  negativeCases: TestCase[],
  edgeCases: TestCase[],
  appName: string,
  reqRef: string,
  cachedBlob?: Blob | null
): Promise<ParsedWorkbookResult> {
  let blob = cachedBlob;
  let disposition = '';

  if (!blob) {
    const authHeaders = getAuthHeaders();
    const payload = {
      positive_test_cases: positiveCases,
      negative_test_cases: negativeCases,
      edge_test_cases: edgeCases,
      application_name: appName,
      requirement_ref: reqRef
    };

    let response: any;
    try {
      response = await axios.post(`${API_BASE_URL}/export/excel`, payload, {
        responseType: 'blob',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream, */*'
        }
      });
    } catch (err: any) {
      if (err.response?.status === 401) {
        setAuthToken(null);
        if (sessionExpiredHandler) sessionExpiredHandler();
        throw new Error('Your session has expired. Please sign in again.');
      }
      throw new Error('Unable to load the Excel file. Please try again.');
    }

    if (response.status !== 200) {
      throw new Error('Unable to load the Excel file. Please try again.');
    }

    blob = response.data;
    disposition = response.headers?.['content-disposition'] || response.headers?.['Content-Disposition'] || '';
  }

  if (!blob || blob.size === 0) {
    throw new Error('Unable to load the Excel file. Please try again.');
  }

  const finalFileName = normalizeExcelFilename(disposition, reqRef);
  const arrayBuffer = await blob.arrayBuffer();

  // Validate and parse XLSX workbook binary
  const workbook = validateXLSXBinary(arrayBuffer);

  const sheets: ParsedSheetData[] = [];
  for (const sheetName of ['Positive', 'Negative', 'Edge']) {
    const ws = workbook.Sheets[sheetName];
    if (!ws) continue;

    // Convert sheet to 2D array of rows
    const data: (string | number)[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    const headers = (data[0] || []).map((h) => String(h || ''));
    const rows = data.slice(1);

    sheets.push({
      name: sheetName,
      headers,
      rows
    });
  }

  const xlsxBlob = new Blob([arrayBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  });
  const blobUrl = window.URL.createObjectURL(xlsxBlob);

  return {
    fileName: finalFileName,
    size: xlsxBlob.size,
    sheets,
    blobUrl,
    rawBlob: xlsxBlob
  };
}

