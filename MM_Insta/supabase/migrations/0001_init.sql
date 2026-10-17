-- 1단계 준비용 스키마 (기획안 §4.2). MVP에서는 아직 적용하지 않는다.
-- 적용: supabase db push 또는 Supabase SQL 편집기에서 실행.

create table if not exists runs (
  id uuid primary key default gen_random_uuid(),
  run_date date not null,
  series text not null,
  topic_id text,
  status text not null check (status in ('생성중', '검수실패', '대기', '발행됨', '중단')),
  error text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  unique (run_date, series)
);

create table if not exists run_steps (
  id bigint generated always as identity primary key,
  run_id uuid not null references runs (id) on delete cascade,
  step text not null,          -- 소재 / 팩트 추출기 / 작가 / G1~G4 / 렌더러 / 퍼블리셔
  status text not null,        -- ok / error / skipped
  duration_ms integer,
  detail jsonb
);

create table if not exists cards (
  run_id uuid not null references runs (id) on delete cascade,
  slide_no smallint not null check (slide_no between 1 and 6),
  image_url text not null,
  width integer not null default 1080,
  height integer not null default 1350,
  script_json jsonb,
  primary key (run_id, slide_no)
);

create table if not exists posts (
  run_id uuid primary key references runs (id) on delete cascade,
  ig_media_id text unique,
  permalink text,
  caption text,
  published_at timestamptz
);

create table if not exists metrics (
  ig_media_id text not null references posts (ig_media_id) on delete cascade,
  fetched_at timestamptz not null default now(),
  reach integer, saved integer, shares integer, comments integer, likes integer,
  primary key (ig_media_id, fetched_at)
);

-- 긴급 정지 스위치 (단일 행)
create table if not exists settings (
  id boolean primary key default true check (id),
  publishing_enabled boolean not null default false,
  publish_time time not null default '21:00',
  retry_limit smallint not null default 3
);
insert into settings (id) values (true) on conflict do nothing;

-- 대시보드는 사내 계정만 (Supabase Auth). 파이프라인은 service_role 키로 RLS를 우회한다.
alter table runs enable row level security;
alter table run_steps enable row level security;
alter table cards enable row level security;
alter table posts enable row level security;
alter table metrics enable row level security;
alter table settings enable row level security;

create policy "staff read runs" on runs for select to authenticated using (true);
create policy "staff read run_steps" on run_steps for select to authenticated using (true);
create policy "staff read cards" on cards for select to authenticated using (true);
create policy "staff read posts" on posts for select to authenticated using (true);
create policy "staff read metrics" on metrics for select to authenticated using (true);
create policy "staff read settings" on settings for select to authenticated using (true);
create policy "staff toggle publishing" on settings for update to authenticated using (true) with check (true);

-- Storage: 공개 버킷 cards/ (경로 YYYY-MM-DD/01.jpg … 06.jpg) — 인스타 Graph API가 공개 URL로 가져감
insert into storage.buckets (id, name, public) values ('cards', 'cards', true) on conflict do nothing;
