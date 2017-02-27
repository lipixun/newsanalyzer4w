# encoding=utf8
# pylint: disable=W0611
""" The utility
    Author: lipixun
    Created Time : 日  2/12 14:14:50 2017

    File Name: utils.py
    Description:

"""

from spec import DataPath

# Import json
try:
    import simplejson as json
except ImportError:
    import json

# NLTK
import nltk
nltk.data.path = [ DataPath ]
