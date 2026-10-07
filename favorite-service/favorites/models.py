from django.db import models


class Favorite(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    userId = models.IntegerField(db_column="userId")
    postId = models.IntegerField(db_column="postId")
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        db_table = "favorites"
        managed = False
        unique_together = (("userId", "postId"),)
