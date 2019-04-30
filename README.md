# AIConferenceRoom
2019年第十届中国大学生服务外包创新创业大赛全国赛三等奖,A类,智能会议室系统后端源码.项目演示地址:https://www.bilibili.com/video/av49845717

该项目是2019年服务外包大赛参赛作品，项目采用前后端分离技术，其中后端功能主要实现智能调度查询空余会议室、基于虹软的人脸识别签到、自动开门、
以及人声分离语音转写等功能。项目后端基于Python的Django rest framework框架开发,其中，用到了消息队列celery、和缓存redis等

__由于后端代码完全由本人一个人编写,所以会存在一些不足的地方,若是有好的建议或不足的地方可以提出.项目仅用于学习交流使用,也是本人记录学习的过程吧.__

项目安装:
需要先安装虚拟环境
　　1、安装 virtualenvwrapper
>pip install virtualenvwrapper

　　2、创建目录存放虚拟环境

>mkdir ~/.virtualenvs

　　3、在.bashrc中末尾添加

>export WORKON_HOME=~/.virtualenvs
>source /usr/local/bin/virtualenvwrapper.sh

 附上几个常用命令
workon:列出虚拟环境列表
lsvirtualenv:同上

mkvirtualenv [envname]:新建虚拟环境

workon [envname]:切换虚拟环境

rmvirtualenv  [envname]:删除虚拟环境

deactivate: 离开虚拟环境

cpvirtualenv [sorce] [dest]　　\#复制虚拟环境

pip freeze > requirements.txt　　导出该环境下所有依赖到requirements.txt文件
  
 虚拟环境安装完成后执行切换到根目录安装需求包:
>pip install -r requirements.txt   
该过程可能因为系统的版本不同而有报错,注意看报错信息,然后解决即可.

数据库使用的是MySQL5.6以上的版本

linux版本建议选centos7以上

后台自动运行可选择:
>\# celery worker -A fuwu -l debug -P eventlet  进入目录启动    pip install eventlet后需要在运行时添加额外参数 -P eventlet
>\# celery -A <mymodule> worker -l info -P eventlet    win10环境下用此命令运行
>\# celery worker -A fuwu -l info -P eventlet linux环境下用此行命令运行


也可以使用Supervisor后台运行Celery和Redis:
1、安装Supervisor
Supervisor是Python开发的，用于在Linux服务器中管理进程。

除了可以讲上面转换程序为后台程序之外，还可以监控进程。若进程崩溃关闭，它可以自动重启进程等等。更多相关介绍可以查看Supervior的官网：http://supervisord.org。
Supervisor安装很简单，使用pip即可安装：
>pip install supervisor

2、Supervisor配置
我们可以使用echo_supervisord_conf命令得到supervisor配置模板，打开终端执行如下Linux shell命令：
>echo_supervisord_conf > supervisord.conf

该命令输出文件到当前目录下（当然，你也可以指定绝对路径到具体位置），文件名为supervisord.conf。
再使用vim命令打开该文件并编辑：
>vim supervisord.conf

新行输入如下配置信息（以celery worker为例，具体含义看注释）：

>[program:celery.worker] 
>;指定运行目录 
>directory=/home/xxx/webapps/yshblog_app/yshblog
>;运行目录下执行命令
>command=celery -A yshblog worker --loglevel info --logfile celery_worker.log
 
>;启动设置 
>numprocs=1          ;进程数
>autostart=true      ;当supervisor启动时,程序将会自动启动 
>autorestart=true    ;自动重启
 
>;停止信号,默认TERM 
>;中断:INT (类似于Ctrl+C)(kill -INT pid)，退出后会将写文件或日志(推荐) 
>;终止:TERM (kill -TERM pid) 
>;挂起:HUP (kill -HUP pid),注意与Ctrl+Z/kill -stop pid不同 
>;从容停止:QUIT (kill -QUIT pid) 
>stopsignal=INT


你也可以把redis添加进来，给supervisor管理。将redis配置写在celery.worker前面。先打开redis服务，再执行celery.worker，最后轮到celery.beat。如下redis配置：
>[program:redis]
>;指定运行目录 
>directory=~/webapps/yshblog_app/lib/redis-3.2.8/
>;执行命令（redis-server redis配置文件路径）
>command=redis-server redis.conf
 
>;启动设置 
>numprocs=1          ;进程数
>autostart=true      ;当supervisor启动时,程序将会自动启动 
>autorestart=true    ;自动重启
 
>;停止信号
>stopsignal=INT

更多关于Supervisor的命令和操作请自行查找.
