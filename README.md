## Overview
This repository contains the code for a discussion application developed as a part of a university course project. The app facilitates the creation and interaction within various discussion areas based on different topics. Each area contains threads, which in turn consist of messages. Users can either be administrators or basic users, with administrators having additional privileges.

## Features

### User Account Management
- **User Registration:** Allows new users to create an account.
- **Login/Logout:** Users can log in to access the application and log out after they're done.

### Discussion Areas
- **Viewing Areas:** Users can see a list of all discussion areas on the homepage along with the number of threads and messages in each area, and the timestamp of the last message sent.
- **Thread Creation:** Users can create a new thread in an area by providing a thread title and the content of the initial message.

### Messaging
- **Posting Messages:** Users can write a new message in an existing thread.
- **Editing Content:** Users have the ability to edit the titles of threads they've created and the content of their messages. They can also delete a thread or a message.
- **Search Functionality:** Users can search for all messages containing a specified word.

### Administration
- **Area Management:** Administrators have the capability to add and remove discussion areas.
- **Secret Areas:** Administrators can create secret areas and designate which users have access to these areas.
