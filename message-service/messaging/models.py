from django.db import models


class Message(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    senderId = models.IntegerField(db_column="senderId")
    receiverId = models.IntegerField(db_column="receiverId")
    content = models.TextField(db_column="content")
    isRead = models.BooleanField(db_column="isRead", null=True, default=False)
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        managed = False
        db_table = "messages"


class Notification(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    userId = models.IntegerField(db_column="userId")
    title = models.CharField(max_length=255, db_column="title")
    message = models.TextField(db_column="message")
    isRead = models.BooleanField(db_column="isRead", null=True, default=False)
    link = models.CharField(max_length=255, db_column="link", null=True)
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        managed = False
        db_table = "notifications"
