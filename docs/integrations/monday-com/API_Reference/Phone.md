---

title: Phone
source: https://developer.monday.com/api-reference/reference/phone
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the phone column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Phone

Learn how to filter by, read, update, and clear the phone column on monday boards using the platform API

The phone column stores a phone number with a relevant country code. You can filter by , read , update , and clear the phone column via the API.

## Filter by the phone column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the phone column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The country'stwo-letter abbreviationas a string
not_any_of | The country'stwo-letter abbreviationas a string
is_empty | null
is_not_empty | null
contains_text | The partial or whole phone number value as a string
not_contains_text | The partial or whole phone number value as a string

### Examples

The following example returns all items on the specified board with a phone column value in the United States.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "phone", compare_value: ["US"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the phone column

You can query the phone column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the phone column are of the PhoneValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on PhoneValue {
        country_short_name
        phone
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
country_short_nameString | The column's ISO-2 country code value.
idID! | The column's unique identifier.
phoneString | The column's phone value.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the phone column

You can update a phone column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

### Simple strings

To update a phone column, send "+", the phone number, and the ISO-2 country code (capitalized) as a string. Make sure to capitalize the country code and separate it from the phone number with a space to avoid errors!

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"phone", value: "+19175998722 US") {
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
      myColumnValue: "+19175998722 US"
      })
    })
  })
```

### JSON

To update a phone column using JSON, send "+", the phone number for the phone key, and the ISO-2 country code (capitalized) for the countryShortName key. Make sure to capitalize the country code to avoid errors!

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"phone\" : {\"phone\" : \"+12025550169\", \"countryShortName\" : \"US\"}}") {
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
      myColumnValues: "{\"phone\" : {\"phone\" : \"+12025550169\", \"countryShortName\" : \"US\"}}"
    })
  })
})
```

#### Phone number validation

You must provide correct and valid phone numbers to ensure that the columns function as expected. Our system confirms the validity and format each time a user submits a new column value, so it must adhere to the requirements to work as expected.

Our system accepts a phone number and country code in ISO 3166 format; it also uses the Google Phone Library to validate the accuracy of the number with the country code. If you are struggling with invalid column values, you can verify the accuracy of the phone number using an online tool .

Check out the following examples of valid phone numbers:

United States (US)

"{\"phone\":\"+12025550172\",\"countryShortName\":\"US\"}" "{\"phone\":\"12025550172\",\"countryShortName\":\"US\"}" "{\"phone\":\"2025550169\",\"countryShortName\":\"US\"}"

Great Britain (GB)

"{\"phone\":\"+447975777666\",\"countryShortName\":\"GB\"}" "{\"phone\":\"447975777666\",\"countryShortName\":\"GB\"}" "{\"phone\":\"+442079460990\",\"countryShortName\":\"GB\"}" "{\"phone\":\"07975777666\",\"countryShortName\":\"GB\"}"

Australia (AU)

"{\"phone\":\"+61488870510\",\"countryShortName\":\"AU\"}" "{\"phone\":\"61488870510\",\"countryShortName\":\"AU\"}" "{\"phone\":\"0488870510\",\"countryShortName\":\"AU\"}" "{\"phone\":\"0255504321\",\"countryShortName\":\"AU\"}"

## Clear the phone column

You have two options to clear a phone column. First, you can use the change_multiple_column_values mutation and pass null or an empty string in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"phone\" : null}") {
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
      myColumnValues: "{\"phone\" : null}"
    })
  })
})
```

You can also use the change_simple_column_value mutation and pass an empty string in the value argument.

GraphQLJavaScript
```
mutation {
  change_simple_column_value(item_id:9876543210, board_id:1234567890, column_id: "phone", value: "") {
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
