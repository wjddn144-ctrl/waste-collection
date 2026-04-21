-- ① Supabase SQL Editor에서 이 쿼리를 실행하세요
-- (Supabase 대시보드 → SQL Editor → New Query → 붙여넣기 → Run)

-- 테이블 생성
CREATE TABLE IF NOT EXISTS collection_schedule (
  id            SERIAL PRIMARY KEY,
  region        TEXT NOT NULL,
  waste_type    TEXT NOT NULL CHECK (waste_type IN ('종량제','재활용','음식물')),
  collection_day TEXT NOT NULL,
  driver_name   TEXT NOT NULL,
  phone         TEXT NOT NULL,
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 중복 방지 인덱스
CREATE UNIQUE INDEX IF NOT EXISTS idx_region_waste
  ON collection_schedule(region, waste_type);

-- ② updated_at 자동 갱신 트리거
--    UPDATE 시 updated_at 컬럼이 자동으로 현재 시각으로 갱신됩니다
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_updated_at ON collection_schedule;
CREATE TRIGGER trg_updated_at
  BEFORE UPDATE ON collection_schedule
  FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ③ RLS(Row Level Security) 설정
--    anon key로는 읽기만 가능, 쓰기(수정/삭제/추가)는 로그인한 관리자만 가능
ALTER TABLE collection_schedule ENABLE ROW LEVEL SECURITY;

-- 기존 정책 초기화 (재실행 시 중복 방지)
DROP POLICY IF EXISTS "public read"  ON collection_schedule;
DROP POLICY IF EXISTS "auth write"   ON collection_schedule;

-- 누구나 읽기 가능 (앱 조회용)
CREATE POLICY "public read" ON collection_schedule
  FOR SELECT USING (true);

-- 인증된 관리자만 삽입·수정·삭제 가능
CREATE POLICY "auth write" ON collection_schedule
  FOR ALL USING (auth.role() = 'authenticated');

-- ④ 샘플 데이터 24개 삽입
INSERT INTO collection_schedule (region, waste_type, collection_day, driver_name, phone) VALUES
  ('광주 북구 양산동', '종량제', '화, 금', '김민준', '010-2345-6789'),
  ('광주 북구 양산동', '재활용', '월, 목', '이도윤', '010-1234-5678'),
  ('광주 북구 양산동', '음식물', '수, 토', '박서준', '010-3456-7890'),
  ('광주 북구 운암동', '종량제', '월, 목', '정현우', '010-5678-9012'),
  ('광주 북구 운암동', '재활용', '화, 금', '최지호', '010-4567-8901'),
  ('광주 북구 운암동', '음식물', '수, 토', '강준서', '010-6789-0123'),
  ('광주 북구 동림동', '종량제', '화, 금', '임지훈', '010-8901-2345'),
  ('광주 북구 동림동', '재활용', '수, 토', '윤시우', '010-7890-1234'),
  ('광주 북구 동림동', '음식물', '월, 목', '한도현', '010-9012-3456'),
  ('광주 광산구 수완동', '종량제', '화, 목', '신지훈', '010-1122-3344'),
  ('광주 광산구 수완동', '재활용', '월, 수, 금', '오예준', '010-0123-4567'),
  ('광주 광산구 수완동', '음식물', '월, 수, 금', '류성민', '010-2233-4455'),
  ('광주 광산구 운남동', '종량제', '월, 수', '남도준', '010-4455-6677'),
  ('광주 광산구 운남동', '재활용', '화, 목', '백지성', '010-3344-5566'),
  ('광주 광산구 운남동', '음식물', '화, 금', '전민재', '010-5566-7788'),
  ('광주 서구 농성동',  '종량제', '수, 토', '조성현', '010-7788-9900'),
  ('광주 서구 농성동',  '재활용', '월, 목', '황준혁', '010-6677-8899'),
  ('광주 서구 농성동',  '음식물', '화, 금', '송민호', '010-8899-0011'),
  ('광주 남구 봉선동',  '종량제', '월, 목', '노준영', '010-0011-2233'),
  ('광주 남구 봉선동',  '재활용', '화, 금', '권태양', '010-9900-1122'),
  ('광주 남구 봉선동',  '음식물', '수, 토', '엄기현', '010-1122-3344'),
  ('광주 동구 계림동',  '종량제', '월, 금', '서동현', '010-3344-5566'),
  ('광주 동구 계림동',  '재활용', '수, 토', '문지환', '010-2233-4455'),
  ('광주 동구 계림동',  '음식물', '화, 목', '안성준', '010-4455-6677')
ON CONFLICT (region, waste_type) DO NOTHING;

-- ⑤ 데이터 수정 예시 (나중에 기사 교체 시 이렇게 하면 됩니다)
--    → updated_at은 트리거가 자동으로 현재 시각으로 갱신합니다
-- UPDATE collection_schedule
-- SET driver_name = '새기사이름', phone = '010-0000-0000'
-- WHERE region = '광주 북구 양산동' AND waste_type = '재활용';
