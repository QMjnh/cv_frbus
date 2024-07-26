import covasim as cv
import numpy as np
import pandas as pd
import sciris as sc
from datetime import datetime

class Covasim():
    def __init__(self):
        self.orig_sim = None
        self.sim = None
        self.vax_df = pd.read_csv('/home/mlq/fed model/covasim/United States Vax.csv')
        self.start_stayhome = None
        self.duration_stayhome = None
        self.pars = dict(
                pop_size  = 1_000_000,
                start_day = '2020-01-05',
                end_day   = '2023-12-31',
                pop_type  = 'hybrid',
                location = 'usa',
                pop_infected = 100,
                beta           = 0.13,                  
                rel_death_prob = 2.67,                    
            )

    def orig_sim(self):
        orig_sim = cv.Sim(self.pars, label='Baseline')
        # Run simulations:
        orig_sim.run()
        no_interventions = orig_sim.to_df()
        no_interventions.to_csv('no-interventions.csv', index=False)

    def estimate_daily_prob(self, coverage, duration):
        if coverage <= 0 or coverage >= 1:
            return 0  # Edge cases
        p = 1 - (1 - coverage) ** (1 / duration)
        return p

    def create_vaccination_campaign_precise(self, row, sim_start_date, us_pop=331_000_000):
        # Convert the index to a datetime
        date = pd.to_datetime(f"{row.name[1]}-{row.name[0]}-01")
        
        # Calculate the monthly coverage
        monthly_coverage = row['people_vaccinated'] / us_pop
        
        # Estimate the daily vaccination probability
        daily_prob = estimate_daily_prob(monthly_coverage, duration=30)
        
        # Calculate days since simulation start
        days = [(date + pd.Timedelta(days=i) - sim_start_date).days for i in range(30)]
        
        # Create a 30-day campaign starting from the date
        campaign = cv.historical_vaccinate_prob(
            vaccine='default',
            days=days,
            prob=daily_prob
        )
        
        return campaign

    def testing_historical(self, pop_scale=331):
        df = pd.read_csv("/home/mlq/fed model/covasim/COVID-19_Diagnostic_Laboratory_Testing__PCR_Testing__Time_Series_20240726.csv")
        df = df.groupby(['date']).sum()
        # df = df[['new_results_reported']]/pop_scale
        df['new_tests'] = df[['new_results_reported']]
        df = df[['new_tests']]/pop_scale

        # df = df[['new_tests']]
        # print("test",df['new_tests'])
        test_list = round(df['new_tests']).tolist()
        start_day = (pd.to_datetime(df.index[0]) - pd.to_datetime(self.pars['start_day'])).days  # Adjust the reference date as needed
        # print(start_day)
        test = cv.test_num(daily_tests=test_list, start_day=start_day)

        # test = cv.test_num(df)
        return test
 

    def vax_precise(self):
        df = self.vax_df
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df = df.groupby(['month', 'year'])[['people_vaccinated', 'total_vaccinations', 'people_fully_vaccinated', 'total_boosters']].last()/pop
        # Convert start_day to datetime
        sim_start_date = pd.to_datetime(self.pars['start_day'])

        # Create vaccination campaigns for each row
        vaccination_campaigns = df.apply(self.create_vaccination_campaign_precise, axis=1, args=(sim_start_date,)).tolist()
        return vaccination_campaigns

    def create_vaccination_campaign_simple(self, sim_start_date, vax_start_date, vax_end_date, vax_pop):    
        # Calculate days since simulation start
        vax_start_date = (vax_start_date - sim_start_date).days
        vax_end_date = (vax_end_date - sim_start_date).days
        
        days = [i for i in range(vax_start_date, vax_end_date)]
        print("days",days)
        prob = vax_pop / len(days)
        print("prob",prob)

        campaign = cv.historical_vaccinate_prob(
            vaccine = 'default',
            days=days,
            prob=prob,
            # label=f'Vaccination {start_date.strftime("%Y-%m")} to {vax_end_date.strftime("%Y-%m")}'
        )  

        return campaign

    def vax_simple(self, us_pop=331_000_000):
        df = self.vax_df
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df = df.groupby('year')[['people_vaccinated', 'total_vaccinations', 'people_fully_vaccinated', 'total_boosters']].last()/us_pop
        df['delta_total_vax'] = df['total_vaccinations'].diff().fillna(df['total_vaccinations'])
        df['delta_people_vax'] = df['people_vaccinated'].diff().fillna(df['people_vaccinated'])
        df['delta_people_fully_vax'] = df['people_fully_vaccinated'].diff().fillna(df['people_fully_vaccinated'])

        print(df.loc[2020, 'delta_total_vax'])
        # Convert start_day to datetime
        sim_start_date = pd.to_datetime(self.pars['start_day'])
        print(sim_start_date)
        # Group the DataFrame by six-month periods and create vaccination campaigns
        vax2020 = self.create_vaccination_campaign_simple(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2020-12-01"), vax_end_date=pd.to_datetime("2020-12-31"), vax_pop=df.loc[2020, 'delta_total_vax'])
        vax2021 = self.create_vaccination_campaign_simple(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2021-01-01"), vax_end_date=pd.to_datetime("2021-12-31"), vax_pop=df.loc[2021, 'delta_total_vax'])
        vax2022 = self.create_vaccination_campaign_simple(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2022-01-01"), vax_end_date=pd.to_datetime("2022-12-31"), vax_pop=df.loc[2022, 'delta_total_vax'])
        # vaccinations in 2023 is insignificant: new vaccinations = 2.044498 - 2.014961 = 0.029537% of the population
        # vax2023 = create_vaccination_campaign_simple(sim_start_date=sim_start_date, vax_start_date=pd.to_datetime("2023-01-01"), vax_end_date=pd.to_datetime("2023-12-31"), vax_pop=df.loc[2023, 'delta_total_vax'])

        vaccination_campaigns = [vax2020, vax2021, vax2022,
                                # vax2023   
        ]

        return vaccination_campaigns

    def week_to_date(self, week):
        # Create a date range starting from the beginning of 2020
        date_range = pd.date_range(start='2020-01-01', periods=week, freq='W')
        # Get the last date in the range
        end_date = date_range[-1]
        # convert week to pd.Timestamp -> datetime -> str
        return end_date.date().strftime('%Y-%m-%d')

    def custom_sim(self, start_stayhome, duration_stayhome):
        # transmission rate = beta = 0.13

        start_stayhome_date = self.week_to_date(start_stayhome)
        end_stayhome_date = self.week_to_date(start_stayhome + duration_stayhome)

        # Define sim with simulations:
        lockdown = cv.change_beta(days=[start_stayhome_date, end_stayhome_date], changes=[0.5, 1.0]) # 0.5 means 50% reduction in transmission rate
        test = self.testing_historical()
        ct = cv.contact_tracing(trace_probs=dict(h=1.0, s=0.5, w=0.5, c=0.3), do_plot=False)
        vax_campaigns = self.vax_simple()

        # interventions = [lockdown, test, ct] + vax_campaigns 
        interventions = [test, ct] + vax_campaigns 


        self.pars['interventions'] = interventions

        # print(self.pars)

        # sim = cv.Sim(self.pars, interventions=interventions, label='With interventions')
        sim = cv.Sim(self.pars, label='With interventions')

        sim.run()
        with_interventions = sim.to_df()
        with_interventions.to_csv('with-interventions.csv', index=False)



if __name__ == '__main__':
    covasim = Covasim()
    covasim.custom_sim(5, 6)
    