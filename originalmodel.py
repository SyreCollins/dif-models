
import pandas as pd
import numpy as np


##################################################################PROCESS MODEL BEGINS##############################################################################

def ChemProcess_Model(
    EcNatGas=53.6,              # Energy content of natural gas (GJ/t)
    ngCcontnt=50.3,            # CO2 content of natural gas (kg CO2/GJ)
    hEFF=0.80,                  # Efficiency of heat source
    eEFF=0.50,                  # Efficiency of electricity source
    Cap=250000,                 # Plant capacity (TPA)
    Yld=0.95,                   # Process yield
    feedEcontnt=25.0,           # Energy content of feedstock (MJ/kg)
    Heat_req=3200,              # Heat requirement (MJ/t)
    Elect_req=600,              # Electricity requirement (kWh/t)
    feedCcontnt=0.85,           # CO2 content of feedstock (kg CO2/kg)
    construction_prd=3,
    operating_prd=27,
    util_operating_first=0.70,
    util_operating_second=0.80,
    util_operating_third=0.95
):
    """
    Computes core process outputs for economic models without dataset dependency.
    All inputs are now driven directly by payload/user inputs for maximum control.
    """

    project_life = construction_prd + operating_prd

    util_fac = np.zeros(project_life)
    if operating_prd >= 1:
        util_fac[construction_prd] = util_operating_first
    if operating_prd >= 2:
        util_fac[construction_prd + 1] = util_operating_second
    if operating_prd >= 3:
        util_fac[(construction_prd + 2):] = util_operating_third

    # Production quantity (TPA)
    prodQ = util_fac * Cap

    # Feedstock quantity required (TPA)
    feedQ = prodQ / Yld

    # Fuel gas usage (MJ/t)
    fuelgas = feedEcontnt * (1 - Yld) * feedQ

    # Heat requirement (MJ/t)
    Rheat = Heat_req * (prodQ / hEFF)

    # Net heat requirement after accounting for fuel gas
    dHF = Rheat - fuelgas
    netHeat = np.maximum(0, dHF)

    # Electricity requirement (kWh/t)
    Relec = Elect_req * (prodQ / eEFF)

    # Direct GHG emissions from heat
    ghg_dir = Rheat * feedCcontnt

    # Indirect GHG emissions from electricity
    ghg_ind = Relec * ngCcontnt / 1000

    return prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind




#####################################################MICROECONOMIC MODEL BEGINS##################################################################################

def MicroEconomic_Model(plant_mode, fund_mode, opex_mode, carbon_value, Cap, Yld, feedEcontnt, Heat_req, Elect_req, feedCcontnt, EcNatGas=53.6, ngCcontnt=50.3, hEFF=0.80, eEFF=0.50, construction_prd=3, capex_spread=None, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=None, ownerCost=0.10, corpTAX_value=0.25, Feed_Price=None, Fuel_Price=None, Elect_Price=None, CarbonTAX_value=None, credit_value=0.10, CAPEX=None, OPEX=None, operating_prd=27, util_operating_first=0.70, util_operating_second=0.80, util_operating_third=0.95):

  prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(Cap, Yld, feedEcontnt, Heat_req, Elect_req, feedCcontnt, EcNatGas, ngCcontnt, hEFF, eEFF, construction_prd=construction_prd, operating_prd=operating_prd, util_operating_first=util_operating_first, util_operating_second=util_operating_second, util_operating_third=util_operating_third)
  
  eEFF = eEFF 

  Infl = infl  #replace with payload value

  if fund_mode == "Mixed":
    shrDebt = shrDebt_value
  elif fund_mode == 'Debt':
    shrDebt = 1
  else:
    shrDebt = 0 #remove triple quote comment when you set payload value

  #shrDebt = 0.60
  shrEquity = 1 - shrDebt
  wacc = (shrDebt * RR) + (shrEquity * IRR)

  
  construction_prd = construction_prd
  #operating_prd = 27 #replace with payload value
  project_life = construction_prd + operating_prd

  #baseYear = baseYear if baseYear is not None else data['Base_Yr'] #replace with payload value
  Year = list(range(baseYear, baseYear + project_life))


  if capex_spread is None:
    capex_spread = [0.2, 0.5, 0.3]  # fallback for default 3 years

  # Validation: length must match construction_prd
  if len(capex_spread) != construction_prd:
    raise ValueError(f"Expected {construction_prd} CAPEX spread values, got {len(capex_spread)}")

  # Validate it sums to ~1.0
  if not abs(sum(capex_spread) - 1.0) < 0.01:
    raise ValueError("CAPEX spread values must sum to 1.0")

  OwnerCost = ownerCost #0.10 replace with payload value

  
  corpTAX = np.zeros(project_life) #replace with payload value
  if corpTAX_value is not None:
    corpTAX[:] = corpTAX_value
  #else:
    #corpTAX[:] = data['corpTAX']

  
  corpTAX[:construction_prd] = 0

  
  credit = credit_value #0.10

  #Feed_Price = Feed_Price if Feed_Price is not None else data["Feed_Price"]
  #Fuel_Price = Fuel_Price if Fuel_Price is not None else data["Fuel_Price"]
  #Elect_Price = Elect_Price if Elect_Price is not None else data["Elect_Price"]

  ##################INFLATED AND UNINFLATED PRICES SCENARIOS BEGINS#########################
  # Set up price arrays based on opex mode.
  if opex_mode == "Inflated":
    feedprice = [Feed_Price * ((1 + infl) ** i) for i in range(project_life)]
    fuelprice = [Fuel_Price * ((1 + infl) ** i) for i in range(project_life)]
    elecprice = [Elect_Price * ((1 + infl) ** i) for i in range(project_life)]
  else:
    feedprice = [Feed_Price] * project_life
    fuelprice = [Fuel_Price] * project_life
    elecprice = [Elect_Price] * project_life

  ##################INFLATED AND UNINFLATED PRICES SCENARIOS ENDS############################

  feedcst = feedQ * feedprice
  fuelcst = netHeat * fuelprice
  eleccst = eEFF * Relec * elecprice

  # CO2 tax calculations
  #CarbonTAX_value = CarbonTAX_value if CarbonTAX_value is not None else data["CO2price"]
  CarbonTAX = [CarbonTAX_value] * project_life

  if carbon_value == "Yes":
    CO2cst = CarbonTAX * ghg_dir
  else:
    CO2cst = [0] * project_life
  
  # Use CAPEX and OPEX from payload if provided, else use data
  #CAPEX = CAPEX if CAPEX is not None else data["CAPEX"]
  #OPEX = OPEX if OPEX is not None else data["OPEX"]
  
  Yrly_invsmt = [0] * project_life

  for i in range(construction_prd):
    Yrly_invsmt[i] = capex_spread[i] * CAPEX
  
  Yrly_invsmt[construction_prd:] = OPEX + feedcst[construction_prd:] + fuelcst[construction_prd:] + eleccst[construction_prd:] + CO2cst[construction_prd:]


  
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

      NetRevn = np.array(Rstark) - np.array(Yrly_invsmt)

      
      for i in range(construction_prd + 1, project_life):
          if sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]) < 0:
              bank_chrg[i] = RR * abs(sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]))
          else:
              bank_chrg[i] = 0

      
      TIC = CAPEX + sum(bank_chrg)

      
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

      
      NetRevn = np.array(Rstark) - np.array(Yrly_invsmt)

      for i in range(construction_prd + 1, project_life):
          if sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]) < 0:
              bank_chrg[i] = RR * abs(sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]))
          else:
              bank_chrg[i] = 0

      
      TIC = CAPEX + sum(bank_chrg)

      
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

      
      TIC = CAPEX + sum(bank_chrg)

      
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

      
      TIC = CAPEX + sum(bank_chrg)

      
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
            bank_chrg[i] = RR * sum([shrDebt * x for x in Yrly_invsmt[:i+1]]) #bank_chrg[i] = RR * sum(shrDebt * Yrly_invsmt[:i+1])
        else:
            bank_chrg[i] = RR * sum([shrDebt * x for x in Yrly_invsmt[:construction_prd+1]]) #bank_chrg[i] = RR * sum(shrDebt * Yrly_invsmt[:construction_prd+1])

    
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

      
      NetRevn = np.array(Rstark) - np.array(Yrly_invsmt)

      
      for i in range(construction_prd + 1, project_life):
          if sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]) < 0:
              bank_chrg[i] = RR * abs(sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]))
          else:
              bank_chrg[i] = 0

      
      TIC = CAPEX + sum(bank_chrg)

      
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

      
      NetRevn = np.array(Rstark) - np.array(Yrly_invsmt)

      
      for i in range(construction_prd + 1, project_life):
          if sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]) < 0:
              bank_chrg[i] = RR * abs(sum(NetRevn[:i]) - sum(bank_chrg[:i - 1]))
          else:
              bank_chrg[i] = 0

      
      TIC = CAPEX + sum(bank_chrg)

      
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
 # NEW: "C20", "F", "K" passed by user -> sector_code
def MacroEconomic_Model( multiplier, sector_code, plant_mode, fund_mode, opex_mode, carbon_value, construction_prd=3, capex_spread=None, PRIcoef=0.3, CONcoef=0.7, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=2025, ownerCost=0.10, corpTAX_value=0.25, Feed_Price=150.0, Fuel_Price=3.5, Elect_Price=0.12, CarbonTAX_value=50.0, credit_value=0.10, CAPEX=10000000, OPEX=500000, operating_prd=27, util_operating_first=0.70, util_operating_second=0.80, util_operating_third=0.95, EcNatGas=53.6, ngCcontnt=50.3, hEFF=0.80, eEFF=0.50, Cap=250000, Yld=0.95, feedEcontnt=25.0, Heat_req=3200, Elect_req=600, feedCcontnt=0.85):

    # Generate process outputs
    prodQ, _, _, _, _, _, _ = ChemProcess_Model(
        EcNatGas=EcNatGas,
        ngCcontnt=ngCcontnt,
        hEFF=hEFF,
        eEFF=eEFF,
        Cap=Cap,
        Yld=Yld,
        feedEcontnt=feedEcontnt,
        Heat_req=Heat_req,
        Elect_req=Elect_req,
        feedCcontnt=feedCcontnt,
        construction_prd=construction_prd,
        operating_prd=operating_prd,
        util_operating_first=util_operating_first,
        util_operating_second=util_operating_second,
        util_operating_third=util_operating_third
    )

    # Generate economic outputs
    Ps, _, _, _, _, _, Year, project_life, _, Yrly_invsmt, bank_chrg, _, _ = MicroEconomic_Model(
        plant_mode=plant_mode,
        fund_mode=fund_mode,
        opex_mode=opex_mode,
        carbon_value=carbon_value,
        EcNatGas=EcNatGas,
        ngCcontnt=ngCcontnt,
        hEFF=hEFF,
        eEFF=eEFF,
        construction_prd=construction_prd,
        capex_spread=capex_spread,
        infl=infl,
        RR=RR,
        IRR=IRR,
        shrDebt_value=shrDebt_value,
        baseYear=baseYear,
        ownerCost=ownerCost,
        corpTAX_value=corpTAX_value,
        Feed_Price=Feed_Price,
        Fuel_Price=Fuel_Price,
        Elect_Price=Elect_Price,
        CarbonTAX_value=CarbonTAX_value,
        credit_value=credit_value,
        CAPEX=CAPEX,
        OPEX=OPEX,
        operating_prd=operating_prd,
        util_operating_first=util_operating_first,
        util_operating_second=util_operating_second,
        util_operating_third=util_operating_third,
        Cap=Cap,
        Yld=Yld,
        feedEcontnt=feedEcontnt,
        Heat_req=Heat_req,
        Elect_req=Elect_req,
        feedCcontnt=feedCcontnt
    )

    # Investment allocation
    pri_invsmt = [0] * project_life
    con_invsmt = [0] * project_life
    bank_invsmt = [0] * project_life

    pri_invsmt[:construction_prd] = [PRIcoef * Yrly_invsmt[i] for i in range(construction_prd)]
    pri_invsmt[construction_prd:] = [OPEX] * len(pri_invsmt[construction_prd:])
    con_invsmt[:construction_prd] = [CONcoef * Yrly_invsmt[i] for i in range(construction_prd)]
    bank_invsmt = bank_chrg

    pri_invsmt = pd.Series(pri_invsmt)
    con_invsmt = pd.Series(con_invsmt)
    bank_invsmt = pd.Series(bank_invsmt)

    # Fetch multipliers
    def get_multiplier(mult_type):
        entry = multiplier[
            (multiplier['Multiplier Type'] == mult_type) &
            (multiplier['Sector'].str.endswith(sector_code))
        ]
        if entry.empty:
            raise ValueError(f"No multiplier found for type {mult_type} and sector {sector_code}")
        return entry.iloc[0]

    gdp_m = get_multiplier("Value-Added Share (USD per million USD output)")
    job_m = get_multiplier("Employment Elasticity (Jobs per million USD output)")
    pay_m = get_multiplier("Compensation (USD per million USD output)")
    tax_m = get_multiplier("Tax Revenue Share (USD per million USD output)")

    ################ GDP Impact
    GDP_dirPRI = gdp_m['Direct Impact'] * pri_invsmt
    GDP_dirCON = gdp_m['Direct Impact'] * con_invsmt
    GDP_dirBAN = gdp_m['Direct Impact'] * bank_invsmt

    GDP_indPRI = gdp_m['Indirect Impact'] * pri_invsmt
    GDP_indCON = gdp_m['Indirect Impact'] * con_invsmt
    GDP_indBAN = gdp_m['Indirect Impact'] * bank_invsmt

    GDP_totPRI = gdp_m['Total Impact'] * pri_invsmt
    GDP_totCON = gdp_m['Total Impact'] * con_invsmt
    GDP_totBAN = gdp_m['Total Impact'] * bank_invsmt

    GDP_dir = GDP_dirPRI + GDP_dirCON + GDP_dirBAN
    GDP_ind = GDP_indPRI + GDP_indCON + GDP_indBAN
    GDP_tot = GDP_totPRI + GDP_totCON + GDP_totBAN

    ################ JOB Impact
    JOB_dirPRI = job_m['Direct Impact'] * pri_invsmt
    JOB_dirCON = job_m['Direct Impact'] * con_invsmt
    JOB_dirBAN = job_m['Direct Impact'] * bank_invsmt

    JOB_indPRI = job_m['Indirect Impact'] * pri_invsmt
    JOB_indCON = job_m['Indirect Impact'] * con_invsmt
    JOB_indBAN = job_m['Indirect Impact'] * bank_invsmt

    JOB_totPRI = job_m['Total Impact'] * pri_invsmt
    JOB_totCON = job_m['Total Impact'] * con_invsmt
    JOB_totBAN = job_m['Total Impact'] * bank_invsmt

    JOB_dir = JOB_dirPRI + JOB_dirCON + JOB_dirBAN
    JOB_ind = JOB_indPRI + JOB_indCON + JOB_indBAN
    JOB_tot = JOB_totPRI + JOB_totCON + JOB_totBAN

    ################ PAY Impact
    PAY_dirPRI = pay_m['Direct Impact'] * pri_invsmt
    PAY_dirCON = pay_m['Direct Impact'] * con_invsmt
    PAY_dirBAN = pay_m['Direct Impact'] * bank_invsmt

    PAY_indPRI = pay_m['Indirect Impact'] * pri_invsmt
    PAY_indCON = pay_m['Indirect Impact'] * con_invsmt
    PAY_indBAN = pay_m['Indirect Impact'] * bank_invsmt

    PAY_totPRI = pay_m['Total Impact'] * pri_invsmt
    PAY_totCON = pay_m['Total Impact'] * con_invsmt
    PAY_totBAN = pay_m['Total Impact'] * bank_invsmt

    PAY_dir = PAY_dirPRI + PAY_dirCON + PAY_dirBAN
    PAY_ind = PAY_indPRI + PAY_indCON + PAY_indBAN
    PAY_tot = PAY_totPRI + PAY_totCON + PAY_totBAN

    ################ TAX Impact
    TAX_dir = [0] * project_life
    TAX_ind = [0] * project_life
    TAX_tot = [0] * project_life

    for i in range(construction_prd, project_life):
        taxable = Yrly_invsmt[i] + (Ps * prodQ[i])
        TAX_dir[i] = tax_m['Direct Impact'] * taxable
        TAX_ind[i] = tax_m['Indirect Impact'] * taxable
        TAX_tot[i] = tax_m['Total Impact'] * taxable

    return (
        GDP_dir, GDP_ind, GDP_tot,
        JOB_dir, JOB_ind, JOB_tot,
        PAY_dir, PAY_ind, PAY_tot,
        TAX_dir, TAX_ind, TAX_tot,
        GDP_totPRI, JOB_totPRI, PAY_totPRI,
        GDP_dirPRI, JOB_dirPRI, PAY_dirPRI
    )


  ####################### Taxation Impacts END ##################

############################################################# MACROECONOMIC MODEL ENDS ############################################################



############################################################# ANALYTICS MODEL BEGINS ############################################################

def Analytics_Model( multiplier, sector_code, plant_mode, fund_mode, opex_mode, carbon_value, construction_prd=3, capex_spread=None, operating_prd=27, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=2025, ownerCost=0.10, corpTAX_value=0.25, Feed_Price=150.0, Fuel_Price=3.5, Elect_Price=0.12, CarbonTAX_value=50.0, credit_value=0.10, CAPEX=10000000, OPEX=500000, PRIcoef=0.3, CONcoef=0.7, util_operating_first=0.70, util_operating_second=0.80, util_operating_third=0.95, EcNatGas=53.6, ngCcontnt=50.3, hEFF=0.80, eEFF=0.50, Cap=250000, Yld=0.95, feedEcontnt=25.0, Heat_req=3200, Elect_req=600, feedCcontnt=0.85):

    tempNUM = 1_000_000

    prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(
        EcNatGas=EcNatGas,
        ngCcontnt=ngCcontnt,
        hEFF=hEFF,
        eEFF=eEFF,
        Cap=Cap,
        Yld=Yld,
        feedEcontnt=feedEcontnt,
        Heat_req=Heat_req,
        Elect_req=Elect_req,
        feedCcontnt=feedCcontnt,
        construction_prd=construction_prd,
        operating_prd=operating_prd,
        util_operating_first=util_operating_first,
        util_operating_second=util_operating_second,
        util_operating_third=util_operating_third
    )

    Ps, Pso, Pc, Pco, cshflw, cshflw2, Year, project_life, _, Yrly_invsmt, bank_chrg, NetRevn, tax_pybl = MicroEconomic_Model(
        plant_mode=plant_mode,
        fund_mode=fund_mode,
        opex_mode=opex_mode,
        carbon_value=carbon_value,
        EcNatGas=EcNatGas,
        ngCcontnt=ngCcontnt,
        hEFF=hEFF,
        eEFF=eEFF,
        construction_prd=construction_prd,
        capex_spread=capex_spread,
        infl=infl,
        RR=RR,
        IRR=IRR,
        shrDebt_value=shrDebt_value,
        baseYear=baseYear,
        ownerCost=ownerCost,
        corpTAX_value=corpTAX_value,
        Feed_Price=Feed_Price,
        Fuel_Price=Fuel_Price,
        Elect_Price=Elect_Price,
        CarbonTAX_value=CarbonTAX_value,
        credit_value=credit_value,
        CAPEX=CAPEX,
        OPEX=OPEX,
        operating_prd=operating_prd,
        util_operating_first=util_operating_first,
        util_operating_second=util_operating_second,
        util_operating_third=util_operating_third,
        Cap=Cap,
        Yld=Yld,
        feedEcontnt=feedEcontnt,
        Heat_req=Heat_req,
        Elect_req=Elect_req,
        feedCcontnt=feedCcontnt
    )

    GDP_dir, GDP_ind, GDP_tot, JOB_dir, JOB_ind, JOB_tot, PAY_dir, PAY_ind, PAY_tot, TAX_dir, TAX_ind, TAX_tot, GDP_totPRI, JOB_totPRI, PAY_totPRI, GDP_dirPRI, JOB_dirPRI, PAY_dirPRI = MacroEconomic_Model(
        multiplier,
        sector_code=sector_code,
        plant_mode=plant_mode,
        fund_mode=fund_mode,
        opex_mode=opex_mode,
        carbon_value=carbon_value,
        construction_prd=construction_prd,
        capex_spread=capex_spread,
        PRIcoef=PRIcoef,
        CONcoef=CONcoef,
        infl=infl,
        RR=RR,
        IRR=IRR,
        shrDebt_value=shrDebt_value,
        baseYear=baseYear,
        ownerCost=ownerCost,
        corpTAX_value=corpTAX_value,
        Feed_Price=Feed_Price,
        Fuel_Price=Fuel_Price,
        Elect_Price=Elect_Price,
        CarbonTAX_value=CarbonTAX_value,
        credit_value=credit_value,
        CAPEX=CAPEX,
        OPEX=OPEX,
        operating_prd=operating_prd,
        util_operating_first=util_operating_first,
        util_operating_second=util_operating_second,
        util_operating_third=util_operating_third,
        EcNatGas=EcNatGas,
        ngCcontnt=ngCcontnt,
        hEFF=hEFF,
        eEFF=eEFF,
        Cap=Cap,
        Yld=Yld,
        feedEcontnt=feedEcontnt,
        Heat_req=Heat_req,
        Elect_req=Elect_req,
        feedCcontnt=feedCcontnt
    )

    Yrly_cost = np.array(Yrly_invsmt) + np.array(bank_chrg)

    Ps_arr = [Ps] * project_life
    Pc_arr = [Pc] * project_life
    Psk = [Pso * ((1 + infl) ** i) for i in range(project_life)]
    Pck = [Pco * ((1 + infl) ** i) for i in range(project_life)]

    Rs = [Ps_arr[i] * prodQ[i] for i in range(project_life)]
    NRs = [Rs[i] - Yrly_cost[i] for i in range(project_life)]
    Rsk = np.array(Psk) * np.array(prodQ)
    NRsk = Rsk - Yrly_cost

    ccflows = np.cumsum(NRs)
    ccflowsk = np.cumsum(NRsk)

    cost_mode = "Supply Cost" if plant_mode == "Green" else "Cash Cost"

    # JOB, GDP, TAX, PAY allocation
    pri_bothJOB = JOB_totPRI.copy()
    pri_directJOB = JOB_dirPRI.copy()
    pri_indirectJOB = JOB_totPRI - JOB_dirPRI

    All_bothJOB = JOB_tot.copy()
    All_directJOB = JOB_dir.copy()
    All_indirectJOB = JOB_tot - JOB_dir

    pri_bothGDP = GDP_totPRI
    pri_directGDP = GDP_dirPRI
    pri_indirectGDP = GDP_totPRI - GDP_dirPRI

    All_bothGDP = GDP_tot
    All_directGDP = GDP_dir
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

    # Assemble DataFrame
    result = pd.DataFrame({
        'Year': Year,
        'Feedstock Input (TPA)': feedQ,
        'Product Output (TPA)': prodQ,
        'Direct GHG Emissions (TPA)': ghg_dir,
        'Cost Mode': [cost_mode] * project_life,
        'Real cumCash Flow': ccflows,
        'Nominal cumCash Flow': ccflowsk,
        'Constant$ Breakeven Price': Ps_arr,
        'Current$ Breakeven Price': Psk,
        'Constant$ SC wCredit': Pc_arr,
        'Current$ SC wCredit': Pck,
        'Project Finance': [fund_mode] * project_life,
        'Carbon Valued': [carbon_value] * project_life,
        'Feedstock Price ($/t)': [Feed_Price] * project_life,
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

    # Optionally save to CSV
    result.to_csv("model_results.csv", index=False)

    return result



########################################################INTEGRATED PROJECT ECONOMICS MODEL######################################################################
# This is a script that integrates and runs all the model functions


'''
The project_data is selected in accordance with two options for each specified attribute as follows:
Pricing formula or cost mode (Supply cost - sc/Cash cost - cc), Plant size (Big/Small), Plant efficiency (High/Low), Project funding (Debt/Equity), Results mode (Constant_$/Inflated_$)
'''


# This is the model run script to run model
project_datas = pd.read_csv("./project_data.csv")
multipliers = pd.read_csv("./sectorwise_multipliers.csv")


#Options to select
"""plant_modes = "Green"  #to reflect pricing formula for all-in supply cost or just cash cost basis
plant_sizes = "Large"
plant_effys = "High"
fund_modes = "Debt"  #types of project financing
opex_modes = "Inflated"
locations = "USA"
products = "Ethylene"
carbon_values = "Yes"
operating_prd=27 
infl=0.02 
RR=0.035 
IRR=0.10 
shrDebt_value=0.60 
baseYear=None 
ownerCost=0.10
corpTAX_value=None 
Feed_Price=None 
Fuel_Price=None 
Elect_Price=None 
CarbonTAX_value=None 
credit_value=0.10
construction_prd= 3
capex_spread=[0.20, 0.50, 0.30]
yr1_capex=0.20
yr2_capex=0.50
yr3_capex=0.30
CAPEX=None 
OPEX=None
PRIcoef=0.3 
CONcoef=0.7
util_operating_first=0.70 
util_operating_second=0.80 
util_operating_third=0.95"""

#for i in range(len(products)):
  #results = Analytics_Model(multiplier=multipliers, project_data=project_datas, location=locations[2], product=products[i], plant_mode=plant_modes[0], fund_mode=fund_modes[1], opex_mode=opex_modes[0], carbon_value=carbon_values[1])
"""results = Analytics_Model(
    multiplier=multipliers,
    plant_mode="Brown",
    fund_mode="Mixed",
    opex_mode="Uninflated",
    carbon_value="No",
    sector_code="CAN_C20",
    Cap=250000,
    Yld=0.95,
    feedEcontnt=25.0,
    Heat_req=3200,
    Elect_req=600,
    feedCcontnt=0.85,
    EcNatGas=53.6,
    ngCcontnt=50.3,
    hEFF=0.80,
    eEFF=0.50,
    construction_prd=3,
    capex_spread=[0.20, 0.50, 0.30],
    operating_prd=27,
    infl=0.02,
    RR=0.035,
    IRR=0.10,
    shrDebt_value=0.60,
    baseYear=2025,
    ownerCost=0.10,
    corpTAX_value=0.25,
    Feed_Price=150.0,
    Fuel_Price=3.5,
    Elect_Price=0.12,
    CarbonTAX_value=50.0,
    credit_value=0.10,
    CAPEX=10000000,
    OPEX=500000,
    PRIcoef=0.3,
    CONcoef=0.7,
    util_operating_first=0.70,
    util_operating_second=0.80,
    util_operating_third=0.95
)

print(results)"""

