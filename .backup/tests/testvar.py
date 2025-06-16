import os
from dotenv import load_dotenv
load_dotenv()

"""Print environment variables related to the database configuration."""

# Retrieve environment variables

db_orders_port = os.getenv('DB_ORDERS_PORT')
db_quickdata_host = os.getenv('DB_QUICKDATA_HOST')
db_orders_username = os.getenv('DB_ORDERS_USERNAME')
db_dms_username = os.getenv('DB_DMS_USERNAME')
db_wms_username = os.getenv('DB_WMS_USERNAME')
  

# Print the values
print(f"DB_ORDERS_PORT: {db_orders_port}")
print(f"DB_QUICKDATA_HOST: {db_quickdata_host}")
print(f"DB_ORDERS_USERNAME: {db_orders_username}")
print(f"DB_DMS_USERNAME: {db_dms_username}")
print(f"DB_WMS_USERNAME: {db_wms_username}")