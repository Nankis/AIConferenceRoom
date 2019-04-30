from __future__ import absolute_import, unicode_literals
from celery import shared_task


# celery worker -A fuwu -l debug -P eventlet  进入目录启动    pip install eventlet后需要在运行时添加额外参数 -P eventlet
# celery -A <mymodule> worker -l info -P eventlet    win10环境下用此命令运行
# celery worker -A fuwu -l info -P eventlet linux环境下用此行命令运行
@shared_task
def add(x, y):
    return x + y

# @shared_task
# def upload_file(x, y):
#     return x + y
