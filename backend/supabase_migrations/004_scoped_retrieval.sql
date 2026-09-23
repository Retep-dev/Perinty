-- Safe with schemas 001/002 or 001/002/003. No existing rows are modified.
-- Demo identities are NOT authentication; only the server may invoke this RPC.
begin;

alter table public.documents enable row level security;
alter table public.chat_messages enable row level security;
drop policy if exists "Users can access their own documents" on public.documents;
create policy "Users can access their own documents" on public.documents
  for all to authenticated
  using ((metadata->>'user_id') = (select auth.uid())::text)
  with check ((metadata->>'user_id') = (select auth.uid())::text);
drop policy if exists "Users can access their own chat messages" on public.chat_messages;
create policy "Users can access their own chat messages" on public.chat_messages
  for all to authenticated
  using (user_id = (select auth.uid())::text)
  with check (user_id = (select auth.uid())::text);

create index if not exists documents_tenant_model_idx
  on public.documents ((metadata->>'user_id'), (metadata->>'embedding_model'));

create or replace function public.match_documents_scoped(
  query_embedding vector(1024),
  match_threshold float,
  match_count int,
  p_user_id text,
  p_embedding_model text,
  p_dimensions int,
  p_file_name text default null
)
returns table (id uuid, content text, metadata jsonb, similarity float)
language sql stable security invoker
set search_path = public
as $$
  select d.id, d.content, d.metadata,
         1 - (d.embedding <=> query_embedding) as similarity
  from public.documents d
  where p_user_id is not null and length(trim(p_user_id)) > 0
    and d.metadata->>'user_id' = p_user_id
    and d.metadata->>'embedding_model' = p_embedding_model
    and d.metadata->>'embedding_dimensions' = p_dimensions::text
    and (p_file_name is null or d.metadata->>'file_name' = p_file_name)
    and 1 - (d.embedding <=> query_embedding) > match_threshold
  order by d.embedding <=> query_embedding
  limit least(greatest(match_count, 1), 20);
$$;

revoke all on function public.match_documents_scoped(vector, float, int, text, text, int, text) from public, anon, authenticated;
grant execute on function public.match_documents_scoped(vector, float, int, text, text, int, text) to service_role;
notify pgrst, 'reload schema';
commit;
