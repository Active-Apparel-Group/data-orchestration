# Customer Mapping UI Design Plan

## Overview
This document outlines the design and implementation plan for building an Electron-based UI to maintain customer mapping data stored in `customer_mapping.yaml`. This UI will serve as the primary interface for data architects and operations teams to manage complex customer configuration rules for our enterprise data orchestration system.

## Current State Analysis

### Existing Customer Mapping Structure
- **Location**: `docs/mapping/customer_mapping.yaml`
- **Current Customers**: 36 customers (review_count: 36)
- **Status Types**: `approved`, `review`
- **Data Sources Integration**: 
  - `packed_products`
  - `shipped`
  - `master_order_list`
  - `mon_customer_ms`

### Current Matching Logic Integration
- **Primary Module**: `src/audit_pipeline/matching.py`
- **Configuration Module**: `src/audit_pipeline/config.py`
- **Current Strategies**: `standard`, `alias_related_item`
- **Performance Optimizations**: Customer config caching, vectorized operations

## New Mapping Standard Requirements

### Enhanced Configuration Structure
```yaml
canonical: CUSTOMER_NAME
status: review|approved
packed_products: "source_name"
shipped: "source_name"
master_order_list:
  - "order_source_1"
  - "order_source_2"
mon_customer_ms: "source_name"
aliases:
  - "alias_1"
  - "alias_2"
matching_config:
  style_match_strategy: "standard"|"alias_related_item"
  preferred_po_field: "Customer_PO"|"Customer_Alt_PO"
  style_field_override: "field_name"
  fuzzy_threshold: 85
  size_aliases:
    "XS": ["EXTRA SMALL", "XSMALL"]
    # ... etc
  exact_match_fields: ["field1", "field2"]
  fuzzy_match_fields: ["field1", "field2"]
```

### Migration Strategy
- **Phase 1**: Upgrade all customers to include `matching_config` section
- **Default Strategy**: Set `style_match_strategy: "standard"` for most customers
- **Special Cases**: Maintain `alias_related_item` for customers like RHYTHM who require it
- **Gradual Rollout**: Start with default/blank configurations, then customize as needed

## Electron UI Design Plan

### 1. Architecture Overview

#### Technology Stack
- **Frontend**: Electron + React + TypeScript
- **UI Framework**: Material-UI or Ant Design for enterprise look
- **Data Management**: React Context + Custom Hooks
- **YAML Processing**: js-yaml library
- **Validation**: Joi or Yup for schema validation
- **File Operations**: Node.js fs module with proper error handling

#### Project Structure
```
customer-mapping-ui/
├── src/
│   ├── main/                 # Electron main process
│   │   ├── main.ts
│   │   ├── file-manager.ts   # YAML file operations
│   │   └── ipc-handlers.ts   # Inter-process communication
│   ├── renderer/             # React frontend
│   │   ├── components/
│   │   │   ├── CustomerList/
│   │   │   ├── CustomerForm/
│   │   │   ├── MatchingConfig/
│   │   │   └── ValidationPanel/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   └── shared/               # Shared types and utilities
├── assets/
├── build/
└── package.json
```

### 2. Core Features

#### 2.1 Customer Management Interface
- **Customer List View**
  - Searchable/filterable table of all customers
  - Status indicators (approved/review)
  - Quick actions (edit, duplicate, delete)
  - Bulk operations support
  
- **Customer Detail Form**
  - Tabbed interface for different configuration sections
  - Real-time validation
  - Auto-save capabilities
  - Change tracking and diff view

#### 2.2 Data Source Mapping
- **Source Configuration**
  - Dropdown selectors for known data sources
  - Free-text input for new sources
  - Validation against existing data sources
  - Multi-select for `master_order_list`

#### 2.3 Matching Configuration Builder
- **Strategy Selection**
  - Radio buttons for `standard` vs `alias_related_item`
  - Dynamic form fields based on strategy
  
- **Field Mapping Interface**
  - Drag-and-drop field selector
  - Field override configuration
  - PO field preference selection
  
- **Fuzzy Matching Tuning**
  - Threshold slider with real-time preview
  - Size alias management (add/remove/edit)
  - Match field configuration with checkboxes

#### 2.4 Validation & Testing
- **Real-time Validation**
  - YAML schema validation
  - Business rule validation
  - Circular reference detection
  
- **Configuration Testing**
  - Mock data preview
  - Configuration impact analysis
  - Integration with existing matching logic

#### 2.5 Import/Export & Migration
- **Batch Operations**
  - CSV import for bulk customer creation
  - Export current configuration
  - Backup and restore functionality
  
- **Migration Tools**
  - Upgrade all customers to new standard
  - Configuration templates
  - Rollback capabilities

### 3. User Experience Design

#### 3.1 Navigation Structure
```
┌─ Customer Mapping UI ────────────────────────────┐
├─ Dashboard                                       │
│  ├─ Summary statistics                           │
│  ├─ Recent changes                               │
│  └─ Validation status                            │
├─ Customers                                       │
│  ├─ List View (filterable/searchable)            │
│  └─ Detail View (tabbed editor)                  │
├─ Templates                                       │
│  ├─ Configuration templates                      │
│  └─ Bulk operation templates                     │
├─ Tools                                           │
│  ├─ Migration utilities                          │
│  ├─ Validation tools                             │
│  └─ Backup/restore                               │
└─ Settings                                        │
   ├─ Data source management                       │
   └─ Application preferences                      │
```

#### 3.2 Key User Flows
1. **Add New Customer**: Wizard-based creation with templates
2. **Edit Customer**: Quick edit mode vs full configuration mode
3. **Bulk Migration**: Step-by-step migration with preview and rollback
4. **Validation Workflow**: Real-time validation with error highlighting
5. **Testing Integration**: Preview matching behavior with sample data

### 4. Technical Implementation Plan

#### 4.1 Phase 1: Foundation (Weeks 1-2)
- [ ] Set up Electron + React project structure
- [ ] Implement basic YAML file reading/writing
- [ ] Create customer data model and TypeScript types
- [ ] Build basic customer list component
- [ ] Implement file backup and version management

#### 4.2 Phase 2: Core CRUD Operations (Weeks 3-4)
- [ ] Customer creation and editing forms
- [ ] Real-time YAML validation
- [ ] Basic search and filtering
- [ ] Alias management interface
- [ ] Status workflow (review → approved)

#### 4.3 Phase 3: Advanced Matching Configuration (Weeks 5-6)
- [ ] Matching configuration builder UI
- [ ] Strategy-specific form sections
- [ ] Size alias management
- [ ] Field mapping interface
- [ ] Fuzzy threshold tuning with preview

#### 4.4 Phase 4: Migration and Testing Tools (Weeks 7-8)
- [ ] Bulk customer upgrade utility
- [ ] Configuration template system
- [ ] Integration testing with matching.py
- [ ] Data validation and error reporting
- [ ] Export/import functionality

#### 4.5 Phase 5: Polish and Production (Weeks 9-10)
- [ ] UI/UX refinements
- [ ] Performance optimization
- [ ] Comprehensive error handling
- [ ] User documentation
- [ ] Deployment packaging

### 5. Integration Points

#### 5.1 Data Pipeline Integration
- **Matching Logic**: Direct integration with `src/audit_pipeline/matching.py`
- **Configuration Loading**: Leverage existing `config.py` module
- **Cache Management**: Handle customer config cache invalidation

#### 5.2 File System Integration
- **Live Editing**: Watch for external file changes
- **Conflict Resolution**: Handle concurrent edits
- **Backup Strategy**: Automatic versioning and rollback

#### 5.3 Validation Integration
- **Schema Validation**: Ensure YAML structure compliance
- **Business Rules**: Validate against audit pipeline requirements
- **Performance Impact**: Analyze configuration changes impact

### 6. Data Safety and Reliability

#### 6.1 Version Control Integration
- [ ] Git integration for change tracking
- [ ] Commit message automation
- [ ] Branch management for different environments

#### 6.2 Backup and Recovery
- [ ] Automatic backup before changes
- [ ] Point-in-time recovery
- [ ] Configuration diff and rollback

#### 6.3 Validation and Testing
- [ ] Schema validation with detailed error messages
- [ ] Business rule validation
- [ ] Integration testing with sample data
- [ ] Performance impact analysis

### 7. Security and Access Control

#### 7.1 Data Protection
- [ ] File permission management
- [ ] Change audit logging
- [ ] Secure credential handling for data sources

#### 7.2 User Management
- [ ] Role-based access (viewer, editor, admin)
- [ ] Change approval workflows
- [ ] Activity monitoring and logging

### 8. Success Criteria

#### 8.1 Functional Requirements
- [ ] Complete CRUD operations for customer mappings
- [ ] Seamless migration of all 36+ customers to new standard
- [ ] Real-time validation with clear error messages
- [ ] Integration with existing audit pipeline without disruption

#### 8.2 Performance Requirements
- [ ] Sub-second response times for common operations
- [ ] Handle 100+ customers without performance degradation
- [ ] Minimal memory footprint for desktop deployment

#### 8.3 Usability Requirements
- [ ] Intuitive interface requiring minimal training
- [ ] Clear visual feedback for all operations
- [ ] Comprehensive error handling and recovery
- [ ] Accessibility compliance (WCAG 2.1 AA)

### 9. Risk Mitigation

#### 9.1 Technical Risks
- **File Corruption**: Implement atomic writes and validation
- **Performance Issues**: Use lazy loading and pagination
- **Integration Failures**: Comprehensive testing suite

#### 9.2 Operational Risks
- **Data Loss**: Multiple backup strategies
- **User Errors**: Confirmation dialogs and undo functionality
- **Version Conflicts**: Merge conflict resolution UI

### 10. Next Steps

#### Immediate Actions (This Week)
1. **Review and Approve Plan**: Stakeholder review of this document
2. **Set Up Development Environment**: Electron + React boilerplate
3. **Define Data Model**: TypeScript interfaces for customer mapping

#### Week 1 Deliverables
1. **Project Setup**: Working Electron application skeleton
2. **YAML Integration**: Basic file reading and parsing
3. **Customer List**: Simple list view of existing customers

#### Decision Points
1. **UI Framework Choice**: Material-UI vs Ant Design vs Custom
2. **State Management**: Context API vs Redux vs Zustand
3. **Deployment Strategy**: Installer vs Portable vs Web-based option

---

**Document Version**: 1.0  
**Last Updated**: June 3, 2025  
**Next Review**: After stakeholder feedback  
**Owner**: Chief Data Architect
