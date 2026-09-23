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
def get_dashboard_data(year: str = "2570", t: str = None):
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
            
        sh = client.open_by_key(spreadsheet_id)
        
        # 1. ดึงข้อมูลแผนยุทธศาสตร์
        records = []
        try:
            main_sheet = sh.worksheet(year)
            records = main_sheet.get_all_records()
        except Exception:
            pass # ปล่อยผ่านเป็น list ว่าง
        
        # 2. ค้นหาชีท Dictionary แบบยืดหยุ่น
        policy_dict_records = []
        policy_sheet = None
        for ws in sh.worksheets():
            if ws.title.strip().lower() == "policydictionary":
                policy_sheet = ws
                break
                
        # ดึงข้อมูลจากคอลัมน์ A (No), B (Name), C (Host), D (Relative)
        if policy_sheet:
            try:
                raw_policy = policy_sheet.get_all_values()
                if len(raw_policy) > 1:
                    for row in raw_policy[1:]:
                        if len(row) > 0:
                            p_no = str(row[0]).strip() if len(row) > 0 else ""
                            p_name = str(row[1]).strip() if len(row) > 1 else ""
                            p_host = str(row[2]).strip() if len(row) > 2 else ""
                            p_relative = str(row[3]).strip() if len(row) > 3 else ""
                            
                            if p_no:
                                policy_dict_records.append({
                                    'Policy_No': p_no, 
                                    'Policy_Name': p_name,
                                    'Policy_Host_Name': p_host,
                                    'Policy_Relative_Name': p_relative
                                })
            except Exception as e:
                print(f"Read policy error: {e}")
        
        response_data = {
            "status": "success", 
            "year": year, 
            "data": records, 
            "policy_dict": policy_dict_records
        }
        
        return JSONResponse(
            content=response_data,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})