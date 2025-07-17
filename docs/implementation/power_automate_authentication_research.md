# Power Automate Logic App Authentication Research

## Problem Statement
Current Azure Resource Manager bearer tokens (scope: `https://management.azure.com/.default`) are not valid for triggering Power Automate Logic Apps via HTTP.

## Error Details
- **Status Code**: 401 Unauthorized
- **Error Code**: `CanNotReadSecurityToken`  
- **Message**: "The provided authentication token is not valid, Security token is either null or is not well formed Json web token."

## Current Token Configuration
```python
# Current scope used for token generation
scope = "https://management.azure.com/.default"
```

## Research: Logic App Authentication Methods

### Method 1: HTTP Trigger with SAS Key
Logic Apps with HTTP triggers typically use **Shared Access Signature (SAS)** authentication instead of bearer tokens.

**URL Structure**:
```
https://prod-27.australiasoutheast.logic.azure.com:443/workflows/{workflow-id}/triggers/manual/paths/invoke?api-version=2016-06-01&sp=<permissions>&sv=<version>&sig=<signature>
```

### Method 2: Azure AD Authentication for Logic Apps
If using Azure AD authentication, Logic Apps may require:
- **Resource Scope**: `https://management.azure.com/` (without .default)
- **Logic Apps Scope**: `https://management.core.windows.net/` 
- **Different API Scope**: Logic Apps may need a specific resource identifier

### Method 3: API Key Authentication
Some Logic Apps use simple API key authentication in headers:
```http
Authorization: Bearer <api-key>
Ocp-Apim-Subscription-Key: <subscription-key>
```

## Investigation Steps

### Step 1: Check Logic App Configuration
- Verify if HTTP trigger requires SAS authentication
- Check if Azure AD authentication is enabled
- Identify required permissions/scopes

### Step 2: Test Different Token Scopes
Test tokens with different scopes:
1. `https://management.core.windows.net/.default`
2. `https://management.azure.com/`
3. `https://graph.microsoft.com/.default`

### Step 3: SAS Key Alternative
If bearer tokens don't work, implement SAS key authentication:
- Extract SAS parameters from Logic App URL
- Use query parameters instead of Authorization header

## Next Actions
1. **Immediate**: Test with SAS query parameters instead of bearer token
2. **Alternative**: Generate token with Logic Apps-specific scope
3. **Fallback**: Use API key authentication if available

## References
- [Logic Apps HTTP Trigger Authentication](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-http-endpoint)
- [Azure AD Authentication for Logic Apps](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-azure-ad-authentication)
