---

title: Email
source: https://developer.monday.com/api-reference/reference/email
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter, read, update, and clear the email column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Email

Learn how to filter, read, update, and clear the email column on monday boards using the platform API

The email column allows you to attach an email address to an item and send emails to that contact with a single click. You can filter , read , update , and clear the email column via the API.

## Filter the email column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the email column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | ""(blank values)The whole email or display text value to filter by*
not_any_of | ""(blank values)The whole email or display text value to filter by*
is_empty | null
is_not_empty | null
contains_text | The partial or whole email or display text value to filter by*
not_contains_text | The partial or whole email or display text value to filter by*

* Please note that you can use either the email or display text when using the any_of , not_any_of , contains_text , or not_contains_text operators, but it must match whatever is in the UI. For example, if the item just has an email without display text, you can search by email. If display text is present, you must search by that and not the email.

### Examples

The following example returns all items on the specified board without "@gmail" in their email address. Please note that if the column had display text values, the query would have to utilize those instead of the email value.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "email", compare_value: ["@gmail"], operator:not_contains_text}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the email column

You can query the email column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the email column are of the EmailValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on EmailValue {
        email
        updated_at
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
emailString | The column's email value.
idID! | The column's unique identifier.
labelString | The column's text value. Please note that this may be the same as theemailvalue if the user didn't enter any text.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the email column

You can update an email column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update an email column, send both the email address and display text as a string separated by a space. You can also include spaces in the display text. Both are required.

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"email", value: "
[email protected]
This is an example email") {
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
      columnId: "email",
      myColumnValue: "
[email protected]
This is an example email"
      })
    })
  })
```

### JSON

To update an email column with JSON, you should send the email address in the email key and display text in the text key. Both keys are required.

## 👍Pro tip

You can mix both string and JSON values in the change_multiple_column_values mutation.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values (item_id:9876543210, board_id:1234567890, column_values: "{\"my_email_column\":{\"email\":\"
[email protected]
\",\"text\":\"This is an example email\"}}") {
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
    query : `mutation ($myBoardId:Int!, $myItemId:Int!, $myColumnValues:JSON!) {
                 change_multiple_column_values(item_id:$myItemId, board_id:$myBoardId, column_values: $myColumnValues) {
                   id
                 }
               }`,
    variables : JSON.stringify({
      myBoardId: 1234567890,
      myItemId: 9876543210,
      myColumnValues: JSON.stringify({
        email : {email : "
[email protected]
","text":"This is an example email"}
      })
    })
  })
})
```

## Clear the email column

You have two options to clear an email column. First, you can use the change_multiple_column_values mutation and pass null , an empty string, or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"email\" : null}") {
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
      myColumnValues: "{\"email\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "email", value: "") {
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
      columnId: "email",
      myColumnValue: ""
      })
    })
  })
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
