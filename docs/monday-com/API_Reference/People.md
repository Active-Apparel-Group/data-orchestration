---

title: People
source: https://developer.monday.com/api-reference/reference/people
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the people column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# People

Learn how to filter by, read, update, and clear the people column on monday boards using the platform API

The people column represents a person(s) who is assigned items. You can filter by , read , update , and clear the people column via the API.

## Filter by the people column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the people column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The user IDs to filter by ("person-123456")"assigned_to_me"(items assigned to the user making the API call)"person-0"(blank values)
not_any_of | The user IDs to filter by ("person-123456")"assigned_to_me"(items assigned to the user making the API call)"person-0"(blank values)
is_empty | null
is_not_empty | null
contains_text | The partial or whole name to filter by (exactly as written)
not_contains_text | The partial or whole name to filter by (exactly as written)
contains_terms | The partial or whole name to filter by (in any order)
starts_with | The value the item starts with
ends_with | The value the item ends with

### Examples

The following example returns all items on the specified board assigned to anyone except the user running the query.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "people", compare_value: ["assigned_to_me"], operator:not_any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the people column

You can query the people column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the people column are of the PeopleValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on PeopleValue {
        persons_and_teams
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
idID! | The column's unique identifier.
persons_and_teams[PeopleEntity!] | The column's people or team values.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the people column

You can update a people column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update a people column, send a string of user IDs separated by a comma that you want to add to the column.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id:"people", value:"123456, 654321") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValue: String!, $columnId: String!) { change_simple_column_value (item_id:$myItemId, board_id:$myBoardId, column_id: $columnId, value: $myColumnValue) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      columnId: "people",
      myColumnValue: "123456, 654321"
      })
    })
  })
```

### JSON

To update a people column, send an array with the people or team IDs you want to add to the column.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"people\" : {\"personsAndTeams\":[{\"id\":\"4616627\",\"kind\":\"person\"},{\"id\":\"4616666\",\"kind\":\"person\"},{\"id\":\"51166\",\"kind\":\"team\"}]}}") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id }}",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues:"{\"people\": {\"personAndTeams\": [{\"id\": \"4616627\", \"kind\": \"person\"}, {\"id\": \"4616666\", \"kind\": \"person\"}, {\"id\": \"51166\", \"kind\": \"team\"}]}}"
    })
  })
})
```

## Clear the people column

You have two options to clear a people column. First, you can use the change_multiple_column_values mutation and pass null , an empty string, or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"people\" : null}") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: "{\"people\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "people", value: "") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValue: String!, $columnId: String!) { change_simple_column_value (item_id:$myItemId, board_id:$myBoardId, column_id: $columnId, value: $myColumnValue) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      columnId: "phone",
      myColumnValue: ""
      })
    })
  })
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
