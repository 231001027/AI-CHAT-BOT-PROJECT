/**
 * db.ts — Supabase database service
 *
 * All writes to Supabase go through this module so the rest of the app
 * never imports supabase directly.
 *
 * Tables required (run in Supabase → SQL Editor):
 *
 *   create table assessments (
 *     id          uuid default gen_random_uuid() primary key,
 *     created_at  timestamptz default now(),
 *     full_name   text not null,
 *     district    text not null,
 *     age         integer not null,
 *     gender      text not null,
 *     phone       text,
 *     audience    text,
 *     routed_to   text
 *   );
 *
 *   create table chat_sessions (
 *     id          uuid default gen_random_uuid() primary key,
 *     created_at  timestamptz default now(),
 *     topic_id    text not null,
 *     topic_title text not null
 *   );
 *
 *   create table chat_messages (
 *     id             uuid default gen_random_uuid() primary key,
 *     session_id     uuid references chat_sessions(id) on delete cascade,
 *     created_at     timestamptz default now(),
 *     role           text not null,
 *     message        text not null,
 *     question_index integer
 *   );
 *
 *   alter table assessments    enable row level security;
 *   alter table chat_sessions  enable row level security;
 *   alter table chat_messages  enable row level security;
 *
 *   create policy "anon insert" on assessments   for insert to anon with check (true);
 *   create policy "anon insert" on chat_sessions for insert to anon with check (true);
 *   create policy "anon insert" on chat_messages for insert to anon with check (true);
 */

import { supabase } from '../lib/supabase';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AssessmentRow {
  full_name: string;
  district:  string;
  age:       number;
  gender:    string;
  phone?:    string;
  audience?: string;   // 'myself' | 'child' | 'someone'
  routed_to?: string;  // 'adult-care' | 'child-care'
}

export interface ChatSessionRow {
  topic_id:    string;
  topic_title: string;
}

export interface ChatMessageRow {
  session_id:     string;
  role:           'bot' | 'user';
  message:        string;
  question_index?: number;
}

// ── Assessment ────────────────────────────────────────────────────────────────

/**
 * Save an assessment form submission.
 * Returns the inserted row id, or null on error.
 */
export async function saveAssessment(data: AssessmentRow): Promise<string | null> {
  const { data: rows, error } = await supabase
    .from('assessments')
    .insert([data])
    .select('id')
    .single();

  if (error) {
    console.error('[db] saveAssessment error:', error.message);
    return null;
  }
  return rows?.id ?? null;
}

// ── Chat session ──────────────────────────────────────────────────────────────

/**
 * Create a new chat Q&A session row.
 * Returns the session id, or null on error.
 */
export async function createChatSession(data: ChatSessionRow): Promise<string | null> {
  const { data: rows, error } = await supabase
    .from('chat_sessions')
    .insert([data])
    .select('id')
    .single();

  if (error) {
    console.error('[db] createChatSession error:', error.message);
    return null;
  }
  return rows?.id ?? null;
}

// ── Chat messages ─────────────────────────────────────────────────────────────

/**
 * Append a single message to an existing chat session.
 */
export async function saveChatMessage(data: ChatMessageRow): Promise<void> {
  const { error } = await supabase
    .from('chat_messages')
    .insert([data]);

  if (error) {
    console.error('[db] saveChatMessage error:', error.message);
  }
}

/**
 * Bulk-save multiple messages to a session (used to flush at session end).
 */
export async function saveChatMessages(messages: ChatMessageRow[]): Promise<void> {
  if (messages.length === 0) return;
  const { error } = await supabase
    .from('chat_messages')
    .insert(messages);

  if (error) {
    console.error('[db] saveChatMessages error:', error.message);
  }
}
