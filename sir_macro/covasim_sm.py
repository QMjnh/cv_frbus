from main import *
import numpy as np
import matplotlib.pyplot as plt
from utilities import *
import pandas as pd
from pandas import DataFrame
from scipy.stats import norm
import sys
import time
sys.path.insert(0, '..')
from find_policy import *
from find_policy_parallel import *

class sir_macro_obj():
        def __init__(self, covasim_res, start_stayhome, end_stayhome, epochs='auto', patience=5, learning_rate=.5, save_policy_as=None, sim_duraion=208, verbose=False, fig_name='./png/convoi2.png'):
                self.covasim_res = covasim_res
                self.start_stayhome = start_stayhome
                self.end_stayhome = end_stayhome
                self.sim_duraion = sim_duraion
                self.verbose = verbose
                self.best_policy = None
                self.policy_history = None
                self.loss_history = None
                self.ss = initial_ss() # pre-pandemic steady state from sir-macro model
                self.epochs = epochs
                self.patience = patience
                self.save_policy_as = save_policy_as
                self.learning_rate = learning_rate
                self.fig_name = fig_name
                self.best_sim = None

        def sir_macro(self, ctax_intensity):
                # print("calling sir-macro")
                if not isinstance(ctax_intensity, pd.Series) :
                        ctax_policy = np.zeros(self.sim_duraion)
                        ctax_policy[self.start_stayhome:self.end_stayhome+1] = ctax_intensity 

                else: ctax_policy = ctax_intensity 


                td = td_solve(ctax=ctax_policy, pr_treat=np.zeros(len(self.covasim_res)), pr_vacc=self.covasim_res['deltaV'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                        eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
                        h=1E-4, tol=1E-8, noisy=False, H_U=None)
                td = pd.DataFrame(td)
                return td

        def loss_sir_macro(self, ctax_intensity):
                # print("calling loss_sir_macro")
                try:
                        td_res = self.sir_macro(ctax_intensity)
                        loss=0
                        for i in ['S', 'I', 'R', 'D', 'T', 'deltaV']:
                                try: loss += np.square(td_res[i] - self.covasim_res[i]).sum()
                                except:print("Error calculating sir-macro loss for", i)
                except Exception as e:
                        print("sir-macro error:", e)
                        loss = -1
                return loss

        def find_best_ctax(self, ctax_intensity):
                # print("find_best_ctax")
                self.best_policy, self.policy_history, self.loss_history = gradient_descent(self.loss_sir_macro, ctax_intensity, learning_rate=self.learning_rate,
                                                         epochs=self.epochs, verbose=self.verbose, patience=self.patience, save_policy_as=self.save_policy_as)
                return self.best_policy, self.policy_history, self.loss_history

        def find_best_ctax_parallel(self, ctax_intensity):
                # print("find_best_ctax_parallel")
                self.best_policy, self.policy_history, self.loss_history = gradient_descent_adam_parallel(self.loss_sir_macro, ctax_intensity, learning_rate=self.learning_rate,
                                                         epochs=self.epochs, verbose=self.verbose, patience=self.patience, save_policy_as=self.save_policy_as)
                return self.best_policy, self.policy_history, self.loss_history

        def best_simulation(self):
                if self.best_policy == None:
                        raise Exception("No best policy found. Run find_best_ctax() or find_best_ctax_parallel() first.")
                self.best_sim = self.sir_macro(self.best_policy['ctax_intensity'])
                for i in ['C', 'N']:
                        self.best_sim[f"{i}_dev"] = (self.best_sim[i] / self.ss[i] - 1)
                return self.best_sim

        def visualize(self):
                if self.best_policy == None:
                        raise Exception("No best policy found. Run find_best_ctax() first.")
                td1 = td_solve(ctax=np.full(self.sim_duraion, 0), pr_treat=np.zeros(len(self.covasim_res)), pr_vacc=self.covasim_res['deltaV'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                        eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=50,
                        h=1E-4, tol=1E-8, noisy=False, H_U=None)


                if not isinstance(self.best_policy['ctax_intensity'], pd.core.series.Series) :
                        print(type(self.best_policy['ctax_intensity']))
                        ctax_policy = np.zeros(self.sim_duraion)
                        ctax_policy[self.start_stayhome:self.end_stayhome+1] = self.best_policy['ctax_intensity']

                else: ctax_policy = self.best_policy['ctax_intensity']

                # td2 = td_solve(ctax=ctax_policy, pr_treat=self.covasim_res['treat'], pr_vacc=self.covasim_res['deltaV'], pi1=0.0046, pi2=7.3983, pi3=0.2055,
                #         eps=0.001, pidbar=0.07 / 18, pir=0.99 * 7 / 18, kappa=0.0, phi=0.8, theta=36, A=39.8, beta=0.96**(1/52), maxit=100,
                #         h=1E-4, tol=1E-8, noisy=False, H_U=None)

                td2 = self.best_simulation()

                td1 = pd.DataFrame(td1)
                td2 = pd.DataFrame(td2)

                scenarios = [{'df': td1, 'name': 'No Policy', 'csv_name': './csv/td1.csv'},
                             {'df': td2, 'name': 'Custom Policy', 'csv_name': './csv/td2.csv'},
                             {'df': self.covasim_res, 'name': 'Covasim', 'csv_name': './csv/td0.csv'}]

                vars = [{"key": "I", "name": "Infected", "y_unit": "% initial pop.",},
                        {"key": "S", "name": "Susceptible", "y_unit": "% initial pop."},
                        {"key": "D", "name": "Death", "y_unit": "% initial pop."},
                        {"key": "T", "name": "New Infections", "y_unit": "% initial pop."},
                        {"key": "C", "name": "Aggregate Consumption", "y_unit": "% deviation from initial ss", 'type': '% deviation'},
                        {"key": "N", "name": "Aggregate labor supply", "y_unit": "% deviation from initial. ss", 'type': '% deviation'},
                        ]
                plot_results_custom(scenarios, variables=vars, ss=self.ss, end_week = self.sim_duraion, fig_name=self.fig_name)




def __main__():
        covasim_df = pd.read_csv("../covasim/with-interventions.csv")
        
        simulated_pop = 1000000
        covasim_df['I'] = covasim_df['cum_infections'] / simulated_pop
        covasim_df['R'] = covasim_df['cum_recoveries'] / simulated_pop
        covasim_df['D'] = covasim_df['cum_deaths'] / simulated_pop
        covasim_df['T'] = covasim_df['new_infections'] / simulated_pop
        covasim_df['S'] = covasim_df['n_susceptible'] / simulated_pop
        covasim_df['deltaV'] = covasim_df['new_vaccinated'] / simulated_pop

        # Generate 208 points from a normal distribution
        x = np.linspace(norm.ppf(0.01), norm.ppf(0.99), 208)
        # Calculate the PDF of the normal distribution at these points
        pdf_values = norm.pdf(x)
        covasim_df = pd.DataFrame(pdf_values/10, columns=['I'])
        covasim_df['deltaV'] = np.full(208, 1/52)

        # print("max", max(covasim_df['I']))

        # covasim_res = {
        #         'deltaV': np.full(208, 1/52),
        #         'treat': np.zeros(208), 
        #         'covasim_res': covasim_df
        # }
        sir = sir_macro_obj(covasim_df, start_stayhome=5, end_stayhome=208, epochs=1, sim_duraion=208, verbose=True, learning_rate=0.3, save_policy_as='./json/sample.json')
        start_time = time.time()
        best_policy, policy_history, loss_history = sir.find_best_ctax({'ctax_intensity': 0.5})
        # print("Time taken sigular:", time.time() - start_time)
        sir.visualize()

        sir_res = sir.best_simulation()

        print(sir_res)
        print(sir_res['C_dev'])


        # covasim_res = {
        #         'deltaV': np.full(208, 1/52),
        #         'treat': np.zeros(208), 
        #         'covasim_res': pd.DataFrame({'I': [0.013] * 208})
        # }
        # sir = sir_macro_obj(covasim_res, start_stayhome=5, end_stayhome=208, epochs=1, sim_duraion=208, verbose=False, learning_rate=0.2, fig_name='./png/convoi2_parallel.png')
        # start_time = time.time()
        # best_policy, policy_history, loss_history = sir.find_best_ctax_parallel({'ctax_intensity': pd.Series(np.full(208, 0.5))})
        # print("Time taken parallel:", time.time() - start_time)
        # sir.visualize()

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