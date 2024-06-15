import pandas as pd
from pyfrbus.frbus import Frbus
from pyfrbus.sim_lib import sim_plot
from pyfrbus.load_data import load_data

# Load data
data = load_data("../data/HISTDATA.TXT")

# Load model
model = Frbus("../models/model.xml")

# Define the start and end dates for the simulation
start_date = pd.Period('2020Q1')
end_date = start_date + 15  

# Solve the model over the baseline data
sim1 = model.solve(start=start_date, end=end_date, input_data=data)

# Plot the baseline simulation
# sim_plot(data, sim1, start_date, end_date, './png/convoitryout1.png')

# Create a copy of the baseline data for the pandemic scenario
pandemic_scenario = data.copy()

# Apply shocks to the pandemic scenario
# Reduce consumption (c) by 10% in 2020Q2 to 2021Q1
# pandemic_scenario.loc['2020Q2':'2020Q4', 'ex'] *= 0.8

# increase unemployment rate
# pandemic_scenario.loc['2019Q4', 'emptrt'] += 1.2
# pandemic_scenario.loc['2020Q1', 'emptrt'] += 4.2
# pandemic_scenario.loc['2020Q2', 'emptrt'] += 3
# pandemic_scenario.loc['2020Q3', 'emptrt'] += .8

# pandemic_scenario.loc['2020Q1', 'em'] *= .2
# pandemic_scenario.loc['2020Q2', 'em'] *= 0.2
# pandemic_scenario.loc['2020Q3', 'em'] *= 0.2

# pandemic_scenario.loc['2019Q4', 'lur'] += 8

pandemic_scenario.loc['2022Q1', 'lurtrsh'] *= .2
pandemic_scenario.loc['2022Q2', 'lurtrsh'] *= .25
pandemic_scenario.loc['2022Q3', 'lurtrsh'] *= .3
pandemic_scenario.loc['2022Q4', 'lurtrsh'] *= .25

print(data['lurtrsh'][-20:])
print(pandemic_scenario['lurtrsh'][-20:])

# print("exogenous variables", model.exo_names)
# print('endogenonus variables', model.endo_names)


# Solve the model over the pandemic scenario
# try:
sim2 = model.solve(start=start_date, end=end_date, input_data=pandemic_scenario)

# print(sim2['lur'][-20:])

# Plot the pandemic scenario simulation
sim_plot(data, sim2, start_date, end_date, './png/data vs sim2.png')
sim_plot(sim1, sim2, start_date, end_date, './png/convoisim1 vs sim2.png')


# Retrieve and print the results for key indicators
# results_df = model.get_dataframe()

# Print key economic indicators to analyze the impact
# print(results_df[['gdp', 'ur', 'c', 'g']].loc[start_date:end_date])

# except ComputationError as e:
#     print("Computation error in solver:", e)
