import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.load_data import load_data
from pyfrbus.custom_plot import custom_plot
import numpy as np
import matplotlib.pyplot as plt
from typing import List


class sm_frbus():
    def __init__(self, start="2019Q4", end="2023Q4",
                 no_pandemic=None, no_stayhome=None,
                 model_path="../models/model.xml", data_path="../data/HISTDATA.TXT",
                 verbose=False # False, partial, or full
                 ):
        self.data = load_data("/home/mlq/fed model/pyfrbus/data/HISTDATA.TXT")
        self.model = Frbus("/home/mlq/fed model/pyfrbus/models/model.xml")
        self.verbose = verbose
        self.start = start
        self.end = end
        # self.real_stayhome = 8 # weeks that the stay-at-home orders is in effect in real life
        self.variables = pd.read_csv("/home/mlq/fed model/pyfrbus/demos/model architecture/model_variables_simple.csv")
        self.dynamic_variables = self.variables[(self.variables["sector"] == "Labor Market") | (self.variables["sector"] == "Household Expenditures")
                            | (self.variables["sector"] == "Aggregate Output Identities")].name
        self.const_variables = self.variables[(self.variables["sector"] == "Foreign Activity") 
                            | (self.variables["sector"] == "Foreign Trade")
                            | (self.variables["sector"] == "Government")
                            ].name

        self.loss_df = None
        self.control = None 
        self.no_pandemic = self.solve_no_pandemic()
        self.no_stayhome = self.solve_no_stayhome()
        self.stayhome_anticipated_errors = self.cal_stayhome_anticipated_errors()
        self.custom_stayhome = None
    def solve_no_pandemic(self):
        """
        Solve the model for the no pandemic scenario
        """
        if self.verbose!=False:
            print("Solving for no pandemic scenario...")
        result = self.model.solve(self.start, self.end, self.data)
        return result

    def trac_const_variables(self):
        targ_trac_const, traj_trac_const, inst_trac_const = [], [], []
        data_trac_const = self.no_stayhome.copy(deep=True)
        for name in self.const_variables:
            try:
                data_trac_const.loc[self.start:self.end, f"{name}_t"] = self.data.loc[self.start:self.end, name]
                targ_trac_const.append(name)
                traj_trac_const.append(f"{name}_t")
                inst_trac_const.append(name)
            except Exception as e:
                print(f"Can't create trajectory for variable '{name}', exception message: {e}")
        return data_trac_const, targ_trac_const, traj_trac_const, inst_trac_const

    def trac_non_dynamic_variables(self):
        dummy = self.model.init_trac(self.start, self.end, self.data)
        for name in self.dynamic_variables:
            try:
                dummy[f"{name}_trac"] = np.zeros(len(self.data))
                # dummy.loc[self.start:start:end, f"{name}_trac"] =  np.zeros(len(self.data)-(pd.Period(self.end)-pd.Period(self.start)))
                pass
            except Exception as e:
                if self.verbose == "full":
                    print(f"Can't untrac dynamic variable '{name}', exception message: {e}")

        return dummy

    def week_to_quarter(self, week):
        # Create a date range starting from the beginning of 2020
        date_range = pd.date_range(start='2020-01-01', periods=week, freq='W')
        # Get the last date in the range
        end_date = date_range[-1]
        return end_date.to_period('Q')

    def calculate_weekly_values(self, start_value_leh, bool_values, decrease_rate=0.019):
        # Convert bool_values to numpy array
        bool_values = np.array(bool_values)        
        # Calculate weekly values for leh
        weekly_values_leh = start_value_leh * np.cumprod(1 - decrease_rate * bool_values)    
        # Return the weekly values
        return weekly_values_leh

    def calculate_quarterly_average(self, start_value_leh, start_week, duration, decrease_rate=0.019):
        start_value_leh = start_value_leh
        # Create a boolean array with 1s for the duration and 0s for the rest
        bool_values = np.zeros(start_week + duration)
        bool_values[start_week:start_week+duration] = 1
          
        # Calculate weekly values
        weekly_values_leh = self.calculate_weekly_values(start_value_leh, bool_values, decrease_rate)

        # Fill the missing weeks for the quarter with the last calculated value
        if (start_week + duration) % 13 != 0:
            end_week = ((start_week + duration) // 13 + 1) * 13
            last_calculated_value = weekly_values_leh[start_week + duration - 1]
            for i in range(1, end_week - (start_week + duration)+1):
                weekly_values_leh = np.append(weekly_values_leh , (weekly_values_leh[start_week + duration - i-1]))


        # Convert weekly values to Series
        series_leh = pd.Series(weekly_values_leh)

        # Create a date range for the series index
        dates = pd.date_range(start='2020-01-01', periods=len(series_leh), freq='W')

        # Assign dates to series index
        series_leh.index = dates

        # Convert the index to PeriodIndex with quarterly frequency
        series_leh.index = series_leh.index.to_period('Q')

        # Resample the series to quarterly frequency and calculate mean
        quarterly_avg_leh = series_leh.groupby(series_leh.index).mean()


        delta_leh = pd.concat([pd.Series(start_value_leh), quarterly_avg_leh])
        delta_leh = delta_leh.diff().dropna()

        # print("\n\nquarter leh", quarterly_avg_leh)
        # print("\ndelta", delta_leh)

        # Return the quarterly averages and weekly series for verification
        return quarterly_avg_leh, delta_leh, start_value_leh

    def solve_no_stayhome(self, start_stayhome_week=12, duration=6):
        if self.verbose!=False:
            print("Creating no stay-at-home orders scenario...")

        start_quarter = self.week_to_quarter(start_stayhome_week) 
        end_quarter = self.week_to_quarter(start_stayhome_week + duration)

        targ_no_stayhome, traj_no_stayhome, inst_no_stayhome = [], [], []

        no_stayhome_data = self.trac_non_dynamic_variables()
        # # Adjust unemployment rates for stay-at-home orders


        expected_leh_by_stayhome, delta_leh,_ = self.calculate_quarterly_average(start_value_leh = self.data.loc[start_quarter-1, 'leh'], start_week = start_stayhome_week, duration = duration)


        no_stayhome_data.loc[start_quarter:end_quarter, "leh_t"] = self.data.loc[start_quarter:end_quarter, 'leh'] - (delta_leh)


        no_stayhome_data.loc[end_quarter+1:self.end , "leh_t"] = self.data.loc[end_quarter+1:self.end, 'leh']
        # Update target and trajectory lists
        targ_no_stayhome += ['leh', ]
        traj_no_stayhome += ['leh_t',]
        inst_no_stayhome += ['leh', ]

        # Run mcontrol to match the target variables to their trajectories
        no_stayhome_result = self.model.mcontrol(start_quarter, end_quarter, no_stayhome_data, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)
        no_stayhome_result = self.model.solve(end_quarter+1, self.end, no_stayhome_result)
        # no_stayhome_result = self.model.mcontrol(end_stayhome+1, self.end, no_stayhome_result, targ_no_stayhome, traj_no_stayhome, inst_no_stayhome)

        return no_stayhome_result

    def cal_stayhome_anticipated_errors(self, start_stayhome_week=12, duration=6, end_stayhome=pd.Period("2020Q2")):
        if self.no_stayhome is None:
            raise Exception("No stayhome scenario has been solved yet. Please run solve_no_stayhome() first.")
        stayhome_aerr_data = self.no_stayhome.copy(deep=True)

        start_stayhome = self.week_to_quarter(start_stayhome_week) 
        end_stayhome = self.week_to_quarter(start_stayhome_week + duration)

        # stayhome_aerr_data.loc[start_stayhome:end_stayhome, "leh_t"] = (stayhome_aerr_data.loc[start_stayhome:end_stayhome, 'leh'] + 
        #  self.calculate_quarterly_average(start_value_leh = stayhome_aerr_data.loc[start_stayhome-1, 'leh'], start_week = start_stayhome_week, duration = duration)[1])
        
        stayhome_aerr_data.loc[start_stayhome:end_stayhome, "leh_t"] = ( 
         self.calculate_quarterly_average(start_value_leh = stayhome_aerr_data.loc[start_stayhome-1, 'leh'], start_week = start_stayhome_week, duration = duration)[0])

        stayhome_aerr = self.model.mcontrol(start_stayhome, end_stayhome, stayhome_aerr_data, ['leh'], ['leh_t'], ['leh'])
        stayhome_aerr = self.model.solve(end_stayhome+1, self.end, stayhome_aerr)

        control = stayhome_aerr.copy(deep=True)

        # Calculate errors for each variable
        for name in self.variables['name']:
            try:
                stayhome_aerr.loc[self.start:self.end, f"{name}_aerr"] = self.data.loc[self.start:self.end, name] - stayhome_aerr.loc[self.start:self.end, name]
                control.loc[self.start:self.end, f"{name}"] += stayhome_aerr.loc[self.start:self.end, f"{name}_aerr"]
            except Exception as e:
                if self.verbose == "full":
                    print(f"Can't calculate anticipated error for variable '{name}', exception message: {e}")

        self.control = control

        return stayhome_aerr

    def solve_custom_stayhome(self, start_lockdown_opt=12, custom_lockdown_duration=17,
                             targ_custom=None, traj_custom=None, inst_custom=None, custom_stayhome_data=None):
        if self.verbose!=False:
            print("Creating custom stay-at-home orders scenario...")
        if not targ_custom or not traj_custom or not inst_custom:
            print("No custom targets, trajectories and instruments provided. Using default empty values.")
            targ_custom, traj_custom, inst_custom = [], [], []

        # print("\n", start_lockdown_opt,"\n")
        end_lockdown_quarter = self.week_to_quarter(start_lockdown_opt + custom_lockdown_duration)        
        start_lockdown_quarter = self.week_to_quarter(start_lockdown_opt)
        # print("\n", end_lockdown_quarter,"\n")
        
        targ_custom += ['leh',]
        traj_custom += ['leh_t', ]
        inst_custom += ['leh_aerr',]

        if custom_stayhome_data is None:
            print("No custom stayhome data provided. Using default values.")
            if self.no_stayhome is None:
                raise Exception("No stayhome scenario has been solved yet. Please run solve_no_stayhome() first.")
            custom_stayhome_data = self.no_stayhome.copy(deep=True)

        # custom_stayhome_data.loc[start_lockdown_quarter:end_lockdown_quarter, "leh_t"] = (custom_stayhome_data.loc[start_lockdown_quarter:end_lockdown_quarter, 'leh'] + 
        #  self.calculate_quarterly_average(start_value_leh = custom_stayhome_data.loc[start_lockdown_quarter-1, 'leh'], start_week = start_lockdown_opt, duration = custom_lockdown_duration)[1])

        custom_stayhome_data.loc[start_lockdown_quarter:end_lockdown_quarter, "leh_t"] = (
         self.calculate_quarterly_average(start_value_leh = custom_stayhome_data.loc[start_lockdown_quarter-1, 'leh'], start_week = start_lockdown_opt, duration = custom_lockdown_duration)[0])


        # print("\n\n", custom_stayhome_data.loc[start_lockdown_quarter:end_lockdown_quarter, "leh_t"], "\n\n")

        custom_stayhome = self.model.mcontrol(start_lockdown_quarter, end_lockdown_quarter, custom_stayhome_data, targ_custom, traj_custom, inst_custom, {'maxit':5000})
        custom_stayhome = self.model.solve(end_lockdown_quarter+1, self.end, custom_stayhome, {'maxit':1000})

        # Apply anticipated errors
        for name in self.variables['name']:
            try:
                custom_stayhome[name] += self.stayhome_anticipated_errors[f"{name}_aerr"]
            except Exception as e:
                if self.verbose:
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
        df_quarter.index = pd.period_range(start=pd.Period('2020Q1'), periods=len(df_quarter), freq='Q') # Set the index to quarters to match the FRB/US model

        targ_custom = ['ec', 'lhp']
        traj_custom = ['ec_t', 'lhp_t']
        inst_custom = ['ec', 'lhp'] 

        if self.no_stayhome is None:
            raise Exception("No stayhome scenario has been solved yet. Please run solve_no_stayhome() first.")
        custom_stayhome_data = self.no_stayhome.copy(deep=True)

        custom_stayhome_data.loc["2020Q1":"2023Q4", "ec_t"] = custom_stayhome_data.loc["2020Q1":"2023Q4", "ec"] * (1+df_quarter['C_dev'])
        custom_stayhome_data.loc["2020Q1":"2023Q4", "lhp_t"] = custom_stayhome_data.loc["2020Q1":"2023Q4", "lhp"] * (1+df_quarter['N_dev'])


        return custom_stayhome_data, targ_custom, traj_custom, inst_custom

    def loss_econ(self):
        if self.custom_stayhome is None:
            raise Exception("No custom stayhome scenario has been solved yet. Please run solve_custom_stayhome() first.")
        # xgdpn = GDP, current $ is in the thousands (10^3), fit with https://data.worldbank.org/indicator/NY.GDP.MKTP.CD?locations=US
        # trillion dollars = 10^12 dollars
        self.loss_df = (self.custom_stayhome['xgdp'] - self.no_stayhome['xgdp']) * (10**9)
        return (self.custom_stayhome['xgdp'] - self.no_stayhome['xgdp']).sum() * (10**9)/4 # avg gdp loss per year

    def save_results(self, path="./results/dynamic_labor_consumption/"):
        if self.no_pandemic is None or self.no_stayhome is None or self.custom_stayhome is None:
            raise Exception("No scenarios have been solved yet. Please run solve_no_pandemic(), solve_no_stayhome() and solve_custom_stayhome() first.")
        self.no_pandemic.to_csv(f"{path}no_pandemic.csv", index=True)
        self.no_stayhome.to_csv(f"{path}no_stayhome.csv", index=True)
        self.custom_stayhome.to_csv(f"{path}custom_stayhome.csv", index)

    def plot_results(self):
        # Generate plots
        dfs = {
            #  'baseline': self.data,
             'no_stayhome': self.no_stayhome,
             'custom_stayhome': self.custom_stayhome,
            #  'no_pandemic': self.no_pandemic,
            #  'control': self.control
             }

        plots = [
            {'column': 'xgdp', 'type': 'value'},
            {'column': 'pcxfe', 'type': 'pct_change', 'name': 'PCE Price Index'},
            {'column': 'ec', 'name': 'Consumption, cw 2012$'},
            {'column': 'pcpi', 'type': 'pct_change', 'name': 'CPI'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, '/home/mlq/fed model/pyfrbus/demos/results/dynamic_labor_consumption/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

        plots = [
            {'column': 'lprdt'},
            {'column': 'lhp', 'name': 'Agg. labor hours, business sector'},
            {'column': 'lww', 'name': 'Workweek, business sector'},
            {'column': 'lqualt'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, '/home/mlq/fed model/pyfrbus/demos/results/dynamic_labor_consumption/labor quality.png', plot_title='No April lockdown + same foreign variables')

        plots = [
            {'column': 'leg', 'name': 'Gov. civilian employment'},
            {'column': 'lur', 'name': 'Unemployment Rate'},
            {'column': 'lurnat'},
            {'column': 'leh'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, '/home/mlq/fed model/pyfrbus/demos/results/dynamic_labor_consumption/(un)employment.png', plot_title='No April lockdown + same foreign variables')

        plots = [
            {'column': 'ex', 'name': 'Export, cw 2012$'},
            {'column': 'em', 'name': 'Import, cw 2012$'},
            {'column': 'fpic', 'name': 'Foreign CPI (G39)'},
            {'column': 'fgdp', 'name': 'Foreign GDP (G39)'}
        ]
        custom_plot(dfs, '2020Q1', '2023Q4', plots, self.variables, '/home/mlq/fed model/pyfrbus/demos/results/dynamic_labor_consumption/export+import.png', plot_title='No April lockdown + same foreign variables')


def main():
    # no-stayhome scenario
    obj2 = sm_frbus()
    obj2.solve_custom_stayhome(start_lockdown_opt=1, custom_lockdown_duration=1)
    loss2 = obj2.loss_econ()

    # optimal stayhome scenario
    obj3 = sm_frbus() 
    obj3.solve_custom_stayhome(start_lockdown_opt=5, custom_lockdown_duration=12)
    loss3 = obj3.loss_econ() 
    obj3.plot_results()


    fig, ax = plt.subplots(2, 1, figsize=(13, 12))
    plt.subplots_adjust(top=0.95, bottom=0.05, left=0.1, right=0.95, hspace=.15)


    x = obj3.custom_stayhome.tail(18).index.astype(str)
    y0 = (obj3.custom_stayhome.tail(18)["xgdp"].values - obj2.no_stayhome.tail(18)['xgdp'].values)/(10**3)
    ax[0].plot(x, y0, marker='o', label="Optimal SAH", color='firebrick', alpha=0.8)
    ax[0].set_title('GDP Compared to no SAH')
    ax[0].set_ylabel('GDP Loss (in Trillion USD)')

    y1 = (obj3.custom_stayhome.tail(18)["leh"].values - obj2.no_stayhome.tail(18)['leh'].values)
    ax[1].plot(x, y1, marker='o', label="Optimal SAH", color='coral', alpha=0.8)
    ax[1].set_title('Civilian Employment Compared to no SAH')
    ax[1].set_ylabel('Civilian Employment Loss (in Million)')



    for i in range(2):
        ax[i].set_facecolor('aliceblue')
        ax[i].spines['top'].set_visible(False)
        ax[i].spines['right'].set_visible(False)
        ax[i].axhline(y=0, color='grey', linestyle='--')
        ax[i].grid(color='lightgray', linestyle='-', linewidth=0.5)
        ax[i].yaxis.grid(True)
        ax[i].xaxis.grid(False)
        ax[i].legend()

    plt.tight_layout(h_pad=2)
    plt.show()
    plt.savefig("econ_SAH_5_12.png")


if __name__ == "__main__":
    main()