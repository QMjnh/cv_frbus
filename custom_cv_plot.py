import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

df_orig = pd.read_csv("/home/mlq/fed model/no-SAH.csv")
df_sah = pd.read_csv("/home/mlq/fed model/SAH_5_12_30per_aerr.csv")


fig, ax = plt.subplots(4, 1, figsize=(15, 13))
# ax = ax.flatten()

plt.subplots_adjust(top=0.95, bottom=0.05, left=0.1, right=0.95, hspace=0.55)
colors = ['tab:blue', 'tab:red']  # Specify the colors for the lines

fig.suptitle('COVID-19 Comparison (β$_{SAH}=0.3$)', fontsize=14, y=0.985, x=0.525)
# fig.suptitle('COVID-19 Scenarios (β=0.5)', fontsize=14, y=0.985, x=0.525)


for i in range(4):
    ax[i].set_facecolor('aliceblue')
    ax[i].spines['top'].set_visible(False)
    ax[i].spines['right'].set_visible(False)
    # ax[i].spines['bottom'].set_visible(False)
    # ax[i].spines['left'].set_visible(False)
    # ax[i].tick_params(axis='both', which='both', length=0)


ax[0].plot(df_orig['t'], df_orig['new_infections'], label='No Stay-at-Home', color=colors[0], alpha = 0.8)
ax[0].plot(df_sah['t'], df_sah['new_infections'], label='Stay-at-Home', color=colors[1], alpha = 0.8)
ax[0].set_title('New Infections')

# Extract the month and year from the 'date' column
df_orig['month_year'] = pd.to_datetime(df_orig['date']).dt.to_period('M')
df_sah['month_year'] = pd.to_datetime(df_sah['date']).dt.to_period('M')
# print(df_sah['month_year'].unique())

# Set the xticks for each subplot
for i in range(4):
    # print(df_orig['month_year'].unique()[::3])
    xtick_lst = []
    for j in df_orig['month_year'].unique()[::3]:
        # print(j)
        xtick_lst.append(int(df_orig[df_orig['month_year'] == j].iloc[0].loc['t']))
        # ax[i].set_xticks([first_row['month_year']])
        # ax[i].set_xticklabels([first_row['month_year']])

    # print(type(xtick_lst), xtick_lst)
    # print(type(xtick_lst[0]))
    ax[i].set_xticks(xtick_lst)
    # ax[i].set_xticklabels(df_orig['month_year'].unique()[::3], rotation=45)

    # Ensure the number of labels matches the number of ticks
    labels = [date.strftime('%m-%Y') for date in df_orig['month_year'].unique()[::3]]
    ax[i].set_xticklabels(labels, rotation=45)



ax[1].plot(df_orig['t'], df_orig['cum_infections'], label='No Stay-at-Home', color=colors[0], alpha = 0.8)
ax[1].plot(df_sah['t'], df_sah['cum_infections'], label='Stay-at-Home', color=colors[1], alpha = 0.8)
ax[1].set_title('Cumulative Infections')

ax[2].plot(df_orig['t'], df_orig['new_deaths'], label='No Stay-at-Home', color=colors[0], alpha = 0.8)
ax[2].plot(df_sah['t'], df_sah['new_deaths'], label='Stay-at-Home', color=colors[1], alpha = 0.8)
ax[2].set_title('New Deaths')

ax[3].plot(df_orig['t'], df_orig['cum_deaths'], label='No Stay-at-Home', color=colors[0], alpha = 0.8)
ax[3].plot(df_sah['t'], df_sah['cum_deaths'], label='Stay-at-Home', color=colors[1], alpha = 0.8)
ax[3].set_title('Cumulative Deaths')

start_vax = (pd.to_datetime("2020-12-13") - pd.to_datetime("2020-01-05")).days

start_sah = pd.to_datetime("2020-01-05") + pd.DateOffset(weeks=5)
end_sah = start_sah + pd.DateOffset(weeks=11)

start_sah = (start_sah - pd.to_datetime("2020-01-05")).days
end_sah = (end_sah - pd.to_datetime("2020-01-05")).days


for i in range(4):
    ax[i].grid(color='lightgray', linestyle='-', linewidth=0.5)
    # ax[i].set_xlabel('Days')
    # ax[i].set_ylabel('Count')
    ax[i].axvline(x=start_vax, color='forestgreen', linestyle='--', linewidth=1, label='Start Vaccination')
    ax[i].axvline(x=start_sah, color='dimgray', linestyle='--', linewidth=1, label='SAH Period')
    ax[i].axvline(x=end_sah, color='dimgray', linestyle='--', linewidth=1, )
    ax[i].legend()



plt.show()
plt.savefig('SAH_5_12_30per_aerr.png')