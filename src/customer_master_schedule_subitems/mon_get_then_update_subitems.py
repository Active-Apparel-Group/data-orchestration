"""
Script to fetch subitems from Monday.com and then update them.
- Runs mon_get_subitems_async.py to fetch and store subitems in the database.
- Then runs mon_update_subitems_async.py to update subitems in Monday.com based on the latest data.
"""
import subprocess
import sys
import os

# Paths to the scripts
GET_SCRIPT = os.path.join(os.path.dirname(__file__), 'mon_get_subitems_async.py')
UPDATE_SCRIPT = os.path.join(os.path.dirname(__file__), 'mon_update_subitems_async.py')

# Run the get script
print("[STEP 1] Fetching and storing subitems from Monday.com...")
get_result = subprocess.run([sys.executable, GET_SCRIPT], check=False)
if get_result.returncode != 0:
    print(f"[ERROR] mon_get_subitems_async.py failed with exit code {get_result.returncode}")
    sys.exit(get_result.returncode)

# Run the update script
print("[STEP 2] Updating subitems in Monday.com...")
update_result = subprocess.run([sys.executable, UPDATE_SCRIPT], check=False)
if update_result.returncode != 0:
    print(f"[ERROR] mon_update_subitems_async.py failed with exit code {update_result.returncode}")
    sys.exit(update_result.returncode)

print("[SUCCESS] Get and update workflow completed.")
