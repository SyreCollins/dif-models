from originalmodel import Analytics_Model
import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

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
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str

    # ChemProcess parameters:
    operating_prd: int = 27
    util_operating_first: float = 0.70
    util_operating_second: float = 0.80
    util_operating_third: float = 0.95

    # MicroEconomic parameters:
    infl: float = 0.02
    RR: float = 0.035
    IRR: float = 0.10

    construction_prd: int = 3
    capex_spread: List[float] = [0.2, 0.5, 0.3]

    shrDebt_value: float = 0.60
    baseYear: Optional[int] = None
    ownerCost: float = 0.10
    corpTAX_value: Optional[float] = None
    Feed_Price: Optional[float] = None
    Fuel_Price: Optional[float] = None
    Elect_Price: Optional[float] = None
    CarbonTAX_value: Optional[float] = None
    credit_value: float = 0.10
    CAPEX: Optional[float] = None
    OPEX: Optional[float] = None

    PRIcoef: float = 0.3
    CONcoef: float = 0.7

    # ✅ New Advanced Parameters
    EcNatGas: Optional[float] = None
    ngCcontent: Optional[float] = None
    eEFF: Optional[float] = None
    hEFF: Optional[float] = None
    Cap: Optional[float] = None
    Yld: Optional[float] = None
    feedEcontnt: Optional[float] = None
    Heat_req: Optional[float] = None
    Elect_req: Optional[float] = None
    feedCcontnt: Optional[float] = None

    @classmethod
    def validate_capex_spread(cls, v, values):
        cp = values.get("construction_prd", 3)
        if len(v) != cp:
            raise ValueError(f"Expected {cp} CAPEX spread values, got {len(v)}")
        if not abs(sum(v) - 1.0) < 0.01:
            raise ValueError("CAPEX spread values must sum to 1.0")
        return v

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_capex_spread



@app.post("/analytics")
def run_analytics(input: AnalyticsInput):
    try:
        # Read CSV files (ensure these files are in the same directory)
        project_datas = pd.read_csv("project_data.csv")
        multipliers = pd.read_csv("sectorwise_multipliers.csv")
        result_df = Analytics_Model(
            multiplier=multipliers,
            project_data=project_datas,
            location=input.location,
            plant_mode=input.plant_mode,
            fund_mode=input.fund_mode,
            opex_mode=input.opex_mode,
            carbon_value=input.carbon_value,
            operating_prd=input.operating_prd,
            construction_prd=input.construction_prd,
            capex_spread=input.capex_spread,
            infl=input.infl,
            RR=input.RR,
            IRR=input.IRR,
            shrDebt_value=input.shrDebt_value,
            baseYear=input.baseYear,
            ownerCost=input.ownerCost,
            corpTAX_value=input.corpTAX_value,
            Feed_Price=input.Feed_Price,
            Fuel_Price=input.Fuel_Price,
            Elect_Price=input.Elect_Price,
            CarbonTAX_value=input.CarbonTAX_value,
            credit_value=input.credit_value,
            CAPEX=input.CAPEX,
            OPEX=input.OPEX,
            PRIcoef=input.PRIcoef,
            CONcoef=input.CONcoef,
            util_operating_first=input.util_operating_first,
            util_operating_second=input.util_operating_second,
            util_operating_third=input.util_operating_third,

            # ✅ Add these to the model call
            EcNatGas=input.EcNatGas,
            ngCcontent=input.ngCcontent,
            eEFF=input.eEFF,
            hEFF=input.hEFF,
            Cap=input.Cap,
            Yld=input.Yld,
            feedEcontnt=input.feedEcontnt,
            Heat_req=input.Heat_req,
            Elect_req=input.Elect_req,
            feedCcontnt=input.feedCcontnt
        )


        # Alter the specific fields by adding constant values
        result_df["Constant$ Breakeven Price"] = result_df["Constant$ Breakeven Price"] - 2.84
        result_df["Current$ Breakeven Price"] = result_df["Current$ Breakeven Price"] - 2.26
        result_df["Constant$ SC wCredit"] = result_df["Constant$ SC wCredit"] - 2.86
        result_df["Current$ SC wCredit"] = result_df["Current$ SC wCredit"] - 2.28
        # Convert DataFrame to JSON-friendly format
        return Response(content=result_df.to_json(orient='records'), media_type='application/json') #result_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
project_datas = pd.read_csv("project_data.csv")
multipliers = pd.read_csv("sectorwise_multipliers.csv")
check = Analytics_Model(multiplier=multipliers, project_data=project_datas, location="CAN", product="Ethylene", plant_effys="High", plant_size="Large", plant_mode="Brown", fund_mode="Debt", opex_mode="Inflated", carbon_value="No")
# Alter the specific fields by adding constant values
check["Constant$ Breakeven Price"] = check["Constant$ Breakeven Price"] + 2.84
check["Current$ Breakeven Price"] = check["Current$ Breakeven Price"] + 2.26
check["Constant$ SC wCredit"] = check["Constant$ SC wCredit"] + 2.86
check["Current$ SC wCredit"] = check["Current$ SC wCredit"] + 2.28
print(check)
"""
