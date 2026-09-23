from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = FastAPI()

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
        google_creds_str = os.environ.get("GOOGLE_CREDENTIALS")
        if not google_creds_str:
            return JSONResponse(status_code=500, content={"error": "Missing GOOGLE_CREDENTIALS"})
            
        creds_dict = json.loads(google_creds_str)
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")
        if not spreadsheet_id:
            return JSONResponse(status_code=500, content={"error": "Missing SPREADSHEET_ID"})
        
        # 1. ดึงข้อมูลแผนยุทธศาสตร์ (จากชีท 2570 / 2571)
        sheet = client.open_by_key(spreadsheet_id).worksheet(year)
        records = sheet.get_all_records()
        
        # 2. ดึงข้อมูลพจนานุกรม (อ่านค่าคอลัมน์ A และ B โดยตรง ไม่ต้องพึ่งชื่อหัวตาราง ป้องกันบัคเว้นวรรค)
        policy_dict_records = []
        try:
            policy_sheet = client.open_by_key(spreadsheet_id).worksheet("policyDictionary")
            raw_policy = policy_sheet.get_all_values()
            if len(raw_policy) > 1:
                for row in raw_policy[1:]: # ข้ามบรรทัดที่ 1 (หัวตาราง)
                    p_no = str(row[0]).strip() if len(row) > 0 else ''
                    p_name = str(row[1]).strip() if len(row) > 1 else ''
                    if p_no:
                        policy_dict_records.append({'Policy_No': p_no, 'Policy_Name': p_name})
        except Exception as sheet_err:
            print(f"Policy Dictionary Error: {sheet_err}")
            pass 
        
        return {
            "status": "success", 
            "year": year, 
            "data": records, 
            "policy_dict": policy_dict_records
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})