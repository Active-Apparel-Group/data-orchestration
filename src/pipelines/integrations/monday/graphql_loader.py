# graphql_loader.py
"""
GraphQL Template Loader
Loads and validates GraphQL templates for Monday.com operations from sql/graphql/ directory
"""

import sys
from pathlib import Path
from typing import Dict, Any
import json

# Standard import pattern for proper logging
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import Kestra-compatible logger
import logger_helper

class GraphQLLoader:
    """Load and manage GraphQL templates from sql/graphql/ directory"""
    
    def __init__(self, repo_root: Path = None):
        """
        Initialize GraphQL loader
        
        Args:
            repo_root: Repository root path. If None, will auto-detect from current file location.
        """
        self.logger = logger_helper.get_logger(__name__)
        
        if repo_root is None:
            repo_root = self._find_repo_root()
        
        self.graphql_dir = repo_root / "sql" / "graphql"
        self.mutations = {}
        self.queries = {}
        
        self.logger.info(f"Initializing GraphQL loader with directory: {self.graphql_dir}")
        self._load_templates()
    
    def _find_repo_root(self) -> Path:
        """Find repository root by looking for pipelines folder (current active structure)"""
        current = Path(__file__).parent
        while current != current.parent:
            # Look for pipelines folder - indicates we're at repo root
            if (current / "pipelines").exists() and (current / "sql").exists():
                self.logger.debug(f"Found repository root: {current}")
                return current
            current = current.parent
        
        error_msg = "Could not find repository root (needs pipelines and sql folders)"
        self.logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    def _load_templates(self):
        """Load all GraphQL templates from sql/graphql/ directory"""
        if not self.graphql_dir.exists():
            error_msg = f"GraphQL directory not found: {self.graphql_dir}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Load mutations
        mutations_dir = self.graphql_dir / "mutations"
        if mutations_dir.exists():
            mutation_count = 0
            for template_file in mutations_dir.glob("*.graphql"):
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.mutations[template_name] = f.read()
                    mutation_count += 1
                    self.logger.debug(f"Loaded mutation template: {template_name}")
            self.logger.info(f"Loaded {mutation_count} mutation templates")
        
        # Load queries  
        queries_dir = self.graphql_dir / "queries"
        if queries_dir.exists():
            query_count = 0
            for template_file in queries_dir.glob("*.graphql"):
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.queries[template_name] = f.read()
                    query_count += 1
                    self.logger.debug(f"Loaded query template: {template_name}")
            self.logger.info(f"Loaded {query_count} query templates")
    
    def get_mutation(self, name: str) -> str:
        """Get mutation template by name"""
        if name not in self.mutations:
            available = list(self.mutations.keys())
            error_msg = f"Mutation template '{name}' not found. Available: {available}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.debug(f"Retrieved mutation template: {name}")
        return self.mutations[name]
    
    def get_query(self, name: str) -> str:
        """Get query template by name"""
        if name not in self.queries:
            available = list(self.queries.keys())
            error_msg = f"Query template '{name}' not found. Available: {available}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.debug(f"Retrieved query template: {name}")
        return self.queries[name]
    
    def list_templates(self) -> Dict[str, list]:
        """List all available templates"""
        templates = {
            'mutations': list(self.mutations.keys()),
            'queries': list(self.queries.keys())
        }
        self.logger.debug(f"Listed templates: {len(templates['mutations'])} mutations, {len(templates['queries'])} queries")
        return templates
    
    def reload_templates(self):
        """Reload all templates from disk"""
        self.logger.info("Reloading GraphQL templates")
        self.mutations.clear()
        self.queries.clear()
        self._load_templates()
