---

title: Rating
source: https://developer.monday.com/api-reference/reference/rating
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by, read, update, and clear the rating column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Rating

Learn how to filter by, read, update, and clear the rating column on monday boards using the platform API

The rating column holds rating information for your item(s) which can be useful for ranking or assigning a grade to your item(s). You can filter by , read , update , and clear the rating column via the API.

## Filter by the rating column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the rating column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | 0(blank values)1(rated 1)2(rated 2)3(rated 3)4(rated 4)5(rated 5)
not_any_of | 0(blank values)1(rated 1)2(rated 2)3(rated 3)4(rated 4)5(rated 5)

### Examples

The following example returns all items on the specified board without a blank rating column.

GraphQL
```
query {
  boards (ids:1234567890) {
    items_page (query_params: {rules: {column_id: "rating", compare_value:[0], operator:not_any_of }}) {
      items {
        id
      }
    }
  }
}
```

## Read the rating column

You can query the rating column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the rating column are of the RatingValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on RatingValue {
        rating
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
idID! | The column's unique identifier.
ratingInt | The column's rating value.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the rating column

You can update a rating column using the change_multiple_column_values mutation and passing a JSON string in the column_values argument. Simple string updates are not supported.

### JSON

To update a rating column using JSON, send a number between 1 and your rating scale. If you'd like to adjust your rating scale, you can do so in the column settings!

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"rating\" : {\"rating\" : 5}}") {
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
      myColumnValues: "{\"rating\" : {\"rating\" : \"5\"}}"
      })
    })
  })
})
```

## Clear the rating column

You can also clear a rating column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:123456789, column_values: "{\"rating\" : null}") {
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
      myColumnValues: "{\"rating\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
