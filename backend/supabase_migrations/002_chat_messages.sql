-- Phase 2: Chat history table for persistent conversational memory

create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  session_id text not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  sources jsonb default '[]'::jsonb,
  created_at timestamp with time zone default now()
);

create index if not exists chat_messages_session_idx
  on chat_messages (user_id, session_id, created_at);
