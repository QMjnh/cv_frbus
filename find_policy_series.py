from daly import *
from typing import Callable
import numpy as np
import json
import time
import pandas as pd
from functools import partial
import multiprocessing as mp



def partial_derivative_estimate(f:Callable, param_name:str, h=.0001, **kwargs):
    """
    This function is to estimate the PARTIAL derivative of function f(x, y, z, ...) when the form of f() is unknown
    f: the loss function to be estimated the derivative of
    h: the infinitesimal change in x to estimate the derivative
    x: the variable to which the derivative is estimated with respect to
    """
    # print("parital derivative is called!!!")
    kwargs_plus_h = kwargs.copy()
    kwargs_plus_h[param_name] += h
    loss = f(**kwargs)
    derivative = (f(**kwargs_plus_h) - loss) / h 
    return derivative, loss

def estimate_partial_for_series(args):
    f, param_name, h, kwargs, index = args
    kwargs_copy = kwargs.copy()
    kwargs_copy[param_name] = kwargs_copy[param_name].copy()
    kwargs_copy[param_name].iloc[index] += h
    loss_plus_h = f(**kwargs_copy)
    loss = f(**kwargs)
    derivative = (loss_plus_h - loss) / h
    return derivative, loss

def clip_policy(policy, min_val=-1e6, max_val=1e6):
    for key, value in policy.items():
        if isinstance(value, pd.Series):
            policy[key] = value.clip(min_val, max_val)
        else:
            policy[key] = max(min(value, max_val), min_val)
    return policy


def gradient_descent_series_parallel(loss_func, policy, learning_rate=0.00001, max_iterations=1000, 
                              tolerance=1e-6, verbose=False, epochs='auto', patience=50, 
                              save_policy_as=None):
    num_cores = mp.cpu_count()
    pool = mp.Pool(num_cores)

    converged = False
    iteration = 0
    best_loss = float('inf')
    best_policy = policy.copy()
    policy_history = []
    loss_history = []
    epochs_without_improvement = 0

    while not converged and iteration < max_iterations:
        current_loss = 0
        for param_name in policy:
            if isinstance(policy[param_name], pd.Series):
                # Implement parallelization for Series
                partial_func = partial(estimate_partial_for_series)
                args_list = [(loss_func, param_name, 0.0001, policy, i) 
                             for i in range(len(policy[param_name]))]
                series_updates = pool.map(partial_func, args_list)
                
                derivatives = pd.Series([update[0] for update in series_updates])
                policy[param_name] -= learning_rate * derivatives
                current_loss = series_updates[0][1]  # Use the loss from any update, they should be the same
            else:
                partial_derivative, loss = partial_derivative_estimate(loss_func, param_name=param_name, **policy)
                policy[param_name] -= learning_rate * partial_derivative
                current_loss = loss

        if current_loss < 0:
            print("Negative loss encountered in GD. Exiting...")
            break

        policy = clip_policy(policy)

        policy_history.append(policy.copy())
        loss_history.append(current_loss)

        if verbose:
            print(f'Iteration {iteration}: {policy}')
            print(f'Loss: {current_loss}')

        # Check for improvement
        if current_loss < best_loss:
            best_loss = current_loss
            best_policy = policy.copy()
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        # Stopping criterion
        if epochs == 'auto':
            if epochs_without_improvement >= patience:
                print(f"Stopping: No improvement for {patience} iterations.")
                break
        elif iteration >= epochs - 1:  # -1 because iteration is 0-indexed
            break

        iteration += 1

    pool.close()
    pool.join()

    print("Iterations ran:", iteration + 1)
    print("Best policy:", best_policy)
    print("Best loss:", best_loss)

    # Convert and write JSON object to file
    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history


def gradient_descent_sequential(loss_func, policy, learning_rate=0.00001, max_iterations=1000, 
                              tolerance=1e-6, verbose=False, epochs='auto', patience=50, 
                              save_policy_as=None):
    num_cores = mp.cpu_count()
    pool = mp.Pool(num_cores)

    converged = False
    iteration = 0
    best_loss = float('inf')
    best_policy = policy.copy()
    policy_history = []
    loss_history = []
    epochs_without_improvement = 0

    while not converged and iteration < max_iterations:
        current_loss = 0
        for param_name in policy:
            if isinstance(policy[param_name], pd.Series):
                for i in range(len(policy[param_name])):
                    args = (loss_func, param_name, 0.0001, policy, i)
                    partial_derivative, loss = estimate_partial_for_series(args)
                    policy[param_name] -= learning_rate * partial_derivative
                    current_loss = loss                
            else:
                partial_derivative, loss = partial_derivative_estimate(loss_func, param_name=param_name, **policy)
                policy[param_name] -= learning_rate * partial_derivative
                current_loss = loss

        if current_loss < 0:
            print("Negative loss encountered in GD. Exiting...")
            break
        
        policy = clip_policy(policy)

        policy_history.append(policy.copy())
        loss_history.append(current_loss)

        if verbose:
            print(f'Iteration {iteration}: {policy}')
            print(f'Loss: {current_loss}')

        # Check for improvement
        if current_loss < best_loss:
            best_loss = current_loss
            best_policy = policy.copy()
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        # Stopping criterion
        if epochs == 'auto':
            if epochs_without_improvement >= patience:
                print(f"Stopping: No improvement for {patience} iterations.")
                break
        elif iteration >= epochs - 1:  # -1 because iteration is 0-indexed
            break

        iteration += 1

    pool.close()
    pool.join()

    print("Iterations ran:", iteration + 1)
    print("Best policy:", best_policy)
    print("Best loss:", best_loss)

    # Convert and write JSON object to file
    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history


def gradient_descent_adam_series_parallel(loss_func, policy, learning_rate=0.001, max_iterations=1000, 
                          tolerance=1e-6, verbose=False, epochs='auto', patience=50, 
                          save_policy_as=None, beta1=0.9, beta2=0.999, epsilon=1e-8):
    num_cores = mp.cpu_count()
    pool = mp.Pool(num_cores)

    converged = False
    iteration = 0
    best_loss = float('inf')
    best_policy = policy.copy()
    policy_history = []
    loss_history = []
    epochs_without_improvement = 0

    # Initialize Adam parameters
    m = {param: np.zeros_like(value) for param, value in policy.items()}
    v = {param: np.zeros_like(value) for param, value in policy.items()}

    while not converged and iteration < max_iterations:
        current_loss = 0
        for param_name in policy:
            if isinstance(policy[param_name], pd.Series):
                partial_func = partial(estimate_partial_for_series)
                args_list = [(loss_func, param_name, 0.0001, policy, i) 
                             for i in range(len(policy[param_name]))]
                series_updates = pool.map(partial_func, args_list)
                
                derivatives = pd.Series([update[0] for update in series_updates])
                current_loss = series_updates[0][1]
            else:
                derivatives, loss = partial_derivative_estimate(loss_func, param_name=param_name, **policy)
                current_loss = loss

            # Adam update
            m[param_name] = beta1 * m[param_name] + (1 - beta1) * derivatives
            v[param_name] = beta2 * v[param_name] + (1 - beta2) * (derivatives ** 2)
            
            m_hat = m[param_name] / (1 - beta1 ** (iteration + 1))
            v_hat = v[param_name] / (1 - beta2 ** (iteration + 1))
            
            policy[param_name] -= learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)

        if current_loss < 0:
            print("Negative loss encountered in GD. Exiting...")
            break

        policy = clip_policy(policy)

        policy_history.append(policy.copy())
        loss_history.append(current_loss)

        if verbose:
            print(f'Iteration {iteration}: {policy}')
            print(f'Loss: {current_loss}')

        if current_loss < best_loss:
            best_loss = current_loss
            best_policy = policy.copy()
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if epochs == 'auto':
            if epochs_without_improvement >= patience:
                print(f"Stopping: No improvement for {patience} iterations.")
                break
        elif iteration >= epochs - 1:
            break

        iteration += 1

    pool.close()
    pool.join()

    print("Iterations ran:", iteration + 1)
    print("Best policy:", best_policy)
    print("Best loss:", best_loss)

    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history







def dummy_loss(j, y, k):
    summ = j.sum()
    return (k**2 + summ ** 2 + y ** 2)**2


def time_function(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def main():
    # Example usage
    policy = {
        'j': pd.Series(np.full(150, 3.0)),
        'y': 7.0,
        'k': 8.0
    }

    # Time the parallel version
    parallel_result, parallel_time = time_function(gradient_descent_series_parallel, dummy_loss, policy.copy(), verbose=False)
    print("\n")

    # parallel_result, parallel_time = time_function(gradient_descent_adam_series_parallel, dummy_loss, policy.copy(), verbose=False)
    # print("\n")

    # Time the sequential version
    sequential_result, sequential_time = time_function(gradient_descent_sequential, dummy_loss, policy.copy(), verbose=False)

    print(f"Parallel version took {parallel_time:.4f} seconds")
    print(f"Sequential version took {sequential_time:.4f} seconds")
    print(f"Speedup: {sequential_time / parallel_time:.2f}x")

    # Compare results
    print("\nParallel best policies:")
    print(type(parallel_result[0]['j']), parallel_result[0])
    print("\nSequential best policies:")
    print(sequential_result[0])

if __name__ == "__main__":
    main()
