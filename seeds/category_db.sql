CREATE DATABASE IF NOT EXISTS category_db;
USE category_db;

CREATE TABLE IF NOT EXISTS Categories (
  id int NOT NULL AUTO_INCREMENT,
  name varchar(255) NOT NULL,
  parentId int DEFAULT NULL,
  PRIMARY KEY (id)
);

INSERT INTO Categories (id, name, parentId) VALUES (1, 'Electronics', NULL), (2, 'Phones', 999);