CREATE DATABASE IF NOT EXISTS auth_db;
USE auth_db;

CREATE TABLE IF NOT EXISTS Users (
  id int NOT NULL AUTO_INCREMENT,
  roleId int DEFAULT '1',
  username varchar(255) NOT NULL,
  email varchar(255) NOT NULL,
  password varchar(255) NOT NULL,
  PRIMARY KEY (id)
);

INSERT INTO Users (id, roleId, username, email, password) VALUES (1, 2, 'admin', 'admin@gmail.com', 'admin_hashed');