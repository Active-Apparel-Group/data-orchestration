---

title: Link
source: https://developer.monday.com/api-reference/reference/link
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the link column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Link

Learn how to filter by, read, update, and clear the link column on monday boards using the platform API

The link column stores a link to a webpage. You can filter by , read , update , and clear the link column via the API.

## Filter by the link column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the link column's supported operators and compare values.

Operators | Compare value
--- | ---
any_of | ""(blank values)The whole URL or display text value to filter by*
not_any_of | ""(blank values)The whole URL or display text value to filter by*
is_empty | null
is_not_empty | null
contains_text | The partial or whole URL or display text value to filter by*
not_contains_text | The partial or whole URL or display text value to filter by*

* Please note that you can use either the URL or display text when using the any_of , not_any_of , contains_text , or not_contains_text operators, but it must match whatever is in the UI. For example, if the item just has a URL without display text, you can search by the URL. If display text is present, you must search by that and not the URL.

### Examples

The following example returns all items on the specified board with link column label that contains "Google".

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "link", compare_value: ["Google"], operator:contains_text}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the link column

You can query the link column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the link column are of the LinkValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on LinkValue {
        url
        url_text
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
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
urlString | The column's URL.
url_textString | The column's URL as text.
valueJSON | The column's JSON-formatted raw value.

## Update the link column

You can update a link column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update a link column, send the URL (including HTTP/HTTPS) and the display text separated with a space. You can include spaces in the display text.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"link", value: "http://monday.com go to monday!") {
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
      columnId: "link",
      myColumnValue: "http://monday.com go to monday!"
      })
    })
  })
```

### JSON

To update a link column, write the URL (including HTTP/HTTPS) in the URL key and the display text in the text key.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"link\" : {\"url\" : \"http://monday.com\", \"text\":\"go to monday!\"}}") {
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
      myColumnValues: "{\"link\" : {\"url\" : \"http://monday.com\", \"text\": \"go to monday!\"}}"
    })
  })
})
```

## Clear the link column

You have two options to clear a link column. First, you use the change_multiple_column_values mutation and pass null , an empty string, or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"link\" : null}") {
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
      myColumnValues: "{\"link\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "link", value: "") {
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
      columnId: "link",
      myColumnValue: ""
      })
    })
  })
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
