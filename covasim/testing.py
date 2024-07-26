import pandas as pd
import numpy as np
import covasim as cv

df = pd.read_csv("/home/mlq/fed model/covasim/COVID-19_Diagnostic_Laboratory_Testing__PCR_Testing__Time_Series_20240726.csv")
# df = df.groupby(['date', 'overall_outcome']).sum()
df = df.groupby(['date']).sum()

# df = df[['new_results_reported',  'total_results_reported']]
df = df[['new_results_reported']]

print(df.head(9))


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

lockdown = cv.change_beta(days=['2020-01-31', '2023-12-31'], changes=[0.5, 1.0]) # 0.5 means 50% reduction in transmission rate
test = cv.test_num(df)
ct = cv.contact_tracing(trace_probs=dict(h=1.0, s=0.5, w=0.5, c=0.3), do_plot=False)
# vax_campaigns = self.vax_simple()

interventions = [lockdown, test, ct]

sim = cv.Sim(pars, interventions=interventions, label='With interventions')
sim.run()