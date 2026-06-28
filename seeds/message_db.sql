-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: message_db
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
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `senderId` int NOT NULL,
  `receiverId` int NOT NULL,
  `content` text NOT NULL,
  `isRead` tinyint(1) DEFAULT '0',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (10,3,4,'hello hàng còn bán k bạn',0,'2026-04-02 04:16:27','2026-04-02 04:16:27'),(11,3,4,'ảo',0,'2026-04-06 07:01:36','2026-04-06 07:01:36'),(12,4,3,'1',0,'2026-04-06 07:01:54','2026-04-06 07:01:54'),(13,5,3,'hi bạn còn sản phẩm này không',0,'2026-04-07 14:29:26','2026-04-07 14:29:26'),(14,6,4,'bạn còn bán sách không nhỉ',0,'2026-04-08 15:18:10','2026-04-08 15:18:10'),(15,6,5,'hi bạn còn đồ này k',0,'2026-04-08 15:20:32','2026-04-08 15:20:32'),(16,6,5,'hi',0,'2026-04-08 15:32:52','2026-04-08 15:32:52'),(17,5,6,'còn bạn ơi',0,'2026-04-08 15:39:56','2026-04-08 15:39:56'),(20,5,6,'hello',0,'2026-04-15 20:32:58','2026-04-15 20:32:58'),(21,5,6,'bạn có vui không',0,'2026-04-15 20:33:10','2026-04-15 20:33:10'),(22,6,5,'có bạn e',0,'2026-04-15 20:35:15','2026-04-15 20:35:15'),(23,6,5,'có bạn e',0,'2026-04-15 20:35:15','2026-04-15 20:35:15'),(24,6,5,'khoẻ bạn ơi',0,'2026-04-15 20:35:27','2026-04-15 20:35:27'),(25,6,5,'khoẻ bạn ơi',0,'2026-04-15 20:35:27','2026-04-15 20:35:27'),(27,5,6,'hihi',0,'2026-04-15 20:43:37','2026-04-15 20:43:37'),(28,5,6,'hi',0,'2026-04-15 20:43:38','2026-04-15 20:43:38'),(29,5,6,'hi',0,'2026-04-15 20:43:38','2026-04-15 20:43:38'),(30,5,6,'hi',0,'2026-04-15 20:43:39','2026-04-15 20:43:39'),(36,5,4,'chào admin',0,'2026-04-15 20:57:15','2026-04-15 20:57:15'),(37,5,4,'chào admin',0,'2026-04-15 20:57:15','2026-04-15 20:57:15'),(38,5,4,'có hỗ trợ không',0,'2026-04-15 20:57:44','2026-04-15 20:57:44'),(39,5,4,'có hỗ trợ không',0,'2026-04-15 20:57:44','2026-04-15 20:57:44'),(40,4,4,'admin',0,'2026-04-15 20:59:54','2026-04-15 20:59:54'),(41,4,4,'admin',0,'2026-04-15 20:59:54','2026-04-15 20:59:54'),(42,4,4,'a',0,'2026-04-15 20:59:57','2026-04-15 20:59:57'),(43,4,4,'a',0,'2026-04-15 20:59:57','2026-04-15 20:59:57'),(44,5,4,'hello',0,'2026-04-15 21:00:16','2026-04-15 21:00:16'),(45,5,4,'hello',0,'2026-04-15 21:00:16','2026-04-15 21:00:16'),(46,5,4,'a',0,'2026-04-15 21:07:29','2026-04-15 21:07:29'),(47,5,4,'a',0,'2026-04-15 21:07:29','2026-04-15 21:07:29'),(48,4,4,'hello',0,'2026-05-07 06:18:46','2026-05-07 06:18:46'),(49,5,4,'aloo',0,'2026-05-07 06:18:54','2026-05-07 06:18:54'),(50,4,5,'alo',0,'2026-05-07 06:19:32','2026-05-07 06:19:32'),(51,3,5,'còn bạn ê',0,'2026-05-07 06:20:14','2026-05-07 06:20:14'),(52,5,3,'bao nhiêu tiền vậy bạn',0,'2026-05-07 06:20:58','2026-05-07 06:20:58'),(53,5,4,'hi',0,'2026-05-08 12:22:55','2026-05-08 12:22:55'),(54,5,4,'tôi cần hỗ trợ',0,'2026-05-08 12:23:58','2026-05-08 12:23:58'),(55,5,4,'duyệt bài cho tôi đi',0,'2026-05-08 12:24:18','2026-05-08 12:24:18'),(56,5,4,'alo',0,'2026-05-08 12:25:47','2026-05-08 12:25:47'),(57,4,5,'hi',0,'2026-05-08 12:26:04','2026-05-08 12:26:04'),(58,4,5,'hi',0,'2026-05-08 12:26:34','2026-05-08 12:26:34'),(59,4,5,'hi',0,'2026-05-08 12:26:45','2026-05-08 12:26:45'),(60,5,4,'alo',0,'2026-05-08 12:26:53','2026-05-08 12:26:53'),(61,4,5,'hi',0,'2026-05-08 12:29:26','2026-05-08 12:29:26'),(62,5,4,'hello',0,'2026-05-08 12:38:00','2026-05-08 12:38:00'),(63,5,4,'hi',0,'2026-05-08 12:38:08','2026-05-08 12:38:08'),(64,4,5,'alo',0,'2026-05-08 12:38:15','2026-05-08 12:38:15'),(65,5,4,'hi',0,'2026-05-08 12:48:07','2026-05-08 12:48:07'),(66,5,4,'alo',0,'2026-05-08 12:48:26','2026-05-08 12:48:26'),(67,5,3,'em muốn mua',0,'2026-05-08 14:20:50','2026-05-08 14:20:50'),(68,5,3,'Chào bạn, mình quan tâm đến sản phẩm:\n[Bàn phím Aula]\n(http://localhost/post/1)',0,'2026-05-08 14:21:09','2026-05-08 14:21:09');
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userId` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `isRead` tinyint(1) DEFAULT '0',
  `link` varchar(255) DEFAULT NULL,
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,5,'Bài viết đã được duyệt','Bài viết \"a\" của bạn đã được hiển thị trên chợ.',1,NULL,'2026-05-08 12:49:15','2026-05-08 12:49:17');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
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
