---

title: Columns
source: https://developer.monday.com/api-reference/reference/columns
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read and update columns on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Columns

Learn how to read and update columns on monday boards using the platform API

monday.com boards are formatted as a table with columns and rows (items). Each column has specific functionality and only stores relevant data. For example, a numbers column will store numerical values, a text column will store text values, and a time tracking column will store only time-based data based on log events.

# Queries

Required scope: boards:read

- Returns an array containing metadata about one or a collection of columns
- Can only be nested within another query

GraphQLJavaScript
```
query {
  boards (ids: 1234567890) {
    columns {
      id
      title
    }		
  }
}
```

```
let query = "query {boards (ids: 1234567890) { columns { id title }}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YourSuperSecretApiKey'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your columns query.

Argument | Description
--- | ---
ids[String] | The specific columns to return. Please use quotation marks when passing this ID as a string.
types[ColumnType!] | The specific type of columns to return.

## Fields

You can use the following field(s) to specify what information your columns query will return.

Field | Field Description
--- | ---
archivedBoolean! | Returnstrueif the column is archived.
descriptionString | The column's description.
idID! | The column's unique identifier.
settings_strString! | The column's settings.
titleString! | The column's title.
typeColumnType! | The column's type.
widthInt | The column's width.

# Mutations

Required scope: boards:write

## Create a column

The create_column mutation allows you to create a new column on a board within the account via the API. You can also specify what fields to query back from the new column when you run the mutation.

GraphQLJavaScript
```
mutation{
  create_column(board_id: 1234567890, title:"Work Status", description: "This is my work status column", column_type:status) {
    id
    title
    description
  }
}
```

```
let query = "mutation { create_column(board_id: 1234567890, title:\"Work Status\", description: \"This is my work status column\", column_type:status){id title description}}"

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

You can use the following argument(s) to define the new column's characteristics.

Argument | Description
--- | ---
after_column_idID | The unique identifier of the column after which the new column will be created.
board_idID! | The unique identifier of the board where the new column should be created.
column_typeColumnType! | The type of column to create.
defaultsJSON | The new column's defaults.
descriptionString | The new column's description.
idString | The column's user-specified unique identifier. The mutation will fail if it does not meet any of the following requirements:- [1-20] characters in length (inclusive)- Only lowercase letters (a-z) and underscores (_)- Must be unique (no other column on the board can have the same ID)- Can't reuse column IDs, even if the column has been deleted from the board- Can't be null, blank, or an empty string
titleString! | The new column's title.

## Create a status or dropdown column with custom labels

The create_column mutation also allows you to create a new status or dropdown column with custom labels via the API. You can also specify what fields to query back from the new column when you run the mutation.

Status column

GraphQLJavaScript
```
mutation {
  create_column(
    board_id: 1234567890
    title: "Project domain"
    column_type: status
    description: "This column indicates the domain of each project."
    defaults: "{\"labels\":{\"1\": \"Information technology\", \"2\": \"Human resources\", \"3\": \"Customer service\", \"4\": \"Other\"}}"
  ) {
    id
  }
}
```

```
let query = "mutation { create_column(board_id: 1234567890, title:\"Project domain\", column_type:status, description: \"This column indicates the domain of each project.\", defaults: \"{\\\"labels\\\":{\\\"1\\\": \\\"Information technology\\\", \\\"2\\\": \\\"Human resources\\\", \\\"3\\\": \\\"Customer service\\\", \\\"4\\\": \\\"Other\\\"}}\"){id}}"

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

Dropdown column

GraphQLJavaScript
```
mutation {
  create_column(
    board_id: 1234567890
    title: "Keywords"
    column_type: dropdown
    description: "This column indicates which keywords to include in each project."
    defaults: "{\"settings\":{\"labels\":[{\"id\":1,\"name\":\"Technology\"}, {\"id\":2,\"name\":\"Marketing\"}, {\"id\":3,\"name\":\"Sales\"}]}}"
  ) {
    id
  }
}
```

```
let query = "mutation {create_column(board_id: 1234567890, title: \"Keywords\", column_type: dropdown, description: \"This column indicates which keywords to include in each project.\", defaults: \"{\\\"settings\\\":{\\\"labels\\\":[{\\\"id\\\":1,\\\"name\\\":\\\"Technology\\\"}, {\\\"id\\\":2,\\\"name\\\":\\\"Marketing\\\"}, {\\\"id\\\":3,\\\"name\\\":\\\"Sales\\\"}]}}\") {id}}"

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE’
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define the new column's characteristics.

Argument | Description
--- | ---
board_idID! | The unique identifier of the board where the new column should be created.
column_typeColumnType! | The type of column to create.
defaultsJSON | The new column's defaults.
descriptionString | The new column's description.
idString | The column's user-specified unique identifier. The mutation will fail if it does not meet any of the following requirements:- [1-20] characters in length (inclusive)- Only lowercase letters (a-z) and underscores (_)- Must be unique (no other column on the board can have the same ID)- Can't reuse column IDs, even if the column has been deleted from the board- Can't be null, blank, or an empty string
titleString! | The new column's title.

## Change a column value

The change_column_value mutation allows you to change the value of a column in a specific item (row) with a JSON value via the API. If you’re using JavaScript, you can use JSON.stringify() to convert a JSON object into a string. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  change_column_value (board_id: 1234567890, item_id: 9876543210, column_id: "email9", value: "{\"text\":\"
[email protected]
\",\"email\":\"
[email protected]
\"}") {
    id
  }
}
```

```
var query = "mutation { change_column_value (board_id: 1234567890, item_id: 9876543210, column_id: \"email9\", value: \"{\\\"text\\\":\\\"
[email protected]
\\\",\\\"email\\\":\\\"
[email protected]
\\\"}\") {id}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define which column to change and its new value.

Argument | Description
--- | ---
board_idID! | The unique identifier of the board that contains the column to change.
column_idString! | The column's unique identifier.
create_labels_if_missingBoolean | Creates status/dropdown labels if they are missing. Requires permission to change the board structure.
item_idID | The unique identifier of the item to change.
valueJSON! | The new value of the column in JSON format.

## Change a simple column value

The change_simple_column_value mutation allows you to change the value of a column in a specific item (row) with a string value via the API. Each column has a certain type, and different column types expect a different set of parameters to update their values. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (board_id: 1234567890, item_id: 9876543210, column_id: "status", value: "Working on it") {
    id
  }
}
```

```
var query = "mutation {change_simple_column_value (board_id: 1234567890, item_id: 9876543210, column_id: \"status\", value: \"Working on it\") {id}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': "mutation {change_simple_column_value (board_id: 1234567890, item_id: 9876543210, column_id: \"status\", value: \"Working on it\") {id}}"
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define which column to change and its new value.

Argument | Description
--- | ---
board_idID! | The unique identifier of the board that contains the column to change.
column_idString! | The column's unique identifier.
create_labels_if_missingBoolean | Creates status/dropdown labels if they are missing. Requires permission to change the board structure.
item_idID | The unique identifier of the item to change.
valueString | The new simple value of the column.

## Change multiple column values

The change_multiple_column_values mutation allows you to change multiple column values of a specific item (row) with a JSON value via the API. You can also specify what fields to query back when you run the mutation.

Each column has a certain type, and different column types expect a different set of parameters to update their values. When sending data in the column_values argument, use a string and build it using this sample form: {\"text\": \"New text\", \"status\": {\"label\": \"Done\"}}

## 👍Pro tip

You can also use simple ( String ) values in this mutation along with regular ( JSON ) values, or just simple values. Here's an example of setting a status with a simple value: {\"text\": \"New text\", \"status\": \"Done\"}

GraphQLJavaScript
```
mutation {
  change_multiple_column_values (item_id: 1234567890, board_id: 9876543210, column_values: "{\"status\": {\"index\": 1},\"date4\": {\"date\":\"2021-01-01\"}, \"person\" : {\"personsAndTeams\":[{\"id\":9603417,\"kind\":\"person\"}]}}") {
    id
  }
}
```

```
var query = "mutation {change_multiple_column_values (item_id: 1234567890, board_id: 9876543210, column_values: \"{\\\"status\\\": {\\\"index\\\": 1},\\\"date4\\\": {\\\"date\\\":\\\"2021-01-01\\\"}, \\\"person\\\" : {\\\"personsAndTeams\\\":[{\\\"id\\\":9603417,\\\"kind\\\":\\\"person\\\"}]}}\") {id}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define which columns to change and their new values.

Argument | Definition
--- | ---
board_idID! | The unique identifier of the board that contains the columns to change.
column_valuesJSON! | The updated column values.
create_labels_if_missingBoolean | Creates status/dropdown labels if they are missing. Requires permission to change the board structure.
item_idID | The unique identifier of the item to change.

## Change a column title

The change_column_title mutation allows you to change the title of an existing column via the API. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  change_column_title (board_id: 1234567890, column_id: "status", title: "new_status") {
    id
  }
}
```

```
var query = "mutation {change_column_title (board_id: 1234567890, column_id: \"status\", title: \"new_status\") {id}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define which column's title to change and its new value.

Argument | Definition
--- | ---
board_idID! | The unique identifier of the board that contains the column to change.
column_idString! | The column's unique identifier.
titleString! | The column's new title.

## Change column metadata

The change_column_metadata mutation allows you to update the metadata of an existing column. Currently, we support updating both the title and description. You can also specify what fields to query back when you run the mutation.

GraphQLJavaScript
```
mutation {
  change_column_metadata(board_id: 1234567890, column_id: "date4", column_property: description, value: "This is my awesome date column"){
    id
    title
    description
  }
}
```

```
var query = "mutation {change_column_metadata (board_id: 1234567890, column_id: \"date4\", column_property: description, value: \"This is my awesome date column\") {id}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

### Arguments

You can use the following argument(s) to define which column to change and its new value.

Argument | Definition | Enum values
--- | --- | ---
board_idID! | The unique identifier of the board that contains the column to change. | 
column_idString! | The column's unique identifier. | 
column_propertyColumnProperty | The property you want to change. | description,title
valueString | The new value of that property. | 

## Delete a column

The delete_column mutation allows you to delete a single column from a board via the API. You can also specify what fields to query back from the deleted column when you run the mutation.

GraphQLJavaScript
```
mutation {
  delete_column (board_id: 1234567890, column_id: "status") {
    id
  }
}
```

```
let query = 'mutation { delete_column(board_id: 1234567890, column_id: \"status\") { id }}';

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

You can use the following argument(s) to define which column to delete.

Argument | Description
--- | ---
board_idID! | The unique identifier of the board that contains the column to delete.
column_idString! | The column's unique identifier.
