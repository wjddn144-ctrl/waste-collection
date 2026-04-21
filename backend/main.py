from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
from supabase import create_client, Client

app = FastAPI(title="수거안내 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Supabase 연결 ─────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Models ────────────────────────────────────────────────────────
class LookupRequest(BaseModel):
    address: str
    waste_type: str


# ── 주소 파서 ─────────────────────────────────────────────────────
def parse_region(address: str):
    address = address.strip()
    bad = ["서울","부산","대구","인천","대전","울산","세종","수원","창원"]
    for c in bad:
        if c in address:
            return None
    gu = re.search(r"(북구|광산구|서구|남구|동구)", address)
    dong = re.search(r"([가-힣]+동)", address)
    if gu and dong:
        return f"광주 {gu.group(1)} {dong.group(1)}"
    return None


# ── Routes ────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "수거안내 API v2"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/lookup")
def lookup(req: LookupRequest):
    region = parse_region(req.address)
    if not region:
        raise HTTPException(400, detail="주소를 인식할 수 없습니다. 예: 광주 북구 양산동 123-45")

    sb = get_supabase()
    res = sb.table("collection_schedule") \
            .select("*") \
            .eq("region", region) \
            .eq("waste_type", req.waste_type) \
            .execute()

    if not res.data:
        raise HTTPException(404, detail=f"'{region}' {req.waste_type} 수거 정보가 없습니다. 담당 부서(062-000-0000)에 문의해주세요.")

    row = res.data[0]
    return {
        "collection_day": row["collection_day"],
        "driver_name": row["driver_name"],
        "phone": row["phone"],
        "region": region,
        "waste_type": req.waste_type,
    }

@app.get("/autocomplete")
def autocomplete(q: str = ""):
    if len(q) < 2:
        return {"suggestions": []}
    sb = get_supabase()
    res = sb.table("collection_schedule") \
            .select("region") \
            .ilike("region", f"%{q}%") \
            .execute()
    regions = list({r["region"] for r in res.data})
    return {"suggestions": sorted(regions)[:8]}
