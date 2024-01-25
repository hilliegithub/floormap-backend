CREATE USER 'floormap_db_user'@'localhost' identified by '123456';

CREATE DATABASE floormap;

GRANT ALL PRIVILEGES ON floormap.* TO 'floormap_db_user'@'localhost';

USE floormap;

CREATE TABLE request (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    floormapname VARCHAR(255) NOT NULL,
    mappingfileAwsKey VARCHAR(255)
);