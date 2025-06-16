---

title: Activity_logs
source: https://developer.monday.com/api-reference/reference/activity-logs
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to query activity logs from a monday board using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Activity logs

Learn how to query activity logs from a monday board using the platform API

Activity logs are records of all activities performed on a board. You can use them to see which actions were performed on your boards, when, and by whom.

# Queries

- Returns an array containing metadata about a collection of activity logs from a specific board
- Can only be nested within a boards query
- Limit: up to 10,000 logs total

GraphQLJavaScript
```
query {
  boards (ids: 1234567890) {
    activity_logs (from: "2021-07-23T00:00:00Z", to: "2021-07-26T00:00:00Z") {
      id
      event
      data
    }
  }
}
```

```
let query = 'query { boards (ids: 1234567890) { activity_logs (from: \"2021-07-23T00:00:00Z\", to: \"2021-07-26T00:00:00Z\") { id event data }}}';

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query' : query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## Arguments

You can use the following argument(s) to reduce the number of results returned in your activity_logs query. Results are returned in reverse chronological order.

Argument | Description
--- | ---
column_ids[String] | The specific columns to return events for.
fromISO8601DateTime | From timestamp (ISO8601).
group_ids[String] | The specific groups to return events for.
item_ids[ID!] | The specific items to return events for.
limitInt | The number of activity log events to return. The default is 25.
pageInt | The page number to return. Starts at 1.
toISO8601DateTime | To timestamp (ISO8601).
user_ids[ID!] | The specific users to return events for.

## Fields

You can use the following field(s) to specify what information your activity_logs query will return.

Field | Description | Enum values
--- | --- | ---
account_idString! | The unique identifier of the account that initiated the event. | 
dataString! | The item's column values. | 
entityString! | The entity of the event that was changed. | boardpulse
eventString! | The action that took place. | 
idString! | The unique identifier of the activity log event. | 
user_idString! | The unique identifier of the user who initiated the event. | 
created_atString! | The time of the event in 17-digit unix time. | 

### Created_atfield

The timestamps returned by this field are formatted as UNIX time with 17 digits.

To convert the timestamp to UNIX time in milliseconds, divide the 17-digit value by 10,000 and round to the nearest integer. For UNIX time in seconds, divide the value by 10,000,000.

JavaScriptPythonPHP
```
myDate = new Date(15880281464518396 / 10000)
```

```
import pandas as pd  
pd.to_datetime(16155031105053254 / 10000000, unit='s')
```

```
<?php
$timestamp=16155031105053254/10000000;
echo gmdate("Y-m-d\TH:i:s\Z", $timestamp);
?>
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
