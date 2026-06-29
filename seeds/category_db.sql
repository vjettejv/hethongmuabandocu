CREATE DATABASE IF NOT EXISTS category_db;
USE category_db;

CREATE TABLE IF NOT EXISTS Categories (
  id int NOT NULL AUTO_INCREMENT,
  name varchar(255) NOT NULL,
  PRIMARY KEY (id)
);