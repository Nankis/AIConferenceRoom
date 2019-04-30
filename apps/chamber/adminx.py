import xadmin
from chamber.models import Equipment, Chamber, ApplyMeeting


class EquipmentAdmin(object):
    list_display = ['name', 'num', 'add_time']
    # model_icon = 'fa fa-calendar'


class ChamberAdmin(object):
    list_display = ['name', 'address', 'space', 'host', 'equipment', 'add_time']


class ApplyMeetingAdmin(object):
    list_display = ['title', 'speaker', 'joins', 'start', 'end', 'remark', 'add_time']


xadmin.site.register(Equipment, EquipmentAdmin)
xadmin.site.register(Chamber, ChamberAdmin)
xadmin.site.register(ApplyMeeting, ApplyMeetingAdmin)
