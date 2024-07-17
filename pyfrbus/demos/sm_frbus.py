import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
from pyfrbus.custom_plot import custom_plot
import numpy as np

class sm_frbus():
    def __init__(self, start=pd.Period("2019Q4"), end=pd.Period("2023Q4")):
        self.data = load_data("../data/HISTDATA.TXT")
        self.model = Frbus("../models/model.xml")
        self.start = start
        self.end = end
        self.variables = pd.read_csv("./model architecture/model_variables_simple.csv")
        self.dynamic_variables = self.variables[(self.variables["sector"] == "Labor Market") | (self.variables["sector"] == "Household Expenditures")
                            | (self.variables["sector"] == "Aggregate Output Identities")].name

        self.no_pandemic = None
        self.no_stayhome = None
        self.custom_stayhome = None

    def solve_no_pandemic(self):
        self.no_pandemic = self.model.solve(self.start, self.end, self.data)

    def trac_non_dynamic_variables(self):
        if not self.no_pandemic:
            print("No pandemic scenario not solved yet.")
            print("Running no pandemic scenario solver now.")
            self.solve_no_pandemic()
        dummy = self.no_pandemic.copy(deep=True)
        dummy = self.model.init_trac(self.start, self.end, dummy)
        for name in self.dynamic_variables:
            try:
                dummy[f"{name}_trac"] = np.zeros(len(self.no_stayhome))
            except Exception as e:
                print(f"Can't untrac dynamic variable '{name}', exception message: {e}")

    def solve_no_stayhome(self, stay_home_total=17, start_stayhome="2020Q2", end_stayhome="2020Q2"):
        stay_home_total = stay_home_total  # weeks
        start_stayhome = start_stayhome
        end_stayhome = end_stayhome
        targ_no_stayhome, traj_no_stayhome, inst_no_stayhome = [], [], []


        self.no_stayhome = self.trac_non_dynamic_variables()
        # Adjust unemployment rates for stay-at-home orders
        self.no_stayhome.loc[start_stayhome:end_stayhome, "lurnat_t"] = self.data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1 - .019)**stay_home_total
        self.no_stayhome.loc[start_stayhome:end_stayhome, "lur_t"] = self.data.loc[start_stayhome:end_stayhome, 'lur'] * (1 - .019)**stay_home_total
        # Update target and trajectory lists
        targ_no_stayhome += ['lur', 'lurnat']
        traj_no_stayhome += ['lur_t', 'lurnat_t']
        inst_no_stayhome += ['lur', 'lurnat']
        # Run mcontrol to match the target variables to their trajectories
        self.no_stayhome = self.model.solve(self.start, self.end, self.no_stayhome)
        self.no_stayhome = self.model.mcontrol(self.start, self.end, self.no_stayhome, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

    def solve(self, start, end, data):
        return data

    def mcontrol(self, start, end, data, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome):
        return data


# Load historical data
data = load_data("../data/HISTDATA.TXT")

# Load FRB/US model
frbus = Frbus("../models/model.xml")

# Define start and end periods
start = "2019Q4"
end = "2023Q4"

############### Solve for no pandemic scenario ###############
no_pandemic = frbus.solve(start, end, data)


############### Create no stay-at-home orders scenario ###############
no_stayhome_data = no_pandemic.copy(deep=True)
no_stayhome_data = frbus.init_trac(start, end, no_stayhome_data)

# Load model variables
variables = pd.read_csv("./model architecture/model_variables_simple.csv")
dynamic_variables = variables[(variables["sector"] == "Labor Market") | (variables["sector"] == "Household Expenditures")
                            | (variables["sector"] == "Aggregate Output Identities")].name

targ_no_stayhome, traj_no_stayhome, inst_no_stayhome = [], [], []

for name in dynamic_variables:
    try:
        no_stayhome_data[f"{name}_trac"] = np.zeros(len(no_stayhome_data))
    except Exception as e:
        print(f"Can't untrac variable '{name}', exception message: {e}")

# Adjust unemployment rates for stay-at-home orders
stay_home_total = 17  # weeks
start_stayhome = "2020Q2"
end_stayhome = "2020Q2"

no_stayhome_data.loc[start_stayhome:end_stayhome, "lurnat_t"] = data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1 - .019)**stay_home_total
no_stayhome_data.loc[start_stayhome:end_stayhome, "lur_t"] = data.loc[start_stayhome:end_stayhome, 'lur'] * (1 - .019)**stay_home_total


# Update target and trajectory lists
targ_no_stayhome += ['lur', 'lurnat']
traj_no_stayhome += ['lur_t', 'lurnat_t']
inst_no_stayhome += ['lur', 'lurnat']


# Run mcontrol to match the target variables to their trajectories
no_stayhome = frbus.mcontrol(start, end, no_stayhome_data, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)
no_stayhome = frbus.solve(start, end, no_stayhome_data)

# Adjust for anticipated errors during stay-at-home period
stayhome_aerr_data = no_stayhome.copy(deep=True)

stayhome_aerr_data.loc[start_stayhome:end_stayhome, "lur_t"] = stayhome_aerr_data.loc[start_stayhome:end_stayhome, 'lur'] * (1.019**stay_home_total)
stayhome_aerr_data.loc[start_stayhome:end_stayhome, "lurnat_t"] = stayhome_aerr_data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1.019**stay_home_total)

stayhome_aerr = frbus.mcontrol(start_stayhome, end_stayhome, stayhome_aerr_data, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)
stayhome_aerr = frbus.solve(end_stayhome, end, stayhome_aerr)
stayhome_aerr = frbus.mcontrol(end_stayhome, end, stayhome_aerr, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

# Calculate errors for each variable
for name in variables['name']:
    try:
        stayhome_aerr.loc[start:end, f"{name}_aerr"] = data.loc[start:end, name] - stayhome_aerr.loc[start:end, name]
    except Exception as e:
        print(f"Can't calculate anticipated error for variable '{name}', exception message: {e}")



############### Custom stay-at-home order scenario ###############
targ_custom, traj_custom, inst_custom = targ_no_stayhome.copy(), traj_no_stayhome.copy(), inst_no_stayhome.copy()

start_lockdown_opt = pd.Period("2020Q2")
end_lockdown_opt = pd.Period("2020Q2")
custom_lockdown_duration = 17  # weeks

custom_stayhome_data = no_stayhome.copy(deep=True)

custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, "lur_t"] = custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, 'lur'] * (1.019**custom_lockdown_duration)
custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, "lurnat_t"] = custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, 'lurnat'] * (1.019**custom_lockdown_duration)

custom_stayhome = frbus.mcontrol(start_lockdown_opt, end_lockdown_opt, custom_stayhome_data, targ_custom, traj_custom, inst_custom)
custom_stayhome = frbus.solve(end_lockdown_opt, end, custom_stayhome)
custom_stayhome = frbus.mcontrol(end_lockdown_opt, end, custom_stayhome, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

# Apply anticipated errors
for name in variables['name']:
    try:
        custom_stayhome[name] += stayhome_aerr[f"{name}_aerr"]
    except Exception as e:
        print(f"Can't calculate anticipated error for variable '{name}', exception message: {e}")

# Save results
no_stayhome.to_csv("./results/dynamic_labor_consumption/no_stayhome.csv", index=True)
custom_stayhome.to_csv("./results/dynamic_labor_consumption/custom_stayhome.csv", index=True)

# Generate plots
dfs = {'baseline': data, 'custom_stayhome': custom_stayhome, 'no_stayhome': no_stayhome, 'no_pandemic': no_pandemic}

plots = [
    {'column': 'xgdp', 'type': 'pct_change'},
    {'column': 'pcxfe', 'type': 'pct_change', 'name': 'PCE Price Index'},
    {'column': 'ec', 'name': 'Consumption, cw 2012$'},
    {'column': 'pcpi', 'type': 'pct_change', 'name': 'CPI'}
]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/dynamic_labor_consumption/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

plots = [
    {'column': 'lprdt'},
    {'column': 'lhp', 'name': 'Agg. labor hours, business sector'},
    {'column': 'lww', 'name': 'Workweek, business sector'},
    {'column': 'lqualt'}
]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/dynamic_labor_consumption/labor quality.png', plot_title='No April lockdown + same foreign variables')

plots = [
    {'column': 'leg', 'name': 'Gov. civilian employment'},
    {'column': 'lur', 'name': 'Unemployment Rate'},
    {'column': 'lurnat'},
    {'column': 'leh'}
]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/dynamic_labor_consumption/(un)employment.png', plot_title='No April lockdown + same foreign variables')

plots = [
    {'column': 'ex', 'name': 'Export, cw 2012$'},
    {'column': 'em', 'name': 'Import, cw 2012$'},
    {'column': 'fpic', 'name': 'Foreign CPI (G39)'},
    {'column': 'fgdp', 'name': 'Foreign GDP (G39)'}
]
custom_plot(dfs, '2020Q1', '2023Q4', plots, variables, './results/dynamic_labor_consumption/export+import.png', plot_title='No April lockdown + same foreign variables')
