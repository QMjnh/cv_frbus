from main import *
import numpy as np
import matplotlib.pyplot as plt
from utilities import *

H=150
# end_week = 100
ss = initial_ss() # pre-pandemic steady state
td1 = td_solve(ctax=np.full(H, 0), pr_treat=np.zeros(H), pr_vacc=np.zeros(H), pi1=0.0046, pi2=7.3983, pi3=0.2055,
             eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=50,
             h=1E-4, tol=1E-8, noisy=True, H_U=None)

td2 = td_solve(ctax=np.full(H, .3), pr_treat=np.zeros(H), pr_vacc=np.full(H, 1/52), pi1=0.0046, pi2=7.3983, pi3=0.2055,
             eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
             h=1E-4, tol=1E-8, noisy=True, H_U=None)

vars = [{"key": "I", "name": "Infected", "y_unit": "% initial pop."},
        {"key": "S", "name": "Susceptible", "y_unit": "% initial pop."},
        {"key": "D", "name": "Death", "y_unit": "% initial pop."},
        {"key": "T", "name": "New Infections", "y_unit": "% initial pop."},
        {"key": "C", "name": "Aggregate Consumption", "y_unit": ""},
        {"key": "N", "name": "Aggregate labor supply", "y_unit": ""},
        ]
plot_results_custom(td1, td2, name1='No Policy', name2 = 'Custom Policy', variables=vars, ss=ss, end_week = H, fig_name='./png/convoi.png', df1_name='./csv/convoi_td1.csv', df2_name='./csv/convoi_td2.csv')

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
C: Aggregate consumption
N: Aggregate labor supply
Neff: Effective labor supply (accounting for productivity loss of infected)
walras: Walras' law check (should be close to zero)
pid: Death probability
mortality: Mortality rate (pid / pir)


h (1E-4): Step size for numerical differentiation.
maxit (50): Maximum number of iterations for the solver.
noisy (False): If True, prints detailed information during solving.
H_U (None): Pre-computed Jacobian matrix (if available).
"""