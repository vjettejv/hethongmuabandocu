from django.db import models


class SearchIndex(models.Model):
    postId = models.IntegerField(primary_key=True, db_column="postId")
    title = models.CharField(max_length=255, db_column="title")
    description = models.TextField(null=True, db_column="description")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, db_column="price")
    categoryId = models.IntegerField(null=True, db_column="categoryId")
    imageUrl = models.CharField(max_length=255, null=True, db_column="imageUrl")
    categoryName = models.CharField(max_length=255, null=True, db_column="categoryName")
    status = models.CharField(max_length=255, null=True, db_column="status")
    createdAt = models.DateTimeField(db_column="createdAt")
    updatedAt = models.DateTimeField(db_column="updatedAt")

    class Meta:
        db_table = "searchindices"
        managed = False
