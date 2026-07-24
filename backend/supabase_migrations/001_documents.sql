-- Phase 2: Documents table for pgvector storage

-- Enable the pgvector extension
create extension if not exists vector;

-- Create the documents table
 create table if not exists documents (
   id uuid primary key default gen_random_uuid(),
   content text not null,
   metadata jsonb default '{}'::jsonb,
   embedding vector(1024)
 );

-- Create an HNSW index for accurate similarity search regardless of dataset size
 create index if not exists documents_embedding_idx
   on documents
   using hnsw (embedding vector_cosine_ops);

-- Create the match_documents function used by the backend
 create or replace function match_documents (
   query_embedding vector(1024),
   match_threshold float,
   match_count int
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
   order by documents.embedding <=> query_embedding
   limit match_count;
 $$;
