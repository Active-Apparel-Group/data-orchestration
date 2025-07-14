# graphql/loader.py
"""
GraphQL Template Loader
Loads and validates GraphQL templates for Monday.com operations
"""

from pathlib import Path
from typing import Dict, Any
import json

class GraphQLLoader:
    """Load and manage GraphQL templates"""
    
    def __init__(self, graphql_dir: Path):
        self.graphql_dir = graphql_dir
        self.mutations = {}
        self.queries = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all GraphQL templates from directory"""
        # Load mutations
        mutations_dir = self.graphql_dir / "mutations"
        if mutations_dir.exists():
            for template_file in mutations_dir.glob("*.graphql"):
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.mutations[template_name] = f.read()
        
        # Load queries  
        queries_dir = self.graphql_dir / "queries"
        if queries_dir.exists():
            for template_file in queries_dir.glob("*.graphql"):
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.queries[template_name] = f.read()
    
    def get_mutation(self, name: str) -> str:
        """Get mutation template by name"""
        if name not in self.mutations:
            raise ValueError(f"Mutation template '{name}' not found")
        return self.mutations[name]
    
    def get_query(self, name: str) -> str:
        """Get query template by name"""
        if name not in self.queries:
            raise ValueError(f"Query template '{name}' not found")
        return self.queries[name]
    
    def list_templates(self) -> Dict[str, list]:
        """List all available templates"""
        return {
            'mutations': list(self.mutations.keys()),
            'queries': list(self.queries.keys())
        }