"""
Unified Token Loader Script
Purpose: Load tokens for multiple Azure service accounts using YAML configuration
Location: pipelines/scripts/powerbi/load_tokens.py

Usage:
    python pipelines/scripts/powerbi/load_tokens.py                    # Load all profiles
    python pipelines/scripts/powerbi/load_tokens.py --profile powerbi_primary  # Load specific profile
    python pipelines/scripts/powerbi/load_tokens.py --refresh          # Force refresh all tokens
"""
import sys, os
import argparse
from pathlib import Path
from typing import Dict, Any

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

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

# Import project utilities
import logger_helper
from token_manager import UniversalTokenManager

def main():
    """Main function for unified token loading"""
    parser = argparse.ArgumentParser(description="Load tokens for Azure service accounts")
    parser.add_argument('--profile', help="Specific profile to load (default: all profiles)")
    parser.add_argument('--refresh', action='store_true', help="Force refresh tokens")
    parser.add_argument('--validate', action='store_true', help="Validate tokens after loading")
    parser.add_argument('--config', default="pipelines/utils/powerbi_config.yaml", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize logger
    logger = logger_helper.get_logger(__name__)
    logger.info("Universal Token Loader Starting")
    logger.info(f"Configuration: {args.config}")
    logger.info(f"Force refresh: {args.refresh}")
    
    try:
        # Initialize token manager
        token_manager = UniversalTokenManager(args.config)
        
        # Load tokens
        if args.profile:
            # Load specific profile
            logger.info(f"Loading tokens for profile: {args.profile}")
            token_data = token_manager.get_token(args.profile, args.refresh)
            tokens = {args.profile: token_data}
        else:
            # Load all profiles
            logger.info("Loading tokens for all profiles")
            tokens = token_manager.get_all_tokens(args.refresh)
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("TOKEN LOADING RESULTS")
        logger.info("="*60)
        
        success_count = 0
        error_count = 0
        
        for profile_name, token_info in tokens.items():
            if 'error' in token_info:
                logger.error(f"FAILED {profile_name}: {token_info['error']}")
                error_count += 1
            else:
                expires_at = token_info.get('expires_at', 'Unknown')
                source = token_info.get('source', 'unknown')
                logger.info(f"SUCCESS {profile_name}: Success ({source}) - Expires: {expires_at}")
                success_count += 1
                
                # Validate token if requested
                if args.validate:
                    is_valid = token_manager.validate_token(profile_name, token_info)
                    if is_valid:
                        logger.info(f"   Validation: Token is valid")
                    else:
                        logger.warning(f"   Validation: Token validation failed")
        
        # Summary
        logger.info("-" * 60)
        logger.info(f"SUMMARY: {success_count} successful, {error_count} failed")
        
        if error_count == 0:
            logger.info("All tokens loaded successfully!")
            return 0
        else:
            logger.warning(f"Some tokens failed to load ({error_count} errors)")
            return 1
            
    except Exception as e:
        logger.error(f"Token loading failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
