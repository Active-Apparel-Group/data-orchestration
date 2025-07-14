---

title: Column_types_reference
source: https://developer.monday.com/api-reference/reference/column-types-reference
author:
  - Monday
published:
created: 2025-05-25
description: The monday.com platform supports a variety of column types to store different data. Our API supports most types, allowing you to read, filter, delete, and update those columns. Most columns have some kind of support, but we also have a handful of unsupported columns. The tables below show a list of ...
tags: [code, api, monday-dot-com]
summary:

---

# Column types reference

The monday.com platform supports a variety of column types to store different data. Our API supports most types, allowing you to read, filter, delete, and update those columns. Most columns have some kind of support, but we also have a handful of unsupported columns.

The tables below show a list of supported and unsupported columns. You can also find a column's implementation value (see here for more info about implementations) and the column type enum value .

Each column has an individual document linked below that contains examples to read or change the values of different supported or partially supported columns. The expected formatting will vary depending on which column type's value you're attempting to change; some columns will accept only JSON values, and some will accept both Strings and JSON values.

# Supported columns

Column title | Implementation | Column type (2023-10and later)
--- | --- | ---
Button | ButtonValue | button
Checkbox | CheckboxValue | checkbox
Color picker | ColorPickerValue | color_picker
Connect boards | BoardRelationValue | board_relation
Country | CountryValue | country
Creation log | CreationLogValue | creation_log
Date | DateValue | date
Dependency | DependencyValue | dependency
Dropdown | DropdownValue | dropdown
Email | EmailValue | email
Files | FileValue | file
Formula | FormulaValue | formula
Hour | HourValue | hour
Item ID | ItemIdValue | item_id
Last updated | LastUpdatedValue | last_updated
Link | LinkValue | link
Location | LocationValue | location
Long Text | LongTextValue | long_text
Mirror | MirrorValue | mirror
monday doc | DocValue | doc
Name |  | name
Numbers | NumbersValue | numbers
People | PeopleValue | people
Phone | PhoneValue | phone
Rating | RatingValue | rating
Status | StatusValue | status
Tags | TagsValue | tags
Text | TextValue | text
Timeline | TimelineValue | timeline
Time tracking | TimeTrackingValue | time_tracking
Vote | VoteValue | vote
Week | WeekValue | week
World clock | WorldClockValue | world_clock

# Unsupported columns

Column title | Implementation | Column type (2023-10and later)
--- | --- | ---
Auto number |  | auto_number
Progress tracking | ProgressValue | progress

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
