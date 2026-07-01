# Tạo CSDL tạm thời
docker exec -i do-cu-search-db mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS temp_db;"

# Import file SQL cũ vào CSDL tạm
docker cp "d:\workspacecuachjp\KienTrucPM\docu_db (1).sql" do-cu-search-db:/tmp/docu_db.sql
docker exec -i do-cu-search-db sh -c "mysql -uroot -proot temp_db < /tmp/docu_db.sql"

# Làm sạch các CSDL của Microservices
docker exec -i do-cu-auth-db mysql -uroot -proot auth_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Users;"
docker exec -i do-cu-user-db mysql -uroot -proot user_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE UserProfiles;"
docker exec -i do-cu-post-db mysql -uroot -proot post_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Posts; TRUNCATE TABLE Images;"
docker exec -i do-cu-category-db mysql -uroot -proot category_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Categories;"
docker exec -i do-cu-message-db mysql -uroot -proot message_db -e "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE Messages;"

# Migrate dữ liệu sang Auth DB
docker exec -i do-cu-search-db mysql -h auth-db -uroot -proot auth_db -e "INSERT INTO Users (id, roleId, username, password, email, isVerified, createdAt, updatedAt) SELECT id, roleId, username, password, email, isVerified, createdAt, updatedAt FROM temp_db.users;"

# Migrate dữ liệu sang User DB
docker exec -i do-cu-search-db mysql -h user-db -uroot -proot user_db -e "INSERT INTO UserProfiles (authId, fullName, phone, address, createdAt, updatedAt) SELECT id, fullName, phone, address, createdAt, updatedAt FROM temp_db.users;"

# Migrate dữ liệu sang Category DB (Bỏ parentId do cấu hình bảng Categories mới không sử dụng cột này)
docker exec -i do-cu-search-db mysql -h category-db -uroot -proot category_db -e "INSERT INTO Categories (id, name, description, createdAt, updatedAt) SELECT id, name, description, NOW(), NOW() FROM temp_db.categories;"

# Migrate dữ liệu sang Post DB (Posts)
docker exec -i do-cu-search-db mysql -h post-db -uroot -proot post_db -e "INSERT INTO Posts (id, userId, categoryId, title, description, price, status, createdAt, updatedAt) SELECT id, userId, categoryId, title, description, price, status, createdAt, updatedAt FROM temp_db.posts;"

# Migrate dữ liệu sang Post DB (Images - Sửa cột url thành imageUrl để khớp với schema bảng Images)
docker exec -i do-cu-search-db mysql -h post-db -uroot -proot post_db -e "INSERT INTO Images (id, postId, imageUrl, createdAt, updatedAt) SELECT id, postId, imageUrl, NOW(), NOW() FROM temp_db.images WHERE postId IS NOT NULL;"

# Migrate dữ liệu sang Message DB
docker exec -i do-cu-search-db mysql -h message-db -uroot -proot message_db -e "INSERT INTO Messages (id, senderId, receiverId, content, createdAt, updatedAt) SELECT id, senderId, receiverId, content, createdAt, updatedAt FROM temp_db.messages;"

# Dọn dẹp CSDL tạm
docker exec -i do-cu-search-db mysql -uroot -proot -e "DROP DATABASE temp_db;"

echo "Migration hoàn tất!"
