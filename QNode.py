#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt4.QtCore import QLineF, QPointF, QRectF, QSizeF, QString, QTime, Qt, pyqtSignal, qAbs, qsrand
from PyQt4.QtGui import QAction, QApplication, QBrush, QCheckBox, QColor, QComboBox, QFont, QFontMetrics, QGraphicsItem, \
    QGraphicsScene, QGraphicsTextItem, QGraphicsView, QHBoxLayout, QInputDialog, QLineEdit, QLinearGradient, \
    QMainWindow, QMenu, QPainter, QPainterPath, QPainterPathStroker, QPen, QPolygonF, QRadialGradient, QSlider, QStyle, \
    QTransform, QVBoxLayout, QWidget
from random import uniform
import math
import logging
from QNetworkxStylesManager import QNetworkxStylesManager
from NodeShapes import NodeShapes

graph_config = QNetworkxStylesManager()
graph_config.load_styles()


class QNodeGraphicItem(QGraphicsItem):
    Type = QGraphicsItem.UserType + 1

    def __init__(self, graph_widget, label, tipo):
        self._logger = logging.getLogger("QNetworkxGraph.QNodeGraphicItem")
        self._logger.setLevel(logging.DEBUG)
        super(QNodeGraphicItem, self).__init__()

        self.graph = graph_widget
        self.edgeList = []
        self.newPos = QPointF()

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(10)
        self.size = 40

        self.forceSize = 40
        self.border_width = 1
        self.label = QGraphicsTextItem(str(label))
        self.label.setParentItem(self)
        self.label.setDefaultTextColor(Qt.black)
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)
        self.animate = False
        self.menu = None
        self.setPos(uniform(-100, 100), uniform(-100, 100))
        self.node_shape = NodeShapes.SQUARE
        self.mass_center = QPointF(0, 0)
        if tipo == "metabolite":
            self.node_profile = 'default'
        else:
            self.node_profile = 'Profile_1'
        self.node_config = graph_config[self.node_profile].NodeConfig

    def set_mass_center(self, mass_center):
        self._logger.debug("Setting mass center to %s" % mass_center)
        self.mass_center = mass_center
        self.calculate_forces()
        self.advance()

    def set_node_shape(self, shape):
        if shape in NodeShapes:
            self.node_shape = shape
        else:
            raise Exception("Shape must be one of the ones defined on NodeShapes class")

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
                xvel += (dx * (7 * self.forceSize)) / l
                yvel += (dy * (7 * self.forceSize)) / l

        # Now subtract all forces pulling items together.
        weight = (len(self.edgeList) + 1) * self.forceSize
        for edge in self.edgeList:
            if edge.source_node() is self:
                pos = self.mapFromItem(edge.dest_node(), 0, 0)
            else:
                pos = self.mapFromItem(edge.source_node(), 0, 0)
            xvel += pos.x() / weight
            yvel += pos.y() / weight

        # Invisible Node pulling to the mass center
        xvel += (self.mapFromScene(self.mass_center).x() / 2) / (weight / 4)
        yvel += (self.mapFromScene(self.mass_center).y() / 2) / (weight / 4)

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
        if self.node_shape == NodeShapes.CIRCLE:
            path.addEllipse(x_coord, y_coord, width, height)
        else:
            path.addRect(x_coord, y_coord, width, height)
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

        node_colors = self.node_config

        # print self.node_config[1]

        if option.state & QStyle.State_Selected:
            pen = QPen(node_colors.Selected.Edge.PenColor)
            pen.setWidth(self.border_width * node_colors.Selected.Edge.PenWidth)
            brush = QBrush(node_colors.Selected.Fill)
        else:
            pen = QPen(node_colors.Default.Edge.PenColor)
            pen.setWidth(self.border_width * node_colors.Default.Edge.PenWidth)
            brush = QBrush(node_colors.Default.Fill)

        # Fill with gradient
        painter.setBrush(brush)
        # Set the outline pen color

        painter.setPen(pen)
        # Draw the circle
        if self.node_shape == NodeShapes.CIRCLE:
            painter.drawEllipse(x_coord, y_coord, width, height)
        else:
            painter.drawRect(x_coord, y_coord, width, height)
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
        if event.button() == Qt.RightButton:
            self.setSelected(True)
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

    def set_node_profile(self, node_profile):
        self.node_profile = node_profile
        self.node_config = graph_config[self.node_profile].NodeConfig
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
            event.setAccepted(False)
            super(QNodeGraphicItem, self).contextMenuEvent(event)
            self._logger.warning("No QNodeGraphicItem defined yet. Use add_context_menu.")

