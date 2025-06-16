---

title: Vote
source: https://developer.monday.com/api-reference/reference/vote
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to filter by and read the vote column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Vote

Learn how to filter by and read the vote column on monday boards using the platform API

The vote column allows board subscribers and team members to vote for items. You can filter by and read the vote column via the API, but you cannot update or clear it.

## Filter by the vote column

Using the items_page object, you can easily filter a board's items by specific columns or column values. The table below contains the vote column's supported operators and compare values.

Operators | Compare values
--- | ---
any_of | The user IDs to filter by"No votes"
not_any_of | The user IDs to filter by"No votes"
is_empty | null
is_not_empty | null

### Examples

The following example returns all items on the specified board where user 123456 voted in the vote column.

GraphQL
```
query {
  boards (ids: 1234567890) {
    items_page (query_params: {rules: [{column_id: "vote", compare_value: [123456], operator:any_of}]}) {
      items {
        id
        name
      }
    }
  }
}
```

## Read the vote column

You can query the vote column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the vote column are of the VoteValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on VoteValue {
        vote_count
        voter_ids
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
textString | The column's value as text. This field will return"0"if the column has no votes.
typeColumnType! | The column's type.
updated_atDate | The column's last updated date.
valueJSON | The column's JSON-formatted raw value.
vote_countInt! | The total number of votes.
voters[User!]! | The users who voted.
voter_ids[ID!]! | The unique identifiers of users who voted.

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
