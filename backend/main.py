from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
from supabase import create_client, Client

app = FastAPI(title="수거안내 API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

class LookupRequest(BaseModel):
    address: str
    waste_type: str

def parse_dong(address: str):
    """주소에서 동 이름만 추출 (구 없어도 됨)"""
    address = address.strip()
    bad = ["서울","부산","대구","인천","대전","울산","세종","수원","창원"]
    for c in bad:
        if c in address:
            return None
    # 동 이름 추출
    dong = re.search(r"([가-힣]+(?:동|가|리))", address)
    if dong:
        return dong.group(1)
    return None

@app.get("/")
def root():
    return {"status": "ok", "message": "수거안내 API v3"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/lookup")
def lookup(req: LookupRequest):
    dong = parse_dong(req.address)
    if not dong:
        raise HTTPException(400, detail="주소를 인식할 수 없습니다. 예: 광주 북구 양산동 123-45")

    waste_type = req.waste_type
    sb = get_supabase()

    # zones 테이블에서 동 이름으로 검색
    res = sb.table("zones") \
            .select("*") \
            .ilike("address_key", f"%{dong}%") \
            .execute()

    if not res.data:
        raise HTTPException(404, detail=f"'{dong}' 수거 정보가 없습니다. 담당 부서(062-000-0000)에 문의해주세요.")

    row = res.data[0]

    # 쓰레기 종류에 따라 수거 요일 선택
    if waste_type == "종량제":
        day = row.get("day_general")
    elif waste_type == "재활용":
        day = row.get("day_recycle")
    elif waste_type == "음식물":
        day = row.get("day_food")
    else:
        day = None

    if not day:
        raise HTTPException(404, detail=f"'{dong}' {waste_type} 수거 정보가 없습니다.")

    return {
        "collection_day": day,
        "driver_name": row.get("driver_name") or "담당자 미배정",
        "phone": row.get("phone") or "062-000-0000",
        "region": row.get("region", dong),
        "waste_type": waste_type,
        "zone_id": row.get("zone_id", ""),
    }

@app.get("/autocomplete")
def autocomplete(q: str = ""):
    if len(q) < 2:
        return {"suggestions": []}
    sb = get_supabase()
    res = sb.table("zones") \
            .select("address_key") \
            .ilike("address_key", f"%{q}%") \
            .execute()
    keys = list({r["address_key"] for r in res.data if r.get("address_key")})
    return {"suggestions": sorted(keys)[:8]}
