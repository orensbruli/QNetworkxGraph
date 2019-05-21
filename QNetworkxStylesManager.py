#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os

try:
    from PySide2.QtGui import QColor
except Exception as e:
    from PyQt4.QtGui import QColor

class QtColorsDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' in obj:
            type = obj['_type']
            if type == 'QColor':
                color = self.to_QColor(obj["_value"])
                if color:
                    return color
        elif self.to_QColor(obj) is not None:
            return self.to_QColor(obj)
        return obj

    def to_QColor(self, obj):
        if isinstance(obj, basestring):
            return QColor(obj)
        elif isinstance(obj, list):
            if len(obj) == 3 or len(obj) == 4:
                if all(isinstance(item, int) for item in obj):
                    if len(obj) > 3:
                        return QColor(obj[0], obj[1], obj[2], obj[3])
                    else:
                        return QColor(obj[0], obj[1], obj[2], 255)
        return None


class QtColorsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QColor):
            return {
                "_type": "QColor",
                "_value": [obj.red(), obj.green(), obj.black(), obj.alpha()]
            }
        return super(QtColorsEncoder, self).default(obj)


class QNetworkxStylesManager(dict):
    def __init__(self, *args, **kwargs):
        super(QNetworkxStylesManager, self).__init__(*args, **kwargs)
        for arg in args:
            self.add_new_style(arg)

        if kwargs:
            self.add_new_style(kwargs)

    def add_new_style(self, style_dict):
        if isinstance(style_dict, (dict, QNetworkxStylesManager)):
            for k, v in style_dict.iteritems():
                if isinstance(v, dict):
                    self[k] = QNetworkxStylesManager(v)
                else:
                    self[k] = v

    def load_style_file(self, path):
        if os.path.isfile(path):
            with open(path) as data_file:
                style_dict = json.load(data_file, cls=QtColorsDecoder)
        else:
            new_path = os.path.join('style', path)
            if os.path.isfile(new_path):
                with open(new_path) as data_file:
                    style_dict = json.load(data_file, cls=QtColorsDecoder)
        return style_dict

    def load_styles(self, path=None):
        if path is None:
            path = os.path.join(os.path.dirname(__file__), 'styles')

        files = os.listdir(path)
        for file in files:
            if file.endswith(".json"):
                style_name = file.split('.')[0]
                style_dict = {style_name: self.load_style_file(os.path.abspath(os.path.join(path, file)))}
                self.add_new_style(style_dict)

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(QNetworkxStylesManager, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(QNetworkxStylesManager, self).__delitem__(key)
        del self.__dict__[key]

# graph_config= QNetworkxStylesManager()
# graph_config.load_styles()
# pprint(graph_config)
