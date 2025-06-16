---

title: Document_blocks
source: https://developer.monday.com/api-reference/reference/blocks
author:
  - Monday
published:
created: 2025-05-25
description: Learn how to read, create, update, and delete content blocks inside of monday docs using the platform API
tags: [code, api, monday-dot-com]
summary:

---

# Document blocks

Learn how to read, create, update, and delete content blocks inside of monday docs using the platform API

Workdocs are comprised of various components called document blocks. Blocks contain different types of content, including text, code, lists, titles, images, videos, and quotes.

# Queries

Required scope: docs:read

- Returns an array containing metadata about one or a collection of blocks
- Can only be nested with a docs query

GraphQLJavaScript
```
query {
  docs (ids:1234567) {
    blocks {
      id
      type
      content
    }
  }
}
```

```
let query = 'query { docs (ids: 1234567) { blocks { id type content }}}';

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

You can use the following argument(s) to reduce the number of results returned in your blocks query.

Argument | Description
--- | ---
limitInt | The number of docs to get. The default is 25.
pageInt | The page number to return. Starts at 1.

## Fields

You can use the following field(s) to specify what information your blocks query will return.

Field | Description
--- | ---
created_atDate | The block's creation date. Returned inYYYY-MM-DDformat.
created_byUser | The block's creator.
doc_idID | The document's unique identifier. In the UI, this ID appears in the top-left corner of the document whendeveloper modeis activated.
idString! | The block's unique identifier.
parent_block_idString | The parent block's unique identifier. First-level blocks will returnnull.
positionFloat | The block's position in the document.
typeString | The block's content type.
updated_atDate | The date the block was last updated. Returned inYYYY-MM-DDformat.
contentJSON | The block's content.

### Content field

The content field will return different information based on the block type. You can view a sample payload for each block type below, but keep in mind that the API will return payloads in a slightly different format using escaped JSON.

TextListTable and layoutNotice boxGIFImage: monday assetImage: public URLVideo: monday assetVideo: raw URL
```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "normal text", // "normal text", "large title", "medium title", "small title", or "quote"
	"content": {
		"alignment": "left", // "left", "center", or "right"
		"direction": "ltr", // "ltr" or "rtl"
		"deltaFormat": [{
			"insert": "document block text",
			"attributes": { // description of the text
				"bold": true, // bold text
				"underline": true, // underlined text
				"strike": true, // text with strike through
				"color": "var(--color-saladish)", // text with font color
				"background": "var(--color-river-selected)" // text with background color
			}
		}]
	}
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "check list", // "bulleted list", "numbered list", or "check list"
	"content": {
		"alignment": "right", // "left", "right", or "center"
		"direction": "rtl", // "ltr" or "rtl"
		"deltaFormat": [{
			"insert": "block 1"
		}],
		"indentation": 1,
		"checked": true // checks or unchecks a box
	}
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "table", // "table" or "layout"
	"content": {
		"cells": [ // the table's rows
			[{
					"blockId": "7f8c145-989f-48bb-b7f8-dc8f91690g42" // ID of the child block
				},
				{
					"blockId": "8g9d256-090g-59cc-c8g9-ed9g02701h53" // ID of the child block
				}
			]
		],
		"alignment": "right", // "left", "right", or "center"
		"direction": "rtl", // "ltr" or "rtl"
		"columnsStyle": [{ // size of the column by percent - the sum of these values has to be 100
				"width": 50
			},
			{
				"width": 50
			}
		]
	}
}
```

```
{
  "id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
  "type": "notice box", 
  "content": {
  	"theme": "info", // "tips", "warning", or "general"
  	"direction": "ltr", // "ltr" or "rtl"
  	"alignment": "left" // "left", "right", or "center"
  }
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "gif",
	"content": {
		"id": "123abc456def",
		"url": "https://media2.giphy.com/media/123abc456def/311x.gif?cid=1d9492h43&rid=200w.gif&ct=g",
		"width": 278,
		"alignment": "center", // "left", "right", or "center"
		"direction": "ltr", // "ltr" or "rtl"
		"aspectRatio": ""
	}
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "image",
	"content": {
		"url": "https://monday.monday.com/test/resources/123456789/testimage.png",
		"width": "900",
		"assetId": 123456789,
		"alignment": "center", // "left", "right", or "center"
		"direction": "ltr", // "ltr" or "rtl"
		"aspectRatio": "2380x1230"
	}
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "image",
	"content": {
		"width": 123, // changes the size of the image
		"publicUrl": "https://www.test.com/static/download/testimage.png",
		"direction": "rtl", // "ltr" or "rtl"
		"alignment": "right" // "left", "right", or "center"
	}
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "video",
	"content": {
		"url": "https://monday.monday.com/test/987654321/testvideo.mov",
		"width": 613,
		"assetId": 987654321,
		"alignment": "center", // "left", "right", or "center"
		"direction": "ltr", // "ltr" or "rtl"
		"aspectRatio": null
	}
}
```

```
{
	"id": "7f8c145-989f-48bb-b7f8-dc8f91690g42",
	"type": "video",
	"content": {
		"url": null,
		"width": 450,
		"rawUrl": "https://www.youtube.com/watch?v=123abc",
		"assetId": null,
		"alignment": "left", // "left", "right", or "center"
		"direction": "ltr", // "ltr" or "rtl"
		"embedData": {
			"embedlyData": {
				"url": "https://www.youtube.com/watch?v=123abc",
				"html": "<iframe class=\"embedly-embed\" src=\"//cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.youtube.com%2Fembed%2F123abc&display_name=YouTube&url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D123abc&image=http%3A%2F%2Fi.ytimg.com%2Fvi%2F123abc%2Fhqdefault.jpg&key=60f4bf4bdbb750b6b09783043556f314&type=text%2Fhtml&schema=youtube\" width=\"854\" height=\"480\" scrolling=\"no\" title=\"YouTube embed\" frameborder=\"0\" allow=\"autoplay; fullscreen\" allowfullscreen=\"true\"></iframe>",
				"type": "video",
				"title": "Sample video title",
				"width": 854,
				"height": 480,
				"version": "1.0",
				"author_url": "https://www.youtube.com/monday.com",
				"author_name": "monday.com",
				"description": "This is a sample monday.com video",
				"provider_url": "http://youtube.com",
				"provider_name": "YouTube",
				"thumbnail_url": "http://i.ytimg.com/vi/3lrXMmciw2N/hqdefault.jpg",
				"thumbnail_width": 480,
				"thumbnail_height": 360
			}
		}
	}
}
```

# Mutations

Required scope: docs:write

## Create document block

This mutation creates a new doc block. You can also specify what fields to query back from the new doc block when you run the mutation.

Alternatively, you can add a new document block using the SDK .

GraphQLJavaScript
```
mutation {
  create_doc_block (type: normal_text, doc_id: 1234567, after_block_id: "7f8c145-989f-48bb-b7f8-dc8f91690g42", content: "{\"alignment\":\"left\",\"direction\":\"ltr\",\"deltaFormat\":[{\"insert\":\"new block\"}]}") {
    id
  }
}
```

```
let query = 'mutation {  create_doc_block (type: normal_text, doc_id: 1234567, after_block_id: "7f8c145-989f-48bb-b7f8-dc8f91690g42", content: \"{\\\"alignment\\\":\\\"left\\\",\\\"direction\\\":\\\"ltr\\\",\\\"deltaFormat\\\":[{\\\"insert\\\":\\\"new block\\\"}]}\") { id }}';

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

### Arguments

You can use the following argument(s) to define the new doc block's characteristics.

Argument | Description | Enum values
--- | --- | ---
after_block_idString | The block's ID that will be above the new block. Used to specify where in the doc the new block should go. Without this argument, the new block will appear at the top of the doc. | 
doc_idID! | The document's unique identifier. | 
parent_block_idString | The parent block's ID that that new block will be created under. | 
typeDocBlockContentType! | The block's content type. | bulleted_listcheck_listcodedividerimagelarge_titlelayoutmedium_titlenormal_textnotice_box,numbered_listpage_breakquotesmall_titletablevideo
contentJSON! | The block's content. | 

#### Content argument

When creating a new block, the content must follow proper JSON formatting and contain all necessary attributes.

For text blocks and most other block types, all attributes are optional. You can use the same fields and attributes returned when you query the block's content.

Tables have two required attributes: column_count and row_count . Tables can have up to 25 rows and 10 columns. You cannot update table dimensions after setting them. The column_style attribute is optional, but you can use it to specify the size of each cell. The sum of each cell's width must equal 100.

Layouts require the column_count field, which determines the size of your layout. You can use the optional column_style attribute to determine the size of each cell in the layout. The sum of each cell's width must equal 100.

## Update document block

This mutation updates a doc block. You can also specify what fields to query back from the updated doc block when you run the mutation.

Alternatively, you can update a document block using the SDK .

GraphQLJavaScript
```
mutation {
  update_doc_block (block_id: "7f8c145-989f-48bb-b7f8-dc8f91690g42", content: "{\"alignment\":\"left\",\"direction\":\"ltr\",\"deltaFormat\":[{\"insert\":\"new block\"}]}") {
    id
  }
}
```

```
let query = 'mutation { update_doc_block (block_id: "7f8c145-989f-48bb-b7f8-dc8f91690g42", content: \"{\\\"alignment\\\":\\\"left\\\",\\\"direction\\\":\\\"ltr\\\",\\\"deltaFormat\\\":[{\\\"insert\\\":\\\"new block\\\"}]}\") { id }}';

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

### Arguments

You can use the following argument(s) to define the updated doc block's characteristics.

Argument | Description
--- | ---
block_idString! | The block's unique identifier.
contentJSON! | The block's content.

#### Content argument

When updating a block, the content must follow proper JSON formatting and contain all necessary attributes.

For text blocks and most other block types, all attributes are optional. You can use the same fields and attributes returned when you query the block's content.

Tables have two required attributes. They need both the column_count and row_count attributes to determine the size of your table. The maximum value for each is 5; you cannot change the values after setting them. The column_style attribute is optional, but you can use it to specify the size of each cell. The sum of each cell's width must equal 100.

Layouts have one required attribute. They require the column_count field to determine the size of your layout. Optionally, you can also use the column_style attribute to determine the size of each cell in the layout. The sum of each cell's width must equal 100.

## Delete document block

This mutation deletes a doc block. You can also specify what fields to query back from the deleted doc block when you run the mutation.

GraphQLJavaScript
```
mutation { 
  delete_doc_block (block_id: "7f8c145-989f-48bb-b7f8-dc8f91690g42") {
    id
  }
}
```

```
let query = 'mutation { delete_doc_block (block_id: "block-4-1671991243355") { id }}';

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

### Arguments

Argument | Description
--- | ---
block_idString! | The block's unique identifier.
