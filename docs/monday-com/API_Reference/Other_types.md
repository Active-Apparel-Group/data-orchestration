---

title: Other_types
source: https://developer.monday.com/api-reference/reference/other-types
author:
  - Monday
published:
created: 2025-05-25
description: Learn about other types supported by the monday platform API
tags: [code, api, monday-dot-com]
summary:

---

# Other types

Learn about other types supported by the monday platform API

# Account product

The AccountProduct type is used as a field on account queries. It contains a set of fields that returns metadata about the account's products.

Field | Description | Enum values
--- | --- | ---
default_workspace_idID | The product's | The account product's default workspace ID.
idID | The unique identifier of the account product. | 
kindAccountProductKind | The account product. | core,crm,forms,marketing,projectManagement,project_management,service,software,whiteboard

# Activate users result

The ActivateUsersResult type contains fields that show the result of activating a user through the activate_users mutation.

Field | Description | Supported fields
--- | --- | ---
activated_users[User!] | The users that were activated. | 
errors[ActivateUsersError!] | The errors that occurred while activating users. Use this field to check for calls that failed. | codeActivateUsersErrorCodemessageStringuser_idID

## Activate users error

The ActivateUsersError type contains a subset of fields to describe the error that occurred when a activate_users mutation fails.

Field | Description | Enum values
--- | --- | ---
codeActivateUsersErrorCode | The error code that occurred. | CANNOT_UPDATE_SELFEXCEEDS_BATCH_LIMITFAILEDINVALID_INPUTUSER_NOT_FOUND
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Assign team owners result

The AssignTeamOwnersResult type contains fields that show the result of assigning team owners through the assign_team_owners mutation.

Field | Description
--- | ---
errors[AssignTeamOwnersError!] | The errors that occurred while assigning owners to a team. Use this field to check for calls that failed.
teamTeam | The team the owners were assigned to.

## Assign team owners error

The AssignTeamOwnersError type contains a subset of fields to describe the error that occurred when a assign_team_owners mutation fails.

Field | Description | Enum values
--- | --- | ---
codeAssignTeamOwnersErrorCode | The error code that occurred. | CANNOT_UPDATE_SELFEXCEEDS_BATCH_LIMITFAILEDINVALID_INPUTUSER_NOT_FOUNDUSER_NOT_MEMBER_OF_TEAMVIEWERS_OR_GUESTS
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Change team memberships result

The ChangeTeamsMembershipResult type contains fields that show the result of adding or removing users from a team for the add_users_to_team and remove_users_from_team mutations.

Field | Description
--- | ---
failed_users[User!] | The users the team membership update failed for.
successful_users[User!] | The users the team membership update succeeded for.

# Column mapping input

The ColumnMappingInput type is an argument on the move_items_to_board mutation that defines the column mapping between the target and source boards.

Field | Description
--- | ---
sourceID! | The source column's unique identifier.
targetID | The target column's unique identifier.

# Column type

ColumnType accepts enum values to specify which column type to filter, read, or update in your query or mutation.

### Enum values

auto_number | long_text
--- | ---
board_relation | mirror
button | name
checkbox | numbers
color_picker | people
country | phone
creation_log | progress
date | rating
dependency | status
doc | subtasks
dropdown | tags
email | team
file | text
formula | timeline
hour | time_tracking
item_assignees | vote
item_id | week
last_updated | world_clock
link | unsupported
location | 

# Create doc input

The CreateDocInput! type is an argument for the create_doc mutation that contains a set of arguments to specify where to create the new doc.

Field | Description | Supported arguments
--- | --- | ---
boardCreateDocBoardInput | The new document's location (when creating a doc on a board). | column_idString!item_idID!
workspaceCreateDocWorkspaceInput | The new document's location (when creating a doc in a workspace). | kindBoardKindnameString!workspace_idID!

## Create doc board input

The CreateDocBoardInput type is used to specify the item and column where you want to create the new document.

Field | Description
--- | ---
column_idString! | The unique identifier of the column to create the new doc in.
item_idID! | The unique identifier of the item to create the new doc on.

## Create doc workspace input

The CreateDocWorkspaceInput type is used to specify the workspace where you want to create a document and the new document's name and kind.

Field | Description | Enum values
--- | --- | ---
kindBoardKind | The kind of document to create. | privatepublicshare
nameString! | The new document's name. | 
workspace_idID! | The unique identifier of the workspace to create the new doc in. | 

# Create team

## Create team attributes input

The CreateTeamAttributesInput! type is used as an argument on the create_team mutation to specify the characteristics of the new team being created via the API.

Field | Description
--- | ---
is_guest_teamBoolean | Whether or not the new team contains guest users.
nameString! | The new team's name.
parent_team_idID | The parent team's unique identifier.
subscriber_ids[ID!] | The team members's unique identifiers. Cannot be empty unlessallow_empty_teamis set.

## Create team options input

The CreateTeamOptionsInput type is used to specify the options when creating a new team via the API.

Field | Description
--- | ---
allow_empty_teamBoolean | Whether or not the team can have no subscribers.

# Deactivate users result

The DeactivateUsersResult type contains fields that show the result of deactivating a user through the deactivate_user mutation.

Field | Description
--- | ---
deactivated_users[User]! | Data from the users that were deactivated.
errors[DeactivateUsersError]! | The errors that occurred during deactivation. Use this field to check for calls that failed.

## Deactivate users error

The DeactivateUsersError type contains a subset of fields to describe the error that occurred when a deactivate_user mutation fails.

Field | Description | Enum values
--- | --- | ---
codeDeactivateUsersErrorCode | The error code that occurred. | CANNOT_UPDATE_SELFEXCEEDS_BATCH_LIMITFAILEDINVALID_INPUTUSER_NOT_FOUND
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Invite users result

The InviteUsersResult type contains fields that show the result of inviting a user through the invite_users mutation.

Field | Description
--- | ---
invited_users[User!] | Data from the users that were successfully invited.
errors[InviteUsersError!] | The errors that occurred while inviting users. Use this field to check for calls that failed.

## Invite users error

The InviteUsersError type contains a subset of fields to describe the error that occurred when an invite_users mutation fails.

Field | Description | Enum values
--- | --- | ---
codeInviteUsersErrorCode | The error code that occurred. | ERROR
messageString | The error message. | 
emailID | The email of the user that caused the error. | 

# Items page by column values query

The ItemsPageByColumnValuesQuery type is used as an argument for the items_page_by_column_values object and contains a set of fields used to specify which columns and column values to filter your results by.

Field | Description
--- | ---
column_idString! | The IDs of the specific columns to return results for.
column_values[String]! | The column values to filter items by.

# Items query

The ItemsQuery type is used as an argument for the items_page object and contains a set of parameters to filter, sort, and control the scope of the boards query.

Field | Description | Enum values | Supported arguments
--- | --- | --- | ---
ids[ID!] | The specific item IDs to return. The maximum is 100. |  | 
rules[ItemsQueryRule!] | The rules to filter your queries. |  | column_idID!compare_attributeStringcompare_valueCompareValue!operatorItemsQueryRuleOperator
operatorItemsQueryOperator | The conditions between query rules. The default isand. | andor | 
order_by[ItemsQueryOrderBy!] | The attributes to sort results by. |  | column_idString!directionItemsOrderByDirection

## [ItemsQueryRule!]

The rules to filter your queries.

Field | Description | Enum values
--- | --- | ---
column_idID! | The unique identifier of the column to filter by. | 
compare_attributeString | The comparison attribute. You can find the supported attributes for each column type in thecolumn types reference. Most columns don't have acompare_attribute. | 
compare_valueCompareValue! | The column value to filter by. This can be astringor index value depending on the column type. You can find the supported values for each column type in thecolumn types reference. | 
operatorItemsQueryRuleOperator | The condition for value comparison. The default isany_of. | any_ofnot_any_ofis_emptyis_not_emptygreater_thangreater_than_or_equalslower_thanlower_than_or_equalbetweennot_contains_textcontains_textcontains_termsstarts_withends_withwithin_the_nextwithin_the_last

## [ItemsQueryOrderBy!]

The attributes to sort results by.

Field | Description | Enum values
--- | --- | ---
column_idString! | The unique identifier of the column to filter or sort by.  You can also enter"__creation_log__"or"__last_updated__"to chronologically sort results by their last updated or creation date (oldest to newest). | 
directionItemsOrderByDirection | The direction to sort items in. The default isasc. | ascdesc

# Like

The Like type is used as a field on updates queries and contains a set of fields to return details about the update's reactions or likes.

Fields | Description | Enum values
--- | --- | ---
created_atDate | The like's creation date. | 
creatorUser | The user that liked the update. | 
creator_idString | The unique identifier of the user that liked the update. | 
idID! | The like's unique identifier. | 
reaction_typeReactionType | The reaction type. | ClapHappyLikeLovePlusOneRocksTrophyWow
updated_atDate | The like's last updated date. | 

# Linked items

The linked_items field returns an item's linked items on an items query.

Arguments | Description
--- | ---
linked_board_idInt! | The linked board's unique identifier.
link_to_item_column_idString! | The link to item column's unique identifier.

# Managed columns

  🚧 Only available in API versions 2025-07 and later

Managed columns are useful tools to standardize workflows across your monday.com account. Select users can create, own, and manage status and dropdown columns with predefined labels that can't be edited by other members. This ensures consistent terminology across different workflows and helps align teams on a unified structure.

Users with managed column permissions can read, create, activate, update, deactivate, and deleted managed dropdown and status columns via the API.

## Dropdown

### Dropdown column settings

DropdownColumnSettings is one of two possible GraphQL implementation types for a managed column's settings field. It includes a subset of fields that return the configuration of a managed dropdown column.

  🚧 Only available in API versions 2025-07 and later

Field | Description | Supported fields
--- | --- | ---
labels[DropdownLabel!] | An array containing the settings of the managed dropdown column's labels. | idIntis_deactivatedBooleanlabelString
typeManagedColumnTypes | The type of managed column:dropdownorstatus. | 

#### Dropdown label

The DropdownLabel type defines the individual labels used in a managed dropdown column. Each label includes details such as display text, ID, and status.

Field | Description
--- | ---
idInt | The unique identifier of the managed dropdown column's label.
is_deactivatedBoolean | Whether the managed dropdown column's label is deactivated.
labelString | The managed dropdown column label's text.

### Create dropdown column settings input

The CreateDropdownColumnSettingsInput type is used as an argument on the create_dropdown_managed_column mutation. It contains one field used to define the properties of the new managed dropdown column's labels.

  🚧 Only available in API versions 2025-07 and later

Field | Description | Supported fields
--- | --- | ---
labels[CreateDropdownLabelInput!]! | An array that specifies the new managed dropdown column's labels. | labelString!

#### Create dropdown label input

The [CreateDropdownLabelInput!]! type contains a one field to specify the new properties of the managed dropdown column's label.

Field | Description
--- | ---
labelString! | The text on the new managed dropdown column's label.

### Update dropdown column settings input

The UpdateDropdownColumnSettingsInput type is used as an argument on the update_dropdown_managed_column mutation. It contains one field used to define the updated managed dropdown column label's properties.

  🚧 Only available in API versions 2025-07 and later

Field | Description | Supported fields
--- | --- | ---
labels[UpdateDropdownLabelInput!]! | An array that specifies the updated managed dropdown column's labels. | idIntis_deactivatedBooleanlabelString!

#### Update dropdown label input

The [UpdateDropdownLabelInput!]! type contains a subset of fields to specify the updated dropdown label's properties.

Field | Description
--- | ---
idInt | The unique identifier of the existing label to update. Omit it to create a new label.
is_deactivatedBoolean | Whether the label is deactivated.
labelString! | The managed dropdown column's updated label.

## Status

### Status column colors

The StatusColumnColors type is used to specify and identify a managed status column's label color. You can find a list of each value and its corresponding color here .

  🚧 Only available in API versions 2025-07 and later

Enum values |  | 
--- | --- | ---
american_gray | aquamarine | berry
blackish | bright_blue | bright_green
brown | bubble | chili_blue
coffee | dark_blue | dark_indigo
dark_orange | dark_purple | dark_red
done_green | egg_yolk | explosive
grass_green | indigo | lavender
lilac | lipstick | navy
orchid | peach | pecan
purple | river | royal
saladish | sky | sofia_pink
steel | stuck_red | sunset
tan | teal | winter
working_orange |  | 

### Status column settings

StatusColumnSettings is one of two possible GraphQL implementation types for a managed column's settings field. It includes a subset of fields that return the configuration of a managed status column.

  🚧 Only available in API versions 2025-07 and later

Field | Description | Supported fields
--- | --- | ---
labels[StatusLabel!] | An array containing the settings of the managed status column's labels. | colorStatusColumnColorsdescriptionStringidIntindexIntis_deactivatedBooleanis_doneBooleanlabelString
typeManagedColumnTypes | The type of managed column:dropdownorstatus. | 

#### Status label

The StatusLabel type defines the individual labels used in a managed status column. Each label includes details such as color, display text, and status.

Field | Description
--- | ---
colorStatusColumnColors | The status label's color. See the complete list of available colors here.
descriptionString | The status label's description.
idInt | The status label's unique identifier.
indexInt | The status label's index.
is_deactivatedBoolean | Whether the status label is deactivated.
is_doneBoolean | Whether the status label is "Done".
labelString | The status label's text.

### Create status column settings input

The CreateStatusColumnSettingsInput type is used as an argument on the create_status_managed_column mutation. It contains one field used to define the properties of the new managed status column's labels.

  🚧 Only available in API versions 2025-07 and later

Field | Description | Supported fields
--- | --- | ---
labels[CreateStatusLabelInput!]! | An array that defines the new managed status column's labels. | colorStatusColumnColors!descriptionStringindexInt!is_doneBooleanlabelString!

#### Create status label input

The [CreateStatusLabelInput!]! type contains a subset of fields to specify the new properties of the managed status column's label.

Field | Description
--- | ---
colorStatusColumnColors! | The color of the new managed status column's label. See the complete list of available colors here.
descriptionString | The new managed status column's description.
indexInt! | The index of the new managed status column's label.
is_doneBoolean | Whether the label is marked as "Done"
labelString! | The text on the new managed status column's label.

### Update status column settings input

The UpdateStatusColumnSettingsInput type is used as an argument on the update_status_managed_column mutation. It contains one field used to define the properties of the updated managed status column's labels.

  🚧 Only available in API versions 2025-07 and later

Field | Description | Supported fields
--- | --- | ---
labels[UpdateStatusLabelInput!]! | An array that defines the updated managed status column's labels. | colorStatusColumnColors!descriptionStringidIntindexInt!is_doneBooleanlabelString!

#### Update status label input

The [UpdateStatusLabelInput!]! type contains a subset of fields to specify the updated status label's properties.

Field | Description
--- | ---
colorStatusColumnColors! | The updated color of the managed status column's label.
descriptionString | The managed status column's updated description.
idInt | The unique identifier of the existing label to update. Omit it to create a new label.
indexInt! | The updated index of the new managed status column's label.
is_deactivatedBoolean | Whether the status label is deactivated.
is_doneBoolean | Whether the label is marked as "Done"
labelString! | The updated text on the new managed status column's label.

# Mirrored item

The MirroredItem type is used as a field on the MirrorValue implementation and contains a set of fields to return details about an item's mirrored items.

Fields | Description | Possible types
--- | --- | ---
linked_boardBoard! | The linked board. | 
linked_board_idID! | The linked board's unique identifier. | 
linked_itemItem! | The linked item. | 
mirrored_valueMirroredValue | The mirrored values. | Board,BoardRelationValue,ButtonValue,CheckboxValue,ColorPickerValue,CountryValue,CreationLogValue,DateValue,DependencyValue,DocValue,DropdownValue,EmailValue,FileValue,FormulaValue,Group,HourValue,ItemIdValue,LastUpdatedValue,LinkValue,LocationValue,LongTextValue,MirrorValue,NumbersValue,PeopleValue,PhoneValue,ProgressValue,RatingValue,StatusValue,SubtasksValue,TagsValue,TeamValue,TextValue,TimeTrackingValue,TimelineValue,UnsupportedValue,VoteValue,WeekValue,WorldClockValue

# Number value unit direction

The NumberValueUnitDirection type is used as a field on the NumbersValue implementation that indicates whether the unit symbol is placed to the right or left of a number value.

Enum values | Description
--- | ---
left | The symbol is placed to the left of the number.
right | The symbol is placed to the right of the number.

# People entity

The PeopleEntity type is used as a field on the PeopleValue implementation that contains the column's people or team values.

Field | Description | Enum values
--- | --- | ---
idID! | The unique identifier of the person or team. | 
kindKind | The type of entity. | personteam

# Platform API daily analytics

The daily_analytics field on platform_API queries returns metadata about an account's daily API consumption. It includes fields to sort data by app, day, user, or view the last updated timestamp.

Field | Description | Supported fields
--- | --- | ---
by_app[PlatformApiDailyAnalyticsByApp!]! | The API usage per app. | api_app_idString!appAppTypeusageInt!
by_day[PlatformApiDailyAnalyticsByDay!]! | The API usage per day. | dayString!usageInt!
by_user[PlatformApiDailyAnalyticsByUser!]! | The daily API usage per user. | usageInt!userUser!
last_updatedISO8601DateTime | The timestamp of when the API usage data was last updated. | 

## By app

The [PlatformApiDailyAnalyticsByApp!]! type is used as a field on platform API daily_analytics queries. It returns API consumption data for the top six apps over the past 14 days.

Field | Description | Supported fields
--- | --- | ---
api_app_idID! | The app's unique API consumer identifier. | 
appAppType | Metadata about the top six apps with the highest API consumption. | api_app_idIDclient_idStringcreated_atDatefeatures[AppFeatureType!]idID!kindStringnameStringstateStringupdated_atDateuser_idID
usageInt! | The API amount consumed by a given app in the past 14 days. | 

## By day

The [PlatformApiDailyAnalyticsByDay!]! type is used as a field on platform API daily_analytics queries. It returns details about API usage per day over the past 14 days.

Field | Description
--- | ---
dayString! | The day.
usageInt! | The amount consumed on a given day.

## By user

The [PlatformApiDailyAnalyticsByUser!]! type is used as a field on daily_analytics queries. It returns API consumption data for the top six users over the past 14 days.

Field | Description
--- | ---
usageInt! | The API amount consumed by a given user in the past 14 days.
userUser! | Metadata about the top six users with the highest API consumption.

# Position relative

The PositionRelative type is used as an argument on the create_item and create_group mutations. It contains a set of enum values to determine the location of the item or group being created.

Enum value | Description
--- | ---
after_at | Creates the new group or item below therelative_tovalue.
before_at | Creates the new group or item above therelative_tovalue.

# Remove team owners result

The RemoveTeamOwnersResult type contains fields that show the result of removing team owners through the remove_team_owners mutation.

Field | Description
--- | ---
errors[RemoveTeamOwnersError!] | The errors that occurred while removing owners from a team. Use this field to check for calls that failed.
teamTeam | The team the owners were removed from.

## Remove team owners error

The RemoveTeamOwnersError type contains a subset of fields to describe the error that occurred when a remove_team_owners mutation fails.

Field | Description | Enum values
--- | --- | ---
codeRemoveTeamOwnersErrorCode | The error code that occurred. | CANNOT_UPDATE_SELFEXCEEDS_BATCH_LIMITFAILEDINVALID_INPUTUSER_NOT_FOUNDUSER_NOT_MEMBER_OF_TEAMVIEWERS_OR_GUESTS
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Reply

The Reply type is used as a field on updates queries and contains a set of fields to return details about the update's replies.

Fields | Description | Supported fields
--- | --- | ---
assets[Asset] | The reply's assets.Only available in versions2025-07and later. | 
bodyString! | The reply's HTML-formatted body. | 
created_atDate | The reply's creation date. | 
creatorUser | The reply's creator. | 
creator_idString | The unique identifier of the reply's creator. | 
edited_atDate! | The date the reply was edited. | 
idID! | The reply's unique identifier. | 
kindString! | The reply's kind. | 
likes[Like!]! | The reply's likes. | created_atDatecreatorUsercreator_idStringidID!reaction_typeStringupdated_atDate
pinned_to_top[UpdatePin!]! | The reply's pin to top data. | item_idID!
text_bodyString | The reply's text body. | 
updated_atDate | The reply's last updated date. | 
viewers[Watcher!]! | The reply's viewers. | mediumString!userUseruser_idID!

# Status label style

The StatusLabelStyle type is used as a field on the StatusValue implementation. It contains a set of fields that return details about the status label's style.

Field | Description
--- | ---
borderString! | The label's border Hex color code.
colorString! | The label's Hex color code.

# Time tracking history item

The TimeTrackingHistoryItem type is used as a field on the TimeTrackingValue implementation. It contains a set of fields that returns data about the time tracking column history.

Field | Description
--- | ---
created_atDate! | The date the session was added to the item.
ended_atDate | The date the session ended.
ended_user_idID | The unique identifier of the user that ended the time tracking.
idID! | The unique session identifier.
manually_entered_end_dateBoolean! | Returnstrueif the session end date was manually entered.
manually_entered_end_timeBoolean! | Returnstrueif the session end time was manually entered.
manually_entered_start_dateBoolean! | Returnstrueif the session start date was manually entered.
manually_entered_start_timeBoolean! | Returnstrueif the session start time was manually entered.
started_atDate | The date the session was started. Only applicable if the session was started by pressing the play button or through an automation.
started_user_idID | The unique identifier of the user that started the time tracking.
statusString! | The session's status.
updated_atDate | The date the session was updated.

# Update users' attributes

## User update input

The [UserUpdateInput!]! type is used as an argument on the update_multiple_users mutation and contains fields to specify what attributes to update.

Field | Description
--- | ---
user_attribute_updatesUserAttributesInput! | The attributes to update.
user_idID! | The unique identifier of the user to update.

### User attributes input

The UserAttributesInput! type contains fields to specify what attributes to update.

Field | Description
--- | ---
birthdayString | The user's updated birthday. Use YYYY-MM-DD format.
departmentString | The user's updated department.
emailString | The user's updated email.
join_dateString | The user's updated join date. Use YYYY-MM-DD format.
locationString | The user's updated location.
mobile_phoneString | The user's updated mobile phone number.
nameString | The user's updated name.
phoneString | The user's updated phone number.
titleString | The user's updated title.

## Update user attributes result

The UpdateUserAttributesResult type contains fields that show the result of updating a user's attributes through the update_multiple_users mutation.

Field | Description
--- | ---
errors[UpdateUserAttributesError!] | The errors that occurred while updating the user's attributes. Use this field to check for failed calls.
updated_users[User!] | Data from the users that were updated.

### Update user attributes error

The [UpdateUserAttributesError!] type contains a subset of fields to describe the error that occurred when an update_multiple_users mutation fails.

Field | Description | Enum values
--- | --- | ---
codeUpdateUserAttributesErrorCode | The error code. | INVALID_FIELD
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Update user's email domain

## Update email domain attributes input

The UpdateEmailDomainAttributesInput type contains fields to specify what attributes to update through the update_email_domain mutation.

Field | Description
--- | ---
new_domainString! | The updated email domain.
user_ids[ID!]! | The unique identifiers of the users to update. The maximum is 200.

## Update user's email domain result

The UpdateUsersEmailDomainResult type contains fields that show the result of updating a user's email domain through the update_email_domain mutation.

Field | Description
--- | ---
errors[UpdateEmailDomainError!] | The errors that occurred while updating the email domain. Use this field to check for failed calls.
updated_users[User!] | Data from the users that were updated.

## Update email domain error

The UpdateEmailDomainError type contains a subset of fields to describe the error that occurred when an update_email_domain mutation fails.

Field | Description | Enum values
--- | --- | ---
codeUpdateEmailDomainErrorCode | The error code that occurred. | CANNOT_UPDATE_SELFEXCEEDS_BATCH_LIMITFAILEDINVALID_INPUTUPDATE_EMAIL_DOMAIN_ERRORUSER_NOT_FOUND
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Update user's role result

The UpdateUsersRoleResult type contains fields that show the result of updating a user's role through the update_users_role mutation.

Field | Description
--- | ---
errors[UpdateUsersRoleError!] | The errors that occurred while updating the role. Use this field to check for calls that failed.
updated_users[User]! | Data from the users that were updated.

## Update user's role error

The UpdateUsersRoleError type contains a subset of fields to describe the error that occurred when an update_users_role mutation fails.

Field | Description | Enum values
--- | --- | ---
codeUpdateUsersRoleErrorCode | The error code that occurred. | CANNOT_UPDATE_SELFEXCEEDS_BATCH_LIMITFAILEDINVALID_INPUTUSER_NOT_FOUND
messageString | The error message. | 
user_idID | The unique identifier of the user that caused the error. | 

# Update workspace attributes input

The UpdateWorkspaceAttributesInput type is used as an argument on the update_workspace mutation and contains fields to specify what attributes to update.

Field | Description | Enum values
--- | --- | ---
descriptionString | The updated workspace description. | 
kindWorkspaceKind | The kind of workspace to update. | closedopen
nameString | The updated workspace name. | 

# Workspace settings

The WorkspaceSettings type is used as a field on workspaces queries. It supports one field to return data about the workspace's settings.

Field | Description | Supported fields
--- | --- | ---
iconWorkspaceIcon | The workspace's icon. | colorStringimageString

## Workspace icon

The WorkspaceIcon type is used as a field when querying a workspace's settings. It contains a set of fields that returns data about the workspace's icon.

Field | Description
--- | ---
colorString | The hex value of the icon's color. Used as a background for the image.
imageString | The temporary public image URL (valid for one hour).
