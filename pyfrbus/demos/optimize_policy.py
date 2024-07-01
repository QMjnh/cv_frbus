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

no_pandemic = frbus.solve(start, end, data)

# Set up trajectories to match the historical data
no_pandemic.loc[start:end, "fgdp_t"] = data.loc[start:end, "fgdp"]     # foreign GDP (world)
no_pandemic.loc[start:end, "fgdpt_t"] = data.loc[start:end, "fgdpt"]   # foreign GDP trend (world)
no_pandemic.loc[start:end, "fpic_t"] = data.loc[start:end, "fpic"]     # foreign CPI (bilateral export trade weights)


no_pandemic.loc[start:end, "fpc_t"] = data.loc[start:end, 'fpc']       # foreign aggregate consumer price (G39)
no_pandemic.loc[start:end, "frl10_t"] = data.loc[start:end, 'frl10']   # foreign long-term interest rate (G10)
no_pandemic.loc[start:end, "frs10_t"] = data.loc[start:end, 'frs10']   # foreign short-term interest rate (G10)



stay_home_total = 17 # weeks
start_stayhome = pd.Period("2020Q2")
end_stayhome = pd.Period("2020Q2")
no_pandemic.loc[start_stayhome:end_stayhome, "lurnat_t"] = data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1-.019)**stay_home_total      # natural rate of unemployment rate
no_pandemic.loc[start_stayhome:end_stayhome, "lur_t"] = data.loc[start_stayhome:end_stayhome, 'lur'] * (1-.019)**stay_home_total      # rate of unemployment rate

no_pandemic.loc[end_stayhome+1:end, "lurnat_t"] = data.loc[end_stayhome+1:end, 'lurnat']
no_pandemic.loc[end_stayhome+1:end, "lur_t"] = data.loc[end_stayhome+1:end, 'lur']

# Define the target variables and their trajectories
targ_no_stayhome = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur', 'lurnat']
traj_no_stayhome = ["fgdp_t", "fgdpt_t", "fpic_t", "fpc_t", "frl10_t", "frs10_t", 'lur_t', 'lurnat_t']

# Define instruments as add-factors for flexibility
# inst = ["fgdp_aerr", "fgdpt_aerr", "fpic_aerr"]
inst_no_stayhome = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur', 'lurnat']
# inst = ["fgdp_aerr", "fgdpt_aerr", "fpic_aerr", "fpc_aerr", "frl10_aerr", "frs10_aerr"]

# Run mcontrol to match the target variables to their trajectories

no_stayhome = frbus.mcontrol(start, end, no_pandemic, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

# print("concho", no_pandemic.loc['2020Q1':'2020Q4', 'lur'])

targ_custom = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur', 'lurnat']
traj_custom = ["fgdp_t", "fgdpt_t", "fpic_t", "fpc_t", "frl10_t", "frs10_t", "lur_t", 'lurnat_t']
inst_custom = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur', 'lurnat']

start_lockdown_opt = pd.Period("2020Q2")
end_lockdown_opt = pd.Period("2020Q2")

# print(no_stayhome.loc[end_lockdown_opt:end, 'lurnat_t'])
# print(no_stayhome.loc[end_lockdown_opt:end, 'lur_t'])


lockdown_duration = 17 # duration in weeks
no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, "lur_t"] = no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, 'lur'] * 1.019**lockdown_duration 
# no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, "lur_t"] *=  1.019**lockdown_duration

no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, "lurnat_t"] = no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, 'lurnat'] * 1.019**lockdown_duration
# no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, "lurnat_t"] *=  (1.019)**lockdown_duration
# print('no_stayhome')
# print(no_stayhome.loc[end_lockdown_opt:end, 'lurnat_t'])
# print(no_stayhome.loc[end_lockdown_opt:end, 'lur_t'])

# print('data')
# print(custom_stayhome.loc[end_lockdown_opt:end, 'lurnat_t'])
custom_stayhome = frbus.mcontrol(start_lockdown_opt, end_lockdown_opt, no_stayhome, targ_custom, traj_custom, inst_custom)
custom_stayhome = frbus.solve(end_lockdown_opt, end, custom_stayhome)
custom_stayhome = frbus.mcontrol(end_lockdown_opt, end, custom_stayhome, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

no_stayhome.to_csv("./results/optimize/no_stayhome.csv", index=True)
custom_stayhome.to_csv("./results/optimize/custom_stayhome.csv", index=True)



# foreign_const_sim.to_csv("mcontrol.csv", index=True)

# # # View results
variables = pd.read_csv('model_variables_simple.csv')


dfs = {'baseline': data, 'custom_stayhome': custom_stayhome, 'no_stayhome': no_stayhome, 'no_pandemic': no_pandemic}

plots = [{'column': 'xgdp', 'type': 'pct_change'}, {'column': 'pcxfe', 'type': 'pct_change', 'name':'PCE Price Index'}, {'column': 'xgdpt'}, {'column': 'pcpi', 'type':'pct_change', 'name':'CPI'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'lprdt'}, {'column': 'lhp', 'name':'Agg. labor hours, business sector'}, {'column': 'lww', 'name':'Workweek, business sector'}, {'column': 'lqualt'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/labor quality.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'leg', 'name': 'Gov. civilian employment'}, {'column': 'lur', 'name':'Unemployment Rate'}, {'column': 'lurnat'}, {'column': 'leh'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/(un)employment.png', plot_title='No April lockdown + same foreign variables')

plots = [{'column': 'ex', 'name':'Export, cw 2012$'}, {'column': 'em','name':'Import, cw 2012$' }, {'column': 'fpic', 'name': 'Foreign CPI (G39)'}, {'column': 'fgdp', 'name':'Foreign GDP (G39)'}]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/optimize/export+import.png', plot_title='No April lockdown + same foreign variables')
