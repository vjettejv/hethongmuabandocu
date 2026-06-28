-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: post_db
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `postId` int NOT NULL,
  `imageUrl` varchar(255) DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `postId` (`postId`),
  CONSTRAINT `images_ibfk_1` FOREIGN KEY (`postId`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `images`
--

LOCK TABLES `images` WRITE;
/*!40000 ALTER TABLE `images` DISABLE KEYS */;
INSERT INTO `images` VALUES (1,1,'https://bizweb.dktcdn.net/thumb/1024x1024/100/492/434/products/screenshot-2024-09-24-155413.png?v=1727168079867','2026-05-06 20:09:15','2026-05-06 20:09:15'),(4,24,'/uploads/1775091697608-901473359.jpg','2026-05-06 20:09:15','2026-05-06 20:09:15'),(5,25,'/uploads/1775091831253-795696211.jpg','2026-05-06 20:09:15','2026-05-06 20:09:15'),(6,26,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQNF1p4JRHRKLM2hwyt66aVHq_OjZ7PZ8O__g&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(7,27,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRTaJ_MQ4DdwOwKAVNw9BYDv93xw-krDUYKag&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(8,28,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSixEHnP_m8USBtw3NaVBKff_VAuGeS9uflOg&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(9,29,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwt0lDM6X_p5MFKIAF2rnURnwI98y2z2hITw&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(10,30,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQEDOQMqH6j7S5-i_bkd2ujvq94FHkf4gQdpA&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(11,31,'https://bizweb.dktcdn.net/100/425/004/products/459335255-1738729976949638-45670-1727425534757.jpg?v=1727429639220','2026-05-06 20:09:15','2026-05-06 20:09:15'),(13,33,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaJWAPssKQTyhlvDCZNvF28NadYddbfsZ__g&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(14,34,'https://i.ytimg.com/vi/GQ58kZEadw8/maxresdefault.jpg','2026-05-06 20:09:15','2026-05-06 20:09:15'),(15,35,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS83fW8EL6bz0motSzuy6PmS4AHZ-msxPvUFg&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(16,36,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSCt-3TxQKdKNnBiBVwHQmHBMJ45IfebL7bTg&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(17,37,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSPvlRx0s8rvUUpsY0OmOPcms9SLodaAGjLgQ&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(18,38,'https://img.lazcdn.com/g/p/8cf5e7347232bc399d4b73b68cce5464.jpg_720x720q80.jpg','2026-05-06 20:09:15','2026-05-06 20:09:15'),(19,39,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRVFkQZj3eI9uJb_nSt7vuptYNxkJMGLfibnQ&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(20,40,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjHPNFE69dY8vevlBGXnZJy9_eVk0veW27Jw&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(21,41,'https://shopus.vip/wp-content/uploads/2021/04/Ao-thun-polo-nam-U.S.-Polo-Assn-form-regular-cotton-co-be-ngan-tay-mau-do-do-size-M-chinh-hang-hang-my-1.jpg','2026-05-06 20:09:15','2026-05-06 20:09:15'),(22,42,'https://kinhmateyeplus.com/wp-content/uploads/2024/11/den.jpg','2026-05-06 20:09:15','2026-05-06 20:09:15'),(23,43,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjsEUvo2rIJ2De8Q_Usc6z8b8j4l2wUoK5aw&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(25,45,'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTh0WlOyUwpounAvji7KIW99utNhRaPJTrZnQ&s','2026-05-06 20:09:15','2026-05-06 20:09:15'),(26,46,'https://picsum.photos/400/300?random=46','2026-05-06 20:09:15','2026-05-06 20:09:15'),(27,47,'https://picsum.photos/400/300?random=47','2026-05-06 20:09:15','2026-05-06 20:09:15'),(28,48,'https://picsum.photos/400/300?random=48','2026-05-06 20:09:15','2026-05-06 20:09:15'),(30,50,'https://picsum.photos/400/300?random=50','2026-05-06 20:09:15','2026-05-06 20:09:15'),(31,51,'https://picsum.photos/400/300?random=51','2026-05-06 20:09:15','2026-05-06 20:09:15'),(32,52,'https://picsum.photos/400/300?random=52','2026-05-06 20:09:15','2026-05-06 20:09:15'),(33,53,'https://picsum.photos/400/300?random=53','2026-05-06 20:09:15','2026-05-06 20:09:15'),(34,54,'https://picsum.photos/400/300?random=54','2026-05-06 20:09:15','2026-05-06 20:09:15'),(35,55,'https://picsum.photos/400/300?random=55','2026-05-06 20:09:15','2026-05-06 20:09:15');
/*!40000 ALTER TABLE `images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userId` int NOT NULL,
  `categoryId` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `price` decimal(10,2) NOT NULL,
  `status` varchar(255) DEFAULT 'available',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `condition` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `posts`
--

LOCK TABLES `posts` WRITE;
/*!40000 ALTER TABLE `posts` DISABLE KEYS */;
INSERT INTO `posts` VALUES (1,3,1,'Bàn phím Aula',NULL,650000.00,'approved','2026-04-01 13:06:21','2026-04-01 13:06:21',NULL),(24,3,3,'HOTWHEELS','Xe mô hình Hot Wheels basic \'73 Honda Civic Custom/Personnalise JBB42.',59000.00,'pending','2026-04-02 01:01:37','2026-05-07 06:59:40',NULL),(25,3,1,'Sạc dự phòng Anker','Sạc dự phòng Anker 25 000 mAh dùng được ít',500000.00,'pending','2026-04-02 01:03:51','2026-05-07 06:59:42',NULL),(26,3,1,'Tai nghe Bluetooth Hổ Vằn','Nghe nhạc hay, pin trâu 5 tiếng, dùng lướt',250000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(27,3,1,'Màn hình máy tính LG 24 inch','Không điểm chết, tần số quét 75Hz, còn hộp',1500000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(28,3,2,'Balo laptop chống nước','Chất vải xịn, nhiều ngăn, vừa laptop 15.6 inch',199000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(29,3,1,'Chuột không dây DareU','Click tĩnh âm, pin xài cả tháng chưa hết',150000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(30,3,4,'Sách \"Nhà Giả Kim\" bản bìa cứng','Sách giữ kỹ, mới đọc 1 lần, không quăn mép',60000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(31,3,2,'Áo khoác gió nam The North Face','Size L, chống nước nhẹ, mặc rất ấm',350000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(33,3,3,'Đèn bàn làm việc Xiaomi','Ánh sáng vàng bảo vệ mắt, kết nối app',400000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(34,3,3,'Quạt mini cầm tay Mute','3 cấp độ gió, có cáp sạc type-C đi kèm',80000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(35,3,1,'Bàn phím giả cơ Zero','Có LED RGB nhiều màu, gõ êm',120000.00,'approved','2026-04-02 08:08:11','2026-04-06 07:08:06',NULL),(36,3,3,'Máy xay sinh tố Philips','Xay đá tốt, cối thủy tinh dễ rửa',650000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(37,3,2,'Giày thể thao Biti\'s Hunter','Size 42, màu đen, đi cực nhẹ',450000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(38,3,4,'Truyện Doraemon trọn bộ 45 tập','Bộ truyện gắn liền tuổi thơ, giấy còn tốt',500000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(39,3,1,'Đồng hồ thông minh Huawei Band 6','Đo nhịp tim, oxy máu, pin 2 tuần',750000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(40,3,3,'Nồi chiên không dầu Lock&Lock 5L','Chiên gà, nướng thịt cực tiện, thanh lý đổi cái to hơn',900000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(41,3,2,'Áo thun polo nam','Vải cá sấu thoáng mát, mặc đi chơi đi làm đều hợp',120000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(42,3,2,'Kính râm thời trang nam','Chống tia UV, gọng nhựa dẻo nhẹ',90000.00,'approved','2026-04-02 08:08:11','2026-04-02 01:33:07',NULL),(43,3,1,'Micro thu âm Boya BY-M1','Mic cài áo, thu âm vlog chuẩn, lọc ồn',200000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(45,4,1,'Tai nghe chụp tai Havit','Bass căng, đệm tai êm không đau tai',300000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(46,4,4,'Sách \"Đắc Nhân Tâm\"','Cuốn sách nên đọc 1 lần trong đời',40000.00,'approved','2026-04-02 08:08:11','2026-04-02 08:08:11',NULL),(47,4,3,'Máy sấy tóc Sunhouse','Công suất 1500W, sấy nhanh khô',150000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:43:31',NULL),(48,3,3,'Bình giữ nhiệt Yeti 900ml','Giữ đá 12h, có nắp chống tràn và ống hút',180000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:43:29',NULL),(50,5,1,'Gậy chụp ảnh Tripod','Có remote bluetooth, kéo dài 1m',65000.00,'approved','2026-04-02 08:08:11','2026-05-07 07:00:06',NULL),(51,4,2,'Áo len nữ dáng rộng','Phong cách Hàn Quốc, len mềm không dặm',160000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:43:13',NULL),(52,4,2,'Vali du lịch size 20','Chất liệu nhựa ABS chịu va đập, size xách tay',380000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:43:11',NULL),(53,4,1,'Sạc laptop Dell kim nhỏ','Sạc zin theo máy, 65W',250000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:42:59',NULL),(54,4,1,'Tấm hắt sáng chụp ảnh','Hắt sáng 2 mặt bạc/vàng, gấp gọn được',85000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:43:01',NULL),(55,4,3,'Bộ nồi inox 3 đáy','Dùng được bếp từ, truyền nhiệt nhanh',450000.00,'pending','2026-04-02 08:08:11','2026-04-02 03:43:03',NULL),(59,10,1,'Test post','Test description',1000.00,'available','2026-05-08 07:15:41','2026-05-08 07:15:41','Mới'),(60,10,1,'Test post 2','Test description 2',2000.00,'available','2026-05-08 07:16:41','2026-05-08 07:16:41','Mới'),(61,1,1,'test','test desc',1000.00,'available','2026-05-08 07:31:10','2026-05-08 07:31:10',NULL);
/*!40000 ALTER TABLE `posts` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-08 14:23:10
