# from django.contrib.auth.models import AbstractUser
# from django.db import models
#
# class CustomUser(AbstractUser):
#     email = models.EmailField(unique=True) #이메일중복방지,데이터 덮어씌우기 방지
#     nickname = models.CharField(max_length=50, unique=True)
#
#
#     def __str__(self):
#         return self.username

from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_set",  # 기존 'user_set'과 충돌 방지
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions_set",  # 기존 'user_set'과 충돌 방지
        blank=True
    )

    def __str__(self):
        return self.username

class UserHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ppt_title = models.CharField(max_length=500)
    ppt_url = models.CharField(max_length=500)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ppt_url}"