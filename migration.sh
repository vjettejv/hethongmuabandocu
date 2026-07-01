#!/bin/bash
set -e

echo "1. Recreating temp_db..."
mysql -uroot -proot -e "DROP DATABASE IF EXISTS temp_db; CREATE DATABASE temp_db;"

echo "2. Importing docu_db (1).sql into temp_db..."
mysql -uroot -proot temp_db < /tmp/docu_db.sql

echo "3. Creating mapping tables..."
mysql -uroot -proot temp_db -e "
CREATE TABLE temp_auth_users AS SELECT id, roleId, username, email, password, isVerified, createdAt, updatedAt FROM users;
CREATE TABLE temp_user_UserProfiles AS SELECT id, id as authId, fullName, phone, address, NULL as avatar, createdAt, updatedAt FROM users;
CREATE TABLE temp_cat_categories AS SELECT id, name, description, NOW() as createdAt, NOW() as updatedAt FROM categories;
CREATE TABLE temp_post_Posts AS SELECT id, userId, categoryId, title, description, price, status, createdAt, updatedAt FROM posts;
CREATE TABLE temp_post_Images AS SELECT id, postId, imageUrl, NOW() as createdAt, NOW() as updatedAt FROM images WHERE postId IS NOT NULL;
CREATE TABLE temp_msg_Messages AS SELECT id, senderId, receiverId, content, createdAt, updatedAt FROM messages;
"

echo "4. Dumping and transforming tables..."
mysqldump -uroot -proot temp_db temp_auth_users --no-create-info --complete-insert --skip-add-drop-table | sed -e 's/`temp_auth_users`/`Users`/g' -e 's/`temp_auth_Users`/`Users`/g' > /tmp/auth.sql
mysqldump -uroot -proot temp_db temp_user_userprofiles --no-create-info --complete-insert --skip-add-drop-table | sed -e 's/`temp_user_userprofiles`/`UserProfiles`/g' -e 's/`temp_user_UserProfiles`/`UserProfiles`/g' > /tmp/user.sql
mysqldump -uroot -proot temp_db temp_cat_categories --no-create-info --complete-insert --skip-add-drop-table | sed -e 's/`temp_cat_categories`/`Categories`/g' -e 's/`temp_cat_Categories`/`Categories`/g' > /tmp/cat.sql
mysqldump -uroot -proot temp_db temp_post_posts --no-create-info --complete-insert --skip-add-drop-table | sed -e 's/`temp_post_posts`/`Posts`/g' -e 's/`temp_post_Posts`/`Posts`/g' > /tmp/post.sql
mysqldump -uroot -proot temp_db temp_post_images --no-create-info --complete-insert --skip-add-drop-table | sed -e 's/`temp_post_images`/`Images`/g' -e 's/`temp_post_Images`/`Images`/g' > /tmp/img.sql
mysqldump -uroot -proot temp_db temp_msg_messages --no-create-info --complete-insert --skip-add-drop-table | sed -e 's/`temp_msg_messages`/`Messages`/g' -e 's/`temp_msg_Messages`/`Messages`/g' > /tmp/msg.sql

echo "5. Truncating target tables..."
mysql -h auth-db -uroot -proot auth_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Users;"
mysql -h user-db -uroot -proot user_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE UserProfiles;"
mysql -h category-db -uroot -proot category_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Categories;"
mysql -h post-db -uroot -proot post_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Images; TRUNCATE TABLE Posts;"
mysql -h message-db -uroot -proot message_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Messages;"

echo "6. Importing to Microservices..."
mysql -h auth-db -uroot -proot auth_db < /tmp/auth.sql
mysql -h user-db -uroot -proot user_db < /tmp/user.sql
mysql -h category-db -uroot -proot category_db < /tmp/cat.sql
mysql -h post-db -uroot -proot post_db < /tmp/post.sql
mysql -h post-db -uroot -proot post_db < /tmp/img.sql
mysql -h message-db -uroot -proot message_db < /tmp/msg.sql

echo "7. Cleanup..."
mysql -uroot -proot -e "DROP DATABASE temp_db;"
rm /tmp/*.sql

echo "Migration completed successfully!"
