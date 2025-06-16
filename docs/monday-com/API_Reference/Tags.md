---

title: Tags
source: https://developer.monday.com/api-reference/reference/tags-1
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query monday account tags using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Tags

Learn how to query monday account tags using the platform API

Tags are objects that help you group items from different groups or different boards throughout your account by a consistent keyword.

There are two types of tags: public and private. Public tags appear on main boards and are accessible to all member and viewer-level users by default, while private tags only appear on private or shareable boards.

Tag entities are created and displayed in the tags column.

# Queries

Required scope: tags:read

- Returns an array containing metadata about one or a collection of the account's public tags
- Can be queried directly at the root or nested within a boards query to return tags stored on private or shareable boards

Queried at the rootNested query
```
query {
  tags (ids: [1, 2, 4, 10]) {
    name
  }
}
```

```
query {
  boards (ids: 1234567890) {
    tags {
      id
    }	
  }
}
```

## 👍Pro tip

Before assigning a tag to an item, use the tags query to ensure it exists.

## Arguments

You can use the following argument(s) to reduce the number of results returned in your tags query.

Argument | Description
--- | ---
ids[Int] | The unique identifiers of specific tags to return. It will return an empty result for private tag IDs.

## Fields

You can use the following field(s) to specify what information your tags query will return.

Field | Description
--- | ---
colorString! | The tag's color.
idInt! | The tag's unique identifier.
nameString! | The tag's name.

# Mutations

Required scope: boards:write

## Create or get a tag

The create_or_get_tag mutation allows you to create new tags or receive their data if they already exist via the API. You can also specify what fields to query back from the tag when you run the mutation.

## 👍After creating a tag, it will only appear in the UI after being used at least once.

GraphQLJavaScript
```
mutation {
  create_or_get_tag (tag_name: "amazing") {
    id
  }
}
```

```
let query = "mutation { create_or_get_tag (tag_name: \"amazing\") { id } }";

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

### Arguments

You can use the following argument(s) to define the new or existing tag's characteristics.

Argument | Description
--- | ---
board_idID | The unique identifier of the shareable or private board where the tag should be created. If you want to create a public tag,do not usethis argument.
tag_nameString | The new tag's name.

## Update a tags column

The change_column_value mutation allows you to change a column value via the API. Check out the tags column type reference for the correct formatting!

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
