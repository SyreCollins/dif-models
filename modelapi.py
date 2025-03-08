from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

# Import your model functions from your original model file.
# Ensure that your original model file is named originalmodel.py.
from originalmodel import Analytics_Model

app = FastAPI(title="IPEM Model API")

# Configure CORS (adjust allowed origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this to your WordPress domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#############################################
# Define a Pydantic model for the input parameters.
#############################################
class RunModelInput(BaseModel):
    plant_mode: str        # e.g., "Green" or "Brown"
    plant_size: str        # e.g., "Large" or "Small" (even if not used by the models, you can keep it for completeness)
    plant_effy: str        # e.g., "High" or "Low"
    fund_mode: str         # e.g., "Debt", "Equity", or "Mixed"
    opex_mode: str         # e.g., "Inflated" or "Constant"
    location: str          # e.g., "USA", "CAN", etc.
    product: str           # e.g., "Methanol", "Ammonia", etc.
    carbon_value: str      # e.g., "Yes" or "No"

#############################################
# Wrapper function to run the full model.
#############################################
def run_full_model(input_data: RunModelInput):
    # Load required CSV files (update the file paths as needed)
    project_datas = pd.read_csv("./project_data.csv")
    multipliers = pd.read_csv("./sectorwise_multipliers.csv")
    
    # Extract the parameters from the input
    plant_mode = input_data.plant_mode
    # plant_size and plant_effy are provided but may not be used by your model;
    # they are here for completeness.
    fund_mode = input_data.fund_mode
    opex_mode = input_data.opex_mode
    location = input_data.location
    product = input_data.product
    carbon_value = input_data.carbon_value

    # Call the Analytics_Model function from your original model code.
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
    
    # Convert the resulting DataFrame to a list of dictionaries (JSON serializable)
    return results.to_dict(orient="records")

#############################################
# API endpoints
#############################################

@app.get("/")
def home():
    return {"info": "Welcome to the IPEM Model API. Use the /run_model endpoint with the required query parameters."}

@app.get("/run_model")
def api_run_model(input_data: RunModelInput = Depends()):
    try:
        result = run_full_model(input_data)
        return {"result": result}
    except Exception as e:
        # Return an HTTP error with the exception message if something goes wrong.
        raise HTTPException(status_code=500, detail=str(e))
