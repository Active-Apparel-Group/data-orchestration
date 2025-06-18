# Codebase Configuration Audit Report

**Generated:** 2025-06-17 20:45:08

## Summary Statistics

- **Total Files Scanned:** 345
- **Files with DB Connections:** 129
- **Files with YAML Mappings:** 87
- **Files with Hardcoded Configs:** 131

## Migration Priority Breakdown

- **Low:** 123 files
- **Medium:** 222 files

## File Tracking Table

| File | Folder | DB Connection | YAML Mapping | Priority | Effort | Notes |
|------|--------|---------------|--------------|----------|--------|-------|
| [README.md](README.md) | . | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 DB patterns; 3 YAML patterns |
| [dev\audit-pipeline\validation\validate_env.py](dev\audit-pipeline\validation\validate_env.py) | dev\audit-pipeline\validation | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [dev\checklists\workflow_development_checklist.md](dev\checklists\workflow_development_checklist.md) | dev\checklists | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [dev\checklists\workflow_plans\customer_master_schedule_plan.md](dev\checklists\workflow_plans\customer_master_schedule_plan.md) | dev\checklists\workflow_plans | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [dev\checklists\workflow_plans\hello_import_test_plan.md](dev\checklists\workflow_plans\hello_import_test_plan.md) | dev\checklists\workflow_plans | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [dev\checklists\workflow_plans\monday_boards_plan.md](dev\checklists\workflow_plans\monday_boards_plan.md) | dev\checklists\workflow_plans | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 DB patterns; 1 YAML patterns |
| [dev\config_update\README.md](dev\config_update\README.md) | dev\config_update | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs; 4 YAML patterns |
| [dev\config_update\scan_codebase_config.py](dev\config_update\scan_codebase_config.py) | dev\config_update | ☑️ | ☑️ | 🟡 Medium | Large (8+ hours) | 10 hardcoded configs; 9 DB patterns; 10 YAML patterns |
| [dev\monday-boards\get_board_planning.py](dev\monday-boards\get_board_planning.py) | dev\monday-boards | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 6 DB patterns; 1 YAML patterns |
| [dev\order-staging\debugging\logs\deploy_staging.py](dev\order-staging\debugging\logs\deploy_staging.py) | dev\order-staging\debugging\logs | ☑️ | ☐ | 🟡 Medium | Medium (4-8 hours) | 3 hardcoded configs; 5 DB patterns |
| [dev\order-staging\validation\milestone_2_customer_analysis.py](dev\order-staging\validation\milestone_2_customer_analysis.py) | dev\order-staging\validation | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 5 DB patterns |
| [dev\shared\test_framework.py](dev\shared\test_framework.py) | dev\shared | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 1 DB patterns |
| [dev\shared\test_repo_root_import.py](dev\shared\test_repo_root_import.py) | dev\shared | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [docs\DOCUMENTATION_STATUS.md](docs\DOCUMENTATION_STATUS.md) | docs | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 DB patterns; 1 YAML patterns |
| [docs\deployment\DEPLOYMENT-COMPLETE.md](docs\deployment\DEPLOYMENT-COMPLETE.md) | docs\deployment | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\deployment\NAMESPACE-STRUCTURE-FIXED.md](docs\deployment\NAMESPACE-STRUCTURE-FIXED.md) | docs\deployment | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\deployment\TOOLS-FINAL.md](docs\deployment\TOOLS-FINAL.md) | docs\deployment | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\design\adr-0001-kestra.md](docs\design\adr-0001-kestra.md) | docs\design | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\design\architecture.md](docs\design\architecture.md) | docs\design | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs; 2 YAML patterns |
| [docs\design\customer_master_schedule_add_order_design.md](docs\design\customer_master_schedule_add_order_design.md) | docs\design | ☐ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 5 hardcoded configs; 5 YAML patterns |
| [docs\design\dynamic_monday_board_implementation_plan.md](docs\design\dynamic_monday_board_implementation_plan.md) | docs\design | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 3 hardcoded configs; 4 DB patterns; 2 YAML patterns |
| [docs\design\dynamic_monday_board_template_system.md](docs\design\dynamic_monday_board_template_system.md) | docs\design | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 3 hardcoded configs; 1 DB patterns; 2 YAML patterns |
| [docs\design\dynamic_monday_board_template_system_diagrams.md](docs\design\dynamic_monday_board_template_system_diagrams.md) | docs\design | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 DB patterns; 1 YAML patterns |
| [docs\design\mapping\customer-mapping-ui-checklist.md](docs\design\mapping\customer-mapping-ui-checklist.md) | docs\design\mapping | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [docs\design\mapping\customer-mapping-ui-plan.md](docs\design\mapping\customer-mapping-ui-plan.md) | docs\design\mapping | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [docs\design\mapping\customer-mapping-ui-technical-spec.md](docs\design\mapping\customer-mapping-ui-technical-spec.md) | docs\design\mapping | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [docs\design\master_mapping_developer_guide.md](docs\design\master_mapping_developer_guide.md) | docs\design | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 3 hardcoded configs; 2 DB patterns; 2 YAML patterns |
| [docs\design\migrate_config_yaml_to_env.md](docs\design\migrate_config_yaml_to_env.md) | docs\design | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 DB patterns; 3 YAML patterns |
| [docs\development\DEVELOPER_HANDOVER.md](docs\development\DEVELOPER_HANDOVER.md) | docs\development | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 5 DB patterns; 2 YAML patterns |
| [docs\development\development_process_configuration.md](docs\development\development_process_configuration.md) | docs\development | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 DB patterns |
| [docs\development\framework_documentation.md](docs\development\framework_documentation.md) | docs\development | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 DB patterns; 1 YAML patterns |
| [docs\diagrams\staging_data_flow.md](docs\diagrams\staging_data_flow.md) | docs\diagrams | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [docs\diagrams\staging_workflow_overview.md](docs\diagrams\staging_workflow_overview.md) | docs\diagrams | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [docs\mapping\IMPLEMENTATION_CHECKLIST.md](docs\mapping\IMPLEMENTATION_CHECKLIST.md) | docs\mapping | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 DB patterns; 3 YAML patterns |
| [docs\mapping\field_mapping_matrix.yaml](docs\mapping\field_mapping_matrix.yaml) | docs\mapping | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [docs\mapping\mapping_fields.yaml](docs\mapping\mapping_fields.yaml) | docs\mapping | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [docs\mapping\monday_column_ids.json](docs\mapping\monday_column_ids.json) | docs\mapping | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 4 hardcoded configs |
| [docs\mapping\orders_unified_monday_comparison.md](docs\mapping\orders_unified_monday_comparison.md) | docs\mapping | ☑️ | ☐ | 🟡 Medium | Large (8+ hours) | 6 hardcoded configs; 2 DB patterns |
| [docs\mapping\orders_unified_monday_mapping.yaml](docs\mapping\orders_unified_monday_mapping.yaml) | docs\mapping | ☐ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 4 hardcoded configs; 2 YAML patterns |
| [docs\monday-com\API_Reference\Account.md](docs\monday-com\API_Reference\Account.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Activity_logs.md](docs\monday-com\API_Reference\Activity_logs.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Assets_files.md](docs\monday-com\API_Reference\Assets_files.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Board_views.md](docs\monday-com\API_Reference\Board_views.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Boards.md](docs\monday-com\API_Reference\Boards.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Checkbox.md](docs\monday-com\API_Reference\Checkbox.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Column_values.md](docs\monday-com\API_Reference\Column_values.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Columns.md](docs\monday-com\API_Reference\Columns.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Complexity.md](docs\monday-com\API_Reference\Complexity.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Connect_boards.md](docs\monday-com\API_Reference\Connect_boards.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Country.md](docs\monday-com\API_Reference\Country.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Date.md](docs\monday-com\API_Reference\Date.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Dependency.md](docs\monday-com\API_Reference\Dependency.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Docs.md](docs\monday-com\API_Reference\Docs.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Document_blocks.md](docs\monday-com\API_Reference\Document_blocks.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Dropdown.md](docs\monday-com\API_Reference\Dropdown.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Email.md](docs\monday-com\API_Reference\Email.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Files_assets.md](docs\monday-com\API_Reference\Files_assets.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Folders.md](docs\monday-com\API_Reference\Folders.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Groups.md](docs\monday-com\API_Reference\Groups.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Hour.md](docs\monday-com\API_Reference\Hour.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Items.md](docs\monday-com\API_Reference\Items.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Items_page.md](docs\monday-com\API_Reference\Items_page.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Items_page_by_column_values.md](docs\monday-com\API_Reference\Items_page_by_column_values.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Link.md](docs\monday-com\API_Reference\Link.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Location.md](docs\monday-com\API_Reference\Location.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Long_text.md](docs\monday-com\API_Reference\Long_text.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Managed_columns.md](docs\monday-com\API_Reference\Managed_columns.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Me.md](docs\monday-com\API_Reference\Me.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Name_first_column.md](docs\monday-com\API_Reference\Name_first_column.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Notifications.md](docs\monday-com\API_Reference\Notifications.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Numbers.md](docs\monday-com\API_Reference\Numbers.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\People.md](docs\monday-com\API_Reference\People.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Person_deprecated.md](docs\monday-com\API_Reference\Person_deprecated.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Phone.md](docs\monday-com\API_Reference\Phone.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Plan.md](docs\monday-com\API_Reference\Plan.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Rating.md](docs\monday-com\API_Reference\Rating.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Status.md](docs\monday-com\API_Reference\Status.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Subitems.md](docs\monday-com\API_Reference\Subitems.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Tags.md](docs\monday-com\API_Reference\Tags.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Team_deprecated.md](docs\monday-com\API_Reference\Team_deprecated.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Teams.md](docs\monday-com\API_Reference\Teams.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Text.md](docs\monday-com\API_Reference\Text.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Timeline.md](docs\monday-com\API_Reference\Timeline.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Updates.md](docs\monday-com\API_Reference\Updates.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Users.md](docs\monday-com\API_Reference\Users.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Version.md](docs\monday-com\API_Reference\Version.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Versions.md](docs\monday-com\API_Reference\Versions.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Viewers.md](docs\monday-com\API_Reference\Viewers.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\Webhooks.md](docs\monday-com\API_Reference\Webhooks.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Week.md](docs\monday-com\API_Reference\Week.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\Workspaces.md](docs\monday-com\API_Reference\Workspaces.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\API_Reference\World_clock.md](docs\monday-com\API_Reference\World_clock.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\API_Reference\monday_doc.md](docs\monday-com\API_Reference\monday_doc.md) | docs\monday-com\API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 DB patterns |
| [docs\monday-com\Emails__Activities_API_Reference\Custom_activity.md](docs\monday-com\Emails__Activities_API_Reference\Custom_activity.md) | docs\monday-com\Emails__Activities_API_Reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\JSON\monday.json](docs\monday-com\JSON\monday.json) | docs\monday-com\JSON | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 5 hardcoded configs |
| [docs\monday-com\Marketplace_API_reference\App_installs.md](docs\monday-com\Marketplace_API_reference\App_installs.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\Marketplace_API_reference\App_subscription.md](docs\monday-com\Marketplace_API_reference\App_subscription.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\Marketplace_API_reference\App_subscription_operations.md](docs\monday-com\Marketplace_API_reference\App_subscription_operations.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\Marketplace_API_reference\App_subscriptions.md](docs\monday-com\Marketplace_API_reference\App_subscriptions.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\Marketplace_API_reference\Apps_monetization_info.md](docs\monday-com\Marketplace_API_reference\Apps_monetization_info.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\Marketplace_API_reference\Apps_monetization_status.md](docs\monday-com\Marketplace_API_reference\Apps_monetization_status.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\monday-com\Marketplace_API_reference\Marketplace_app_discounts.md](docs\monday-com\Marketplace_API_reference\Marketplace_app_discounts.md) | docs\monday-com\Marketplace_API_reference | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 DB patterns |
| [docs\plans\db_helper_refactoring_plan.md](docs\plans\db_helper_refactoring_plan.md) | docs\plans | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 hardcoded configs; 2 DB patterns; 2 YAML patterns |
| [docs\plans\master_mapping_implementation.md](docs\plans\master_mapping_implementation.md) | docs\plans | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 DB patterns; 6 YAML patterns |
| [docs\plans\master_mapping_implementation_complete.md](docs\plans\master_mapping_implementation_complete.md) | docs\plans | ☐ | ☑️ | 🟡 Medium | Large (8+ hours) | 10 hardcoded configs; 6 YAML patterns |
| [docs\plans\plan_phase01_mvp.md](docs\plans\plan_phase01_mvp.md) | docs\plans | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 3 YAML patterns |
| [docs\plans\staging_table_refactor_plan.md](docs\plans\staging_table_refactor_plan.md) | docs\plans | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs; 1 YAML patterns |
| [docs\plans\workflow_update_plan_v2.md](docs\plans\workflow_update_plan_v2.md) | docs\plans | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 YAML patterns |
| [docs\project\CLEANUP-COMPLETED.md](docs\project\CLEANUP-COMPLETED.md) | docs\project | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\project\CLEANUP-FINAL.md](docs\project\CLEANUP-FINAL.md) | docs\project | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\project\PROJECT-CLEANUP-PLAN.md](docs\project\PROJECT-CLEANUP-PLAN.md) | docs\project | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\project\PROJECT-ORGANIZATION-RULES.md](docs\project\PROJECT-ORGANIZATION-RULES.md) | docs\project | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [docs\runbooks\audit_pipeline_filtering_logic.md](docs\runbooks\audit_pipeline_filtering_logic.md) | docs\runbooks | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 hardcoded configs; 2 DB patterns; 2 YAML patterns |
| [docs\workflows\monday_board_groups_sync\PLAN.md](docs\workflows\monday_board_groups_sync\PLAN.md) | docs\workflows\monday_board_groups_sync | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [scripts\audit_pipeline\config.py](scripts\audit_pipeline\config.py) | scripts\audit_pipeline | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 6 DB patterns; 4 YAML patterns |
| [scripts\audit_pipeline\matching.py](scripts\audit_pipeline\matching.py) | scripts\audit_pipeline | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [scripts\audit_pipeline\report.py](scripts\audit_pipeline\report.py) | scripts\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [scripts\ayoun-flow\README.md](scripts\ayoun-flow\README.md) | scripts\ayoun-flow | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [scripts\customer_master_schedule\README.md](scripts\customer_master_schedule\README.md) | scripts\customer_master_schedule | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [scripts\customer_master_schedule\add_bulk_orders.py](scripts\customer_master_schedule\add_bulk_orders.py) | scripts\customer_master_schedule | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 3 hardcoded configs; 7 DB patterns; 4 YAML patterns |
| [scripts\customer_master_schedule\add_order.py](scripts\customer_master_schedule\add_order.py) | scripts\customer_master_schedule | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs; 6 YAML patterns |
| [scripts\customer_master_schedule\monday_integration.py](scripts\customer_master_schedule\monday_integration.py) | scripts\customer_master_schedule | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 DB patterns |
| [scripts\customer_master_schedule\order_mapping.py](scripts\customer_master_schedule\order_mapping.py) | scripts\customer_master_schedule | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs; 7 YAML patterns |
| [scripts\customer_master_schedule\order_queries.py](scripts\customer_master_schedule\order_queries.py) | scripts\customer_master_schedule | ☑️ | ☐ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 4 DB patterns |
| [scripts\customer_master_schedule_subitems\mon_add_customer_ms_subitems.py](scripts\customer_master_schedule_subitems\mon_add_customer_ms_subitems.py) | scripts\customer_master_schedule_subitems | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 3 hardcoded configs; 6 DB patterns; 3 YAML patterns |
| [scripts\customer_master_schedule_subitems\mon_get_subitems_async.py](scripts\customer_master_schedule_subitems\mon_get_subitems_async.py) | scripts\customer_master_schedule_subitems | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 7 DB patterns; 2 YAML patterns |
| [scripts\customer_master_schedule_subitems\mon_update_subitems_async.py](scripts\customer_master_schedule_subitems\mon_update_subitems_async.py) | scripts\customer_master_schedule_subitems | ☑️ | ☑️ | 🟡 Medium | Large (8+ hours) | 5 hardcoded configs; 8 DB patterns; 4 YAML patterns |
| [scripts\customer_master_schedule_subitems\monday_subitems_spec.md](scripts\customer_master_schedule_subitems\monday_subitems_spec.md) | scripts\customer_master_schedule_subitems | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs; 1 YAML patterns |
| [scripts\customer_master_schedule_subitems\update_subitems_plan.md](scripts\customer_master_schedule_subitems\update_subitems_plan.md) | scripts\customer_master_schedule_subitems | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 2 YAML patterns |
| [scripts\jobs\run_audit.py](scripts\jobs\run_audit.py) | scripts\jobs | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 1 DB patterns |
| [scripts\monday-boards\README.md](scripts\monday-boards\README.md) | scripts\monday-boards | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [scripts\monday-boards\add_board_groups.py](scripts\monday-boards\add_board_groups.py) | scripts\monday-boards | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 6 DB patterns |
| [scripts\monday-boards\get_board_planning.py](scripts\monday-boards\get_board_planning.py) | scripts\monday-boards | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 6 DB patterns; 1 YAML patterns |
| [scripts\monday-boards\sync_board_groups.py](scripts\monday-boards\sync_board_groups.py) | scripts\monday-boards | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 6 DB patterns |
| [scripts\order_staging\batch_processor.py](scripts\order_staging\batch_processor.py) | scripts\order_staging | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 2 DB patterns; 4 YAML patterns |
| [scripts\order_staging\error_handler.py](scripts\order_staging\error_handler.py) | scripts\order_staging | ☑️ | ☐ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 3 DB patterns |
| [scripts\order_staging\staging_config.py](scripts\order_staging\staging_config.py) | scripts\order_staging | ☑️ | ☐ | 🟡 Medium | Large (8+ hours) | 6 hardcoded configs; 2 DB patterns |
| [scripts\order_staging\staging_operations.py](scripts\order_staging\staging_operations.py) | scripts\order_staging | ☑️ | ☐ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 3 DB patterns |
| [scripts\order_sync_v2.py](scripts\order_sync_v2.py) | scripts | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 5 DB patterns |
| [scripts\test-sql\test_sql_enhanced.py](scripts\test-sql\test_sql_enhanced.py) | scripts\test-sql | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 4 DB patterns |
| [scripts\test-sql\test_sql_with_env.py](scripts\test-sql\test_sql_with_env.py) | scripts\test-sql | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 4 DB patterns |
| [scripts\test-this-out\README.md](scripts\test-this-out\README.md) | scripts\test-this-out | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [scripts\test-this-out\main.py](scripts\test-this-out\main.py) | scripts\test-this-out | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 4 DB patterns |
| [sql\ddl\README.md](sql\ddl\README.md) | sql\ddl | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\ddl\deploy_staging_infrastructure.sql](sql\ddl\deploy_staging_infrastructure.sql) | sql\ddl | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [sql\ddl\tables\orders\dbo_mon_coo_planning.sql](sql\ddl\tables\orders\dbo_mon_coo_planning.sql) | sql\ddl\tables\orders | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\ddl\tables\orders\dbo_mon_custmasterschedule.sql](sql\ddl\tables\orders\dbo_mon_custmasterschedule.sql) | sql\ddl\tables\orders | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\ddl\tables\orders\dbo_mon_custmasterschedule_subitems.sql](sql\ddl\tables\orders\dbo_mon_custmasterschedule_subitems.sql) | sql\ddl\tables\orders | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\ddl\tables\orders\error\err_mon_custmasterschedule.sql](sql\ddl\tables\orders\error\err_mon_custmasterschedule.sql) | sql\ddl\tables\orders\error | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [sql\ddl\tables\orders\error\err_mon_custmasterschedule_subitems.sql](sql\ddl\tables\orders\error\err_mon_custmasterschedule_subitems.sql) | sql\ddl\tables\orders\error | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [sql\ddl\tables\orders\staging\stg_mon_custmasterschedule.sql](sql\ddl\tables\orders\staging\stg_mon_custmasterschedule.sql) | sql\ddl\tables\orders\staging | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs |
| [sql\ddl\tables\orders\staging\stg_mon_custmasterschedule_subitems.sql](sql\ddl\tables\orders\staging\stg_mon_custmasterschedule_subitems.sql) | sql\ddl\tables\orders\staging | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs |
| [sql\staging\v_mon_customer_ms.sql](sql\staging\v_mon_customer_ms.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs |
| [sql\staging\v_mon_customer_ms_itemIDs.sql](sql\staging\v_mon_customer_ms_itemIDs.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\staging\v_mon_customer_ms_subitems.sql](sql\staging\v_mon_customer_ms_subitems.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\staging\v_orders_shipped.sql](sql\staging\v_orders_shipped.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs |
| [sql\staging\v_packed_barcode.sql](sql\staging\v_packed_barcode.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\staging\v_packed_products.sql](sql\staging\v_packed_products.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs |
| [sql\staging\v_shipped.sql](sql\staging\v_shipped.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\staging\v_shipped_products.sql](sql\staging\v_shipped_products.sql) | sql\staging | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [sql\tests\test_order_selection.sql](sql\tests\test_order_selection.sql) | sql\tests | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\audit_pipeline\check_rhythm_data.py](tests\audit_pipeline\check_rhythm_data.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 1 DB patterns |
| [tests\audit_pipeline\check_rhythm_shipped.py](tests\audit_pipeline\check_rhythm_shipped.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\audit_pipeline\debug_config.py](tests\audit_pipeline\debug_config.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 DB patterns |
| [tests\audit_pipeline\debug_rhythm_order_data.py](tests\audit_pipeline\debug_rhythm_order_data.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\audit_pipeline\performance\test_performance.py](tests\audit_pipeline\performance\test_performance.py) | tests\audit_pipeline\performance | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 1 DB patterns |
| [tests\audit_pipeline\performance\test_performance_fix.py](tests\audit_pipeline\performance\test_performance_fix.py) | tests\audit_pipeline\performance | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\audit_pipeline\query_master_order_count.py](tests\audit_pipeline\query_master_order_count.py) | tests\audit_pipeline | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 4 DB patterns; 1 YAML patterns |
| [tests\audit_pipeline\simple_rhythm_check.py](tests\audit_pipeline\simple_rhythm_check.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\audit_pipeline\simple_rhythm_check_fixed.py](tests\audit_pipeline\simple_rhythm_check_fixed.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\audit_pipeline\test_global_customer_audit_fuzzy_match.py](tests\audit_pipeline\test_global_customer_audit_fuzzy_match.py) | tests\audit_pipeline | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 2 hardcoded configs; 7 DB patterns; 3 YAML patterns |
| [tests\audit_pipeline\test_query.py](tests\audit_pipeline\test_query.py) | tests\audit_pipeline | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 1 DB patterns |
| [tests\audit_pipeline\unit\test_config_connections.py](tests\audit_pipeline\unit\test_config_connections.py) | tests\audit_pipeline\unit | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\audit_pipeline\unit\test_config_connections_pytest.py](tests\audit_pipeline\unit\test_config_connections_pytest.py) | tests\audit_pipeline\unit | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tests\customer_master_schedule_tests\final_validation.py](tests\customer_master_schedule_tests\final_validation.py) | tests\customer_master_schedule_tests | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\debug\debug_column_mapping.py](tests\debug\debug_column_mapping.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs; 4 YAML patterns |
| [tests\debug\debug_title.py](tests\debug\debug_title.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\debug\simple_db_test.py](tests\debug\simple_db_test.py) | tests\debug | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\debug\test_computed_fields.py](tests\debug\test_computed_fields.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 4 YAML patterns |
| [tests\debug\test_monday_api.py](tests\debug\test_monday_api.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs; 4 YAML patterns |
| [tests\debug\test_simple_steps.py](tests\debug\test_simple_steps.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 6 hardcoded configs; 4 YAML patterns |
| [tests\debug\test_sql_schema.py](tests\debug\test_sql_schema.py) | tests\debug | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\debug\test_staged_data_api.py](tests\debug\test_staged_data_api.py) | tests\debug | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs |
| [tests\debug\test_staging_insert.py](tests\debug\test_staging_insert.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs; 2 YAML patterns |
| [tests\debug\test_staging_table_data.py](tests\debug\test_staging_table_data.py) | tests\debug | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\debug\test_step_by_step.py](tests\debug\test_step_by_step.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 6 hardcoded configs; 4 YAML patterns |
| [tests\debug\test_workflow_validation.py](tests\debug\test_workflow_validation.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\debug\test_yaml_config.py](tests\debug\test_yaml_config.py) | tests\debug | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [tests\monday_boards\test_add_board_groups.py](tests\monday_boards\test_add_board_groups.py) | tests\monday_boards | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 4 DB patterns |
| [tests\monday_boards\test_sync.py](tests\monday_boards\test_sync.py) | tests\monday_boards | ☐ | ☐ | 🟡 Medium | Small (1-4 hours) | 2 hardcoded configs |
| [tests\other\cleanup_test_data.py](tests\other\cleanup_test_data.py) | tests\other | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\other\debug_column_values.py](tests\other\debug_column_values.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 4 YAML patterns |
| [tests\other\debug_mapping.py](tests\other\debug_mapping.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 4 YAML patterns |
| [tests\other\simple_db_test.py](tests\other\simple_db_test.py) | tests\other | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\other\test_complete_workflow.py](tests\other\test_complete_workflow.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\other\test_customer_master_schedule_db.py](tests\other\test_customer_master_schedule_db.py) | tests\other | ☐ | ☐ | 🟡 Medium | Minimal (<1 hour) | 1 hardcoded configs |
| [tests\other\test_debug_actual_api_call.py](tests\other\test_debug_actual_api_call.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\other\test_debug_mapping.py](tests\other\test_debug_mapping.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [tests\other\test_debug_transform.py](tests\other\test_debug_transform.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\other\test_debug_why_mapping_fails.py](tests\other\test_debug_why_mapping_fails.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\other\test_end_to_end_complete.py](tests\other\test_end_to_end_complete.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs; 4 YAML patterns |
| [tests\other\test_end_to_end_monday_integration.py](tests\other\test_end_to_end_monday_integration.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs; 4 YAML patterns |
| [tests\other\test_find_active_input.py](tests\other\test_find_active_input.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\other\test_monday_integration_complete.py](tests\other\test_monday_integration_complete.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 3 hardcoded configs; 4 YAML patterns |
| [tests\other\test_order_type.py](tests\other\test_order_type.py) | tests\other | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 4 YAML patterns |
| [tests\other\test_staging_debug_simple.py](tests\other\test_staging_debug_simple.py) | tests\other | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 5 DB patterns |
| [tests\test_minimal_workflow.py](tests\test_minimal_workflow.py) | tests | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 hardcoded configs; 1 DB patterns |
| [tools\deploy-scripts-clean.ps1](tools\deploy-scripts-clean.ps1) | tools | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [tools\deploy-workflows.ps1](tools\deploy-workflows.ps1) | tools | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [tools\extract_ddl.py](tools\extract_ddl.py) | tools | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [tools\workflow_generator.py](tools\workflow_generator.py) | tools | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 4 DB patterns; 3 YAML patterns |
| [ui\package.json](ui\package.json) | ui | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [utils\config.yaml](utils\config.yaml) | utils | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 3 DB patterns |
| [utils\data_mapping.yaml](utils\data_mapping.yaml) | utils | ☐ | ☑️ | 🟡 Medium | Large (8+ hours) | 15 hardcoded configs; 6 YAML patterns |
| [utils\db_helper.py](utils\db_helper.py) | utils | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 5 DB patterns; 2 YAML patterns |
| [utils\mapping_helper.py](utils\mapping_helper.py) | utils | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 5 YAML patterns |
| [utils\mapping_migration_helper.py](utils\mapping_migration_helper.py) | utils | ☑️ | ☑️ | 🟡 Medium | Medium (4-8 hours) | 1 hardcoded configs; 1 DB patterns; 3 YAML patterns |
| [utils\test_helper.py](utils\test_helper.py) | utils | ☑️ | ☐ | 🟡 Medium | Small (1-4 hours) | 1 DB patterns |
| [utils\test_mapping.py](utils\test_mapping.py) | utils | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 2 YAML patterns |
| [workflows\last-one.yml](workflows\last-one.yml) | workflows | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [workflows\test-this-out.yml](workflows\test-this-out.yml) | workflows | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |
| [workflows\wolf_750702.yml](workflows\wolf_750702.yml) | workflows | ☐ | ☑️ | 🟡 Medium | Small (1-4 hours) | 1 YAML patterns |

## Detailed Findings

