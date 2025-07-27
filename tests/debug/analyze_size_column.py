import sys
sys.path.append('utils')
import db_helper as db
import pandas as pd

# Get S column data 
with db.get_connection('orders') as conn:
    df = pd.read_sql('SELECT [S] FROM [dbo].[xGREYSON_ORDER_LIST]', conn)

series = df['S']
non_null_series = series.dropna()

# Find problematic values
numeric_converted = pd.to_numeric(non_null_series.astype(str), errors='coerce')
problematic_mask = numeric_converted.isnull()
problematic_values = non_null_series[problematic_mask]

print('Total values:', len(non_null_series))
print('Successfully converted:', len(numeric_converted.dropna()))
print('Failed to convert:', len(problematic_values))
print('Unique problematic values:', problematic_values.unique()[:20])
