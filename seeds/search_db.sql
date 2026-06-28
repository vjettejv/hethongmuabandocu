-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: search_db
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
-- Table structure for table `searchindices`
--

DROP TABLE IF EXISTS `searchindices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `searchindices` (
  `postId` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `price` decimal(10,2) DEFAULT NULL,
  `categoryId` int DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `imageUrl` varchar(255) DEFAULT NULL,
  `categoryName` varchar(255) DEFAULT NULL,
  `status` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`postId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `searchindices`
--

LOCK TABLES `searchindices` WRITE;
/*!40000 ALTER TABLE `searchindices` DISABLE KEYS */;
INSERT INTO `searchindices` VALUES (1,'Bàn phím Aula',NULL,650000.00,1,'2026-05-07 07:25:24','2026-05-07 07:25:24','https://bizweb.dktcdn.net/thumb/1024x1024/100/492/434/products/screenshot-2024-09-24-155413.png?v=1727168079867','Đồ điện tử','approved'),(26,'Tai nghe Bluetooth Hổ Vằn','Nghe nhạc hay, pin trâu 5 tiếng, dùng lướt',250000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQNF1p4JRHRKLM2hwyt66aVHq_OjZ7PZ8O__g&s','Đồ điện tử','approved'),(27,'Màn hình máy tính LG 24 inch','Không điểm chết, tần số quét 75Hz, còn hộp',1500000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRTaJ_MQ4DdwOwKAVNw9BYDv93xw-krDUYKag&s','Đồ điện tử','approved'),(28,'Balo laptop chống nước','Chất vải xịn, nhiều ngăn, vừa laptop 15.6 inch',199000.00,2,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSixEHnP_m8USBtw3NaVBKff_VAuGeS9uflOg&s','Thời trang','approved'),(29,'Chuột không dây DareU','Click tĩnh âm, pin xài cả tháng chưa hết',150000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwt0lDM6X_p5MFKIAF2rnURnwI98y2z2hITw&s','Đồ điện tử','approved'),(30,'Sách \"Nhà Giả Kim\" bản bìa cứng','Sách giữ kỹ, mới đọc 1 lần, không quăn mép',60000.00,4,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQEDOQMqH6j7S5-i_bkd2ujvq94FHkf4gQdpA&s','Giải trí','approved'),(31,'Áo khoác gió nam The North Face','Size L, chống nước nhẹ, mặc rất ấm',350000.00,2,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://bizweb.dktcdn.net/100/425/004/products/459335255-1738729976949638-45670-1727425534757.jpg?v=1727429639220','Thời trang','approved'),(33,'Đèn bàn làm việc Xiaomi','Ánh sáng vàng bảo vệ mắt, kết nối app',400000.00,3,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaJWAPssKQTyhlvDCZNvF28NadYddbfsZ__g&s','Đồ gia dụng','approved'),(34,'Quạt mini cầm tay Mute','3 cấp độ gió, có cáp sạc type-C đi kèm',80000.00,3,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://i.ytimg.com/vi/GQ58kZEadw8/maxresdefault.jpg','Đồ gia dụng','approved'),(35,'Bàn phím giả cơ Zero','Có LED RGB nhiều màu, gõ êm',120000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS83fW8EL6bz0motSzuy6PmS4AHZ-msxPvUFg&s','Đồ điện tử','approved'),(36,'Máy xay sinh tố Philips','Xay đá tốt, cối thủy tinh dễ rửa',650000.00,3,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSCt-3TxQKdKNnBiBVwHQmHBMJ45IfebL7bTg&s','Đồ gia dụng','approved'),(37,'Giày thể thao Biti\'s Hunter','Size 42, màu đen, đi cực nhẹ',450000.00,2,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSPvlRx0s8rvUUpsY0OmOPcms9SLodaAGjLgQ&s','Thời trang','approved'),(38,'Truyện Doraemon trọn bộ 45 tập','Bộ truyện gắn liền tuổi thơ, giấy còn tốt',500000.00,4,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://img.lazcdn.com/g/p/8cf5e7347232bc399d4b73b68cce5464.jpg_720x720q80.jpg','Giải trí','approved'),(39,'Đồng hồ thông minh Huawei Band 6','Đo nhịp tim, oxy máu, pin 2 tuần',750000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRVFkQZj3eI9uJb_nSt7vuptYNxkJMGLfibnQ&s','Đồ điện tử','approved'),(40,'Nồi chiên không dầu Lock&Lock 5L','Chiên gà, nướng thịt cực tiện, thanh lý đổi cái to hơn',900000.00,3,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjHPNFE69dY8vevlBGXnZJy9_eVk0veW27Jw&s','Đồ gia dụng','approved'),(41,'Áo thun polo nam','Vải cá sấu thoáng mát, mặc đi chơi đi làm đều hợp',120000.00,2,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://shopus.vip/wp-content/uploads/2021/04/Ao-thun-polo-nam-U.S.-Polo-Assn-form-regular-cotton-co-be-ngan-tay-mau-do-do-size-M-chinh-hang-hang-my-1.jpg','Thời trang','approved'),(42,'Kính râm thời trang nam','Chống tia UV, gọng nhựa dẻo nhẹ',90000.00,2,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://kinhmateyeplus.com/wp-content/uploads/2024/11/den.jpg','Thời trang','approved'),(43,'Micro thu âm Boya BY-M1','Mic cài áo, thu âm vlog chuẩn, lọc ồn',200000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjsEUvo2rIJ2De8Q_Usc6z8b8j4l2wUoK5aw&s','Đồ điện tử','approved'),(45,'Tai nghe chụp tai Havit','Bass căng, đệm tai êm không đau tai',300000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTh0WlOyUwpounAvji7KIW99utNhRaPJTrZnQ&s','Đồ điện tử','approved'),(46,'Sách \"Đắc Nhân Tâm\"','Cuốn sách nên đọc 1 lần trong đời',40000.00,4,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://picsum.photos/400/300?random=46','Giải trí','approved'),(49,'Bộ lego lắp ráp xe đua','Gồm 500 chi tiết, rèn luyện trí tuệ',220000.00,3,'2026-05-08 12:28:15','2026-05-08 14:17:08',NULL,'Đồ gia dụng','deleted'),(50,'Gậy chụp ảnh Tripod','Có remote bluetooth, kéo dài 1m',65000.00,1,'2026-05-07 07:25:25','2026-05-07 07:25:25','https://picsum.photos/400/300?random=50','Đồ điện tử','approved'),(59,'Test post','Test description',1000.00,1,'2026-05-08 07:15:41','2026-05-08 07:15:41',NULL,'Đồ điện tử','available'),(60,'Test post 2','Test description 2',2000.00,1,'2026-05-08 07:16:41','2026-05-08 07:16:41',NULL,'Đồ điện tử','available'),(61,'test','test desc',1000.00,1,'2026-05-08 07:31:10','2026-05-08 07:31:10',NULL,'Đồ điện tử','available'),(62,'hảo','a',12333.00,1,'2026-05-08 07:36:22','2026-05-08 07:36:22','/uploads/1778225782640-screencapture-127-0-0-1-5500-bangduliet-html-2026-04-21-02_46_13.png','Đồ điện tử','available'),(63,'a','aa',123.00,2,'2026-05-08 07:51:36','2026-05-08 07:51:36','/uploads/1778226695859-screencapture-127-0-0-1-5500-bangduliet-html-2026-04-21-02_46_13.png','Thời trang','available'),(64,'a','ádas',12231.00,2,'2026-05-08 12:49:06','2026-05-08 12:49:22','/uploads/1778244546250-screencapture-127-0-0-1-5500-bangduliet-html-2026-04-21-02_46_13.png','Thời trang','pending');
/*!40000 ALTER TABLE `searchindices` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-08 14:23:45
