---

title: Country
source: https://developer.monday.com/api-reference/reference/country
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter, read, update, and clear the country column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Country

Learn how to filter, read, update, and clear the country column on monday boards using the platform API

The country column represents a country from the list of available countries . You can filter , read , update , and clear the country column via the API.

## Filter the country column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the country column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | ""(blank values)The country'stwo-letter abbreviationto filter by
not_any_of | ""(blank values)The country'stwo-letter abbreviationto filter by
is_empty | null
is_not_empty | null
contains_text | The partial or whole country name to filter by as a string
not_contains_text | The partial or whole country name to filter by as a string

### Examples

The following example returns all items on the specified board with a country column value of Uruguay.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "country", compare_value: ["UY"], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the country column

You can query the country column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the country column are of the CountryValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on CountryValue {
        country
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
countryCountry | The country's value.
idID! | The column's unique identifier.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the country column

You can update a country column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update a country column, send the ISO-2 country code (a two-letter code) and the country name in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values:"{\"country\":{\"countryCode\":\"US\",\"countryName\":\"United States\"}}"){
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
      myColumnValues: "{\"country\": {\"countryCode\" : \"US\", \"countryName\": \"United States\"}}"
    })
  })
})
```

## Clear the country column

You can also clear a country column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"country\" : null}") {
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
      myColumnValues: "{\"country\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
