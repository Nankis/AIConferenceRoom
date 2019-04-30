# -*- coding: utf-8 -*-
__author__ = 'Ginseng'
import os

from rest_framework.fields import CreateOnlyDefault

from user.models import Department, UserArcFace, UserProfile
from utils.tools import DeleteFile, DeleteFolderInnerAllFile

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator

User = get_user_model()


class UserRegSerializer(serializers.ModelSerializer):
    """
    用户注册
    """
    username = serializers.CharField(label="用户名", help_text="用户名", required=True, allow_blank=False,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message="用户已经存在")])

    password = serializers.CharField(
        style={'input_type': 'password'}, help_text="密码", label="密码", write_only=True,
    )

    # password2 = serializers.CharField(
    #     style={'input_type': 'password'}, help_text="确认密码", label="确认密码", write_only=True,
    # )
    name = serializers.CharField(label="姓名", help_text="姓名", required=True, allow_blank=False)
    sex = serializers.CharField(label="性别", help_text="性别", required=True, allow_blank=False)
    department = serializers.CharField(label="部门", help_text="部门", required=True, allow_blank=False)
    job = serializers.CharField(label="职位", help_text="职位", required=True, allow_blank=False)
    empno = serializers.CharField(label="员工编号", help_text="员工编号", required=True, allow_blank=False,
                                  validators=[UniqueValidator(queryset=User.objects.all(), message="该员工编号已经存在了,请换一个!")])
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    # def validate_password2(self, password2):
    #     if self.context["request"].data["password"] != password2:
    #         raise serializers.ValidationError("您两次输入密码不一致!")

    def validate_sex(self, sex):
        if self.initial_data["sex"] != '男' and self.initial_data["sex"] != '女':
            raise serializers.ValidationError("性别有错误,请填写男或女!")
        return sex

    def validate_department(self, department):
        dp_qs = Department.objects.all()
        id_list = []
        for v in dp_qs:
            id_list.append(v.id)
        try:
            if int(department) in id_list:
                return department
            else:
                raise serializers.ValidationError("请填写已存在的部门id!")
        except Exception as e:
            raise serializers.ValidationError("数据异常,请填写已存在的部门id!")

    def create(self, validated_data):
        user = super(UserRegSerializer, self).create(validated_data=validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    class Meta:
        model = User
        fields = ('username', 'password', 'name', 'sex', 'department', 'job', 'add_time', 'empno')


class DepartmentSerializer(serializers.ModelSerializer):
    """
    部门序列化
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ('id', 'name')

    def get_name(self, obj):
        try:
            name = obj.name
            return name
        except Exception as e:
            return


class CreateDepartmentSerializer(serializers.ModelSerializer):
    """
    部门序列化--创建
    """

    class Meta:
        model = Department
        fields = ('id', 'name')


class UserSerializer(serializers.ModelSerializer):
    """
    显示用户列表
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
    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    # department = DepartmentSerializer(many=True)
    department = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_department(self, obj):
        if obj.department:
            department_qs = obj.department.all()
            return department_qs[0].name
        return ""


class DelUserSerializer(serializers.ModelSerializer):
    """
    删除用户
    """
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

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

    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    department = DepartmentSerializer(many=True)

    class Meta:
        model = User
        fields = "__all__"


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    更新员工信息
    """
    password = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    is_superuser = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()

    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = User
        fields = "__all__"

    def get_password(self, obj):
        return '无权查看'

    def get_username(self, obj):
        return '无权查看'

    def get_last_login(self, obj):
        return '无权查看'

    def get_first_name(self, obj):
        return '无权查看'

    def get_last_name(self, obj):
        return '无权查看'

    def get_groups(self, obj):
        return '无权查看'

    def get_user_permissions(self, obj):
        return '无权查看'

    def get_is_superuser(self, obj):
        return '无权查看'

    def get_is_active(self, obj):
        return '无权查看'

    def get_is_staff(self, obj):
        return '无权查看'

    def get_email(self, obj):
        return '无权查看'

    def get_date_joined(self, obj):
        return '无权查看'


class UserSimpleSerializer(serializers.ModelSerializer):
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
    # id = serializers.CharField(write_only=True)
    department = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = "__all__"


class UserArcFaceSerializer(serializers.ModelSerializer):
    """
    虹软人脸识别--特征文件
    """
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = UserArcFace
        fields = "__all__"

    def validate_feature_file(self, data):
        datas = self.context['request'].data
        empno = datas["empno"]
        exists_us = UserProfile.objects.filter(empno=empno)
        if exists_us.count() == 0:
            raise serializers.ValidationError("员工编号不存在,请输入正确的员工编号!")

        qs_uf = UserArcFace.objects.filter(empno=empno)
        if qs_uf.count() >= 1:  # 如果之前已经存在记录 那么删除数据库已存在的
            uf = qs_uf.first()
            file_path = str(uf.feature_file.path)  # 获取文件路径
            try:
                DeleteFile(file_path)  # 传入一个本项目的文件路径,删除项目内文件
                exists = UserArcFace.objects.filter(empno=empno)
                exists.delete()
                return data
            except Exception as e:
                try:
                    exists_us = exists_us.first()
                    # 移除文件夹后重新创建,以达到覆盖效果,需要传入用户的名字
                    DeleteFolderInnerAllFile(exists_us.name)

                    exists = UserArcFace.objects.filter(empno=empno)  # 异常只删除数据库存储索引
                    exists.delete()
                    return data
                except Exception as e:
                    raise serializers.ValidationError("数据异常.请重新识别或联系管理员删除已存在的特征文件!")
        return data
