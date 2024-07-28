# first line: 402
    @memory.cache
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
