#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4.QtCore import QLineF, QPointF, QRectF, QSizeF, QString, QTime, Qt, pyqtSignal, qAbs, qsrand
from PyQt4.QtGui import QAction, QApplication, QBrush, QCheckBox, QColor, QComboBox, QFont, QFontMetrics, QGraphicsItem, \
    QGraphicsScene, QGraphicsTextItem, QGraphicsView, QHBoxLayout, QInputDialog, QLineEdit, QLinearGradient, \
    QMainWindow, QMenu, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QRadialGradient, QSlider, QStyle, \
    QTransform, QVBoxLayout, QWidget
import math
import logging
from QNetworkxStylesManager import QNetworkxStylesManager

graph_config = QNetworkxStylesManager()
graph_config.load_styles()

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
        self.setZValue(11)
        self.set_label_visible(label_visible)
        self.edge_profile = 'default'
        self.edge_config = graph_config[self.edge_profile].EdgeConfig

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

        painter.setPen(QPen(self.edge_config.EdgeColors.Self.LineColor, 1, Qt.SolidLine,
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
        painter.setPen(QPen(self.edge_config.EdgeColors.Self.ArrowEdgeColor))
        painter.setBrush(QBrush(self.edge_config.EdgeColors.Self.ArrowFillColor))
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

        painter.setPen(QPen(self.edge_config.EdgeColors.Default.LineColor, 1, Qt.SolidLine,
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

        painter.setPen(QPen(self.edge_config.EdgeColors.Default.ArrowEdgeColor))
        painter.setBrush(QBrush(self.edge_config.EdgeColors.Default.ArrowFillColor))
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

