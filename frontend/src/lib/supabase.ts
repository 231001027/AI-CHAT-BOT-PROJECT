import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.trim() || '';
const supabaseKey = (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined)?.trim() || '';

let client: SupabaseClient | null = null;

if (supabaseUrl && supabaseKey) {
  client = createClient(supabaseUrl, supabaseKey);
} else {
  console.warn(
    '[supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is missing in frontend/.env',
  );
}

export function getSupabase(): SupabaseClient {
  if (!client) {
    throw new Error('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
  }
  return client;
}

export const supabaseConfigured = Boolean(client);
