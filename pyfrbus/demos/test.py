# import pandas as pd
# import numpy as np
# def week_to_quarter(start_week, duration)->pd.Series:
#     """
#     calculate the coefficient of the stay-at-home orders
#     """
#     start_quarter = pd.Period(f"{start_week//52+2020}Q{start_week%52//13+1}")

#     end_week = start_week + duration
#     end_quarter = pd.Period(f"{(end_week)//52+2020}Q{(end_week)%52//13+1}")
#     print(start_quarter, end_quarter)

#     return series

# week_to_quarter(5, 10)

# def calculate_weekly_values(start_value_leh, lf, bool_values):
#     # Convert bool_values to numpy array
#     bool_values = np.array(bool_values)
    
#     # Calculate weekly values for leh
#     weekly_values_leh = start_value_leh * np.cumprod(1 - 0.019 * bool_values)
    
#     # Calculate weekly values for lur
#     weekly_values_lur = 1 - weekly_values_leh / lf
    
#     # Return the weekly values
#     return weekly_values_leh, weekly_values_lur

# # Test the function with a start value of (2020Q1w1) and a list of boolean values
# start_value_leh = 158.977973
# lf = 165.333428
# bool_values = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]  # Example boolean values for 13 weeks

# leh, lur = calculate_weekly_values(start_value_leh, lf, bool_values)

# print(leh)
# print(lur)
# print(np.average(leh))
# print(np.average(lur))




# def unemployment():
    # # Define the data for each dataframe
    # data_lf = {
    #     '2019Q1': 164.091895,
    #     '2019Q2': 163.972297,
    #     '2019Q3': 165.059192,
    #     '2019Q4': 165.677434,
    #     '2020Q1': 165.333428,
    #     '2020Q2': 159.682386,
    #     '2020Q3': 162.087216,
    #     '2020Q4': 162.400506,
    #     '2021Q1': 161.928409,
    #     '2021Q2': 162.784563,
    #     '2021Q3': 163.527099,
    #     '2021Q4': 164.087490,
    #     '2022Q1': 164.361515,
    #     '2022Q2': 164.718250,
    #     '2022Q3': 165.272741,
    #     '2022Q4': 165.534114,
    #     '2023Q1': 166.275400,
    #     '2023Q2': 166.833549,
    #     '2023Q3': 167.613620,
    #     '2023Q4': 167.763087
    # }

#     data_leh = {
#         "2019Q1": 157.745399,
#         "2019Q2": 157.953897,
#         "2019Q3": 159.065456,
#         "2019Q4": 159.748137,
#         "2020Q1": 158.977973,
#         "2020Q2": 154.765454,
#         "2020Q3": 153.850880,
#         "2020Q4": 155.888418,
#         "2021Q1": 156.687551,
#         "2021Q2": 156.406972,
#         "2021Q3": 157.126853,
#         "2021Q4": 157.487223,
#         "2022Q1": 157.631240,
#         "2022Q2": 157.465755,
#         "2022Q3": 157.950078,
#         "2022Q4": 157.809439,
#         "2023Q1": 157.702908,
#         "2023Q2": 157.714101,
#         "2023Q3": 157.669758,
#         "2023Q4": 157.663817
#     }

#     data_lur = {
#         "2019Q1": 3.867648,
#         "2019Q2": 3.670376,
#         "2019Q3": 3.631264,
#         "2019Q4": 3.578820,
#         "2020Q1": 3.844023,
#         "2020Q2": 11.166986,
#         "2020Q3": 8.836066,
#         "2020Q4": 6.750529,
#         "2021Q1": 6.242108,
#         "2021Q2": 5.939336,
#         "2021Q3": 5.133398,
#         "2021Q4": 4.178408,
#         "2022Q1": 3.849261,
#         "2022Q2": 3.672350,
#         "2022Q3": 3.566360,
#         "2022Q4": 3.581550,
#         "2023Q1": 3.515600,
#         "2023Q2": 3.563175,
#         "2023Q3": 3.696020,
#         "2023Q4": 3.770010
#     }

#     # Create dataframes from the data
#     df_lf = pd.DataFrame(list(data_lf.items()), columns=['Date', 'lf'])
#     df_leh = pd.DataFrame(list(data_leh.items()), columns=['Date', 'leh'])
#     df_lur = pd.DataFrame(list(data_lur.items()), columns=['Date', 'lur'])

#     # Print the dataframes
#     # print(df_lf)
#     # print(df_leh)
#     # print(df_lur)


    
# week_to_quarter(5, 208-6)
# week_to_quarter(5, 14-6)


import pandas as pd
import numpy as np

def calculate_weekly_values(start_value_leh, lf, bool_values):
    # Convert bool_values to numpy array
    bool_values = np.array(bool_values)
    
    # Calculate weekly values for leh
    weekly_values_leh = start_value_leh * np.cumprod(1 - 0.019 * bool_values)
    
    # Calculate weekly values for lur
    weekly_values_lur = 1 - weekly_values_leh / lf.iloc[:len(weekly_values_leh)]
    
    # Return the weekly values
    return weekly_values_leh, weekly_values_lur

def calculate_quarterly_average(start_value_leh, lf, start_week, duration):
    # Create a boolean array with 1s for the duration and 0s for the rest
    bool_values = np.zeros(start_week + duration)
    bool_values[start_week:start_week+duration] = 1

    # Resample `lf` series to weekly frequency using linear interpolation
    lf_weekly = lf.resample('W').interpolate()

    # Calculate weekly values
    weekly_values_leh, weekly_values_lur = calculate_weekly_values(start_value_leh, lf_weekly, bool_values)

    # Fill the missing weeks for the quarter with the last calculated value
    if (start_week + duration) % 13 != 0:
        end_week = ((start_week + duration) // 13 + 1) * 13
        last_calculated_value = weekly_values_leh[start_week + duration - 1]
        for i in range(1, end_week - (start_week + duration)+1):
            weekly_values_leh = np.append(weekly_values_leh , (weekly_values_leh[start_week + duration - i-1]))
            weekly_values_lur = np.append(weekly_values_lur , (weekly_values_lur[start_week + duration - i-1]))


    # Convert weekly values to Series
    series_leh = pd.Series(weekly_values_leh)
    series_lur = pd.Series(weekly_values_lur)

    # Create a date range for the series index
    dates = pd.date_range(start='2020-01-01', periods=len(series_leh), freq='W')

    # Assign dates to series index
    series_leh.index = dates
    series_lur.index = dates

    print(series_leh)
    print(series_lur)

    # Convert the index to PeriodIndex with quarterly frequency
    series_leh.index = series_leh.index.to_period('Q')
    series_lur.index = series_lur.index.to_period('Q')

    # Resample the series to quarterly frequency and calculate mean
    quarterly_avg_leh = series_leh.groupby(series_leh.index).mean()
    quarterly_avg_lur = series_lur.groupby(series_lur.index).mean()

    print(quarterly_avg_leh)
    print(quarterly_avg_lur)
    # Return the quarterly averages and weekly series for verification
    return quarterly_avg_leh, quarterly_avg_lur, series_leh, series_lur

start_value_leh = 158.977973
lf = pd.Series({
    '2019Q1': 164.091895,
    '2019Q2': 163.972297,
    '2019Q3': 165.059192,
    '2019Q4': 165.677434,
    '2020Q1': 165.333428,
    '2020Q2': 159.682386,
    '2020Q3': 162.087216,
    '2020Q4': 162.400506,
    '2021Q1': 161.928409,
    '2021Q2': 162.784563,
    '2021Q3': 163.527099,
    '2021Q4': 164.087490,
    '2022Q1': 164.361515,
    '2022Q2': 164.718250,
    '2022Q3': 165.272741,
    '2022Q4': 165.534114,
    '2023Q1': 166.275400,
    '2023Q2': 166.833549,
    '2023Q3': 167.613620,
    '2023Q4': 167.763087
}, name='lf')

# Convert lf to a PeriodIndex with quarterly frequency
lf.index = pd.PeriodIndex(lf.index, freq='Q')

calculate_quarterly_average(start_value_leh, lf, 10, 12)



import pandas as pd
from datetime import timedelta

def week_to_quarter(week):
    # Create a date range starting from the beginning of 2020
    date_range = pd.date_range(start='2020-01-01', periods=week, freq='W')
    # Get the last date in the range
    end_date = date_range[-1]
    return end_date.to_period('Q')

# Example usage
print(week_to_quarter(1))   # First week of 2020
print(week_to_quarter(52))  # Last week of 2020
print(week_to_quarter(53))  # First week of 2021
print(week_to_quarter(260)) # A week in 2024