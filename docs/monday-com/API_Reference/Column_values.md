---

title: Column_values
source: https://developer.monday.com/api-reference/reference/column-values-v2
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read column values on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Column values

Learn how to read column values on monday boards using the platform API

Every monday.com board has one or more columns , each holding a particular type of information. These column values make up the board's content, and their inner value structure varies based on their type.

You can query a column's values using the column_values endpoint. Our schema also contains types that extend the ColumnValue type. You can read more in the implementations section of this doc.

# Queries

- Returns an array containing metadata about one or a collection of columns
- Can only be nested within an items query

GraphQLJavaScript
```
query {
  items (ids: 1234567890) {
    column_values {
      column {
        title
      }
      id
      type
      value
    }
  }
}
```

```
let query = "query { items { column_values { column { title } id type value}}}";

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

You can use the following argument(s) to reduce the number of results returned in your column_values query.

Argument | Description
--- | ---
ids[String!] | The specific columns to return.
types[ColumnType!] | The specific type of columns to return.

## Fields

You can use the following field(s) to specify what information your column_values query will return.

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
idID! | The column's unique identifier.
textString | The text representation of the column's value. Not every column supports the text value.
typeColumnType! | The column's type.
valueJSON | The column's raw value.

# Implementations

Our schema also contains specific types for each column value, such as ButtonValue and StatusValue . These extend the core ColumnValue type, so you can query column-specific fields instead of parsing the column's raw JSON value.

Take the StatusValue type for example. On top of the 5 core fields , it also exposes the column , id , index , is_done , label , label_style , text , type , update_id , updated_at , and value fields specific to the StatusValue type.

## Using fragments to get column-specific fields

You can return subfields for a specific column type using GraphQL fragments , or queries that will only run if a specific type is returned. Fragments can help you selectively return column-specific data that doesn't exist on other columns on the board. Each column type has its own fields that are documented here .

### Example

Notice the ...on StatusValue expression, which will return the label and update_id only on status columns.

GraphQL
```
query {
  items (ids: 1234567890) {
    column_values {
      value
      type
      ... on StatusValue  { # will only run for status columns
        label
        update_id
      }
    }
  }
}
```
