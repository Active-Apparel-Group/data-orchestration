---

title: Items_page_by_column_values
source: https://developer.monday.com/api-reference/reference/items-page-by-column-values
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read items on monday boards based on predefined column values using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Items page by column values

Learn how to read items on monday boards based on predefined column values using the platform API

Items are core objects in the monday.com platform that hold the actual data within the board. To better illustrate the platform, imagine that each board is a table and an item is a single row in that table. Now take one row, fill it with whatever information you'd like, and you now have an item!

# Queries

Required scope: boards:read

Querying items_page_by_column_values will search for items based on predefined column values and return metadata about these specific items. This method accepts various arguments and returns an array.

You can only query items_page_by_column_values directly at the root, so it can't be nested within another query. This object supports specific column types, while some only have limited support. The supported and unsupported section below outlines the support for each column and which values to send for each.

The items_page_by_column_values object allows you to combine multiple column values by sending an array. Unless specified otherwise, most column values will be used with an ANY_OF operator and only return items with all of the specified column values.

The following code sample returns 50 items from board 1234567890 that have a text column value of "This is a text column" AND a country column value of either the United States or Israel.

GraphQLJavaScript
```
query {
  items_page_by_column_values (limit: 50, board_id: 1234567890, columns: [{column_id: "text", column_values: ["This is a text column"]}, {column_id: "country", column_values: ["US", "IL"]}]) {
    cursor
    items {
      id
      name
    }
  }
}
```

```
let query = "query { items_page_by_column_values (limit: 50, board_id: 1234567890, columns: [{column_id: \"text\", column_values: [\"This is a text column\"]}, {column_id: \"country\", column_values: [\"US\", \"IL\"]}]) { cursor items { id name }}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-version' : '2023-10'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

The query will also return a cursor value that represents the position in the data set after returning 50 items. You can then use that string value to return the next 50 relevant items in the data set using the next_items_page object. After returning the next cursor value, you can continue the process to paginate through the entire data set.

GraphQLJavaScript
```
query {
  next_items_page (cursor: "MSw5NzI4MDA5MDAsaV9YcmxJb0p1VEdYc1VWeGlxeF9kLDg4MiwzNXw0MTQ1NzU1MTE5", limit: 50) {
    cursor
    items {
      id
      name
    }
  }
}
```

```
let query = "query { next_items_page (cursor: \"MSw5NzI4MDA5MDAsaV9YcmxJb0p1VEdYc1VWeGlxeF9kLDg4MiwzNXw0MTQ1NzU1MTE5\", limit: 50) { cursor items { id name }}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE',
    'API-version' : '2023-10'
   },
   body: JSON.stringify({
     query : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your items_page_by_column_values query. Unlike other queries, some arguments are required.

Argument | Description | Supported fields
--- | --- | ---
board_idID! | The specific board ID to return items for. | 
columns[ItemsPageByColumnValuesQuery!] | One or more columns and their values to search by.Please notethat you can't usecolumnsandcursorin the same request. We recommend usingcolumnsfor the initial request andcursorfor paginated requests. | column_idString!column_values[String]!
cursorString | An opaque token representing the position in the result set from which to resume fetching items. Use this to paginate through large result sets.Please notethat you can't usecolumnsandcursorin the same request. We recommend usingcolumnsfor the initial request andcursorfor paginated requests. | 
limitInt! | The number of items to return. The default is 25, but the maximum is 500. | 

## Fields

You can use the following field(s) to specify what information your items_page_by_column_values query will return. Please note that some fields will have their own arguments.

Field | Description
--- | ---
cursorString | An opaque cursor that represents the position in the list after the last returned item. When paginating through items, use this cursor to fetch the next set of items. There are no more items to fetch if the cursor isnull.
items[Item!]! | The items associated with the cursor.

## Supported and unsupported columns

### Supported columns

The following columns are supported by items_page_by_column_values queries. Unless specified otherwise below, most columns accept either "" or null value to return items with empty column values.

Column type | Notes
--- | ---
Checkbox | Pass true (e.g.["1", "t", "true"]) or false (e.g.["false", "f", null]value as a string. If you pass multiple values in the query, it will only return results based on thelastvalue.For example:column_id: "check", column_values: ["1", "false", "f", "t"]would return true values only.
Country | Pass the full name of the country as it appears in the UI as a string. You can also use the uppercase country code.For example:{column_id: "country", column_values: [null, "United States", "IL"]}
Date | Pass justonestring value in ISO-2 format (YYYY-MM-DD) with or without the hour, but please note that querying by the hour is not supported.For example:{column_id: "date", column_values: ["2023-08-01"]}
Dropdown | Pass justonepartial or whole string value to match the dropdown label.For example:{column_id: "dropdown", column_values: ["y Labe"]}or{column_id: "dropdown", column_values: ["My Label"]}
Email | Pass the display text (label) values as strings. Please note that this column performs an exact match of theentirelabel textual value.For example:{column_id: "email", column_values: ["[email protected]", "[email protected]", null]}or{column_id: "email", column_values: ["Home email", "Work email", ""]}
Hour | Pass the 24-hour value with or without the colon or one of these predefined values as a string:MORNING(6:00-12:00)AFTERNOON(12:00-16:00)EVENING(16:00-20:00)NIGHT(20:00-6:00)Please note that specifying an exact hour is only used to match the time to one of the predefined values. Itwill notreturn just the results with that specific value.For example:{column_id: "hour", column_values: ["12:30", "EVENING", "0500", null]}(returns all items in the afternoon, evening, or morning time ranges or those with empty values)
Link | Pass either the link or label value as it appears in the UI as a string. If there is both a link and label, use the label value.For example:{column_id: "link", column_values: ["https://www.google.com", "Link 1"}
Long Text | Pass the entire text value as a string. This column searches for an exact match of the entire text value.For example:{column_id: "long_text", column_values: ["", "This is the entire value of a long text column. :)"]}
Numbers | Pass the number value as a string.For example:{column_id: "numbers", column_values: ["", "-42"]}
People | Pass a user's display name or user ID as a string.For example:{column_id: "people", column_values: ["565481", "Test user", null]}
Phone | Pass an array of country names or codes as strings to return all of the properly formatted numbers corresponding to each country. You can also passonefull or partial number without any characters to return all items that contain the provided value.For example:{column_id: "phone", column_values: ["US", null, "Israel"]}or{column_id: "phone", column_values: ["665"]}(returns all items containing a phone number with 665)
Status | Pass the label text value as seen in the UI as a string.For example:{column_id: "status", column_values: ["Done", "Working on it", null]}
Text | Pass the entire text value as a string. This column searches for a case-insensitive match of theentiretext value.For example:{column_id: "text", column_values: ["This is a text column.", null]}
Timeline | Pass justonestring value in ISO-2 format (YYYY-MM-DD) to return an exact match for the timeline's start date.For example:{column_id: "timeline", column_values: ["2023-07-01"]}or{column_id: "timeline", column_values: [""]}
World Clock | Pass the label value as it appears in the UI as a string.For example:{column_id: "world_clock", column_values: ["", "Central"]}

### Unsupported columns

The following columns are not supported by items_page_by_column_values queries. If you query an unsupported column, you will receive an error.

- Auto number
- Color picker
- Connect boards
- Creation log
- File
- Formula
- Item ID
- Last updated
- Location
- Mirror
- Rating
- Tags
- Time tracking
- Vote

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
