create extension if not exists vector;

create table if not exists legal_documents (
    id bigserial primary key,
    content text not null,
    jurisdiction text not null check (jurisdiction in ('federal', 'punjab', 'sindh', 'kp', 'balochistan')),
    domain text not null,
    source_act text not null,
    section_ref text,
    language text default 'en',
    embedding vector(384) not null,
    created_at timestamptz default now()
);

create index if not exists legal_documents_embedding_idx
    on legal_documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function match_legal_docs (
    query_embedding vector(384),
    match_jurisdictions text[],
    match_domain text default null,
    match_count int default 5
)
returns table (id bigint, content text, source_act text, section_ref text, similarity float)
language sql stable
as $$
    select id, content, source_act, section_ref,
           1 - (embedding <=> query_embedding) as similarity
    from legal_documents
    where jurisdiction = any(match_jurisdictions)
      and (match_domain is null or domain = match_domain)
    order by embedding <=> query_embedding
    limit match_count;
$$;