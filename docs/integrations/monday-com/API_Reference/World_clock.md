---

title: World_clock
source: https://developer.monday.com/api-reference/reference/world-clock
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the world clock column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# World clock

Learn how to filter by, read, update, and clear the world clock column on monday boards using the platform API

The world clock column holds the current time of any place in the world. You can filter by , read , update , and clear the world clock column via the API.

## Filter by the world clock column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the world clock column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The name of the timezone (as shown in the UI)
not_any_of | The name of the timezone (as shown in the UI)

### Examples

The following example returns all items on the specified board with a world clock column value of Samoa.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "world_clock", compare_value: ["Samoa"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the world clock column

You can query the world clock column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the world clock column are of the WorldClockValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on WorldClockValue {
        text
        timezone
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
textString | The column's value as text. This field will return""if the column has an empty value.
timezoneString | The column's timezone.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the world clock column

You can update a world clock column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update a world clock column, send the time zone of the user as a string in continent/city form.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"world_clock\" : {\"timezone\" : \"Europe/London\"}}") {
    id
  }
}
```

```
fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY'
  },
  body: JSON.stringify({
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id }}",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: "{\"world_clock\" : {\"timezone\" : \"Europe/London\"}}"
    })
  })
})
```

## Clear the world clock column

You can also clear a world clock column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"world_clock\" : null}") {
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
      myColumnValues: "{\"world_clock\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
