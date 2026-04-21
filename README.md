# 📱 수거안내 앱 — 무료 온라인 배포 가이드

## 전체 구조

```
민원인 앱 (안드로이드)
     ↕ 인터넷
Render (FastAPI 서버) ← 무료
     ↕
Supabase (DB) ← 무료
     ↕ 웹브라우저로 수정 가능
관리자 (데이터 수정)
```

---

## STEP 1 — Supabase DB 만들기 (5분)

1. https://supabase.com 접속 → **Start your project** → 구글 로그인
2. **New project** 클릭
   - Name: `waste-collection`
   - Database Password: 비밀번호 설정 (저장해두기)
   - Region: **Northeast Asia (Seoul)** 선택
3. 프로젝트 생성 완료 후 왼쪽 메뉴 **SQL Editor** 클릭
4. **New Query** → `backend/supabase_setup.sql` 내용 전체 붙여넣기 → **Run**
5. 왼쪽 메뉴 **Table Editor** → `collection_schedule` 테이블에 데이터 확인

> ⚠️ SQL 실행 시 RLS(보안 정책)와 `updated_at` 자동 트리거도 함께 적용됩니다.
> 별도 설정 없이 `supabase_setup.sql` 한 번 실행으로 모두 완료됩니다.

### API 키 복사
- 왼쪽 메뉴 **Project Settings → API**
- `Project URL` 복사 → 메모장에 저장
- `anon public` 키 복사 → 메모장에 저장

> 🔒 **보안 주의**: `anon key`는 앱 사용자 누구나 볼 수 있는 키입니다.
> `supabase_setup.sql`에 포함된 RLS 정책 덕분에 이 키로는 **읽기만** 가능하고
> 데이터 수정·삭제는 Supabase 대시보드에 로그인한 관리자만 할 수 있습니다.

---

## STEP 2 — GitHub에 코드 올리기 (5분)

1. https://github.com 가입 (무료)
2. **New repository** → 이름: `waste-collection` → Create
3. **`.gitignore` 파일 먼저 생성** (키 유출 방지):

```
# backend/.gitignore
.env
__pycache__/
*.pyc
```

4. 환경변수는 `.env` 파일에 저장 (Git에 올리지 않음):

```
# backend/.env  ← 절대 GitHub에 올리지 마세요
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGci...
```

5. 로컬에서 아래 명령어 실행:

```bash
cd backend
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/내아이디/waste-collection.git
git push -u origin main
```

> ✅ `.env` 파일은 `.gitignore`에 의해 자동으로 제외됩니다.
> GitHub에 키가 올라가면 즉시 Supabase 대시보드에서 키를 재발급하세요.

---

## STEP 3 — Render에 서버 배포 (10분)

1. https://render.com 접속 → 구글 로그인
2. **New → Web Service**
3. GitHub 연결 → `waste-collection` 저장소 선택
4. 설정:
   - **Name**: `waste-collection`
   - **Region**: Singapore (가장 빠름)
   - **Branch**: main
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables** 추가 (`.env` 파일 내용을 여기에 직접 입력):
   - `SUPABASE_URL` = STEP 1에서 복사한 Project URL
   - `SUPABASE_KEY` = STEP 1에서 복사한 anon key
6. **Create Web Service** 클릭 → 배포 완료까지 3~5분 대기
7. 상단에 `https://waste-collection-xxxx.onrender.com` 주소 복사

> ⚠️ **Render 무료 플랜 주의사항**
> - 월 **750시간** 사용 제한 (1개 서비스만 운영 시 충분)
> - **90일간 미사용** 시 서비스 자동 삭제될 수 있음
> - 장기 운영 시 아래 UptimeRobot 설정으로 슬립 및 삭제를 방지하세요

### 배포 확인
브라우저에서 아래 주소 열기:
```
https://waste-collection-xxxx.onrender.com/health
→ {"status":"ok"} 나오면 성공!
```

---

## STEP 4 — 앱에 서버 주소 등록 (2분)

`android-project/app/src/main/assets/www/index.html` 파일 열기

```javascript
// 이 줄을 찾아서
const API_BASE = "https://YOUR-APP-NAME.onrender.com";

// Render 주소로 교체
const API_BASE = "https://waste-collection-xxxx.onrender.com";
```

> 🔒 **보안 참고**: 앱은 Supabase에 직접 접속하지 않고 Render 서버를 통해서만
> 데이터를 가져옵니다. Supabase 키는 서버 환경변수에만 보관되어 APK 내부에
> 노출되지 않습니다.

---

## STEP 5 — APK 빌드 & 배포

1. Android Studio에서 프로젝트 열기
2. `Build → Build APK(s)`
3. `app-debug.apk` 생성 → 카카오톡으로 민원인에게 전송

---

## 데이터 수정 방법 (관리자)

### 방법 A — Supabase 웹 대시보드 (엑셀처럼 편집)
1. https://supabase.com → 프로젝트 → **Table Editor**
2. `collection_schedule` 테이블 클릭
3. 셀 클릭 → 직접 수정 → **Save** 클릭
4. **즉시 반영** (앱 재배포 불필요)
5. `updated_at` 컬럼이 수정 시각으로 **자동 갱신**됨

### 방법 B — SQL로 수정
```sql
-- 기사 교체 (updated_at은 트리거가 자동으로 갱신)
UPDATE collection_schedule
SET driver_name = '새기사이름', phone = '010-0000-0000'
WHERE region = '광주 북구 양산동' AND waste_type = '재활용';

-- 새 지역 추가
INSERT INTO collection_schedule (region, waste_type, collection_day, driver_name, phone)
VALUES ('광주 북구 새동', '재활용', '월, 목', '홍길동', '010-0000-0000');
```

---

## 무료 플랜 한계 & 해결법

| 문제 | 원인 | 해결 |
|------|------|------|
| 첫 요청 30초 느림 | Render 무료 슬립 | UptimeRobot으로 5분마다 핑 (무료) |
| 월 750시간 제한 | Render 무료 플랜 | 서비스 1개 운영 시 문제없음 |
| 90일 미사용 삭제 | Render 무료 정책 | UptimeRobot 설정으로 방지 |
| DB 500MB 제한 | Supabase 무료 | 수거 데이터는 1MB도 안 됨, 문제없음 |

### UptimeRobot 설정 (슬립 방지 + 자동 삭제 방지, 무료)
1. https://uptimerobot.com 가입
2. **Add New Monitor**
   - Type: HTTP(s)
   - URL: `https://waste-collection-xxxx.onrender.com/health`
   - Interval: 5 minutes
3. 저장 → 서버가 항상 켜진 상태 유지

---

## 보안 체크리스트

배포 전 아래 항목을 반드시 확인하세요:

- [ ] `supabase_setup.sql` 실행 완료 (RLS 정책 포함)
- [ ] `.gitignore`에 `.env` 추가 확인
- [ ] GitHub 저장소에 `.env` 파일이 올라가지 않았는지 확인
- [ ] Render 환경변수에 키 입력 완료
- [ ] 앱이 Supabase 직접 접속이 아닌 Render 서버 경유하는지 확인

---

## 최종 흐름 요약

```
① Supabase에서 데이터 수정 (엑셀처럼, 관리자 로그인 필요)
        ↓ 즉시 반영 / updated_at 자동 기록
② 앱 실행 → Render 서버에서 최신 데이터 가져옴
        ↓
③ 민원인 화면에 최신 정보 표시
```
