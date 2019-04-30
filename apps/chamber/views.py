# -*- coding: utf-8 -*-
import json
import socket
from datetime import datetime, timedelta, date

from celery.task import task
from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, filters, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from rest_framework.response import Response
from chamber.models import Equipment, Chamber, ApplyMeeting, UserUploadFile, Messages, Signed, SepVoices
from chamber.serializers import EquipmentSerializer, ChamberSerializer, ManageChamberSerializer, ApplyMeetingSerializer, \
    CreateAndUpdateApplyMeetingSerializer, CreateEquipmentSerializer, UserUploadFileSerializer, ChamberSimpleSerializer, \
    ApplyMeetingSimpleSerializer, MessagesSerializer, GetUserMeetingSerializer, ChamberMeetingPreInfoSerializer, \
    ChamberMeetingInfoSerializer, SignedSerializer, ListSepVoiceSerializer, CreateSepVoiceSerializer, \
    AllMeetingSimpleSerializer, ChamberMeetingPreInfoAdminSerializer
from user.models import UserProfile
from user.serializers import UserSerializer
from utils.permissions import IsOwnerOrReadOnly
from utils.separationVocies import request_lfasr_result
from utils.tools import DeleteFile

User = get_user_model()


def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))

    try:
        print("Send: {}".format(message))
        sock.sendall(message.encode("utf-8"))
        response = sock.recv(1024)
        jresp = json.loads(response.decode('utf-8'))
        print("Recv: ", jresp)
        return jresp
    finally:
        sock.close()


def request_open(door_id=0):
    HOST, PORT = "140.143.75.206", 20000  # 请求的服务端地址和端口
    msg = [{
        "request": "open",  # 默认请求开启
        "door_id": door_id,  # 对应会议室的门,即会议室的id
    }]
    jmsg = json.dumps(msg)
    return client(HOST, PORT, jmsg)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    设备管理
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = EquipmentSerializer

    queryset = Equipment.objects.all()

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return EquipmentSerializer
        elif self.action == "create":
            return CreateEquipmentSerializer
        elif self.action == "retrieve":
            return EquipmentSerializer
        return EquipmentSerializer


class ChamberViewSet(viewsets.ModelViewSet):
    """
    会议室管理
    list:
        查看所有会议室
    create:
        新增会议室
    retrieve:
        删除指定id会议室
    update:
        更新指定id会议室,用于更新会议室的使用状态
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('address', 'name', 'space', 'host')

    queryset = Chamber.objects.all().order_by("-add_time")

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return ChamberSerializer
        elif self.action == "create":
            return ManageChamberSerializer
        elif self.action == "retrieve":
            return ChamberSerializer
        elif self.action == "update":
            return ManageChamberSerializer
        return ChamberSerializer


class ApplyMeetingViewSet(viewsets.ModelViewSet):
    """
    预定会议
    1.可以按照演讲者或者参与者的名字搜索,对应功能----用户全部日程api(包括已经参与过的任务)
    2.可按照演讲主题搜索
    3.可按照主讲人名字或参与人名字(被邀请人名字)过滤
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    queryset = ApplyMeeting.objects.all().order_by("-add_time")
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('speaker__name', 'joins__name', 'title')
    filter_fields = ('speaker__name', 'joins__name')

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return ApplyMeetingSerializer
        elif self.action == "create":
            return CreateAndUpdateApplyMeetingSerializer
        elif self.action == "retrieve":
            return ApplyMeetingSerializer
        elif self.action == "update":
            return CreateAndUpdateApplyMeetingSerializer
        return ApplyMeetingSerializer

    def perform_create(self, serializer):
        meeting_instance = serializer.save()
        meeting = ApplyMeeting.objects.get(id=meeting_instance.id)
        joins = meeting.joins.all()
        start_time = meeting.start.strftime("%Y-%m-%d %H:%M")
        end_time = meeting.end.strftime("%Y-%m-%d %H:%M")
        msg = "会议邀请通知:{speaker}邀请您参与主题为:《{title}》的会议,时间为:{start}到{end},地点在{address}的{chamber},备注:{remark}".format(
            speaker=meeting.speaker.name,
            title=meeting.title,
            start=start_time, end=end_time,
            address=meeting.chamber.address,
            chamber=meeting.chamber.name,
            remark=meeting.remark)
        msg_title = "会议邀请通知"
        for v in joins:
            Messages.objects.create(user=v, content=msg, title=msg_title, meeting=meeting_instance.id)

    def perform_destroy(self, instance):
        meeting = ApplyMeeting.objects.get(id=instance.id)
        joins = meeting.joins.all()
        start_time = meeting.start.strftime("%Y-%m-%d %H:%M")
        end_time = meeting.end.strftime("%Y-%m-%d %H:%M")
        msg = "会议取消通知:{speaker}已取消主题为:《{title}》的会议,时间为:{start}到{end},地点在{address}的{chamber},请您注意会议的更变!".format(
            speaker=meeting.speaker.name,
            title=meeting.title,
            start=start_time, end=end_time,
            address=meeting.chamber.address,
            chamber=meeting.chamber.name)
        msg_title = "会议取消通知"
        for v in joins:
            Messages.objects.create(user=v, content=msg, title=msg_title, meeting=instance.id, status=1)
        instance.delete()

    def perform_update(self, serializer):
        first_record = Messages.objects.filter(meeting=serializer.instance.id, status=0)  # 查找出首次创建的记录
        updated_record = Messages.objects.filter(meeting=serializer.instance.id, status=1).order_by(
            "-add_time")  # 获取最新修改记录

        first_joins = []
        updated_joins = []
        for v in first_record:
            first_joins.append(v.user)
        if updated_record:  # 如果原先有更新记录就覆盖
            date_rang = updated_record[0].add_time + timedelta(seconds=-4)  # 最新数据-4s已便于获取一个时间段范围
            updated_record = Messages.objects.filter(meeting=serializer.instance.id, status=1, add_time__gte=date_rang)
            for v in updated_record:
                updated_joins.append(v.user)
            first_joins = updated_joins

        new_record = serializer.save()
        meeting = ApplyMeeting.objects.get(id=new_record.id)  # 获取更新后的meeting实例
        new_joins_qs = meeting.joins.all()
        new_joins = []
        for v in new_joins_qs:
            new_joins.append(v)

        set_dif = list(set(first_joins).difference(set(new_joins)))
        start_time = meeting.start.strftime("%Y-%m-%d %H:%M")
        end_time = meeting.end.strftime("%Y-%m-%d %H:%M")

        msg_change = "会议更变通知:{speaker}邀请您参与主题为:《{title}》的会议已发生更变,更变后时间为:{start}到{end},地点在{address}的{chamber},备注:{remark}".format(
            speaker=meeting.speaker.name,
            title=meeting.title,
            start=start_time, end=end_time,
            address=meeting.chamber.address,
            chamber=meeting.chamber.name,
            remark=meeting.remark)

        msg_cancel = "会议取消通知:{speaker}已取消主题为:《{title}》的会议,时间为:{start}到{end},地点在{address}的{chamber},请您注意会议的更变!".format(
            speaker=meeting.speaker.name,
            title=meeting.title,
            start=start_time, end=end_time,
            address=meeting.chamber.address,
            chamber=meeting.chamber.name)

        msg_invite = "会议邀请通知:{speaker}邀请您参与主题为:《{title}》的会议,时间为:{start}到{end},地点在{address}的{chamber},备注:{remark}".format(
            speaker=meeting.speaker.name,
            title=meeting.title,
            start=start_time, end=end_time,
            address=meeting.chamber.address,
            chamber=meeting.chamber.name,
            remark=meeting.remark)
        msg_title_change = "会议更变通知"
        if len(set_dif) == 0:  # 说明参与人数不变
            for v in new_joins:
                Messages.objects.create(user=v, content=msg_change, title=msg_title_change, meeting=new_record.id,
                                        status=1)
        else:  # 前后参与的人员已发生改变
            msg_title_cancel = "会议取消通知"
            msg_title_invite = "会议邀请通知"
            set_inters = list(set(first_joins).intersection(set(new_joins)))  # 交集-->表示部分参与人不变,通知会议更改
            for v in set_inters:
                Messages.objects.create(user=v, content=msg_change, title=msg_title_change, meeting=new_record.id,
                                        status=1)

            for v in set_dif:  # 差集-->通知原先被邀请的人取消会议
                Messages.objects.create(user=v, content=msg_cancel, title=msg_title_cancel, meeting=new_record.id,
                                        status=1)

            bj = list(set(first_joins).union(set(new_joins)))  # 并集
            set_new = list(set(bj).difference(set(first_joins)))  # 先和原先的并集,结果再和原先的做差集
            for v in set_new:  # 通知邀请新增人员参加会议
                Messages.objects.create(user=v, content=msg_invite, title=msg_title_invite, meeting=new_record.id,
                                        status=1)


class UserUploadFileViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    """
    可以按会议的id或则上传者的名字进行筛选
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('user__name',)
    filter_fields = ('meeting',)
    serializer_class = UserUploadFileSerializer
    queryset = UserUploadFile.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        file_path = instance.file.path
        try:
            DeleteFile(file_path)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class GetFreeChamberByDateViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    通过时间段获取:不带参数返回所有会议任务,带参数返回当前时间段可用的会议室:
    请求方法:get
    请求格式:?start=2019-02-10 17:00:00.000000&end=2019-02-10 21:00:00.000000
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    EXCEPTION_VIEW_FLAG = 0  # 异常时显示的模式

    def get_serializer_class(self):
        if self.action == "list" and self.EXCEPTION_VIEW_FLAG == 1:  # 没有附加参数时显示
            return ApplyMeetingSimpleSerializer
        return ChamberSimpleSerializer

    def get_queryset(self):
        try:
            start = self.request.query_params["start"]
            end = self.request.query_params["end"]
            if start >= end:
                return

            qs_chamber = Chamber.objects.all()
            qs_applymeeting = ApplyMeeting.objects.filter(start__gte=start, end__lte=end).distinct()
            for v in qs_applymeeting:
                qs_chamber = qs_chamber.exclude(id=v.chamber.id)
            return qs_chamber
        except Exception as e:
            self.EXCEPTION_VIEW_FLAG = 1
            return ApplyMeeting.objects.all()


class MessagesViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    """
    用户消息管理:可按会议id与用户id(或名字)组合搜索,格式:?meeting=47&search=2(或?meeting=47&search=阿龙)
    也可只单独按照用户名字或id搜索,格式:?&search=2(?&search=阿龙)
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('user__name', 'user__id')
    filter_fields = ('meeting',)
    serializer_class = MessagesSerializer
    queryset = Messages.objects.filter(Q(status=0) | Q(status=1)).order_by("-add_time")

    def perform_destroy(self, instance):
        message_instance = Messages.objects.get(id=instance.id)  # 此id是messages的id 而不是会议的id,meeting是会议的id
        message_instance.status = -1
        message_instance.save()
        cur_meeting = ApplyMeeting.objects.filter(id=instance.meeting).count()
        if cur_meeting == 0:  # 如果这个会议已被删除,那么消息也会被删除
            Messages.objects.filter(meeting=instance.meeting, status=-1).delete()


class CurUserMessagesViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """
    当前登录用户收到的通知信息
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('user__name', 'user__id')
    filter_fields = ('meeting',)
    serializer_class = MessagesSerializer

    def get_queryset(self):
        qs = Messages.objects.filter(user=self.request.user.id).filter(Q(status=0) | Q(status=1)).order_by("-add_time")
        return qs

    def perform_destroy(self, instance):
        message_instance = Messages.objects.get(id=instance.id)  # 此id是messages的id 而不是会议的id,meeting是会议的id
        message_instance.status = -1
        message_instance.save()
        cur_meeting = ApplyMeeting.objects.filter(id=instance.meeting).count()
        if cur_meeting == 0:  # 如果这个会议已被删除,那么消息也会被删除
            Messages.objects.filter(meeting=instance.meeting, status=-1).delete()


class CurUserMeetingByDateViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    通过时间获取当前登录用户的某天会议列表:参数:?day=2019-02-21,方法GET
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = ApplyMeetingSerializer

    def get_queryset(self):
        try:
            day_start = self.request.query_params["day"]
            day_start = datetime.strptime(day_start, "%Y-%m-%d")
            day_end = day_start + timedelta(days=1)  # 明天
            qs_applymeeting = ApplyMeeting.objects.filter(
                Q(speaker=self.request.user) | Q(joins=self.request.user)).filter(start__gte=day_start,
                                                                                  end__lt=day_end).distinct().order_by(
                "start")
            return qs_applymeeting
        except Exception as e:
            return


class CurUserMeetingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    当前用户的会议:不传参数为当前用户全部会议,
    ?type=pubuser  ---当前用户发起的会议
    ?type=join    ---当前用户参与的会议(被邀约的会议)

    ?type=pubuser&day=2019-03-01  ---当前用户在指定日期发起的会议 #并非当天有会议
    ?type=join&day=2019-03-01 --当前用户在指定日期参与的会议(被邀约的会议)
    请求方法:GET
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = ApplyMeetingSerializer

    def get_queryset(self):
        try:
            type = self.request.query_params["type"]
            qs_pubuser_meeting = ApplyMeeting.objects.filter(
                Q(pubuser=self.request.user) | Q(speaker=self.request.user)).order_by("-add_time").distinct()
            if type == "pubuser":
                try:
                    day_start = self.request.query_params["day"]  # 新算法的day参数只是用于区分筛选模式
                    day_start = datetime.strptime(day_start, "%Y-%m-%d")
                    day_end = day_start + timedelta(days=1)  # 明天
                    qs_pubuser_meeting_day = qs_pubuser_meeting.filter(start__gte=day_start, end__lt=day_end)
                    return qs_pubuser_meeting_day
                except Exception as e:
                    return qs_pubuser_meeting  # 不加day就返回全部
            if type == "join":
                qs_join_meeting = ApplyMeeting.objects.filter(joins=self.request.user).order_by("-add_time").distinct()
                try:
                    day_start = self.request.query_params["day"]
                    day_start = datetime.strptime(day_start, "%Y-%m-%d")
                    day_start = day_start + timedelta(hours=23, minutes=59, seconds=59)
                    # day_end = day_start + timedelta(days=1)  # 明天
                    list_time = []
                    for v in qs_join_meeting:
                        if v.start <= day_start <= v.end:
                            list_time.append(v.start)
                            list_time.append(v.end)
                    min_start = min(list_time)
                    max_end = max(list_time)
                    qs_join_meeting_day = qs_join_meeting.filter(start__gte=min_start, end__lte=max_end)
                    return qs_join_meeting_day
                except Exception as e:
                    return qs_join_meeting  # 不加day就返回全部
        except Exception as e:
            return ApplyMeeting.objects.filter(
                Q(speaker=self.request.user) | Q(joins=self.request.user)).order_by(
                "-add_time").distinct()


class GetMeetingDataViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    获取当前用户会议的日期
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = GetUserMeetingSerializer

    def get_queryset(self):
        return ApplyMeeting.objects.filter(
            Q(speaker=self.request.user) | Q(joins=self.request.user)).order_by(
            "-add_time").distinct()


class GetChamberStatusViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    不传参数默认返回当天全部会议室会议信息
    获得指定会议室预定状态信息,只返回当天时间的预定信息
    """
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('chamber',)

    serializer_class = ChamberMeetingPreInfoSerializer

    def get_queryset(self):
        today = date.today()  # 获取当天日期
        tomorrow = today + timedelta(days=1)
        pre_meeting_qs = ApplyMeeting.objects.filter(start__gte=today, end__lt=tomorrow).order_by(
            "-add_time").distinct()
        return pre_meeting_qs


class CurChamberStatusViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    获取当前会议室当天的状态信息--参数?chamber=1,!!注意,是传会议室ID而不是会议id,方法GET 返回id=1的会议室状态信息,当天当前有会议正在进行则返回,否则不返回值
    """
    serializer_class = ChamberMeetingInfoSerializer

    def get_queryset(self):
        try:
            chamber_id = self.request.query_params["chamber"]
            now = datetime.now()
            today = date.today()  # 获取当天日期
            tomorrow = today + timedelta(days=1)
            pre_meeting_qs = ApplyMeeting.objects.filter(chamber=chamber_id).order_by(
                "start").distinct()  # 获取指定会议室所有预定的会议任务
            for v in pre_meeting_qs:
                if v.start <= now <= v.end:  # 如果该会议在进行中则直接获取该会议信息
                    return pre_meeting_qs.filter(start=v.start, end=v.end)
            return
        except Exception as  e:
            return


class JoinsSignedViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    参会人员签到,参数?empno=A1&meeting=12,方法GET,不传或传错则返回所有签到信息,若用户签到成功,则返回一条签到信息
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = SignedSerializer

    def get_queryset(self):
        try:
            empno = self.request.query_params["empno"]  # 应该先判断该用户之前是否被邀请到该会议
            user = UserProfile.objects.filter(empno=empno).first()
            if UserProfile.objects.filter(empno=empno).count() == 0:
                return  # 用户编号可能不存在

            meeting_id = self.request.query_params["meeting"]
            meeting = ApplyMeeting.objects.filter(id=meeting_id).first()

            if ApplyMeeting.objects.filter(id=meeting_id).count() == 0:
                return
            speaker = meeting.speaker  # 会议可能不存在
            pubuser = meeting.pubuser  # 会议发布人

            #   只能在会议开始前1小时或会议结束前可以签到
            now = datetime.now()
            pre_start = meeting.start + timedelta(hours=-1)
            if now < pre_start or now > meeting.end:
                return

            joins = meeting.joins.all()  # 获取到该会议的所有被邀请的人员
            signed_qs = Signed.objects.filter(user=user, meeting=meeting)
            if user not in joins and user != speaker and user != pubuser:  # 并非参会人员,无法签到
                return
            elif signed_qs.exists():  # 已签过到
                return

            Signed.objects.create(user=user, meeting=meeting)  # 用户签到
            # 第一次扫码成功也开门
            try:
                door_stauts = request_open(meeting.chamber.id)
                if door_stauts[0]["status"] == "open":  # 请求开门
                    return Signed.objects.filter(user=user, meeting=meeting)
            except Exception as e:
                return  # 签到成功,但是门打开失败

        except Exception as e:
            return Signed.objects.all().order_by("-add_time")

    def list(self, request, *args, **kwargs):
        try:
            empno = self.request.query_params["empno"]  # 应该先判断该用户之前是否被邀请到该会议
            user = UserProfile.objects.filter(empno=empno).first()
            if UserProfile.objects.filter(empno=empno).count() == 0:
                data = [{'msg': '不存在的员工号,请输入正确的员工号!'}, ]
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

            meeting = self.request.query_params["meeting"]
            meeting_instance = ApplyMeeting.objects.filter(id=meeting).first()

            if ApplyMeeting.objects.filter(id=meeting).count() == 0:
                data = [{'msg': '该会议不存在!'}, ]
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
            speaker = meeting_instance.speaker  # 会议存在,所以一定存在主讲人,该代码必须在判断会议存在之后执行
            pubuser = meeting_instance.pubuser  # 会议存在,所以一定存在发布人

            joins = meeting_instance.joins.all()  # 获取到该会议的所有被邀请的人员
            #   只能在会议开始前1小时或会议结束前可以签到
            now = datetime.now()
            pre_start = meeting_instance.start + timedelta(hours=-1)
            if now < pre_start or now > meeting_instance.end:
                data = [{'msg': '未到签到时间,请在会议开始前1小时到会议结束之前签到!'}, ]
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

            if user not in joins and user != speaker and user != pubuser:
                data = [{'msg': '您没有被邀请参与该会议,无法签到!'}, ]
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

            signed_qs = Signed.objects.filter(user=user, meeting=meeting)
            if signed_qs.exists():  # 已签过到
                chamber_id = meeting_instance.chamber.id
                try:
                    door_stauts = request_open(chamber_id)
                    if door_stauts[0]["status"] == "open":
                        data = [{'msg': '门已打开!'}, ]
                        return Response(data=data, status=status.HTTP_200_OK)
                except Exception as e:
                    data = [{'msg': '打开门失败!服务端可能被关闭了'}, ]
                    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

            # 验证通过...
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            # 验证通过...
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)


class SepVoicesViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    """
    人声分离
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('meeting',)

    def get_queryset(self):
        return SepVoices.objects.all().order_by("-add_time")

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return ListSepVoiceSerializer
        elif self.action == "create":
            return CreateSepVoiceSerializer
        return ListSepVoiceSerializer

    def perform_create(self, serializer):
        instance = serializer.save()  # 音频存到数据库后,马上调用转写并存储到数据库,显示的时候就正常显示
        file_path = instance.voices_file.path
        file_path = file_path.replace('\\', '/')
        request_lfasr_result.delay(file_path, instance.id)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        if instance.result == "等待转写文字中...":
            file_path = instance.voices_file.path
            file_path = file_path.replace('\\', '/')
            request_lfasr_result.delay(file_path, instance.id)
        return Response(serializer.data)


class AllMeetingSimpleInfoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    所有会议的简要信息
    """
    serializer_class = AllMeetingSimpleSerializer
    queryset = ApplyMeeting.objects.all()


class AllMeetingByDayViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    通过时间获取所有用户的某天会议列表:参数:?day=2019-02-21,方法GET
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = ApplyMeetingSerializer

    def get_queryset(self):
        try:
            day_start = self.request.query_params["day"]
            day_start = datetime.strptime(day_start, "%Y-%m-%d")
            day_end = day_start + timedelta(days=1)  # 明天
            qs_applymeeting = ApplyMeeting.objects.filter(start__gte=day_start, end__lt=day_end).distinct().order_by(
                "start")

            return qs_applymeeting
        except Exception as e:
            return


class GetChamberStatusAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    不传参数默认返回当天全部会议室会议信息
    获得指定会议室预定状态信息,只返回当天时间的预定信息(Admin管理端使用)
    """
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('chamber',)

    serializer_class = ChamberMeetingPreInfoAdminSerializer

    def get_queryset(self):
        today = date.today()  # 获取当天日期
        tomorrow = today + timedelta(days=1)
        pre_meeting_qs = ApplyMeeting.objects.filter(start__gte=today, end__lt=tomorrow).order_by(
            "-add_time").distinct()
        return pre_meeting_qs
