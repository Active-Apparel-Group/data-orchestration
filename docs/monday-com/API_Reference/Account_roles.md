---

title: Account_roles
source: https://developer.monday.com/api-reference/reference/account-roles
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query an account's user roles
tags: [code, api, monday-dot-com]
summary:

---

# Account roles

Learn how to query an account's user roles

When a user joins a monday.com account, they are assigned a role that specifies their permissions and what actions they can perform. All accounts have the following role types by default: admin, members, viewers, and guests. Some monday.com plans also allow you to create custom roles.

# Queries

Required scope: account:read

- Returns an object containing metadata about all user roles in an account (both default and custom)
- Can be queried directly at the root

## Examples

Example GQL queryExample JSON response
```
query {
  account_roles {
    id
    name
    roleType
  }
}
```

```
{
  "data": {
    "account_roles": [
      {
        "id": "1",
        "name": "admin",
        "roleType": "basic_role"
      },
      {
        "id": "2",
        "name": "member",
        "roleType": "basic_role"
      },
      {
        "id": "3",
        "name": "view_only",
        "roleType": "basic_role"
      },
      {
        "id": "4",
        "name": "guest",
        "roleType": "basic_role"
      }
    ]
  }
}
```

## Fields

The following field(s) are available in the account_roles query response.

Fields | Description
--- | ---
idID | The role's unique identifier.
nameString | The role's name.
roleTypeString | The role's type.
