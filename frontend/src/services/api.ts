/**
 * NIEPMD Audiology — Frontend API service layer
 *
 * All communication with the Node.js gateway (which proxies to FastAPI)
 * goes through this module. Components never call fetch() directly.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

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
  source?: 'rag' | 'rag_extract' | 'keyword';
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

export interface AssessmentPayload {
  full_name: string;
  district: string;
  age: number;
  gender: string;
  phone?: string;
  audience?: string;
  routed_to?: string;
}

export interface AssessmentResponse extends AssessmentPayload {
  id: string;
  created_at: string;
}

export interface ChatSessionPayload {
  topic_id: string;
  topic_title: string;
}

export interface ChatSessionResponse extends ChatSessionPayload {
  id: string;
  created_at: string;
}

export interface ChatMessagePayload {
  session_id: string;
  role: 'bot' | 'user';
  message: string;
  question_index?: number;
}

export interface ContactPayload {
  name: string;
  email: string;
  subject?: string;
  message: string;
}

export interface ContactResponse {
  id: string;
  created_at: string;
  status: string;
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
      if (Array.isArray(detail)) {
        detail = detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join('; ');
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export async function sendChatMessage(message: string): Promise<ChatApiResponse> {
  return apiFetch<ChatApiResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message } satisfies ChatApiRequest),
  });
}

// ---------------------------------------------------------------------------
// Domain data
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

// ---------------------------------------------------------------------------
// Persistence (Python FastAPI + SQLite)
// ---------------------------------------------------------------------------

export async function createAssessment(data: AssessmentPayload): Promise<AssessmentResponse> {
  return apiFetch<AssessmentResponse>('/api/assessments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function createChatSessionApi(data: ChatSessionPayload): Promise<ChatSessionResponse> {
  return apiFetch<ChatSessionResponse>('/api/chat-sessions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function createChatMessageApi(data: ChatMessagePayload): Promise<void> {
  await apiFetch('/api/chat-messages', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function createChatMessagesBulkApi(messages: ChatMessagePayload[]): Promise<void> {
  if (messages.length === 0) return;
  await apiFetch('/api/chat-messages/bulk', {
    method: 'POST',
    body: JSON.stringify({ messages }),
  });
}

export async function submitContactForm(data: ContactPayload): Promise<ContactResponse> {
  return apiFetch<ContactResponse>('/api/contact', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
