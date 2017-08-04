#!/usr/bin/env python
# -*- coding: utf-8 -*-


# TODO: Create a color/sizes scheme for nodes, edges and background (may be with a json file)
# TODO: Create a visualization window focused on changing colours, sizes, etc of nodes edges and background
# TODO: Menu to add the different predefined Networkx Graphs (Graph generators)
#       https://networkx.github.io/documentation/development/reference/generators.html?highlight=generato
# TODO: Physic on label edges. Attraction to edge center, repulsion from near edges
# TODO: contraction of a node (if its a tree and there's no loops)
# TODO: Add methods to attach context menus to the items of the graph
# TODO: Add _logger to the classes of the library
# TODO: Make it possible that the nodes have any shape
# FIX: The circumference of a selected node appears cutted up, down, right and left.
# TODO: Multiple selection and deselection
# TODO: Create gravity centers for group of nodes

# Done: Show labels on nodes
# Done: Option to Calculate the widest label and set that width for all the nodes
# Done: Combobox menu listing the available layouts
# Done: Labels on edges
# Done: Create directed and not directed edges
# Done: Fix: Context menu on edges depend on the bounding rect, so it's very large
# Done: Make real zoom on the scene (+ and -)
# Done: Loop edges


import logging
import math
from random import uniform

import networkx as nx
from PyQt4.QtCore import QString, QPointF, Qt, QRectF, qsrand, QTime, QLineF, QSizeF, qAbs, pyqtSignal
from PyQt4.QtGui import QMainWindow, QWidget, QVBoxLayout, QSlider, QGraphicsView, QPen, QBrush, QHBoxLayout, \
    QCheckBox, QFont, QFontMetrics, QComboBox, QGraphicsTextItem, QMenu, QAction, QPainterPath, QPainterPathStroker, \
    QTransform, QGraphicsItem, QApplication, QLinearGradient, QPolygonF, QRadialGradient, QStyle, QColor, \
    QGraphicsScene, QPainter
from scipy.interpolate import interp1d

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
file_handler = logging.FileHandler('QNetworkxGraph.log')
file_handler.setLevel(logging.DEBUG)
# create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
current_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(current_format)
console_handler.setFormatter(current_format)
# add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.info('Created main logger')


class QEdgeGraphicItem(QGraphicsItem):
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QGraphicsItem.UserType + 2

    def __init__(self, first_node, second_node, label=None, directed=False, label_visible=True):
        self._logger = logging.getLogger("QNetworkxGraph.QEdgeGraphicItem")
        self._logger.setLevel(logging.DEBUG)
        super(QEdgeGraphicItem, self).__init__()

        self.arrowSize = 10.0
        self.arc_angle = 315
        self.source_point = QPointF()
        self.dest_point = QPointF()

        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        # self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        # self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.source = first_node
        self.dest = second_node
        self.node_size = 10
        if not label:
            if first_node.label is not None and second_node.label is not None:
                label = "%s - %s" % (first_node.label.toPlainText(), second_node.label.toPlainText())
            else:
                label = ''
        self.label = QGraphicsTextItem(label, self)
        self.label.setParentItem(self)
        self.label.setDefaultTextColor(Qt.white)
        self.source.add_edge(self)
        self.dest.add_edge(self)
        self.adjust()
        self.menu = QMenu()
        self.is_directed = directed
        self.set_label_visible(label_visible)

    def set_label_visible(self, boolean):
        self.label.setVisible(boolean)

    def type(self):
        return QEdgeGraphicItem.Type

    def source_node(self):
        return self.source

    def set_source_node(self, node):
        self.source = node
        self.adjust()

    def dest_node(self):
        return self.dest

    def set_dest_node(self, node):
        self.dest = node
        self.adjust()

    def adjust(self):
        if not self.source or not self.dest:
            return

        if self.source != self.dest:
            scene_line = QLineF(self.source.mapToScene(0, 0), self.dest.mapToScene(0, 0))

            scene_line_center = QPointF((scene_line.x1() + scene_line.x2()) / 2,
                                        (scene_line.y1() + scene_line.y2()) / 2)

            self.setPos(scene_line_center)

            line = QLineF(self.mapFromItem(self.source, 0, 0),
                          self.mapFromItem(self.dest, 0, 0))
            nodes_center_distance = line.length()

            self.prepareGeometryChange()

            source_node_radius = self.source.boundingRect().width() / 2
            dest_node_radius = self.dest.boundingRect().width() / 2
            if nodes_center_distance > source_node_radius + dest_node_radius + 6:
                edge_offset = QPointF((line.dx() * source_node_radius) / nodes_center_distance,
                                      (line.dy() * dest_node_radius) / nodes_center_distance)

                self.source_point = line.p1() + edge_offset
                self.dest_point = line.p2() - edge_offset
            else:
                self.source_point = line.p1()
                self.dest_point = line.p1()
                # self.setPos(self.mapToParent(self.boundingRect().center()))
                # print "Adjust of %s" % self.label.toPlainText()
        else:
            # setting and getting initial variables we will use
            angle_rad = math.radians(self.arc_angle)
            node_radius = self.source.size / 2.0
            arc_radius = node_radius * 0.60
            centers_distance = node_radius + (2 * arc_radius / 3.0)

            # calculate x, y position of the arc center from the node center
            arc_center_x = math.cos(angle_rad) * centers_distance
            arc_center_y = math.sin(angle_rad) * centers_distance

            # Visual Debug
            # painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine,
            #                           Qt.RoundCap, Qt.RoundJoin))
            # painter.drawEllipse(arc_center_x-2, arc_center_y-2, 4, 4)

            # calculate the P1 and P2 points where both circles cut (on arc coordinate)
            # http://mathworld.wolfram.com/Circle-CircleIntersection.html
            p1_cut_point_x = (math.pow(centers_distance, 2) - math.pow(node_radius, 2) + math.pow(arc_radius,
                                                                                                  2)) / float(
                (2 * centers_distance))
            p1_cut_point_y = math.sqrt(math.pow(arc_radius, 2) - math.pow(p1_cut_point_x, 2))
            p1 = QPointF(p1_cut_point_x, p1_cut_point_y)
            p2 = QPointF(p1_cut_point_x, -p1_cut_point_y)
            self.setPos(self.source.pos().x() + arc_center_x, self.source.pos().y() + arc_center_y)
            self.prepareGeometryChange()
            self.source_point = p1
            self.dest_point = p2

    def boundingRect(self):
        if not self.source or not self.dest:
            return QRectF()

        if self.source != self.dest:
            pen_width = 1.0
            extra = (pen_width + self.arrowSize) / 2.0
            return QRectF(self.source_point,
                          QSizeF(self.dest_point.x() - self.source_point.x(),
                                 self.dest_point.y() - self.source_point.y())).normalized().adjusted(-extra,
                                                                                                     -extra,
                                                                                                     extra,
                                                                                                     extra)
        else:
            return self.arc_shape().boundingRect().adjusted(0, 0, +1, +1)
            # return QRectF(-2000,-2000, 4000, 4000)

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        if self.source == self.dest:
            self.paint_arc(painter, option, widget)
        else:
            self.paint_arrow(painter, option, widget)
            # if self.label:
            #     # Calculate edge center
            #     # Calculate label width
            #     # Draw label background
            #     # Draw label text
            #     painter.drawText(QRect(x_coord, y_coord, width, height), Qt.AlignCenter, str(self.label))
            # QGraphicsItem.paint(self,painter,option,widget)

            # Debug
            # painter.setBrush(Qt.NoBrush)
            # painter.setPen(Qt.red)
            # painter.drawRect(self.boundingRect())
            # self.label.setPlainText("%s - %s (length = %s" % (self.scenePos().x(), self.scenePos().y(), line.length()))
            # print str(self.scenePos().x()) + " " + str(self.scenePos().y())
            # painter.drawPath(self.shape())
            # painter.drawRect(self.shape().boundingRect())

    def add_context_menu(self, options):
        """
        Add context menus actions the edge.

        Parameters
        ----------
        options : dict
            Dict with the text of the option as key and the name of the method to call if activated.
            The values of the dict are tuples like (object, method).
        """
        self._logger.debug("Adding custom context menu to edge %s" % str(self.label.toPlainText()))
        for option_string, callback in options.items():
            instance, method = callback
            action = QAction(option_string, self.menu)
            action.triggered.connect(getattr(instance, method))
            self.menu.addAction(action)

    def contextMenuEvent(self, event):
        self._logger.debug("ContextMenuEvent received on edge %s" % str(self.label.toPlainText()))
        if self.menu:
            self.menu.exec_(event.screenPos())
            event.setAccepted(True)
        else:
            self._logger.warning("No QEdgeGraphicsItem defined yet. Use add_context_menu.")
            event.setAccepted(False)

    def shape(self):
        if self.source == self.dest:
            new_path = self.arc_shape()
        else:
            new_path = self.arrow_shape()
        return new_path

    def paint_arc(self, painter, option, widget):
        # setting and getting initial variables we will use
        node_radius = self.source.size / 2.0
        arc_radius = node_radius * 0.60
        # # Translate also the painter to keep it synchronized to
        # painter.translate(arc_center_x, arc_center_y)
        painter.rotate(180 + self.arc_angle)
        # painter.scale(-1,1)
        # painter.rotate(180)

        painter.setPen(QPen(Qt.white, 1, Qt.SolidLine,
                            Qt.RoundCap, Qt.RoundJoin))
        # Debug visual information
        # painter.drawEllipse(p1, 4, 4)
        # painter.drawText(p1, "P1")
        # # painter.drawText(p1, "      %s , %s" % (p1.x(), p1.y()))
        # painter.drawEllipse(p2, 4, 4)
        # painter.drawText(p2, "P2")
        # # painter.drawText(p2, "      %s , %s" % (p2.x(), p2.y()))
        # painter.drawEllipse(-2,-2, 4, 4)
        # painter.drawEllipse(-2,-2, 4, 4)
        # painter.drawEllipse(-2, 40, 4, 4)
        # painter.drawEllipse(-2, 40, 4, 4)
        # painter.drawText(0,40, "0x,40y")
        # painter.drawEllipse(40, -2, 4, 4)
        # painter.drawEllipse(40, -2, 4, 4)
        # painter.drawText(40, 0, "40x,0y")

        # Calculate the P1 and P2 angle on arc circle coordinates
        p1_angle = math.atan2(self.source_point.y(), self.source_point.x())
        p2_angle = math.atan2(self.dest_point.y(), self.dest_point.x())

        p1_angle_normalized = p1_angle % (2 * math.pi)
        p2_angle_normalized = p2_angle % (2 * math.pi)
        difference = abs(p1_angle_normalized - p2_angle_normalized) % (2 * math.pi)
        span_angle = (2 * math.pi) - difference if difference < math.pi else difference

        p1_angle_degrees = math.degrees(p1_angle_normalized)
        span_angle_degrees = math.degrees(span_angle)

        painter.drawArc(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2, p1_angle_degrees * 16,
                        span_angle_degrees * 16)

        # Arrows of the arc
        source_arrow_p1 = self.source_point + QPointF(
            math.sin(
                p1_angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                p1_angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        source_arrow_p2 = self.source_point + QPointF(
            math.sin(
                p1_angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                p1_angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p1 = self.dest_point + QPointF(
            math.sin(
                p2_angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                p2_angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p2 = self.dest_point + QPointF(
            math.sin(
                p2_angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                p2_angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        painter.setBrush(Qt.white)
        if not self.is_directed:
            painter.drawPolygon(QPolygonF([self.source_point, source_arrow_p1, source_arrow_p2]))
        painter.drawPolygon(QPolygonF([self.dest_point, dest_arrow_p1, dest_arrow_p2]))

        # Visual debug
        # painter.setPen(QPen(Qt.red, 1, Qt.SolidLine,
        #                           Qt.RoundCap, Qt.RoundJoin))
        # painter.drawArc(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2, p1_angle_degrees * 16, 20 * 16)
        # painter.setPen(QPen(Qt.yellow, 1, Qt.SolidLine,
        #                           Qt.RoundCap, Qt.RoundJoin))
        # painter.drawArc(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2, 0 * 16,
        #                 45 * 16)
        # self.setZValue(3)

    def paint_arrow(self, painter, option, widget):
        # Draw the line itself.
        line = QLineF(self.source_point, self.dest_point)

        if line.length() == 0.0:
            return

        painter.setPen(QPen(Qt.white, 1, Qt.SolidLine,
                            Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = QEdgeGraphicItem.TwoPi - angle

        source_arrow_p1 = self.source_point + QPointF(
            math.sin(
                angle + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        source_arrow_p2 = self.source_point + QPointF(
            math.sin(
                angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p1 = self.dest_point + QPointF(
            math.sin(
                angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p2 = self.dest_point + QPointF(
            math.sin(
                angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        painter.setBrush(Qt.white)
        if not self.is_directed:
            painter.drawPolygon(QPolygonF([line.p1(), source_arrow_p1, source_arrow_p2]))
        painter.drawPolygon(QPolygonF([line.p2(), dest_arrow_p1, dest_arrow_p2]))

    def arc_shape(self):
        shape = QPainterPath()
        # setting and getting initial variables we will use
        angle_rad = math.radians(self.arc_angle)
        node_radius = self.source.size / 2.0
        arc_radius = node_radius * 0.60
        centers_distance = node_radius + (2 * arc_radius / 3.0)

        # calculate x, y position of the arc center from the node center
        arc_center_x = math.cos(angle_rad) * centers_distance
        arc_center_y = math.sin(angle_rad) * centers_distance

        # Visual Debug
        # painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine,
        #                           Qt.RoundCap, Qt.RoundJoin))
        # painter.drawEllipse(arc_center_x-2, arc_center_y-2, 4, 4)

        # calculate the P1 and P2 points where both circles cut (on arc coordinate)
        # http://mathworld.wolfram.com/Circle-CircleIntersection.html
        p1_cut_point_x = (math.pow(centers_distance, 2) - math.pow(node_radius, 2) + math.pow(arc_radius, 2)) / float(
            (2 * centers_distance))
        p1_cut_point_y = math.sqrt(math.pow(arc_radius, 2) - math.pow(p1_cut_point_x, 2))
        p1 = QPointF(p1_cut_point_x, p1_cut_point_y)
        p2 = QPointF(p1_cut_point_x, -p1_cut_point_y)

        transform = QTransform()
        # # Translate also the painter to keep it synchronized to
        transform.translate(arc_center_x, arc_center_y)
        transform.rotate(180 + self.arc_angle)
        shape = transform.map(shape)
        # painter.scale(-1,1)
        # painter.rotate(180)

        # shape.setPen(QPen(Qt.cyan, 1, Qt.SolidLine,
        #                           Qt.RoundCap, Qt.RoundJoin))
        # Debug visual information
        # painter.drawEllipse(p1, 4, 4)
        # painter.drawText(p1, "P1")
        # # painter.drawText(p1, "      %s , %s" % (p1.x(), p1.y()))
        # painter.drawEllipse(p2, 4, 4)
        # painter.drawText(p2, "P2")
        # # painter.drawText(p2, "      %s , %s" % (p2.x(), p2.y()))
        # painter.drawEllipse(-2,-2, 4, 4)
        # painter.drawEllipse(-2,-2, 4, 4)
        # painter.drawEllipse(-2, 40, 4, 4)
        # painter.drawEllipse(-2, 40, 4, 4)
        # painter.drawText(0,40, "0x,40y")
        # painter.drawEllipse(40, -2, 4, 4)
        # painter.drawEllipse(40, -2, 4, 4)
        # painter.drawText(40, 0, "40x,0y")

        # Calculate the P1 and P2 angle on arc circle coordinates
        p1_angle = math.atan2(p1.y(), p1.x())
        p2_angle = math.atan2(p2.y(), p2.x())

        p1_angle_normalized = p1_angle % (2 * math.pi)
        p2_angle_normalized = p2_angle % (2 * math.pi)
        difference = abs(p1_angle_normalized - p2_angle_normalized) % (2 * math.pi)
        span_angle = (2 * math.pi) - difference if difference < math.pi else difference

        p1_angle_degrees = math.degrees(p1_angle_normalized)
        span_angle_degrees = math.degrees(span_angle)

        shape.arcTo(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2, p1_angle_degrees * 16,
                    span_angle_degrees * 16)
        # Expand the shape 2 pixels to be able to click on edge lines
        stroker = QPainterPathStroker()
        stroker.setWidth(2)
        stroker.setJoinStyle(Qt.MiterJoin)
        shape = (stroker.createStroke(shape) + shape).simplified()
        return shape

        # Visual debug
        # painter.setPen(QPen(Qt.red, 1, Qt.SolidLine,
        #                           Qt.RoundCap, Qt.RoundJoin))
        # painter.drawArc(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2, p1_angle_degrees * 16, 20 * 16)
        # painter.setPen(QPen(Qt.yellow, 1, Qt.SolidLine,
        #                           Qt.RoundCap, Qt.RoundJoin))
        # painter.drawArc(-arc_radius, -arc_radius, arc_radius * 2, arc_radius * 2, 0 * 16,
        #                 45 * 16)

    def arrow_shape(self):
        shape_path = QPainterPath()
        if not self.source or not self.dest:
            return

            # Draw the line itself.
        line = QLineF(self.source_point, self.dest_point)

        if line.length() == 0.0:
            return

        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = QEdgeGraphicItem.TwoPi - angle

        source_arrow_p1 = self.source_point + QPointF(
            math.sin(
                angle + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        source_arrow_p2 = self.source_point + QPointF(
            math.sin(
                angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p1 = self.dest_point + QPointF(
            math.sin(
                angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p2 = self.dest_point + QPointF(
            math.sin(
                angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        if not self.is_directed:
            shape_path.addPolygon(QPolygonF([line.p1(), source_arrow_p1, source_arrow_p2]))
        shape_path.moveTo(self.source_point)
        shape_path.lineTo(self.dest_point)
        shape_path.addPolygon(QPolygonF([line.p2(), dest_arrow_p1, dest_arrow_p2]))

        # Expand the shape 2 pixels to be able to click on edge lines
        stroker = QPainterPathStroker()
        stroker.setWidth(2)
        stroker.setJoinStyle(Qt.MiterJoin)
        new_path = (stroker.createStroke(shape_path) + shape_path).simplified()
        return new_path


class QNodeGraphicItem(QGraphicsItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, graph_widget, label):
        self._logger = logging.getLogger("QNetworkxGraph.QEdgeGraphicItem")
        self._logger.setLevel(logging.DEBUG)
        super(QNodeGraphicItem, self).__init__()

        self.graph = graph_widget
        self.edgeList = []
        self.newPos = QPointF()

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)
        self.size = 40
        self.border_width = 4
        self.label = QGraphicsTextItem(str(label))
        self.label.setParentItem(self)
        self.label.setDefaultTextColor(Qt.white)
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)
        self.animate = True
        self.menu = None
        self.setPos(uniform(-10, 10), uniform(-10, 10))

    def type(self):
        return QNodeGraphicItem.Type

    def add_edge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList

    def calculate_forces(self):
        if not self.scene() or self.scene().mouseGrabberItem() is self or not self.animate:
            self.newPos = self.pos()
            return

        # Sum up all forces pushing this item away.
        xvel = 0.0
        yvel = 0.0
        for item in self.scene().items():
            if not isinstance(item, QNodeGraphicItem):
                continue

            line = QLineF(self.mapFromItem(item, 0, 0),
                          QPointF(0, 0))
            dx = line.dx()
            dy = line.dy()
            l = 2.0 * (dx * dx + dy * dy)
            if l > 0:
                xvel += (dx * (7 * self.size)) / l
                yvel += (dy * (7 * self.size)) / l

        # Now subtract all forces pulling items together.
        weight = (len(self.edgeList) + 1) * self.size
        for edge in self.edgeList:
            if edge.source_node() is self:
                pos = self.mapFromItem(edge.dest_node(), 0, 0)
            else:
                pos = self.mapFromItem(edge.source_node(), 0, 0)
            xvel += pos.x() / weight
            yvel += pos.y() / weight

        # Invisible Node pulling to the center
        xvel -= (self.pos().x() / 2) / (weight / 4)
        yvel -= (self.pos().y() / 2) / (weight / 4)

        if qAbs(xvel) < 0.1 and qAbs(yvel) < 0.1:
            xvel = yvel = 0.0

        scene_rect = self.scene().sceneRect()
        self.newPos = self.pos() + QPointF(xvel, yvel)
        self.newPos.setX(min(max(self.newPos.x(), scene_rect.left() + 10), scene_rect.right() - 10))
        self.newPos.setY(min(max(self.newPos.y(), scene_rect.top() + 10), scene_rect.bottom() - 10))

    def advance(self):
        if self.newPos == self.pos() or self.isSelected():
            return False

        self.setPos(self.newPos)
        return True

    def boundingRect(self):
        x_coord = y_coord = (-1 * (self.size / 2)) - self.border_width / 2
        width = height = 2 + self.size + self.border_width / 2
        return QRectF(x_coord, y_coord, width,
                      height)

    def shape(self):
        x_coord = y_coord = (-1 * (self.size / 2)) - self.border_width
        width = height = self.size
        path = QPainterPath()
        path.addEllipse(x_coord, y_coord, width, height)
        return path

    def paint(self, painter, option, widget):
        x_coord = y_coord = -(self.size / 2)
        width = height = self.size
        painter.save()
        # Draw the shadow
        # painter.setPen(Qt.NoPen)
        # painter.setBrush(Qt.darkGray)
        # painter.drawEllipse(x_coord+3, y_coord+3, width, height)

        # Gradient depends on the image selected or not
        gradient = QRadialGradient(-3, -3, 10)
        if option.state & QStyle.State_Sunken:
            gradient.setCenter(3, 3)
            gradient.setFocalPoint(3, 3)
            gradient.setColorAt(1, QColor(Qt.lightGray).light(120))
            gradient.setColorAt(0, QColor(Qt.black).light(120))
            pen = QPen(Qt.lightGray)
            pen.setWidth(self.border_width * 2)
        elif option.state & QStyle.State_Selected:
            gradient.setColorAt(0, Qt.blue)
            gradient.setColorAt(1, Qt.darkBlue)
            pen = QPen(QColor(255, 0, 0, 255))
            pen.setWidth(self.border_width)
        else:
            gradient.setColorAt(0, Qt.blue)
            gradient.setColorAt(1, Qt.darkBlue)
            pen = QPen(QColor(200, 0, 100, 127))
            pen.setWidth(self.border_width)

        # Fill with gradient
        painter.setBrush(QBrush(QColor(100, 0, 200, 127)))
        # Set the outline pen color

        painter.setPen(pen)
        # Draw the circle
        painter.drawEllipse(x_coord, y_coord, width, height)
        # painter.setPen(Qt.white)
        # painter.drawText(QRect(x_coord,y_coord, width, height), Qt.AlignCenter, str(self.label))
        painter.restore()
        # self.setOpacity(0.5)
        # print "Node: " + str(self.scenePos().x()) + " " + str(self.scenePos().y())

        # Debug
        # painter.setBrush(Qt.NoBrush)
        # painter.setPen(Qt.red)
        # painter.drawRect(self.boundingRect())
        # painter.drawEllipse(-3, -3, 6, 6)
        # self.label.setPlainText("%s - %s" % (self.scenePos().x(), self.scenePos().y()))

    def node_label_width(self):
        font = QFont()
        font.setFamily(font.defaultFamily())
        fm = QFontMetrics(font)
        label_width = fm.width(QString(str(self.label.toPlainText()))) + self.border_width * 2 + 40
        return label_width

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edgeList:
                edge.adjust()
            self.graph.item_moved()

        return super(QNodeGraphicItem, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(QNodeGraphicItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super(QNodeGraphicItem, self).mouseReleaseEvent(event)

    def set_size(self, new_size):
        self.prepareGeometryChange()
        self.size = new_size
        self.calculate_forces()
        self.advance()
        self.update()

    def animate_node(self, animate):
        self.animate = animate

    def add_context_menu(self, options):
        """
        Add context menus actions the edge.

        Parameters
        ----------
        options : dict
            Dict with the text of the option as key and the name of the method to call if activated.
            The values of the dict are tuples like (object, method).
        """
        self._logger.debug("Adding custom context menu to node %s" % str(self.label.toPlainText()))
        self.menu = QMenu()
        for option_string, callback in options.items():
            instance, method = callback
            action = QAction(option_string, self.menu)
            action.triggered.connect(getattr(instance, method))
            self.menu.addAction(action)

    def contextMenuEvent(self, event):
        self._logger.debug("ContextMenuEvent received on node %s" % str(self.label.toPlainText()))
        selection_path = QPainterPath()
        selection_path.addPolygon(self.mapToScene(self.boundingRect()))
        if event.modifiers() & Qt.CTRL:
            selection_path += self.scene().selectionArea()
        else:
            self.scene().clearSelection()
        self.scene().setSelectionArea(selection_path)
        if self.menu:
            self.menu.exec_(event.screenPos())
            event.setAccepted(True)
        else:
            self._logger.warning("No QNodeGraphicItem defined yet. Use add_context_menu.")


class QNetworkxWidget(QGraphicsView):
    node_selection_changed = pyqtSignal(list)

    def __init__(self, directed=False, parent=None):
        super(QNetworkxWidget, self).__init__(parent)

        self.timer_id = 0
        self.background_color = QColor(0, 0, 0)
        self.last_position = None
        self.current_position = None
        self.panning_mode = False

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.scene.setSceneRect(-400, -400, 800, 800)
        self.setScene(self.scene)
        self.scene.selectionChanged.connect(self.on_selection_change)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMinimumSize(400, 400)
        self.setWindowTitle("QNetworkXWidget")

        self.nodes = {}
        self.edges = {}
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.is_directed = directed

        self._scale_factor = 1.15
        self.set_panning_mode(False)
        self.menu = QMenu()
        action1 = QAction("Panning mode", self)
        action1.triggered.connect(self.set_panning_mode)
        action1.setCheckable(True)
        self.menu.addSeparator()
        self.menu.addAction(action1)

    #     self.zoom_in_action = QAction("Zoom in", self)
    #     self.zoom_in_action.setShortcut("Ctrl++")
    #     self.zoom_in_action.triggered.connect(self.zoom_in_one_step)
    #     self.zoom_out_action = QAction("Zoom out", self)
    #     self.zoom_out_action.setShortcut("Ctrl+-")
    #     self.zoom_out_action.triggered.connect(self.zoom_out_one_step)
    #     # self.scale(self._scale, self._scale)
    #
    # def zoom_in_one_step(self):
    #     self.scale(self._scale_factor, self._scale_factor)
    #
    # def zoom_out_one_step(self):
    #     self.scale(1/self._scale_factor, 1/self._scale_factor)

    def on_selection_change(self):
        selected_nodes = self.selected_nodes()
        self.node_selection_changed.emit(selected_nodes)

    def selected_nodes(self):
        changed = self.scene.selectedItems()
        selected_nodes = []
        for item in changed:
            if isinstance(item, QNodeGraphicItem):
                selected_nodes.append(item.label.toPlainText())
        return selected_nodes

    def set_panning_mode(self, mode=False):
        self.panning_mode = mode
        if self.panning_mode:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def get_current_nodes_positions(self):
        position_dict = {}
        for node_label, item in self.nodes.items():
            position_dict[node_label] = (item.pos().x(), item.pos().y())
        return position_dict

    def set_scale_factor(self, scale_factor):
        self._scale_factor = scale_factor

    def item_moved(self):
        if not self.timer_id:
            self.timer_id = self.startTimer(1000 / 25)

    def add_node(self, label=None):
        if label is None:
            node_label = "Node %s" % len(self.nodes)
        else:
            node_label = label
        if isinstance(label, QString):
            label = unicode(label.toUtf8(), encoding="UTF-8")
        if label not in self.nodes:
            node = QNodeGraphicItem(self, node_label)
            self.nodes[node_label] = node
            self.scene.addItem(node)
        else:
            # TODO: raise exception
            pass

    def add_edge(self, label=None, first_node=None, second_node=None, node_tuple=None, label_visible=True):
        if node_tuple:
            node1_str, node2_str = node_tuple
            if node1_str in self.nodes and node2_str in self.nodes:
                node1 = self.nodes[node1_str]
                node2 = self.nodes[node2_str]
        elif first_node and second_node:
            if isinstance(first_node, basestring):
                node1 = self.nodes[first_node]
            elif isinstance(first_node, QNodeGraphicItem):
                node1 = first_node
            elif isinstance(first_node, QString):
                node1 = self.nodes[unicode(first_node.toUtf8(), encoding="UTF-8")]
            else:
                raise Exception("Nodes must be existing labels on the graph or QNodeGraphicItem")
            if isinstance(second_node, basestring):
                node2 = self.nodes[second_node]
            elif isinstance(second_node, QNodeGraphicItem):
                node2 = second_node
            elif isinstance(second_node, QString):
                node2 = self.nodes[unicode(second_node.toUtf8(), encoding="UTF-8")]
            else:
                raise Exception("Nodes must be existing labels on the graph or QNodeGraphicItem")

        edge = QEdgeGraphicItem(first_node=node1, second_node=node2, label=label, directed=self.is_directed,
                                label_visible=label_visible)
        edge.adjust()
        if edge and edge.label.toPlainText() not in self.edges:
            self.edges[edge.label.toPlainText()] = edge
            self.scene.addItem(edge)
            # self.scene.addItem(edge.label)

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Plus:
            self.scale_view(self._scale_factor)
        elif key == Qt.Key_Minus:
            self.scale_view(1 / self._scale_factor)
        else:
            super(QNetworkxWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.panning_mode:
            if event.button() == Qt.MidButton or (event.buttons() & Qt.RightButton and event.buttons() & Qt.LeftButton):
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                self.last_position = event.pos()

        QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.panning_mode:
            if self.dragMode() == QGraphicsView.ScrollHandDrag:
                self.current_position = event.pos()
                dx = self.current_position.x() - self.last_position.x()
                dy = self.current_position.y() - self.last_position.y()
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
                self.last_position = self.current_position

        QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.panning_mode:
            self.setDragMode(QGraphicsView.NoDrag)

        QGraphicsView.mouseReleaseEvent(self, event)

    def timerEvent(self, event):
        nodes = self.nodes.values()

        for node in nodes:
            node.calculate_forces()

        items_moved = False
        for node in nodes:
            if node.advance():
                items_moved = True

        if not items_moved:
            self.killTimer(self.timer_id)
            self.timer_id = 0

    def wheelEvent(self, event):
        self.scale_view(math.pow(2.0, -event.delta() / 240.0))

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        # self.centerOn(self.mapToScene(0, 0))
        self.resize_scene()

    def resize_scene(self):
        if self.panning_mode:
            rect = self.mapToScene(self.viewport().geometry()).boundingRect()
            initial_height = rect.height()
            initial_width = rect.width()
            rect.setLeft(rect.left() - initial_width)
            rect.setRight(rect.right() + initial_width)
            rect.setTop(rect.top() - initial_height)
            rect.setBottom(rect.bottom() + initial_height)
            self.scene.setSceneRect(rect)
        else:
            self.scene.setSceneRect(self.mapToScene(self.viewport().geometry()).boundingRect())

    def drawBackground(self, painter, rect):
        # Shadow.
        scene_rect = self.sceneRect()
        # rightShadow = QRectF(sceneRect.right(), sceneRect.top() + 5, 5,
        #                             sceneRect.height())
        # bottomShadow = QRectF(sceneRect.left() + 5, sceneRect.bottom(),
        #                              sceneRect.width(), 5)
        # if rightShadow.intersects(rect) or rightShadow.contains(rect):
        #     painter.fillRect(rightShadow, Qt.darkGray)
        # if bottomShadow.intersects(rect) or bottomShadow.contains(rect):
        #     painter.fillRect(bottomShadow, Qt.darkGray)

        # Fill.
        gradient = QLinearGradient(scene_rect.topLeft(),
                                   scene_rect.bottomRight())
        gradient.setColorAt(0, Qt.black)
        gradient.setColorAt(1, Qt.darkGray)
        painter.fillRect(rect.intersect(scene_rect), QBrush(self.background_color))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(scene_rect)
        self.scene.addEllipse(-10, -10, 20, 20,
                              QPen(Qt.white), QBrush(Qt.SolidPattern))

    def set_node_size(self, size):
        nodes = self.nodes.values()
        edges = self.edges.values()
        for node in nodes:
            node.set_size(size)
        for edge in edges:
            edge.adjust()

    def animate_nodes(self, animate):
        for node in self.nodes.values():
            node.animate_node(animate)
            if animate:
                node.calculate_forces()
                node.advance()

    def stop_animation(self):
        self.animate_nodes(False)

    def start_animation(self):
        self.animate_nodes(True)

    def set_node_positions(self, position_dict):
        for node_str, position in position_dict.items():
            if node_str in self.nodes:
                node = self.nodes[node_str]
                node.setPos(position[0], position[1])
                node.update()
                for edge in node.edges():
                    edge.adjust()
                    edge.update()

    def resize_nodes_to_minimum_label_width(self):
        node_label_width_list = []
        for node in self.nodes.values():
            node_label_width_list.append(node.node_label_width())
        max_width = max(node_label_width_list)
        self.set_node_size(max_width)
        return max_width

    def scale_view(self, scale_factor):
        factor = self.matrix().scale(scale_factor, scale_factor).mapRect(QRectF(0, 0, 1, 1)).width()

        if factor < 0.07 or factor > 100:
            return

        self.scale(scale_factor, scale_factor)
        self.resize_scene()

    def add_context_menu(self, options, related_classes=["graph"]):
        """
        Add variable context menus actions to the graph elements.

        Parameters
        ----------
        options : dict
            Dict with the text of the option as key and the name of the method to call if activated.
            The values of the dict are tuples like (object, method).
        related_classes:
            List of elements to add the menu actions ["nodes", "edges", "graph"]
        """
        if "nodes" in related_classes:
            for node in self.nodes.values():
                node.add_context_menu(options)
        if "edges" in related_classes:
            for edge in self.edges.values():
                edge.add_context_menu(options)
        if "graph" in related_classes:
            for option_string, callback in options.items():
                instance, method = callback
                action1 = QAction(option_string, self)
                action1.triggered.connect(getattr(instance, method))
                self.addAction(action1)

    def delete_graph(self):
        for node in self.nodes.values():
            self.scene.removeItem(node)
        for edge in self.edges.values():
            self.scene.removeItem(edge)
        self.nodes.clear()
        self.edges.clear()

    def clear(self):
        self.delete_graph()

    def contextMenuEvent(self, event):
        # self._logger.debug("ContextMenuEvent received on graph")
        if self.menu:
            self.menu.exec_(event.scenePos())
            event.setAccepted(True)
        else:
            self._logger.warning("No QNodeGraphicItem defined yet. Use add_context_menu.")


class QNetworkxController(object):
    def __init__(self):
        self.graph_widget = QNetworkxWidget(directed=True)
        self.graph = nx.Graph()
        # self.node_positions = self.construct_the_graph()

    def print_something(self):
        print "THAT THING"

    def delete_graph(self):
        self.graph_widget.delete_graph()
        self.graph = None

    def set_graph(self, g, initial_pos=None):
        self.graph = g

        for node in self.graph.nodes():
            self.graph_widget.add_node(node)

        for edge in self.graph.edges():
            self.graph_widget.add_edge(node_tuple=edge)

        if not initial_pos:
            initial_pos = nx.circular_layout(self.graph)

        initial_pos = self.networkx_positions_to_pixels(initial_pos)
        self.graph_widget.set_node_positions(initial_pos)

    def set_elements_context_menus(self, options_dict, elements):
        self.graph_widget.add_context_menu(options_dict, elements)

    def networkx_positions_to_pixels(self, position_dict):
        pixel_positions = {}
        minimum = min(map(min, zip(*position_dict.values())))
        maximum = max(map(max, zip(*position_dict.values())))
        for node, pos in position_dict.items():
            s_r = self.graph_widget.scene.sceneRect()
            if minimum != maximum:
                m = interp1d([minimum, maximum], [s_r.y(), s_r.y() + s_r.height()])
                pixel_positions[node] = (m(pos[0]), m(pos[1]))
            else:
                pixel_positions[node] = (s_r.center().x(), s_r.center().y())
        return pixel_positions

    def get_widget(self):
        return self.graph_widget

        # scene.addItem(node2)
        # scene.addItem(node3)
        # scene.addItem(node4)
        # scene.addItem(self.centerNode)
        # scene.addItem(node6)
        # scene.addItem(node7)
        # scene.addItem(node8)
        # scene.addItem(node9)
        # scene.addItem()
        # scene.addItem(QEdgeGraphicItem(node2, node3))
        # scene.addItem(QEdgeGraphicItem(node2, self.centerNode))
        # scene.addItem(QEdgeGraphicItem(node3, node6))
        # scene.addItem(QEdgeGraphicItem(node4, node1))
        # scene.addItem(QEdgeGraphicItem(node4, self.centerNode))
        # scene.addItem(QEdgeGraphicItem(self.centerNode, node6))
        # scene.addItem(QEdgeGraphicItem(self.centerNode, node8))
        # scene.addItem(QEdgeGraphicItem(node6, node9))
        # scene.addItem(QEdgeGraphicItem(node7, node4))
        # scene.addItem(QEdgeGraphicItem(node8, node7))
        # scene.addItem(QEdgeGraphicItem(node9, node8))
        #
        # node1.setPos(-50, -50)
        # node2.setPos(0, -50)
        # node3.setPos(50, -50)
        # node4.setPos(-50, 0)
        # self.centerNode.setPos(0, 0)
        # node6.setPos(50, 0)
        # node7.setPos(-50, 50)
        # node8.setPos(0, 50)
        # node9.setPos(50, 50)

        # X = set(n for n, d in self.graph.nodes(data=True) if d['bipartite'] == 0)
        # Y = set(self.graph) - X
        #
        # X = sorted(X, reverse=True)
        # Y = sorted(Y, reverse=True)
        #
        # self.node_positions.update((n, (1, i)) for i, n in enumerate(X))  # put nodes from X at x=1
        # self.node_positions.update((n, (2, i)) for i, n in enumerate(Y))  # put nodes from Y at x=2
        # return nx.spring_layout(self.graph)


class QNetworkxWindowExample(QMainWindow):
    def __init__(self, parent=None):
        super(QNetworkxWindowExample, self).__init__(parent)

        self.main_layout = QVBoxLayout()

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)
        self.network_controller = QNetworkxController()

        self.graph_widget = self.network_controller.get_widget()
        self.main_layout.addWidget(self.graph_widget)

        self.horizontal_layout = QHBoxLayout()
        self.main_layout.addLayout(self.horizontal_layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximum(200)
        self.slider.setMinimum(10)
        self.slider.valueChanged.connect(self.graph_widget.set_node_size)
        self.horizontal_layout.addWidget(self.slider)

        self.animation_checkbox = QCheckBox("Animate graph")
        self.horizontal_layout.addWidget(self.animation_checkbox)
        self.animation_checkbox.stateChanged.connect(self.graph_widget.animate_nodes)
        self.graph_model = nx.complete_graph(10)
        # self.graph_model.add_edge(1,1)
        initial_positions = nx.circular_layout(self.graph_model)
        self.network_controller.set_graph(self.graph_model, initial_positions)
        self.graph_widget.animate_nodes(self.animation_checkbox.checkState())
        current_width = self.graph_widget.resize_nodes_to_minimum_label_width()
        self.slider.setValue(current_width)

        self.layouts_combo = QComboBox()
        for layout_method in dir(ly):
            if "_layout" in layout_method and callable(getattr(ly, layout_method)) and layout_method[0] != '_':
                self.layouts_combo.addItem(layout_method)
        self.main_layout.addWidget(self.layouts_combo)
        self.layouts_combo.currentIndexChanged.connect(self.on_change_layout)

        a = {
            "Option 1": (self.network_controller, "print_something"),
            "option 2": (self.network_controller, "print_something")
        }
        self.network_controller.set_elements_context_menus(a, ["edges"])
        print self.graph_widget.get_current_nodes_positions()
        # self.create_looped_graph()

    def create_looped_graph(self):
        self.network_controller.delete_graph()
        self.graph_model = nx.DiGraph()
        self.graph_model.add_node("Patata")
        self.graph_model.add_edge("Patata", "Patata")
        self.network_controller.set_graph(self.graph_model)
        self.graph_widget.animate_nodes(self.animation_checkbox.checkState())
        self.graph_widget.set_node_size(200)

    def on_change_layout(self, index):
        item = self.layouts_combo.itemText(index)
        layout_method = getattr(ly, str(item))
        pos = layout_method(self.graph_model)
        pos = self.network_controller.networkx_positions_to_pixels(pos)
        self.graph_widget.set_node_positions(pos)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))
    window = QNetworkxWindowExample()
    window.showMaximized()

    sys.exit(app.exec_())
