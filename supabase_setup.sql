create table if not exists public.diary_entries (
  entry_date date primary key,
  mood smallint not null check (mood between 1 and 5),
  mood_name text not null,
  energy smallint not null check (energy between 1 and 5),
  rating smallint not null default 5 check (rating between 1 and 10),
  feelings jsonb not null default '[]'::jsonb,
  note text not null default '',
  gratitude text not null default '',
  need text not null default '',
  reflection text not null default '',
  created_at timestamp with time zone not null,
  updated_at timestamp with time zone not null
);

alter table public.diary_entries enable row level security;
alter table public.diary_entries add column if not exists reflection text not null default '';
alter table public.diary_entries add column if not exists rating smallint not null default 5 check (rating between 1 and 10);

-- Deliberately create no public policies. The app talks to this table only
-- with the server-side secret key stored in Streamlit's encrypted secrets.
revoke all on table public.diary_entries from anon, authenticated;
grant all on table public.diary_entries to service_role;
