from main import *
import numpy as np
import matplotlib.pyplot as plt
from utilities import *
import pandas as pd
from pandas import DataFrame
# from find_policy import *

sir_macro_policy = {
        'vax': np.full(150, 1/52),
        'treat': np.zeros(150),
        'start_stayhome': 5, # start stayhome at week 5
        'end_stayhome': 30, # end stayhome at week 30
}

def sir_macro(policy, sim_duraion=150, ctax_intensity=0.5, verbose=False):

        ss = initial_ss() # pre-pandemic steady state
        if verbose:
                print('Steady state:', ss)

        ctax_policy = np.zeros(sim_duraion)
        ctax_policy[policy['start_stayhome']:policy['end_stayhome']+1] = ctax_intensity 

        # td1 = td_solve(ctax=np.full(sim_duraion, 0), pr_treat=np.zeros(sim_duraion), pr_vacc=np.zeros(sim_duraion), pi1=0.0046, pi2=7.3983, pi3=0.2055,
        #         eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=50,
        #         h=1E-4, tol=1E-8, noisy=False, H_U=None)

        td2 = td_solve(ctax=ctax_policy, pr_treat=policy['treat'], pr_vacc=policy['vax'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
                h=1E-4, tol=1E-8, noisy=verbose, H_U=None)

        # td1 = pd.DataFrame(td1)
        td2 = pd.DataFrame(td2)

        # vars = [{"key": "I", "name": "Infected", "y_unit": "% initial pop."},
        #         {"key": "S", "name": "Susceptible", "y_unit": "% initial pop."},
        #         {"key": "D", "name": "Death", "y_unit": "% initial pop."},
        #         {"key": "T", "name": "New Infections", "y_unit": "% initial pop."},
        #         {"key": "C", "name": "Aggregate Consumption", "y_unit": ""},
        #         {"key": "N", "name": "Aggregate labor supply", "y_unit": ""},
        #         ]
        # plot_results_custom(td1, td2, name1='No Policy', name2 = 'Custom Policy', variables=vars, ss=ss, end_week = sim_duraion, fig_name='./png/convoi.png', df1_name='./csv/convoi_td1.csv', df2_name='./csv/convoi_td2.csv')

        print(type(td2))
        print(td2)
        print(td2["I"])

        return td2

def loss_sir_macro(td_res:DataFrame, covasim_res:DataFrame):
        return np.square(td_res['I'] - covasim_res['I'])

def find_containment():
        gradient_descent(f=loss_sir_macro(), policy:dict, learning_rate=.01, num_iterations=1000, *args)


def __main__():
        sir_macro(sir_macro_policy)



if __name__ == '__main__':
    __main__()


"""
ctax: Consumption tax (containment policy)
H: Number of periods (weeks) to simulate 
pr_treat, pr_vacc: Probabilities of treatment and vaccination
pi1, pi2, pi3: Transmission probabilities for consumption, work, and other activities (e.g. meeting a neighbor or touching a contaminated surface)
eps: Initial infection rate
pidbar: Baseline death probability
pir: Recovery probability
kappa: Parameter for hospital capacity constraints
phi: labor productivity parameter
theta: Disutility of labor parameter
A: Productivity parameter
beta: Discount factor


ns, ni, nr: Labor supply for susceptible, infected, and recovered individuals
cs, ci, cr: Consumption for susceptible, infected, and recovered individuals
T: New infections
S, I, R, D: Population shares of Susceptible, Infected, Recovered, and Deceased
tau: Infection probability
Ur, Ui, Us: Value functions for recovered, infected, and susceptible individuals
mus: Multiplier on infection probability
lami, lams: Lagrange multipliers for infected and susceptible budget constraints
P: Total population (1 - D)
R1, R2, R3: Residuals for equilibrium conditions
C: Aggregate consumption (Consumption (C) equals output, which is productivity (A) times labor (N))
N: Aggregate labor supply (hours worked)
Neff: Effective labor supply (accounting for productivity loss of infected)
walras: Walras' law check (should be close to zero)
pid: Death probability
mortality: Mortality rate (pid / pir)


h (1E-4): Step size for numerical differentiation.
maxit (50): Maximum number of iterations for the solver.
noisy (False): If True, prints detailed information during solving.
H_U (None): Pre-computed Jacobian matrix (if available).
"""