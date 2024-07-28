import sys
from daly import *
from find_policy import *
# from find_policy_series import *
# from scipy.stats import norm
sys.path.insert(0, '/home/mlq/fed model/pyfrbus')
from demos.sm_frbus import sm_frbus
sys.path.insert(0, '/home/mlq/fed model/sir_macro')
from covasim_sm import sir_macro_obj
sys.path.insert(0, '/home/mlq/fed model/covasim')
from simulations import Covasim
from joblib import Memory



# import contextlib
# import resource

# @contextlib.contextmanager
# def limit_memory(max_mem_gb):
#     soft, hard = resource.getrlimit(resource.RLIMIT_AS)
#     resource.setrlimit(resource.RLIMIT_AS, (max_mem_gb * 1024 * 1024 * 1024, hard))
#     try:
#         yield
#     finally:
#         resource.setrlimit(resource.RLIMIT_AS, (soft, hard))







def global_run_function(start_stayhome, duration_stayhome):
    """
    because the sm_frbus or Covasim objects contain unpicklable elements.
    We need to avoid passing these objects through the multiprocessing pool.
    This approach creates a new cv_frbus object for each function call in the parallel processing, which should avoid the pickling issues.
    However, this might be less efficient if creating these objects is time-consuming.
    """
    obj = cv_frbus()
    return obj.run(start_stayhome, duration_stayhome)

class cv_frbus():
    def __init__(self, start_stayhome=None, duration_stayhome=None):
        self.frbus_obj = sm_frbus()
        self.covasim_obj = Covasim()

        self.covasim_res = None
        self.frbus_res = None
        self.start_stayhome = start_stayhome
        self.duration_stayhome = duration_stayhome

        self.loss_total = None
        self.loss_gdp = None
        self.loss_econ_daly = None

        self.best_policy = None
        self.policy_history = None
        self.loss_history = None
    
    def run_covasim(self):
        # covasim = Covasim()
        # covasim_df = covasim.custom_sim(self.start_stayhome, self.duration_stayhome)

        self.covasim_res = self.covasim_obj.custom_sim(self.start_stayhome, self.duration_stayhome)


    def run_frbus(self):
        self.frbus_res = self.frbus_obj.solve_custom_stayhome(start_lockdown_opt=self.start_stayhome, custom_lockdown_duration=self.duration_stayhome)
        # obj.plot_results()
        self.loss_gdp = self.frbus_obj.loss_econ()
        # return frbus_obj

    def cal_loss_total(self):
        with open(log_file, 'w') as log:
            log.write("Loss_GDP,Loss_DALY,Start_week,Duration\n")  # Write header
            loss_econ_daly = cal_econ_daly_precise(self.covasim_res)*331
            self.loss_total = self.loss_gdp + loss_econ_daly
            # print("\n\nconcho\n", self.loss_gdp + loss_econ_daly)
            log.write(f"{self.loss_gdp},{loss_econ_daly},{self.start_stayhome},{self.duration_stayhome}\n")

        return self.loss_total

    def run(self, start_stayhome, duration_stayhome):
        self.start_stayhome = start_stayhome
        self.duration_stayhome = duration_stayhome
        # print(self.start_stayhome, self.duration_stayhome)
        self.run_frbus()
        self.run_covasim()
        self.cal_loss_total()

        print("\n\nconmeo\n\n",abs(self.loss_total))

        return abs(self.loss_total)
        
    def optimize(self):

        policy = {'start_stayhome': 7, 'duration_stayhome': 13}
        # self.run(policy)
        self.best_policy, self.policy_history, self.loss_history = gradient_descent_with_adam(self.run, policy, verbose=True, epochs='auto',
                                                                         learning_rate=1, 
                                                                         save_policy_as='sample.json', integer_policy=True)

    def optimize_parallel(self):
        ## multiprocessing
        # policy = {'start_stayhome': 8, 'duration_stayhome': 11}
        
        # self.best_policy, self.policy_history, self.loss_history = parallel_gradient_descent_with_adam(
        #     global_run_function, policy, verbose=True, epochs='auto',
        #     learning_rate=1, 
        #     save_policy_as='sample.json', integer_policy=True)


        # joblib
        # memory = Memory(location='.', verbose=0)
        policy = {'start_stayhome': 8, 'duration_stayhome': 11}
        # with limit_memory(8):
            # Your memory-intensive code here
        self.best_policy, self.policy_history, self.loss_history = joblib_parallel_gradient_descent_with_adam(
            self.run, policy, verbose=True, epochs='auto',
            learning_rate=1, 
            save_policy_as='sample.json', integer_policy=True)

def main():
    obj = cv_frbus()
    # obj.run()
    # obj.optimize_parallel()
    obj.optimize()
    # print(obj.loss_total())
    obj.frbus_obj.plot_results()
    cv_fig = obj.covasim_obj.plot()
    cv_fig.savefig('covasim_plot.png', dpi=300, bbox_inches='tight')



if __name__ == "__main__":
    main()