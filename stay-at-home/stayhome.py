import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

# Define the SIR model
def sir_model(t, y, beta, gamma):
    S, I, R = y
    dSdt = -beta * S * I
    dIdt = beta * S * I - gamma * I
    dRdt = gamma * I
    return [dSdt, dIdt, dRdt]

# Define the utility function
def utility(C, L):
    return np.log(C) + np.log(L)

# Define the disutility from infections
def disutility(I):
    return I**2

# Define the economic impact of the mitigation policy
def economic_impact(tau, C0, L0):
    C = C0 * (1 - tau)
    L = L0 * (1 - tau)
    return C, L

# Define the objective function for optimization
def objective(tau, S0, I0, R0, beta, gamma, C0, L0):
    # Solve the SIR model
    sol = solve_ivp(sir_model, [0, 160], [S0, I0, R0], args=(beta, gamma), dense_output=True)
    t = np.linspace(0, 160, 160)
    S, I, R = sol.sol(t)
    
    # Calculate the economic impact
    C, L = economic_impact(tau, C0, L0)
    
    # Calculate the total utility
    total_utility = np.sum(utility(C, L) - disutility(I))
    
    # We want to maximize utility, so we minimize the negative utility
    return -total_utility

# Initial conditions and parameters
S0 = 0.99
I0 = 0.01
R0 = 0.0
beta = 0.3
gamma = 0.1
C0 = 1.0
L0 = 1.0

# Initial guess for the mitigation policy
tau_initial = 0.1

# Bounds for the mitigation policy (0 <= tau <= 1)
bounds = [(0, 1)]

# Optimize the mitigation policy
result = minimize(objective, tau_initial, args=(S0, I0, R0, beta, gamma, C0, L0), bounds=bounds)

# Optimal mitigation policy
tau_optimal = result.x[0]

print(f"Optimal mitigation policy (tau): {tau_optimal:.4f}")
