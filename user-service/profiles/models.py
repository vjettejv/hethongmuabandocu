from django.db import models


class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    auth_id = models.IntegerField(db_column="authId", unique=True)
    full_name = models.CharField(db_column="fullName", max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    avatar = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(db_column="createdAt")
    updated_at = models.DateTimeField(db_column="updatedAt")

    class Meta:
        db_table = "userprofiles"
        managed = False
