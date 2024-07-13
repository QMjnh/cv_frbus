from main import *
import numpy as np
import matplotlib.pyplot as plt
from utilities import *
import pandas as pd
from pandas import DataFrame
from math import ceil
import sys
sys.path.insert(0, '..')
from find_policy import *

sir_macro_policy = {
        'start_stayhome': 5, # start stayhome at week 5
        'end_stayhome': 7, # end stayhome at week 30
        'ctax_intensity': 0.5
}

covasim_res = pd.DataFrame({'I': [0.00013] * 150})
vax =  np.full(150, 1/52),
treat =  np.zeros(150),

medical_dict = {
        'vax': vax,
        'treat': treat, 
        'covasim_res': covasim_res
}

class sir_macro():
        def __init__(self, medical_dict, start_stayhome, end_stayhome, sim_duraion=150, verbose=False):
                self.medical_dict = medical_dict
                self.start_stayhome = start_stayhome
                self.end_stayhome = end_stayhome
                # self.ctax_intensity = ctax_intensity
                self.sim_duraion = sim_duraion
                self.verbose = verbose

        def sir_macro(self, ctax_intensity):
                ss = initial_ss() # pre-pandemic steady state
                # if self.verbose:
                #         print('Steady state:', ss)
                ctax_policy = np.zeros(self.sim_duraion)
                ctax_policy[self.start_stayhome:self.end_stayhome+1] = ctax_intensity 
                td = td_solve(ctax=ctax_policy, pr_treat=self.medical_dict['treat'][-1], pr_vacc=self.medical_dict['vax'][-1], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                        eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
                        h=1E-4, tol=1E-8, noisy=False, H_U=None)
                td = pd.DataFrame(td)
                return td

        def loss_sir_macro(self, ctax_intensity):
                try:
                        td_res = self.sir_macro(ctax_intensity)
                        loss = np.square(td_res['I'] - covasim_res['I']).sum()
                except Exception as e:
                        print("sir-macro error:", e)
                        loss = -1
                return loss

        def find_best_ctax(self, ctax_intensity):
                best_policy, _, _ = gradient_descent_with_adam(self.loss_sir_macro, ctax_intensity, learning_rate=1,
                                                         epochs='auto', verbose=self.verbose, patience=5, save_policy_as=None)
                return best_policy


def __main__():
        sir = sir_macro(medical_dict, start_stayhome=5, end_stayhome=7, sim_duraion=150, verbose=True)
        sir.find_best_ctax({'ctax_intensity': 0.5})


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