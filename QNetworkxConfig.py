#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor


QNetworkxConfig_default= {
    "NodeConfig":
        {
            "Profile_1":
                {
                    "Sunken":
                        {
                            "Edge":
                                {
                                    "PenColor": QColor(Qt.lightGray),
                                    "PenWidth": 2
                                },
                            "Fill": QColor(255, 0, 0, 127)
                        },
                    "Selected":
                        {
                            "Edge":
                                {
                                    "PenColor": QColor(255, 0, 0, 255),
                                    "PenWidth": 1
                                },
                            "Fill": QColor(255, 0, 0, 127)
                        },
                    "Default":
                        {
                            "Edge":
                                {
                                    "PenColor": QColor(200, 0, 100, 127),
                                    "PenWidth": 1
                                },
                            "Fill": QColor(255, 0, 0, 127)
                        }
                 },
            "Profile_2":
                {
                    "Sunken":
                        {
                            "Edge":
                                {
                                    "PenColor": QColor(Qt.lightGray),
                                    "PenWidth": 2
                                },
                            "Fill": QColor(0, 255, 0, 127)
                        },
                    "Selected":
                        {
                            "Edge":
                                {
                                    "PenColor": QColor(255, 0, 0, 255),
                                    "PenWidth": 1
                                },
                            "Fill": QColor(0, 255, 0, 127)
                        },
                    "Default":
                        {
                            "Edge":
                                {
                                    "PenColor": QColor(200, 0, 100, 127),
                                    "PenWidth": 1
                                },
                            "Fill": QColor(0, 255, 0, 127)
                        }
                 }
        },
    "EdgeConfig":
        {
            "EdgeColors":
                {
                    "Default":
                        {
                            "LineColor": QColor(255,255,255),
                            "ArrowEdgeColor": QColor(255,255,255),
                            "ArrowFillColor": QColor(255,255,255)
                        },
                    "Self":
                        {
                            "LineColor": QColor(255,255,255),
                            "ArrowEdgeColor": QColor(255,255,255),
                            "ArrowFillColor": QColor(255,255,255)
                        },
                }
        }
}


class QNetworkxConfig(dict):
    def __init__(self, *args, **kwargs):
        super(QNetworkxConfig, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    if isinstance(v,dict):
                        self[k] = QNetworkxConfig(v)
                    else:
                        self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                if isinstance(v, dict):
                    self[k] = QNetworkxConfig(v)
                else:
                    self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(QNetworkxConfig, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(QNetworkxConfig, self).__delitem__(key)
        del self.__dict__[key]


graph_config= QNetworkxConfig(QNetworkxConfig_default)
