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
targ_no_stayhome = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10"]
traj_no_stayhome = ["fgdp_t", "fgdpt_t", "fpic_t", "fpc_t", "frl10_t", "frs10_t"]

# Define instruments as add-factors for flexibility
# inst = ["fgdp_aerr", "fgdpt_aerr", "fpic_aerr"]
inst_no_stayhome = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10"]
# inst = ["fgdp_aerr", "fgdpt_aerr", "fpic_aerr", "fpc_aerr", "frl10_aerr", "frs10_aerr"]

# Run mcontrol to match the target variables to their trajectories

# this is wrong because no_pandemic shouldn't be run on with_adds. It should be run on the data
no_pandemic = frbus.solve(start, end, with_adds)
no_stayhome = frbus.mcontrol(start, end, no_pandemic, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

print("concho", no_pandemic.loc['2020Q1':'2020Q4', 'lur'])

targ_custom = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur']
traj_custom = ["fgdp_t", "fgdpt_t", "fpic_t", "fpc_t", "frl10_t", "frs10_t", "lur_t"]
inst_custom = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur']

start_lockdown = pd.Period("2020Q2")
end_lockdown = pd.Period("2020Q3")
lockdown_duration = 17 # duration in weeks
no_pandemic.loc[start_lockdown:end_lockdown, "lur_t"] = no_stayhome.loc[start_lockdown:end_lockdown, 'lur']
print('convoi', no_pandemic.loc[start_lockdown:end_lockdown, "lur_t"])
no_pandemic.loc[start_lockdown:end_lockdown, "lur_t"] *=  1.019**lockdown_duration
print('convoi', no_pandemic.loc[start_lockdown:end_lockdown, "lur_t"])
custom_stayhome = frbus.mcontrol(start_lockdown, end_lockdown, no_pandemic, targ_custom, traj_custom, inst_custom)

no_stayhome.to_csv("./results/optimize/no_stayhome.csv", index=True)
custom_stayhome.to_csv("./results/optimize/custom_stayhome.csv", index=True)



# foreign_const_sim.to_csv("mcontrol.csv", index=True)

# # # View results
variables = pd.read_csv('model_variables_simple.csv')


dfs = {'baseline': data, 'custom_stayhome': custom_stayhome, 'no_stayhome': no_stayhome}

plots = [{'column': 'xgdp', 'type': 'pct_change'}, {'column': 'pcxfe', 'type': 'pct_change', 'name':'PCE Price Index'}, {'column': 'xgdpt'}, {'column': 'pcpi', 'type':'pct_change', 'name':'CPI'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'lprdt'}, {'column': 'lhp', 'name':'Agg. labor hours, business sector'}, {'column': 'lww', 'name':'Workweek, business sector'}, {'column': 'lqualt'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/labor quality.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'leg', 'name': 'Gov. civilian employment'}, {'column': 'lur', 'name':'Unemployment Rate'}, {'column': 'lurnat'}, {'column': 'leh'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/(un)employment.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'ex', 'name':'Export, cw 2012$'}, {'column': 'em','name':'Import, cw 2012$' }, {'column': 'fpic', 'name': 'Foreign CPI (G39)'}, {'column': 'fgdp', 'name':'Foreign GDP (G39)'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/export+import.png', plot_title='No April lockdown + same foreign variables')
