# encoding=utf8

""" The spec
    Author: lipixun
    Created Time : 日  2/12 15:23:06 2017

    File Name: spec.py
    Description:

"""

import math

from os.path import abspath, dirname, join

DataPath = join(dirname(abspath(__file__)), "data")

SheetCountry        = "country"
SheetRegion         = "region"
SheetProvince       = "province"
SheetCity           = "city"
SheetNews           = u"数字版"

KeyCountry          = u"国家"
KeyRegion           = u"地区"
KeyProvince         = u"省"
KeyCity             = u"城市"


IDFDictFilename     = join(DataPath, "idf.dict")

MissingValueIDF     = math.log(100.0)   # p = 1/100

DropWords = {
    "'s"
}
