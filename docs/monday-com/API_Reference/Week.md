---

title: Week
source: https://developer.monday.com/api-reference/reference/week
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the week column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Week

Learn how to filter by, read, update, and clear the week column on monday boards using the platform API

The week column contains the relative week(s) (from the current week) of the dates inputted. You can filter by , read , update , and clear the week column via the API.

## Filter by the week column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the week column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | "THIS_WEEK"(current week)"NEXT_WEEKS"(future weeks)"PAST_WEEKS"(past weeks)
not_any_of | "THIS_WEEK"(current week)"NEXT_WEEKS"(future weeks)"PAST_WEEKS"(past weeks)
is_empty | null
is_not_empty | null

### Examples

The following example returns all items on the specified board with a week column value of any week in the past.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "week", compare_value: ["past_weeks"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the week column

You can query the week column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the week column are of the WeekValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on WeekValue {
        start_date
        end_date
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
end_dateDate | The week's end date.
idID! | The column's unique identifier.
start_dateDate | The column's start date.
textString | The range of dates representing the week in YYYY-MM-DD format. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.

## Update the week column

You can update a week column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update a week column using JSON, send the start and end dates in a YYYY-MM-DD format. The dates must be 7 days apart (inclusive of the first and last date) and start at the beginning of the work week defined in the account settings.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"week\":{ \"week\": {\"startDate\" : \"2019-06-10\", \"endDate\" : \"2019-06-16\"}}}") {
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
      myColumnValues: "{\"week\" : {\"startDate\" : \"2019-06-10\", \"endDate\" : \"2019-06-16\"}}"
    })
  })
})
```

## Clear the week column

You can also clear a week column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"week\" : null}") {
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
      myColumnValues: "{\"week\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
