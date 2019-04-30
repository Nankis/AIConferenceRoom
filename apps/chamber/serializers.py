# -*- coding: utf-8 -*-
import datetime
import json
from chamber.models import Equipment, Chamber, ApplyMeeting, UserUploadFile, Messages, Signed, SepVoices
from user.models import UserProfile, Department
from user.serializers import UserSerializer, UserSimpleSerializer
from utils.separationVocies import request_lfasr_result
from utils.tools import GetFileSize
from fuwu import celery
# from celery.schedules import crontab

import utils.globalvar as glo

__author__ = 'Ginseng'

from rest_framework import serializers


class EquipmentSerializer(serializers.ModelSerializer):
    """
    设备序列化--显示
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = ('id', 'name', 'num')

    def get_name(self, obj):
        try:
            name = obj.name
            return name
        except Exception as e:
            return []


class CreateEquipmentSerializer(serializers.ModelSerializer):
    """
    设备序列化--创建
    """

    class Meta:
        model = Equipment
        fields = ('id', 'name', 'num')


class ManageChamberSerializer(serializers.ModelSerializer):
    """
    会议室序列化--添加,删除,更新
    """
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = Chamber
        fields = "__all__"


class ChamberSerializer(serializers.ModelSerializer):
    """
    会议室序列化--查看或删除
    """
    host = UserSimpleSerializer(many=False)
    equipment = EquipmentSerializer(many=True)
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = Chamber
        fields = "__all__"


class ChamberSimpleSerializer(serializers.ModelSerializer):
    """
    会议室简化序列化
    """
    add_time = serializers.DateTimeField(write_only=True)
    host = serializers.SerializerMethodField()

    class Meta:
        model = Chamber
        fields = "__all__"

    def get_host(self, obj):
        name = obj.host.name
        return name


class ApplyMeetingSimpleSerializer(serializers.ModelSerializer):
    """
    预定会议简化序列化
    """
    add_time = serializers.DateTimeField(write_only=True)
    start = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    end = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = ApplyMeeting
        fields = "__all__"


class ApplyMeetingSerializer(serializers.ModelSerializer):
    """
    会议室预定显示列表---用于list和del
    """
    # joins = UserSimpleSerializer(many=True)
    joins = serializers.SerializerMethodField()
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    start = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    end = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    chamber = ChamberSerializer(many=False)
    # speaker = UserSimpleSerializer(many=False)
    speaker = serializers.SerializerMethodField()
    meeting_status = serializers.SerializerMethodField()
    pubuser = serializers.SerializerMethodField()

    class Meta:
        model = ApplyMeeting
        fields = "__all__"

    def get_meeting_status(self, obj):
        start = obj.start
        end = obj.end
        now = datetime.datetime.now()
        if now < start:
            return "未开始"
        elif start <= now <= end:
            return "进行中"
        return "已结束"

    def get_joins(self, obj):
        joins_list = []
        pre_joins = obj.joins.all()

        for v in pre_joins:
            join = UserProfile.objects.get(id=v.id)

            us = UserSimpleSerializer(join, many=False, context={'request': self.context['request']}).data
            is_signed = Signed.objects.filter(meeting=obj.id, user=v).count()
            if is_signed:
                us["signed"] = "已签到"
            else:
                us["signed"] = "未签到"
            department = join.department.all().first().name
            us["department"] = department
            joins_list.append(us)
        json_data = json.dumps(joins_list, ensure_ascii=False)
        # return eval(json_data)   # 不能用eval不属于python存在安全问题,且会可能会报错NameError: name 'null' is not defined
        return json.loads(json_data)

    def get_speaker(self, obj):
        speaker = obj.speaker
        us = UserSimpleSerializer(speaker, many=False, context={'request': self.context['request']}).data
        is_signed = Signed.objects.filter(meeting=obj.id, user=speaker).count()
        if is_signed:
            us["signed"] = "已签到"
        else:
            us["signed"] = "未签到"
        return us

    def get_pubuser(self, obj):
        pubuser = obj.pubuser
        us = UserSimpleSerializer(pubuser, many=False, context={'request': self.context['request']}).data
        is_signed = Signed.objects.filter(meeting=obj.id, user=pubuser).count()
        if is_signed:
            us["signed"] = "已签到"
        else:
            us["signed"] = "未签到"
        return us


class CreateAndUpdateApplyMeetingSerializer(serializers.ModelSerializer):
    """
    会议室预定显示列表---用于create和update
    """
    pubuser = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    def validate_end(self, end):
        if self.initial_data["start"] > self.initial_data["end"]:
            raise serializers.ValidationError("会议开始时间不能大于结束时间!")
        return end

    def validate_start(self, start):
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')  # 格式为str
        # now_date =
        start = self.initial_data["start"]
        if start < now_date:
            raise serializers.ValidationError("会议开始时间不能是过去!")
        return start

    class Meta:
        model = ApplyMeeting
        fields = "__all__"


class UserUploadFileSerializer(serializers.ModelSerializer):
    """
    用户上传文件
    """
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    file_name = serializers.CharField(read_only=True)
    file_size = serializers.CharField(read_only=True)
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = UserUploadFile
        fields = "__all__"

    def create(self, validated_data):
        file_list = self.context["request"].FILES.getlist('file')
        instance = super(UserUploadFileSerializer, self).create(validated_data=validated_data)
        instance.file_name = file_list[0].name
        instance.file_size = GetFileSize(file_list[0].size)
        instance.save()
        return instance


class MessagesSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    # meeting = serializers.SerializerMethodField() # 存在修改过后主题和信息里的主题不匹配问题..

    class Meta:
        model = Messages
        fields = "__all__"

    # def get_meeting(self, obj):
    #     meeting_id = Messages.objects.filter(id=obj.id).first().meeting
    #     title = ApplyMeeting.objects.filter(id=meeting_id).first().title
    #     return title


class GetUserMeetingSerializer(serializers.ModelSerializer):
    """
    获取当前用户的会议日期
    """
    start = serializers.DateTimeField(read_only=True, format='%Y-%m-%d')

    class Meta:
        model = ApplyMeeting
        fields = ('id', 'start', 'title')


class ChamberMeetingPreInfoSerializer(serializers.ModelSerializer):
    """
    会议室会议预定信息
    """
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    start = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    end = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    chamber = serializers.SerializerMethodField()
    speaker = serializers.SerializerMethodField()
    pubuser = serializers.SerializerMethodField()

    class Meta:
        model = ApplyMeeting
        # fields = "__all__"
        exclude = ['remark', 'joins', ]

    def get_chamber(self, obj):
        chamber_name = obj.chamber.name
        return chamber_name

    def get_speaker(self, obj):
        speaker_name = obj.speaker.name
        return speaker_name

    def get_pubuser(self, obj):
        pubuser_name = obj.pubuser.name
        return pubuser_name


class ChamberMeetingInfoSerializer(serializers.ModelSerializer):
    """
    显示当前会议室的信息
    """

    chamber = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    speaker = serializers.SerializerMethodField()
    start = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    end = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = ApplyMeeting
        # fields = "__all__"
        exclude = ['joins', 'remark']

    def get_chamber(self, obj):
        chamber_name = obj.chamber.name
        return chamber_name

    def get_speaker(self, obj):
        speaker_name = obj.speaker.name
        return speaker_name

    def get_space(self, obj):
        space = obj.chamber.space
        return space

    def get_address(self, obj):
        address = obj.chamber.address
        return address

    def get_host(self, obj):
        host_name = obj.chamber.host.name
        return host_name


class SignedSerializer(serializers.ModelSerializer):
    """
    参会人员签到
    """
    meeting = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = Signed
        fields = "__all__"

    def get_meeting(self, obj):
        title = obj.meeting.title
        return title

    def get_user(self, obj):
        user_name = obj.user.name
        return user_name


class CreateSepVoiceSerializer(serializers.ModelSerializer):
    """
    人声分离--create
    """
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    result = serializers.CharField(read_only=True)
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = SepVoices
        fields = "__all__"


class ListSepVoiceSerializer(serializers.ModelSerializer):
    """
    list
    """
    result = serializers.SerializerMethodField()
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = SepVoices
        fields = "__all__"

    def get_result(self, obj):
        if obj.result == "等待转写文字中...":
            return "等待转写文字中..."
        else:
            return eval(obj.result)


class AllMeetingSimpleSerializer(serializers.ModelSerializer):
    """
    所有会议的简要信息
    """
    start = serializers.DateTimeField(read_only=True, format='%Y-%m-%d')
    end = serializers.DateTimeField(read_only=True, format='%Y-%m-%d')
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')
    remark = serializers.CharField(write_only=True)
    chamber = serializers.CharField(write_only=True)
    status = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()

    speaker = UserSimpleSerializer(many=False)
    pubuser = UserSimpleSerializer(many=False)
    joins = UserSimpleSerializer(many=True)

    class Meta:
        model = ApplyMeeting
        fields = "__all__"

    def get_color(self, obj):
        start = obj.start
        end = obj.end
        now = datetime.datetime.now()
        if now < start:
            return "#66CCFF"
        elif start <= now <= end:
            return "#67C23A"
        return "#909399"

    def get_status(self, obj):
        start = obj.start
        end = obj.end
        now = datetime.datetime.now()
        if now < start:
            return "未开始"
        elif start <= now <= end:
            return "进行中"
        return "已结束"


class UserForChamberStatusSerializer(serializers.ModelSerializer):
    """
    用户简单信息序列化-
    """
    password = serializers.CharField(write_only=True)
    last_login = serializers.DateTimeField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    groups = serializers.CharField(write_only=True)
    user_permissions = serializers.CharField(write_only=True)
    is_superuser = serializers.CharField(write_only=True)
    is_active = serializers.CharField(write_only=True)
    is_staff = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True)
    date_joined = serializers.DateTimeField(write_only=True)
    add_time = serializers.DateTimeField(write_only=True, format="%Y-%m-%d %H:%M")

    username = serializers.CharField(write_only=True)
    id = serializers.CharField(write_only=True)

    department = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = "__all__"

    def get_department(self, obj):
        if obj.department:
            department_qs = obj.department.all()
            return department_qs[0].name
        return ""


class ChamberMeetingPreInfoAdminSerializer(serializers.ModelSerializer):
    """
    会议室会议预定信息
    """
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    start = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    end = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")
    chamber = serializers.SerializerMethodField()
    speaker = serializers.SerializerMethodField()
    pubuser = UserForChamberStatusSerializer(many=False)
    joins = UserForChamberStatusSerializer(many=True)

    class Meta:
        model = ApplyMeeting
        # fields = "__all__"
        exclude = ['remark', ]

    def get_chamber(self, obj):
        chamber_name = obj.chamber.name
        return chamber_name

    def get_speaker(self, obj):
        speaker_name = obj.speaker.name
        return speaker_name
