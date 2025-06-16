---

title: Timeline
source: https://developer.monday.com/api-reference/reference/timeline
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the timeline column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Timeline

Learn how to filter by, read, update, and clear the timeline column on monday boards using the platform API

The timeline column contains a range of dates. This is useful should your item(s) require more than a single date to be stored. You can filter by , read , update , and clear the timeline column via the API.

## Filter by the timeline column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the timeline column's supported operators, compare values, and compare attributes.

Operators | Compare values | Compare attributes
--- | --- | ---
any_of | "CURRENT","DUE_TODAY","FUTURE_TIMELINE","PAST_TIMELINE","DONE_ON_TIME","OVERDUE","DONE_OVERDUE","MILESTONE","$$$blank$$$" | 
not_any_of | "CURRENT","DUE_TODAY","FUTURE_TIMELINE","PAST_TIMELINE","DONE_ON_TIME","OVERDUE","DONE_OVERDUE","MILESTONE","$$$blank$$$" | 
is_empty | null | 
is_not_empty | null | 
greater_than | "TODAY","TOMORROW","YESTERDAY","THIS_WEEK","ONE_WEEK_AGO","ONE_WEEK_FROM_NOW","THIS_MONTH","ONE_MONTH_AGO","ONE_MONTH_FROM_NOW","PAST_DATETIME","FUTURE_DATETIME","UPCOMING","OVERDUE","DONE_ON_TIME","DONE_OVERDUE","EXACT" | "START_DATE","END_DATE"
greater_than_or_equals | "TODAY","TOMORROW","YESTERDAY","THIS_WEEK","ONE_WEEK_AGO","ONE_WEEK_FROM_NOW","THIS_MONTH","ONE_MONTH_AGO","ONE_MONTH_FROM_NOW","PAST_DATETIME","FUTURE_DATETIME","UPCOMING","OVERDUE","DONE_ON_TIME","DONE_OVERDUE","EXACT" | "START_DATE","END_DATE"
lower_than | "TODAY","TOMORROW","YESTERDAY","THIS_WEEK","ONE_WEEK_AGO","ONE_WEEK_FROM_NOW","THIS_MONTH","ONE_MONTH_AGO","ONE_MONTH_FROM_NOW","PAST_DATETIME","FUTURE_DATETIME","UPCOMING","OVERDUE","DONE_ON_TIME","DONE_OVERDUE","EXACT" | "START_DATE","END_DATE"
lower_than_or_equal | "TODAY","TOMORROW","YESTERDAY","THIS_WEEK","ONE_WEEK_AGO","ONE_WEEK_FROM_NOW","THIS_MONTH","ONE_MONTH_AGO","ONE_MONTH_FROM_NOW","PAST_DATETIME","FUTURE_DATETIME","UPCOMING","OVERDUE","DONE_ON_TIME","DONE_OVERDUE","EXACT" | "START_DATE","END_DATE"
between | "TODAY","TOMORROW","YESTERDAY","THIS_WEEK","ONE_WEEK_AGO","ONE_WEEK_FROM_NOW","THIS_MONTH","ONE_MONTH_AGO","ONE_MONTH_FROM_NOW","PAST_DATETIME","FUTURE_DATETIME","UPCOMING","OVERDUE","DONE_ON_TIME","DONE_OVERDUE","EXACT" | "START_DATE","END_DATE"

### Examples

The following example returns all items on the specified board with a timeline column end date of the current week, or later.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "timeline", compare_value:"THIS_WEEK" , compare_attribute: "END_DATE", operator:greater_than_or_equals}]}) {
      items {
        id
      }
    }
  }
}
```

The following examples returns all items on the specified board with a timeline column start date of March 1st, 2024, or earlier.

GraphQL
```
query { 
  boards(ids: 1234567890) { 
    items_page (query_params: {rules: [{column_id: "timeline", compare_value: ["EXACT","2024-03-01"], compare_attribute: "START_DATE", operator: lower_than_or_equal}]}) { 
      items { 
        id 
      } 
    } 
  } 
}
```

## Read the timeline column

You can query the timeline column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the timeline column are of the TimelineValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on TimelineValue {
        from
        to
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
fromDate | The timeline's start date.
idID! | The column's unique identifier.
textString | The timeline's date range in YYYY-MM-DD format. This field will return""if the column has an empty value.
toDate | The timeline's end date.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.
visualization_stringString | The timeline's visualization type.

## Update the timeline column

You can update a timeline column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update a timeline column using JSON, send the start and end dates in a YYYY-MM-DD format. The start date is “from” and the end date is “to”.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"timeline\" : {\"from\" : \"2019-06-03\", \"to\" : \"2019-06-07\"}}") {
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
      myColumnValues: "{\"timeline\" : {\"from\" : \"2019-06-03\", \"to\": \"2019-06-07\"}}"
    })
  })
})
```

## Clear the timeline column

You can also clear a timeline column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"timeline\" : null}") {
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
      myColumnValues: "{\"timeline\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
