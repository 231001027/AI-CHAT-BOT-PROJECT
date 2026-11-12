/**
 * Typed fetch wrapper for the NIEPMD clinical API.
 * When the FastAPI backend is not hosted (typical Vercel-only deploy), Take Test
 * uses the embedded clinical snapshot in localClinical.ts.
 */
import { localClinical } from '@/lib/localClinical';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || '';

/** True on production builds with no API host — use embedded clinical engine. */
export function useEmbeddedClinical(): boolean {
  return Boolean(import.meta.env.PROD) && !API_BASE;
}

const TOKEN_KEY = 'niepmd_access_token';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
  headers?: Record<string, string>;
  formData?: FormData;
};

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers || {}) };
  const token = getStoredToken();
  if (opts.auth !== false && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let body: BodyInit | undefined;
  if (opts.formData) {
    body = opts.formData;
  } else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.body);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method || (opts.body || opts.formData ? 'POST' : 'GET'),
    headers,
    body,
  });

  if (!res.ok) {
    let errBody: unknown;
    let message = res.statusText;
    try {
      errBody = await res.json();
      if (errBody && typeof errBody === 'object' && 'detail' in errBody) {
        const detail = (errBody as { detail: unknown }).detail;
        message = typeof detail === 'string' ? detail : JSON.stringify(detail);
      }
    } catch {
      try {
        message = await res.text();
      } catch {
        /* ignore */
      }
    }
    throw new ApiError(res.status, message || `Request failed (${res.status})`, errBody);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return (await res.json()) as T;
  return (await res.blob()) as T;
}

export const api = {
  get: <T>(path: string, auth = true) => request<T>(path, { method: 'GET', auth }),
  post: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: 'POST', body, auth }),
  patch: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: 'PATCH', body, auth }),
  put: <T>(path: string, body?: unknown, auth = true) =>
    request<T>(path, { method: 'PUT', body, auth }),
  delete: <T>(path: string, auth = true) => request<T>(path, { method: 'DELETE', auth }),
  upload: <T>(path: string, formData: FormData, auth = true) =>
    request<T>(path, { method: 'POST', formData, auth }),
  downloadUrl: (path: string) => `${API_BASE}${path}`,
};

// ── Domain helpers ──────────────────────────────────────────────────────────

export type FlowType = 'adult' | 'child';
export type UserType = 'myself' | 'my_child' | 'someone_else';
export type ClinicalDepartment = 'audiology' | 'speech_language';

export type Patient = {
  id: string;
  name: string;
  age: number;
  gender: string;
  district: string;
  phone?: string | null;
  user_type: UserType;
  user_code?: string | null;
  date_of_birth?: string | null;
  created_at: string;
  profile?: {
    id: string;
    flow_type: FlowType;
    department?: ClinicalDepartment | null;
    child_subtype?: string | null;
    consent_given: boolean;
    consent_by?: string | null;
    consent_at?: string | null;
  } | null;
};

export type Category = {
  id: string;
  slug: string;
  name: string;
  flow_type: FlowType;
  department?: ClinicalDepartment;
  description: string;
  display_order: number;
};

export type Condition = {
  id: string;
  category_id: string;
  slug: string;
  name: string;
  description: string;
  display_order: number;
};

export type Option = {
  id: string;
  label: string;
  value: string;
  display_order: number;
  next_question_id?: string | null;
  is_terminal: boolean;
};

export type Question = {
  id: string;
  condition_id: string;
  key: string;
  text: string;
  help_text?: string | null;
  display_order: number;
  question_type: string;
  is_entry: boolean;
  options: Option[];
};

export type SessionState = {
  session_id: string;
  patient_id: string;
  condition_id?: string | null;
  category_id?: string | null;
  status: string;
  is_complete: boolean;
  question?: Question | null;
  progress: { answered: number; total: number };
};

export type AnswerOut = {
  question_id: string;
  question_key: string;
  question_text: string;
  answer_value: string;
  answer_label: string;
  answered_at: string;
};

export type SessionSummary = {
  session_id: string;
  patient: Patient;
  category?: Category | null;
  condition?: Condition | null;
  status: string;
  answers: AnswerOut[];
  created_at: string;
  completed_at?: string | null;
};

export type RecommendedTest = {
  test_code: string;
  test_name: string;
  reason_text: string;
  rule_name: string;
  description?: string | null;
  preparation?: string | null;
  duration_minutes?: number | null;
};

export type Recommendation = {
  session_id: string;
  plan_id: string;
  recommended_tests: RecommendedTest[];
  general_recommendations: string[];
  matched_rule_ids: string[];
  generated_at: string;
  disclaimer: string;
};

export type Explanation = {
  test_name: string;
  explanation: string;
  source: string;
  sources: { title: string; excerpt: string; score: number; chunk_index: number }[];
  model?: string | null;
  disclaimer: string;
};

export type Report = {
  id: string;
  patient_id: string;
  session_id: string;
  generated_at: string;
  download_url: string;
  report_json: Record<string, unknown>;
};

export type Doctor = {
  id: string;
  name: string;
  email: string;
  role: string;
  specialization?: string | null;
  phone?: string | null;
  is_active: boolean;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_minutes: number;
  doctor: Doctor;
};

export const patientsApi = {
  register: async (body: Record<string, unknown>) => {
    if (useEmbeddedClinical()) return localClinical.register(body);
    try {
      return await api.post<Patient>('/api/patients', body, false);
    } catch (error) {
      if (error instanceof ApiError && (error.status === 404 || error.status === 405)) {
        return localClinical.register(body);
      }
      throw error;
    }
  },
  update: async (patientId: string, body: Record<string, unknown>) => {
    if (useEmbeddedClinical()) return localClinical.update(patientId, body);
    try {
      return await api.patch<Patient>(`/api/patients/${patientId}`, body, false);
    } catch (error) {
      if (error instanceof ApiError && (error.status === 404 || error.status === 405)) {
        return localClinical.update(patientId, body);
      }
      throw error;
    }
  },
  signup: (body: Record<string, unknown>) =>
    useEmbeddedClinical()
      ? Promise.resolve(localClinical.register(body))
      : api.post<Patient>('/api/patients/signup', body, false),
  login: (body: { user_id: string; password: string }) =>
    api.post<Patient>('/api/patients/login', body, false),
};

export const catalogApi = {
  categories: async (flow_type?: FlowType, department?: ClinicalDepartment) => {
    if (useEmbeddedClinical()) return localClinical.categories(flow_type, department);
    try {
      const params = new URLSearchParams();
      if (flow_type) params.set('flow_type', flow_type);
      if (department) params.set('department', department);
      const qs = params.toString();
      return await api.get<Category[]>(`/api/categories${qs ? `?${qs}` : ''}`, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.categories(flow_type, department);
      }
      throw error;
    }
  },
  conditions: async (categoryId: string) => {
    if (useEmbeddedClinical()) return localClinical.conditions(categoryId);
    try {
      return await api.get<Condition[]>(`/api/conditions?category_id=${categoryId}`, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.conditions(categoryId);
      }
      throw error;
    }
  },
  questions: (conditionId: string) =>
    api.get<Question[]>(`/api/questions?condition_id=${conditionId}`, false),
};

export const sessionsApi = {
  start: async (patient_id: string, condition_id: string) => {
    if (useEmbeddedClinical()) return localClinical.startSession(patient_id, condition_id);
    try {
      return await api.post<SessionState>('/api/sessions', { patient_id, condition_id }, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.startSession(patient_id, condition_id);
      }
      throw error;
    }
  },
  answer: async (sessionId: string, question_id: string, option_id: string) => {
    if (useEmbeddedClinical()) return localClinical.answer(sessionId, question_id, option_id);
    try {
      return await api.post<SessionState>(
        `/api/sessions/${sessionId}/answers`,
        { question_id, option_id },
        false,
      );
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.answer(sessionId, question_id, option_id);
      }
      throw error;
    }
  },
  get: async (sessionId: string) => {
    if (useEmbeddedClinical()) return localClinical.getSession(sessionId);
    try {
      return await api.get<SessionState>(`/api/sessions/${sessionId}`, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.getSession(sessionId);
      }
      throw error;
    }
  },
  summary: async (sessionId: string) => {
    if (useEmbeddedClinical()) return localClinical.summary(sessionId);
    try {
      return await api.get<SessionSummary>(`/api/sessions/${sessionId}/summary`, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.summary(sessionId);
      }
      throw error;
    }
  },
};

export const recommendationsApi = {
  evaluate: async (session_id: string) => {
    if (useEmbeddedClinical()) return localClinical.evaluate(session_id);
    try {
      return await api.post<Recommendation>('/api/recommendations/evaluate', { session_id }, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.evaluate(session_id);
      }
      throw error;
    }
  },
  get: async (sessionId: string) => {
    if (useEmbeddedClinical()) return localClinical.getRecommendation(sessionId);
    try {
      return await api.get<Recommendation>(`/api/recommendations/${sessionId}`, false);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.getRecommendation(sessionId);
      }
      throw error;
    }
  },
};

export const aiApi = {
  explainTest: (body: {
    session_id: string;
    test_code?: string;
    test_name: string;
    question?: string;
  }) => api.post<Explanation>('/api/ai/explain-test', body, false),
};

export const reportsApi = {
  generate: async (session_id: string) => {
    if (useEmbeddedClinical()) return localClinical.generateReport(session_id);
    try {
      return await api.post<Report>(
        '/api/reports/generate',
        { session_id, include_explanations: true },
        false,
      );
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return localClinical.generateReport(session_id);
      }
      throw error;
    }
  },
  downloadUrl: (reportId: string) => api.downloadUrl(`/api/reports/${reportId}/download`),
};

export const authApi = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/api/auth/login', { email, password }, false),
  me: () => api.get<Doctor>('/api/auth/me'),
};

export const adminApi = {
  dashboard: () => api.get<Record<string, unknown>>('/api/admin/dashboard'),
  categories: () => api.get<Category[]>('/api/admin/categories'),
  createCategory: (body: Record<string, unknown>) =>
    api.post<Category>('/api/admin/categories', body),
  conditions: (categoryId?: string) =>
    api.get<Condition[]>(
      `/api/admin/conditions${categoryId ? `?category_id=${categoryId}` : ''}`,
    ),
  createCondition: (body: Record<string, unknown>) =>
    api.post<Condition>('/api/admin/conditions', body),
  questions: (conditionId?: string) =>
    api.get<Question[]>(
      `/api/admin/questions${conditionId ? `?condition_id=${conditionId}` : ''}`,
    ),
  createQuestion: (body: Record<string, unknown>) =>
    api.post<Question>('/api/admin/questions', body),
  rules: () => api.get<Record<string, unknown>[]>('/api/admin/rules'),
  documents: () =>
    api.get<{
      items: Record<string, unknown>[];
      total: number;
      indexing_available?: boolean;
    }>('/api/admin/documents'),
  uploadDocument: (formData: FormData) =>
    api.upload<Record<string, unknown>>('/api/admin/documents/upload', formData),
  aiLogs: () => api.get<Record<string, unknown>[]>('/api/admin/ai-logs'),
  doctors: () => api.get<Doctor[]>('/api/admin/doctors'),
  createDoctor: (body: Record<string, unknown>) =>
    api.post<Doctor>('/api/admin/doctors', body),
  reports: () => api.get<Report[]>('/api/admin/reports'),
};
