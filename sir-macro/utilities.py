import numpy as np
import scipy.linalg
import inspect
import matplotlib.pyplot as plt
import pandas as pd
import math

'''Part 1: Manipulating Jacobians'''


def pack_vectors(vs, names, T):
    """Dictionary of vectors into a single vector."""
    v = np.zeros(len(names)*T)
    for i, name in enumerate(names):
        if name in vs:
            v[i*T:(i+1)*T] = vs[name]
    return v


def unpack_vectors(v, names, T):
    """Single vector to dictionary of vectors."""
    vs = {}
    for i, name in enumerate(names):
        vs[name] = v[i*T:(i+1)*T]
    return vs


def pack_jacobians(jacdict, inputs, outputs, T):
    """If we have T*T jacobians from nI inputs to nO outputs in jacdict, combine into (nO*T)*(nI*T) jacobian matrix."""
    nI, nO = len(inputs), len(outputs)

    outjac = np.empty((nO * T, nI * T))
    for iO in range(nO):
        subdict = jacdict.get(outputs[iO], {})
        for iI in range(nI):
            outjac[(T * iO):(T * (iO + 1)), (T * iI):(T * (iI + 1))] = subdict.get(inputs[iI], np.zeros((T, T)))
    return outjac


def J_to_HU(J, H, unknowns, targets):
    """Jacdict to LU-factored jacobian."""
    H_U = pack_jacobians(J, unknowns, targets, H)
    H_U_factored = factor(H_U)
    return H_U_factored


'''Part 2: Efficient Newton step'''


def factor(X):
    return scipy.linalg.lu_factor(X)


def factored_solve(Z, y):
    return scipy.linalg.lu_solve(Z, y)


'''Part 3: Convenience'''


def input_list(f):
    """Return list of function inputs"""
    return inspect.getfullargspec(f).args


def plot_results_default(td1, td2, name1, name2, ss, end_week, fig_name='./png/fig1.png', df1_name='./csv/td1.csv', df2_name='./csv/td2.csv'):
    fig1, axes = plt.subplots(2, 3, figsize=(.8*12, .8*8))
    ax = axes.flatten()

    ax[0].plot(100 * td1['I'][:end_week], label=name1, linewidth=2)
    ax[0].plot(100 * td2['I'][:end_week], label=name2, linewidth=2)
    ax[0].set_title('Infected, I')
    ax[0].set_ylabel('% of initial population')
    ax[0].legend()

    ax[1].plot(100 * td1['S'][:end_week], label=name1, linewidth=2)
    ax[1].plot(100 * td2['S'][:end_week], label=name2, linewidth=2)
    ax[1].set_title('Susceptibles, S')
    ax[1].set_ylabel('% of initial population')
    ax[1].legend()

    ax[2].plot(100 * td1['R'][:end_week], label=name1, linewidth=2)
    ax[2].plot(100 * td2['R'][:end_week], label=name2, linewidth=2)
    ax[2].set_title('Recovered, R')
    ax[2].set_ylabel('% of initial population')
    ax[2].legend()

    ax[3].plot(100 * td1['D'][:end_week], label=name1, linewidth=2)
    ax[3].plot(100 * td2['D'][:end_week], label=name2, linewidth=2)
    ax[3].set_title('Deaths, D')
    ax[3].set_ylabel('% of initial population')
    ax[3].set_xlabel('weeks')
    ax[3].legend()

    ax[4].plot(100 * (td1['C'] / ss['C'] - 1)[:end_week], label=name1, linewidth=2)
    ax[4].plot(100 * (td2['C'] / ss['C'] - 1)[:end_week], label=name2, linewidth=2)
    ax[4].axhline(0, color='gray', linestyle='--')
    ax[4].set_title('Aggregate Consumption, C')
    ax[4].set_ylabel('% deviation from initial ss')
    ax[4].set_xlabel('weeks')
    ax[4].legend()

    ax[5].plot(100 * (td1['N'] / ss['N'] - 1)[:end_week], label=name1, linewidth=2)
    ax[5].plot(100 * (td2['N'] / ss['N'] - 1)[:end_week], label=name2, linewidth=2)
    ax[5].axhline(0, color='gray', linestyle='--')
    ax[5].set_title('Aggregate Hours, N')
    ax[5].set_ylabel('% deviation from initial ss')
    ax[5].set_xlabel('weeks')
    ax[5].legend()

    plt.tight_layout()
    
    df1 = pd.DataFrame(td1)
    df2 = pd.DataFrame(td2)
    plt.savefig(fig_name)
    df1.to_csv(df1_name)
    df2.to_csv(df2_name)
    plt.show()
    plt.close()


def plot_results_custom(scenarios:[dict], ss, end_week, variables:[dict], fig_name='./png/fig1.png'):
    """
    Plot results of custom pandemic scenarios.

    Example Usage:
    scenarios = [{'df': td1, 'name': 'No Policy', 'csv_name': './csv/td1.csv'},
                {'df': td2, 'name': 'Custom Policy', 'csv_name': './csv/td2.csv'},
                {'df': self.medical_dict['covasim_res'], 'name': 'Covasim', 'csv_name': './csv/td0.csv'}]


    vars = [{"key": "I", "name": "Infected", "y_unit": "% initial pop.",},
            {"key": "S", "name": "Susceptible", "y_unit": "% initial pop."},
            {"key": "D", "name": "Death", "y_unit": "% initial pop."},
            {"key": "T", "name": "New Infections", "y_unit": "% initial pop."},
            {"key": "C", "name": "Aggregate Consumption", "y_unit": "% deviation from initial ss", 'type': '% deviation'},
            {"key": "N", "name": "Aggregate labor supply", "y_unit": "% deviation from initial. ss", 'type': '% deviation'},
            ]
    plot_results_custom(scenarios, variables=vars, ss=self.ss, end_week = self.sim_duraion, fig_name='./png/convoi.png')
    
    """

    num_vars = len(variables)
    num_rows = math.ceil(num_vars / 3)  # Adjust as needed
    num_cols = 3

    fig1, axes = plt.subplots(num_rows, num_cols, figsize=(.8*4*num_cols, .8*4*num_rows))
    ax = axes.flatten()

    for i in range(len(variables)):
        ax[i].set_title(variables[i]['name'])
        ax[i].set_ylabel(variables[i]['y_unit'])
        ax[i].set_xlabel('weeks')

        try:
            variables[i]['type']
        except: 
            variables[i]['type'] = '' 

        if variables[i]['type'] == '% deviation':
            for j in range(len(scenarios)):
                ax[i].axhline(0, color='gray', linestyle='--')
                try:
                    ax[i].plot(100 * (scenarios[j]['df'][variables[i]['key']] / ss[variables[i]['key']]-1) [:end_week], label=scenarios[j]['name'], linewidth=2)
                except Exception as e:
                    print(f"Error in plotting {scenarios[j]['name']}:", e, ". Skipping...")


        else:
            for j in range(len(scenarios)):
                try:
                    ax[i].plot(100 * scenarios[j]['df'][variables[i]['key']][:end_week], label=scenarios[j]['name'], linewidth=2)
                except Exception as e:
                    print(f"Error in plotting {scenarios[j]['name']}:", e, ". Skipping...")

        ax[i].legend()


    for j in range(len(scenarios)):
        scenarios[j]['df'].to_csv(scenarios[j]['csv_name'])

    plt.tight_layout()
    plt.savefig(fig_name)
    plt.show()
    plt.close()