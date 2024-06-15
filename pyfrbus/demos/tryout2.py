import pandas
from numpy import array, cumprod

from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
from pyfrbus.sim_lib import _single_plot
from pyfrbus.sim_lib import sim_plot
from pyfrbus.custom_plot import custom_plot

# Load data
data = load_data("../data/HISTDATA.TXT")

# Load model
frbus = Frbus("../models/model.xml")

# Specify dates
start = pandas.Period("2019Q4")
end = "2023Q4"


# Solve to baseline with adds
dummy = frbus.init_trac(start, end, data)
foreign_const = data.copy(deep=True)


# no_stayhome = frbus.solve("2020Q2", "2023Q4", data)
# no_stayhome.to_csv("economy_noApril_stayhome.csv")
# custom_plot(data, no_stayhome, "2020Q2", "2023Q4", "png/no_stayhome.png", plot1 = "xgdp", plot2 = "fpic", plot3 = 'ex', plot4='em')
# sim_plot(data, no_stayhome, "2020Q2", "2023Q4", 'png/economy_noApril_stayhome.png')


"""
# ecnia: Personal consumption expenditures, cw 2012$ (NIPA definition)
# pcxfe: Price index for personal consumption expendits ex. food and energy, cw (NIPA definition)

# pcpi: Consumer price index,total

# ex: Exports of goods and services, cw 2012$ (depends on fgdp (foreign GDP) and fxgap (foreign output gap))
# emo: Imports of goods and services ex. petroleum, cw 2012$
# emon: Imports of goods and services ex. petroleum, nominal, current $ 
# em: Imports of goods and services, cw 2012$
# emp: Petroleum imports, cw 2012$
# empn: Petroleum imports, nominal, current $
# pmo: Price index for imports ex. petroleum, cw
# pmp: Price index for petroleum imports
# poil: Price of imported oil ($ per barrel)

# fpic: Foreign consumer price inflation (G39, bilateral export trade weights) # https://www.federalreserve.gov/releases/H10/Weights/
# fpi10: Foreign consumer price inflation (G10)
# fgdp: Foreign aggregate GDP (world, bilateral export weights)

# hggdpt: Trend growth rate of XGDP, cw 2012$ (annual rate)
# xgdpt: Potential GDP, cw 2012$
# xgdp: GDP, cw 2012$
# xgdpn: GDP, nominal, current $ 

# lfpr: Labor force participation rate
# lhp: Aggregate labor hours, business sector (employee and self-employed)
# lprdt: Trend labor productivity
# lww: Workweek, business sector (employee and self-employed)
# lqualt: Labor quality, trend level
# qlfpr: Trend labor force participation rate       # The trend participation rate follows a random walk with time-varying drift.
# lur: Civilian unemployment rate (break adjusted)
# leh: Civilian employment (break adjusted)
# leg: Government civilian employment ex. gov. enterprise
# lep: Employment in business sector (employee and  self-employed)
# lurnat: Natural rate of unemployment

# queco: Desired level of consumption of nondurable goods and nonhousing services

# yh: Income, household, total (real after-tax)
# yniln: Labor income (national income component)

# pxr: Price index for exports, cw (relative to PXP)
# pxp: Price index for final sales plus imports less gov. labor

# fpx: Nominal exchange rate (G39, import/export trade weights)
# fpxr: Real exchange rate (G39, import/export trade weights)
# frl10: Foreign long-term interest rate (G10)
# frs10: Foreign short-term interest rate (G10)
# fpc: Foreign aggregate consumer price (G39, import/export trade weights)

# rff: Federal funds rate
# egfe: Federal Government expenditures, CW 2012$
# egfen: Federal Government expenditures, nominal, current $
# egfet: Trend Federal Government expenditures
"""

# simulate the situation where the economy is hit by a pandemic but the US government does not enforce a stay-at-home order
# this is achieved by setting _trac for variables reflects foreign economies (to keep them the same as the baseline) 
# and set _trac for import and export variables to reflect the pandemic's impact on the US economy

foreign_const["fpic_trac"] = dummy['fpic_trac']
foreign_const["fpi10_trac"] = dummy['fpi10_trac']
foreign_const["fxgap_trac"] = dummy['fxgap_trac']
foreign_const["fgdp_trac"] = dummy['fgdp_trac']
foreign_const["fgdpt_trac"] = dummy['fgdpt_trac']
foreign_const["fpc_trac"] = dummy['fpc_trac']
foreign_const["frl10_trac"] = dummy['frl10_trac']
foreign_const["frs10_trac"] = dummy['frs10_trac']
# foreign_const["fpitrg_trac"] = dummy['fpitrg_trac'] # exogenous, doesnt work
# foreign_const["frstar_trac"] = dummy['frstar_trac'] # makes the fpic simulation worse

foreign_const["fpx_trac"] = dummy['fpx_trac']
foreign_const["fpxr_trac"] = dummy['fpxr_trac']

## export 
foreign_const["ex_trac"] = dummy['ex_trac']
foreign_const["exn_trac"] = dummy['exn_trac']
foreign_const["pxp_trac"] = dummy['pxp_trac']
foreign_const["pxr_trac"] = dummy['pxr_trac']


## import depends on emo and emp, both depends on xgdp
# foreign_const['em_trac'] = dummy['em_trac']
# foreign_const['emon_trac'] = dummy['emon_trac']
# foreign_const['emn_trac'] = dummy['emn_trac']
# foreign_const['emo_trac'] = dummy['emo_trac']
# foreign_const['emp_trac'] = dummy['emp_trac']
# foreign_const['empn_trac'] = dummy['empn_trac']
# foreign_const['pmo_trac'] = dummy['pmo_trac']
# foreign_const['pmp_trac'] = dummy['pmp_trac']
# foreign_const["poil_trac"] = dummy['poil_trac']
# foreign_const["poilr_trac"] = dummy['poilr_trac']
# foreign_const["poilrt_trac"] = dummy['poilrt_trac'] # exogenous, doesnt work
# foreign_const["xgap_trac"] = dummy['xgap_trac']     # depends on internal variables of US economy
# foreign_const["xgap2_trac"] = dummy['xgap2_trac']   # depends on xgdp


foreign_const_sim = frbus.solve(start, end, foreign_const)
foreign_const_sim.to_csv("foreign_const.csv", index=True)

# # View results
variables = pd.read_csv('model_variables_simple.csv')

plots = [{'column': 'xgdp', 'type': 'pct_change'}, {'column': 'pcxfe', 'type': 'pct_change', 'name':'PCE Price Index'}, {'column': 'xgdpt'}, {'column': 'pcpi', 'type':'pct_change', 'name':'CPI'}]
custom_plot(data, foreign_const_sim, '2020Q1', '2023Q4', plots, variables, './png/foreign const/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'lprdt'}, {'column': 'lhp', 'name':'Agg. labor hours, business sector'}, {'column': 'lww', 'name':'Workweek, business sector'}, {'column': 'lqualt'}]
custom_plot(data, foreign_const_sim, '2020Q1', '2023Q4', plots, variables, './png/foreign const/labor quality.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'leg', 'name': 'Gov. civilian employment'}, {'column': 'lep', 'name':'Employment, business sector'}, {'column': 'lurnat'}, {'column': 'leh'}]
custom_plot(data, foreign_const_sim, '2020Q1', '2023Q4', plots, variables, './png/foreign const/(un)employment.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'ex', 'name':'Export, cw 2012$'}, {'column': 'em','name':'Import, cw 2012$' }, {'column': 'fpic', 'name': 'Foreign CPI (G39)'}, {'column': 'fgdp', 'name':'Foreign GDP (G39)'}]
custom_plot(data, foreign_const_sim, '2020Q1', '2023Q4', plots, variables, './png/foreign const/export+import.png', plot_title='No April lockdown + same foreign variables')
