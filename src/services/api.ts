/**
 * HearConnect — Frontend API service layer
 *
 * All communication with the Node.js gateway (which proxies to FastAPI)
 * goes through this module. Components never call fetch() directly.
 */

// Vite exposes env vars prefixed with VITE_ at build time.
// Falls back to the local gateway for development.
const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:3000';

// ---------------------------------------------------------------------------
// Shared types (mirror backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface ChatApiRequest {
  message: string;
}

export interface ChatApiResponse {
  response: string;
  followups: string[];
  matched_keywords: string[];
}

export interface HearingProblem {
  id: string;
  title: string;
  accent: 'blue' | 'purple' | 'green';
  symptoms: string[];
  route: string;
}

export interface AdultSection {
  id: string;
  title: string;
  accent: 'blue' | 'purple' | 'green';
  questions: string[];
  tests: string[];
}

export interface SpecialTest {
  code: string;
  name: string;
  description: string;
}

export interface ChildCategory {
  id: string;
  title: string;
  ageRange: string;
  accent: 'blue' | 'purple' | 'green';
  questions: string[];
  tests: string[];
}

// ---------------------------------------------------------------------------
// Internal helper
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body?.error ?? detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

/**
 * Send a user message to the HearConnect AI engine.
 * Returns the bot response, follow-up suggestions, and matched keywords.
 */
export async function sendChatMessage(message: string): Promise<ChatApiResponse> {
  return apiFetch<ChatApiResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message } satisfies ChatApiRequest),
  });
}

// ---------------------------------------------------------------------------
// Domain data  (used by Assessment, Adult Care, Child Care pages)
// ---------------------------------------------------------------------------

export async function fetchHearingProblems(): Promise<HearingProblem[]> {
  return apiFetch<HearingProblem[]>('/api/hearing-problems');
}

export async function fetchAdultSections(): Promise<AdultSection[]> {
  return apiFetch<AdultSection[]>('/api/adult-sections');
}

export async function fetchSpecialTests(): Promise<SpecialTest[]> {
  return apiFetch<SpecialTest[]>('/api/special-tests');
}

export async function fetchChildCategories(): Promise<ChildCategory[]> {
  return apiFetch<ChildCategory[]>('/api/child-categories');
}
