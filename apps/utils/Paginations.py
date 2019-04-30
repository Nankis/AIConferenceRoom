# -*- coding: utf-8 -*-
__author__ = 'Ginseng'

from rest_framework.pagination import PageNumberPagination


class CommonPagination(PageNumberPagination):
    page_size = 10  # 默认每页显示的个数
    page_size_query_param = 'limit'  # 可以动态改变每页显示的个数
    page_query_param = 'page'  # 页码参数
    max_page_size = 100  # 最多显示多少页
