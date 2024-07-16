import covasim as cv
import pandas as pd
import sciris as sc 

epi = pd.read_csv('epidemiology.csv')
epi.dropna(inplace=True)
epi = epi.drop(columns=['location_key'])
epi = epi.groupby('date').sum().reset_index()
epi = epi.rename(columns={'new_confirmed': 'new_diagnoses', 'new_deceased': 'deaths', 'new_tested': 'new_tests'})

# Create default simulation parameters
pars = sc.objdict(
    pop_size       = 1_000_000,                 # Size of the population in the simulation
    start_day      = '2020-01-31',              # Start date of the simulation
    end_day        = '2020-03-13',              # End date of the simulation
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
        total_trials=1          # Total number of calibration trials to run
    )
