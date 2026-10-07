from django.db import models


class Review(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    reviewerId = models.IntegerField(db_column="reviewerId")
    revieweeId = models.IntegerField(db_column="revieweeId")
    postId = models.IntegerField(db_column="postId", null=True)
    rating = models.IntegerField(db_column="rating")
    comment = models.TextField(db_column="comment", null=True)
    imageUrl = models.CharField(db_column="imageUrl", max_length=255, null=True)
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        db_table = "reviews"
        managed = False
