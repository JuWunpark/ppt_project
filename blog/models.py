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
from django.db import models

class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True)

    # 🔥 충돌 방지: related_name 설정 추가
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