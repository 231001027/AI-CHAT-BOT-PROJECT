/**
 * Persistence for assessments and guided Q&A chat — stored in Supabase.
 */

import { getSupabase } from '@/lib/supabase';

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

export async function saveAssessment(data: AssessmentRow): Promise<string | null> {
  try {
    const { data: row, error } = await getSupabase()
      .from('assessments')
      .insert({
        full_name: data.full_name,
        district: data.district,
        age: data.age,
        gender: data.gender,
        phone: data.phone ?? null,
        audience: data.audience ?? null,
        routed_to: data.routed_to ?? null,
      })
      .select('id')
      .single();

    if (error) throw error;
    return row?.id ?? null;
  } catch (err) {
    console.error('[db] saveAssessment error:', err instanceof Error ? err.message : err);
    return null;
  }
}

export async function createChatSession(data: ChatSessionRow): Promise<string | null> {
  try {
    const { data: row, error } = await getSupabase()
      .from('chat_sessions')
      .insert({
        topic_id: data.topic_id,
        topic_title: data.topic_title,
      })
      .select('id')
      .single();

    if (error) throw error;
    return row?.id ?? null;
  } catch (err) {
    console.error('[db] createChatSession error:', err instanceof Error ? err.message : err);
    return null;
  }
}

export async function saveChatMessage(data: ChatMessageRow): Promise<void> {
  try {
    const { error } = await getSupabase().from('chat_messages').insert({
      session_id: data.session_id,
      role: data.role,
      message: data.message,
      question_index: data.question_index ?? null,
    });
    if (error) throw error;
  } catch (err) {
    console.error('[db] saveChatMessage error:', err instanceof Error ? err.message : err);
  }
}

export async function saveChatMessages(messages: ChatMessageRow[]): Promise<void> {
  if (messages.length === 0) return;
  try {
    const { error } = await getSupabase()
      .from('chat_messages')
      .insert(
        messages.map((m) => ({
          session_id: m.session_id,
          role: m.role,
          message: m.message,
          question_index: m.question_index ?? null,
        })),
      );
    if (error) throw error;
  } catch (err) {
    console.error('[db] saveChatMessages error:', err instanceof Error ? err.message : err);
  }
}
