import sys
from daly import *
from find_policy import cal_econ_daly
from find_policy_parallel import *
from scipy.stats import norm
sys.path.insert(0, '/home/mlq/fed model/pyfrbus')
from demos.sm_frbus import sm_frbus
sys.path.insert(0, '/home/mlq/fed model/sir_macro')
from covasim_sm import sir_macro_obj

class covasim_sm_frbus():
    def __init__(self):
        self.covasim_res = None
        self.sm_res = None
        self.frbus_res = None
        self.start_stayhome = None
        self.end_stayhome = None

        self.loss_total = None
        self.loss_gdp = None
        self.loss_econ_daly = None
    
    def run_covasim(self):
        covasim_df = pd.read_csv("/home/mlq/fed model/covasim/with-interventions.csv")
        
        simulated_pop = 1000000
        covasim_df['I'] = covasim_df['cum_infections'] / simulated_pop
        covasim_df['R'] = covasim_df['cum_recoveries'] / simulated_pop
        covasim_df['D'] = covasim_df['cum_deaths'] / simulated_pop
        covasim_df['T'] = covasim_df['new_infections'] / simulated_pop
        covasim_df['S'] = covasim_df['n_susceptible'] / simulated_pop
        covasim_df['deltaV'] = covasim_df['new_vaccinated'] / simulated_pop
        # Generate 208 points from a normal distribution
        x1 = np.linspace(norm.ppf(0.01), norm.ppf(0.99), 208)
        x2 = np.linspace(norm.ppf(0.1), norm.ppf(0.8), 208)
        # Calculate the PDF of the normal distribution at these points
        pdf_values = norm.pdf(x1)
        covasim_df = pd.DataFrame(pdf_values/10, columns=['I'])

        pdf_values = norm.pdf(x2)
        covasim_df = pd.concat([covasim_df, pd.DataFrame(pdf_values/10, columns=['D'])], axis=1)
        covasim_df['deltaV'] = np.full(208, 1/52)

        self.covasim_res = covasim_df


    def run_covasim_sm(self):
        sir = sir_macro_obj(self.covasim_res, start_stayhome=5, end_stayhome=208, epochs=1, sim_duraion=208, verbose=True, learning_rate=0.3, save_policy_as='/home/mlq/fed model/sample.json')
        best_policy, policy_history, loss_history = sir.find_best_ctax({'ctax_intensity': 0.5})
        self.sm_res = sir.best_simulation()


    def run_sm_frbus(self):
        obj = sm_frbus()
        custom_stayhome_data, targ_custom, traj_custom, inst_custom = obj.link_sm_frbus(self.sm_res)
        custom_stayhome_res = obj.solve_custom_stayhome(start_lockdown_opt="2020Q2", end_lockdown_opt="2020Q2", custom_lockdown_duration=17,
                                custom_stayhome_data=custom_stayhome_data,
                                targ_custom=targ_custom, traj_custom=traj_custom, inst_custom=inst_custom)
        # obj.plot_results()
        self.loss_gdp = obj.loss_econ()
        return obj

    def cal_loss_total(self):
        loss_econ_daly = cal_econ_daly(self.covasim_res)
        print("\n\nconcho\n", loss_econ_daly)
        self.loss_total = self.loss_gdp + loss_econ_daly
        return self.loss_gdp + loss_econ_daly

    def run(self):
        self.run_covasim()
        self.run_covasim_sm()
        self.run_sm_frbus()
        self.cal_loss_total()
        


def main():
    obj = covasim_sm_frbus()
    obj.run()
    # print(obj.loss_total())

if __name__ == "__main__":
    main()