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


import math

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QPointF
from PyQt4.QtGui import QMainWindow, QWidget, QVBoxLayout, QSlider, QGraphicsView, QPen, QBrush
import networkx as nx
from scipy.interpolate import interp1d


class QEdgeGraphicItem(QtGui.QGraphicsItem):
    Pi = math.pi
    TwoPi = 2.0 * Pi

    Type = QtGui.QGraphicsItem.UserType + 2

    def __init__(self, sourceNode, destNode):
        super(QEdgeGraphicItem, self).__init__()

        self.arrowSize = 10.0
        self.sourcePoint = QtCore.QPointF()
        self.destPoint = QtCore.QPointF()

        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self.source = sourceNode
        self.dest = destNode
        self.node_size = 10
        self.source.addEdge(self)
        self.dest.addEdge(self)
        self.adjust()

    def type(self):
        return QEdgeGraphicItem.Type

    def sourceNode(self):
        return self.source

    def setSourceNode(self, node):
        self.source = node
        self.adjust()

    def destNode(self):
        return self.dest

    def setDestNode(self, node):
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
            edgeOffset = QtCore.QPointF((line.dx() * (self.node_size/2)) / length,
                                        (line.dy() * (self.node_size/2)) / length)

            self.sourcePoint = line.p1() + edgeOffset
            self.destPoint = line.p2() - edgeOffset
        else:
            self.sourcePoint = line.p1()
            self.destPoint = line.p1()

    def boundingRect(self):
        if not self.source or not self.dest:
            return QtCore.QRectF()

        penWidth = 1.0
        extra = (penWidth + self.arrowSize) / 2.0

        return QtCore.QRectF(self.sourcePoint,
                             QtCore.QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                                           self.destPoint.y() - self.sourcePoint.y())).normalized().adjusted(-extra,
                                                                                                             -extra,
                                                                                                             extra,
                                                                                                             extra)

    def paint(self, painter, option, widget):
        if not self.source or not self.dest:
            return

        # Draw the line itself.
        line = QtCore.QLineF(self.sourcePoint, self.destPoint)

        if line.length() == 0.0:
            return

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1, QtCore.Qt.SolidLine,
                                  QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the arrows if there's enough room.
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = QEdgeGraphicItem.TwoPi - angle

        sourceArrowP1 = self.sourcePoint + QtCore.QPointF(math.sin(angle + QEdgeGraphicItem.Pi / 3) * self.arrowSize,
                                                          math.cos(angle + QEdgeGraphicItem.Pi / 3) * self.arrowSize)
        sourceArrowP2 = self.sourcePoint + QtCore.QPointF(math.sin(angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3) * self.arrowSize,
                                                          math.cos(angle + QEdgeGraphicItem.Pi - QEdgeGraphicItem.Pi / 3) * self.arrowSize);
        destArrowP1 = self.destPoint + QtCore.QPointF(math.sin(angle - QEdgeGraphicItem.Pi / 3) * self.arrowSize,
                                                      math.cos(angle - QEdgeGraphicItem.Pi / 3) * self.arrowSize)
        destArrowP2 = self.destPoint + QtCore.QPointF(math.sin(angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3) * self.arrowSize,
                                                      math.cos(angle - QEdgeGraphicItem.Pi + QEdgeGraphicItem.Pi / 3) * self.arrowSize)

        painter.setBrush(QtCore.Qt.white)
        painter.drawPolygon(QtGui.QPolygonF([line.p1(), sourceArrowP1, sourceArrowP2]))
        painter.drawPolygon(QtGui.QPolygonF([line.p2(), destArrowP1, destArrowP2]))

    def set_node_size(self, new_size):
        self.node_size = new_size
        self.update()

class QNodeGraphicItem(QtGui.QGraphicsItem):
    Type = QtGui.QGraphicsItem.UserType + 1

    def __init__(self, graphWidget, label):
        super(QNodeGraphicItem, self).__init__()

        self.graph = graphWidget
        self.edgeList = []
        self.newPos = QtCore.QPointF()

        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)
        self.size = 40
        self.edge_width = 4
        self.label = label
        self.animate = True


    def type(self):
        return QNodeGraphicItem.Type

    def addEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def edges(self):
        return self.edgeList

    def calculateForces(self):
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
                xvel += (dx * 150.0) / l
                yvel += (dy * 150.0) / l

        # Now subtract all forces pulling items together.
        weight = (len(self.edgeList) + 1) * self.size/1.5
        for edge in self.edgeList:
            if edge.sourceNode() is self:
                pos = self.mapFromItem(edge.destNode(), 0, 0)
            else:
                pos = self.mapFromItem(edge.sourceNode(), 0, 0)
            xvel += pos.x() / weight
            yvel += pos.y() / weight
        # Invisible Node pulling to the center
        pos = self.mapFromItem(self, 0, 0)
        xvel -= (self.pos().x()/2) / weight
        yvel -= (self.pos().y()/2) / weight

        if QtCore.qAbs(xvel) < 0.1 and QtCore.qAbs(yvel) < 0.1:
            xvel = yvel = 0.0

        sceneRect = self.scene().sceneRect()
        self.newPos = self.pos() + QtCore.QPointF(xvel, yvel)
        self.newPos.setX(min(max(self.newPos.x(), sceneRect.left() + 10), sceneRect.right() - 10))
        self.newPos.setY(min(max(self.newPos.y(), sceneRect.top() + 10), sceneRect.bottom() - 10))

    def advance(self):
        if self.animate:
            if self.newPos == self.pos():
                return False

            self.setPos(self.newPos)
            return True
        else:
            return False

    def boundingRect(self):
        adjust = 2.0
        x_coord = y_coord = (-1*(self.size/2)) - self.edge_width
        width = height = self.size+23+self.edge_width
        return QtCore.QRectF(x_coord, y_coord , width,
                             height)

    def shape(self):
        x_coord = y_coord = (-1 * (self.size / 2)) - self.edge_width
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

        # Gradiente depends on the image selected or not
        gradient = QtGui.QRadialGradient(-3, -3, 10)
        if option.state & QtGui.QStyle.State_Sunken:
            gradient.setCenter(3, 3)
            gradient.setFocalPoint(3, 3)
            gradient.setColorAt(1, QtGui.QColor(QtCore.Qt.lightGray).light(120))
            gradient.setColorAt(0, QtGui.QColor(QtCore.Qt.black).light(120))
            pen = QtGui.QPen(QtCore.Qt.lightGray)
            pen.setWidth(self.edge_width*2)
        else:
            gradient.setColorAt(0, QtCore.Qt.blue)
            gradient.setColorAt(1, QtCore.Qt.darkBlue)
            pen = QtGui.QPen(QtGui.QColor(200, 0, 100, 127))
            pen.setWidth(self.edge_width)

        # Fill with gradient
        painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 0, 200, 127)))
        # Set the outline pen color

        painter.setPen(pen)
        # Draw the circle
        painter.drawEllipse(x_coord, y_coord, width, height)
        painter.restore()
        # self.setOpacity(0.5)

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edgeList:
                edge.adjust()
            self.graph.itemMoved()

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
        self.graph.itemMoved()
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

    def itemMoved(self):
        if not self.timerId:
            self.timerId = self.startTimer(1000 / 25)


    def add_node(self, label=None):
        if not label:
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
            node1= first_node
            node2 = second_node

        if not label:
            label = "%s-%s" % (node1.label, node2.label)
        edge = QEdgeGraphicItem(node1, node2)
        if edge:
            self.edges[label] = edge
            self.scene.addItem(edge)


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
            self.scaleView(1.2)
        elif key == QtCore.Qt.Key_Minus:
            self.scaleView(1 / 1.2)
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

        itemsMoved = False
        for node in nodes:
            if node.advance():
                itemsMoved = True

        if not itemsMoved:
            self.killTimer(self.timerId)
            self.timerId = 0

    def wheelEvent(self, event):
        self.scaleView(math.pow(2.0, -event.delta() / 240.0))

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        # self.centerOn(self.mapToScene(0, 0))
        self.scene.setSceneRect(self.mapToScene(self.viewport().geometry()).boundingRect())


    def drawBackground(self, painter, rect):
        # Shadow.
        sceneRect = self.sceneRect()
        # rightShadow = QtCore.QRectF(sceneRect.right(), sceneRect.top() + 5, 5,
        #                             sceneRect.height())
        # bottomShadow = QtCore.QRectF(sceneRect.left() + 5, sceneRect.bottom(),
        #                              sceneRect.width(), 5)
        # if rightShadow.intersects(rect) or rightShadow.contains(rect):
        #     painter.fillRect(rightShadow, QtCore.Qt.darkGray)
        # if bottomShadow.intersects(rect) or bottomShadow.contains(rect):
        #     painter.fillRect(bottomShadow, QtCore.Qt.darkGray)

        # Fill.
        gradient = QtGui.QLinearGradient(sceneRect.topLeft(),
                                         sceneRect.bottomRight())
        gradient.setColorAt(0, QtCore.Qt.black)
        gradient.setColorAt(1, QtCore.Qt.darkGray)
        painter.fillRect(rect.intersect(sceneRect), QtGui.QBrush(QtCore.Qt.black))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(sceneRect)
        self.scene.addEllipse(0, 0, 20, 20,
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
        for edge in edges:
            edge.set_node_size(size)
            edge.adjust()


    def animate_nodes(self, animate):
        for node in self.nodes.values():
            node.animate_node(animate)

    def set_node_positions(self, position_dict):

        for node_str, position in position_dict.items():
            if node_str in self.nodes:
                node = self.nodes[node_str]
                node.setPos(position[0], position[1])
                node.update()


    def scaleView(self, scaleFactor):
        factor = self.matrix().scale(scaleFactor, scaleFactor).mapRect(QtCore.QRectF(0, 0, 1, 1)).width()

        if factor < 0.07 or factor > 100:
            return

        self.scale(scaleFactor, scaleFactor)

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


class QNetworkxControler():
    def __init__(self):
        self.graph_widget = QNetworkxWidget()
        self.graph = nx.Graph()
        self.node_positions = self.construct_the_graph()

    def construct_the_graph(self):
        self.graph.add_nodes_from([1, 2, 3, 4])
        self.graph.add_nodes_from(["asdf", 'b', 'c', 'd', 'e'])
        self.graph.add_edges_from([(1, 'a'), (2, 'c'), (3, 'd'), (3, 'e'), (4, 'e'), (4, 'd')])

        for node in self.graph.nodes():
            self.graph_widget.add_node(node)

        pos = nx.circular_layout(self.graph)
        self.nx_positions_to_pixels(pos)
        self.graph_widget.set_node_positions(pos)

        self.graph_widget.animate_nodes(False)

        for edge in self.graph.edges():
            self.graph_widget.add_edge(node_tuple=edge)

    def nx_positions_to_pixels(self, position_dict):
        minimum = min(map(min, zip(*position_dict.values())))
        maximum = max(map(max, zip(*position_dict.values())))
        for node, pos in position_dict.items():
            s_r = self.graph_widget.scene.sceneRect()
            m = interp1d([minimum, maximum], [s_r.y(), s_r.y() + s_r.height()])
            position_dict[node] = (m(pos[0]), m(pos[1]))

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

if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    QtCore.qsrand(QtCore.QTime(0, 0, 0).secsTo(QtCore.QTime.currentTime()))
    window = QMainWindow()
    main_layout = QVBoxLayout()
    main_widget = QWidget()
    main_widget.setLayout(main_layout)
    window.setCentralWidget(main_widget)
    network_controler = QNetworkxControler()
    graph_widget = network_controler.get_widget()
    graph_widget.set_node_size(40)
    main_layout.addWidget(graph_widget)
    slider = QSlider(QtCore.Qt.Horizontal)
    slider.setMaximum(200)
    slider.setMinimum(10)
    slider.valueChanged.connect(graph_widget.set_node_size)
    main_layout.addWidget(slider)
    window.showMaximized()

    sys.exit(app.exec_())