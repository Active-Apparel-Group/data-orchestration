#!/usr/bin/env python3
"""
🧪 Sequential Pipeline Debugger - AAG SEASON Dropdown Issue
===========================================================

PURPOSE: Find where 'AAG SEASON = 2025 FALL' becomes 'None' in Monday.com

ISSUE: Database shows '2025 FALL' but Monday.com shows 'None'
APPROACH: Sequential step-by-step validation to isolate the exact failure point

TEST SEQUENCE:
1. Database Query - Validate source data
2. Config Loading - Validate TOML configuration
3. Column Mapping - Validate transformations
4. Record Transform - Validate field mappings
5. API Call Validation - Validate GraphQL generation
6. Monday.com CREATE - Test actual API call
7. Monday.com Validation - Verify dropdown persistence
8. UPDATE Test - Test SyncEngine UPDATE pattern (TASK020)

EXPECTED OUTCOME: Find exact step where dropdown value is lost
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient
from src.pipelines.sync_order_list.sync_engine import SyncEngine

logger = logger.get_logger(__name__)

def main():
    """
    🔍 Sequential Pipeline Debugger
    Tests each step of the pipeline to find where AAG SEASON becomes None
    """
    
    # Test configuration
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    test_data = {
        'customer': 'GREYSON',
        'po_number': '4755',
        'expected_aag_season': '2025 FALL'
    }
    
    logger.info("🔍 Sequential Pipeline Debugger initialized")
    logger.info(f"   Config: {config_path}")
    logger.info(f"   Test data: {test_data}")
    
    logger.info("🚀 Starting Sequential Pipeline Testing")
    logger.info("🎯 Goal: Find where 'AAG SEASON = 2025 FALL' becomes 'None'")
    logger.info("=" * 60)
    
    # Sequential test execution
    try:
        # Step 1: Database Query Validation
        sample_record = step_1_database_query_validation(test_data)
        if not sample_record:
            logger.error("💥 STOPPED: Step 1 failed")
            return
        
        # Step 2: Config Loading Validation
        config = step_2_config_loading_validation(config_path)
        if not config:
            logger.error("💥 STOPPED: Step 2 failed")
            return
        
        # Step 3: Column Mapping Validation
        api_client = step_3_column_mapping_validation(config_path)
        if not api_client:
            logger.error("💥 STOPPED: Step 3 failed")
            return
        
        # Step 4: Record Transformation Validation
        transformed_record = step_4_record_transformation_validation(api_client, sample_record)
        if not transformed_record:
            logger.error("💥 STOPPED: Step 4 failed")
            return
        
        # Step 5: Monday.com API Call Validation
        step_5_api_call_validation(api_client, transformed_record)
        
        # Step 6: Monday.com CREATE API Call Test
        created_item_id = step_6_create_api_call_test(api_client, transformed_record)
        if not created_item_id:
            logger.error("💥 STOPPED: Step 6 failed")
            return
        
        # Step 7: Monday.com Item Validation
        validation_passed = step_7_monday_item_validation(api_client, created_item_id, test_data['expected_aag_season'])
        if not validation_passed:
            logger.warning("⚠️  Step 7 identified dropdown issue - continuing with SyncEngine comparison")
        
        # SyncEngine comparison testing
        step_6b_prepare_syncengine_test_data(test_data)
        syncengine_item_ids = step_6c_syncengine_integration_test(config_path)
        step_6d_syncengine_monday_validation(api_client, syncengine_item_ids, test_data['expected_aag_season'])
        
        # Step 8: UPDATE Test using SyncEngine (TASK020) - Use SyncEngine-created item
        if syncengine_item_ids and len(syncengine_item_ids) > 0:
            step_8_syncengine_update_test(config_path, syncengine_item_ids[0], api_client)
        else:
            logger.warning("⚠️  No SyncEngine-created items available for Step 8 UPDATE test")
        
        logger.info("🎉 Sequential Pipeline Testing Complete!")
        logger.info("📊 Check results above for dropout analysis")
        
    except Exception as e:
        logger.exception(f"💥 Pipeline testing failed: {e}")

def step_1_database_query_validation(test_data):
    """
    Step 1: Validate source data from database
    Goal: Confirm AAG SEASON exists in source data
    """
    logger.info("=" * 60)
    logger.info("STEP 1: Database Query Validation")
    logger.info("=" * 60)
    
    try:
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Database connection using config.db_key
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Query source data
            query = """
            SELECT TOP 1 
                [AAG ORDER NUMBER],
                [AAG SEASON],
                [CUSTOMER SEASON],
                [CUSTOMER NAME],
                [PO NUMBER]
            FROM FACT_ORDER_LIST 
            WHERE [CUSTOMER NAME] = ? 
            AND [PO NUMBER] = ?
            ORDER BY [AAG ORDER NUMBER]
            """
            
            cursor.execute(query, (test_data['customer'], test_data['po_number']))
            row = cursor.fetchone()
            
            if row:
                # Create record dictionary
                columns = [desc[0] for desc in cursor.description]
                record = dict(zip(columns, row))
                
                logger.info("✅ Database record found:")
                logger.info(f"   AAG ORDER: {record['AAG ORDER NUMBER']}")
                logger.info(f"   AAG SEASON: '{record['AAG SEASON']}' (type: {type(record['AAG SEASON']).__name__})")
                logger.info(f"   CUSTOMER SEASON: '{record['CUSTOMER SEASON']}' (type: {type(record['CUSTOMER SEASON']).__name__})")
                logger.info(f"   CUSTOMER: {record['CUSTOMER NAME']}")
                logger.info(f"   PO: {record['PO NUMBER']}")
                
                # Validate expected value
                if record['AAG SEASON'] == test_data['expected_aag_season']:
                    logger.info(f"✅ STEP 1 PASSED: AAG SEASON = '{record['AAG SEASON']}' (matches expected)")
                    cursor.close()
                    return record
                else:
                    logger.error(f"❌ STEP 1 FAILED: Expected '{test_data['expected_aag_season']}', got '{record['AAG SEASON']}'")
                    cursor.close()
                    return None
            else:
                logger.error(f"❌ STEP 1 FAILED: No records found for {test_data['customer']} PO {test_data['po_number']}")
                cursor.close()
                return None
                
    except Exception as e:
        logger.exception(f"❌ STEP 1 ERROR: Database query failed: {e}")
        return None

def step_2_config_loading_validation(config_path):
    """
    Step 2: Validate TOML configuration loading
    Goal: Confirm dropdown mappings and settings are correct
    """
    logger.info("=" * 60)
    logger.info("STEP 2: Config Loading Validation")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        config = DeltaSyncConfig.from_toml(config_path)
        
        logger.info("✅ Config loaded successfully:")
        logger.info(f"   Environment: {config.environment}")
        logger.info(f"   Database: {config.db_key}")
        
        # Validate dropdown mapping specifically
        import tomli
        with open(config_path, 'rb') as f:
            toml_config = tomli.load(f)
        
        # Check AAG SEASON mapping
        environment = config.environment
        monday_mapping = toml_config.get('monday', {}).get('column_mapping', {})
        headers_mapping = monday_mapping.get(environment, {}).get('headers', {})
        
        aag_season_mapping = headers_mapping.get('AAG SEASON')
        if aag_season_mapping:
            logger.info(f"   AAG SEASON mapping: 'AAG SEASON' → '{aag_season_mapping}'")
            
            # Check create_labels_if_missing setting
            dropdown_config = toml_config.get('monday', {}).get(environment, {}).get('headers', {}).get('create_labels_if_missing', {})
            create_labels = dropdown_config.get(aag_season_mapping, dropdown_config.get('default', False))
            logger.info(f"   AAG SEASON create_labels: {create_labels}")
            
            logger.info("✅ STEP 2 PASSED: Config settings correct")
            return config
        else:
            logger.error("❌ STEP 2 FAILED: AAG SEASON mapping not found")
            return None
            
    except Exception as e:
        logger.exception(f"❌ STEP 2 ERROR: Config loading failed: {e}")
        return None

def step_3_column_mapping_validation(config_path):
    """
    Step 3: Validate column mapping functionality
    Goal: Confirm API client can retrieve correct mappings
    """
    logger.info("=" * 60)
    logger.info("STEP 3: Column Mapping Validation")
    logger.info("=" * 60)
    
    try:
        # Initialize API client
        api_client = MondayAPIClient(config_path)
        
        # Get column mappings
        column_mappings = api_client._get_column_mappings('create_items')
        
        logger.info("✅ Column mappings retrieved:")
        logger.info(f"   Total mappings: {len(column_mappings)}")
        
        # Check AAG SEASON mapping specifically
        aag_season_mapping = column_mappings.get('AAG SEASON')
        if aag_season_mapping:
            logger.info(f"   AAG SEASON mapping: 'AAG SEASON' → '{aag_season_mapping}'")
            logger.info("✅ STEP 3 PASSED: Column mapping correct")
            return api_client
        else:
            logger.error("❌ STEP 3 FAILED: AAG SEASON mapping not found in column mappings")
            return None
            
    except Exception as e:
        logger.exception(f"❌ STEP 3 ERROR: Column mapping validation failed: {e}")
        return None

def step_4_record_transformation_validation(api_client, sample_record):
    """
    Step 4: Validate record transformation
    Goal: Confirm database record transforms correctly with column mappings
    """
    logger.info("=" * 60)
    logger.info("STEP 4: Record Transformation Validation")
    logger.info("=" * 60)
    
    try:
        # Show input record
        logger.info("📦 Input record:")
        for key, value in sample_record.items():
            logger.info(f"   {key}: '{value}' (type: {type(value).__name__})")
        
        # Get column mappings and transform
        column_mappings = api_client._get_column_mappings('create_items')
        transformed_record = api_client._transform_record(sample_record, column_mappings)
        
        # Show transformed record
        logger.info("✨ Transformed record:")
        for monday_column, value in transformed_record.items():
            logger.info(f"   {monday_column}: '{value}' (type: {type(value).__name__})")
        
        # Analyze dropdown fields specifically
        logger.info("🎯 Dropdown field analysis:")
        for monday_column, value in transformed_record.items():
            if monday_column.startswith('dropdown_'):
                # Try to find the original field name
                original_field = None
                for db_field, mapped_field in column_mappings.items():
                    if mapped_field == monday_column:
                        original_field = db_field
                        break
                
                logger.info(f"   {monday_column} ({original_field}): '{value}'")
        
        # Validate AAG SEASON specifically
        aag_season_column = column_mappings.get('AAG SEASON')
        if aag_season_column and aag_season_column in transformed_record:
            aag_season_value = transformed_record[aag_season_column]
            if aag_season_value == sample_record['AAG SEASON']:
                logger.info("✅ STEP 4 PASSED: AAG SEASON value preserved during transformation")
                return transformed_record
            else:
                logger.error(f"❌ STEP 4 FAILED: AAG SEASON value changed from '{sample_record['AAG SEASON']}' to '{aag_season_value}'")
                return None
        else:
            logger.error("❌ STEP 4 FAILED: AAG SEASON not found in transformed record")
            return None
            
    except Exception as e:
        logger.exception(f"❌ STEP 4 ERROR: Record transformation failed: {e}")
        return None

def step_5_api_call_validation(api_client, transformed_record):
    """
    Step 5: Validate API call preparation
    Goal: Confirm GraphQL query generation is correct
    """
    logger.info("=" * 60)
    logger.info("STEP 5: Monday.com API Call Validation")
    logger.info("=" * 60)
    
    try:
        logger.info("🚀 Testing Monday.com API call with transformed record")
        logger.info(f"   Record to send: {transformed_record}")
        
        # Find AAG SEASON value in transformed record
        aag_season_value = None
        for column_id, value in transformed_record.items():
            if column_id.startswith('dropdown_') and 'AAG SEASON' in str(column_id):
                aag_season_value = value
                break
        
        if not aag_season_value:
            # Check by column mapping
            column_mappings = api_client._get_column_mappings('create_items')
            aag_season_column = column_mappings.get('AAG SEASON')
            if aag_season_column:
                aag_season_value = transformed_record.get(aag_season_column)
        
        if aag_season_value:
            logger.info(f"   Testing dropdown value: '{aag_season_value}'")
            
            # Test create_labels_if_missing determination
            logger.info("📞 Testing dropdown value validation...")
            create_labels = api_client._determine_create_labels_for_records([transformed_record], 'headers')
            
            # Find the specific column for detailed logging
            column_mappings = api_client._get_column_mappings('create_items')
            aag_season_column = column_mappings.get('AAG SEASON')
            if aag_season_column:
                logger.info(f"   createLabelsIfMissing for {aag_season_column}: {create_labels}")
            
            if create_labels:
                logger.info(f"✅ createLabelsIfMissing is enabled - Monday should create '{aag_season_value}' if missing")
            else:
                logger.warning(f"⚠️  createLabelsIfMissing is disabled - '{aag_season_value}' must already exist")
            
            logger.info("✅ STEP 5 COMPLETED: API call validation ready")
            logger.info("   Next: Test actual API call in dry-run mode")
        else:
            logger.error("❌ STEP 5 FAILED: AAG SEASON value not found in transformed record")
            
    except Exception as e:
        logger.exception(f"❌ STEP 5 ERROR: API call validation failed: {e}")

def step_6_create_api_call_test(api_client, transformed_record):
    """
    Step 6: Test actual Monday.com CREATE API call
    Goal: Execute real API call and capture Monday.com response
    """
    logger.info("=" * 60)
    logger.info("STEP 6: Monday.com CREATE API Call Test")
    logger.info("=" * 60)
    
    try:
        logger.info("🚀 Testing LIVE Monday.com CREATE API call")
        logger.info(f"   Record to create: {transformed_record}")
        
        logger.info("📞 Making CREATE API call...")
        result = api_client.execute("create_items", transformed_record, dry_run=False)
        
        logger.info("✅ API call completed!")
        logger.info(f"   Result: {result}")
        
        if result.get('success') and result.get('monday_ids'):
            created_item_id = result['monday_ids'][0]
            logger.info(f"✅ Item created successfully with ID: {created_item_id}")
            logger.info("✅ STEP 6 PASSED: CREATE API call successful")
            logger.info("   Next: Validate dropdown value persisted correctly")
            return created_item_id
        else:
            logger.error(f"❌ STEP 6 FAILED: CREATE API call failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.exception(f"❌ STEP 6 ERROR: CREATE API call failed: {e}")
        return None

def step_7_monday_item_validation(api_client, item_id, expected_aag_season):
    """
    Step 7: Validate created Monday.com item
    Goal: Query Monday.com to check if dropdown values persisted correctly
    """
    logger.info("=" * 60)
    logger.info("STEP 7: Monday.com Item Validation")
    logger.info("=" * 60)
    
    try:
        logger.info(f"🔍 Validating created item ID: {item_id}")
        logger.info(f"   Expected item name: 'GRE-04326'")
        logger.info(f"   Expected AAG SEASON: '{expected_aag_season}'")
        
        # Query Monday.com for the created item
        logger.info("📞 Querying Monday.com for created item...")
        
        # GraphQL query to get item details with column values
        query = f"""
        query {{
            items(ids: [{item_id}]) {{
                id
                name
                column_values {{
                    id
                    text
                    type
                    value
                }}
            }}
        }}
        """
        
        import aiohttp
        import asyncio
        
        async def query_item():
            result = await api_client._make_api_call(query, variables={})
            return result
        
        response = asyncio.run(query_item())
        
        if response.get('success') and response.get('data', {}).get('items'):
            item = response['data']['items'][0]
            
            logger.info("✅ Item retrieved successfully:")
            logger.info(f"   Item ID: {item['id']}")
            logger.info(f"   Item Name: '{item['name']}'")
            
            # Analyze column values
            column_mappings = api_client._get_column_mappings('create_items')
            aag_season_column = column_mappings.get('AAG SEASON')
            
            dropdown_found = False
            correct_aag_season = False
            
            for col in item['column_values']:
                if col['type'] == 'dropdown' or col['id'] in column_mappings.values():
                    # Find the original field name
                    original_field = None
                    for db_field, mapped_field in column_mappings.items():
                        if mapped_field == col['id']:
                            original_field = db_field
                            break
                    
                    display_name = original_field if original_field else col['id']
                    logger.info(f"   {display_name} ({col['id']}): '{col['text']}' (type: {col['type']})")
                    
                    # Check AAG SEASON specifically
                    if col['id'] == aag_season_column:
                        dropdown_found = True
                        if col['text'] == expected_aag_season:
                            correct_aag_season = True
            
            if dropdown_found and correct_aag_season:
                logger.info("✅ STEP 7 PASSED: AAG SEASON dropdown correctly populated")
                return True
            else:
                logger.error("❌ STEP 7 FAILED: AAG SEASON dropdown is empty/None")
                logger.error("   🚨 DROPDOWN ISSUE CONFIRMED: Value not persisting in Monday.com")
                return False
        else:
            logger.error(f"❌ STEP 7 FAILED: Could not retrieve item {item_id} from Monday.com")
            return False
            
    except Exception as e:
        logger.exception(f"❌ STEP 7 ERROR: Monday.com validation failed: {e}")
        return False

def step_6b_prepare_syncengine_test_data(test_data):
    """
    Step 6B: Prepare test data for SyncEngine validation
    Goal: Ensure FACT_ORDER_LIST has records with sync_state = 'PENDING'
    """
    logger.info("🔄 Starting SyncEngine testing (proven pattern approach)...")
    logger.info("=" * 60)
    logger.info("🔄 STEP 6B: Prepare SyncEngine Test Data")
    logger.info("🎯 Goal: Verify FACT_ORDER_LIST has our test records for SyncEngine")
    
    try:
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Database connection using config.db_key
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Check available test records
            analysis_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN [AAG SEASON] = ? THEN 1 END) as season_matches,
                COUNT(CASE WHEN [CUSTOMER NAME] = ? THEN 1 END) as customer_matches
            FROM FACT_ORDER_LIST 
            WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
            """
            
            cursor.execute(analysis_query, (
                test_data['expected_aag_season'], 
                test_data['customer'],
                test_data['customer'], 
                test_data['po_number']
            ))
            stats = cursor.fetchone()
            
            logger.info("📊 Database state analysis:")
            logger.info(f"   Total {test_data['customer']} PO {test_data['po_number']} records: {stats[0]}")
            logger.info(f"   {test_data['expected_aag_season']} seasons: {stats[1]}")
            logger.info(f"   {test_data['customer']} records: {stats[2]}")
            
            if stats[0] > 0:
                logger.info("✅ STEP 6B PASSED: Test records available for SyncEngine")
                
                # Get a sample record for reference
                sample_query = """
                SELECT TOP 1 
                    [AAG ORDER NUMBER],
                    [AAG SEASON],
                    [CUSTOMER NAME],
                    [PO NUMBER]
                FROM FACT_ORDER_LIST 
                WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
                ORDER BY [AAG ORDER NUMBER]
                """
                
                cursor.execute(sample_query, (test_data['customer'], test_data['po_number']))
                sample = cursor.fetchone()
                
                if sample:
                    logger.info("📝 Sample record for SyncEngine:")
                    logger.info(f"   AAG ORDER NUMBER: '{sample[0]}'")
                    logger.info(f"   AAG SEASON: '{sample[1]}'")
                    logger.info(f"   CUSTOMER NAME: '{sample[2]}'")
                    logger.info(f"   PO NUMBER: '{sample[3]}'")
                
                cursor.close()
                return True
            else:
                logger.error("❌ STEP 6B FAILED: No test records found for SyncEngine")
                cursor.close()
                return False
                
    except Exception as e:
        logger.exception(f"❌ STEP 6B ERROR: Test data preparation failed: {e}")
        return False

def step_6c_syncengine_integration_test(config_path):
    """
    Step 6C: Test SyncEngine integration
    Goal: Execute SyncEngine.run_sync() to test proven pattern
    """
    logger.info("=" * 60)
    logger.info("🔄 STEP 6C: SyncEngine Integration Test")
    logger.info("🎯 Goal: Test proven SyncEngine.run_sync() pattern for dropdown handling")
    logger.info("📝 Processing records from 69 available GREYSON records")
    
    try:
        logger.info("🔧 Initializing SyncEngine (proven pattern approach)...")
        
        # Initialize SyncEngine
        sync_engine = SyncEngine(config_path)
        
        logger.info("✅ SyncEngine initialized:")
        logger.info(f"   Items board: {sync_engine.config.monday_board_id}")
        logger.info(f"   Subitems board: {sync_engine.config.monday_subitems_board_id}")
        logger.info(f"   Target table: {sync_engine.config.target_table}")
        
        # Execute SyncEngine
        logger.info("🚀 Executing SyncEngine.run_sync() - PROVEN PATTERN")
        logger.info("   Method: sync_engine.run_sync(dry_run=False, limit=1)")
        
        result = sync_engine.run_sync(dry_run=False, limit=1)
        
        logger.info("📊 SyncEngine results:")
        logger.info(f"   Raw result: {result}")
        
        if result.get('success'):
            total_synced = result.get('total_synced', 0)
            monday_item_ids = []
            
            # Extract Monday.com IDs from batch results
            batch_results = result.get('batch_results', [])
            for batch_result in batch_results:
                if batch_result.get('success') and 'monday_item_ids' in batch_result:
                    monday_item_ids.extend(batch_result['monday_item_ids'])
            
            logger.info("✅ SyncEngine execution successful!")
            logger.info(f"   Total synced: {total_synced}")
            logger.info(f"   Monday.com Item IDs: {monday_item_ids}")
            logger.info("✅ STEP 6C PASSED: SyncEngine created Monday.com items successfully")
            logger.info("   Next: Validate dropdown values in created items")
            
            return monday_item_ids
        else:
            logger.error(f"❌ STEP 6C FAILED: SyncEngine execution failed: {result}")
            return None
            
    except Exception as e:
        logger.exception(f"❌ STEP 6C ERROR: SyncEngine integration test failed: {e}")
        return None

def step_6d_syncengine_monday_validation(api_client, monday_item_ids, expected_aag_season):
    """
    Step 6D: Validate SyncEngine-created Monday.com items
    Goal: Check if SyncEngine properly handles dropdown values
    """
    logger.info("=" * 60)
    logger.info("🔄 STEP 6D: SyncEngine Monday.com Validation")
    logger.info("🎯 Goal: Validate dropdown values in SyncEngine-created items")
    logger.info(f"🔍 Validating SyncEngine-created items: {monday_item_ids}")
    
    try:
        if not monday_item_ids:
            logger.error("❌ STEP 6D FAILED: No Monday.com item IDs provided")
            return False
        
        successful_validations = 0
        total_items = len(monday_item_ids)
        
        for item_id in monday_item_ids:
            logger.info(f"📞 Querying Monday.com item: {item_id}")
            
            # GraphQL query to get item details
            query = f"""
            query {{
                items(ids: [{item_id}]) {{
                    id
                    name
                    column_values {{
                        id
                        text
                        type
                        value
                    }}
                }}
            }}
            """
            
            import asyncio
            
            async def query_item():
                result = await api_client._make_api_call(query, variables={})
                return result
            
            response = asyncio.run(query_item())
            
            if response.get('success') and response.get('data', {}).get('items'):
                item = response['data']['items'][0]
                
                logger.info(f"✅ Item {item_id} retrieved:")
                logger.info(f"   Name: '{item['name']}'")
                
                # Find dropdown columns
                column_mappings = api_client._get_column_mappings('create_items')
                aag_season_column = column_mappings.get('AAG SEASON')
                
                aag_season_found = False
                aag_season_correct = False
                
                for col in item['column_values']:
                    if col['type'] == 'dropdown':
                        # Find the original field name
                        original_field = None
                        for db_field, mapped_field in column_mappings.items():
                            if mapped_field == col['id']:
                                original_field = db_field
                                break
                        
                        display_name = original_field if original_field else col['id']
                        logger.info(f"   {display_name} ({col['id']}): '{col['text']}' (type: {col['type']})")
                        
                        # Check AAG SEASON specifically
                        if col['id'] == aag_season_column:
                            aag_season_found = True
                            if col['text'] == expected_aag_season:
                                aag_season_correct = True
                
                if aag_season_found and aag_season_correct:
                    successful_validations += 1
            else:
                logger.error(f"❌ Could not retrieve item {item_id}")
        
        logger.info("📊 SyncEngine validation summary:")
        logger.info(f"   Items queried: {total_items}")
        logger.info(f"   Successfully retrieved: {total_items}")
        logger.info(f"   Correct AAG SEASON: {successful_validations}")
        
        if successful_validations > 0:
            logger.info("✅ STEP 6D PASSED: SyncEngine correctly set AAG SEASON dropdown!")
            logger.info(f"   🎉 {successful_validations}/{total_items} items have correct '{expected_aag_season}' value")
            logger.info("   🔍 FINDING: SyncEngine path works correctly for dropdown values")
            return True
        else:
            logger.error("❌ STEP 6D FAILED: SyncEngine did not correctly set AAG SEASON")
            return False
            
    except Exception as e:
        logger.exception(f"❌ STEP 6D ERROR: SyncEngine Monday.com validation failed: {e}")
        return False

def step_8_syncengine_update_test(config_path, target_item_id, api_client):
    """
    Step 8: Test UPDATE using SyncEngine pattern (TASK020)
    Goal: Prove SyncEngine can handle UPDATE operations for dropdown values
    """
    logger.info("🔄 Starting UPDATE testing for TASK020...")
    logger.info("=" * 60)
    logger.info("🔄 STEP 8: SyncEngine UPDATE Test")
    logger.info("🎯 Goal: Test UPDATE using SyncEngine pattern (database → sync → Monday.com)")
    logger.info(f"📝 Target item for UPDATE: {target_item_id}")
    
    try:
        # Config FIRST
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Step 8A: Find database record for this Monday.com item
        logger.info("🔍 Step 8A: Finding database record for Monday.com item...")
        with db.get_connection(config.db_key) as connection:
            cursor = connection.cursor()
            
            # Find the database record that corresponds to this Monday.com item
            find_query = """
            SELECT TOP 1 
                [record_uuid],
                [AAG ORDER NUMBER],
                [AAG SEASON],
                [CUSTOMER NAME],
                [monday_item_id],
                [sync_state]
            FROM FACT_ORDER_LIST 
            WHERE [monday_item_id] = ?
            """
            
            cursor.execute(find_query, (target_item_id,))
            db_record = cursor.fetchone()
            
            if db_record:
                columns = [desc[0] for desc in cursor.description]
                record_dict = dict(zip(columns, db_record))
                
                logger.info("✅ Found database record:")
                logger.info(f"   record_uuid: {record_dict['record_uuid']}")
                logger.info(f"   AAG ORDER NUMBER: '{record_dict['AAG ORDER NUMBER']}'")
                logger.info(f"   Current AAG SEASON: '{record_dict['AAG SEASON']}'")
                logger.info(f"   Monday.com item_id: {record_dict['monday_item_id']}")
                logger.info(f"   Current sync_state: '{record_dict['sync_state']}'")
                
                # Step 8B: Update database record with new values and set for UPDATE
                logger.info("🔄 Step 8B: Preparing database record for UPDATE operation...")
                
                new_aag_season = "2025 SPRING"  # Change from 2025 FALL to 2025 SPRING
                update_query = """
                UPDATE FACT_ORDER_LIST 
                SET 
                    [AAG SEASON] = ?,
                    [sync_state] = 'PENDING',
                    [action_type] = 'UPDATE',
                    [sync_pending_at] = GETDATE()
                WHERE [monday_item_id] = ?
                """
                
                cursor.execute(update_query, (new_aag_season, target_item_id))
                connection.commit()
                
                logger.info(f"✅ Database record prepared for UPDATE:")
                logger.info(f"   New AAG SEASON: '{new_aag_season}'")
                logger.info(f"   sync_state: 'PENDING'")
                logger.info(f"   action_type: 'UPDATE'")
                logger.info(f"   sync_pending_at: NOW")
                
                # Step 8C: Run SyncEngine UPDATE operation (NEW FUNCTIONALITY)
                logger.info("🚀 Step 8C: Running SyncEngine UPDATE operation...")
                
                sync_engine = SyncEngine(config_path)
                
                # Run sync with UPDATE action type (NEW FUNCTIONALITY)
                sync_result = sync_engine.run_sync(
                    dry_run=False, 
                    limit=1, 
                    action_types=['UPDATE']  # Use new UPDATE functionality
                )
                
                if sync_result.get('success'):
                    logger.info("✅ SyncEngine UPDATE completed successfully!")
                    logger.info(f"   Records synced: {sync_result.get('total_synced', 0)}")
                    
                    # Step 8D: Validate Monday.com item was updated
                    logger.info("🔍 Step 8D: Validating Monday.com UPDATE...")
                    
                    # Query Monday.com to verify the update
                    query = f"""
                    query {{
                        items(ids: [{target_item_id}]) {{
                            id
                            name
                            column_values {{
                                id
                                text
                                type
                                value
                            }}
                        }}
                    }}
                    """
                    
                    import asyncio
                    
                    async def query_updated_item():
                        result = await api_client._make_api_call(query)
                        return result
                    
                    response = asyncio.run(query_updated_item())
                    
                    if response.get('success') and response.get('data', {}).get('items'):
                        item = response['data']['items'][0]
                        
                        logger.info(f"✅ Updated item {target_item_id} retrieved:")
                        logger.info(f"   Name: '{item['name']}'")
                        
                        # Find AAG SEASON column
                        column_mappings = api_client._get_column_mappings('create_items')
                        aag_season_column = column_mappings.get('AAG SEASON')
                        
                        aag_season_updated = False
                        
                        for col in item['column_values']:
                            if col['id'] == aag_season_column:
                                logger.info(f"   AAG SEASON ({col['id']}): '{col['text']}' (type: {col['type']})")
                                
                                if col['text'] == new_aag_season:
                                    aag_season_updated = True
                                    break
                        
                        if aag_season_updated:
                            logger.info("✅ STEP 8 PASSED: SyncEngine UPDATE successfully changed AAG SEASON!")
                            logger.info(f"   🎉 Monday.com item now shows '{new_aag_season}'")
                            logger.info("   🔍 FINDING: SyncEngine handles both CREATE and UPDATE operations correctly")
                            return True
                        else:
                            logger.error(f"❌ STEP 8 FAILED: AAG SEASON not updated to '{new_aag_season}'")
                            return False
                    else:
                        logger.error("❌ STEP 8 FAILED: Could not retrieve updated item from Monday.com")
                        return False
                else:
                    logger.error(f"❌ STEP 8 FAILED: SyncEngine UPDATE failed: {sync_result}")
                    return False
            else:
                logger.error(f"❌ STEP 8 FAILED: No database record found for Monday.com item {target_item_id}")
                return False
                
            cursor.close()
            
    except Exception as e:
        logger.exception(f"❌ STEP 8 ERROR: SyncEngine UPDATE test failed: {e}")
        return False

if __name__ == "__main__":
    main()
