-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: auth_db
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
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `roleId` int DEFAULT '1',
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `isVerified` tinyint(1) DEFAULT '0',
  `createdAt` datetime NOT NULL,
  `updatedAt` datetime NOT NULL,
  `otp` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `username_2` (`username`),
  UNIQUE KEY `email_2` (`email`),
  UNIQUE KEY `username_3` (`username`),
  UNIQUE KEY `email_3` (`email`),
  UNIQUE KEY `username_4` (`username`),
  UNIQUE KEY `email_4` (`email`),
  UNIQUE KEY `username_5` (`username`),
  UNIQUE KEY `email_5` (`email`),
  UNIQUE KEY `username_6` (`username`),
  UNIQUE KEY `email_6` (`email`),
  UNIQUE KEY `username_7` (`username`),
  UNIQUE KEY `email_7` (`email`),
  UNIQUE KEY `username_8` (`username`),
  UNIQUE KEY `email_8` (`email`),
  UNIQUE KEY `username_9` (`username`),
  UNIQUE KEY `email_9` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (3,1,'vietdeptrai','nguyenhaducviet.02@gmail.com','$2b$10$.Roo5WLpG85SqRthtW6OyOpZDxm8VZElySKBLVKqpIVu1OXXgiDuO',0,'2026-04-01 20:51:10','2026-04-01 20:51:10',NULL),(4,2,'admin','kengamer2k5@gmail.com','$2b$10$fdR2a69luxHyr6grgK1/eecq27tLclyCAnb9mTq.94H0j.oI5IvxS',0,'2026-04-01 21:08:38','2026-04-01 21:08:38',NULL),(5,1,'viet','chipxinhgaiii@gmail.com','$2b$10$.Roo5WLpG85SqRthtW6OyOpZDxm8VZElySKBLVKqpIVu1OXXgiDuO',0,'2026-04-02 00:32:25','2026-04-08 15:38:59',NULL),(6,1,'chip','kengamer2k5cn@gmail.com','$2b$10$qkhQ.8ZGAyarkC7ELMBO/OWEZepJmlGw2gERbPyYnnLtcb2t2B1M6',1,'2026-04-07 14:49:25','2026-04-07 14:51:30',NULL),(7,1,'haviet','tonhanh1945@gmail.com','$2b$10$e6RGH2E0kn2sV68zXjWrveNZq3hPdOSkOHYdD1BJpWU4rPZ4qA81e',0,'2026-04-09 02:28:52','2026-04-09 02:28:52',NULL),(8,1,'quynh','quynhdo25112005@gmail.com','$2b$10$cMm3d9H3uKt4324MUfExUuV7d8ZiR1Mh.Nl/1LLHMZVd9VpnKq0J2',1,'2026-04-09 02:33:23','2026-04-09 02:33:43',NULL),(9,1,'ngocanh','ngoccanhh26100@gmail.com','$2a$10$mZj5Z9iB0GeTFYYBlWL5Wu0n97SDYs4B2a2StqyKxGdHRFQUFmyRS',0,'2026-05-08 06:33:54','2026-05-08 06:33:54',NULL),(10,1,'testuser123','test.docu.2026@gmail.com','$2a$10$w99YhwPKdCo.NDOe6BIZzuRFEG/i7ILhsqP1Yb2JNlUscT.qhfH56',0,'2026-05-08 06:52:32','2026-05-08 06:52:32','944064');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-08 14:22:56
