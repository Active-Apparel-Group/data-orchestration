"""
Universal Token Manager
Purpose: Unified token management for Power BI and Power Automate operations
Location: pipelines/utils/token_manager.py
"""
import os
import sys
import yaml
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

# Import project utilities (already in pipelines/utils)
import db_helper as db
import logger_helper

class UniversalTokenManager:
    """
    Universal token manager for multiple Azure service accounts
    Supports Power BI, Power Automate, and other Azure services
    """
    
    def __init__(self, config_path: str = "pipelines/utils/powerbi_config.yaml"):
        """Initialize with configuration file"""
        self.logger = logger_helper.get_logger(__name__)
        
        # Handle relative paths from workspace root
        if not Path(config_path).is_absolute():
            # Find workspace root (has pipelines/ folder)
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "pipelines").exists():
                    workspace_root = current
                    break
                current = current.parent
            else:
                raise FileNotFoundError("Could not find workspace root")
            
            self.config_path = workspace_root / config_path
        else:
            self.config_path = Path(config_path)
            
        self.config = self._load_config()
        self.db_config = db.load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Expand environment variables
            config = self._expand_env_vars(config)
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise
    
    def _expand_env_vars(self, obj):
        """Recursively expand environment variables in config"""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            value = os.getenv(env_var)
            if value is None:
                self.logger.warning(f"Environment variable {env_var} not found")
                return obj
            return value
        return obj
    
    def get_token(self, profile_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get token for specified credential profile
        
        Args:
            profile_name: Name of credential profile from config
            force_refresh: Force new token even if cached version exists
            
        Returns:
            Dict containing token info and metadata
        """
        self.logger.info(f"[TOKEN] Requesting token for profile: {profile_name}")
        
        # Get profile configuration
        if profile_name not in self.config['credential_profiles']:
            raise ValueError(f"Profile '{profile_name}' not found in configuration")
        
        profile = self.config['credential_profiles'][profile_name]
        
        # Check for cached token first
        if not force_refresh:
            cached_token = self._get_cached_token(profile_name)
            if cached_token:
                self.logger.info(f"[TOKEN] Using cached token for {profile_name}")
                return cached_token
        
        # Get new token
        self.logger.info(f"[TOKEN] Fetching new token for {profile_name}")
        token_data = self._fetch_new_token(profile)
        
        # Store in database
        self._store_token(profile_name, token_data, profile)
        
        return token_data
    
    def _get_cached_token(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Check for valid cached token in database using existing log.BearerTokens table"""
        try:
            # Use existing log.BearerTokens table with actual column names
            sql = """
            SELECT TOP 1 
                bearerToken as access_token,
                expiresOn as expires_at,
                dateRetrieved as created_at,
                token_type
            FROM log.BearerTokens 
            WHERE expiresOn > GETDATE()
                AND token_type = ?
            ORDER BY dateRetrieved DESC
            """
            
            # Determine token type based on profile
            token_type = 'powerbi' if 'powerbi' in profile_name.lower() else 'power_automate'
            
            result = db.run_query(sql, 'orders', params=(token_type,))
            
            if not result.empty:
                token_row = result.iloc[0]
                return {
                    'access_token': token_row['access_token'],
                    'expires_at': token_row['expires_at'], 
                    'token_type': 'Bearer',
                    'profile_name': profile_name,
                    'source': 'cached'
                }
                        
        except Exception as e:
            self.logger.warning(f"Error checking cached token: {e}")
            
        return None
    
    def _fetch_new_token(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch new token from Azure AD"""
        
        # Build token request
        token_url = f"https://login.microsoftonline.com/{profile['tenant_id']}/oauth2/v2.0/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': profile['client_id'],
            'client_secret': profile['client_secret'],
            'scope': profile['scope']
        }
        
        self.logger.info(f"[AUTH] Requesting token from: {token_url}")
        self.logger.info(f"[AUTH] Scope: {profile['scope']}")
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_response = response.json()
            
            # Calculate expiration
            expires_in = token_response.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            token_data = {
                'access_token': token_response['access_token'],
                'token_type': token_response.get('token_type', 'Bearer'),
                'expires_in': expires_in,
                'expires_at': expires_at,
                'scope': profile['scope'],
                'source': 'fresh'
            }
            
            self.logger.info(f"[TOKEN] Successfully obtained token (expires in {expires_in}s)")
            return token_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"[AUTH] Token request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"[AUTH] Response: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"[TOKEN] Unexpected error: {e}")
            raise
    
    def _store_token(self, profile_name: str, token_data: Dict[str, Any], profile: Dict[str, Any]):
        """Store token in database using existing log.InsertBearerToken stored procedure"""
        try:
            # Determine token type based on profile
            token_type = 'powerbi' if 'powerbi' in profile_name.lower() else 'power_automate'
            
            # Use existing stored procedure from load_token.py pattern with token_type
            store_sql = """
            EXEC log.InsertBearerToken 
                @bearerToken = ?, 
                @expires_in = ?,
                @token_type = ?
            """
            
            # Execute using existing db_helper pattern
            rows_affected = db.execute(
                store_sql, 
                "orders", 
                params=(token_data['access_token'], token_data['expires_in'], token_type)
            )
            
            self.logger.info(f"[DB] Token stored successfully for profile: {profile_name} (type: {token_type})")
            self.logger.info(f"[DB] Database rows affected: {rows_affected}")
            
            # Verify storage using existing table
            verify_sql = "SELECT COUNT(*) as token_count FROM log.BearerTokens WHERE token_type = ?"
            result = db.run_query(verify_sql, "orders", params=(token_type,))
            token_count = result.iloc[0]['token_count']
            self.logger.info(f"[DB] Total {token_type} tokens in database: {token_count}")
            
        except Exception as e:
            self.logger.warning(f"[DB] Failed to store token: {e}")
            # Don't raise - token is still valid even if storage fails
    
    def get_all_tokens(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get tokens for all configured profiles
        
        Args:
            force_refresh: Force refresh all tokens
            
        Returns:
            Dict mapping profile names to token data
        """
        self.logger.info("[TOKEN] Fetching tokens for all profiles")
        
        tokens = {}
        profiles = self.config['credential_profiles'].keys()
        
        for profile_name in profiles:
            try:
                token_data = self.get_token(profile_name, force_refresh)
                tokens[profile_name] = token_data
                self.logger.info(f"[TOKEN] SUCCESS {profile_name}: Success")
                
            except Exception as e:
                self.logger.error(f"[TOKEN] FAILED {profile_name}: {e}")
                tokens[profile_name] = {'error': str(e)}
        
        return tokens
    
    def validate_token(self, profile_name: str, token_data: Dict[str, Any]) -> bool:
        """
        Validate token by making a test API call
        
        Args:
            profile_name: Name of the credential profile
            token_data: Token data to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        profile = self.config['credential_profiles'][profile_name]
        
        # Different validation endpoints based on scope
        if 'powerbi' in profile['scope']:
            test_url = "https://api.powerbi.com/v1.0/myorg/groups"
        elif 'management.azure.com' in profile['scope']:
            test_url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
        else:
            self.logger.warning(f"No validation endpoint for scope: {profile['scope']}")
            return True  # Assume valid if we can't test
        
        headers = {
            'Authorization': f"{token_data['token_type']} {token_data['access_token']}",
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(test_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"[VALIDATE] SUCCESS {profile_name}: Token is valid")
                return True
            elif response.status_code == 401:
                self.logger.warning(f"[VALIDATE] WARNING {profile_name}: 401 - May need admin consent")
                return False
            else:
                self.logger.warning(f"[VALIDATE] WARNING {profile_name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"[VALIDATE] {profile_name}: {e}")
            return False

# Factory function for easy usage
def create_token_manager() -> UniversalTokenManager:
    """Factory function to create token manager instance"""
    return UniversalTokenManager()
