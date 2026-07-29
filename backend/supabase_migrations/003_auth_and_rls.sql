-- Phase 3: Auth & Row-Level Security (RLS) Multi-Tenancy

-- 1. Ensure user_id column exists on documents table
alter table if exists documents add column if not exists user_id text;

-- Create an index on user_id for faster tenant filtering
create index if not exists documents_user_id_idx on documents (user_id);

-- 2. Enable Row Level Security (RLS)
alter table documents enable row level security;
alter table chat_messages enable row level security;

-- 3. RLS Policies for documents table
drop policy if exists "Users can access their own documents" on documents;
create policy "Users can access their own documents"
  on documents
  for all
  using (
    user_id = auth.uid()::text 
    or (metadata->>'user_id') = auth.uid()::text
    or auth.role() = 'service_role'
    or user_id is null
  );

-- 4. RLS Policies for chat_messages table
drop policy if exists "Users can access their own chat messages" on chat_messages;
create policy "Users can access their own chat messages"
  on chat_messages
  for all
  using (
    user_id = auth.uid()::text 
    or auth.role() = 'service_role'
  );

-- 5. Updated match_documents function with optional user_id scoping
create or replace function match_documents (
  query_embedding vector(1024),
  match_threshold float,
  match_count int,
  p_user_id text default null
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
    and (
      p_user_id is null 
      or user_id = p_user_id 
      or (metadata->>'user_id') = p_user_id
    )
  order by documents.embedding <=> query_embedding
  limit match_count;
$$;
