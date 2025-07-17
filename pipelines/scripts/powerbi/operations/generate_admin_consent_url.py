"""
Generate Admin Consent URL for Power BI API Access
Purpose: Generate the URL that your tenant admin needs to visit to grant consent
"""
import os
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

def generate_admin_consent_url():
    """Generate admin consent URL"""
    tenant_id = os.getenv('AZ_TENANT_ID')
    client_id = os.getenv('PBI_CLIENT_ID')
    
    # Power BI API scopes that need admin consent
    scopes = [
        "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
        "https://analysis.windows.net/powerbi/api/Dataflow.ReadWrite.All",
        "https://analysis.windows.net/powerbi/api/Workspace.Read.All"
    ]
    
    scope_string = " ".join(scopes)
    
    admin_consent_url = (
        f"https://login.microsoftonline.com/{tenant_id}/adminconsent"
        f"?client_id={client_id}"
        f"&scope={scope_string}"
        f"&redirect_uri=http://localhost:8080/callback"
    )
    
    print("=" * 80)
    print("ADMIN CONSENT REQUIRED FOR POWER BI API ACCESS")
    print("=" * 80)
    print()
    print("The authentication is working, but your app needs admin consent")
    print("for Power BI API access.")
    print()
    print("SEND THIS URL TO YOUR TENANT ADMIN:")
    print("-" * 40)
    print(admin_consent_url)
    print("-" * 40)
    print()
    print("What the admin needs to do:")
    print("1. Click the URL above")
    print("2. Sign in as tenant admin")
    print("3. Review and approve the requested permissions")
    print("4. The app will then have access to Power BI APIs")
    print()
    print("Required permissions:")
    for scope in scopes:
        print(f"  - {scope}")
    print()
    print("After admin consent, all authentication methods will work:")
    print("  - Service Principal (production)")
    print("  - Device Code Flow (testing)")
    print("  - User Delegation (interactive)")
    print("=" * 80)

if __name__ == "__main__":
    generate_admin_consent_url()
