import numpy as np
import pandas as pd
import covasim as cv
import sciris as sc
from datetime import datetime

pop = 331_000_000
df = pd.read_csv('/home/mlq/fed model/covasim/United States Vax.csv')

df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year
# df = df.groupby(['month', 'year'])[['people_vaccinated', 'total_vaccinations', 'people_fully_vaccinated', 'total_boosters']].last()/pop
df = df.groupby('year')[['people_vaccinated', 'total_vaccinations', 'people_fully_vaccinated', 'total_boosters']].last()/pop
df['delta_total_vax'] = df['total_vaccinations'].diff().fillna(df['total_vaccinations'])
df['delta_people_vax'] = df['people_vaccinated'].diff().fillna(df['people_vaccinated'])
df['delta_people_fully_vax'] = df['people_fully_vaccinated'].diff().fillna(df['people_fully_vaccinated'])

print(df)

# Assuming your DataFrame is called 'df'

pars = dict(
    pop_size = 1_000_000,
    start_day = '2020-01-31',
    end_day = '2023-12-31',
    pop_type = 'hybrid',
    location = 'usa',
    pop_infected = 1,
    beta = 0.13,
    rel_death_prob = 2.67,
)

# def estimate_daily_prob(coverage, duration):
#     if coverage <= 0 or coverage >= 1:
#         return 0  # Edge cases
#     p = 1 - (1 - coverage) ** (1 / duration)
#     return p

# def create_vaccination_campaign(row, sim_start_date, pop=331_000_000):
#     # Convert the index to a datetime
#     date = pd.to_datetime(f"{row.name[1]}-{row.name[0]}-01")
    
#     # Calculate the monthly coverage
#     monthly_coverage = row['people_vaccinated'] / pop
    
#     # Estimate the daily vaccination probability
#     daily_prob = estimate_daily_prob(monthly_coverage, duration=30)

#     print(date, daily_prob)
    
#     # Calculate days since simulation start
#     days = [(date + pd.Timedelta(days=i) - sim_start_date).days for i in range(30)]
    
#     # Create a 30-day campaign starting from the date
#     campaign = cv.historical_vaccinate_prob(
#         vaccine='default',
#         days=days,
#         prob=daily_prob
#     )
    
#     return campaign

# # Convert start_day to datetime
# sim_start_date = pd.to_datetime(pars['start_day'])

# # Create vaccination campaigns for each row
# vaccination_campaigns = df.apply(create_vaccination_campaign, axis=1, args=(sim_start_date,)).tolist()
# print(len(vaccination_campaigns))

# # Define other interventions
# lockdown = cv.change_beta(days=['2020-03-24', '2020-05-04'], changes=[0.5, 1.0])
# test = cv.test_prob(symp_prob=0.2, asymp_prob=0.001, start_day='2020-01-31')
# ct = cv.contact_tracing(trace_probs=dict(h=1.0, s=0.5, w=0.5, c=0.3), do_plot=False)

# # Combine all interventions
# all_interventions = [lockdown, test, ct] + vaccination_campaigns

# # Create and run the simulation
# sim = cv.Sim(pars, interventions=all_interventions, label='With all interventions')
# sim.run()

# # You can now analyze the results
# results = sim.results






# def create_bimonthly_vaccination_campaign(group, sim_start_date, pop=331_000_000):
#     # Get the first month and year of the two-month period
#     month, year = group.index[0]
#     date = pd.to_datetime(f"{year}-{month:02d}-01")
    
#     # Calculate the total coverage for the two-month period
#     bimonthly_coverage = group['people_vaccinated'].mean()
    
#     # Calculate days since simulation start
#     days = (date - sim_start_date).days
    
#     # Create a single vaccination event for the two-month period
#     campaign = cv.vaccinate(
#         vaccine='default',
#         days=days,
#         prob=bimonthly_coverage,
#         label=f'Vaccination {date.strftime("%Y-%m")}-{(date + pd.DateOffset(months=1)).strftime("%Y-%m")}'
#     )
    
#     return campaign

# # Convert start_day to datetime
# sim_start_date = pd.to_datetime(pars['start_day'])

# # Group the DataFrame by two-month periods and create vaccination campaigns
# df['two_month_period'] = df.groupby(level='year').cumcount() // 3
# vaccination_campaigns = df.groupby('two_month_period').apply(create_bimonthly_vaccination_campaign, sim_start_date=sim_start_date).tolist()
# print(len(vaccination_campaigns))
# # Define other interventions
# lockdown = cv.change_beta(days=['2020-03-24', '2020-05-04'], changes=[0.5, 1.0])
# test = cv.test_prob(symp_prob=0.2, asymp_prob=0.001, start_day='2020-01-31')
# ct = cv.contact_tracing(trace_probs=dict(h=1.0, s=0.5, w=0.5, c=0.3), do_plot=False)

# # Combine all interventions
# all_interventions = [lockdown, test, ct] + vaccination_campaigns

# # Create and run the simulation
# sim = cv.Sim(pars, interventions=all_interventions, label='With all interventions')
# sim.run()

# # You can now analyze the results
# results = sim.results



def create_vaccination_campaign(sim_start_date, vax_start_date, vax_end_date, vax_pop):    
    # Calculate days since simulation start
    vax_start_date = (vax_start_date - sim_start_date).days
    vax_end_date = (vax_end_date - sim_start_date).days
    
    days = [i for i in range(vax_start_date, vax_end_date)]
    # print(days)
    prob = vax_pop / len(days)
    # print("prob",prob)

    campaign = cv.historical_vaccinate_prob(
        vaccine = 'default',
        days=days,
        prob=prob,
        # label=f'Vaccination {start_date.strftime("%Y-%m")} to {vax_end_date.strftime("%Y-%m")}'
    )  
    return campaign

# Convert start_day to datetime
sim_start_date = pd.to_datetime(pars['start_day'])
# Group the DataFrame by six-month periods and create vaccination campaigns
vax2020 = create_vaccination_campaign(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2020-12-01"), vax_end_date=pd.to_datetime("2020-12-31"), vax_pop=df.loc[2020, 'delta_total_vax'])
vax2021 = create_vaccination_campaign(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2021-01-01"), vax_end_date=pd.to_datetime("2021-12-31"), vax_pop=df.loc[2021, 'delta_total_vax'])
vax2022 = create_vaccination_campaign(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2022-01-01"), vax_end_date=pd.to_datetime("2022-12-31"), vax_pop=df.loc[2022, 'delta_total_vax'])
# vaccinations in 2023 is insignificant: new vaccinations = 2.044498 - 2.014961 = 0.029537% of the population
# vax2023 = create_vaccination_campaign(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2023-01-01"), vax_end_date=pd.to_datetime("2023-12-31"), vax_pop=df.loc[2023, 'delta_total_vax'])

vaccination_campaigns = [vax2020, vax2021, vax2022]

# Define other interventions
lockdown = cv.change_beta(days=['2020-03-24', '2020-05-04'], changes=[0.5, 1.0])
test = cv.test_prob(symp_prob=0.2, asymp_prob=0.001, start_day='2020-01-31')
ct = cv.contact_tracing(trace_probs=dict(h=1.0, s=0.5, w=0.5, c=0.3), do_plot=False)

# Combine all interventions
all_interventions = [lockdown, test, ct] + vaccination_campaigns

# Create and run the simulation
sim = cv.Sim(pars, interventions=all_interventions, label='With all interventions')
sim.run()

# You can now analyze the results
results = sim.results