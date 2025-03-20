from originalmodel import Analytics_Model
import pandas as pd
from fastapi import FastAPI, HTTPException
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
        # Convert DataFrame to JSON-friendly format
        return result_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#project_datas = pd.read_csv("project_data.csv")
#multipliers = pd.read_csv("sectorwise_multipliers.csv")
#check = Analytics_Model(multiplier=multipliers, project_data=project_datas, location="CAN", product="Ethylene", plant_effys="High", plant_size="Large", plant_mode="Brown", fund_mode="Equity", opex_mode="Inflated", carbon_value="No")
#print(check)

