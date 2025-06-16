---

title: Hour
source: https://developer.monday.com/api-reference/reference/hour
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the hour column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Hour

Learn how to filter by, read, update, and clear the hour column on monday boards using the platform API

The hour column contains a specific time entry for an item in HH:MM format. You can filter by , read , update , and clear the hour column via the API.

## Filter by the hour column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the hour column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | "Early morning""Morning""Afternoon""Evening""Night"
not_any_of | "Early morning""Morning""Afternoon""Evening""Night"
is_empty | null
is_not_empty | null

### Compare values

The hour column takes a set of predefined compare values to align with the filtering options in the UI. Please note that these times are based on the monday.com timezone configuration of the user making the API call.

- Early morning : 4:00 - 7:00 AM
- Morning : 7:00 AM - 12:00 PM
- Afternoon : 12:00 - 8:00 PM
- Evening : 8:00 - 11:00 PM
- Night : 11:00 PM - 4:00 AM

### Examples

The following example returns all items on the specified board with an hour column value in the afternoon.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "hour", compare_value: ["Afternoon"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the hour column

You can query the hour column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the hour column are of the HourValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on HourValue {
        minute
        hour
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
hourInt | The column's hour value.
idID! | The column's unique identifier.
minuteInt | The column's minute value.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the hour column

You can update an hour column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update an hour column, send the hour and minute in 24-hour format. Make sure you remove any leading zeroes from the data you send (i.e., send the number 9 instead of 09).

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"hour\" : {\"hour\" : 16, \"minute\" : 42}}") {
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
    query : "mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) { change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) { id } }",
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: "{\"hour\" : {\"hour\" : 16, \"minute\": 42}}"
    })
  })
})
```

## Clear the hour column

You can also clear an hour column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"hour\" : null}") {
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
      myColumnValues: "{\"hour\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
