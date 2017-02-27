# encoding=utf8

""" The data model
    Author: lipixun
    Created Time : 日  2/12 15:25:08 2017

    File Name: model.py
    Description:

"""

class Country(object):
    """The country
    """
    def __init__(self, name, alias = None):
        """Create a new Country
        """
        self.name = name
        self.alias = alias or []    # The alias of the country including the name itself

    def __str__(self):
        """Convert to string
        """
        return "%s: %s" % (self.name, ",".join(self.alias))

class Region(object):
    """The region
    """
    def __init__(self, name, alias = None, countries = None):
        """Create a new Region
        """
        self.name = name
        self.alias = alias or []
        self.countries = countries or []

    def __str__(self):
        """Convert to string
        """
        return "%s: %s" % (self.name, ",".join(self.alias))

class Province(object):
    """The province
    """
    def __init__(self, name, alias = None):
        """Create a new Province
        """
        self.name = name
        self.alias = alias or []    # The alias of the province including the name itself

    def __str__(self):
        """Convert to string
        """
        return "%s: %s" % (self.name, ",".join(self.alias))

class City(object):
    """The city
    """
    def __init__(self, name, alias = None):
        """Create a new City
        """
        self.name = name
        self.alias = alias or []    # The alias of the city including the name itself

    def __str__(self):
        """Convert to string
        """
        return "%s: %s" % (self.name, ",".join(self.alias))

class News(object):
    """The news
    """
    def __init__(self, title = None, content = None):
        """Create a new News
        """
        self.title = title
        self.content = content

    def __str__(self):
        """Convert to string
        """
        return "%s: %s" % (self.title, self.content)
