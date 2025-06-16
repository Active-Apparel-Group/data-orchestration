---

title: Files_assets
source: https://developer.monday.com/api-reference/reference/files-1
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, update, and clear the files column on monday boards using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Files (assets)

Learn how to read, update, and clear the files column on monday boards using the platform API

The files column contains files attached to a board. You can read , update , and clear the files column via the API, but you currently cannot filter your results by it.

## Read the files column

You can query the files column using the column_values object that enables you to return column-specific subfields by sending a fragment in your query.  Values for the files column are of the FileValue type.

GraphQL
```
query {
  items (ids:[1234567890, 9876543210]) {
    column_values {
      ... on FileValue {
        id
        column
      }
    }
  }
}
```

### Fields

Field | Description
--- | ---
columnColumn! | The column the value belongs to.
files[FileValueItem!]! | The column's attached files.
idID! | The column's unique identifier.
textString | The column's value as text. This field will return""if the column has an empty value.
typeColumnType! | The column's type.
valueJSON | The column's JSON-formatted raw value.

## Update the files column

You can update the files column using the add_file_to_column mutation. Please note that this requires the boards:write scope.

GraphQLJavaScript
```
mutation {
    add_file_to_column (item_id: 1234567890, column_id: "files", file: YOUR_FILE) {
        id
    }
}
```

```
var fs = require('fs');
var fetch = require('node-fetch'); // requires node-fetch as dependency

// adapted from: https://gist.github.com/tanaikech/40c9284e91d209356395b43022ffc5cc

// set filename
var upfile = 'sample.png';

// set auth token and query
var API_KEY = "MY_API_KEY"
var query = 'mutation ($file: File!) { add_file_to_column (file: $file, item_id: 1234567890, column_id: "files") { id } }';

// set URL and boundary
var url = "https://api.monday.com/v2/file";
var boundary = "xxxxxxxxxx";
var data = "";

fs.readFile(upfile, function(err, content){

    // simple catch error
    if(err){
        console.error(err);
    }

    // construct query part
    data += "--" + boundary + "\r\n";
    data += "Content-Disposition: form-data; name=\"query\"; \r\n";
    data += "Content-Type:application/json\r\n\r\n";
    data += "\r\n" + query + "\r\n";

    // construct file part
    data += "--" + boundary + "\r\n";
    data += "Content-Disposition: form-data; name=\"variables[file]\"; filename=\"" + upfile + "\"\r\n";
    data += "Content-Type:application/octet-stream\r\n\r\n";
    var payload = Buffer.concat([
            Buffer.from(data, "utf8"),
            new Buffer.from(content, 'binary'),
            Buffer.from("\r\n--" + boundary + "--\r\n", "utf8"),
    ]);

    // construct request options
    var options = {
        method: 'post',
        headers: {
          "Content-Type": "multipart/form-data; boundary=" + boundary,
          "Authorization" : API_KEY
        },
        body: payload,
    };

    // make request
    fetch(url, options)
      .then(res => res.json())
      .then(json => console.log(json));
});
```

## Clear the files column

You can clear a files column using the change_column_value mutation and passing "{\"clear_all\": true}" in the value argument.

GraphQLJavaScript
```
mutation {
 change_column_value(board_id:1234567890, item_id:9876543210, column_id: "files", value: "{\"clear_all\": true}") {
  id
 }
}
```

```
var query = "mutation { change_column_value (board_id: 1234567890, item_id: 9876543210, column_id: \"files\", value: \"{\\\"clear_all\\\": true}\") {id}}";

fetch ("https://api.monday.com/v2", {
  method: 'post',
  headers: {
    'Content-Type': 'application/json',
    'Authorization' : 'YOUR_API_KEY_HERE'
   },
   body: JSON.stringify({
     'query': query
   })
  })
   .then(res => res.json())
   .then(res => console.log(JSON.stringify(res, null, 2)));
```

## 📘Join our developer community!

We've created a community specifically for our devs where you can search through previous topics to find solutions, ask new questions, hear about new features and updates, and learn tips and tricks from other devs. Come join in on the fun! 😎
