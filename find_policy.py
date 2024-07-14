from daly import *
from typing import Callable
import numpy as np
import json

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


def gradient_descent(f: Callable, policy: dict, learning_rate=0.01, epochs='auto', verbose=False, patience=100, save_policy_as=None):
    """
    This function estimates the gradient of a function f(x, y, z, ...) when the form of f() is unknown
    f: the loss function to be estimated the gradient of
    policy: the dictionary of parameters to optimize
    learning_rate: the rate at which the gradient is updated
    epochs: the number of epochs to update the gradient, or 'auto' for automatic stopping
    verbose: whether to print progress information
    patience: number of epochs to wait for improvement before stopping (when epochs='auto')
    save_policy_as: the name of the file to save the best policy as a JSON object
    """
    policy_history = []  # Store the policy parameters at each epoch
    loss_history = []  # Store the loss at each epoch

    print("Initial Policy:", policy)
    print("Starting Gradient Descent...")

    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0

    while True:
        for parameter in policy.keys():
            # print("parameter", parameter)
            partial_derivative, current_loss = partial_derivative_estimate(f, param_name=parameter, **policy)
            policy[parameter] -= learning_rate * partial_derivative
            # print("after update:", policy[parameter])

        # current_loss = f(**policy)
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

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    # Convert and write JSON object to file
    if save_policy_as:
        with open("sample.json", "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history

def gradient_descent_with_adam(f:Callable, policy:dict, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8, epochs='auto', verbose=False, patience=100, save_policy_as=None):
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
    """
    policy_history = []  # Store the policy parameters at each epoch
    loss_history = []  # Store the loss at each epoch
    m = {key: 0 for key in policy.keys()}  # Initialize 1st moment vector
    v = {key: 0 for key in policy.keys()}  # Initialize 2nd moment vector

    print("Initial Policy", policy)
    print("Starting Gradient Descent with Adam...")
    
    best_loss = float('inf')
    epochs_without_improvement = 0
    epoch = 0
    
    while True:
        for param_name in policy.keys():
            print("param_name", param_name)
            # Estimate the gradient for the current parameter
            gradient, current_loss = partial_derivative_estimate(f, param_name=param_name, **policy)
            
            # Update biased first moment estimate
            m[param_name] = beta1 * m[param_name] + (1 - beta1) * gradient
            # Update biased second raw moment estimate
            v[param_name] = beta2 * v[param_name] + (1 - beta2) * (gradient ** 2)
            # Compute bias-corrected first moment estimate
            m_hat = m[param_name] / (1 - beta1 ** (epoch + 1))
            # Compute bias-corrected second raw moment estimate
            v_hat = v[param_name] / (1 - beta2 ** (epoch + 1))
            # Update the parameter
            policy[param_name] -= learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
        
        # current_loss = f(**policy)
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
        elif epoch >= epochs - 1:  # -1 because epoch is 0-indexed
            break

        epoch += 1

    best_policy = policy_history[np.argmin(loss_history)]
    print("Epochs ran:", epoch + 1)
    print("Best policy:", best_policy)
    print("Best loss:", np.min(loss_history))

    # Convert and write JSON object to file
    if save_policy_as:
        with open("sample.json", "w") as outfile: 
            json.dump(best_policy, outfile)
        print(f"Best policy saved as {save_policy_as}")

    return best_policy, policy_history, loss_history


class GD():
    def __init__(loss_func:Callable, policy:dict, learning_rate=0.001, derivative_step = .0001,
                 beta1=0.9, beta2=0.999, epsilon=1e-8,
                 epochs='auto', verbose=False, patience=100, save_policy_as=None):
        self.loss = None
        self.policy = policy
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.epochs = epochs
        self.verbose = verbose
        self.patience = patience
        self.save_policy_as = save_policy_as
        self.derivative_step = derivative_step
        self.loss_func = loss_func

        self.policy_history = None
        self.loss_history = None
        self.best_policy = None

    def partial_derivative_estimate(self, param_name:str, **kwargs):
        """
        This function is to estimate the PARTIAL derivative of function f(x, y, z, ...) when the form of f() is unknown
        f: the loss function to be estimated the derivative of
        h: the infinitesimal change in x to estimate the derivative
        x: the variable to which the derivative is estimated with respect to
        """
        # print("parital derivative is called!!!")
        kwargs_plus_h = kwargs.copy()
        kwargs_plus_h[param_name] += self.derivative_step
        self.loss = self.loss_func(**kwargs)
        return (self.loss_func(**kwargs_plus_h) - self.loss) / self.derivative_step


    def gradient_descent(self):
        """
        This function estimates the gradient of a function f(x, y, z, ...) when the form of f() is unknown
        f: the loss function to be estimated the gradient of
        policy: the dictionary of parameters to optimize
        learning_rate: the rate at which the gradient is updated
        epochs: the number of epochs to update the gradient, or 'auto' for automatic stopping
        verbose: whether to print progress information
        patience: number of epochs to wait for improvement before stopping (when epochs='auto')
        save_policy_as: the name of the file to save the best policy as a JSON object
        """
        self.policy_history = []  # Store the policy parameters at each epoch
        self.loss_history = []  # Store the loss at each epoch

        print("Initial Policy:", self.policy)
        print("Starting Gradient Descent...")

        best_loss = float('inf')
        epochs_without_improvement = 0
        epoch = 0

        while True:
            for parameter in self.policy.keys():
                # print("parameter", parameter)
                partial_derivative = self.partial_derivative_estimate(param_name=parameter, **self.policy)
                self.policy[parameter] -= self.learning_rate * partial_derivative
                # print("after update:", policy[parameter])

            current_loss = self.loss
            if current_loss < 0:
                print("Negative loss encountered in GD. Exiting...")
                break
            self.policy_history.append(self.policy.copy())
            self.loss_history.append(current_loss)

            if self.verbose:
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
                if epochs_without_improvement >= self.patience:
                    print(f"Stopping: No improvement for {self.patience} epochs.")
                    break
            elif epoch >= self.epochs - 1:  # -1 because epoch is 0-indexed
                break

            epoch += 1

        self.best_policy = self.policy_history[np.argmin(self.loss_history)]
        print("Epochs ran:", epoch + 1)
        print("Best policy:", self.best_policy)
        print("Best loss:", np.min(self.loss_history))

        # Convert and write JSON object to file
        if self.save_policy_as:
            with open("sample.json", "w") as outfile: 
                json.dump(self.best_policy, outfile)
            print(f"Best policy saved as {self.save_policy_as}")

        return self.best_policy, self.policy_history, self.loss_history

    def gradient_descent_with_adam():
        pass















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