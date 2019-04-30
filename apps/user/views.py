from datetime import date, timedelta, datetime

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from chamber.models import ApplyMeeting
from chamber.serializers import ChamberMeetingPreInfoSerializer, ChamberMeetingInfoSerializer
from user.models import Department, UserProfile, UserArcFace
from utils.Paginations import CommonPagination
from utils.tools import DeleteFile
from .serializers import UserRegSerializer, UserSerializer, DelUserSerializer, UpdateUserSerializer, \
    DepartmentSerializer, CreateDepartmentSerializer, UserArcFaceSerializer
from rest_framework.authentication import SessionAuthentication

User = get_user_model()


class UserRegViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    员工注册
    """
    serializer_class = UserRegSerializer
    queryset = User.objects.all()


class UserViewSet(mixins.DestroyModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    员工管理:
        list:
            显示员工列表
        destroy:
            删除员工
        补充:
        可筛选性别,部门
        可以按用户名精确搜索
        可按姓名,员工编号模糊匹配
        可按员工id排序
    """
    queryset = User.objects.all().order_by("-add_time")
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('=username', 'name', 'empno')
    filter_fields = ('department__name', 'sex')
    ordering_fields = ('id',)

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return UserSerializer
        elif self.action == "retrieve":
            return DelUserSerializer
        return UserSerializer


class UpdateUserViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    更新员工信息
    """
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = UpdateUserSerializer

    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('=username', 'name', 'empno')
    filter_fields = ('sex',)


class DepartmentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    部门的管理--增删查
    """
    queryset = Department.objects.all()

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return DepartmentSerializer
        elif self.action == "retrieve":
            return DepartmentSerializer
        elif self.action == "create":
            return CreateDepartmentSerializer
        return DepartmentSerializer


class CurUserInfoViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """
    获取当前用户登录的信息,后面加任意参数即可修改用户数据,如curuserinfo/a/,方法:PATCH
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):  # 动态设置serializer
        if self.action == "list":
            return UserSerializer
        elif self.action == "retrieve":
            return UpdateUserSerializer
        elif self.action == "update":
            return UpdateUserSerializer
        return UserSerializer


class UserArcFaceViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
                         mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """
    人脸识别 特征文件上传,可通过用户名搜索获取对应用户上传的特征文件,
    同个用户上传特征文件会覆盖原先的,即同个用户最多只有一个特征文件存在
    """
    serializer_class = UserArcFaceSerializer
    queryset = UserArcFace.objects.all()

    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
