---

title: Teams
source: https://developer.monday.com/api-reference/reference/teams
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query monday team data using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Teams

Learn how to query monday team data using the platform API

Teams are the most efficient way to manage groups of users in monday.com. Teams are comprised of one or multiple users, and every user can be a part of multiple teams (or none).

# Queries

Required scope: teams:read

- Returns an array containing metadata about one or several teams
- Can be queried directly at the root or nested within a users query to return the teams a user is part of

GraphQLJavaScript
```
query {
  teams {
    name
    picture_url
    users {
      created_at
      phone
    }
  }
}
```

```
let query = "query { teams { name picture_url users { created_at phone } } }";

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

You can use the following argument(s) to reduce the number of results returned in your teams query.

Argument | Description
--- | ---
ids[ID!] | The unique identifiers of the specific teams to return.

## Fields

You can use the following field(s) to specify what information your teams query will return. Please note that some fields will have their own arguments.

Field | Description | Supported arguments
--- | --- | ---
idID! | The team's unique identifier. | 
nameString! | The team's name. | 
owners[User!]! | The users that are the team's owners. | ids[ID!]
picture_urlString | The team's picture URL. | 
users[User] | The team's users. | emails[String]ids[ID!]kindUserKindlimitIntnameStringnewest_firstBooleannon_activeBooleanpageInt

# Mutations

## Create team

Required scope: teams:write

The create_team mutation allows you to create a team via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  create_team (input: {name: "New team", is_guest_team:false, subscriber_ids: [1234567890, 9876543210]}, options: {allow_empty_team: false}) {
    id
  }
}
```

```
let query = 'mutation { create_team (input: {name: \"New team\", is_guest_team:false, subscriber_ids: [1234567890, 9876543210]}, options: {allow_empty_team: false}) { id } }';

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

You can use the following argument(s) to define the new team's characteristics.

Argument | Description | Supported fields
--- | --- | ---
inputCreateTeamAttributesInput! | The new team's attributes. | is_guest_teamBooleannameString!parent_team_idIDsubscriber_ids[ID!]
optionsCreateTeamOptionsInput | The options for creating a new team. | allow_empty_teamBoolean

## Add teams to a board

Required scope: boards:write

The add_teams_to_board mutation allows you to add teams to a board via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  add_teams_to_board (board_id: 1234567890, kind: owner, team_ids: [654321, 123456]) {
    id
  }
}
```

```
let query = 'mutation { add_teams_to_board (board_id: 1234567890, kind: owner, team_ids: [654321,123456]) { id } }';

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

You can use the following argument(s) to define which teams to add to the board.

Argument | Description | Enum values
--- | --- | ---
board_idID! | The board's unique identifier. | 
kindBoardSubscriberKind | The team's role. If the argument is not used, the team will be added as asubscriber. | ownersubscriber
team_ids[ID!]! | The unique identifiers of the teams to add to the board. You can pass-1to subscribe everyone in an account to the board (see morehere). | 

## Add users to a team

Required scope: teams:write

The add_users_to_team mutation allows you to add users to a team via the API. This mutation returns the ChangeTeamMembershipResult type which allows you to specify what fields to query back when you run the mutation.

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

## Add teams to a workspace

Required scope: workspaces:write

The add_teams_to_workspace mutation allows you to add teams to a workspace via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  add_teams_to_workspace (workspace_id: 1234567, kind: owner, team_ids: [123456, 654321, 012345]) {
    id
  }
}
```

```
let query = 'mutation { add_teams_to_workspace (workspace_id: 1234567, kind: owner, team_ids: [123456, 654321, 012345]) { id } }';

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

You can use the following argument(s) to define which teams to add to the workspace.

Arguments | Description | Enum values
--- | --- | ---
kindWorkspaceSubscriberKind | The team's role. | ownersubscriber
team_ids[ID!]! | The unique identifiers of the teams to add to the workspace. | 
workspace_idID! | The workspace's unique identifier. | 

## Assign team owners

This mutation allows you to assign owners to a team. It returns the AssignTeamOwnersResut type which supports a set of fields that you can query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  assign_team_owners (user_ids: [654321, 123456], team_id: 24681012) {
    errors {
      message
      code
      user_id
    }
    team {
      owners {
        id
      }
    }
  }
}
```

```
let query = 'mutation { assign_team_owners (user_ids: [654321, 123456], team_id: 24681012) { errors { message code user_id } team { owners { id }}}}';

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

You can use the following argument(s) to define which users to add as a team owner.

Argument | Description
--- | ---
team_idID! | The unique identifier of the team to remove owners to.
user_ids[ID!]! | The unique identifiers of the users to be assigned. Maximum of 200.

## Remove team owners

This mutation allows you to remove owners from a team. It returns the RemoveTeamOwnersResult type which supports a set of fields that you can query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  remove_team_owners (user_ids: [654321, 123456], team_id: 24681012) {
    errors {
      message
      code
      user_id
    }
    team {
      owners {
        id
      }
    }
  }
}
```

```
let query = 'mutation { remove_team_owners (user_ids: [654321, 123456], team_id: 24681012) { errors { message code user_id } team { owners { id }}}}';

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

You can use the following argument(s) to define which users to remove as a team owner.

Argument | Description
--- | ---
team_idID! | The unique identifier of the team to remove owners from.
user_ids[ID!]! | The unique identifiers of the users to be removed. The maximum is 200.

## Remove users from a team

Required scope: teams:write

The remove_users_from_team mutation allows you to remove users from a team. It returns the ChangeTeamMembershipResult type which supports a set of fields that you can query back when you run the mutation.

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

## Delete team

Required scope: teams:write

The delete_team mutation allows you to delete a team via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_team (team_id: 1234567890) {
    id
  }
}
```

```
let query = 'mutation { delete_team (team_id: 1234567890) { id } }';

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

You can use the following argument(s) to define which teams to delete.

Argument | Description
--- | ---
team_idID! | The unique identifier of the team to be deleted.

## Delete teams from a board

Required scope: boards:write

The delete_teams_from_board mutation allows you to delete teams from a board via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_teams_from_board (board_id: 1234567890, team_ids: [123456, 654321, 012345]) {
    id
  }
}
```

```
let query = 'mutation { delete_teams_from_board (board_id: 1234567890, team_ids: [123456, 654321, 012345]) { id } }';

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

You can use the following argument(s) to define which teams to delete from the board.

Arguments | Description
--- | ---
board_idID! | The board's unique identifier.
team_ids[ID!]! | The unique identifiers of the teams to delete from the board.

## Delete teams from a workspace

Required scope: workspaces:write

The delete_teams_from_workspace mutation allows you to delete teams from a workspace via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_teams_from_workspace (workspace_id: 1234567, team_ids: [123456, 654321, 012345]) {
    id
  }
}
```

```
let query = 'mutation { delete_teams_from_workspace (workspace_id: 1234567, team_ids: [123456, 654321, 012345]) { id } }';

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

You can use the following argument(s) to define which teams to delete from the workspace.

Arguments | Description
--- | ---
team_ids[ID!]! | The unique identifiers of the teams to delete from the workspace.
workspace_idID! | The workspace's unique identifier.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
