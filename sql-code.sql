CREATE DATABASE test_db;
USE test_db;

CREATE TABLE Users (
-- column:        type:             constraints:
   id             UNIQUEIDENTIFIER  PRIMARY KEY,
   [login]        NVARCHAR(30)      NOT NULL UNIQUE,
   [password]     NVARCHAR(30)      NOT NULL,
   last_seen      DATETIME          NOT NULL DEFAULT GETDATE(),
   is_online      BIT               NOT NULL DEFAULT 1,
   color          CHAR(7)           NOT NULL
);

CREATE TABLE Contacts (
-- column:        type:             constraints:
   [user_id]      UNIQUEIDENTIFIER  FOREIGN KEY REFERENCES Users(id),
   friend_id      UNIQUEIDENTIFIER  FOREIGN KEY REFERENCES Users(id)
);

CREATE TABLE FriendRequests (
-- column:        type:             constraints:
   [from]         UNIQUEIDENTIFIER  FOREIGN KEY REFERENCES Users(id),
   [to]           UNIQUEIDENTIFIER  FOREIGN KEY REFERENCES Users(id)
);

CREATE TABLE [Messages] (
-- column:        type:             constraints:
   id             UNIQUEIDENTIFIER  PRIMARY KEY,
   [from]         UNIQUEIDENTIFIER  FOREIGN KEY REFERENCES Users(id),
   [to]           UNIQUEIDENTIFIER  FOREIGN KEY REFERENCES Users(id),
   [text]         NVARCHAR(MAX)     DEFAULT NULL,
   [image]        VARBINARY(MAX)    DEFAULT NULL,
   [date]         DATETIME          NOT NULL,
   CHECK (([text] IS NOT NULL AND [image] IS NULL) OR 
          ([text] IS NULL AND [image] IS NOT NULL))
);
