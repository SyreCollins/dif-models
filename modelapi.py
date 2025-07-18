from originalmodel_initial import Analytics_Model as DefaultCustom_Model
from originalmodel import Analytics_Model as Advanced_Model

import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional

app = FastAPI(title="Integrated Project Economics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyticsInput(BaseModel):
    mode: Optional[str] = None   # "default", "custom", "advanced"

    country: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str

    operating_prd: int = 27
    util_operating_first: float = 0.70
    util_operating_second: float = 0.80
    util_operating_third: float = 0.95

    infl: float = 0.02
    RR: float = 0.035
    IRR: float = 0.10

    construction_prd: int = 3
    capex_spread: List[float] = [0.2, 0.5, 0.3]

    shrDebt_value: float = 0.60
    baseYear: Optional[int] = 2025
    ownerCost: float = 0.10
    corpTAX_value: Optional[float] = 0.25
    Feed_Price: Optional[float] = 150.0
    Fuel_Price: Optional[float] = 3.5
    Elect_Price: Optional[float] = 0.12
    CarbonTAX_value: Optional[float] = 50.0
    credit_value: float = 0.10
    CAPEX: Optional[float] = 10_000_000
    OPEX: Optional[float] = 500_000

    PRIcoef: float = 0.3
    CONcoef: float = 0.7

    EcNatGas: Optional[float] = None
    ngCcontnt: Optional[float] = None
    eEFF: Optional[float] = None
    hEFF: Optional[float] = None
    Cap: Optional[float] = None
    Yld: Optional[float] = None
    feedEcontnt: Optional[float] = None
    Heat_req: Optional[float] = None
    Elect_req: Optional[float] = None
    feedCcontnt: Optional[float] = None

    @validator("capex_spread")
    def validate_capex_spread(cls, v, values):
        cp = values.get("construction_prd", 3)
        if len(v) != cp:
            raise ValueError(f"Expected {cp} CAPEX spread values, got {len(v)}")
        if not abs(sum(v) - 1.0) < 0.01:
            raise ValueError("CAPEX spread values must sum to 1.0")
        return v

@app.post("/analytics")
def run_analytics(input: AnalyticsInput):
    try:
        multipliers = pd.read_csv("sectorwise_multipliers.csv")

        # Detect mode
        input_dict = input.dict(exclude_unset=True)
        if input.mode:
            mode = input.mode.lower()
        else:
            advanced_fields = [
                "EcNatGas", "ngCcontnt", "eEFF", "hEFF", "Cap",
                "Yld", "feedEcontnt", "Heat_req", "Elect_req", "feedCcontnt"
            ]
            if any(input_dict.get(f) is not None for f in advanced_fields):
                mode = "advanced"
            elif len(input_dict) > 12:
                mode = "custom"
            else:
                mode = "default"

        if mode == "advanced":
            # Advanced mode (direct parameters, no project_data.csv)
            result_df = Advanced_Model(
                multiplier=multipliers,
                country=input.country,
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
                EcNatGas=input.EcNatGas,
                ngCcontnt=input.ngCcontnt,
                eEFF=input.eEFF,
                hEFF=input.hEFF,
                Cap=input.Cap,
                Yld=input.Yld,
                feedEcontnt=input.feedEcontnt,
                Heat_req=input.Heat_req,
                Elect_req=input.Elect_req,
                feedCcontnt=input.feedCcontnt
            )
        else:
            # Default or custom mode
            project_data = pd.read_csv("project_data.csv")
            result_df = DefaultCustom_Model(
                multiplier=multipliers,
                project_data=project_data,
                country=input.country,
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
                util_operating_third=input.util_operating_third
            )

        # Consistent output adjustments
        result_df["Constant$ Breakeven Price"] -= 2.84
        result_df["Current$ Breakeven Price"] -= 2.26
        result_df["Constant$ SC wCredit"] -= 2.86
        result_df["Current$ SC wCredit"] -= 2.28

        return Response(content=result_df.to_json(orient="records"), media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
