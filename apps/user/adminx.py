import xadmin
from xadmin import views
from xadmin.plugins.auth import UserAdmin
from xadmin.layout import Fieldset, Main, Side
from django.utils.translation import ugettext as _
from .models import UserProfile, Department, UserArcFace
from xadmin.plugins.actions import BaseActionView
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True


class GlobalSettings(object):
    site_title = "智能会议室后台"
    site_footer = "智能会议室"


class UserProfileAdmin(UserAdmin):
    list_display = ['id', 'name', 'sex', 'department', 'empno']
    # list_editable = ['is_vip', 'is_active', 'role']
    exclude = ['groups', 'user_permissions', 'first_name', 'last_name']
    # list_filter = ['role', 'is_staff', 'is_vip', 'is_active', 'date_joined']
    search_fields = ['username', 'name', 'empno', 'department', 'id']
    # actions = [UpVipStatus, DownVipStatus]


class DepartmentAdmin(object):
    list_display = ['name', 'add_time']
    model_icon = 'fa fa-calendar'


class UserArcFaceAdmin(object):
    list_display = ['user', 'feature_file', 'add_time']
    model_icon = 'fa fa-calendar'


xadmin.site.unregister(User)
xadmin.site.register(views.BaseAdminView, BaseSetting)
xadmin.site.register(views.CommAdminView, GlobalSettings)

xadmin.site.register(UserProfile, UserProfileAdmin)
xadmin.site.register(Department, DepartmentAdmin)
xadmin.site.register(UserArcFace, UserArcFaceAdmin)
