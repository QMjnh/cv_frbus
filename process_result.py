import pandas as pd
import io
import numpy as np


with open('/home/mlq/fed model/result_spc.txt', 'r') as file:
    data = file.read()

# Function to process the data
def process_data(data):
    # Split the data into rows
    rows = data.split('Loss_GDP,Loss_DALY,Loss_total,Start_week,Duration')[1:]
    
    # Process each row
    processed_rows = []
    for row in rows:
        values = row.strip().split(',')
        processed_rows.append(values)
    
    # Create DataFrame
    df = pd.DataFrame(processed_rows, columns=['Loss_GDP', 'Loss_DALY', 'Loss_total', 'Start_week', 'Duration'])
    
    # Convert columns to appropriate data types
    df = df.astype({
        'Loss_GDP': float,
        'Loss_DALY': float,
        'Loss_total': float,
        'Start_week': int,
        'Duration': int
    })
    
    return df

# Process the data and create DataFrame
df = process_data(data)

print(df[df['Loss_total'] == np.min(df['Loss_total'])])

# Display the DataFrame
print(df)