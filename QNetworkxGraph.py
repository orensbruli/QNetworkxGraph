#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

# TODO: Create a color/sizes scheme for nodes, edges and background (may be with a json file)
# TODO: Menu to add the different predefined Networkx Graphs (Graph generators)
#       https://networkx.github.io/documentation/development/reference/generators.html?highlight=generato
# TODO: Create directed and not directed edges
# TODO: Physhic on label edges. Atraction to edge center, repulsion from near edges
# TODO: Loop edges
# TODO: contraction of a node (if its a tree an there's no loops)


# Done: Show labels on nodes
# Done: Option to Calculate the widest label and set that width for all the nodes
# Done: Combobox menu listing the available layouts
# Done: Labels on edges


import math

import networkx as nx
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QString
from PyQt4.QtGui import QMainWindow, QWidget, QVBoxLayout, QSlider, QGraphicsView, QPen, QBrush, QHBoxLayout, QCheckBox, \
    QFont, QFontMetrics, QComboBox, QGraphicsTextItem
from scipy.interpolate import interp1d


class QEdgeGraphicItem(QtGui.QGraphicsItem):
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QtGui.QGraphicsItem.UserType + 2

    def __init__(self, source_node, dest_node, label=None):
        super(QEdgeGraphicItem, self).__init__()

        self.arrowSize = 10.0
        self.source_point = QtCore.QPointF()
        self.dest_point = QtCore.QPointF()

        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        self.source = source_node
        self.dest = dest_node
        self.node_size = 10
        if not label:
            if source_node.label is not None and dest_node.label is not None:
                label = "%s - %s" % (source_node.label.toPlainText(), dest_node.label.toPlainText())
            else:
                label = ''
        self.label = QGraphicsTextItem(label, self)
        self.label.setParentItem(self)
        self.label.setDefaultTextColor(QtCore.Qt.white)
        self.source.add_edge(self)
        self.dest.add_edge(self)
        self.adjust()

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

        line = QtCore.QLineF(self.mapFromItem(self.source, 0, 0),
                             self.mapFromItem(self.dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        if length > self.node_size:
            edge_offset = QtCore.QPointF((line.dx() * (self.node_size/2)) / length,
                                         (line.dy() * (self.node_size/2)) / length)

            self.source_point = line.p1() + edge_offset
            self.dest_point = line.p2() - edge_offset
        else:
            self.source_point = line.p1()
            self.dest_point = line.p1()
        self.setPos(self.mapToScene(self.boundingRect().center()))
        self.update()

    def boundingRect(self):
        # print "CALLED"
        if not self.source or not self.dest:
            return QtCore.QRectF()

        pen_width = 1.0
        extra = (pen_width + self.arrowSize) / 2.0

        # return QtCore.QRectF(-100,-100,200,200)
        return QtCore.QRectF(self.source_point,
                             QtCore.QSizeF(self.dest_point.x() - self.source_point.x(),
                                           self.dest_point.y() - self.source_point.y())).normalized().adjusted(-extra,
                                                                                                               -extra,
                                                                                                               extra,
                                                                                                               extra)

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        # Draw the line itself.
        line = QtCore.QLineF(self.source_point, self.dest_point)

        if line.length() == 0.0:
            return

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1, QtCore.Qt.SolidLine,
                                  QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = QEdgeGraphicItem.TwoPi - angle

        source_arrow_p1 = self.source_point + QtCore.QPointF(
            math.sin(
                angle + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        source_arrow_p2 = self.source_point + QtCore.QPointF(
            math.sin(
                angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p1 = self.dest_point + QtCore.QPointF(
            math.sin(
                angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle - QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        dest_arrow_p2 = self.dest_point + QtCore.QPointF(
            math.sin(
                angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize,
            math.cos(
                angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3
            ) * self.arrowSize)

        painter.setBrush(QtCore.Qt.white)
        painter.drawPolygon(QtGui.QPolygonF([line.p1(), source_arrow_p1, source_arrow_p2]))
        painter.drawPolygon(QtGui.QPolygonF([line.p2(), dest_arrow_p1, dest_arrow_p2]))
        # if self.label:
        #     # Calculate edge center
        #     # Calculate label width
        #     # Draw label background
        #     # Draw label text
        #     painter.drawText(QRect(x_coord, y_coord, width, height), QtCore.Qt.AlignCenter, str(self.label))
        # QtGui.QGraphicsItem.paint(self,painter,option,widget)
        # painter.setBrush(QtCore.Qt.NoBrush)
        # painter.setPen(QtCore.Qt.red)
        # painter.drawRect(self.boundingRect())
        # print str(self.scenePos().x()) + " " + str(self.scenePos().y())

    def set_node_size(self, new_size):
        self.node_size = new_size
        self.update()


class QNodeGraphicItem(QtGui.QGraphicsItem):
    Type = QtGui.QGraphicsItem.UserType + 1

    def __init__(self, graph_widget, label):
        super(QNodeGraphicItem, self).__init__()

        self.graph = graph_widget
        self.edgeList = []
        self.newPos = QtCore.QPointF()

        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)
        self.size = 40
        self.border_width = 4
        self.label = QGraphicsTextItem(str(label), self)
        self.label.setParentItem(self)
        self.label.setDefaultTextColor(QtCore.Qt.white)
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width()/2, -rect.height()/2)
        self.animate = True

    def type(self):
        return QNodeGraphicItem.Type

    def add_edge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList

    def calculate_forces(self):
        if not self.scene() or self.scene().mouseGrabberItem() is self:
            self.newPos = self.pos()
            return

        # Sum up all forces pushing this item away.
        xvel = 0.0
        yvel = 0.0
        for item in self.scene().items():
            if not isinstance(item, QNodeGraphicItem):
                continue

            line = QtCore.QLineF(self.mapFromItem(item, 0, 0),
                                 QtCore.QPointF(0, 0))
            dx = line.dx()
            dy = line.dy()
            l = 2.0 * (dx * dx + dy * dy)
            if l > 0:
                xvel += (dx * (7*self.size)) / l
                yvel += (dy * (7*self.size)) / l

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
        xvel -= (self.pos().x()/2) / (weight/4)
        yvel -= (self.pos().y()/2) / (weight/4)

        if QtCore.qAbs(xvel) < 0.1 and QtCore.qAbs(yvel) < 0.1:
            xvel = yvel = 0.0

        scene_rect = self.scene().sceneRect()
        self.newPos = self.pos() + QtCore.QPointF(xvel, yvel)
        self.newPos.setX(min(max(self.newPos.x(), scene_rect.left() + 10), scene_rect.right() - 10))
        self.newPos.setY(min(max(self.newPos.y(), scene_rect.top() + 10), scene_rect.bottom() - 10))

    def advance(self):
        if self.animate:
            if self.newPos == self.pos():
                return False

            self.setPos(self.newPos)
            return True
        else:
            return False

    def boundingRect(self):
        x_coord = y_coord = (-1*(self.size/2)) - self.border_width
        width = height = self.size+23+self.border_width
        return QtCore.QRectF(x_coord, y_coord, width,
                             height)

    def shape(self):
        x_coord = y_coord = (-1 * (self.size / 2)) - self.border_width
        width = height = self.size
        path = QtGui.QPainterPath()
        path.addEllipse(x_coord, y_coord, width, height)
        return path

    def paint(self, painter, option, widget):
        x_coord = y_coord = -(self.size / 2)
        width = height = self.size
        painter.save()
        # Draw the shadow
        # painter.setPen(QtCore.Qt.NoPen)
        # painter.setBrush(QtCore.Qt.darkGray)
        # painter.drawEllipse(x_coord+3, y_coord+3, width, height)

        # Gradient depends on the image selected or not
        gradient = QtGui.QRadialGradient(-3, -3, 10)
        if option.state & QtGui.QStyle.State_Sunken:
            gradient.setCenter(3, 3)
            gradient.setFocalPoint(3, 3)
            gradient.setColorAt(1, QtGui.QColor(QtCore.Qt.lightGray).light(120))
            gradient.setColorAt(0, QtGui.QColor(QtCore.Qt.black).light(120))
            pen = QtGui.QPen(QtCore.Qt.lightGray)
            pen.setWidth(self.border_width * 2)
        else:
            gradient.setColorAt(0, QtCore.Qt.blue)
            gradient.setColorAt(1, QtCore.Qt.darkBlue)
            pen = QtGui.QPen(QtGui.QColor(200, 0, 100, 127))
            pen.setWidth(self.border_width)

        # Fill with gradient
        painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 0, 200, 127)))
        # Set the outline pen color

        painter.setPen(pen)
        # Draw the circle
        painter.drawEllipse(x_coord, y_coord, width, height)
        # painter.setPen(QtCore.Qt.white)
        # painter.drawText(QRect(x_coord,y_coord, width, height), QtCore.Qt.AlignCenter, str(self.label))
        painter.restore()
        # self.setOpacity(0.5)
        # print "Node: " + str(self.scenePos().x()) + " " + str(self.scenePos().y())

    def node_label_width(self):
        font = QFont()
        font.setFamily(font.defaultFamily())
        fm = QFontMetrics(font)
        label_width = fm.width(QString(str(self.label))) + self.border_width * 2 + 40
        return label_width

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edgeList:
                edge.adjust()
            self.graph.item_moved()

        return super(QNodeGraphicItem, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super(QNodeGraphicItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # self.update()
        super(QNodeGraphicItem, self).mouseReleaseEvent(event)

    def set_size(self, new_size):
        self.prepareGeometryChange()
        self.size = new_size
        self.calculate_forces()
        self.advance()
        self.update()

    def animate_node(self, animate):
        self.animate = animate


class QNetworkxWidget(QtGui.QGraphicsView):
    def __init__(self):
        super(QNetworkxWidget, self).__init__()

        self.timerId = 0

        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setSceneRect(-400, -400, 800, 800)
        self.setScene(self.scene)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QtGui.QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)

        self.scale(0.8, 0.8)
        self.setMinimumSize(400, 400)
        self.setWindowTitle("Elastic Nodes")

        self.nodes = {}
        self.edges = {}

    def item_moved(self):
        if not self.timerId:
            self.timerId = self.startTimer(1000 / 25)

    def add_node(self, label=None):
        if label is None:
            node_label = "Node %s" % len(self.nodes)
        else:
            node_label = label
        node = QNodeGraphicItem(self, node_label)
        self.nodes[node_label] = node
        self.scene.addItem(node)

    def add_edge(self, label=None, first_node=None, second_node=None, node_tuple=None):
        if node_tuple:
            node1_str, node2_str = node_tuple
            if node1_str in self.nodes and node2_str in self.nodes:
                node1 = self.nodes[node1_str]
                node2 = self.nodes[node2_str]
        elif first_node and second_node:
            node1 = first_node
            node2 = second_node

        edge = QEdgeGraphicItem(node1, node2)
        edge.adjust()
        if edge:
            self.edges[label] = edge
            self.scene.addItem(edge)
            # self.scene.addItem(edge.label)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Up:
            self.centerNode.moveBy(0, -20)
        elif key == QtCore.Qt.Key_Down:
            self.centerNode.moveBy(0, 20)
        elif key == QtCore.Qt.Key_Left:
            self.centerNode.moveBy(-20, 0)
        elif key == QtCore.Qt.Key_Right:
            self.centerNode.moveBy(20, 0)
        elif key == QtCore.Qt.Key_Plus:
            self.scale_view(1.2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale_view(1 / 1.2)
        elif key == QtCore.Qt.Key_Space or key == QtCore.Qt.Key_Enter:
            for item in self.scene().items():
                if isinstance(item, QNodeGraphicItem):
                    item.setPos(-150 + QtCore.qrand() % 300, -150 + QtCore.qrand() % 300)
        else:
            super(QNetworkxWidget, self).keyPressEvent(event)

    def timerEvent(self, event):
        nodes = self.nodes.values()

        for node in nodes:
            node.calculateForces()

        items_moved = False
        for node in nodes:
            if node.advance():
                items_moved = True

        if not items_moved:
            self.killTimer(self.timerId)
            self.timerId = 0

    def wheelEvent(self, event):
        self.scale_view(math.pow(2.0, -event.delta() / 240.0))

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        # self.centerOn(self.mapToScene(0, 0))
        self.scene.setSceneRect(self.mapToScene(self.viewport().geometry()).boundingRect())

    def drawBackground(self, painter, rect):
        # Shadow.
        scene_rect = self.sceneRect()
        # rightShadow = QtCore.QRectF(sceneRect.right(), sceneRect.top() + 5, 5,
        #                             sceneRect.height())
        # bottomShadow = QtCore.QRectF(sceneRect.left() + 5, sceneRect.bottom(),
        #                              sceneRect.width(), 5)
        # if rightShadow.intersects(rect) or rightShadow.contains(rect):
        #     painter.fillRect(rightShadow, QtCore.Qt.darkGray)
        # if bottomShadow.intersects(rect) or bottomShadow.contains(rect):
        #     painter.fillRect(bottomShadow, QtCore.Qt.darkGray)

        # Fill.
        gradient = QtGui.QLinearGradient(scene_rect.topLeft(),
                                         scene_rect.bottomRight())
        gradient.setColorAt(0, QtCore.Qt.black)
        gradient.setColorAt(1, QtCore.Qt.darkGray)
        painter.fillRect(rect.intersect(scene_rect), QtGui.QBrush(QtCore.Qt.black))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(scene_rect)
        self.scene.addEllipse(-10, -10, 20, 20,
                              QPen(QtCore.Qt.white), QBrush(QtCore.Qt.SolidPattern))

        # # Text.
        # textRect = QtCore.QRectF(sceneRect.left() + 4, sceneRect.top() + 4,
        #                          sceneRect.width() - 4, sceneRect.height() - 4)
        # message = "Click and drag the nodes around, and zoom with the " \
        #           "mouse wheel or the '+' and '-' keys"
        #
        # font = painter.font()
        # font.setBold(True)
        # font.setPointSize(14)
        # painter.setFont(font)
        # painter.setPen(QtCore.Qt.lightGray)
        # painter.drawText(textRect.translated(2, 2), message)
        # painter.setPen(QtCore.Qt.black)
        # painter.drawText(textRect, message)

    def set_node_size(self, size):
        nodes = self.nodes.values()
        edges = self.edges.values()
        for node in nodes:
            node.set_size(size)
            node.update()
            node.calculateForces()
            node.advance()
        for edge in edges:
            edge.set_node_size(size)
            edge.adjust()

    def animate_nodes(self, animate):
        for node in self.nodes.values():
            node.animate_node(animate)
            if animate:
                node.calculateForces()
                node.advance()

    def set_node_positions(self, position_dict):

        for node_str, position in position_dict.items():
            if node_str in self.nodes:
                node = self.nodes[node_str]
                node.setPos(position[0], position[1])
                node.update()

    def resize_nodes_to_minimum_label_width(self):
        node_label_width_list = []
        for node in self.nodes.values():
            node_label_width_list.append(node.node_label_width())
        max_width = max(node_label_width_list)
        self.set_node_size(max_width)
        return max_width

    def scale_view(self, scale_factor):
        factor = self.matrix().scale(scale_factor, scale_factor).mapRect(QtCore.QRectF(0, 0, 1, 1)).width()

        if factor < 0.07 or factor > 100:
            return

        self.scale(scale_factor, scale_factor)

    # def graph_example(self):
    #     self.the_graph.add_nodes_from([1, 2, 3, 4])
    #     self.the_graph.add_nodes_from(["asdf", 'b', 'c', 'd', 'e'])
    #     self.the_graph.add_edges_from([(1, 'a'), (2, 'c'), (3, 'd'), (3, 'e'), (4, 'e'), (4, 'd')])
    #
    #     # X = set(n for n, d in self.the_graph.nodes(data=True) if d['bipartite'] == 0)
    #     # Y = set(self.the_graph) - X
    #     #
    #     # X = sorted(X, reverse=True)
    #     # Y = sorted(Y, reverse=True)
    #     #
    #     # self.node_positions.update((n, (1, i)) for i, n in enumerate(X))  # put nodes from X at x=1
    #     # self.node_positions.update((n, (2, i)) for i, n in enumerate(Y))  # put nodes from Y at x=2
    #     self.node_positions = pos=nx.spring_layout(self.the_graph)


class QNetworkxController(object):

    def __init__(self):
        self.graph_widget = QNetworkxWidget()
        self.graph = nx.Graph()
        # self.node_positions = self.construct_the_graph()

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

    def networkx_positions_to_pixels(self, position_dict):
        pixel_positions = {}
        minimum = min(map(min, zip(*position_dict.values())))
        maximum = max(map(max, zip(*position_dict.values())))
        for node, pos in position_dict.items():
            s_r = self.graph_widget.scene.sceneRect()
            m = interp1d([minimum, maximum], [s_r.y(), s_r.y() + s_r.height()])
            pixel_positions[node] = (m(pos[0]), m(pos[1]))
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
        self.graph_widget.set_node_size(40)
        self.main_layout.addWidget(self.graph_widget)

        self.horizontal_layout = QHBoxLayout()
        self.main_layout.addLayout(self.horizontal_layout)

        self.slider = QSlider(QtCore.Qt.Horizontal)
        self.slider.setMaximum(200)
        self.slider.setMinimum(10)
        self.slider.valueChanged.connect(self.graph_widget.set_node_size)
        self.horizontal_layout.addWidget(self.slider)

        self.animation_checkbox = QCheckBox("Animate graph")
        self.horizontal_layout.addWidget(self.animation_checkbox)
        self.animation_checkbox.stateChanged.connect(self.graph_widget.animate_nodes)
        self.graph_model = nx.circular_ladder_graph(4)
        initial_positions = nx.circular_layout(self.graph_model)
        self.network_controller.set_graph(self.graph_model, initial_positions)
        self.graph_widget.animate_nodes(self.animation_checkbox.checkState())
        current_width = self.graph_widget.resize_nodes_to_minimum_label_width()
        self.slider.setValue(current_width)

        self.layouts_combo = QComboBox()
        import networkx.drawing.layout as ly
        for layout_method in dir(ly):
            if "_layout" in layout_method and callable(getattr(ly, layout_method)) and layout_method[0] != '_':
                self.layouts_combo.addItem(layout_method)
        self.main_layout.addWidget(self.layouts_combo)
        self.layouts_combo.currentIndexChanged.connect(self.on_change_layout)

    def on_change_layout(self, index):
        item = self.layouts_combo.itemText(index)
        import networkx.drawing.layout as ly
        layout_method = getattr(ly, str(item))
        pos = layout_method(self.graph_model)
        pos = self.network_controller.networkx_positions_to_pixels(pos)
        self.graph_widget.set_node_positions(pos)

if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    QtCore.qsrand(QtCore.QTime(0, 0, 0).secsTo(QtCore.QTime.currentTime()))
    window = QNetworkxWindowExample()
    window.showMaximized()

    sys.exit(app.exec_())
