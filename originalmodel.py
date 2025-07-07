
import pandas as pd
import numpy as np


##################################################################PROCESS MODEL BEGINS##############################################################################

def ChemProcess_Model(data, EcNatGas=None, ngCcontent=None, hEFF=None, eEFF=None, Cap=None, Yld=None, feedEcontnt=None, Heat_req=None, Elect_req=None, feedCcontnt=None, construction_prd=3, operating_prd=27, util_operating_first=0.70, util_operating_second=0.80, util_operating_third=0.95): #add 5 more optional function requirements

  data['Cap'] = Cap if Cap is not None else data['Cap']
  data['Yld'] = Yld if Yld is not None else data['Yld']
  data['feedEcontnt'] = feedEcontnt if feedEcontnt is not None else data['feedEcontnt']
  data['Heat_req'] = Heat_req if Heat_req is not None else data['Heat_req']
  data['Elect_req'] = Elect_req if Elect_req is not None else data['Elect_req']
  data['feedCcontnt'] = feedCcontnt if feedCcontnt is not None else data['feedCcontnt']

  # Energy/Heat content (HHV) of natural gas...GJ/t
  EcNatGas = EcNatGas if EcNatGas is not None else 53.6
  # CO2 content of natural gas --> kg CO2 per GJ
  ngCcontnt = ngCcontnt if ngCcontnt is not None else 50.3
  hEFF = hEFF if hEFF is not None else 0.80
  eEFF = eEFF if eEFF is not None else 0.50



  
  #construction_prd = 3 #add value from payload value
  #operating_prd = 27 #replace with payload value
  project_life = construction_prd + operating_prd

  
  util_fac = np.zeros(project_life)
  # For operating years: assign the first two values, then use the third for all remaining years.
  if operating_prd >= 1:
    util_fac[construction_prd] = util_operating_first
  if operating_prd >= 2:
    util_fac[construction_prd + 1] = util_operating_second
  if operating_prd >= 3:
    util_fac[(construction_prd + 2):] = util_operating_third

  #util_fac[construction_prd] = 0.70 #1st year value replace with payload value
  #util_fac[(construction_prd+1)] = 0.80 #2nd year value replace with payload value
  #util_fac[(construction_prd+2):] = 0.95 #3rd year value replace with payload value

  
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

def MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value, EcNatGas=None, ngCcontnt=None, hEFF=None, eEFF=None, construction_prd=3, capex_spread=None, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=None, ownerCost=0.10, corpTAX_value=None, Feed_Price=None, Fuel_Price=None, Elect_Price=None, CarbonTAX_value=None, credit_value=0.10,CAPEX=None, OPEX=None, operating_prd=27, util_operating_first=0.70, util_operating_second=0.80,util_operating_third=0.95):

  prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(data, EcNatGas=EcNatGas, ngCcontnt=ngCcontnt, hEFF=hEFF, eEFF=eEFF, construction_prd=construction_prd, operating_prd=operating_prd, util_operating_first=util_operating_first, util_operating_second=util_operating_second, util_operating_third=util_operating_third)
  eEFF = eEFF 

  
  Infl = infl  #replace with payload value
  #RR = 0.035  #replace with payload value
  #IRR = 0.10 #replace with payload value

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

  baseYear = baseYear if baseYear is not None else data['Base_Yr'] #replace with payload value
  Year = list(range(baseYear, baseYear + project_life))

  
  """yr1_capex = yr1_capex
  yr2_capex = yr2_capex
  yr3_capex = yr3_capex"""

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
  else:
    corpTAX[:] = data['corpTAX']

  
  corpTAX[:construction_prd] = 0

  
  credit = credit_value #0.10

  Feed_Price = Feed_Price if Feed_Price is not None else data["Feed_Price"]
  Fuel_Price = Fuel_Price if Fuel_Price is not None else data["Fuel_Price"]
  Elect_Price = Elect_Price if Elect_Price is not None else data["Elect_Price"]

  #feedprice = Feed_Price if Feed_Price is not None else [0] * project_life #replace with payload value
  #fuelprice = Fuel_Price if Fuel_Price is not None else [0] * project_life #replace with payload value
  #elecprice = Elect_Price if Elect_Price is not None else [0] * project_life #replace with payload value

  ##################INFLATED AND UNINFLATED PRICES SCENARIOS BEGINS#########################
  """if opex_mode == "Inflated":
    
    for i in range(project_life):
        feedprice[i] = data["Feed_Price"] * ((1 + Infl) ** i)
        fuelprice[i] = data["Fuel_Price"] * ((1 + Infl) ** i)
        elecprice[i] = data["Elect_Price"] * ((1 + Infl) ** i)
  else:

    feedprice = [data["Feed_Price"]] * project_life
    fuelprice = [data["Fuel_Price"]] * project_life
    elecprice = [data["Elect_Price"]] * project_life"""
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
  CarbonTAX_value = CarbonTAX_value if CarbonTAX_value is not None else data["CO2price"]
  CarbonTAX = [CarbonTAX_value] * project_life

  
  if carbon_value == "Yes":
    CO2cst = CarbonTAX * ghg_dir
  else:
    CO2cst = [0] * project_life
  
  # Use CAPEX and OPEX from payload if provided, else use data
  CAPEX = CAPEX if CAPEX is not None else data["CAPEX"]
  OPEX = OPEX if OPEX is not None else data["OPEX"]
  
  Yrly_invsmt = [0] * project_life

  #data["CAPEX"] = 'user payload value' #replace with payload value Apply CAPEX spread dynamically
  for i in range(construction_prd):
    Yrly_invsmt[i] = capex_spread[i] * CAPEX
  
  """Yrly_invsmt[0] = yr1_capex * CAPEX
  Yrly_invsmt[1] = yr2_capex * CAPEX
  Yrly_invsmt[2] = yr3_capex * CAPEX
  Yrly_invsmt[3:] = OPEX + feedcst[3:] + fuelcst[3:] + eleccst[3:] + CO2cst[3:]"""
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

def MacroEconomic_Model(multiplier, data, location, plant_mode, fund_mode, opex_mode, carbon_value, construction_prd=3, capex_spread=None, PRIcoef=0.3, CONcoef=0.7, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=None, ownerCost=0.10, corpTAX_value=None, Feed_Price=None, Fuel_Price=None, Elect_Price=None, CarbonTAX_value=None, credit_value=0.10,CAPEX=None, OPEX=None, operating_prd=27, util_operating_first=0.70, util_operating_second=0.80,util_operating_third=0.95):
  # This model is based on the multipliers generated in-house using OECD data on national input output tables for various countries


  PRIcoef = PRIcoef #replace with payload value
  CONcoef = CONcoef #replace with payload value

  prodQ, _, _, _, _, _, _ = ChemProcess_Model(data, construction_prd=construction_prd, operating_prd=operating_prd, util_operating_first=util_operating_first, util_operating_second=util_operating_second, util_operating_third=util_operating_third)
  Ps, _, _, _, _, _, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, _, _ = MicroEconomic_Model(data, plant_mode, fund_mode, opex_mode, carbon_value, construction_prd=construction_prd, capex_spread=capex_spread, infl=infl, RR=RR, IRR=IRR, shrDebt_value=shrDebt_value, baseYear=baseYear, ownerCost=ownerCost, corpTAX_value=corpTAX_value, Feed_Price=Feed_Price, Fuel_Price=Fuel_Price, Elect_Price=Elect_Price, CarbonTAX_value=CarbonTAX_value, credit_value=credit_value, CAPEX=CAPEX, OPEX=OPEX, operating_prd=operating_prd, util_operating_first=util_operating_first, util_operating_second=util_operating_second, util_operating_third=util_operating_third)
  
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

def Analytics_Model( multiplier, project_data, location, plant_mode, fund_mode, opex_mode, carbon_value, construction_prd=3, capex_spread=None, operating_prd=27, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=None, ownerCost=0.10, corpTAX_value=None, Feed_Price=None, Fuel_Price=None, Elect_Price=None, CarbonTAX_value=None, credit_value=0.10, CAPEX=None, OPEX=None, PRIcoef=0.3, CONcoef=0.7, util_operating_first=0.70, util_operating_second=0.80, util_operating_third=0.95):
    # ✅ Filter only by location
    dt = project_data[(project_data['Country'] == location)]

    Infl = 0.02  # inflation factor

    tempNUM = 1000000
    results = []

    for index, data in dt.iterrows():
        prodQ, feedQ, Rheat, netHeat, Relec, ghg_dir, ghg_ind = ChemProcess_Model(
            data,
            construction_prd=construction_prd,
            operating_prd=operating_prd,
            util_operating_first=util_operating_first,
            util_operating_second=util_operating_second,
            util_operating_third=util_operating_third
        )

        Ps, Pso, Pc, Pco, cshflw, cshflw2, Year, project_life, construction_prd, Yrly_invsmt, bank_chrg, NetRevn, tax_pybl = MicroEconomic_Model(
            data,
            plant_mode,
            fund_mode,
            opex_mode,
            carbon_value,
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
            util_operating_third=util_operating_third
        )

        GDP_dir, GDP_ind, GDP_tot, JOB_dir, JOB_ind, JOB_tot, PAY_dir, PAY_ind, PAY_tot, TAX_dir, TAX_ind, TAX_tot, GDP_totPRI, JOB_totPRI, PAY_totPRI, GDP_dirPRI, JOB_dirPRI, PAY_dirPRI = MacroEconomic_Model(
            multiplier,
            data,
            location,
            plant_mode,
            fund_mode,
            opex_mode,
            carbon_value,
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
            util_operating_third=util_operating_third
        )

        Yrly_cost = np.array(Yrly_invsmt) + np.array(bank_chrg)

        Ps = [Ps] * project_life
        Pc = [Pc] * project_life
        Psk = [Pso * ((1 + Infl) ** i) for i in range(project_life)]
        Pck = [Pco * ((1 + Infl) ** i) for i in range(project_life)]

        Rs = [Ps[i] * prodQ[i] for i in range(project_life)]
        NRs = [Rs[i] - Yrly_cost[i] for i in range(project_life)]
        Rsk = np.array(Psk) * np.array(prodQ)
        NRsk = Rsk - Yrly_cost

        ccflows = np.cumsum(NRs)
        ccflowsk = np.cumsum(NRsk)

        cost_modes = ["Supply Cost", "Cash Cost"]
        cost_mode = cost_modes[0] if plant_mode == "Green" else cost_modes[1]

        # JOB, GDP, TAX, PAY processing unchanged

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

        pri_bothJOB[construction_prd:] = JOB_totPRI[construction_prd:]
        pri_directJOB[construction_prd:] = JOB_dirPRI[construction_prd:]
        pri_indirectJOB[construction_prd:] = JOB_totPRI[construction_prd:] - JOB_dirPRI[construction_prd:]

        pri_bothJOB[:construction_prd] = JOB_totPRI[:construction_prd]
        pri_directJOB[:construction_prd] = JOB_dirPRI[:construction_prd]
        pri_indirectJOB[:construction_prd] = JOB_totPRI[:construction_prd] - JOB_dirPRI[:construction_prd]

        All_bothJOB[construction_prd:] = JOB_tot[construction_prd:]
        All_directJOB[construction_prd:] = JOB_dir[construction_prd:]
        All_indirectJOB[construction_prd:] = JOB_tot[construction_prd:] - JOB_dir[construction_prd:]

        All_bothJOB[:construction_prd] = JOB_tot[:construction_prd]
        All_directJOB[:construction_prd] = JOB_dir[:construction_prd]
        All_indirectJOB[:construction_prd] = JOB_tot[:construction_prd] - JOB_dir[:construction_prd]

        result = pd.DataFrame({
            'Year': Year,
            'Process Technology': [data['ProcTech']] * project_life,
            'Feedstock Input (TPA)': feedQ,
            'Product Output (TPA)': prodQ,
            'Direct GHG Emissions (TPA)': ghg_dir,
            'Cost Mode': [cost_mode] * project_life,
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
    results.to_csv("model_results.csv", index=False)

    return results



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
plant_modes = "Green"  #to reflect pricing formula for all-in supply cost or just cash cost basis
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
"""yr1_capex=0.20
yr2_capex=0.50
yr3_capex=0.30"""
CAPEX=None 
OPEX=None
PRIcoef=0.3 
CONcoef=0.7
util_operating_first=0.70 
util_operating_second=0.80 
util_operating_third=0.95

#for i in range(len(products)):
  #results = Analytics_Model(multiplier=multipliers, project_data=project_datas, location=locations[2], product=products[i], plant_mode=plant_modes[0], fund_mode=fund_modes[1], opex_mode=opex_modes[0], carbon_value=carbon_values[1])
#results = Analytics_Model(multiplier=multipliers, project_data=project_datas, location="CAN", product="Ethylene", plant_effys="High", plant_size="Large", construction_prd=3, capex_spread=[0.20, 0.50, 0.30], plant_mode="Brown", fund_mode="Mixed", opex_mode="Uninflated", carbon_value="No", operating_prd=27, infl=0.02, RR=0.035, IRR=0.10, shrDebt_value=0.60, baseYear=None, ownerCost=0.10, corpTAX_value=None, Feed_Price=None, Fuel_Price=None, Elect_Price=None, CarbonTAX_value=None, credit_value=0.10, CAPEX=None, OPEX=None,PRIcoef=0.3, CONcoef=0.7,util_operating_first=0.70, util_operating_second=0.80, util_operating_third=0.95)
#print(results)

