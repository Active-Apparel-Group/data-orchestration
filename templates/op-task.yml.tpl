---
# Unique identifier (auto-filled by scaffold tool)
id: "{{ task_id }}"

# Metadata
type: ops
title: "{{ title }}"
description: >
  {{ description }}

# Scheduling (cron format or manual trigger)
schedule: "{{ cron_expression }}"  # e.g., "0 2 * * *" for nightly at 02:00, or "manual" for on-demand

# Operation category (aligns with our existing tools)
category: "{{ operation_category }}"  # deployment, maintenance, monitoring, data-quality, backup

# Context & references (respecting our current docs structure)
context:
  runbook: "docs/runbooks/{{ operation_name }}-runbook.md"
  checklist: "dev/checklists/{{ operation_category }}_checklist.md"
  logs_location: "{{ log_path }}"  # Where operation logs are stored

# Checklist: marks completion status
checklist:
  - "[ ] Validate prerequisites and environment"
  - "[ ] Execute primary operation steps"
  - "[ ] Verify operation success"
  - "[ ] Update monitoring/status"
  - "[ ] Archive logs and cleanup"
  - "[ ] Document any issues or improvements"

# Operation steps (following our established patterns)
jobs:
  - name: Pre-flight checks
    command: "{{ pre_check_command }}"
    working_directory: "{{ working_dir | default('.') }}"
    timeout_minutes: 5
    
  - name: Execute main operation
    command: "{{ main_command }}"
    working_directory: "{{ working_dir | default('.') }}"
    timeout_minutes: "{{ timeout_minutes | default(30) }}"
    
  - name: Post-operation validation
    command: "{{ validation_command }}"
    working_directory: "{{ working_dir | default('.') }}"
    timeout_minutes: 5

# Environment requirements (aligns with our .env pattern)
environment:
  required_vars:
    - "{{ required_env_var_1 }}"
    - "{{ required_env_var_2 }}"
  optional_vars:
    - "{{ optional_env_var_1 }}"

# Dependencies (respecting our current structure)
dependencies:
  tools:
    - "{{ required_tool_1 }}"  # e.g., docker, python, powershell
  services:
    - "{{ required_service_1 }}"  # e.g., kestra, sql-server
  files:
    - "{{ required_file_1 }}"  # e.g., requirements.txt, config.yaml

# Notifications (following our existing patterns)
notifications:
  on_failure:
    - type: log
      target: "{{ error_log_path }}"
    - type: alert
      target: "{{ alert_channel }}"  # e.g., slack channel, email list
  on_success:
    - type: log
      target: "{{ success_log_path }}"

# Resource cleanup and archival (respecting our current organization)
post_run:
  archive:
    logs: "{{ archive_logs_to }}"
    outputs: "{{ archive_outputs_to }}"
  cleanup:
    temp_files: "{{ temp_files_pattern }}"
  retention_days: "{{ retention_days | default(30) }}"

# Monitoring and metrics
monitoring:
  health_check: "{{ health_check_command }}"
  metrics:
    - name: "{{ metric_name }}"
      command: "{{ metric_command }}"
  alerts:
    - condition: "{{ alert_condition }}"
      action: "{{ alert_action }}"

# Integration with our existing tools
integration:
  kestra_workflow: "workflows/{{ workflow_name }}.yml"  # If this op has a Kestra counterpart
  deployment_script: "tools/{{ deployment_script }}"   # If this uses our existing tools
  makefile_target: "{{ makefile_target }}"             # If this can be run via make
