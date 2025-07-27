# GraphQL Mutation Test for O/S Label Creation

## Background
Our code is failing when trying to create subitems with 'O/S' size value. Monday.com returns:
```
"The dropdown label 'O/S' does not exist, possible labels are: {...57: OS, 58: ONE SIZE...}"
```

## Exact GraphQL Mutation Our Code Is Making

Based on the logs and our GraphQL templates, here's the exact mutation:

```graphql
mutation {
  create_subitem(
    parent_item_id: 9683248375,
    item_name: "O/S",
    column_values: "{\"dropdown_mkrak7qp\": {\"labels\": [\"O/S\"]}}",
    create_labels_if_missing: true
  ) {
    id
    name
    column_values {
      id
      text
      value
    }
  }
}
```

## Test Variables
- **Board ID (subitems)**: 9609317948
- **Parent Item ID**: 9683248375 (from AESM004MAGNETAES-00013)
- **Column ID**: dropdown_mkrak7qp (size dropdown)
- **Label Value**: "O/S"
- **create_labels_if_missing**: true

## Alternative Test - Simple Column Value Change

Try this simpler version first:

```graphql
mutation {
  change_simple_column_value(
    item_id: 9683248375,
    board_id: 9609317948,
    column_id: "dropdown_mkrak7qp",
    value: "O/S",
    create_labels_if_missing: true
  ) {
    id
  }
}
```

## Expected Results
1. **If it works**: The 'O/S' label should be created automatically
2. **If it fails**: Monday.com has a limitation with the slash character or conflict with 'OS'

## Test This In Monday.com Developer Portal
1. Go to Monday.com Developer Portal
2. Use your API token
3. Run the mutation above
4. Check if the 'O/S' label gets created

## Current Hypothesis
Monday.com's `create_labels_if_missing` parameter may not handle:
- Special characters like '/' in labels
- Labels that are similar to existing ones ('O/S' vs 'OS')
- Case-sensitive conflicts
