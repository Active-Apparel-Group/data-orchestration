---

title: Workspaces
source: https://developer.monday.com/api-reference/reference/workspaces
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query and update monday workspaces using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Workspaces

Learn how to query and update monday workspaces using the platform API

monday.com workspaces are used by teams to manage their accounts by departments, teams, or projects. They contain boards, dashboards, and folders to help you stay organized.

# Queries

Required scope: workspaces:read

- Returns an array containing metadata about one or a collection of workspaces
- Can be queried directly at the root or nested within a boards query to return the workspace ID
- If nested, you only need the boards:read scope

Nested

GraphQLJavaScript
```
query {
  boards {
    id
    workspace_id
  }
}
```

```
let query = 'query { boards { id workspace_id }}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

At the root

GraphQLJavaScript
```
query {
  workspaces (ids: 1234567) {
    id
    name
    kind
    description
  }
}
```

```
let query = 'query { workspaces (id: 1234567) { id name kind description }}}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Querying the main workspace

Every account has a main workspace, but you typically can't query its details via the API.

However, users will eventually be able to query main workspace details as we complete a multi-product migration over the next few months. This capability will be released gradually, so you may not have access yet. All users will have this capability by the end of the migration.

Here's the expected behavior for both pre-and post-migration:

#### Pre-migration

If you query the workspaces on your account, the main workspace will not appear in the results because it has a null or -1 ID. You can, however, filter for boards in the main workspace by passing null as the workspace_id .

GraphQL
```
query {
  boards (workspace_ids: [null], limit:50) {
    name
  }
}
```

#### Post-migration

If you query the workspaces on your account, the main workspace will appear in the results with a real id . You can then use that ID to query the main workspace.

## Arguments

You can use the following argument(s) to reduce the number of results returned in your workspaces query.

Argument | Description | Enum values
--- | --- | ---
ids[ID!] | The specific workspace(s) to return. | 
kindWorkspaceKind | The kind of workspaces to return:openorclosed. | 
limitInt | The number of workspaces to return. The default is 25. | 
order_byWorkspacesOrderBy | The order in which to retrieve your workspaces. For now, you can only order bycreated_at. | 
pageInt | The page number to get. Starts at 1. | 
stateState | The state of workspaces you want to search by. The default isactive. | activeallarchived,deleted

## Fields

You can use the following field(s) to specify what information your workspaces query will return. Please note that some fields will have their own arguments or fields.

Field | Description | Enum values | Supported fields
--- | --- | --- | ---
account_productAccountProduct | The account's product that contains the workspace. |  | 
created_atDate | The workspace's creation date. |  | 
descriptionString | The workspace's description. |  | 
idID | The workspace's unique identifier. |  | 
is_default_workspaceBoolean | Returnstrueif a workspace is the default workspace of the product or account. Not all accounts can query themain workspace(see morehere). |  | 
kindWorkspaceKind | The workspace's kind:openorclosed. | closed,open | 
nameString! | The workspace's name. |  | 
owners_subscribers[User] | The workspace's owners. The default is 25. Requiresusers:readscope. |  | 
settingsWorkspaceSettings | The workspace's settings. |  | iconWorkspaceIcon
stateState | The state of the workspace. The default isactive. | active,all,archived,deleted | 
team_owners_subscribers[Team!] | The workspace's team owners. The default is 25. Requiresteams:readscope. |  | 
teams_subscribers[Team] | The teams subscribed to the workspace. The default is 25. Requiresteams:readscope. |  | 
users_subscribers[User] | The users subscribed to the workspace. The default is 25. Requiresusers:readscope. |  | 

# Mutations

Required scope: workspaces:write

## Create a workspace

The create_workspace mutation allows you to create a new workspace via the API. You can also specify what fields to query back from the new workspace when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_workspace (name:"New Cool Workspace", kind: open, description: "This is a cool description", account_product_id: 505616) {
    id
    description
  }
}
```

```
let query = 'mutation { create_workspace (name: \"New Cool Workspace\", kind: open, description: \"This is a cool description\", account_product_id: 505616) { id description } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define the new workspace's characteristics.

Arguments | Description | Enum values
--- | --- | ---
account_product_idID | The unique identifier of the account’s product in which to create the new workspace. Available in API versions2025-07and later. | 
descriptionString | The new workspace's description. | 
kindWorkspaceKind! | The new workspace's kind. | closed,open
nameString! | The new workspace's name. | 

## Update a workspace

The update_workspace mutation allows you to update a workspace via the API. You can also specify what fields to query back from the deleted workspace when you run the mutation.

GraphQLJavaScript
```
mutation {
  update_workspace (id: 1234567, attributes:{name:"Marketing team", description: "This workspace is for the marketing team." }) {
    id
  }
}
```

```
let query = 'mutation { update_workspace (id: 1234567, attributes:{name: \"Marketing team\", description: \"This workspace is for the marketing team.\"}) { id } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify what to update.

Arguments | Description
--- | ---
attributesUpdateWorkspaceAttributesInput! | The workspace's attributes to update.
idID | The unique identifier of the workspace.

## Delete a workspace

The delete_workspace mutation allows you to delete a workspace via the API. You can also specify what fields to query back from the deleted workspace when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_workspace (workspace_id: 1234567) {
    id
  }
}
```

```
let query = 'mutation { delete_workspace (workspace_id: 1234567) { id } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which workspace to delete.

Arguments | Description
--- | ---
workspace_idID! | The workspace's unique identifier.

## Add users to a workspace

The add_users_to_workspace mutation allows you to add users to a workspace via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  add_users_to_workspace (workspace_id: 1234567, user_ids: [12345678, 87654321, 01234567], kind: subscriber) {
    id
  }
}
```

```
let query = 'mutation { add_users_to_workspace (workspace_id: 1234567, user_ids: [12345678, 87654321, 01234567], kind: subscriber) { id } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to add to the workspace and their subscription type.

Arguments | Description | Enum values
--- | --- | ---
kindWorkspaceSubscriberKind | The user's role. | owner,subscriber
user_ids[ID!]! | The unique identifiers of the users to add to the workspace. | 
workspace_idID! | The workspace's unique identifier. | 

## Delete users from a workspace

The delete_users_from_workspace mutation allows you to delete users from a workspace via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_users_from_workspace (workspace_id: 1234567, user_ids: [12345678, 87654321, 01234567]) {
    id
  }
}
```

```
let query = 'mutation { delete_users_from_workspace (workspace_id: 1234567, user_ids: [12345678, 87654321, 01234567]) { id } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to remove from the workspace.

Arguments | Description
--- | ---
user_ids[ID!]! | The unique identifiers of the users to remove from the workspace.
workspace_idID! | The workspace's unique identifier.

## Add teams to a workspace

The add_teams_to_workspace mutation allows you to add teams to a workspace via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  add_teams_to_workspace (workspace_id: 1234567, team_ids: [12345678, 87654321, 01234567]) {
    id
  }
}
```

```
let query = 'mutation { add_teams_to_workspace (workspace_id: 1234567, team_ids: [12345678, 87654321, 01234567]) { id } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which teams to add to the workspace.

Arguments | Description | Enum values
--- | --- | ---
kindWorkspaceSubscriberTeam | The subscriber's role. | owner,subscriber
team_ids[ID!]! | The unique identifiers of the teams to add to the workspace. | 
workspace_idID! | The workspace's unique identifier. | 

## Delete teams from a workspace

The delete_teams_from_workspace mutation allows you to delete teams from a workspace via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_teams_from_workspace (workspace_id: 1234567, team_ids: [12345678, 87654321, 01234567]) {
    id
  }
}
```

```
let query = 'mutation { delete_teams_from_workspace (workspace_id: 1234567, team_ids: [12345678, 87654321, 01234567]) { id } }';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-01'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which teams to remove from the workspace.

Arguments | Description
--- | ---
team_ids[ID!]! | The unique identifiers of the teams to remove from the workspace.
workspace_idID! | The workspace's unique identifier.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
