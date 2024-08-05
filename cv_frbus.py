import sys
from daly import *
from find_policy import *
import covasim as cv
sys.path.insert(0, '/home/mlq/fed model/pyfrbus')
from demos.sm_frbus import sm_frbus
sys.path.insert(0, '/home/mlq/fed model/sir_macro')
from covasim_sm import sir_macro_obj
sys.path.insert(0, '/home/mlq/fed model/covasim')
from simulations import Covasim
from joblib import Memory


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
        self.covasim_res = self.covasim_obj.custom_sim(self.start_stayhome, self.duration_stayhome)


    def run_frbus(self):
        self.frbus_res = self.frbus_obj.solve_custom_stayhome(start_lockdown_opt=self.start_stayhome, custom_lockdown_duration=self.duration_stayhome)
        # obj.plot_results()
        self.loss_gdp = abs(self.frbus_obj.loss_econ())
        # return frbus_obj

    def cal_loss_total(self):
        scale_factor = 331000000/self.covasim_obj.pars['pop_size']
        log_file = 'loss_log.txt'
        with open(log_file, 'a') as log:
            log.write("Loss_GDP,Loss_DALY,Loss_total,Start_week,Duration\n")  # Write header
            self.loss_econ_daly = cal_econ_daly_precise(self.covasim_res)*scale_factor
            self.loss_total = self.loss_gdp + self.loss_econ_daly
            # print("\n\nconcho\n", self.loss_gdp + loss_econ_daly)
            print("Writing to log file")
            log.write(f"{self.loss_gdp},{self.loss_econ_daly},{self.loss_total},{self.start_stayhome},{self.duration_stayhome}\n")

        return self.loss_total

    def run(self, start_stayhome, duration_stayhome):
        self.start_stayhome = start_stayhome
        self.duration_stayhome = duration_stayhome
        print("start-end main",self.start_stayhome, self.duration_stayhome)
        self.run_frbus()
        self.run_covasim()
        self.cal_loss_total()

        print("\n\nconmeo\n\n",abs(self.loss_total))

        return abs(self.loss_total)
        
    def optimize(self):

        policy = {'start_stayhome': 3, 'duration_stayhome': 5}
        # self.run(policy)
        self.best_policy, self.policy_history, self.loss_history = gradient_descent_with_adam(self.run, policy, verbose=True, epochs='auto',
                                                                         learning_rate=1, 
                                                                         save_policy_as='sample.json', integer_policy=True,
                                                                         log_file='log_new.csv')

    def optimize_parallel(self):
        # joblib
        # memory = Memory(location='.', verbose=0)
        policy = {'start_stayhome': 8, 'duration_stayhome': 11}
        # with limit_memory(8):
            # Your memory-intensive code here
        self.best_policy, self.policy_history, self.loss_history = joblib_parallel_gradient_descent_with_adam(
            self.run, policy, verbose=True, epochs='auto',
            learning_rate=1, 
            save_policy_as='sample.json', integer_policy=True)

    def plot_results(self, start_stayhome, duration_stayhome):
        self.start_stayhome = start_stayhome
        self.duration_stayhome = duration_stayhome
        self.run_frbus()






def main():
    obj = cv_frbus()
    obj.run(5,12)
    # obj.optimize_parallel()
    # obj.optimize()
    # print(obj.loss_total())
    obj.frbus_obj.plot_results()

    print("\n\nXGDP:", (obj.frbus_obj.custom_stayhome - obj.frbus_obj.data)["xgdp"].sum())

    print("\n\nXGDPN:", (obj.frbus_obj.custom_stayhome - obj.frbus_obj.data)["xgdpn"].sum())




    # obj.covasim_obj.orig_sim()


    obj.covasim_obj.custom_stayhome_res.to_csv('SAH_5_12_30per.csv', index=False)
    # obj.covasim_obj.orig_sim_obj.to_df().to_csv('no_SAH_5_8.csv', index=False)


    print(f"{obj.loss_gdp},{obj.loss_econ_daly},{obj.loss_total},{obj.start_stayhome},{obj.duration_stayhome}\n")

    
    # cv.plot_compare(obj.covasim_obj.custom_stayhome_res, do_save=True)

    
    cv_fig = obj.covasim_obj.custom_sim_obj.plot(do_save=True)





    # s1 = cv.Sim(beta=0.01, label='Low')
    # s2 = cv.Sim(beta=0.02, label='High')
    # cv.parallel(obj.covasim_obj.orig_sim_obj, obj.covasim_obj.custom_sim_obj).plot(do_save=True)
    # msim = cv.parallel([s1, s2], keep_people=True)


    msim = cv.MultiSim([obj.covasim_obj.orig_sim_obj, obj.covasim_obj.custom_sim_obj])
    msim_fig = msim.plot()


    # from datetime import datetime

    # # Assuming msim_fig is your existing figure with subplots
    # fig = msim_fig.figure

    # # Convert the date string to a datetime object
    # vax_start_date = datetime.strptime('2020-12-13', '%Y-%m-%d')

    # # Add vertical line to each subplot
    # for ax in fig.axes:
    #     ax.axvline(x=vax_start_date, color='gray', linestyle='--', linewidth=1, label='Start Vaccination')

    # # Adjust the legend to include the new line
    # handles, labels = ax.get_legend_handles_labels()
    # ax.legend(handles, labels, loc='best')

    # # Update the x-axis to ensure the new line is visible
    # for ax in fig.axes:
    #     ax.set_xlim(left=min(ax.get_xlim()[0], mdates.date2num(vax_start_date)))

    # # Redraw the figure
    # fig.canvas.draw()

    # Save the figure
    # fig.savefig('msim6-5.png', dpi=300, bbox_inches='tight')

    cv_fig.savefig('covasim_plot.png', dpi=300, bbox_inches='tight')

    cv.savefig(fig=msim_fig, filename="msim5-8.png", dpi=300)
    print(f"{obj.loss_gdp},{obj.loss_econ_daly},{obj.loss_total},{obj.start_stayhome},{obj.duration_stayhome}\n")



if __name__ == "__main__":
    main()