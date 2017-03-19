# encoding=utf8

""" The main entry
    Author: lipixun
    Created Time : 日  2/12 14:15:29 2017

    File Name: __main__.py
    Description:

"""

import sys
reload(sys)
sys.setdefaultencoding("utf8")

from sys import argv

from .main import main

main(argv[1:])
