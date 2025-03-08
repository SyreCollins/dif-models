from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Import the model functions from the separate file.
# (Assuming your original file is renamed to models.py and is in the same directory.)
from originalmodel import ChemProcess_Model, MicroEconomic_Model, MacroEconomic_Model, Analytics_Model

app = FastAPI(title="IPEM Model API")

# Configure CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, change this to your WordPress domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#############################################
# Pydantic model for the API input parameters.
#############################################
class RunModelInput(BaseModel):
    plant_mode: str
    plant_size: str
    plant_effy: str
    fund_mode: str
    opex_mode: str
    location: str
    product: str
    carbon_value: str

#############################################
# Integrated run function wrapper.
#############################################
def run_full_model(input_data: RunModelInput):
    # Load required CSV files (update the paths as necessary)
    project_datas = pd.read_csv("./project_data.csv")
    multipliers = pd.read_csv("./sectorwise_multipliers.csv")
    
    # Extract the single-value parameters from the input.
    plant_mode = input_data.plant_mode
    fund_mode = input_data.fund_mode
    opex_mode = input_data.opex_mode
    location = input_data.location
    product = input_data.product
    carbon_value = input_data.carbon_value

    # Call the integrated analytics model function from your original code.
    results = Analytics_Model(
        multiplier=multipliers,
        project_data=project_datas,
        location=location,
        product=product,
        plant_mode=plant_mode,
        fund_mode=fund_mode,
        opex_mode=opex_mode,
        carbon_value=carbon_value
    )
    
    # Return results as a list of dictionaries (JSON-friendly)
    return results.to_dict(orient="records")

#############################################
# API endpoints
#############################################

@app.get("/")
def home():
    return {"info": "Welcome to the IPEM Model API. Use the /run_model endpoint with required parameters."}

@app.get("/run_model")
def api_run_model(input_data: RunModelInput = Depends()):
    try:
        result = run_full_model(input_data)
        return {"result": result}
    except Exception as e:
        # Return an HTTP error with the exception message if something goes wrong.
        raise HTTPException(status_code=500, detail=str(e))
