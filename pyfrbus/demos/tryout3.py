import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
from pyfrbus.custom_plot import custom_plot

# Load data
data = load_data("../data/HISTDATA.TXT")

# Load model
frbus = Frbus("../models/model.xml")

# Specify dates
start = pd.Period("2019Q4")
end = "2023Q4"

# Initialize tracking residuals to match the historical data
# with_adds = frbus.init_trac(start, end, data)
with_adds = data.copy(deep=True)

# Set up trajectories to match the historical data
with_adds.loc[start:end, "fgdp_t"] = data.loc[start:end, "fgdp"]     # foreign GDP (world)
with_adds.loc[start:end, "fgdpt_t"] = data.loc[start:end, "fgdpt"]   # foreign GDP trend (world)
with_adds.loc[start:end, "fpic_t"] = data.loc[start:end, "fpic"]     # foreign CPI (bilateral export trade weights)


with_adds.loc[start:end, "fpc_t"] = data.loc[start:end, 'fpc']       # foreign aggregate consumer price (G39)
with_adds.loc[start:end, "frl10_t"] = data.loc[start:end, 'frl10']   # foreign long-term interest rate (G10)
with_adds.loc[start:end, "frs10_t"] = data.loc[start:end, 'frs10']   # foreign short-term interest rate (G10)

# Define the target variables and their trajectories
targ = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10"]
traj = ["fgdp_t", "fgdpt_t", "fpic_t", "fpc_t", "frl10_t", "frs10_t"]

# Define instruments as add-factors for flexibility
# inst = ["fgdp_aerr", "fgdpt_aerr", "fpic_aerr"]
inst = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10"]
# inst = ["fgdp_aerr", "fgdpt_aerr", "fpic_aerr", "fpc_aerr", "frl10_aerr", "frs10_aerr"]

# Run mcontrol to match the target variables to their trajectories

no_pandemic = frbus.solve(start, end, with_adds)
no_stayhome = frbus.mcontrol(start, end, no_pandemic, targ, traj, inst)

no_pandemic.to_csv("no_pandemic.csv", index=True)
no_stayhome.to_csv("no_stayhome.csv", index=True)



# foreign_const_sim.to_csv("mcontrol.csv", index=True)

# # # View results
variables = pd.read_csv('model_variables_simple.csv')


dfs = {'baseline': data, 'no_stayhome': no_stayhome, 'no_pandemic': no_pandemic}

plots = [{'column': 'xgdp', 'type': 'pct_change'}, {'column': 'pcxfe', 'type': 'pct_change', 'name':'PCE Price Index'}, {'column': 'xgdpt'}, {'column': 'pcpi', 'type':'pct_change', 'name':'CPI'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './png/mcontrol/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'lprdt'}, {'column': 'lhp', 'name':'Agg. labor hours, business sector'}, {'column': 'lww', 'name':'Workweek, business sector'}, {'column': 'lqualt'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './png/mcontrol/labor quality.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'leg', 'name': 'Gov. civilian employment'}, {'column': 'lep', 'name':'Employment, business sector'}, {'column': 'lurnat'}, {'column': 'leh'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './png/mcontrol/(un)employment.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'ex', 'name':'Export, cw 2012$'}, {'column': 'em','name':'Import, cw 2012$' }, {'column': 'fpic', 'name': 'Foreign CPI (G39)'}, {'column': 'fgdp', 'name':'Foreign GDP (G39)'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './png/mcontrol/export+import.png', plot_title='No April lockdown + same foreign variables')
