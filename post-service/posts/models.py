from django.db import models


class Post(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã duyệt"
        REJECTED = "rejected", "Từ chối"

    id = models.AutoField(primary_key=True, db_column="id")
    userId = models.IntegerField(db_column="userId")
    categoryId = models.IntegerField(db_column="categoryId")
    title = models.CharField(max_length=255, db_column="title")
    description = models.TextField(null=True, db_column="description")
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column="price")
    condition = models.CharField(max_length=255, null=True, db_column="condition")
    status = models.CharField(
        max_length=255, choices=Status.choices, default=Status.PENDING, db_column="status"
    )
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        managed = False
        db_table = "posts"


class Image(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    post = models.ForeignKey(Post, models.DO_NOTHING, db_column="postId", related_name="Images")
    imageUrl = models.CharField(max_length=255, null=True, db_column="imageUrl")
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        managed = False
        db_table = "images"
