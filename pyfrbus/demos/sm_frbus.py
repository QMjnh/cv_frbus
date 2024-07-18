import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
from pyfrbus.custom_plot import custom_plot
import numpy as np

class sm_frbus():
    def __init__(self, start="2019Q4", end="2023Q4",
                 no_pandemic=None, no_stayhome=None,
                 model_path="../models/model.xml", data_path="../data/HISTDATA.TXT"):
        self.data = load_data("../data/HISTDATA.TXT")
        self.model = Frbus("../models/model.xml")
        self.start = start
        self.end = end
        self.variables = pd.read_csv("./model architecture/model_variables_simple.csv")
        self.dynamic_variables = self.variables[(self.variables["sector"] == "Labor Market") | (self.variables["sector"] == "Household Expenditures")
                            | (self.variables["sector"] == "Aggregate Output Identities")].name

        self.no_pandemic = self.solve_no_pandemic()
        self.no_stayhome = self.solve_no_stayhome()
        self.stayhome_anticipated_errors = self.cal_stayhome_anticipated_errors()
        self.custom_stayhome = None

    def solve_no_pandemic(self):
        print("Solving for no pandemic scenario...")
        result = self.model.solve(self.start, self.end, self.data)
        return result

    def trac_non_dynamic_variables(self):
        dummy = self.model.init_trac(self.start, self.end, self.data)
        for name in self.dynamic_variables:
            try:
                dummy[f"{name}_trac"] = np.zeros(len(self.data))
            except Exception as e:
                print(f"Can't untrac dynamic variable '{name}', exception message: {e}")

        return dummy

    def solve_no_stayhome(self, stay_home_total=17, start_stayhome="2020Q2", end_stayhome="2020Q2"):
        print("Creating no stay-at-home orders scenario...")
        stay_home_total = stay_home_total  # weeks
        start_stayhome = start_stayhome
        end_stayhome = end_stayhome
        targ_no_stayhome, traj_no_stayhome, inst_no_stayhome = [], [], []

        no_stayhome_data = self.trac_non_dynamic_variables()
        # Adjust unemployment rates for stay-at-home orders
        no_stayhome_data.loc[start_stayhome:end_stayhome, "lurnat_t"] = self.data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1 - .019)**stay_home_total
        no_stayhome_data.loc[start_stayhome:end_stayhome, "lur_t"] = self.data.loc[start_stayhome:end_stayhome, 'lur'] * (1 - .019)**stay_home_total
        # Update target and trajectory lists
        targ_no_stayhome += ['lur', 'lurnat']
        traj_no_stayhome += ['lur_t', 'lurnat_t']
        inst_no_stayhome += ['lur', 'lurnat']

        # Run mcontrol to match the target variables to their trajectories
        no_stayhome_result = self.model.mcontrol(self.start, self.end, no_stayhome_data, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)
        no_stayhome_result = self.model.solve(self.start, self.end, no_stayhome_result)
        no_stayhome_result = self.model.mcontrol(self.start, self.end, no_stayhome_result, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

        return no_stayhome_result

    def cal_stayhome_anticipated_errors(self, stay_home_total=17, start_stayhome="2020Q2", end_stayhome="2020Q2"):
        if self.no_stayhome is None:
            raise Exception("No stayhome scenario has been solved yet. Please run solve_no_stayhome() first.")
        stayhome_aerr_data = self.no_stayhome.copy(deep=True)

        stayhome_aerr_data.loc[start_stayhome:end_stayhome, "lur_t"] = stayhome_aerr_data.loc[start_stayhome:end_stayhome, 'lur'] * (1.019**stay_home_total)
        stayhome_aerr_data.loc[start_stayhome:end_stayhome, "lurnat_t"] = stayhome_aerr_data.loc[start_stayhome:end_stayhome, 'lurnat'] * (1.019**stay_home_total)

        stayhome_aerr = self.model.mcontrol(start_stayhome, end_stayhome, stayhome_aerr_data, ['lur', 'lurnat'], ['lur_t', 'lurnat_t'], ['lur', 'lurnat'])
        stayhome_aerr = self.model.solve(end_stayhome, self.end, stayhome_aerr)
        stayhome_aerr = self.model.mcontrol(end_stayhome, self.end, stayhome_aerr, ['lur', 'lurnat'], ['lur_t', 'lurnat_t'], ['lur', 'lurnat'])

        # Calculate errors for each variable
        for name in self.variables['name']:
            try:
                stayhome_aerr.loc[self.start:self.end, f"{name}_aerr"] = self.data.loc[self.start:self.end, name] - stayhome_aerr.loc[self.start:self.end, name]
            except Exception as e:
                print(f"Can't calculate anticipated error for variable '{name}', exception message: {e}")

        return stayhome_aerr

    def solve_custom_stayhome(self, start_lockdown_opt="2020Q2", end_lockdown_opt="2020Q2", custom_lockdown_duration=17,
                             targ_custom=None, traj_custom=None, inst_custom=None, custom_stayhome_data=None):
        if not targ_custom or not traj_custom or not inst_custom:
            print("No custom targets, trajectories and instruments provided. Using default empty values.")
            targ_custom, traj_custom, inst_custom = [], [], []

        targ_custom += ['lur', 'lurnat']
        traj_custom += ['lur_t', 'lurnat_t']
        inst_custom += ['lur', 'lurnat']

        print("traj",traj_custom)

        if custom_stayhome_data is None:
            print("No custom stayhome data provided. Using default values.")
            if self.no_stayhome is None:
                raise Exception("No stayhome scenario has been solved yet. Please run solve_no_stayhome() first.")
            custom_stayhome_data = self.no_stayhome.copy(deep=True)

        custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, "lur_t"] = custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, 'lur'] * (1.019**custom_lockdown_duration)
        custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, "lurnat_t"] = custom_stayhome_data.loc[start_lockdown_opt:end_lockdown_opt, 'lurnat'] * (1.019**custom_lockdown_duration)

        custom_stayhome = self.model.mcontrol(start_lockdown_opt, end_lockdown_opt, custom_stayhome_data, targ_custom, traj_custom, inst_custom)
        custom_stayhome = self.model.solve(end_lockdown_opt, self.end, custom_stayhome)
        # custom_stayhome = self.model.mcontrol(end_lockdown_opt, self.end, custom_stayhome, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)
        custom_stayhome = self.model.mcontrol(start_lockdown_opt, end_lockdown_opt, custom_stayhome_data, targ_custom, traj_custom, inst_custom)

        # Apply anticipated errors
        for name in self.variables['name']:
            try:
                custom_stayhome[name] += self.stayhome_anticipated_errors[f"{name}_aerr"]
            except Exception as e:
                print(f"Can't calculate anticipated error for variable '{name}', exception message: {e}")

        self.custom_stayhome = custom_stayhome
        return custom_stayhome

    def link_sm_frbus(self, df):
        """
        Link the effects of the stay-at-home order on Consumption and Labor Hours modelled by SIR-MACRO to the FRB/US model
        ec: Consumption, cw 2012$ (FRB/US definition)
        lhp: Aggregate labor hours,  business sector (employee and  self-employed)
        """
        # Define the number of rows to group
        group_size = 13 # weeks in a quarter
        # Create a new column 'group' that assigns each row to a group
        df['group'] = df.index // group_size
        # Calculate the mean of each group
        df_quarter = df.groupby('group').mean()
        df_quarter.index = pd.period_range(start='2020Q1', periods=len(df_quarter), freq='Q') # Set the index to quarters to match the FRB/US model

        targ_custom = ['ec', 'lhp']
        traj_custom = ['ec_t', 'lhp_t']
        inst_custom = ['ec', 'lhp'] 

        if self.no_stayhome is None:
            raise Exception("No stayhome scenario has been solved yet. Please run solve_no_stayhome() first.")
        custom_stayhome_data = self.no_stayhome.copy(deep=True)

        custom_stayhome_data.loc["2020Q1":"2023Q4", "ec_t"] = custom_stayhome_data.loc["2020Q1":"2023Q4", "ec"] * (1+df_quarter['C_dev'])
        custom_stayhome_data.loc["2020Q1":"2023Q4", "lhp_t"] = custom_stayhome_data.loc["2020Q1":"2023Q4", "lhp"] * (1+df_quarter['N_dev'])


        return custom_stayhome_data, targ_custom, traj_custom, inst_custom

    def save_results(self, path="./results/dynamic_labor_consumption/"):
        if self.no_pandemic is None or self.no_stayhome is None or self.custom_stayhome is None:
            raise Exception("No scenarios have been solved yet. Please run solve_no_pandemic(), solve_no_stayhome() and solve_custom_stayhome() first.")
        self.no_pandemic.to_csv(f"{path}no_pandemic.csv", index=True)
        self.no_stayhome.to_csv(f"{path}no_stayhome.csv", index=True)
        self.custom_stayhome.to_csv(f"{path}custom_stayhome.csv", index)

    def plot_results(self):
        # Generate plots
        dfs = {'baseline': self.data, 'custom_stayhome': self.custom_stayhome, 'no_stayhome': self.no_stayhome, 'no_pandemic': self.no_pandemic}

        plots = [
            {'column': 'xgdp', 'type': 'pct_change'},
            {'column': 'pcxfe', 'type': 'pct_change', 'name': 'PCE Price Index'},
            {'column': 'ec', 'name': 'Consumption, cw 2012$'},
            {'column': 'pcpi', 'type': 'pct_change', 'name': 'CPI'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, './results/dynamic_labor_consumption/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

        plots = [
            {'column': 'lprdt'},
            {'column': 'lhp', 'name': 'Agg. labor hours, business sector'},
            {'column': 'lww', 'name': 'Workweek, business sector'},
            {'column': 'lqualt'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, './results/dynamic_labor_consumption/labor quality.png', plot_title='No April lockdown + same foreign variables')

        plots = [
            {'column': 'leg', 'name': 'Gov. civilian employment'},
            {'column': 'lur', 'name': 'Unemployment Rate'},
            {'column': 'lurnat'},
            {'column': 'leh'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, './results/dynamic_labor_consumption/(un)employment.png', plot_title='No April lockdown + same foreign variables')

        plots = [
            {'column': 'ex', 'name': 'Export, cw 2012$'},
            {'column': 'em', 'name': 'Import, cw 2012$'},
            {'column': 'fpic', 'name': 'Foreign CPI (G39)'},
            {'column': 'fgdp', 'name': 'Foreign GDP (G39)'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, './results/dynamic_labor_consumption/export+import.png', plot_title='No April lockdown + same foreign variables')



obj = sm_frbus()
sm_df = pd.read_csv("../../sir-macro/csv/td2.csv")
custom_stayhome_data, targ_custom, traj_custom, inst_custom = obj.link_sm_frbus(sm_df)
obj.solve_custom_stayhome(start_lockdown_opt="2020Q2", end_lockdown_opt="2020Q2", custom_lockdown_duration=17,
                             custom_stayhome_data=custom_stayhome_data,
                             targ_custom=targ_custom, traj_custom=traj_custom, inst_custom=inst_custom)

obj.plot_results()