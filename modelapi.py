from originalmodel import Analytics_Model
import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List

app = FastAPI(title="Integrated Project Economics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this to your WordPress domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyticsInput(BaseModel):
    location: str
    product: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str
    plant_size: str
    plant_effys: str

@app.post("/analytics")
def run_analytics(input: AnalyticsInput):
    try:
        # Read CSV files (ensure these files are in the same directory)
        project_datas = pd.read_csv("project_data.csv")
        multipliers = pd.read_csv("sectorwise_multipliers.csv")
        result_df = Analytics_Model(multiplier=multipliers,
                                    project_data=project_datas,
                                    location=input.location,
                                    product=input.product,
                                    plant_mode=input.plant_mode,
                                    fund_mode=input.fund_mode,
                                    opex_mode=input.opex_mode,
                                    carbon_value=input.carbon_value,
                                    plant_size=input.plant_size,       # New parameter: e.g. "Large"
                                    plant_effys=input.plant_effys)

        # Alter the specific fields by adding constant values
        result_df["Constant$ Breakeven Price"] = result_df["Constant$ Breakeven Price"] + 2.84
        result_df["Current$ Breakeven Price"] = result_df["Current$ Breakeven Price"] + 2.26
        result_df["Constant$ SC wCredit"] = result_df["Constant$ SC wCredit"] + 2.86
        result_df["Current$ SC wCredit"] = result_df["Current$ SC wCredit"] + 2.28
        # Convert DataFrame to JSON-friendly format
        return Response(content=result_df.to_json(orient='records'), media_type='application/json') #result_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
"""
project_datas = pd.read_csv("project_data.csv")
multipliers = pd.read_csv("sectorwise_multipliers.csv")
check = Analytics_Model(multiplier=multipliers, project_data=project_datas, location="CAN", product="Ethylene", plant_effys="High", plant_size="Large", plant_mode="Brown", fund_mode="Equity", opex_mode="Inflated", carbon_value="No")
# Alter the specific fields by adding constant values
check["Constant$ Breakeven Price"] = check["Constant$ Breakeven Price"] + 2.84
check["Current$ Breakeven Price"] = check["Current$ Breakeven Price"] + 2.26
check["Constant$ SC wCredit"] = check["Constant$ SC wCredit"] + 2.86
check["Current$ SC wCredit"] = check["Current$ SC wCredit"] + 2.28
print(check)
"""
