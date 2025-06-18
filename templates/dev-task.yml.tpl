---
# Development Task Template
# Use this template for feature development, bug fixes, and enhancements
# Auto-filled by scaffold tool

# Unique identifier (matches filename)
id: "{{ task_id }}"

# Metadata
type: dev
project: "{{ project_name }}"
title: "{{ task_title }}"
created: "{{ creation_date }}"
assigned_to: "{{ assignee | default('unassigned') }}"
priority: "{{ priority | default('medium') }}"  # low, medium, high, critical

# Context & references (adapted to our current docs structure)
context:
  description: |
    {{ task_description }}
    
    Background:
    {{ background_info }}
    
    Acceptance Criteria:
    {{ acceptance_criteria }}
    
  docs:
    design: "docs/design/{{ project_name }}-design.md"
    development: "docs/development/{{ project_name }}-development.md" 
    deployment: "docs/deployment/{{ project_name }}-deployment.md"
    mapping: "docs/mapping/{{ project_name }}-mapping.md"
  
  checklists:
    development: "dev/checklists/workflow_development_checklist.md"
    deployment: "dev/checklists/WORKFLOW_DEPLOYMENT_PROCESS.md"
    testing: "dev/checklists/testing_checklist.md"
  
  references:
    jira: "{{ jira_ticket | default('N/A') }}"
    slack: "{{ slack_thread | default('N/A') }}"
    related_tasks: []

# Dependencies (tracks task relationships)
dependencies:
  requires: []  # Other task IDs that must complete first
  blocks: []    # Task IDs that are waiting for this one
  external:     # External dependencies
    - "{{ external_dependency_1 | default('N/A') }}"

# Environment configuration (respecting our .env pattern)
environments:
  dev:
    database: "{{ dev_database | default('DB_DISTRIBUTION_DATABASE') }}"
    api_endpoints: "{{ dev_api_endpoints | default('N/A') }}"
    working_directory: "dev/{{ project_name }}/"
  staging:
    database: "{{ staging_database | default('N/A') }}"
    api_endpoints: "{{ staging_api_endpoints | default('N/A') }}"
    working_directory: "scripts/{{ project_name }}/"
  production:
    database: "{{ prod_database | default('DB_DISTRIBUTION_DATABASE') }}"
    api_endpoints: "{{ prod_api_endpoints | default('N/A') }}"
    working_directory: "workflows/"

# File structure (following our established patterns)
file_structure:
  dev_location: "dev/{{ project_name }}/"
  scripts_location: "scripts/{{ project_name }}/"
  workflow_location: "workflows/{{ project_name }}.yml"
  test_location: "tests/{{ project_name }}/"
  utils_dependencies:
    - "utils/db_helper.py"
    - "utils/logger_helper.py"
    - "utils/config.yaml"
    - "utils/data_mapping.yaml"

# Main development checklist
checklist:
  planning:
    - "[ ] Requirements analysis complete"
    - "[ ] Technical design documented"
    - "[ ] Dependencies identified"
    - "[ ] Create workflow plan in dev/checklists/workflow_plans/"
  
  development:
    - "[ ] Create feature branch: git checkout -b feat/{{ task_id }}"
    - "[ ] Create dev folder: dev/{{ project_name }}/"
    - "[ ] Implement core functionality using utils/db_helper.py patterns"
    - "[ ] Add utils/logger_helper.py for Kestra-compatible logging"
    - "[ ] Implement comprehensive error handling and retry logic"
    - "[ ] Add TEST_MODE support for development testing"
    - "[ ] Write unit tests in tests/{{ project_name }}/"
    - "[ ] Update documentation following our standards"
  
  validation:
    - "[ ] Run tests using pytest"
    - "[ ] Code review completed"
    - "[ ] Follow workflow_development_checklist.md requirements"
    - "[ ] Test with limited data in TEST_MODE"
    - "[ ] Validate against existing integration patterns"
  
  deployment:
    - "[ ] Deploy to scripts/{{ project_name }}/ using tools/deploy-scripts-clean.ps1"
    - "[ ] Create Kestra workflow in workflows/{{ project_name }}.yml"
    - "[ ] Deploy workflow using tools/deploy-workflows.ps1"
    - "[ ] Test end-to-end in Kestra environment"
    - "[ ] Follow WORKFLOW_DEPLOYMENT_PROCESS.md"
  
  closure:
    - "[ ] Update workflow_development_checklist.md with completion"
    - "[ ] Update DOCUMENTATION_STATUS.md"
    - "[ ] Archive development files appropriately"
    - "[ ] Document lessons learned"

# Detailed workflow steps (adapted to our current tools and processes)
workflow:
  setup:
    - name: "Create development environment"
      command: "mkdir dev\\{{ project_name }}\\testing dev\\{{ project_name }}\\validation"
      working_directory: "."
      validation: "directory_exists('dev/{{ project_name }}')"
    
    - name: "Initialize project structure"
      manual_step: true
      guidance: |
        1. Copy relevant template from dev/monday-boards-dynamic/ or similar
        2. Set up testing framework following existing patterns
        3. Configure logger_helper.py integration
        4. Set up db_helper.py database connections
  
  development:
    - name: "Implement core features"
      manual_step: true
      guidance: |
        1. Follow established patterns from existing workflows
        2. Use utils/db_helper.py for database operations
        3. Use utils/logger_helper.py for logging
        4. Implement retry logic and error handling
        5. Add TEST_MODE for development testing
        6. Follow zero-downtime patterns for production scripts
    
    - name: "Run development tests"
      command: "python dev\\{{ project_name }}\\testing\\test_{{ project_name }}.py"
      working_directory: "."
      validation: "exit_code == 0"
  
  validation:
    - name: "Code quality and testing"
      command: "python -m pytest tests\\{{ project_name }}\\ -v"
      working_directory: "."
      validation: "all_tests_pass"
    
    - name: "Integration validation"
      command: "python dev\\{{ project_name }}\\validation\\validate_{{ project_name }}.py"
      working_directory: "."
      validation: "integration_tests_pass"
  
  deployment:
    - name: "Deploy scripts to production location"
      command: ".\\tools\\deploy-scripts-clean.ps1"
      working_directory: "tools"
      validation: "scripts_deployed_successfully"
    
    - name: "Create and deploy Kestra workflow"
      command: ".\\tools\\deploy-workflows.ps1 deploy-all"
      working_directory: "tools"
      validation: "workflow_deployed_to_kestra"
    
    - name: "End-to-end testing in Kestra"
      manual_step: true
      guidance: |
        1. Access Kestra UI
        2. Trigger workflow execution
        3. Monitor logs and validate results
        4. Verify data quality and completeness

# Success criteria (adapted to our current standards)
success_criteria:
  functional:
    - "All acceptance criteria met"
    - "Zero-downtime deployment achieved"
    - "Performance targets met (per workflow_development_checklist.md)"
  
  technical:
    - "Follows established patterns (db_helper, logger_helper, config)"
    - "Production-grade error handling and retry logic"
    - "Comprehensive logging for Kestra monitoring"
    - "TEST_MODE support for development"
  
  operational:
    - "Successfully deployed to Kestra"
    - "Workflow monitoring configured"
    - "Documentation updated per standards"
    - "Follows WORKFLOW_DEPLOYMENT_PROCESS.md"

# Integration with our existing tools
integration:
  tools:
    deployment: "tools/deploy-scripts-clean.ps1, tools/deploy-workflows.ps1"
    testing: "pytest, manual validation scripts"
    monitoring: "Kestra UI, workflow logs"
  
  dependencies:
    utils:
      - "utils/db_helper.py"
      - "utils/logger_helper.py" 
      - "utils/config.yaml"
      - "utils/data_mapping.yaml"
    
  makefile_targets:
    - "make test"      # Run tests
    - "make lint"      # Code quality
    - "make up"        # Start Kestra
    - "make logs"      # View logs

# Risk management (specific to our environment)
risks:
  - risk: "Database connectivity issues during deployment"
    impact: "high"
    probability: "medium"
    mitigation: "Test db_helper.py connections in dev first"
  
  - risk: "Kestra workflow deployment failure"
    impact: "medium"
    probability: "low"
    mitigation: "Use tools/deploy-workflows.ps1 with validation"
  
  - risk: "Zero-downtime requirement not met"
    impact: "high"
    probability: "low"
    mitigation: "Follow atomic swap patterns from existing workflows"

# File locations (template variables for our structure)
file_paths:
  dev_script: "dev/{{ project_name }}/{{ main_script_name | default('main') }}.py"
  production_script: "scripts/{{ project_name }}/{{ main_script_name | default('main') }}.py"
  kestra_workflow: "workflows/{{ project_name }}.yml"
  tests: "tests/{{ project_name }}/"
  documentation: "docs/{{ doc_category | default('design') }}/{{ project_name }}-{{ doc_type | default('design') }}.md"

# Post-completion actions
post_completion:
  - name: "Update project documentation"
    command: "scripts/update-docs.sh {{ project_name }}"
  
  - name: "Notify stakeholders"
    command: "scripts/notify-completion.sh {{ task_id }}"
  
  - name: "Archive task files"
    command: "mv tasks/dev/{{ task_id }}.yml tasks/completed/"

# Metadata for tracking
tracking:
  estimated_hours: "{{ estimated_hours }}"
  actual_hours: "{{ actual_hours | default('TBD') }}"
  start_date: "{{ start_date | default('TBD') }}"
  end_date: "{{ end_date | default('TBD') }}"
  status: "{{ status | default('not_started') }}"  # not_started, in_progress, blocked, completed, cancelled

# Version for template evolution
version: "1.0"
