from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
import pandas as pd
import numpy as np
import uvicorn

app = FastAPI(title="Integrated Project Economics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this to your WordPress domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

  if fund_mode == "Debt":    #----------------------------------------------------DEBT----------------------------------
    for i in range(project_life):
        if i <= (construction_prd + 1):
            bank_chrg[i] = RR * sum(Yrly_invsmt[:i+1])
        else:
            bank_chrg[i] = RR * sum(Yrly_invsmt[:construction_prd+1])

    
    deprCAPEX = (1-OwnerCost)*sum(Yrly_invsmt[:construction_prd])
    
    cshflw = [0] * project_life  
    dctftr = [0] * project_life  
    #----------------------------------------------------------------------------Green field
    if plant_mode == "Green":
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i]))) / ((1 + IRR) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i])) * ((1 + Infl) ** i)) / ((1 + IRR) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [0] * project_life
      for i in range(project_life):
        Pstark[i] = Pstaro * ((1 + Infl) ** i)
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]

      
      NetRevn = Rstark - Yrly_invsmt

      
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
                  tax_pybl[i] = (NetRevn[i] + depr_asst - deprCAPEX) * (corpTAX[i])
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
                  tax_pybl[i] = NetRevn[i] * (corpTAX[i])

                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + IRR) ** i)
                  dctftr[i] = prodQ[i] / ((1 + IRR) ** i)

                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + IRR) ** i)

      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)




    #----------------------------------------------------------------------------Brown field
    else:
      bank_chrg = [0] * project_life
      Yrly_invsmt[:construction_prd] = [0] * construction_prd
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i]))) / ((1 + IRR) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i])) * ((1 + Infl) ** i)) / ((1 + IRR) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [0] * project_life
      for i in range(project_life):
        Pstark[i] = Pstaro * ((1 + Infl) ** i)
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]

      
      NetRevn = Rstark - Yrly_invsmt

      
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
              tax_pybl[i] = NetRevn[i] * (corpTAX[i])

              cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + IRR) ** i)
              dctftr[i] = prodQ[i] / ((1 + IRR) ** i)

              dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
              cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + IRR) ** i)

      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)




  elif fund_mode == "Equity":   #-----------------------------------------------EQUITY-------------------------------
    bank_chrg = [0] * project_life

    
    deprCAPEX = (1-OwnerCost)*sum(Yrly_invsmt[:construction_prd])
    
    cshflw = [0] * project_life  
    dctftr = [0] * project_life  
    #----------------------------------------------------------------------------Green field
    if plant_mode == "Green":
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i]))) / ((1 + IRR) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i])) * ((1 + Infl) ** i)) / ((1 + IRR) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [0] * project_life
      for i in range(project_life):
        Pstark[i] = Pstaro * ((1 + Infl) ** i)
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]

      
      #NetRevn = Rstark - Yrly_cost
      NetRevn = [r - y for r, y in zip(Rstark, Yrly_cost)]

      
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
                  tax_pybl[i] = (NetRevn[i] + depr_asst - deprCAPEX) * (corpTAX[i])
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
                  tax_pybl[i] = NetRevn[i] * (corpTAX[i])

                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + IRR) ** i)
                  dctftr[i] = prodQ[i] / ((1 + IRR) ** i)

                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + IRR) ** i)

      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)





    #----------------------------------------------------------------------------Brown field
    else:
      bank_chrg = [0] * project_life
      Yrly_invsmt[:construction_prd] = [0] * construction_prd
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i]))) / ((1 + IRR) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + IRR) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i])) * ((1 + Infl) ** i)) / ((1 + IRR) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [0] * project_life
      for i in range(project_life):
        Pstark[i] = Pstaro * ((1 + Infl) ** i)
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]

      
      #NetRevn = Rstark - Yrly_cost
      NetRevn = [r - y for r, y in zip(Rstark, Yrly_cost)]

      
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
              tax_pybl[i] = NetRevn[i] * (corpTAX[i])

              cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + IRR) ** i)
              dctftr[i] = prodQ[i] / ((1 + IRR) ** i)

              dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + IRR) ** i)
              cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + IRR) ** i)

      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)



  else:     #fund_mode is Mixed     ----------------------------------------------MIXED---------------------------------
    for i in range(project_life):
        if i <= (construction_prd + 1):
            bank_chrg[i] = RR * sum(shrDebt * Yrly_invsmt[:i+1])
        else:
            bank_chrg[i] = RR * sum(shrDebt * Yrly_invsmt[:construction_prd+1])

    
    deprCAPEX = (1-OwnerCost)*sum(Yrly_invsmt[:construction_prd])
    
    cshflw = [0] * project_life  
    dctftr = [0] * project_life  
    #----------------------------------------------------------------------------Green field
    if plant_mode == "Green":
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + wacc) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i]))) / ((1 + wacc) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + wacc) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i])) * ((1 + Infl) ** i)) / ((1 + wacc) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [0] * project_life
      for i in range(project_life):
        Pstark[i] = Pstaro * ((1 + Infl) ** i)
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]

      
      NetRevn = Rstark - Yrly_invsmt

      
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
              cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
              dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

              dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
              cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
          else:
              if depr_asst < deprCAPEX and (NetRevn[i] + depr_asst) < deprCAPEX:
                  tax_pybl[i] = 0
                  depr_asst += NetRevn[i]

                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
                  dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
              elif depr_asst < deprCAPEX and (NetRevn[i] + depr_asst) > deprCAPEX:
                  tax_pybl[i] = (NetRevn[i] + depr_asst - deprCAPEX) * (corpTAX[i])
                  depr_asst += (deprCAPEX - depr_asst)

                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + wacc) ** i)
                  dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + wacc) ** i)
              elif depr_asst < deprCAPEX and (NetRevn[i] + depr_asst) == deprCAPEX:
                  tax_pybl[i] = 0
                  depr_asst += NetRevn[i]

                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
                  dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
              else:
                  tax_pybl[i] = NetRevn[i] * (corpTAX[i])

                  cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + wacc) ** i)
                  dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

                  dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
                  cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + wacc) ** i)

      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)




    #----------------------------------------------------------------------------Brown field
    else:
      bank_chrg = [0] * project_life
      Yrly_invsmt[:construction_prd] = [0] * construction_prd
      Yrly_cost = [sum(x) for x in zip(Yrly_invsmt, bank_chrg)]

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + wacc) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i]))) / ((1 + wacc) ** i)
      Pstar = sum(cshflw) / sum(dctftr)
      Rstar = Pstar * prodQ

      for i in range(len(Year)):
        cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) * (1 - (corpTAX[i])) / ((1 + wacc) ** i)
        dctftr[i] = (prodQ[i] * (1 - (corpTAX[i])) * ((1 + Infl) ** i)) / ((1 + wacc) ** i)
      Pstaro = sum(cshflw) / sum(dctftr)
      Pstark = [0] * project_life
      for i in range(project_life):
        Pstark[i] = Pstaro * ((1 + Infl) ** i)
      Rstark = [Pstark[i] * prodQ[i] for i in range(project_life)]

      
      NetRevn = Rstark - Yrly_invsmt

      
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
              cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
              dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

              dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
              cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i]) / ((1 + wacc) ** i)
          else:
              tax_pybl[i] = NetRevn[i] * (corpTAX[i])

              cshflw[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i]) / ((1 + wacc) ** i)
              dctftr[i] = prodQ[i] / ((1 + wacc) ** i)

              dctftr2[i] = prodQ[i] * ((1 + Infl) ** i) / ((1 + wacc) ** i)
              cshflw2[i] = (Yrly_invsmt[i] + bank_chrg[i] + tax_pybl[i] * (1 - credit)) / ((1 + wacc) ** i)

      Ps = sum(cshflw) / sum(dctftr)
      Pso = sum(cshflw) / sum(dctftr2)
      Pc = sum(cshflw2) / sum(dctftr)
      Pco = sum(cshflw2) / sum(dctftr2)


  return Ps, Pso, Pc, Pco, cshflw, cshflw2, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, NetRevn, tax_pybl

#####################################################MICROECONOMIC MODEL ENDS##################################################################################






############################################################MACROECONOMIC MODEL BEGINS############################################################################

def MacroEconomic_Model(multiplier, data, location, plant_mode, fund_mode, opex_mode, carbon_value):
  # This model is based on the multipliers generated in-house using OECD data on national input output tables for various countries


  
  PRIcoef = 0.3
  CONcoef = 0.7

  prodQ, _, _, _, _, _, _ = ChemProcess_Model(data)
  Ps, _, _, _, _, _, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, _, _ = MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value)
  
  pri_invsmt = [0] * project_life
  con_invsmt = [0] * project_life
  bank_invsmt = [0] * project_life

  pri_invsmt[:construction_prd] = [PRIcoef * Yrly_invsmt[i] for i in range(construction_prd)]
  pri_invsmt[construction_prd:] = [data["OPEX"]] * len(pri_invsmt[construction_prd:])   
  con_invsmt[:construction_prd] = [CONcoef * Yrly_invsmt[i] for i in range(construction_prd)]
  bank_invsmt = bank_chrg


  
  output_PRI = multiplier[(multiplier['Country'] == location) &
                          (multiplier['Multiplier Type'] == "Output Multiplier") &
                          (multiplier['Sector'] == (location + "_" + "C20"))]

  pay_PRI = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Compensation (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "C20"))]

  job_PRI = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Employment Elasticity (Jobs per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "C20"))]

  tax_PRI = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Tax Revenue Share (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "C20"))]

  gdp_PRI = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Value-Added Share (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "C20"))]


  
  output_CON = multiplier[(multiplier['Country'] == location) &
                          (multiplier['Multiplier Type'] == "Output Multiplier") &
                          (multiplier['Sector'] == (location + "_" + "F"))]

  pay_CON = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Compensation (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "F"))]

  job_CON = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Employment Elasticity (Jobs per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "F"))]

  tax_CON = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Tax Revenue Share (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "F"))]

  gdp_CON = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Value-Added Share (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "F"))]


  
  output_BAN = multiplier[(multiplier['Country'] == location) &
                          (multiplier['Multiplier Type'] == "Output Multiplier") &
                          (multiplier['Sector'] == (location + "_" + "K"))]

  pay_BAN = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Compensation (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "K"))]

  job_BAN = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Employment Elasticity (Jobs per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "K"))]

  tax_BAN = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Tax Revenue Share (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "K"))]

  gdp_BAN = multiplier[(multiplier['Country'] == location) &
                       (multiplier['Multiplier Type'] == "Value-Added Share (USD per million USD output)") &
                       (multiplier['Sector'] == (location + "_" + "K"))]




  pri_invsmt = pd.Series(pri_invsmt)
  con_invsmt = pd.Series(con_invsmt)
  bank_invsmt = pd.Series(bank_invsmt)

  ####################### GDP Impacts BEGIN #####################
  GDP_dirPRI = gdp_PRI['Direct Impact'].values[0] * pri_invsmt
  GDP_dirCON = gdp_CON['Direct Impact'].values[0] * con_invsmt
  GDP_dirBAN = gdp_BAN['Direct Impact'].values[0] * bank_invsmt

  GDP_indPRI = gdp_PRI['Indirect Impact'].values[0] * pri_invsmt
  GDP_indCON = gdp_CON['Indirect Impact'].values[0] * con_invsmt
  GDP_indBAN = gdp_BAN['Indirect Impact'].values[0] * bank_invsmt

  GDP_totPRI = gdp_PRI['Total Impact'].values[0] * pri_invsmt
  GDP_totCON = gdp_CON['Total Impact'].values[0] * con_invsmt
  GDP_totBAN = gdp_BAN['Total Impact'].values[0] * bank_invsmt

  GDP_dir = GDP_dirPRI + GDP_dirCON + GDP_dirBAN
  GDP_ind = GDP_indPRI + GDP_indCON + GDP_indBAN
  GDP_tot = GDP_totPRI + GDP_totCON + GDP_totBAN

  ####################### GDP Impacts END #######################


  ####################### Job Impacts BEGIN #####################
  JOB_dirPRI = job_PRI['Direct Impact'].values[0] * pri_invsmt
  JOB_dirCON = job_CON['Direct Impact'].values[0] * con_invsmt
  JOB_dirBAN = job_BAN['Direct Impact'].values[0] * bank_invsmt

  JOB_indPRI = job_PRI['Indirect Impact'].values[0] * pri_invsmt
  JOB_indCON = job_CON['Indirect Impact'].values[0] * con_invsmt
  JOB_indBAN = job_BAN['Indirect Impact'].values[0] * bank_invsmt

  JOB_totPRI = job_PRI['Total Impact'].values[0] * pri_invsmt
  JOB_totCON = job_CON['Total Impact'].values[0] * con_invsmt
  JOB_totBAN = job_BAN['Total Impact'].values[0] * bank_invsmt

  JOB_dir = JOB_dirPRI + JOB_dirCON + JOB_dirBAN
  JOB_ind = JOB_indPRI + JOB_indCON + JOB_indBAN
  JOB_tot = JOB_totPRI + JOB_totCON + JOB_totBAN

  ####################### Job Impacts END #######################


  ####################### Wages & Salaries Impacts BEGIN #####################
  PAY_dirPRI = pay_PRI['Direct Impact'].values[0] * pri_invsmt
  PAY_dirCON = pay_CON['Direct Impact'].values[0] * con_invsmt
  PAY_dirBAN = pay_BAN['Direct Impact'].values[0] * bank_invsmt

  PAY_indPRI = pay_PRI['Indirect Impact'].values[0] * pri_invsmt
  PAY_indCON = pay_CON['Indirect Impact'].values[0] * con_invsmt
  PAY_indBAN = pay_BAN['Indirect Impact'].values[0] * bank_invsmt

  PAY_totPRI = pay_PRI['Total Impact'].values[0] * pri_invsmt
  PAY_totCON = pay_CON['Total Impact'].values[0] * con_invsmt
  PAY_totBAN = pay_BAN['Total Impact'].values[0] * bank_invsmt

  PAY_dir = PAY_dirPRI + PAY_dirCON + PAY_dirBAN
  PAY_ind = PAY_indPRI + PAY_indCON + PAY_indBAN
  PAY_tot = PAY_totPRI + PAY_totCON + PAY_totBAN

  ####################### Wages & Salaries Impacts END #######################


  ####################### Taxation Impacts (Potential Tax Revenues) BEGIN ################
  
  TAX_dir = [0] * project_life
  TAX_ind = [0] * project_life
  TAX_tot = [0] * project_life

  for i in range(construction_prd, project_life):
      TAX_dir[i] = tax_PRI['Direct Impact'].values[0] * np.array(Yrly_invsmt[i] + (Ps * prodQ[i]))
      TAX_ind[i] = tax_PRI['Indirect Impact'].values[0] * np.array(Yrly_invsmt[i] + (Ps * prodQ[i]))
      TAX_tot[i] = tax_PRI['Total Impact'].values[0] * np.array(Yrly_invsmt[i] + (Ps * prodQ[i]))


  return GDP_dir, GDP_ind, GDP_tot, JOB_dir, JOB_ind, JOB_tot, PAY_dir, PAY_ind, PAY_tot, TAX_dir, TAX_ind, TAX_tot, GDP_totPRI, JOB_totPRI, PAY_totPRI, GDP_dirPRI, JOB_dirPRI, PAY_dirPRI
  ####################### Taxation Impacts END ##################

############################################################# MACROECONOMIC MODEL ENDS ############################################################





############################################################# ANALYTICS MODEL BEGINS ############################################################

def Analytics_Model(multiplier, project_data, location, product, plant_mode, fund_mode, opex_mode, carbon_value):


  dt = project_data[(project_data['Country'] == location) & (project_data['Main_Prod'] == product)]


  Infl = 0.02  # inflation factor

  tempNUM = 1000000
  results=[]
  for index, data in dt.iterrows():

    prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(data)
    Ps, Pso, Pc, Pco, cshflw, cshflw2, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, NetRevn, tax_pybl = MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value)
    GDP_dir, GDP_ind, GDP_tot, JOB_dir, JOB_ind, JOB_tot, PAY_dir, PAY_ind, PAY_tot, TAX_dir, TAX_ind, TAX_tot, GDP_totPRI, JOB_totPRI, PAY_totPRI, GDP_dirPRI, JOB_dirPRI, PAY_dirPRI = MacroEconomic_Model(multiplier, data, location, plant_mode, fund_mode, opex_mode, carbon_value)

    Yrly_cost = np.array(Yrly_invsmt) + np.array(bank_chrg)

    Ps = [Ps] * project_life
    Pc = [Pc] * project_life
    Psk = [0] * project_life
    Pck = [0] * project_life

    for i in range(project_life):
      Psk[i] = Pso * ((1 + Infl) ** i)
      Pck[i] = Pco * ((1 + Infl) ** i)

    
    Rs = [Ps[i] * prodQ[i] for i in range(project_life)]
    NRs = [Rs[i] - Yrly_cost[i] for i in range(project_life)]

    
    Rsk = Psk * prodQ
    NRsk = Rsk - Yrly_cost

    ccflows = np.cumsum(NRs)
    ccflowsk = np.cumsum(NRsk)

    cost_modes = ["Supply Cost", "Cash Cost"]
    if plant_mode == "Green":
      cost_mode = cost_modes[0]
    else:
      cost_mode = cost_modes[1]


    pri_bothJOB = [0] * project_life
    pri_directJOB = [0] * project_life
    pri_indirectJOB = [0] * project_life

    All_directJOB = [0] * project_life
    All_indirectJOB = [0] * project_life
    All_bothJOB = [0] * project_life

    pri_bothGDP = GDP_totPRI
    pri_directGDP = GDP_dirPRI
    pri_indirectGDP = GDP_totPRI - GDP_dirPRI
    All_bothGDP = GDP_tot
    All_directGDP =  GDP_dir
    All_indirectGDP = GDP_tot - GDP_dir

    pri_bothTAX = TAX_tot
    pri_directTAX = TAX_dir
    pri_indirectTAX = TAX_ind

    pri_bothPAY = PAY_totPRI
    pri_directPAY = PAY_dirPRI
    pri_indirectPAY = PAY_totPRI - PAY_dirPRI
    All_bothPAY = PAY_tot
    All_directPAY = PAY_dir
    All_indirectPAY = PAY_tot - PAY_dir


  
    pri_bothJOB[construction_prd:] = JOB_totPRI[construction_prd:]
    pri_directJOB[construction_prd:] = JOB_dirPRI[construction_prd:]
    pri_indirectJOB[construction_prd:] = JOB_totPRI[construction_prd:]  - JOB_dirPRI[construction_prd:]

    pri_bothJOB[:construction_prd] = JOB_totPRI[:construction_prd]
    pri_directJOB[:construction_prd] = JOB_dirPRI[:construction_prd]
    pri_indirectJOB[:construction_prd] = JOB_totPRI[:construction_prd]  - JOB_dirPRI[:construction_prd]



    All_bothJOB[construction_prd:] = JOB_tot[construction_prd:]
    All_directJOB[construction_prd:] = JOB_dir[construction_prd:]
    All_indirectJOB[construction_prd:] = JOB_tot[construction_prd:]  - JOB_dir[construction_prd:]

    All_bothJOB[:construction_prd] = JOB_tot[:construction_prd]
    All_directJOB[:construction_prd] = JOB_dir[:construction_prd]
    All_indirectJOB[:construction_prd] = JOB_tot[:construction_prd]  - JOB_dir[:construction_prd]



    result = pd.DataFrame({
        'Year': Year,
        'Process Technology': [data['ProcTech']] * project_life,
        'Plant Size': [data['Plant_Size']] * project_life,
        'Plant Efficiency': [data['Plant_Effy']] * project_life,
        'Feedstock Input (TPA)': feedQ,
        'Product Output (TPA)': prodQ,
        'Direct GHG Emissions (TPA)': ghg_dir,
        'Cost Mode': [cost_mode]  * project_life,
        'Real cumCash Flow': ccflows,
        'Nominal cumCash Flow': ccflowsk,
        'Constant$ Breakeven Price': Ps,
        'Current$ Breakeven Price': Psk,
        'Constant$ SC wCredit': Pc,
        'Current$ SC wCredit': Pck,
        'Project Finance': [fund_mode] * project_life,
        'Carbon Valued': [carbon_value] * project_life,
        'Feedstock Price ($/t)': [data['Feed_Price']] * project_life,
        'pri_directGDP': np.array(pri_directGDP)/tempNUM,
        'pri_bothGDP': np.array(pri_bothGDP)/tempNUM,
        'All_directGDP': np.array(All_directGDP)/tempNUM,
        'All_bothGDP': np.array(All_bothGDP)/tempNUM,
        'pri_directPAY': np.array(pri_directPAY)/tempNUM,
        'pri_bothPAY': np.array(pri_bothPAY)/tempNUM,
        'All_directPAY': np.array(All_directPAY)/tempNUM,
        'All_bothPAY': np.array(All_bothPAY)/tempNUM,
        'pri_directJOB': np.array(pri_directJOB)/tempNUM,
        'pri_bothJOB': np.array(pri_bothJOB)/tempNUM,
        'All_directJOB': np.array(All_directJOB)/tempNUM,
        'All_bothJOB': np.array(All_bothJOB)/tempNUM,
        'pri_directTAX': np.array(pri_directTAX)/tempNUM,
        'pri_bothTAX': np.array(pri_bothTAX)/tempNUM
    })
    results.append(result)


  results = pd.concat(results, ignore_index=True)



  return results







########################################################INTEGRATED PROJECT ECONOMICS MODEL######################################################################
# This is a script that integrates and runs all the model functions


'''
The project_data is selected in accordance with two options for each specified attribute as follows:
Pricing formula or cost mode (Supply cost - sc/Cash cost - cc), Plant size (Big/Small), Plant efficiency (High/Low), Project funding (Debt/Equity), Results mode (Constant_$/Inflated_$)
'''


# This is the model run script to run model
'''project_datas = pd.read_csv("./project_data.csv")
multipliers = pd.read_csv("./sectorwise_multipliers.csv")


#Options to select
plant_modes = ["Green", "Brown"]  #to reflect pricing formula for all-in supply cost or just cash cost basis
plant_sizes = ["Large", "Small"]
plant_effys = ["High", "Low"]
fund_modes = ["Debt", "Equity", "Mixed"]  #types of project financing
opex_modes = ["Inflated", "Constant"]
locations = ["USA", "CAN", "SAU", "CHN", "NGA"]
products = ["Methanol", "Ammonia", "Ethylene", "Propylene"]
carbon_values = ["Yes", "No"]

#for i in range(len(products)):
  #results = Analytics_Model(multiplier=multipliers, project_data=project_datas, location=locations[2], product=products[i], plant_mode=plant_modes[0], fund_mode=fund_modes[1], opex_mode=opex_modes[0], carbon_value=carbon_values[1])
results = Analytics_Model(multiplier=multipliers, project_data=project_datas, location="USA", product="Ethylene", plant_mode="Brown", fund_mode="Equity", opex_mode="Inflated", carbon_value="No")
print(results)'''

class AnalyticsInput(BaseModel):
    location: str
    product: str
    plant_mode: str
    fund_mode: str
    opex_mode: str
    carbon_value: str

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
                                    carbon_value=input.carbon_value)
        # Convert DataFrame to JSON-friendly format
        return result_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

