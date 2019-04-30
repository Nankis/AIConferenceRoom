import os
import random
import shutil

from rest_framework.compat import unicode_to_repr


def RandomStr(numb):
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sa = []
    for i in range(numb):
        sa.append(random.choice(seed))
    salt = ''.join(sa)
    return salt


def GetFileSize(file_size):
    """
    转换字节单位  传入为基本单位为 B
    :param file_size:
    :return:
    """
    if file_size < 1024000:  # 最大为1000 KB
        return '%.2f KB' % (file_size / 1024)
    elif 1024000 <= file_size < 1024000000:
        return '%.2f MB' % (file_size / 1024 / 1024)  # 最大为1000MB
    elif 1024000000 <= file_size < 1024000000000:
        return '%.2f GB' % (file_size / 1024 / 1024 / 1024)  # 最大为1000GB
    else:
        return "未知大小"


def DeleteFile(file_path):
    """
    移除项目里指定路径文件
    :param file_path:
    :return:
    """
    file_path = str(file_path)
    # dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # dir_parent = os.path.dirname(dir)
    # file = os.path.join(dir_parent, "media/" + file_path)
    # file = file.replace('\\', '/')
    file = file_path.replace('\\', '/')
    os.remove(file)


def DeleteFolderInnerAllFile(exists_usname):
    """
    删除指定用户特征文件夹内文件,防止数据库索引不到而造成无法覆盖
    :param folder_path:
    :return:
    """
    dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dir_parent = os.path.dirname(dir)
    folder_path = os.path.join(dir_parent, "media/feature_files/" + exists_usname)
    folder_path = folder_path.replace('\\', '/')

    shutil.rmtree(folder_path)
