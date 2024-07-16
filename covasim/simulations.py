import covasim as cv

# Define baseline parameters and sim
pars = dict(
    pop_size  = 1_000_000,
    start_day = '2020-01-31',
    end_day   = '2023-12-31',
    pop_type  = 'hybrid',
    location = 'usa',
    pop_infected = 1,
    beta           = 0.13,                  
    rel_death_prob = 2.67,                    
)
orig_sim = cv.Sim(pars, label='Baseline')

# Define sim with simulations:
lockdown = cv.change_beta(days=['2020-03-24', '2020-05-04'], changes=[0.5, 1.0])
test = cv.test_prob(symp_prob=0.2, asymp_prob=0.001, start_day='2020-01-31')
ct = cv.contact_tracing(trace_probs=dict(h=1.0, s=0.5, w=0.5, c=0.3), do_plot=False)
pfizer = cv.vaccinate_prob(vaccine='pfizer', days='2020-12-24', prob=0.8)
sim = cv.Sim(pars, interventions=[lockdown, test, ct, pfizer], label='With interventions')

# Run simulations:
orig_sim.run()
no_interventions = orig_sim.to_df()
no_interventions.to_csv('no-interventions.csv', index=False)

sim.run()
with_interventions = sim.to_df()
with_interventions.to_csv('with-interventions.csv', index=False)