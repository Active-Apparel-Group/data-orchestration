---
# Monday.com Board Deployment Workflow Template
# Use this template when deploying a new Monday.com board to Kestra
# This is a specialized workflow template, not a generic dev/ops task

# Workflow metadata
workflow_type: "monday_board_deployment"
template_version: "1.0"
board_id: "{{ board_id }}"
board_name: "{{ board_name }}"
table_name: "{{ table_name | default(board_name | lower | replace(' ', '_')) }}"
created_by: "{{ developer_name }}"
created_date: "{{ creation_date }}"

# Board-specific configuration
board_config:
  monday_board_id: "{{ board_id }}"
  board_name: "{{ board_name }}"
  target_table: "{{ table_name }}"
  update_frequency: "{{ update_frequency | default('daily') }}"  # daily, hourly, weekly
  auto_reject_board_relations: true  # Always true for production deployments
  
# Deployment checklist (specific to Monday.com boards)
checklist:
  discovery:
    - "[ ] Identify Monday.com board ID: {{ board_id }}"
    - "[ ] Analyze board structure and columns using universal_board_extractor.py"
    - "[ ] Review existing similar boards for patterns"
    - "[ ] Determine update frequency requirements"
    - "[ ] Confirm target SQL table naming convention"
  
  development:
    - "[ ] Generate script using universal_board_extractor.py with board ID {{ board_id }}"
    - "[ ] Review generated script in dev/monday-boards-dynamic/generated/"
    - "[ ] Test script in TEST_MODE with limited data sample"
    - "[ ] Validate data types and column mappings"
    - "[ ] Verify board_relation columns are auto-rejected"
    - "[ ] Test zero-downtime atomic swap functionality"
    - "[ ] Validate error handling and retry logic"
  
  testing:
    - "[ ] Run data type validator on sample data"
    - "[ ] Test with production data volume in TEST_MODE"
    - "[ ] Verify SQL DDL generation and table creation"
    - "[ ] Test schema change detection and auto-adaptation"
    - "[ ] Validate logging output for Kestra compatibility"
    - "[ ] Performance test: confirm <3 minutes per 1000 records"
  
  deployment:
    - "[ ] Copy script to scripts/monday-boards/get_board_{{ table_name }}.py"
    - "[ ] Create Kestra workflow: workflows/monday-board-{{ table_name }}.yml"
    - "[ ] Deploy using tools/deploy-scripts-clean.ps1"
    - "[ ] Deploy workflow using tools/deploy-workflows.ps1"
    - "[ ] Test end-to-end execution in Kestra environment"
    - "[ ] Verify data quality and completeness"
    - "[ ] Configure monitoring and alerting"
  
  production:
    - "[ ] Schedule production runs in Kestra"
    - "[ ] Monitor first few production runs"
    - "[ ] Update DOCUMENTATION_STATUS.md"
    - "[ ] Add board to workflow_development_checklist.md as completed"
    - "[ ] Archive development files"
    - "[ ] Document any lessons learned or edge cases"

# Technical specifications (Monday.com specific)
technical_specs:
  script_location: "scripts/monday-boards/get_board_{{ table_name }}.py"
  workflow_location: "workflows/monday-board-{{ table_name }}.yml"
  dev_location: "dev/monday-boards-dynamic/generated/get_board_{{ table_name }}.py"
  
  required_tools:
    - "dev/monday-boards-dynamic/universal_board_extractor.py"
    - "dev/monday-boards-dynamic/core/data_type_validator.py"
    - "utils/db_helper.py"
    - "utils/logger_helper.py"
    - "tools/deploy-scripts-clean.ps1"
    - "tools/deploy-workflows.ps1"
  
  environment_variables:
    - "MONDAY_API_TOKEN"
    - "DB_DISTRIBUTION_HOST"
    - "DB_DISTRIBUTION_DATABASE"
    - "DB_DISTRIBUTION_USERNAME"
    - "DB_DISTRIBUTION_PASSWORD"

# Quality gates (specific to Monday.com boards)
quality_gates:
  data_validation:
    - "All column types correctly detected and mapped"
    - "Board relation columns automatically rejected"
    - "Date/datetime fields properly converted"
    - "Numeric fields correctly typed (not strings)"
    - "No data loss during atomic swap"
  
  performance:
    - "API fetch: ~250 records per 15-20 seconds"
    - "Data processing: ~500 records per second"
    - "Database insert: ~1000 records per 4-5 seconds"
    - "Total time: <3 minutes per 1000 records"
  
  production_readiness:
    - "Zero-downtime deployment confirmed"
    - "Error handling gracefully recovers from API timeouts"
    - "Retry logic with exponential backoff functional"
    - "Kestra-compatible logging implemented"
    - "TEST_MODE support for safe development"

# Standard Monday.com board deployment commands
commands:
  generate_script:
    command: "python dev/monday-boards-dynamic/universal_board_extractor.py"
    description: "Generate extraction script for board {{ board_id }}"
  
  test_script:
    command: "python dev/monday-boards-dynamic/generated/get_board_{{ table_name }}.py"
    environment: "TEST_MODE=true"
    description: "Test generated script with limited data"
  
  validate_data_types:
    command: "python dev/monday-boards-dynamic/core/data_type_validator.py {{ board_id }}"
    description: "Analyze and validate data types for board"
  
  deploy_to_production:
    command: "powershell tools/deploy-scripts-clean.ps1"
    description: "Deploy script to production location"
  
  deploy_workflow:
    command: "powershell tools/deploy-workflows.ps1 deploy-all"
    description: "Deploy Kestra workflow"

# Risk assessment (Monday.com specific)
risks:
  - risk: "Monday.com API rate limiting or timeouts"
    impact: "medium"
    probability: "low"
    mitigation: "Implemented 60s timeout and 3-retry exponential backoff"
  
  - risk: "Board schema changes breaking extraction"
    impact: "high"
    probability: "medium"
    mitigation: "Dynamic schema detection auto-adapts to changes"
  
  - risk: "Large data volume causing performance issues"
    impact: "medium"
    probability: "low"
    mitigation: "Tested with 3000+ records, optimized bulk operations"
  
  - risk: "Database connectivity issues during atomic swap"
    impact: "high"
    probability: "low"
    mitigation: "Atomic swap ensures zero data loss, rollback capability"

# Success criteria (Monday.com deployment specific)
success_criteria:
  functional:
    - "Board {{ board_id }} data successfully extracted and loaded"
    - "All expected columns present with correct data types"
    - "Zero-downtime deployment achieved"
    - "Scheduled updates running reliably in Kestra"
  
  technical:
    - "Generated script follows established patterns"
    - "Performance meets benchmarks (<3 min per 1000 records)"
    - "Error handling comprehensive and tested"
    - "Monitoring and alerting configured"
  
  operational:
    - "Development team can repeat process for new boards"
    - "Documentation updated and complete"
    - "Production support team trained on monitoring"

# Post-deployment monitoring
monitoring:
  kestra_workflow: "monday-board-{{ table_name }}"
  key_metrics:
    - "Execution time per run"
    - "Record count processed"
    - "API response times"
    - "Error rate percentage"
  
  alerts:
    - condition: "Execution time > 10 minutes"
      action: "Alert development team"
    - condition: "Error rate > 5%"
      action: "Escalate to on-call engineer"
    - condition: "Zero records processed"
      action: "Check Monday.com API connectivity"

# References to our established patterns
references:
  established_patterns: "dev/monday-boards-dynamic/get_planning_board.py"
  template_system: "dev/monday-boards-dynamic/templates/board_extractor_production.py.j2"
  deployment_process: "dev/checklists/WORKFLOW_DEPLOYMENT_PROCESS.md"
  development_checklist: "dev/checklists/workflow_development_checklist.md"
  
# Template usage instructions
usage:
  description: |
    This template should be used for every new Monday.com board deployment.
    It ensures consistency, completeness, and quality across all board deployments.
    
  steps:
    1. "Copy this template to tasks/workflows/monday-board-[BOARD_NAME]-[DATE].yml"
    2. "Fill in board_id, board_name, and other metadata"
    3. "Follow the checklist step by step"
    4. "Use the provided commands for each phase"
    5. "Mark items complete as you progress"
    6. "Archive to tasks/completed/ when deployment is finished"

version: "1.0"
