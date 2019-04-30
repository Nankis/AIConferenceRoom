from datetime import datetime

from django.db import models

from user.models import UserProfile, upload_file, upload_image_chamber, upload_voices_file


class Equipment(models.Model):
    """
    设备表
    """
    name = models.CharField(max_length=30, verbose_name="设备名称")
    num = models.IntegerField(default=0, verbose_name="设备数量")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = '设备'
        verbose_name_plural = '设备列表'

    def __str__(self):
        return self.name


class Chamber(models.Model):
    """
    会议室
    """
    name = models.CharField(max_length=30, verbose_name="会议室名称")
    address = models.CharField(max_length=30, verbose_name="会议室地点")
    space = models.IntegerField(default=0, verbose_name="可容纳人数")
    host = models.ForeignKey(UserProfile, verbose_name="负责人", db_column="host", default=1)
    equipment = models.ManyToManyField(Equipment, verbose_name="所拥有设备", null=True, blank=True)
    chamber_img = models.ImageField(upload_to=upload_image_chamber, default="/chamber_img/default_chamber_img.jpg",
                                    blank=True,
                                    null=True,
                                    verbose_name="会议室图片")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = '会议室'
        verbose_name_plural = '会议室列表'

    def __str__(self):
        return self.name


class ApplyMeeting(models.Model):
    """
    申请预定会议
    """
    title = models.CharField(max_length=30, verbose_name="会议主题")
    chamber = models.ForeignKey(Chamber, db_column="chamber", verbose_name="会议室")
    speaker = models.ForeignKey(UserProfile, verbose_name="主讲人", db_column="speaker", related_name="speaker_user")
    joins = models.ManyToManyField(UserProfile, verbose_name="参与人", related_query_name="join_user")
    start = models.DateTimeField(verbose_name="开始时间")
    end = models.DateTimeField(verbose_name="结束时间")
    remark = models.TextField(max_length=500, verbose_name="会议备注", null=True, blank=True)
    pubuser = models.ForeignKey(UserProfile, db_column="pubuser", verbose_name="会议发起人", related_name="pub_user")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = '预定会议'
        verbose_name_plural = '预定会议列表'

    def __str__(self):
        return self.title


class UserUploadFile(models.Model):
    """
    用户上传共享的文件
    """
    user = models.ForeignKey(UserProfile, verbose_name="上传的用户")
    file = models.FileField(upload_to=upload_file, verbose_name="上传的文件", help_text="上传的文件")
    file_name = models.CharField(max_length=100, default=file.name, null=True, blank=True, verbose_name="文件名字")
    meeting = models.ForeignKey(ApplyMeeting, verbose_name="对应会议")
    file_size = models.CharField(max_length=50, null=True, blank=True, verbose_name="文件大小")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "用户上传的文件"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file if self.file else self.user.name + "上传的文件"


class Messages(models.Model):
    """
    会议预定---创建,修改,删除时的消息通知
    """
    title = models.CharField(max_length=50, verbose_name="消息主题", null=True, blank=True)
    user = models.ForeignKey(UserProfile, db_column="user", verbose_name="接收消息的用户")
    meeting = models.CharField(max_length=20, verbose_name="会议ID")  # 不用设置成外键,否则删除applymeeting时messages也会删除
    content = models.CharField(max_length=255, verbose_name="消息")

    # 消息创建状态 用于更新操作时判断joins的变化 -1也用于表示假删除
    status = models.IntegerField(verbose_name="本条消息是否过期", choices=((1, '更新状态'), (0, '首次创建'), (-1, '对应会议被删除')),
                                 default=0)
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "用户消息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.name


class Signed(models.Model):
    """
    预定会议参会人员签到表
    """
    user = models.ForeignKey(UserProfile, db_column="user", verbose_name="接收消息的用户")
    meeting = models.ForeignKey(ApplyMeeting, db_column="meeting", verbose_name="会议ID")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "参会人员签到表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.name


class SepVoices(models.Model):
    """
    语音转写-人声分离
    """
    meeting = models.ForeignKey(ApplyMeeting, db_column="meeting", verbose_name="对应会议")
    voices_file = models.FileField(upload_to=upload_voices_file, verbose_name="音频文件")
    result = models.TextField(default='等待转写文字中...', verbose_name="语音转录的文字")
    user = models.ForeignKey(UserProfile, db_column="user", verbose_name="上传的用户")
    add_time = models.DateTimeField(default=datetime.now, verbose_name="添加时间")

    class Meta:
        verbose_name = "语音转写-人声分离"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.meeting.title + "-" + self.user.name
