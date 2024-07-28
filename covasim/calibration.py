import covasim as cv
import pandas as pd
import sciris as sc 

epi = pd.read_csv('full_data.csv')
epi.dropna(inplace=True)
# epi = epi.drop(columns=['location_key'])
# epi = epi.groupby('date').sum().reset_index()
# epi = epi.rename(columns={'new_confirmed': 'new_diagnoses', 'new_deceased': 'deaths', 'new_tested': 'new_tests'})
epi = epi[epi['location'] == 'United States']
epi = epi.rename(columns={'new_cases': 'new_diagnoses', 'new_deaths': 'deaths'})
print(epi.columns)
epi['new_diagnoses'] = epi['new_diagnoses']/331
epi['deaths'] = epi['deaths']/331



# Create default simulation parameters
pars = sc.objdict(
    pop_size       = 1_000_000,                 # Size of the population in the simulation
    start_day      = '2020-01-31',              # Start date of the simulation
    end_day        = '2020-12-31',              # End date of the simulation
    beta           = 0.15,                      # Transmission rate of the disease
    rel_death_prob = 1.0,                       # Relative probability of death from the disease
    verbose        = 0,                         # Level of output verbosity (0 means no extra output)
)

# Create a simulation object with the specified parameters
sim = cv.Sim(pars=pars, datafile=epi)  # 'epi' presumably refers to a data file for epidemiological data

# Parameters to calibrate -- format is [best, low, high]
calib_pars = dict(
    beta           = [pars.beta, 0.005, 0.20],        # Transmission rate with initial, lower, and upper bounds
    rel_death_prob = [pars.rel_death_prob, 0.5, 3.0], # Relative death probability with initial, lower, and upper bounds
)

# Main block to ensure code runs only when executed as a script
if __name__ == '__main__':

    # Run the calibration
    calib = sim.calibrate(
        calib_pars=calib_pars,  # Parameters to be calibrated
        total_trials=5          # Total number of calibration trials to run
    )

# [I 2024-07-28 08:32:21,573] A new study created in RDB with name: covasim_calibration
# [I 2024-07-28 08:38:43,758] Trial 0 finished with value: 435.186168711951 and parameters: {'beta': 0.05746142771925268, 'rel_death_prob': 1.4928248771250856}. Best is trial 0 with value: 435.186168711951.
# [I 2024-07-28 08:38:50,268] Trial 1 finished with value: 435.186168711951 and parameters: {'beta': 0.0668292027789055, 'rel_death_prob': 2.6281522258373324}. Best is trial 0 with value: 435.186168711951.
# [I 2024-07-28 08:38:56,255] Trial 6 finished with value: 435.186168711951 and parameters: {'beta': 0.08236451050296537, 'rel_death_prob': 2.377924904370044}. Best is trial 0 with value: 435.186168711951.
# [I 2024-07-28 08:38:59,034] Trial 3 finished with value: 435.186168711951 and parameters: {'beta': 0.09851159020436404, 'rel_death_prob': 2.317289910893508}. Best is trial 0 with value: 435.186168711951.
# [I 2024-07-28 08:39:01,035] Trial 4 finished with value: 435.186168711951 and parameters: {'beta': 0.1063753639388868, 'rel_death_prob': 1.950677391296373}. Best is trial 0 with value: 435.186168711951.

# [I 2024-07-28 09:51:39,366] A new study created in RDB with name: covasim_calibration
# [I 2024-07-28 09:58:12,398] Trial 4 finished with value: 435.186168711951 and parameters: {'beta': 0.07609785743606515, 'rel_death_prob': 2.809166231898467}. Best is trial 4 with value: 435.186168711951.
# [I 2024-07-28 09:58:24,966] Trial 3 finished with value: 435.186168711951 and parameters: {'beta': 0.09793859798796073, 'rel_death_prob': 1.0982727079137722}. Best is trial 3 with value: 435.186168711951.
# [I 2024-07-28 09:58:26,128] Trial 2 finished with value: 435.186168711951 and parameters: {'beta': 0.12589663971276277, 'rel_death_prob': 1.2706887764359567}. Best is trial 2 with value: 435.186168711951.
# [I 2024-07-28 09:58:28,283] Trial 1 finished with value: 435.186168711951 and parameters: {'beta': 0.1341505598888762, 'rel_death_prob': 1.625631504929667}. Best is trial 1 with value: 435.186168711951.