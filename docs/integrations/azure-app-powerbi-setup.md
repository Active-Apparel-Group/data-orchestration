# Azure App Registration for Power BI Dataflow Operations

## Overview
This guide explains how to set up an Azure App Registration for Power BI dataflow operations using delegated authentication.

## Prerequisites
- Azure Active Directory admin access
- Power BI Pro or Premium license
- Access to Azure portal

## Azure App Registration Setup

### 1. Create App Registration
1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Set name: `PowerBI-Dataflow-Client`
5. Select **Accounts in this organizational directory only**
6. Click **Register**

### 2. Configure API Permissions
1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Power BI Service**
4. Choose **Delegated permissions**
5. Add these permissions:
   - `Dataset.ReadWrite.All`
   - `Dataflow.ReadWrite.All`
   - `Tenant.Read.All` (optional, for broader access)

### 3. Grant Admin Consent
1. In **API permissions**, click **Grant admin consent for [Your Tenant]**
2. Confirm the consent

### 4. Create Client Secret
1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Set description: `PowerBI-Dataflow-Secret`
4. Set expiration: **24 months** (recommended)
5. Click **Add**
6. **Copy the secret value immediately** (you won't see it again)

### 5. Note Configuration Values
Record these values for your environment configuration:
- **Application (client) ID** → `PA_CLIENT_ID`
- **Directory (tenant) ID** → `AZ_TENANT_ID` 
- **Client secret value** → `PA_CLIENT_SECRET`

## Environment Configuration

Add these variables to your `.env` file:
```bash
# Azure App Registration for Power BI
PA_CLIENT_ID=your-client-id-here
PA_CLIENT_SECRET=your-client-secret-here
AZ_TENANT_ID=your-tenant-id-here
```

## Testing the Configuration

Run the token retrieval script:
```bash
python pipelines/scripts/ingestion/load_token_new.py
```

Expected output:
```
🔐 Requesting Power BI bearer token from Azure AD...
✅ Power BI token retrieved successfully
🔑 Token preview: eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI...
⏳ Expires in: 3600 seconds (60 minutes)
🔍 Validating token with Power BI API...
✅ Token validation successful - Power BI API accessible
📦 Storing token in database...
✅ Token stored. Rows affected: 1
🎉 Power BI dataflow token retrieval and storage complete!
```

## Troubleshooting

### Common Issues

#### 1. "Invalid client" error
- Verify `PA_CLIENT_ID` is correct
- Ensure app registration exists and is enabled

#### 2. "Invalid client secret" error  
- Verify `PA_CLIENT_SECRET` is correct
- Check if client secret has expired

#### 3. "Insufficient privileges" error
- Ensure admin consent was granted
- Verify delegated permissions are configured
- Check if user has Power BI license

#### 4. Token validation fails
- Verify Power BI service permissions
- Check if user has access to Power BI tenant
- Ensure app has proper delegated permissions

### Permission Verification
You can verify permissions by checking the token at [jwt.ms](https://jwt.ms):
1. Copy the token from log output
2. Paste into jwt.ms
3. Check `scp` claim contains: `Dataset.ReadWrite.All Dataflow.ReadWrite.All`

## Security Notes

- Client secrets should be rotated regularly (every 6-24 months)
- Store credentials securely in key vault or environment variables
- Monitor app registration usage in Azure AD logs
- Follow principle of least privilege for permissions

## Related Scripts

- `load_token_new.py` - Updated Power BI token retrieval and storage
- `unified_token_manager.py` - Universal token management for multiple service accounts
- `universal_powerbi_manager.py` - Universal Power BI resource operations
- `order_list_dataflow_refresh.py` - Uses stored token for dataflow operations
