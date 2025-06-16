---

title: Location
source: https://developer.monday.com/api-reference/reference/location
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, update, and clear the location column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Location

Learn how to read, update, and clear the location column on monday boards using the platform API

The location column stores a location with longitude and latitude precision (but displayed with text). You can read , update , and clear the location column via the API, but you cannot filter your results by it.

## Read the location column

You can query the location column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the location column are of the LocationValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on LocationValue {
        country
        street
        street_number
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
addressString | The column's address value.
cityString | The column's city value.
city_shortString | The column's shortened city value.
columnColumn! | The column the value belongs to.
countryString | The column's country value.
country_shortString | The column's shortened country value.
idID! | The column's unique identifier.
latFloat | The column's latitude value.
lngFloat | The column's longitude value.
place_idString | The unique place identifier of the location.
streetString | The column's street value.
street_numberString | The column's street building number value.
street_number_shortString | The column's shortened street building number value.
street_shortString | The column's shortened street value.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.

## Update the location column

You can update a location column using the change_simple_column_value mutation and sending a simple string in the value argument. You can also use the change_multiple_column_values mutation and pass a JSON string in the column_values argument.

## 📘Note

The address is not verified to match the latitude/longitude and is just used as the text displayed in the cell. In case no address is provided, the address will be displayed as unknown .

The legal values for latitude are between -90.0 and 90.0 exclusive and between -180.0 and 180.0 inclusive for longitude. If the updated values exceed those ranges, you will get an error.

### Simple strings

To update a location column, send the latitude, longitude, and address of the location separated by spaces (optional).

GraphQLJavaScript
```
mutation {
  change_simple_column_value (item_id:9876543210, board_id:1234567890, column_id:"location", value:"29.9772962 31.1324955 Giza Pyramid Complex") {
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
      columnId: "location",
      myColumnValue: "29.9772962 31.1324955 Giza Pyramid Complex"
      })
    })
  })
```

### JSON

To update a location column using JSON, send the latitude, longitude, and address of the location (optional).

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"location\" : {\"lat\":\"29.9772962\",\"lng\":\"31.1324955\",\"address\":\"Giza Pyramid Complex\"}}") {
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
      myColumnValues: "{\"location\" : {\"lat\" : \"29.9772962\", \"lng\": \"31.1324955\", \"address\": \"Giza Pyramid Complex\"}}"
    })
  })
})
```

## Clear the location column

You can also clear a location column using the change_multiple_column_values mutation and passing null or an empty object in the column_values argument.

GraphQLJavaScript
```
mutation {
  change_multiple_column_values(item_id:9876543210, board_id:1234567890, column_values: "{\"location\" : null}") {
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
      myColumnValues: "{\"location\" : null}"
    })
  })
})
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
