from django.contrib.auth import get_user_model
from django.db import models
from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

from utils.tools import RandomStr


def upload_file(instance, filename):
    return '/'.join(
        ['files', instance.meeting.title, instance.user.name + '上传-' + filename])


def upload_feature_file(instance, filename):
    username = UserProfile.objects.filter(empno=instance.empno).first().name
    return '/'.join(
        ['feature_files', username, username + "-" + str(instance.empno) + ".data"])


def upload_image(instance, filename):
    return '/'.join(
        ['head_img', instance.username, RandomStr(4) + '-' + filename])


def upload_image_chamber(instance, filename):
    return '/'.join(
        ['chamber_img', instance.name, instance.host.name + '-' + filename])


def upload_voices_file(instance, filename):
    return '/'.join(
        ['voices', instance.meeting.title, instance.user.name, filename])


class Department(models.Model):
    """
    部门
    """
    name = models.CharField(max_length=30, null=True, blank=True, verbose_name="部门名字")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门列表"


class UserProfile(AbstractUser):
    """
    员工用户
    """
    SEX = (
        ("男", "男"),
        ("女", "女")
    )
    name = models.CharField(max_length=30, verbose_name="姓名")
    sex = models.CharField(max_length=10, choices=SEX, default="男", verbose_name="性别")
    department = models.ManyToManyField(Department, verbose_name="选择部门")
    job = models.CharField(max_length=20, verbose_name="职位")
    empno = models.CharField(max_length=20, verbose_name="员工号", unique=True)
    head_img = models.ImageField(upload_to=upload_image, default="/head_img/default_head_img.jpg", blank=True,
                                 null=True,
                                 verbose_name="用户头像")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    # is_staff = models.BooleanField(
    #     _('权限状态'),
    #     # default=False,
    #     help_text=_('Designates whether the user can log into this admin site.'),
    # )

    class Meta:
        verbose_name = "员工"
        verbose_name_plural = "员工列表"

    def __str__(self):
        return self.name if self.name else self.username


class UserArcFace(models.Model):
    """
    用于虹软人脸识别
    """
    empno = models.CharField(max_length=50, db_column="empno", verbose_name="绑定用户的员工号")
    feature_file = models.FileField(upload_to=upload_feature_file, verbose_name="特征值存储文件")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "虹软识别"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.empno
