from django.db import models


class AuthUser(models.Model):
    id = models.AutoField(primary_key=True)
    role_id = models.IntegerField(db_column="roleId", default=1, null=True)
    username = models.CharField(max_length=255, unique=True)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_verified = models.BooleanField(db_column="isVerified", default=False, null=True)
    otp = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(db_column="createdAt")
    updated_at = models.DateTimeField(db_column="updatedAt")

    class Meta:
        db_table = "users"
        managed = False
