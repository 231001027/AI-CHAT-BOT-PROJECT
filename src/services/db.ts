/**
 * db.ts — Persistence service (Python FastAPI backend)
 *
 * Keeps the same function signatures used by AssessmentPage / ChatPanel
 * so UI code does not need to know about the transport.
 *
 * Data is stored in SQLite by the FastAPI service (see backend/fastapi).
 */

import {
  createAssessment,
  createChatMessageApi,
  createChatMessagesBulkApi,
  createChatSessionApi,
} from './api';

export interface AssessmentRow {
  full_name: string;
  district: string;
  age: number;
  gender: string;
  phone?: string;
  audience?: string;
  routed_to?: string;
}

export interface ChatSessionRow {
  topic_id: string;
  topic_title: string;
}

export interface ChatMessageRow {
  session_id: string;
  role: 'bot' | 'user';
  message: string;
  question_index?: number;
}

/**
 * Save an assessment form submission.
 * Returns the inserted row id, or null on error.
 */
export async function saveAssessment(data: AssessmentRow): Promise<string | null> {
  try {
    const row = await createAssessment(data);
    return row.id ?? null;
  } catch (err) {
    console.error('[db] saveAssessment error:', err instanceof Error ? err.message : err);
    return null;
  }
}

/**
 * Create a new chat Q&A session row.
 * Returns the session id, or null on error.
 */
export async function createChatSession(data: ChatSessionRow): Promise<string | null> {
  try {
    const row = await createChatSessionApi(data);
    return row.id ?? null;
  } catch (err) {
    console.error('[db] createChatSession error:', err instanceof Error ? err.message : err);
    return null;
  }
}

/**
 * Append a single message to an existing chat session.
 */
export async function saveChatMessage(data: ChatMessageRow): Promise<void> {
  try {
    await createChatMessageApi(data);
  } catch (err) {
    console.error('[db] saveChatMessage error:', err instanceof Error ? err.message : err);
  }
}

/**
 * Bulk-save multiple messages to a session (used to flush at session end).
 */
export async function saveChatMessages(messages: ChatMessageRow[]): Promise<void> {
  if (messages.length === 0) return;
  try {
    await createChatMessagesBulkApi(messages);
  } catch (err) {
    console.error('[db] saveChatMessages error:', err instanceof Error ? err.message : err);
  }
}
