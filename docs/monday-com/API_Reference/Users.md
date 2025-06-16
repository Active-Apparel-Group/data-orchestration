---

title: Users
source: https://developer.monday.com/api-reference/reference/users
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, add, and delete monday users via the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Users

Learn how to read, add, and delete monday users via the platform API

Every monday.com user is part of an account or organization as an admin, team member, member, viewer, guest, subscriber, board owner, or in a custom role. Each user has a unique set of user details. This information is accessible via the API through the users endpoint.

# Queries

Required scope: users:read

- Returns an array containing metadata about one or multiple users
- Can be queried directly at the root or nested within a teams query to return users from a specific team

GraphQLAPI clientFetch
```
query {
  users (limit: 50) {
    created_at
    email
    account {
      name
      id
    }
  }
}
```

```
const GET_USERS = "query { users (limit: 50) { created_at email account { name id }}}";
const seamlessApiClient = new SeamlessApiClient("2025-04");

const response = await seamlessApiClient.request(GET_USERS)
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your users query.

Argument | Description | Enum values
--- | --- | ---
emails[String] | The specific user emails to return. | 
ids[ID!] | The unique identifier of the specific users to return. | 
kindUserKind | The kind of users you want to search by. | allguestsnon_guestsnon_pending
limitInt | The number of users to get. | 
nameString | A fuzzy search of users by name. | 
newest_firstBoolean | Lists the most recently created users at the top. | 
non_activeBoolean | Returns the account's non-active users. | 
pageInt | The page number to return. Starts at 1. | 

## Fields

You can use the following field(s) to specify what information your users query will return. Please note that some fields will have their own arguments or fields.

Field | Field description | Supported fields
--- | --- | ---
accountAccount! | The user's account. | 
birthdayDate | The user's date of birth. Returned asYYYY-MM-DD. | 
country_codeString | The user's country code. | 
created_atDate | The user's creation date. Returned asYYYY-MM-DD. | 
current_languageString | The user's language. | 
custom_field_metas[CustomFieldMetas] | The user profile custom fields metadata. | descriptionStringeditableBooleanfield_typeStringflaggedBooleaniconStringidStringpositionStringtitleString
custom_field_values[CustomFieldValue] | The user profile custom field values. | custom_field_meta_idStringvalueString
emailString! | The user's email. | 
enabledBoolean! | Returnstrueif the user is enabled. | 
idID! | The user's unique identifier. | 
is_adminBoolean | Returnstrueif the user is an admin. | 
is_guestBoolean | Returnstrueif the user is a guest. | 
is_pendingBoolean | Returnstrueif the user didn't confirm their email yet. | 
is_view_onlyBoolean | Returnstrueif the user is only a viewer. | 
is_verifiedBoolean | Returnstrueif the user verified their email. | 
join_dateDate | The date the user joined the account. Returned asYYYY-MM-DD. | 
last_activityDate | The last date and time the user was active. Returned asYYYY-MM-DDT00:00:00. | 
locationString | The user's location. | 
mobile_phoneString | The user's mobile phone number. | 
nameString! | The user's name. | 
out_of_officeOutOfOffice | The user's out-of-office status. | activeBooleandisable_notificationsBooleanend_dateDatestart_dateDatetypeString
phoneString | The user's phone number. | 
photo_originalString | Returns the URL of the user's uploaded photo in its original size. | 
photo_smallString | Returns the URL of the user's uploaded photo in a small size (150x150 px). | 
photo_thumbString | Returns the URL of the user's uploaded photo in thumbnail size (100x100 px). | 
photo_thumb_smallString | Returns the URL of the user's uploaded photo in a small thumbnail size (50x50 px). | 
photo_tinyString | Returns the URL of the user's uploaded photo in tiny size (30x30 px). | 
sign_up_product_kindString | The product the user first signed up to. | 
teams[Team] | The user's teams. | 
time_zone_identifierString | The user's timezone identifier. | 
titleString | The user's title. | 
urlString! | The user's profile URL. | 
utc_hours_diffInt | The user’s UTC hours difference. | 

# Mutations

## Add users to a board

Required scope: boards:write

This mutation adds users to a board. You can specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  add_users_to_board (board_id: 1234567890, user_ids: [123456, 234567, 345678], kind: owner) {
    id
  }
}
```

```
let query = "mutation { add_users_to_board (board_id:1234567890, user_ids: [123456, 234567, 345678], kind: owner) { id }}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to add to the board and their roles.

Argument | Description | Enum values
--- | --- | ---
board_idID! | The board's unique identifier. | 
kindBoardSubscriberKind | The user's role. | owner,subscriber
user_ids[ID!]! | The unique identifiers of the users to add to the board. | 

## Add users to a team

This mutation adds users to a team. It returns the ChangeTeamMembershipResult type which allows you to specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  add_users_to_team (team_id: 7654321, user_ids: [123456, 654321, 012345]) {
    successful_users {
      name
      email 
    }
    failed_users {
      name
      email
    }
  }
}
```

```
let query = "mutation { add_users_to_team (team_id:7654321, user_ids: [123456, 654321, 012345]) { successful_users { name email } failed_users { name email }}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to add to the team.

Argument | Description
--- | ---
team_idID! | The unique identifier of the team to add users to.
user_ids[ID!]! | The unique identifiers of the users to add to the team.

## Add users to a workspace

Required scope: workspaces:write

This mutation adds users to a workspace. You can specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  add_users_to_workspace (workspace_id: 1234567, user_ids: [123456, 654321, 012345], kind: subscriber) {
    id
  }
}
```

```
let query = "mutation { add_users_to_workspace (workspace_id: 1234567, user_ids: [123456, 654321, 012345], kind: subscriber) { id } }";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to add to the workspace and their roles.

Arguments | Description | Enum values
--- | --- | ---
kindWorkspaceSubscriberKind | The user's role. | owner,subscriber
user_ids[ID!]! | The unique identifiers of the users to add to the workspace. | 
workspace_idID! | The workspace's unique identifier. | 

## Activate users

This mutation activates or re-activates users in a monday.com account. It returns the ActivateUsersResult type which allows you to specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  activate_users (user_ids: [54321, 12345]) {
    activated_users {
     id
     name
     email
    }
    errors {
      user_id
      code
      message
    }
  }
}
```

```
let query = 'mutation { activate_users (user_ids: [54321, 12345]) { activated_users { id name email } errors { user_id code message }}}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

Argument | Description
--- | ---
user_ids[ID!]! | The unique identifiers of the users to activate. The maximum is 200.

## Invite users

This mutation invites users to join a monday.com account. They will be in a pending status until the invitation is accepted.

It returns the InviteUsersResult type which allows you to specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  invite_users (emails: ["
[email protected]
", "
[email protected]
"], product: crm, user_role: VIEW_ONLY) {
    errors { 
      message 
      code
      email 
    }
    invited_users {
      name
      id
    }
  }
}
```

```
let query = 'mutation { invite_users (input: ) { deactivated_users { id name }}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

Argument | Description | Enum values
--- | --- | ---
emails[String!]! | The emails of the users to invite. | 
productProduct | The product to invite the user to. | crmdevformsknowledgeservicewhiteboardworkflowswork_management
user_roleUserRole | The invited user's new role. | ADMINGUESTMEMBERVIEW_ONLY

## Update users' attributes

The update_multiple_users mutation updates one or multiple users' attributes. It returns the UpdateUserAttributesResult type which supports a set of fields you can query back.

GraphQL
```
mutation {
  update_multiple_users (
    user_updates: [
      { 
        user_id: 12345678, 
        user_attribute_updates: {birthday: "1985-06-01", email: "
[email protected]
"}
      },
      { 
        user_id: 87654321, 
        user_attribute_updates: {birthday: "1975-01-20", email: "
[email protected]
"}
      }
    ]
  ) {
    updated_users {
      name
      birthday
      email
      id
    }
    errors {
      message
      code
      user_id
    }
  }
}
```

### Arguments

Argument | Description | Supported fields
--- | --- | ---
user_updates[UserUpdateInput!]! | The unique identifiers and attributes to update. | user_attribute_updatesUserAttributesInput!user_idID!

## Update a user's email domain

This mutation updates a user's email domain. It returns the UpdateEmailDomainResult type which allows you to specify what fields to query back when you run it.

GraphQL
```
mutation {
  update_email_domain (input: {new_domain: "
[email protected]
", user_ids: [123456, 654321]}) {
    updated_users {
      name
      is_admin
    }
    errors {
      user_id
      code
      message
    }
  }
}
```

### Arguments

Argument | Description | Supported fields
--- | --- | ---
inputUpdateEmailDomainAttributesInput! | The attributes to update. | new_domainString!user_ids[ID!]!

## Update a user's role

This mutation updates a user's role (accepts both custom or default roles). It returns the UpdateUsersRoleResult type which allows you to specify what fields to query back when you run it.

Please keep the following in mind:

- You can't update yourself
- Maximum of 200 user IDs per mutation
- Only admins can use this mutation

Default roleCustom role
```
mutation {
  update_users_role (user_ids: [12345, 54321], new_role: ADMIN) {
    updated_users {
      name
      is_admin
    }
    errors {
      user_id
      code
      message
    }
  }
}
```

```
mutation {
  update_users_role (user_ids: [12345, 54321], role_id: "5") {
    updated_users {
      name
    }
    errors {
      user_id
      code
      message
    }
  }
}
```

### Arguments

Argument | Description | Enum values
--- | --- | ---
new_roleBaseRoleName | The user's updated role. Only used to update default roles, not custom ones (read morehere). | ADMINGUESTMEMBERVIEW_ONLY
role_idID | The custom role's unique identifier (found by queryingaccount_roles). Available only for enterprise customers in version2025-04. | 
user_ids[ID!]! | The unique identifiers of the users to update. The maximum is 200. | 

## Delete subscribers from a board

This mutation deletes subscribers from a board. You can also specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  delete_subscribers_from_board(board_id: 1234567890, user_ids: [12345678, 87654321, 01234567]) {
    id
  }
}
```

```
let query = 'mutation { delete_subscribers_from_board (board_id: 1234567890, user_ids: [12345678, 87654321, 01234567]) { id }}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which subscribers to delete from the board.

Argument | Description
--- | ---
board_idID! | The board's unique identifier.
user_ids[ID!]! | The unique identifiers of the users to unsubscribe from the board.

## Remove users from a team

This mutation removes users from a team. It returns the ChangeTeamMembershipResult type which allows you to specify what fields to query back when you run it.

GraphQLJavaScript
```
mutation {
  remove_users_from_team (team_id: 7654321, user_ids: [123456, 654321, 012345]) {
    successful_users {
      name
      email 
    }
    failed_users {
      name
      email
    }
  }
}
```

```
let query = "mutation { remove_users_from_team (team_id:7654321, user_ids: [123456, 654321, 012345]) { successful_users { name email } failed_users { name email }}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to remove from the team.

Argument | Description
--- | ---
team_idID! | The unique identifier of the team to remove users from.
user_ids[ID!]! | The unique identifiers of the users to remove from the team.

## Delete users from a workspace

Required scope: workspaces:write

This mutation deletes users from a workspace. You can also specify what fields to query back from the user when you run it.

GraphQLJavaScript
```
mutation {
  delete_users_from_workspace (workspace_id: 1234567, user_ids: [123456, 654321, 012345]) {
    id
  }
}
```

```
let query = "mutation { delete_users_from_workspace (workspace_id: 1234567, user_ids: [123456, 654321, 012345]) { id } }";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to specify which users to delete from the workspace.

Arguments | Description
--- | ---
user_ids[ID!]! | The unique identifiers of the users to remove from the workspace.
workspace_idID!! | The workspace's unique identifier.

## Deactivate users

This mutation deactivates users from a monday.com account. It returns the DeactivateUsersResult type which supports a set of fields that you can query back when you run it.

Please keep the following in mind:

- You can't deactivate yourself
- There's a maximum of 200 users per mutation
- Only admins can use this mutation
- Deactivating a user also deactivates the integrations and automations they've created. Read more about deactivating users here !

GraphQL
```
mutation {
  deactivate_users (user_ids: [54321, 12345]) {
    deactivated_users {
     id
     name
    }
    errors {
      message
      code
      user_id
    }
  }
}
```

### Arguments

Arguments | Description
--- | ---
user_ids[ID!]! | The unique identifiers of the users to deactivate. The maximum is 200.
