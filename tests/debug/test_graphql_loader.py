"""
Test GraphQL Loader Functionality
Validates that the new GraphQLLoader works correctly with sql/graphql/ directory
"""

try:
    # ✅ Modern import - works after pip install -e .
    from pipelines.integrations.monday import GraphQLLoader
    
    print("🧪 Testing GraphQL Loader...")
    
    # Test initialization
    loader = GraphQLLoader()
    print(f"   ✅ Loader initialized, GraphQL dir: {loader.graphql_dir}")
    
    # Test template listing
    templates = loader.list_templates()
    print(f"   📋 Available templates:")
    print(f"      Mutations: {templates['mutations']}")
    print(f"      Queries: {templates['queries']}")
    
    # Test loading a specific mutation
    if 'update_item' in templates['mutations']:
        update_template = loader.get_mutation('update_item')
        print(f"   ✅ Loaded update_item template: {len(update_template)} characters")
    else:
        print(f"   ⚠️  update_item template not found")
    
    # Test loading create-master-item if available
    if 'create-master-item' in templates['mutations']:
        create_template = loader.get_mutation('create-master-item')
        print(f"   ✅ Loaded create-master-item template: {len(create_template)} characters")
    else:
        print(f"   ⚠️  create-master-item template not found")
    
    print("   🎉 GraphQL Loader test completed successfully!")
    
except Exception as e:
    print(f"   ❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
