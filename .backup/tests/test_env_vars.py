import os

print("=== DIRECT ENVIRONMENT ACCESS TEST ===")
print("Testing if environment variables from .env files are available directly in container")
print()

# Test the specific variables from your docker inspect output
test_vars = [
    'DB_ORDERS_PORT',
    'DB_QUICKDATA_HOST', 
    'DB_ORDERS_USERNAME',
    'DB_DMS_USERNAME',
    'DB_WMS_USERNAME',
    'DB_ORDERS_HOST',
    'DB_ORDERS_DATABASE',
    'SECRET_DB_ORDERS_PORT',
    'SECRET_DB_QUICKDATA_HOST'
]

print("=== Testing Environment Variables ===")
found_vars = 0
for var in test_vars:
    value = os.getenv(var)
    if value:
        found_vars += 1
        if 'SECRET' in var:
            print(f"{var}: [SECRET - LENGTH {len(value)}]")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT FOUND")

print(f"\nFound {found_vars} out of {len(test_vars)} variables")

# Show all DB_* variables
print("\n=== All DB_* Variables ===")
db_vars = {k: v for k, v in os.environ.items() if k.startswith('DB_')}
for key, value in sorted(db_vars.items())[:10]:
    print(f"{key}: {value}")

print(f"\nTotal DB_* variables: {len(db_vars)}")

# Show all SECRET_DB_* variables  
print("\n=== All SECRET_DB_* Variables ===")
secret_vars = {k: v for k, v in os.environ.items() if k.startswith('SECRET_DB_')}
for key in sorted(secret_vars.keys())[:10]:
    print(f"{key}: [PRESENT]")

print(f"\nTotal SECRET_DB_* variables: {len(secret_vars)}")

if db_vars or secret_vars:
    print("\n✅ SUCCESS: Environment variables ARE available in container!")
    print("   Problem is with envs.* syntax, not the variables themselves")
else:
    print("\n❌ FAILURE: No environment variables found in container")

# Show ALL environment variables (first 30)
print("\n=== ALL ENVIRONMENT VARIABLES (First 30) ===")
all_vars = dict(os.environ)
for i, (key, value) in enumerate(sorted(all_vars.items())):
    if i >= 30:
        break
    if 'PASSWORD' in key or 'SECRET' in key:
        print(f"{key}: [HIDDEN]")
    else:
        display_value = value[:50] + "..." if len(str(value)) > 50 else value
        print(f"{key}: {display_value}")

print(f"\n... and {len(all_vars) - 30} more variables")
print(f"Total environment variables: {len(all_vars)}")
