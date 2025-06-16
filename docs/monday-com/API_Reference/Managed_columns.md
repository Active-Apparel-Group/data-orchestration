---

title: Managed_columns
source: https://developer.monday.com/api-reference/reference/managed-columns
author:
  - Monday
published:
created: 2025-05-25
description: 🚧 Only available in API versions 2025-07 and later Managed columns are useful tools to standardize workflows across your monday.com account. Select users can create, own, and manage status and dropdown columns with predefined labels that can't be edited by other members. This ensures consistent ter...
tags: [code, api, monday-dot-com]
summary:

---

# Managed columns

  🚧 Only available in API versions 2025-07 and later

Managed columns are useful tools to standardize workflows across your monday.com account. Select users can create, own, and manage status and dropdown columns with predefined labels that can't be edited by other members. This ensures consistent terminology across different workflows and helps align teams on a unified structure.

Users with managed column permissions can read, create, activate, update, deactivate, and deleted managed columns via the API.

# Queries

- Returns an array containing metadata about one or several managed columns
- Can only be queried directly at the root

GraphQLJavaScript
```
query {
  managed_column (state: active) {
    created_by
    revision
    settings {
      ...on StatusColumnSettings { 
        type
        labels {
          id
          description
        }
      }
    }
  }
}
```

```
let query = 'query { managed_column(state: active) { created_by revision settings { ...on StatusColumnSettings { type labels { id description } } } } }';

fetch("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'YOUR_API_KEY_HERE',
    'API-Version': '2025-07'
  },
  body: JSON.stringify({
    query: query
  })
})
.then(res => res.json())
.then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your managed_column query.

Argument | Description | Enum values
--- | --- | ---
id[String!] | The unique identifier of the managed column to filter by. | 
state[ManagedColumnState!] | The state of the managed column to filter by. | activeinactive

## Fields

You can use the following field(s) to specify what information your managed_columns query will return.

Field | Description | Possible types
--- | --- | ---
created_atDate | The managed column's creation date. | 
created_byID | The unique identifier of the user who created the managed column. | 
descriptionString | The managed column's description. | 
idString | The unique identifier of the managed column. | 
revisionInt | The current version of the managed column. | 
settingsColumnSettings | The managed column's settings. | DropdownColumnSettings,StatusColumnSettings
settings_jsonJSON | The managed column's settings in JSON. | 
stateManagedColumnState | The managed column's state:activeorinactive. | 
titleString | The managed column's title. | 
updated_atDate | The managed column's last updated date. | 
updated_byID | The unique identifier of the user who last updated the managed column. | 

# Mutations

## Create a managed status column

This mutation creates a new managed status column via the API. You can also specify a set of fields to return metadata about the new column.

GraphQLJavaScript
```
mutation {
  create_status_managed_column (
    title: "Project status"
    description:"This column indicates the project's status."
    settings: {
      labels: [
        {
          color: done_green
          label: "Done"
          index: 1
          is_done: true
        },
        {			
          color: working_orange
          label: "In progress"
          index: 2
        },
        {			
          color: stuck_red
          label: "Stuck"
          index: 3
        }
      ]
    }
  ) {
    id
    state
    created_at
    created_by
  }
}
```

```
let query = 'mutation { create_status_managed_column ( title: "Project status", description: "This column indicates the project\'s status.", settings: { labels: [ { color: done_green, label: "Done", index: 1, is_done: true }, { color: working_orange, label: "In progress", index: 2 }, { color: stuck_red, label: "Stuck", index: 3 } ] } ) { id state created_at created_by } }';

fetch("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'YOUR_API_KEY_HERE',
    'API-Version': '2025-07'
  },
  body: JSON.stringify({
    'query': query
  })
})
.then(res => res.json())
.then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following arguments to define the new managed dropdown column's properties.

Argument | Description | Supported fields
--- | --- | ---
descriptionString | The description of the new managed dropdown column. | 
settingsCreateStatusColumnSettingsInput | The settings of the new managed dropdown column. | labels[CreateStatusLabelInput!]!
titleString! | The title of the new managed dropdown column. | 

## Create a managed dropdown column

This mutation creates a new managed dropdown column via the API. You can also specify a set of fields to return metadata about the new column.

GraphQLJavaScript
```
mutation {
  create_dropdown_managed_column(
    title: "Project Domains"
    description: "This column lists all of the domains the project falls under."
    settings: {
      labels: [
        {
          label: "Research and Development" 
        }, 
        { 
          label: "Human Resources" 
        }, 
        {
          label: "Customer Support"
        }
      ]
    }
  ) {
    id
    title
    state
    created_at
    created_by
    settings {
      labels {
        id
        label
        is_deactivated
      }
    }
  }
}
```

```
let query = 'mutation { create_dropdown_managed_column( title: "Project Domains", description: "This column lists all of the domains the project falls under.", settings: { labels: [ { label: "Research and Development" }, { label: "Human Resources" }, { label: "Customer Support" } ] } ) { id title state created_at created_by settings { labels { id label is_deactivated } } } }';

fetch("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'YOUR_API_KEY_HERE',
    'API-Version': '2025-07'
  },
  body: JSON.stringify({ query })
})
.then(res => res.json())
.then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following arguments to define the new managed dropdown column's properties.

Argument | Description | Supported fields
--- | --- | ---
descriptionString | The description of the new managed dropdown column. | 
settingsCreateDropdownColumnSettingsInput | The settings of the new managed dropdown column. | labels[CreateDropdownLabelInput!]!
titleString! | The title of the new managed dropdown column. | 

## Activate managed column

This mutation activates a managed column via the API. You can also specify a set of fields to return metadata about the activated column.

GraphQLJavaScript
```
mutation {
  activate_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce") {
    status
    title
  }
}
```

```
let query = 'mutation { activate_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce") { state title } }';

fetch ("https://api.monday.com/v2", {
	method: 'post',
	headers: {
		'Content-Type': 'application/json',
		'Authorization' : 'YOUR_API_KEY_HERE', 
    'API-Version' : '2025-07`
	},
	body: JSON.stringify({
		'query' : query
	})
})
 .then(res => res.json())
 .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument to specify which managed column to activate.

Argument | Description
--- | ---
idString! | The unique identifier of the managed column to activate.

## Update status managed column

This mutation updates a managed status column via the API. You can also specify a set of fields to return metadata about the updated column.

  🚧 You must provide all of the column’s labels—even if you’re only updating one of them.

GraphQLJavaScript
```
mutation {
  update_status_managed_column (
    id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce"
    revision: 0
    title: "Project status"
    description:"This column indicates the status of the project."
    settings: {
      labels: [
        {
          color: bright_blue
          label: "In progress"
          index: 2
        }
      ]
    }
) {
  id
  description
  updated_at
  settings {
    labels {
      color
    }
  }
}
```

```
let query = 'mutation { update_status_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce", revision: 0, title: "Project status", description: "This column indicates the status of the project.", settings: { labels: [{ color: bright_blue, label: "In progress", index: 2 }] }) { id description updated_at created_by settings { labels { color } } } }';

fetch("https://api.monday.com/v2", {
	method: 'post',
	headers: {
		'Content-Type': 'application/json',
		'Authorization': 'YOUR_API_KEY_HERE',
		'API-Version': '2025-07'
	},
	body: JSON.stringify({
		'query': query
	})
})
.then(res => res.json())
.then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following arguments to specify the updated managed status column's properties.

Argument | Description | Supported fields
--- | --- | ---
descriptionString | The managed status column's new description. | 
idString! | The unique identifier of the managed status column to update. | 
revisionInt! | The current version of the managed column. Must be provided when updating the column to ensure your data is up to date. If you receive a revision error, the revision may be outdated — fetch the latest column data and try again. | 
settingsUpdateStatusColumnSettingsInput | The managed status column's settings to update. | labels[UpdateStatusLabelInput!]!
titleString | The managed status column's new title. | 

## Update dropdown managed column

This mutation updates a managed dropdown column via the API. You can also specify a set of fields to return metadata about the updated column.

  🚧 You must provide all of the column’s labels—even if you’re only updating one of them.

GraphQLJavaScript
```
mutation {  
  update_dropdown_managed_column (
    id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce"
    revision: 0
    title: "Project Domains"
    description: "This column tracks each domain a project falls under."
    settings: {
      labels: [
        {
          id: 1
          label: "Research & Development"
        }
      ]
    }
  ) {
    description
    updated_at
    revision
    state
  }
}
```

```
let query = 'mutation { update_dropdown_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce", revision: 0, title: "Project Domains", description: "This column tracks each domain a project falls under.", settings: { labels: [{ id: 1, label: "Research & Development" }] }) { description updated_at revision state } }';

fetch("https://api.monday.com/v2", {
	method: 'post',
	headers: {
		'Content-Type': 'application/json',
		'Authorization' : 'YOUR_API_KEY_HERE', 
    'API-Version' : '2025-07'
	},
	body: JSON.stringify({
		'query' : query
	})
})
.then(res => res.json())
.then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following arguments to specify the updated managed dropdown column's properties.

Argument | Description | Supported fields
--- | --- | ---
descriptionString | The managed dropdown column's updated description. | 
idString! | The unique identifier of the managed dropdown column to update. | 
revisionInt! | The current version of the managed column. Must be provided when updating the column to ensure your data is up to date. If you receive a revision error, the revision may be outdated — fetch the latest column data and try again. | 
settingsUpdateDropdownColumnSettingsInput | The managed dropdown column's settings to update. | labels[UpdateDropdownLabelInput!]!
titleString | The managed dropdown column's updated title. | 

## Deactivate managed column

This mutation deactivates a managed column via the API. You can also specify a set of fields to return metadata about the deactivated column.

Deactivating a managed column prevents users from adding it to new boards. The column remains on existing boards and can be reactivated at any time using the activate_managed_column mutation or through the UI.

GraphQLJavaScript
```
mutation {
  deactivate_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce") {
    state
    title
  }
}
```

```
let query = 'mutation { deactivate_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce") { state title } }';

fetch ("https://api.monday.com/v2", {
	method: 'post',
	headers: {
		'Content-Type': 'application/json',
		'Authorization' : 'YOUR_API_KEY_HERE', 
    'API-Version' : '2025-07`
	},
	body: JSON.stringify({
		'query' : query
	})
})
 .then(res => res.json())
 .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument to specify which managed column to deactivate.

Argument | Description
--- | ---
idString! | The unique identifier of the managed column to deactivate.

## Delete managed column

This mutation deletes a managed column via the API. You can also specify a set of fields to return metadata about the deleted column.

Deleting a managed column removes it from the Managed Column list in the Column Center and prevents users from adding it to new boards. The deleted column will remain on existing boards as a normal column, but it cannot be reactivated as a managed column.

GraphQLJavaScript
```
mutation {
  delete_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce") {
    state
    title
  }
}
```

```
let query = 'mutation { delete_managed_column (id: "f01e5115-fe6c-3861-8daa-4a1bcce2c2ce") { state title } }';

fetch ("https://api.monday.com/v2", {
	method: 'post',
	headers: {
		'Content-Type': 'application/json',
		'Authorization' : 'YOUR_API_KEY_HERE',
    'API-Version' : '2025-07`
	},
	body: JSON.stringify({
		'query' : query
	})
})
 .then(res => res.json())
 .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument to specify which managed column to delete.

Argument | Description
--- | ---
idString! | The unique identifier of the managed column to delete.
