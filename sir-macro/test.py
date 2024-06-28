from main import *
import numpy as np
import matplotlib.pyplot as plt

td_solve(ctaxctax=np.full(H, 0), pr_treat=np.zeros(250), pr_vacc=np.zeros(250), pi1=0.0046, pi2=7.3983, pi3=0.2055,
             eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=50,
             h=1E-4, tol=1E-8, noisy=False, H_U=None)

"""
ctax: Consumption tax (containment policy)
pr_treat, pr_vacc: Probabilities of treatment and vaccination
pi1, pi2, pi3: Transmission probabilities for consumption, work, and other activities
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
"""