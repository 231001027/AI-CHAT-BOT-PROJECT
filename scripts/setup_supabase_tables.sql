-- ============================================================
-- HearConnect AI — Supabase table setup
-- Run this entire script in: Supabase → SQL Editor → New query
-- ============================================================

-- 1. Assessments table
create table if not exists assessments (
  id          uuid        default gen_random_uuid() primary key,
  created_at  timestamptz default now(),
  full_name   text        not null,
  district    text        not null,
  age         integer     not null,
  gender      text        not null,
  phone       text,
  audience    text,
  routed_to   text
);

-- 2. Chat sessions table
create table if not exists chat_sessions (
  id          uuid        default gen_random_uuid() primary key,
  created_at  timestamptz default now(),
  topic_id    text        not null,
  topic_title text        not null
);

-- 3. Chat messages table
create table if not exists chat_messages (
  id             uuid        default gen_random_uuid() primary key,
  session_id     uuid        references chat_sessions(id) on delete cascade,
  created_at     timestamptz default now(),
  role           text        not null,
  message        text        not null,
  question_index integer
);

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table assessments   enable row level security;
alter table chat_sessions enable row level security;
alter table chat_messages enable row level security;

-- Drop existing policies if any (so script is re-runnable)
drop policy if exists "anon insert assessments"   on assessments;
drop policy if exists "anon insert chat_sessions" on chat_sessions;
drop policy if exists "anon insert chat_messages" on chat_messages;
drop policy if exists "anon select assessments"   on assessments;
drop policy if exists "anon select chat_sessions" on chat_sessions;
drop policy if exists "anon select chat_messages" on chat_messages;

-- Allow anonymous users to INSERT (needed by the frontend without login)
create policy "anon insert assessments"
  on assessments for insert to anon with check (true);

create policy "anon insert chat_sessions"
  on chat_sessions for insert to anon with check (true);

create policy "anon insert chat_messages"
  on chat_messages for insert to anon with check (true);

-- Allow anonymous users to SELECT (needed for the return=representation header)
create policy "anon select assessments"
  on assessments for select to anon using (true);

create policy "anon select chat_sessions"
  on chat_sessions for select to anon using (true);

create policy "anon select chat_messages"
  on chat_messages for select to anon using (true);
