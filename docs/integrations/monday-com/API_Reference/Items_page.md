---

title: Items_page
source: https://developer.monday.com/api-reference/reference/items-page
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter monday board data using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Items page

Learn how to filter monday board data using the platform API

The items_page object represents a page of items. As a query, you can use it to filter data from a board. As an object type, it represents a set of items returned by the parent resolver.

Every board has advanced filters that enable you to retrieve items based on specified criteria quickly. You can replicate this behavior via the API using the items_page object and customized parameters to filter your results.

As the monday.com platform evolves, so does the allotted number of items on each board. These filters are the only way to retrieve items from larger boards without hitting any limits or timeouts since you can't query a board with all items.

As a bonus, these filters are more expressive so you don't have to waste any of your complexity budget retrieving unnecessary data.

## 🚧Want to read specific items on a board?

The items_page object allows you to query and filter all items on a board. If you want to read specific items using their IDs (up to 100 at a time), use the items object instead!

# Queries

Querying items_page will return items filtered by the specified criteria. This method accepts various arguments and returns an object.

You can only query items_page by nesting it within a boards query, so it can't be used at the root.

GraphQLJavaScript
```
query {
  boards (ids: 1234567890){
    items_page (limit: 1, query_params: {rules: [{column_id: "status", compare_value: [1]}], operator: and}) {
      cursor
      items {
        id 
        name 
      }
    }
  }
}
```

```
let query = "query { boards (ids: 1234567890) { items_page (limit:1, query_params: {rules: [{column_id: \"status\", compare_value: [1]}], operator: and}) { cursor items { id name }}}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_key_here',
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

You can use the following argument(s) to reduce the number of results returned in your items_page query.

Argument | Description | Supported arguments
--- | --- | ---
cursorString | An opaque token representing the position in a set of results to fetch items from. Use this to paginate through large result sets.Please notethat you can't usequery_paramsandcursorin the same request. We recommend usingquery_paramsfor the initial request andcursorfor paginated requests. | 
limitInt! | The number of items to return. The default is 25, but the maximum is 500. | 
query_paramsItemsQuery | A set of parameters to filter, sort, and control the scope of theboardsquery. Use this to customize the results based on specific criteria.Please notethat you can't usequery_paramsandcursorin the same request. We recommend usingquery_paramsfor the initial request andcursorfor paginated requests. | operatorItemsQueryOperatororder_by[ItemsQueryOrderBy!]rules[ItemsQueryRule!]

## Fields

You can use the following field(s) to specify what information your items_page query will return.

Field | Description
--- | ---
cursorString | An opaque cursor that represents the position in the list after the last returned item. Use this cursor for pagination to fetch the next set of items. If the cursor isnull, there are no more items to fetch.
items[Item!]! | The cursor's corresponding item.

# Cursor-based pagination usingnext_items_page

items_page utilizes cursor-based pagination to help return smaller sets of items from a large data set. When querying items_page , you can return the cursor argument that represents the next page of items.

After returning the cursor, you can keep paginating through the data set using the next_items_page object. This object allows you to retrieve the next page of items while avoiding the complexity cost of nesting items_page within a boards query. It takes the cursor argument, so you can specify where in the data set you want to start from.

## 🚧Cursor validity

Cursors are generated when you first request a given board and are cached for 60 minutes. Each cursor will expire 60 minutes after the first request .

## Queries

Querying next_items_page will return the next set of items that correspond with the provided cursor. This method accepts various arguments and returns an object. You can only query next_items_page at the root, so it cannot be nested within another query.

### Arguments

You can use the following argument(s) to reduce the number of results returned in your next_items_page query.

Argument | Description
--- | ---
cursorString! | An opaque cursor that represents the position in the list after the last returned item. Use this cursor for pagination to fetch the next set of items. If the cursor isnull, there are no more items to fetch.
limitInt! | The number of items to return. The maximum is 500.

### Fields

You can use the following field(s) to specify what information your next_items_page query will return.

Field | Description
--- | ---
cursorString | An opaque cursor that represents the position in the list after the last returned item. Use this cursor for pagination to fetch the next set of items. If the cursor isnull, there are no more items to fetch.
items[Item!]! | The cursor's corresponding item.

### Example

Now that you know the available arguments and fields for the next_items_page object, let's walk through an example. Say you only want to retrieve items with a timeline column that started between June 30, 2023, and July 1, 2023, from board 1234567890. This board contains thousands of items that cannot be retrieved simultaneously, so you can use cursor-based pagination.

The query below would return the ID and name of the first 50 items with a timeline column that started between those dates and a cursor value that represents the position in the data set after returning 50 items.

GraphQL
```
query {
  boards (ids:1234567890) {
    items_page (limit: 50, query_params: {rules: {column_id: "timeline", compare_value: ["2023-06-30", "2023-07-01"], compare_attribute: "START_DATE", operator:between}}) {
      cursor
      items {
        id
        name
      }
    }
  }
}
```

You can then use the next_items_page object with the cursor argument from the first query to return the following 50 relevant items in the data set. After returning the next cursor value, you can continue paginating through the entire data set.

GraphQL
```
query {
  next_items_page (limit: 50, cursor: "MSw5NzI4MDA5MDAsaV9YcmxJb0p1VEdYc1VWeGlxeF9kLDg4MiwzNXw0MTQ1NzU1MTE5") {
    cursor
    items {
      id
      name
    }
  }
}
```

# Use cases

This document has already covered the arguments and fields for the items_page object and how to use the next_items_page object to filter through large data sets using cursor-based pagination. Now, we will dive into a few use cases to demonstrate how and when to use the items_page object to filter and sort items.

### Filtering items by name

You only want to retrieve items named "New item" on board 1234567890.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "name", compare_value: ["New item"]}]}) {
      cursor
      items {
        id
      }
    }
  }
}
```

### Filtering items assigned to yourself with a checkmark

You only want to retrieve items assigned to yourself with a checkmark in the checkbox column on board 1234567890.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "people", compare_value: ["assigned_to_me"], operator:any_of} {column_id: "check", compare_value: null, operator: is_not_empty}]}) {
      cursor
      items {
        id
        name
      }
    }
  }
}
```

### Filtering items with specific status and people column values

You only want to retrieve items assigned to Person 1 (ID#76543210) or Person 7 (ID#01234567). In addition, you just need items marked as Done or Removed in the status column on board 1234567890.

With the people column , you have two different ways to filter data:

1. Send their name(s) as a string along with the contains_text operator
1. Use the any_of operator along with their IDs as a string in the following format: "person-XXXXXXXX"

GraphQL with textGraphQL with IDs
```
query {
  boards (ids: 1234567890){
    items_page (query_params: {rules: [{column_id: "people", compare_value: ["Person 1", "Person 2"], operator:contains_text} {column_id: "status", compare_value: [1, 0]}]operator:and}) {
      cursor
      items {
        id 
        name 
      }
    }
  }
}
```

```
query {
  boards (ids: 1234567890){
    items_page (query_params: {rules: [{column_id: "people", compare_value: ["person-87654321", "person-12345678"], operator:any_of} {column_id: "status", compare_value: [1, 0]}]operator:and}) {
      cursor
      items {
        id 
        name 
      }
    }
  }
}
```

### Filtering items with specific date column values in a particular group that are not assigned to yourself

You only want to retrieve items assigned to everyone but yourself, with a release date between June 1 and June 30, 2023, also in the group named Finished on board 1234567890.

GraphQL
```
query {
  boards (ids: 1234567890){
    items_page (query_params: {rules: [{column_id: "date", compare_value: ["2023-06-01","2023-06-30"], operator:between} {column_id: "group", compare_value: ["new_group12345"], operator:any_of} {column_id: "people", compare_value: "assigned_to_me", operator:not_any_of}]operator:and}) {
      cursor
      items {
        id 
        name 
      }
    }
  }
}
```

### Sorting items by column type

You can also use the items_page object to sort items by column type.

Let's say you want to retrieve items from a board and sort them by the item name column. The following query will return the first 25 items on board 1234567890 in ascending order (alphabetically) within each group.

GraphQL
```
query {
  boards(ids: 1234567890) {
    items_page(query_params: {order_by:[{column_id:"name"}]}) {
      cursor
      items {
        id
        name
      }
    }
  }
}
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
