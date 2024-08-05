from daly import *
from typing import Callable
import numpy as np
import json
from math import ceil, floor
from joblib import Parallel, delayed
import csv

import multiprocessing
from functools import partial
from joblib import Memory
import traceback

def partial_derivative_estimate(f:Callable, param_name:str, h=.0001, current_loss=None, **kwargs):
    """
    This function is to estimate the PARTIAL derivative of function f(x, y, z, ...) when the form of f() is unknown
    f: the loss function to be estimated the derivative of
    h: the infinitesimal change in x to estimate the derivative
    param_name: the parameter name to which the derivative is estimated with respect to
    current_loss: the pre-calculated loss for the current parameters, if not provided, it will be calculated
    """
    kwargs_plus_h = kwargs.copy()
    kwargs_plus_h[param_name] += h
    
    if not current_loss:
        loss = f(**kwargs)
        derivative = (f(**kwargs_plus_h) - loss) / h
        # print("derivative", derivative)
        return derivative, loss
    else:
        derivative = (f(**kwargs_plus_h) - current_loss) / h
        # print("derivative", derivative)
        return derivative


def gradient_descent(f: Callable, policy: dict, learning_rate=0.01, epochs='auto', verbose=False, patience=100, save_policy_as=None, integer_policy=False):
    """
    This function estimates the gradient of a function f(x, y, z, ...) when the form of f() is unknown
    f: the loss function to be estimated the gradient of
    policy: the dictionary of parameters to optimize
    learning_rate: the rate at which the gradient is updated
    epochs: the number of epochs to update the gradient, or 'auto' for automatic stopping
    verbose: whether to print progress information
    patience: number of epochs to wait for improvement before stopping (when epochs='auto')
    save_policy_as: the name of the file to save the best policy as a JSON object
    integer_policy: whether to round the policy parameters
    """
    policy_history = []  # Store the policy parameters at each epoch
    loss_history = []  # Store the loss at each epoch

    print("Initial Policy", policy)
    print("Starting Gradient Descent...")
    
    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0
    
    with open(log_file, 'w', newline='') as csvfile:
        fieldnames = ['epoch', 'loss'] + list(policy.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        while True:
            gradients = {}
            current_loss = None
            
            # Compute all gradients first
            for i, param_name in enumerate(policy.keys()):
                if i == 0:
                    # For the first parameter, calculate both gradient and loss
                    if integer_policy:
                        gradient, current_loss = partial_derivative_estimate(f, h=1, param_name=param_name, **policy)
                    else:
                        gradient, current_loss = partial_derivative_estimate(f, param_name=param_name, **policy)
                else:
                    # For subsequent parameters, use the previously calculated loss
                    if integer_policy:
                        gradient = partial_derivative_estimate(f, h=1, param_name=param_name, current_loss=current_loss, **policy)
                    else:
                        gradient = partial_derivative_estimate(f, param_name=param_name, current_loss=current_loss, **policy)
                gradients[param_name] = gradient
            
            # Now update all parameters
            for param_name in policy.keys():
                gradient = gradients[param_name]
                # Update the parameter
                update = learning_rate * gradient
                if integer_policy:
                    policy[param_name] = policy[param_name] - ceil(update)
                else:
                    policy[param_name] -= update

            if current_loss < 0:
                print("Negative loss encountered in GD. Exiting...")
                break
            if verbose:
                print(f'Epoch {epoch}: {policy}')
                print(f'Loss: {current_loss}')
            policy_history.append(policy.copy())
            loss_history.append(current_loss)

            # Write to CSV file
            row = {'epoch': epoch, 'loss': current_loss}
            row.update(policy)
            writer.writerow(row)
            csvfile.flush()  # Ensure it's written immediately

            # Check for improvement
            if current_loss < best_loss:
                best_loss = current_loss
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1

            # Stopping criterion
            if epochs == 'auto':
                if epochs_without_improvement >= patience:
                    print(f"Stopping: No improvement for {patience} epochs.")
                    break
            elif epoch >= epochs - 1:  # -1 because epoch is 0-indexed
                break

            epoch += 1

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history



def gradient_descent_with_adam(f:Callable, policy:dict, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8, epochs='auto', verbose=False, patience=100, save_policy_as=None, integer_policy=False, log_file='gradient_descent_log.csv'):
    """
    This function implements the gradient descent algorithm with Adam optimization to find the policy parameters that minimize the total economic loss.
    f: the loss function to be estimated the gradient of
    policy: the dictionary of parameters to optimize
    learning_rate: the rate at which the gradient is updated
    beta1, beta2: exponential decay rates for the moment estimates
    epsilon: small constant for numerical stability
    epochs: the number of epochs to update the gradient, or 'auto' for automatic stopping
    verbose: whether to print progress information
    patience: number of epochs to wait for improvement before stopping (when epochs='auto')
    save_policy_as: the name of the file to save the best policy as a JSON object
    integer_policy: whether to round the policy parameters to integers
    """
    policy_history = []
    loss_history = []
    m = {key: 0 for key in policy.keys()}
    v = {key: 0 for key in policy.keys()}

    print("Initial Policy", policy)
    print("Starting Gradient Descent with Adam...")
    
    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0
    
    with open(log_file, 'w', newline='') as csvfile:
        fieldnames = ['epoch', 'loss'] + list(policy.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        while True:
            gradients = {}
            current_loss = None
            
            # Compute all gradients first
            for i, param_name in enumerate(policy.keys()):
                print("Param", param_name)
                if i == 0:
                    # For the first parameter, calculate both gradient and loss
                    if integer_policy:
                        gradient, current_loss = partial_derivative_estimate(f, h=1, param_name=param_name, **policy)
                    else:
                        gradient, current_loss = partial_derivative_estimate(f, param_name=param_name, **policy)
                    print(f"gradient {param_name}", gradient)
                else:
                    # For subsequent parameters, use the previously calculated loss
                    if integer_policy:
                        gradient = partial_derivative_estimate(f, h=1, param_name=param_name, current_loss=current_loss, **policy)
                    else:
                        gradient = partial_derivative_estimate(f, param_name=param_name, current_loss=current_loss, **policy)
                    print(f"gradient {param_name}", gradient)
                gradients[param_name] = gradient
            
            # Now update all parameters
            for param_name in policy.keys():
                gradient = gradients[param_name]
                
                # Update biased first moment estimate
                m[param_name] = beta1 * m[param_name] + (1 - beta1) * gradient
                # Update biased second raw moment estimate
                v[param_name] = beta2 * v[param_name] + (1 - beta2) * (gradient ** 2)
                # Compute bias-corrected first moment estimate
                m_hat = m[param_name] / (1 - beta1 ** (epoch + 1))
                # Compute bias-corrected second raw moment estimate
                v_hat = v[param_name] / (1 - beta2 ** (epoch + 1))
                # Update the parameter
                update = learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
                print(f"pre update {param_name}", update)
                if integer_policy:
                    if update < 0:
                        update = floor(update)
                    else:
                        update = ceil(update)
                    policy[param_name] = policy[param_name] - update
                    if policy[param_name] < 1:
                        policy[param_name] = 1
                    print(f"post update {param_name}", update, policy[param_name])
                else:
                    policy[param_name] -= update

            if current_loss < 0:
                print("Negative loss encountered in GDwA. Exiting...")
                break
            if verbose:
                print(f'Epoch {epoch}: {policy}')
                print(f'Loss: {current_loss}')
            policy_history.append(policy.copy())
            loss_history.append(current_loss)

            # Write to CSV file
            row = {'epoch': epoch, 'loss': current_loss}
            row.update(policy)
            writer.writerow(row)
            csvfile.flush()  # Ensure it's written immediately

            # Check for improvement
            if current_loss < best_loss:
                best_loss = current_loss
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1

            # Stopping criterion
            if epochs == 'auto':
                if epochs_without_improvement >= patience:
                    print(f"Stopping: No improvement for {patience} epochs.")
                    break
            elif epoch >= epochs - 1:  # -1 because epoch is 0-indexed
                break

            epoch += 1

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history


def compute_gradient(f, param_name, policy, integer_policy):
    try:
        if integer_policy:
            gradient, loss = partial_derivative_estimate(f, h=1, param_name=param_name, **policy)
        else:
            gradient, loss = partial_derivative_estimate(f, param_name=param_name, **policy)
        return param_name, gradient, loss
    except Exception as e:
        return param_name, str(e), traceback.format_exc()

def parallel_gradient_descent(f: Callable, policy: dict, learning_rate=0.01, h=0.0001, epochs='auto', verbose=False, patience=100, save_policy_as=None, integer_policy=False):
    policy_history = []
    loss_history = []

    print("Initial Policy:", policy)
    print("Starting Gradient Descent...")

    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0

    # Create a pool of worker processes
    num_cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_cores)

    while True:
        # Prepare the function for parallel computation
        compute_grad_func = partial(compute_gradient, f, policy=policy, h=h, integer_policy=integer_policy)
        
        # Compute gradients in parallel
        results = pool.map(compute_grad_func, policy.keys())
        
        gradients = {}
        current_loss = None
        for param_name, gradient, loss in results:
            gradients[param_name] = gradient
            if current_loss is None:
                current_loss = loss

        # Update all parameters
        for parameter in policy.keys():
            if integer_policy:
                if gradients[parameter] < 0:
                    policy[parameter] = policy[parameter] - floor(learning_rate * gradients[parameter])
                else:
                    policy[parameter] = policy[parameter] - ceil(learning_rate * gradients[parameter])
            else:
                policy[parameter] -= learning_rate * gradients[parameter]

        if current_loss < 0:
            print("Negative loss encountered in GD. Exiting...")
            break
        policy_history.append(policy.copy())
        loss_history.append(current_loss)

        if verbose:
            print(f'epoch {epoch}: {policy}')
            print(f'Loss: {current_loss}')

        # Check for improvement
        if current_loss < best_loss:
            best_loss = current_loss
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        # Stopping criterion
        if epochs == 'auto':
            if epochs_without_improvement >= patience:
                print(f"Stopping: No improvement for {patience} epochs.")
                break
        elif epoch >= epochs - 1:  # -1 because epoch is 0-indexed
            break

        epoch += 1

    # Close the pool of worker processes
    pool.close()
    pool.join()

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    # Convert and write JSON object to file
    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history


def parallel_gradient_descent_with_adam(f:Callable, policy:dict, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8, epochs='auto', verbose=False, patience=100, save_policy_as=None, integer_policy=False):
    policy_history = []
    loss_history = []
    m = {key: 0 for key in policy.keys()}
    v = {key: 0 for key in policy.keys()}

    print("Initial Policy", policy)
    print("Starting Gradient Descent with Adam...")
    
    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0
    
    # Create a pool of worker processes
    num_cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_cores)
    
    while True:
        # Prepare the function for parallel computation
        compute_grad_func = partial(compute_gradient, f, policy=policy, integer_policy=integer_policy)
        
        # Compute gradients in parallel
        results = pool.map(compute_grad_func, policy.keys())
        
        gradients = {}
        current_loss = None
        for param_name, gradient, loss in results:
            gradients[param_name] = gradient
            if current_loss is None:
                current_loss = loss
        
        # Update all parameters
        for param_name in policy.keys():
            gradient = gradients[param_name]
            
            # Update biased first moment estimate
            m[param_name] = beta1 * m[param_name] + (1 - beta1) * gradient
            # Update biased second raw moment estimate
            v[param_name] = beta2 * v[param_name] + (1 - beta2) * (gradient ** 2)
            # Compute bias-corrected first moment estimate
            m_hat = m[param_name] / (1 - beta1 ** (epoch + 1))
            # Compute bias-corrected second raw moment estimate
            v_hat = v[param_name] / (1 - beta2 ** (epoch + 1))
            # Update the parameter
            update = learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
            if integer_policy:
                if update < 0:
                    policy[param_name] = policy[param_name] - floor(update)
                else:
                    policy[param_name] = policy[param_name] - ceil(update)
            else:
                policy[param_name] -= update

        if current_loss < 0:
            print("Negative loss encountered in GDwA. Exiting...")
            break
        if verbose:
            print(f'Epoch {epoch}: {policy}')
            print(f'Loss: {current_loss}')
        policy_history.append(policy.copy())
        loss_history.append(current_loss)

        # Check for improvement
        if current_loss < best_loss:
            best_loss = current_loss
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        # Stopping criterion
        if epochs == 'auto':
            if epochs_without_improvement >= patience:
                print(f"Stopping: No improvement for {patience} epochs.")
                break
        elif epoch >= epochs - 1:
            break

        epoch += 1

    # Close the pool of worker processes
    pool.close()
    pool.join()

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history




def joblib_parallel_gradient_descent_with_adam(run_func, policy, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8, epochs='auto', verbose=False, patience=100, save_policy_as=None, integer_policy=False):
    policy_history = []
    loss_history = []
    m = {key: 0 for key in policy.keys()}
    v = {key: 0 for key in policy.keys()}

    print("Initial Policy", policy)
    print("Starting Gradient Descent with Adam...")
    
    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0
    
    # memory = Memory(location='.', verbose=0)
    # @memory.cache
    def compute_gradient(param_name):
        try:
            if integer_policy:
                h = 1
            else:
                h = 0.0001
            policy_plus_h = policy.copy()
            policy_plus_h[param_name] += h
            loss = run_func(**policy)
            loss_plus_h = run_func(**policy_plus_h)
            gradient = (loss_plus_h - loss) / h
            return param_name, gradient, loss
        except Exception as e:
            return param_name, str(e), traceback.format_exc()

    while True:
        # Compute gradients in parallel
        try:
            results = Parallel(n_jobs=2, backend='threading')(delayed(compute_gradient)(param_name) for param_name in policy.keys())
        except Exception as e:
            print(f"Parallel execution failed: {str(e)}")
            break

        gradients = {}
        current_loss = None
        for param_name, gradient, loss in results:
            if isinstance(gradient, str):
                print(f"Error in computing gradient for {param_name}: {gradient}")
                print(f"Traceback: {loss}")
                return None, None, None
            gradients[param_name] = gradient
            if current_loss is None:
                current_loss = loss
        
        # Update all parameters
        for param_name in policy.keys():
            gradient = gradients[param_name]
            
            # Update biased first moment estimate
            m[param_name] = beta1 * m[param_name] + (1 - beta1) * gradient
            # Update biased second raw moment estimate
            v[param_name] = beta2 * v[param_name] + (1 - beta2) * (gradient ** 2)
            # Compute bias-corrected first moment estimate
            m_hat = m[param_name] / (1 - beta1 ** (epoch + 1))
            # Compute bias-corrected second raw moment estimate
            v_hat = v[param_name] / (1 - beta2 ** (epoch + 1))
            # Update the parameter
            update = learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
            if integer_policy:
                policy[param_name] = ceil(policy[param_name] - update)
            else:
                policy[param_name] -= update

        if current_loss < 0:
            print("Negative loss encountered in GDwA. Exiting...")
            break
        if verbose:
            print(f'Epoch {epoch}: {policy}')
            print(f'Loss: {current_loss}')
        policy_history.append(policy.copy())
        loss_history.append(current_loss)

        # Check for improvement
        if current_loss < best_loss:
            best_loss = current_loss
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        # Stopping criterion
        if epochs == 'auto':
            if epochs_without_improvement >= patience:
                print(f"Stopping: No improvement for {patience} epochs.")
                break
        elif epoch >= epochs - 1:
            break

        epoch += 1

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    if save_policy_as:
        with open(save_policy_as, "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history









def total_econ_loss(covasim_model, econ_model, policy):
    """
    This function is to calculate economic loss (daly + loss gdp) due to the pandemic
    """
    return cal_econ_daly(covasim_model, policy) + cal_gdp_loss(econ_model, policy)

def dummy_loss(j, y, k):
    return (k**2 + j ** 2 + y ** 2)**2

def main():
    # gradient_descent(total_econ_loss, policy)
    policy = {'j': 3, 'y': 5, 'k': 4}

    best_policy, policy_history, loss_history = gradient_descent(dummy_loss, policy, verbose=True, epochs='auto', save_policy_as='sample.json')
    # print("best policy", best_policy)
    # print("policy history", policy_history)
    # print("loss history", loss_history)


if __name__ == '__main__':
    main()