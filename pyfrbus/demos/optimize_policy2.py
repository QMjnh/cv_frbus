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
print(no_pandemic.shape)
print(no_pandemic["lur_trac"].values)
# Set up trajectories to match the historical data
# no_pandemic.loc[start:end, "fgdp_t"] = data.loc[start:end, "fgdp"]     # foreign GDP (world)
# no_pandemic.loc[start:end, "fgdpt_t"] = data.loc[start:end, "fgdpt"]   # foreign GDP trend (world)
# no_pandemic.loc[start:end, "fpic_t"] = data.loc[start:end, "fpic"]     # foreign CPI (bilateral export trade weights)


# no_pandemic.loc[start:end, "fpc_t"] = data.loc[start:end, 'fpc']       # foreign aggregate consumer price (G39)
# no_pandemic.loc[start:end, "frl10_t"] = data.loc[start:end, 'frl10']   # foreign long-term interest rate (G10)
# no_pandemic.loc[start:end, "frs10_t"] = data.loc[start:end, 'frs10']   # foreign short-term interest rate (G10)


no_stayhome_data = frbus.init_trac(start, end, data)
print(no_stayhome_data.shape)
print(no_stayhome_data["lur_trac"].values)

# no_stayhome_data.drop(['lurnat_aerr', 'lur_aerr'], axis=1, inplace=True)
stay_home_total = 17 # weeks
start_stayhome = pd.Period("2020Q2")
end_stayhome = pd.Period("2020Q3")
# no_stayhome_data.loc[start_stayhome:end_stayhome, "lurnat_t"] = data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1-.019)**stay_home_total      # natural rate of unemployment rate
no_stayhome_data.loc[start_stayhome:end_stayhome, "lur_t"] = data.loc[start_stayhome:end_stayhome, 'lur'] * (1-.019)**stay_home_total      # rate of unemployment rate

# no_stayhome_data.loc[end_stayhome+1:end, "lurnat_t"] = data.loc[end_stayhome+1:end, 'lurnat']
no_stayhome_data.loc[end_stayhome+1:end, "lur_t"] = data.loc[end_stayhome+1:end, 'lur']

# print("trac", no_stayhome_data.loc[start_stayhome:end_stayhome, 'lurnat_t'])
# print("data", no_stayhome_data.loc[start_stayhome:end_stayhome, 'lurnat'])

# Define the target variables and their trajectories
# targ_no_stayhome = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur', 'lurnat']
# traj_no_stayhome = ["fgdp_t", "fgdpt_t", "fpic_t", "fpc_t", "frl10_t", "frs10_t", 'lur_t', 'lurnat_t']

targ_no_stayhome = ['lur']
traj_no_stayhome = ['lur_t']
# Define instruments as add-factors for flexibility
# inst_no_stayhome = ["fgdp", "fgdpt", "fpic", "fpc", "frl10", "frs10", 'lur', 'lurnat']
inst_no_stayhome = ['lur']

# Run mcontrol to match the target variables to their trajectories

no_stayhome = frbus.mcontrol(start, end, no_stayhome_data, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)
# print("last", no_stayhome.loc[start_stayhome:end_stayhome, 'lurnat'])

# ec
# ecd
# ech
# ecnia
# ecnian
# eco

# em
# emn
# emo
# emon
# emp
# empn
# emptrt
# ex
# exn
# fcbn
# fcbrn

# hggdp
# hggdpt

#n16


targ_custom = ['lur']
traj_custom = ["lur_t"]
inst_custom = ['lur']

start_lockdown_opt = pd.Period("2020Q2")
end_lockdown_opt = pd.Period("2020Q3")


lockdown_duration = 17 # duration in weeks
no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, "lur_t"] = no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, 'lur'] * 1.019**lockdown_duration 

# no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, "lurnat_t"] = no_stayhome.loc[start_lockdown_opt:end_lockdown_opt, 'lurnat'] * 1.019**lockdown_duration
custom_stayhome = frbus.mcontrol(start_lockdown_opt, end_lockdown_opt, no_stayhome, targ_custom, traj_custom, inst_custom)
custom_stayhome = frbus.solve(end_lockdown_opt, end, custom_stayhome)
custom_stayhome = frbus.mcontrol(end_lockdown_opt, end, custom_stayhome, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

no_stayhome.to_csv("./results/optimize/no_stayhome.csv", index=True)
custom_stayhome.to_csv("./results/optimize/custom_stayhome.csv", index=True)



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
