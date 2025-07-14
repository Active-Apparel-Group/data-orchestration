---

title: Date
source: https://developer.monday.com/api-reference/reference/date
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter, read, update, and clear the date column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Date

Learn how to filter, read, update, and clear the date column on monday boards using the platform API

The date column represents a specific date (and potentially time). You can filter , read , update , and clear the date column via the API.

## Filter the date column

Using the items_page object, you can easily filter a board's items by specific columns or column values.

This section explains how to use the API to filter by dates. To query items with a specific date column value, you must add an operator with one or more predefined or custom compare values. Some compare values are static (e.g., specific dates), while others are dynamic and will change according to the date and time during which you make the API call (e.g., "TOMORROW").

💡 The results depend on the timezone, date format, and first day of the week settings configured in the monday.com profile of the user making the API call.

The table below outlines the supported operators, compare values, and compare attributes for the date column.

Compare value | Description | Operators
--- | --- | ---
"TODAY" | Items with today's date. | -any_of: returns items with today's date-not_any_of: returns items with a date that is not today-greater_than: returns items with any date after today's-greater_than_or_equals: returns items with today's date or later-lower_than: returns items with any date before today's-lower_than_or_equal: returns items with today's date or earlier
"TOMORROW" | Items with tomorrow's date. | -any_of: returns items with tomorrow's date-not_any_of: returns items with a date that is not tomorrow-greater_than: returns items with any date after tomorrow's-greater_than_or_equals: returns items with tomorrow's date or later-lower_than: returns items with any date before tomorrow's-lower_than_or_equal: returns items with tomorrow's date or earlier
"YESTERDAY" | Items with yesterday's date. | -any_of: returns items with yesterday's date-not_any_of: returns items with a date that is not yesterday-greater_than: returns items with any date after yesterday's-greater_than_or_equals: returns items with yesterday's date or later-lower_than: returns items with any date before yesterday's-lower_than_or_equal: returns items with yesterday's date or earlier
"THIS_WEEK" | Items with a date during the current week. Thefirst day of the week(either Sunday or Monday) is defined based on the settings configured in the monday.com account of the person making the API call. | -any_of: returns items with a date during the current week-not_any_of: returns items with a date that is not in the current week-greater_than: returns items with any date after this week-greater_than_or_equals: returns items with any date during or after the current week-lower_than: returns items with any date before this week-lower_than_or_equal: returns items with any date during or before the current week
"ONE_WEEK_AGO" | Items with a date during the previous week. Thefirst day of the week(either Sunday or Monday) is defined based on the settings configured in the monday.com account of the person making the API call. | -any_of: returns items with a date in the previous week-not_any_of: returns items with a date that is not in the previous week-greater_than: returns items with any date after the previous week-greater_than_or_equals: returns items with any date during or after the previous week-lower_than: returns items with any date before the previous week-lower_than_or_equal: returns items with any date during or before the previous week
"ONE_WEEK_FROM_NOW" | Items with a date during the upcoming week. Thefirst day of the week(either Sunday or Monday) is defined based on the settings configured in the monday.com account of the person making the API call. | -any_of: returns items with a date in the upcoming week-not_any_of: returns items with a date that is not in the upcoming week-greater_than: returns items with any date after the upcoming week-greater_than_or_equals: returns items with any date during or after the upcoming week-lower_than: returns items with any date before the upcoming week-lower_than_or_equal: returns items with any date during or before the upcoming week
"THIS_MONTH" | Items with a date during the current month. | -any_of: returns items with a date in the current month-not_any_of: returns items with a date that is not in the current month-greater_than: returns items with any date after the current month-greater_than_or_equals: returns items with any date during or after the current month-lower_than: returns items with any date before the current month-lower_than_or_equal: returns items with any date during or before the current month
"ONE_MONTH_AGO" | Items with a date during the previous month. | -any_of: returns items with a date in the previous month-not_any_of: returns items with a date that is not in the previous month-greater_than: returns items with any date after the previous month-greater_than_or_equals: returns items with any date during or after the previous month-lower_than: returns items with any date before the previous month-lower_than_or_equal: returns items with any date during or before the previous month
"ONE_MONTH_FROM_NOW" | Items with a date during the upcoming month. | -any_of: returns items with a date in the upcoming month-not_any_of: returns items with a date that is not in the upcoming month-greater_than: returns items with any date after the upcoming month-greater_than_or_equals: returns items with any date during or after the upcoming month-lower_than: returns items with any date before the upcoming month-lower_than_or_equal: returns items with any date during or before the upcoming month
"PAST_DATETIME" | Items with a date and time in the past. | -any_of: returns items with a date and time in the past-not_any_of: returns items with a date and time that is not in the past
"FUTURE_DATETIME" | Items with a date and time in the future. | -any_of: returns items with a date and time in the future-not_any_of: returns items with a date and time that is not in the future
"UPCOMING" | Used in conjunction with a status column, this compare value returns items that are not marked as "Done" and the date in the date column has not passed.Please notethat the item will not show as upcoming if today's date is in the date column. | -any_of: returns items not marked as "Done" before the date in the date column-not_any_of: returns items marked as "Done" before the date in the date column
"OVERDUE" | Used in conjunction with a status column, this compare value returns items that are not marked as "Done" and the date in the date column has passed.Please notethat the item will not show as overdue until the following day if the date column contains today's date. | -any_of: returns items not marked as "Done" after the date in the date column-not_any_of: returns items marked as "Done" after the date in the date column
"DONE_ON_TIME" | Used in conjunction with a status column, this compare value returns items that were marked as "Done" before the date in the date column. | -any_of: returns items that were completed before the date-not_any_of: returns items that were not completed before the date
"DONE_OVERDUE" | Used in conjunction with a status column, this compare value returns items that were marked as "Done" after the date in the date column. | -any_of: returns items that were completed after the date-not_any_of: returns items that were not completed after the date
Exact dates (e.g.,"2023-07-01" | You can return items with an exact/static date by sending the date as a string with the"EXACT"compare value. The dates must be in "YYYY-MM-DD" format.For example:["EXACT", "2023-07-01"] | -any_of: returns items with a specific date. Must be used in conjunction with the"EXACT"compare value.-not_any_of: returns items with any date besides the specified one. Must be used in conjunction with the"EXACT"compare value.-between: returns items between two specific dates-greater_than: returns items with any date after the specified date. Must be used in conjunction with the"EXACT"compare value.-greater_than_or_equals: returns items with any date during or after the upcoming week. Must be used in conjunction with the"EXACT"compare value.-lower_than: returns items with any date before the upcoming week. Must be used in conjunction with the"EXACT"compare value.-lower_than_or_equal: returns items with any date during or before the upcoming week. Must be used in conjunction with the"EXACT"compare value.
"EXACT" | Used with select operators to return items with a specific date. | 
"$$$blank$$$" | Items with a blank value. | -any_of: returns items with a blank value-not_any_of: returns items without a blank value

### Examples

This example returns all items on board 1234567890 with a date column value of July 1st, 2023 (based on the user making the API call). To return items with a specific date, just replace the "2023-07-01" with the date you'd like to filter by!

GraphQL
```
query {
  boards(ids: [1234567890]) {
    items_page(
      query_params: {rules: [ { 
        column_id: "date", 
        compare_value: ["EXACT", "2023-07-01"], 
        operator: any_of}]}
    ) {
      items {
        id
        name
      }
    }
  }
}
```

This example shows how to filter a date column with multiple compare values.

GraphQL
```
query {
  boards(ids: [1234567890]) {
    items_page(
      query_params: {rules: [ { 
        column_id: "date4", 
        compare_value: ["EXACT", "2024-09-10", "TODAY", "EXACT", "2024-09-11", "TOMORROW"], 
        operator: any_of}]}
    ) {
      items {
        id
        name
      }
    }
  }
}
```

This example returns all items on board 1234567890 with a date column value that is in the current week or after (based on the user making the API call).

GraphQL
```
query {
  boards(ids: [1234567890]) {
    items_page(
      query_params: {rules: [ { 
        column_id: "date", 
        compare_value: ["THIS_WEEK"], 
        operator: greater_than_or_equals}]}
    ) {
      items {
        id
        name
      }
    }
  }
}
```

This example returns all items on board 1234567890 that are not marked as "Done" in the status column and have a date column value that has not yet passed.

GraphQL
```
query {
  boards(ids: [1234567890]) {
    items_page(
      query_params: {rules: [ { 
        column_id: "date", 
        compare_value: ["UPCOMING"], 
        operator: any_of}]}
    ) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the date column

You can query the date column using the column_values object that object enables you to return column-specific subfields by sending a fragment in your query.  Values for the date column are of the DateValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on DateValue {
        time
        date
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
dateString | The column's date value.
iconString | The selected icon as a string.
idID! | The column's unique identifier.
textString | The column's value as text. This field will return""if the column has an empty value.
timeString | The column's time value. Results are based on the timezone settings configured in the monday.com profile of theuser who made the call.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value. Results are in UTC.

## Updating the date column

You can update a date column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update a date column, send the date as a string in a YYYY-MM-DD format. You can also add a time by passing it in HH:MM:SS format with a space between the date and time. (Make sure to enter the date and time in UTC, so it will be converted to the user's timezone when they look at the board!)

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"date", value: "2019-06-03 13:25:00") {
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
      columnId: "date",
      myColumnValue: "2019-06-03 13:25:00"
      })
    })
  })
```

### JSON

To update a date column with JSON, send a JSON string with a date and time key (optional). The date should also be in YYYY-MM-DD format, and the time in HH:MM:SS format. (Make sure to enter the date and time in UTC, so it will be converted to the user's timezone when they look at the board!)

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"date\" : {\"date\" : \"1993-08-27\", \"time\" : \"18:00:00\"}}") {
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
      myBoardId: YOUR_BOARD_ID,
      myItemId: YOUR_ITEM_ID,
      myColumnValues: "{\"date\" : {\"date\" : \"1993-08-27\", \"time\": \"18:00:00\"}}"
    })
  })
})
```

## Clear the date column

You have two options to clear a date column. First, you can use the change_multiple_column_values mutation and pass null , an empty string, or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"date\" : null}") {
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
      myColumnValues: "{\"date\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "date", value: "") {
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
      columnId: "date",
      myColumnValue: ""
      })
    })
  })
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
