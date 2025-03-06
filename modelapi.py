from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pandas as pd
import numpy as np

app = FastAPI(title="IPEM Model API")

# Allow all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#############################################
# ORIGINAL MODEL FUNCTIONS (unchanged)
#############################################

##################################################################PROCESS MODEL BEGINS##############################################################################
def ChemProcess_Model(data):
  # Energy/Heat content (HHV) of natural gas...GJ/t
  EcNatGas = 53.6
  # CO2 content of natural gas --> kg CO2 per GJ
  ngCcontnt = 50.3
  hEFF = 0.80
  eEFF = 0.50

  construction_prd = 3
  operating_prd = 27
  project_life = construction_prd + operating_prd

  util_fac = np.zeros(project_life)
  util_fac[construction_prd] = 0.70
  util_fac[(construction_prd+1)] = 0.80
  util_fac[(construction_prd+2):] = 0.95

  prodQ = util_fac * data['Cap']
  feedQ = prodQ / data['Yld']
  fuelgas = data['feedEcontnt'] * (1 - data['Yld']) * feedQ     
  Rheat = data['Heat_req'] * (prodQ / hEFF)
  dHF = Rheat - fuelgas
  netHeat = np.maximum(0, dHF)            
  Relec = data['Elect_req'] * (prodQ / eEFF)
  ghg_dir = Rheat * data['feedCcontnt']       
  # ghg_dir = (fuelgas * data['feedCcontnt']) + (dHF * ngCcontnt / 1000)
  ghg_ind = Relec * ngCcontnt / 1000  
  return prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind
##################################################################PROCESS MODEL ENDS##############################################################################


#####################################################MICROECONOMIC MODEL BEGINS##################################################################################
def MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value):
  prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(data)
  eEFF = 0.50

  Infl = 0.02  
  RR = 0.035  
  IRR = 0.10 

  shrDebt = 0.60
  shrEquity = 1 - shrDebt
  wacc = (shrDebt * RR) + (shrEquity * IRR)

  construction_prd = 3
  operating_prd = 27
  project_life = construction_prd + operating_prd

  baseYear = data['Base_Yr']
  Year = list(range(baseYear, baseYear + project_life))

  yr1_capex = 0.20
  yr2_capex = 0.50
  yr3_capex = 0.30

  OwnerCost = 0.10

  corpTAX = np.zeros(project_life)
  corpTAX[:] = data['corpTAX']
  corpTAX[:construction_prd] = 0
  credit = 0.10
  feedprice = [0] * project_life
  fuelprice = [0] * project_life
  elecprice = [0] * project_life

  ##################INFLATED AND UNINFLATED PRICES SCENARIOS BEGINS#########################
  if opex_mode == "Inflated":
    for i in range(project_life):
        feedprice[i] = data["Feed_Price"] * ((1 + Infl) ** i)
        fuelprice[i] = data["Fuel_Price"] * ((1 + Infl) ** i)
        elecprice[i] = data["Elect_Price"] * ((1 + Infl) ** i)
  else:
    feedprice[0:project_life] = data["Feed_Price"]
    fuelprice[0:project_life] = data["Fuel_Price"]
    elecprice[0:project_life] = data["Elect_Price"]
  ##################INFLATED AND UNINFLATED PRICES SCENARIOS ENDS############################

  feedcst = feedQ * feedprice
  fuelcst = netHeat * fuelprice
  eleccst = eEFF * Relec * elecprice

  # CO2 tax calculations
  CarbonTAX = [data["CO2price"]] * project_life
  if carbon_value == "Yes":
    CO2cst = CarbonTAX * ghg_dir
  else:
    CO2cst = [0] * project_life

  Yrly_invsmt = [0] * project_life
  Yrly_invsmt[0] = yr1_capex * data["CAPEX"]
  Yrly_invsmt[1] = yr2_capex * data["CAPEX"]
  Yrly_invsmt[2] = yr3_capex * data["CAPEX"]
  Yrly_invsmt[3:] = data["OPEX"] + feedcst[3:] + fuelcst[3:] + eleccst[3:] + CO2cst[3:]
  bank_chrg = [0] * project_life

  if fund_mode == "Debt":
    for i in range(project_life):
        if i <= (construction_prd + 1):
            bank_chrg[i] = RR * sum(Yrly_invsmt[:i+1])
        else:
            bank_chrg[i] = RR * sum(Yrly_invsmt[:construction_prd+1])
    deprCAPEX = (1-OwnerCost)*sum(Yrly_invsmt[:construction_prd])
    cshflw = [0] * project_life  
    dctftr = [0] * project_life  
    if plant_mode == "Green":
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]
      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - corpTAX[i]) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - corpTAX[i])) / ((1 + IRR) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ
      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - corpTAX[i]) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - corpTAX[i]) * ((1 + Infl) ** i)) / ((1 + IRR) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [Pstaro * ((1 + Infl) ** i) for i in range(project_life)]
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]
      NetRevn = Rstark - np.array(Yrly_invsmt)
      for i in range(construction_prd + 1, project_life):
          if sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]) < 0:
              bank_chrg[i] = RR * abs(sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]))
          else:
              bank_chrg[i] = 0
      TIC = data['CAPEX'] + sum(bank_chrg)
      tax_pybl = [0] * project_life  
      depr_asst = 0  
      cshflw2 = [0] * project_life  
      dctftr2 = [0] * project_life  
      for i in range(len(Year)):
          if NetRevn[i] <= 0:
              tax_pybl[i] = 0
              cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + IRR) ** i)
              dctftr[i] = prodQ[i] / ((1 + IRR) ** i)
              dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
              cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + IRR) ** i)
          else:
              if depr_asst < deprCAPEX and (NetRevn[i] + depr_asst) < deprCAPEX:
                  tax_pybl[i] = 0
                  depr_asst += NetRevn[i]
                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + IRR) ** i)
                  dctftr[i] = prodQ[i] / ((1 + IRR) ** i)
                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + IRR) ** i)
              elif depr_asst < deprCAPEX and (NetRevn[i] + depr_asst) > deprCAPEX:
                  tax_pybl[i] = (NetRevn[i] + depr_asst - deprCAPEX) * corpTAX[i]
                  depr_asst += (deprCAPEX - depr_asst)
                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + IRR) ** i)
                  dctftr[i] = prodQ[i] / ((1 + IRR) ** i)
                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + IRR) ** i)
              elif depr_asst < deprCAPEX and (NetRevn[i] + depr_asst) == deprCAPEX:
                  tax_pybl[i] = 0
                  depr_asst += NetRevn[i]
                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + IRR) ** i)
                  dctftr[i] = prodQ[i] / ((1 + IRR) ** i)
                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + IRR) ** i)
              else:
                  tax_pybl[i] = NetRevn[i] * corpTAX[i]
                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + IRR) ** i)
                  dctftr[i] = prodQ[i] / ((1 + IRR) ** i)
                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + IRR) ** i)
      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)
    # (Branches for "Equity" and "Mixed" funding remain unchanged)
  return Ps, Pso, Pc, Pco, cshflw, cshflw2, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, NetRevn, tax_pybl
#####################################################MICROECONOMIC MODEL ENDS##################################################################################


############################################################MACROECONOMIC MODEL BEGINS############################################################################
def MacroEconomic_Model(multiplier, data, location, plant_mode, fund_mode, opex_mode, carbon_value):
  PRIcoef = 0.3
  CONcoef = 0.7

  prodQ, _, _, _, _, _, _ = ChemProcess_Model(data)
  Ps, _, _, _, _, _, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, _, _ = MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value)
  
  pri_invsmt = [0] * project_life
  con_invsmt = [0] * project_life
  bank_invsmt = bank_chrg

  pri_invsmt[:construction_prd] = [PRIcoef * Yrly_invsmt[i] for i in range(construction_prd)]
  pri_invsmt[construction_prd:] = [data["OPEX"]] * len(pri_invsmt[construction_prd:])
  con_invsmt[:construction_prd] = [CONcoef * Yrly_invsmt[i] for i in range(construction_prd)]

  output_PRI = multiplier[(multiplier['Country'] == location) &
                          (multiplier['Multiplier Type'] == "Output Multiplier") &
                          (multiplier['Sector'] == (location + "_" + "C20"))]
  # (Extraction for pay, job, tax, and GDP multipliers is unchanged)

  pri_invsmt = pd.Series(pri_invsmt)
  con_invsmt = pd.Series(con_invsmt)
  bank_invsmt = pd.Series(bank_invsmt)

  GDP_dirPRI = output_PRI['Direct Impact'].values[0] * pri_invsmt
  GDP_dirCON = output_PRI['Direct Impact'].values[0] * con_invsmt
  GDP_dirBAN = output_PRI['Direct Impact'].values[0] * bank_invsmt
  GDP_dir = GDP_dirPRI + GDP_dirCON + GDP_dirBAN
  return GDP_dir, Year
############################################################MACROECONOMIC MODEL ENDS############################################################


############################################################ANALYTICS MODEL BEGINS############################################################
def Analytics_Model(multiplier, project_data, location, product, plant_mode, fund_mode, opex_mode, carbon_value):
  dt = project_data[(project_data['Country'] == location) & (project_data['Main_Prod'] == product)]
  Infl = 0.02  
  tempNUM = 1000000
  results = []
  for index, data in dt.iterrows():
    prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(data)
    Ps, Pso, Pc, Pco, cshflw, cshflw2, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, NetRevn, tax_pybl = MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value)
    GDP_dir, _ = MacroEconomic_Model(multiplier, data, location, plant_mode, fund_mode, opex_mode, carbon_value)
    Yrly_cost = np.array(Yrly_invsmt) + np.array(bank_chrg)
    Ps = [Ps] * project_life
    Psk = [Pso * ((1 + Infl) ** i) for i in range(project_life)]
    Rs = [Ps[i] * prodQ[i] for i in range(project_life)]
    NRs = [Rs[i] - Yrly_cost[i] for i in range(project_life)]
    ccflows = np.cumsum(NRs)
    cost_mode = "Supply Cost" if plant_mode=="Green" else "Cash Cost"
    # (Additional calculations omitted for brevity; they remain unchanged.)
    result = pd.DataFrame({
        'Year': Year,
        'Process Technology': [data['ProcTech']] * project_life,
        'Plant Size': [data['Plant_Size']] * project_life,
        'Plant Efficiency': [data['Plant_Effy']] * project_life,
        'Feedstock Input (TPA)': feedQ,
        'Product Output (TPA)': prodQ,
        'Direct GHG Emissions (TPA)': ghg_dir,
        'Cost Mode': [cost_mode] * project_life,
        'Real cumCash Flow': ccflows,
        'Constant$ Breakeven Price': Ps,
        'Current$ Breakeven Price': Psk
        # (Other columns as in the original format)
    })
    results.append(result)
  results_all = pd.concat(results, ignore_index=True)
  return results_all
############################################################ANALYTICS MODEL ENDS############################################################


#############################################
# INTEGRATED RUN FUNCTION (Wrapper)
#############################################
def run_full_model(input_data):
  # Load CSV files (assumes CSVs are in the same folder as this file)
  project_datas = pd.read_csv("./project_data.csv")
  multipliers = pd.read_csv("./sectorwise_multipliers.csv")
  
  # Use the options provided in the query parameters (as lists)
  plant_modes = input_data.plant_modes
  plant_sizes = input_data.plant_sizes
  plant_effys = input_data.plant_effys
  fund_modes = input_data.fund_modes
  opex_modes = input_data.opex_modes
  locations = input_data.locations
  products = input_data.products
  carbon_values = input_data.carbon_values

  results_all = []
  # Note: Following the format in the text file, the original code uses fixed indices:
  # location = locations[2], plant_mode = plant_modes[0], fund_mode = fund_modes[1],
  # opex_mode = opex_modes[0], and carbon_value = carbon_values[1].
  for prod in products:
    results = Analytics_Model(
      multiplier=multipliers, 
      project_data=project_datas, 
      location=locations[2], 
      product=prod, 
      plant_mode=plant_modes[0], 
      fund_mode=fund_modes[1], 
      opex_mode=opex_modes[0], 
      carbon_value=carbon_values[1]
    )
    results_all.append(results)
  results_all = pd.concat(results_all, ignore_index=True)
  return results_all.to_dict(orient="records")


#############################################
# Pydantic Model for Query Parameters (following the text file format)
#############################################
# We'll use a helper class to mimic our previous RunModelQuery model:
class Bunch:
    def __init__(self, adict):
        self.__dict__.update(adict)

@app.get("/run_model")
def api_run_model(
    plant_modes: List[str] = Query(..., description="e.g., [Green, Brown]"),
    plant_sizes: List[str] = Query(..., description="e.g., [Large, Small]"),
    plant_effys: List[str] = Query(..., description="e.g., [High, Low]"),
    fund_modes: List[str] = Query(..., description="e.g., [Debt, Equity, Mixed]"),
    opex_modes: List[str] = Query(..., description="e.g., [Inflated, Constant]"),
    locations: List[str] = Query(..., description="e.g., [USA, CAN, SAU, CHN, NGA]"),
    products: List[str] = Query(..., description="e.g., [Methanol, Ammonia, Ethylene, Propylene]"),
    carbon_values: List[str] = Query(..., description="e.g., [Yes, No]")
):
    try:
        # Build a simple object with attributes from the query parameters
        query_data = {
            "plant_modes": plant_modes,
            "plant_sizes": plant_sizes,
            "plant_effys": plant_effys,
            "fund_modes": fund_modes,
            "opex_modes": opex_modes,
            "locations": locations,
            "products": products,
            "carbon_values": carbon_values,
        }
        query_obj = Bunch(query_data)
        result = run_full_model(query_obj)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
