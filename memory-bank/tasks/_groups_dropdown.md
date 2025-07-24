

# Dropdown management

## Instruction 3: Dropdown
ALSO add an urgent follow up task for 19:15 (please specify the date and timezone, e.g., 19:15 UTC on 2024-06-15): 

### Notes and proposed solution
**Issue from last sync: We have no CUSTOMER SEASON or AAG SEASON in the board.** 
**They are both dropdown columns they are mapped in:** [sync_order_list.toml](../../configs/pipelines/sync_order_list.toml)
- === Season and Planning ===
    "AAG SEASON" = "dropdown_mkr58de6" # dropdown - AAG SEASON
    "CATEGORY" = "dropdown_mkr5s5n3" # dropdown - CATEGORY
    "CUSTOMER SEASON" = "dropdown_mkr5rgs6" # dropdown - CUSTOMER SEASON

- when we call #file:batch_create_items.graphql or #file:batch_create_subitems.graphql are we including
- "create_labels_if_missing: true"
- this should be options, based on the column
- we can define this in TOML (not be environment - i.e. development, production - but global)
- just dropdown columns ...
- We could name the TOML header:
- monday.create_labels_if_missing
  - default = false
  - "dropdown_mkr58de6" = true # dropdown - AAG SEASON
  - "dropdown_mkr5s5n3" = false # dropdown - CATEGORY
  - "dropdown_mkr5rgs6" = true # dropdown - CUSTOMER SEASON

- this config would be really elegant!
- TOML to find header - monday.create_labels_if_missing
- extract everything after monday. = create_labels_if_missing
- then fetch true or false, then we have our string
- create_labels_if_missing: true


```graphql
  mutation {
  change_simple_column_value(
  item_id: 1234567890,
  board_id: 9876543210,
  column_id: "dropdown",
  value: "New dropdown value",
  create_labels_if_missing: true
  ) {
  id
  }
  }
```


Action item: Ensure all discussed dropdown configuration details are documented and tracked in the memory bank for future reference.
