import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def custom_plot(baseline: pd.DataFrame, sim: pd.DataFrame, start: str, end: str,
         plots: list, variables: pd.DataFrame, file_name = './png/plot.png', plot_title = 'US Economic Simulation'):
    # Pad with 25% history but not more than 6 or less than 2 qtrs
    back_pad = max(min(round((pd.Period(end) - pd.Period(start)).n / 4), 6), 2)
    plot_period = pd.period_range(pd.Period(start) - back_pad, end, freq="Q")
    
    num_plots = len(plots)
    num_rows = int(num_plots**0.5)
    num_cols = num_plots // num_rows + (num_plots % num_rows > 0)
    
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=(7, 7))
    axes = axes.flatten()  # Flatten the array in case of more than one row and column
    
    for i, plot in enumerate(plots):
        column = plot.get('column')
        type = plot.get('type', 'value')
        subplot_name = plot.get('name')  # Get the subplot name from the plot dictionary
        
        if column not in baseline.columns or column not in sim.columns:
            print(f"Column '{column}' does not exist in one of the DataFrames.")
            continue
        if type not in ['value', 'pct_change']:
            print(f"Invalid type '{type}'. Type must be either 'value' or 'pct_change'.")
            continue
        
        if type == 'pct_change':
            baseline_data = baseline[column].pct_change(4) * 100
            baseline_data = baseline_data[plot_period]
            sim_data = sim[column].pct_change(4) * 100
            sim_data = sim_data[plot_period]
            title = ('pct_change ' + variables[variables.name == column].definition.values[0]) if column in variables.name.values else column
        else:
            baseline_data = baseline.loc[plot_period, column]
            sim_data = sim.loc[plot_period, column]
            title = (variables[variables.name == column].definition.values[0]) if column in variables.name.values else column
            
        # Convert the PeriodIndex to datetime
        baseline_data.index = baseline_data.index.strftime('%yQ%q')
        sim_data.index = sim_data.index.strftime('%yQ%q')
        
        # If the subplot name is provided, use it as the title
        if subplot_name is not None:
            title = subplot_name

        # If the title is too long, set it to the column name
        if len(title) > 50:
            print(f"Title '{title}' is too long. Setting title to default.")
            title = 'pct_change ' + column if 'pct_change' in title else column
        
        axes[i].plot(baseline_data, label='Baseline')
        axes[i].plot(sim_data, label='Simulation', linestyle='--')
        axes[i].set_title(title)
        axes[i].legend()
        
        # Set xticks to only include one tick per year, up to a maximum of 12 ticks
        years = np.unique(baseline_data.index.str[:-2])  # Get the unique years
        if len(years) > 12:
            years = years[::len(years)//12]  # If there are more than 12 years, select years to have 12 evenly spaced ticks
        xticks = [np.where(baseline_data.index.str[:-2] == year)[0][0] for year in years]  # Get the index of the first occurrence of each year
        xticklabels = baseline_data.index[xticks]  # Get the corresponding labels
        axes[i].set_xticks(xticks)
        axes[i].set_xticklabels(xticklabels, rotation=45)
        
        # Show the xgrid
        axes[i].xaxis.grid(True)

    fig.suptitle(plot_title)
    plt.tight_layout()
    plt.savefig(file_name)
    plt.show()

"""
example usage:

import pandas as pd

# Load the baseline data from the provided text file
# Adjusting the separator to comma (',') since the data is comma-separated
baseline_df = pd.read_csv('./fed model/data_only_package/HISTDATA.TXT', sep=',', index_col=0)
baseline_df.columns = baseline_df.columns.str.lower()
baseline_df.index = pd.PeriodIndex(baseline_df.index, freq='Q')

variables = pd.read_csv('model_variables_simple.csv')
foreign_const = pd.read_csv('foreign_const.csv', index_col=0)
foreign_const.index = pd.PeriodIndex(foreign_const.index, freq='Q')

plots = [{'column': 'xgdp', 'type': 'pct_change'},
        {'column': 'pcxfe', 'type': 'pct_change', 'name':'PCE Price Index'}, 
        {'column': 'xgdpn',  
        {'column': 'pcpi', ]

custom_plot(baseline_df, foreign_const_sim, '2020Q1', '2023Q4', plots, variables, './png/foreign const/gdp+inflation.png', plot_title='No April lockdown + same foreign variables')

"""
