from main import *
import numpy as np
import matplotlib.pyplot as plt

def find_optimal_policy(H=250, initial_ctax=0.0, plot_results=True):
    """
    Find the optimal containment policy using the Ramsey optimization.
    
    Parameters:
    H (int): Number of periods to simulate
    initial_ctax (float): Initial guess for the containment tax
    plot_results (bool): Whether to plot the results
    
    Returns:
    dict: Results of the optimization
    """
    # Set up initial conditions and parameters
    ctax0 = np.full(H, initial_ctax)
    s0, i0, r0 = 1 - 0.001, 0.001, 0  # Initial population shares
    
    # Call the Ramsey optimization function
    result = ramsey(ctax0=ctax0, s0=s0, i0=i0, r0=r0)
    
    if result.success:
        print("Optimization successful!")
    else:
        print("Optimization failed.")
        return None
    
    # Solve the model with the optimal policy
    optimal_ctax = result.x
    optimal_solution = td_solve(ctax=optimal_ctax)
    
    # Solve the model with no containment policy for comparison
    no_containment_solution = td_solve(ctax=np.zeros(H))
    
    if plot_results:
        plot_optimal_policy(optimal_solution, no_containment_solution, optimal_ctax)
    
    return {
        'optimal_ctax': optimal_ctax,
        'optimal_solution': optimal_solution,
        'no_containment_solution': no_containment_solution
    }

def plot_optimal_policy(optimal, no_containment, ctax):
    """
    Plot the results of the optimal policy compared to no containment.
    
    Parameters:
    optimal (dict): Results from the optimal policy
    no_containment (dict): Results from no containment policy
    ctax (array): Optimal containment tax
    """
    fig, axs = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot infected population
    axs[0, 0].plot(optimal['I'], label='Optimal Policy')
    axs[0, 0].plot(no_containment['I'], label='No Containment')
    axs[0, 0].set_title('Infected Population')
    axs[0, 0].legend()
    
    # Plot consumption
    axs[0, 1].plot(optimal['C'], label='Optimal Policy')
    axs[0, 1].plot(no_containment['C'], label='No Containment')
    axs[0, 1].set_title('Consumption')
    axs[0, 1].legend()
    
    # Plot labor supply
    axs[1, 0].plot(optimal['N'], label='Optimal Policy')
    axs[1, 0].plot(no_containment['N'], label='No Containment')
    axs[1, 0].set_title('Labor Supply')
    axs[1, 0].legend()
    
    # Plot optimal containment tax
    axs[1, 1].plot(ctax)
    axs[1, 1].set_title('Optimal Containment Tax')

    plt.savefig('./png/ramsey.png')    
    plt.tight_layout()
    plt.show()

# Run the optimization
results = find_optimal_policy()