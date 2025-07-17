"""
Power BI Operations Manager
Purpose: Universal manager for Power BI dataflows, datasets, reports, and datamarts
Location: pipelines/utils/powerbi_manager.py
"""
import os
import sys
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

# Import project utilities (already in pipelines/utils)
import db_helper as db
import logger_helper
from token_manager import UniversalTokenManager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: manually load .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

class PowerBIManager:
    """
    Universal Power BI operations manager
    Handles dataflows, datasets, reports, and datamarts
    """
    
    def __init__(self, config_path: str = "pipelines/utils/powerbi_config.yaml"):
        """Initialize Power BI manager"""
        self.logger = logger_helper.get_logger(__name__)
        self.token_manager = UniversalTokenManager(config_path)
        self.config = self.token_manager.config
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    def _get_headers(self, profile_name: str = "powerbi_primary") -> Dict[str, str]:
        """Get authorization headers for Power BI API"""
        token_data = self.token_manager.get_token(profile_name)
        return {
            'Authorization': f"{token_data['token_type']} {token_data['access_token']}",
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, url: str, profile_name: str = "powerbi_primary", **kwargs) -> requests.Response:
        """Make authenticated request to Power BI API"""
        headers = self._get_headers(profile_name)
        
        self.logger.info(f"[API] {method.upper()} {url}")
        
        try:
            response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            
            self.logger.info(f"[API] Response: {response.status_code}")
            
            if response.status_code == 401:
                self.logger.warning("[API] 401 Unauthorized - Token may be invalid or missing permissions")
            elif response.status_code >= 400:
                self.logger.error(f"[API] Error {response.status_code}: {response.text}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"[API] Request failed: {e}")
            raise
    
    def discover_workspaces(self, profile_name: str = "powerbi_primary") -> List[Dict[str, Any]]:
        """
        Discover available Power BI workspaces
        
        Returns:
            List of workspace information
        """
        self.logger.info("[DISCOVER] Fetching Power BI workspaces...")
        
        url = f"{self.base_url}/groups"
        response = self._make_request("GET", url, profile_name)
        
        if response.status_code == 200:
            workspaces = response.json().get('value', [])
            self.logger.info(f"[DISCOVER] Found {len(workspaces)} workspaces")
            
            for workspace in workspaces:
                self.logger.info(f"  - {workspace['name']} (ID: {workspace['id']})")
            
            return workspaces
        else:
            self.logger.error(f"[DISCOVER] Failed to fetch workspaces: {response.status_code}")
            return []
    
    def discover_dataflows(self, workspace_id: str, profile_name: str = "powerbi_primary") -> List[Dict[str, Any]]:
        """
        Discover dataflows in a workspace
        
        Args:
            workspace_id: Power BI workspace ID
            
        Returns:
            List of dataflow information
        """
        self.logger.info(f"[DISCOVER] Fetching dataflows in workspace: {workspace_id}")
        
        url = f"{self.base_url}/groups/{workspace_id}/dataflows"
        response = self._make_request("GET", url, profile_name)
        
        if response.status_code == 200:
            dataflows = response.json().get('value', [])
            self.logger.info(f"[DISCOVER] Found {len(dataflows)} dataflows")
            
            for dataflow in dataflows:
                self.logger.info(f"  - {dataflow['name']} (ID: {dataflow['objectId']})")
            
            return dataflows
        else:
            self.logger.error(f"[DISCOVER] Failed to fetch dataflows: {response.status_code}")
            return []
    
    def refresh_dataflow(self, workspace_id: str, dataflow_id: str, 
                        profile_name: str = "powerbi_primary", 
                        wait_for_completion: bool = False) -> Dict[str, Any]:
        """
        Refresh a Power BI dataflow
        
        Args:
            workspace_id: Power BI workspace ID
            dataflow_id: Dataflow ID to refresh
            profile_name: Token profile to use
            wait_for_completion: Whether to wait for refresh to complete
            
        Returns:
            Refresh operation result
        """
        self.logger.info(f"[REFRESH] Starting dataflow refresh: {dataflow_id}")
        
        url = f"{self.base_url}/groups/{workspace_id}/dataflows/{dataflow_id}/refreshes"
        
        # Start refresh
        response = self._make_request("POST", url, profile_name)
        
        result = {
            'dataflow_id': dataflow_id,
            'workspace_id': workspace_id,
            'started_at': datetime.now().isoformat(),
            'status': 'failed',
            'request_id': None
        }
        
        if response.status_code == 202:
            self.logger.info(f"[REFRESH] ✅ Dataflow refresh started successfully")
            result['status'] = 'started'
            
            # Extract request ID from location header if present
            location = response.headers.get('Location', '')
            if location:
                result['request_id'] = location.split('/')[-1]
            
            # Wait for completion if requested
            if wait_for_completion:
                result = self._wait_for_refresh_completion(workspace_id, dataflow_id, profile_name, result)
                
        else:
            self.logger.error(f"[REFRESH] ❌ Failed to start refresh: {response.status_code}")
            result['error'] = f"HTTP {response.status_code}: {response.text}"
        
        # Log result to database
        self._log_operation('dataflow_refresh', result)
        
        return result
    
    def _wait_for_refresh_completion(self, workspace_id: str, dataflow_id: str, 
                                   profile_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for dataflow refresh to complete"""
        self.logger.info("[REFRESH] Waiting for completion...")
        
        max_wait_time = 600  # 10 minutes
        check_interval = 30   # 30 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            # Check refresh status
            status = self.get_dataflow_refresh_status(workspace_id, dataflow_id, profile_name)
            
            if status and len(status) > 0:
                latest_refresh = status[0]
                refresh_status = latest_refresh.get('status', 'Unknown')
                
                self.logger.info(f"[REFRESH] Status check: {refresh_status} (elapsed: {elapsed_time}s)")
                
                if refresh_status.lower() in ['completed', 'success']:
                    result['status'] = 'completed'
                    result['completed_at'] = datetime.now().isoformat()
                    self.logger.info("[REFRESH] ✅ Dataflow refresh completed successfully")
                    break
                elif refresh_status.lower() in ['failed', 'error']:
                    result['status'] = 'failed'
                    result['error'] = f"Refresh failed with status: {refresh_status}"
                    self.logger.error(f"[REFRESH] ❌ Dataflow refresh failed: {refresh_status}")
                    break
        else:
            result['status'] = 'timeout'
            result['error'] = f"Refresh did not complete within {max_wait_time} seconds"
            self.logger.warning(f"[REFRESH] ⚠️ Timeout waiting for completion")
        
        return result
    
    def get_dataflow_refresh_status(self, workspace_id: str, dataflow_id: str, 
                                  profile_name: str = "powerbi_primary") -> List[Dict[str, Any]]:
        """
        Get dataflow refresh history/status
        
        Args:
            workspace_id: Power BI workspace ID
            dataflow_id: Dataflow ID
            
        Returns:
            List of refresh history entries
        """
        url = f"{self.base_url}/groups/{workspace_id}/dataflows/{dataflow_id}/refreshes"
        response = self._make_request("GET", url, profile_name)
        
        if response.status_code == 200:
            refreshes = response.json().get('value', [])
            self.logger.info(f"[STATUS] Retrieved {len(refreshes)} refresh entries")
            return refreshes
        else:
            self.logger.error(f"[STATUS] Failed to get refresh status: {response.status_code}")
            return []
    
    def trigger_power_automate_workflow(self, workflow_name: str = "order_list_refresh", 
                                      payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trigger Power Automate workflow (fallback method)
        
        Args:
            workflow_name: Name of workflow in config
            payload: Optional payload for the workflow
            
        Returns:
            Workflow trigger result
        """
        self.logger.info(f"[PA] Triggering Power Automate workflow: {workflow_name}")
        
        # Get workflow config
        workflow_config = self.config['power_automate']['workflows'].get(workflow_name)
        if not workflow_config:
            raise ValueError(f"Workflow '{workflow_name}' not found in configuration")
        
        # Build full URL
        url = f"{workflow_config['logic_app_url']}?api-version={workflow_config['api_version']}&{workflow_config['access_key_params']}"
        
        # Default payload
        if payload is None:
            payload = {
                "trigger_source": "data_orchestration",
                "timestamp": datetime.now().isoformat(),
                "workflow_name": workflow_name
            }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DataOrchestration-UniversalPowerBI/1.0"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            result = {
                'workflow_name': workflow_name,
                'started_at': datetime.now().isoformat(),
                'status': 'success' if response.status_code == 200 else 'failed',
                'status_code': response.status_code,
                'response': response.text[:500]  # Truncate response
            }
            
            if response.status_code == 200:
                self.logger.info(f"[PA] ✅ Workflow triggered successfully")
            else:
                self.logger.error(f"[PA] ❌ Workflow trigger failed: {response.status_code}")
                result['error'] = f"HTTP {response.status_code}: {response.text}"
            
            # Log result
            self._log_operation('power_automate_trigger', result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"[PA] Workflow trigger exception: {e}")
            result = {
                'workflow_name': workflow_name,
                'started_at': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            }
            self._log_operation('power_automate_trigger', result)
            return result
    
    def _log_operation(self, operation_type: str, operation_data: Dict[str, Any]):
        """Log operation to database for audit purposes"""
        try:
            with db.get_connection('orders') as conn:
                sql = """
                INSERT INTO log.PowerBIOperations (
                    operation_type,
                    operation_data,
                    created_at
                ) VALUES (?, ?, GETDATE())
                """
                
                db.execute_query(conn, sql, [
                    operation_type,
                    json.dumps(operation_data, default=str)
                ])
                
                self.logger.info(f"[LOG] Operation logged: {operation_type}")
                
        except Exception as e:
            self.logger.warning(f"[LOG] Failed to log operation: {e}")

# Factory function for easy usage
def create_powerbi_manager() -> PowerBIManager:
    """Factory function to create Power BI manager instance"""
    return PowerBIManager()
