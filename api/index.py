from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = FastAPI()

# อนุญาตให้ Frontend เรียกใช้งาน API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
def get_dashboard_data(year: str = "2570"):
    try:
        # 1. โหลด Key จาก Environment Variable ของ Vercel
        google_creds_str = os.environ.get("GOOGLE_CREDENTIALS")
        if not google_creds_str:
            return JSONResponse(status_code=500, content={"error": "Missing GOOGLE_CREDENTIALS"})
            
        creds_dict = json.loads(google_creds_str)
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 2. อ่าน Spreadsheet ID จาก Environment Variable
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")
        if not spreadsheet_id:
            return JSONResponse(status_code=500, content={"error": "Missing SPREADSHEET_ID"})
        
        # 3. เปิดไฟล์และดึงข้อมูลตามปีงบประมาณ (ชื่อ Tab)
        sheet = client.open_by_key(spreadsheet_id).worksheet(year)
        records = sheet.get_all_records() # ดึงข้อมูลทั้งหมดมาเป็น List of Dictionaries
        
        return {"status": "success", "year": year, "data": records}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})