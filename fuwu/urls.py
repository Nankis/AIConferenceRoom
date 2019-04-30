"""fuwu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.views.static import serve

from chamber.views import EquipmentViewSet, ChamberViewSet, ApplyMeetingViewSet, UserUploadFileViewSet, \
    GetFreeChamberByDateViewSet, MessagesViewSet, CurUserMessagesViewSet, CurUserMeetingByDateViewSet, \
    CurUserMeetingViewSet, GetMeetingDataViewSet, GetChamberStatusViewSet, CurChamberStatusViewSet, JoinsSignedViewSet, \
    SepVoicesViewSet, AllMeetingSimpleInfoViewSet, AllMeetingByDayViewSet, GetChamberStatusAdminViewSet
from fuwu.settings import MEDIA_ROOT
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.documentation import include_docs_urls
import xadmin
from user.views import UserRegViewSet, UserViewSet, UpdateUserViewSet, DepartmentViewSet, CurUserInfoViewSet, \
    UserArcFaceViewSet

router = DefaultRouter()

# 用户注册
router.register(r'register', UserRegViewSet, base_name='register')

# 更新用户信息
router.register(r'updateuser', UpdateUserViewSet, base_name='updateuser')

# 删除用户
router.register(r'usermanage', UserViewSet, base_name='usermanage')

# 部门的管理
router.register(r'department', DepartmentViewSet, base_name='department')

# 设备管理
router.register(r'equipment', EquipmentViewSet, base_name='equipment')

# 会议事管理
router.register(r'chamber', ChamberViewSet, base_name='chamber')

# 会议室预定
router.register(r'applymeeting', ApplyMeetingViewSet, base_name='applymeeting')

# 用户文件上传
router.register(r'uploadfile', UserUploadFileViewSet, base_name='uploadfile')

# 获取空闲会议室
router.register(r'getfreechamber', GetFreeChamberByDateViewSet, base_name='getfreechamber')

# 获取用户消息
router.register(r'messages', MessagesViewSet, base_name='messages')

# 当前登录用户的个人信息
router.register(r'curuserinfo', CurUserInfoViewSet, base_name='curuserinfo')

# 当前登录用户的通知信息
router.register(r'curusermsg', CurUserMessagesViewSet, base_name='curusermsg')

# 当前登录用户的某天会议列表
router.register(r'curusermeeting', CurUserMeetingByDateViewSet, base_name='curusermeeting')

# 当前登录用户的会议(我的会议和邀约的会议)
router.register(r'usermeetings', CurUserMeetingViewSet, base_name='usermeetings')

# 虹软人脸识别特征文件
router.register(r'userarcface', UserArcFaceViewSet, base_name='userarcface')

# 获取当前用户的会议日期
router.register(r'meetingdata', GetMeetingDataViewSet, base_name='meetingdata')

# 获取指定会议室预定信息
router.register(r'chamberstatus', GetChamberStatusViewSet, base_name='chamberstatus')

# 当前会议室的信息(是否被占用)
router.register(r'curchamberinfo', CurChamberStatusViewSet, base_name='curchamberinfo')

# 参会人员签到接口
router.register(r'joinsigned', JoinsSignedViewSet, base_name='joinsigned')

# 人声分离
router.register(r'sepvoice', SepVoicesViewSet, base_name='sepvoice')

# 所有会议的简要信息
router.register(r'meetingsimpleinfo', AllMeetingSimpleInfoViewSet, base_name='meetingsimpleinfo')

# 根据时间获取获取当天所有用户的会议
router.register(r'allmeetingbyday', AllMeetingByDayViewSet, base_name='allmeetingbyday')

# 获取当前会议室预定信息--管理端使用
router.register(r'chamberstatusadmin', GetChamberStatusAdminViewSet, base_name='chamberstatusadmin')

urlpatterns = [
    url('^api/admin/', xadmin.site.urls),
    url(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),
    url(r'^api/', include(router.urls)),  # 路由跳转根目录
    url(r'^api/docs/', include_docs_urls(title="智能会议室")),
    url(r'^api/login/$', obtain_jwt_token),
]
