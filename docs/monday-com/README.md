# 📚 Monday.com API Documentation

Comprehensive Monday.com API reference documentation for integration development.

## 📁 **Documentation Structure**

### **🔧 API_Reference/** 
Complete Monday.com API documentation covering all endpoints, column types, and features:
- **Core Objects**: Boards, Items, Groups, Columns, Users, Workspaces
- **Column Types**: Status, Date, People, Timeline, Numbers, Text, etc.
- **Advanced Features**: Webhooks, Notifications, Subitems, Board Views
- **Platform APIs**: Account, Teams, Plans, Versions

*60+ detailed reference files covering every aspect of the Monday.com API*

### **📧 Emails__Activities_API_Reference/**
Email and activity integration APIs:
- Custom activity creation and management
- Timeline item handling
- Email integration patterns

### **📖 Introduction/**
Getting started guides and API overview:
- About the API reference
- Authentication and setup guidance

### **🏪 Marketplace_API_reference/**
Marketplace and monetization APIs:
- App installation and subscription management
- Monetization info and status tracking
- App subscription operations and discounts

## 🎯 **Usage with Kestra Integration**

This documentation supports the Monday.com adapter implementation in:
```
scripts/audit_pipeline/adapters/monday.py
```

## 🚀 **Key Resources**

- **Boards.md** - Core board operations
- **Items.md** - Item CRUD operations  
- **Column_types_reference.md** - All available column types
- **Webhooks.md** - Real-time integration setup
- **Platform_API.md** - Authentication and platform features

## 📋 **Quick Reference**

Most commonly used for audit pipeline integration:
- **Items**: Create, read, update board items
- **Column_values**: Extract and manipulate data
- **Boards**: Access board structure and metadata
- **Users**: User information and permissions

---

*Complete Monday.com API documentation ready for integration development*
