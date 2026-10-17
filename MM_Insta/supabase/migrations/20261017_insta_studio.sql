-- 메이저맵 인스타 스튜디오 (Supabase 프로젝트: majormap-studio)
-- 하루 1건(월·수·금 입시 / 화·목 트렌드). 생성은 GitHub Actions(service_role), 열람은 웹(publishable key).

create table if not exists public.insta_posts (
  id uuid primary key default gen_random_uuid(),
  post_date date not null unique,
  track text not null check (track in ('admissions', 'trend')),
  status text not null default 'ready' check (status in ('generating', 'ready', 'failed')),
  title text,                                  -- 소재 제목 (내부용)
  headline text,                               -- 1장 헤드라인
  caption text,                                -- 인스타 본문 (출처 포함, 해시태그 제외)
  hashtags text[] not null default '{}',
  image_urls text[] not null default '{}',     -- 01~06.jpg 공개 URL (또는 웹앱 상대경로)
  source_id text,                              -- 노션 페이지/섹션 id — 같은 소재 재사용 방지
  source_url text,
  source_name text,
  topic jsonb,
  facts jsonb,
  script jsonb,
  gate_report jsonb,
  error text,
  mode text not null default 'llm',            -- llm | seed
  version integer not null default 1,
  posted_at timestamptz,                       -- '업로드 완료' 표시
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()   -- 파이프라인이 갱신 시 직접 기록
);

create index if not exists insta_posts_source_id_idx on public.insta_posts (source_id);

alter table public.insta_posts enable row level security;

-- 웹(publishable key)은 읽기만. 인스타에 공개될 콘텐츠라 읽기 공개는 허용한다.
drop policy if exists "insta_posts read" on public.insta_posts;
create policy "insta_posts read" on public.insta_posts for select to anon, authenticated using (true);

-- '업로드 완료' 토글만 허용하는 좁은 RPC (다른 컬럼은 못 바꾼다)
create or replace function public.insta_set_posted(p_id uuid, p_posted boolean)
returns timestamptz
language sql security definer set search_path = '' as $$
  update public.insta_posts
     set posted_at = case when p_posted then now() else null end
   where id = p_id
  returning posted_at;
$$;
revoke all on function public.insta_set_posted(uuid, boolean) from public;
grant execute on function public.insta_set_posted(uuid, boolean) to anon, authenticated;

-- 카드 이미지 공개 버킷 (쓰기는 service_role만)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('insta-cards', 'insta-cards', true, 5242880, array['image/jpeg'])
on conflict (id) do nothing;
