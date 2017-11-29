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
import networkx as nx
import networkx.drawing.layout as ly
from PyQt4.QtCore import QPointF, QRectF, QString, QTime, Qt, pyqtSignal, qsrand
from PyQt4.QtGui import QAction, QApplication, QBrush, QCheckBox, QColor, QComboBox, \
    QGraphicsScene, QGraphicsView, QHBoxLayout, QInputDialog, QLineEdit, QLinearGradient, QMainWindow, QMenu, QPainter, QPen, QSlider, QVBoxLayout, QWidget
from scipy.interpolate import interp1d
from ParticlesBackgroundDecoration import ParticlesBackgroundDecoration
from QEdge import QEdgeGraphicItem
from QNode import QNodeGraphicItem

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

from QNetworkxStylesManager import QNetworkxStylesManager

graph_config = QNetworkxStylesManager()
graph_config.load_styles()

class Region(object):
    def __init__(self, shape_):
        shape = shape_

class Circle(Region):
    def __init__(self, center_, radious_):
        super(Circle, self).__init__("circle")
        self.center = QPointF()
        self.center = center_
        self.radious = radious_

    def local_coor(self, point):
        return point - self.center

class Square(Region):
    def __init__(self, rect_):
        super(Circle, self).__init("square")
        self.rect = QRectF()
        self.rect = rect_

    def local_coor(self, point):
        return point - self.rect.center()


class QNetworkxWidget(QGraphicsView):
    node_selection_changed = pyqtSignal(list)

    def __init__(self, directed=False, parent=None):
        super(QNetworkxWidget, self).__init__(parent)

        self.timer_id = 0
        self.background_color = QColor(255, 255, 255)
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

        self.particle_background = None

        self.setMinimumSize(400, 400)
        self.setWindowTitle("QNetworkXWidget")

        self.nx_graph = nx.Graph()
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.is_directed = directed

        self._scale_factor = 1.15
        self.set_panning_mode(False)

        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.node_groups = {}
        self.node_groups_actions = {}

        self.menu = QMenu()
        action1 = QAction("Panning mode", self)
        action1.triggered.connect(self.set_panning_mode)
        action1.setCheckable(True)
        action2 = QAction("Set mass center", self)
        action2.triggered.connect(self.set_mass_center)
        self.node_groups_menu = self.menu.addMenu("Add to group...")
        self.new_group_action = QAction("Add new group...", self)
        self.new_group_action.triggered.connect(self.create_new_node_group)
        self.node_groups_menu.addAction(self.new_group_action)
        self.node_groups_menu.addSeparator()
        self.menu.addAction(action1)
        self.menu.addAction(action2)
        self.menu.addSeparator()

    def set_mass_center(self):
        if self.selected_nodes():
            for node_label in self.selected_nodes():
                self.nx_graph.node[node_label]['item'].set_mass_center(self.last_menu_position)

    def create_new_node_group(self, node_group_name=None):
        if not node_group_name:
            text, result = QInputDialog.getText(self, u"New node group", u"Node group name:", QLineEdit.Normal, "...")
            if (result and not text.isEmpty()):
                node_group_name = unicode(text.toUtf8(), encoding="UTF-8")
            else:
                return
        nodes = self.selected_nodes()
        self.node_groups[node_group_name] = nodes
        action = self.node_groups_menu.addAction(node_group_name)
        action.triggered.connect(lambda a: self.add_nodes_to_node_group(node_group_name=node_group_name))
        self.node_groups_actions[node_group_name] = action
        print "Created new group %s with nodes %s" % (node_group_name, nodes)

    def remove_node_group(self, node_group_name):
        del self.node_groups[node_group_name]
        self.node_groups_menu.removeAction()

    def add_nodes_to_node_group(self, node_group_name, nodes_names=None):
        if not nodes_names:
            nodes_names = self.selected_nodes()
            if not nodes_names:
                raise Exception("No node provided to be added to %s node group" % node_group_name)
        print "Adding %s to %s node group" % (nodes_names, node_group_name)
        for node_name in nodes_names:
            if node_name in self.nx_graph.nodes():
                if node_group_name in self.node_groups and node_name not in self.node_groups[node_group_name]:
                    self.node_groups[node_group_name].append(node_name)
                else:
                    raise Exception("Can't add a node to a non existing group")
            else:
                raise Exception("Can't add a node non existing in the graph to a group")

    def remove_node_from_node_group(self, node_name, node_group_name):
        if node_name in self.nx_graph.nodes():
            if node_group_name in self.node_groups and node_name in self.node_groups[node_group_name]:
                self.node_groups[node_group_name].remove(node_name)
            else:
                raise Exception("Can't add a node to a non existing group")
        else:
            raise Exception("Can't add a node non existing in the graph to a group")

    # self.zoom_in_action = QAction("Zoom in", self)
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

    def set_particle_background(self):
        ParticlesBackgroundDecoration(self.scene)
        self.particle_background.generate_particles(200)
        self.particle_background.reduce_speed(0.3)
        color = QColor(255, 255, 255, 40)
        self.particle_background.set_color(color)

    def on_selection_change(self):
        self.node_selection_changed.emit(self.selected_nodes())

    def selected_nodes(self):
        changed = self.scene.selectedItems()
        selected_nodes = []
        for item in changed:
            if isinstance(item, QNodeGraphicItem):
                selected_nodes.append(unicode(item.label.toPlainText().toUtf8(), encoding="UTF-8"))
        return selected_nodes

    def get_selected_nodes(self):
        return self.selected_nodes()

    def set_panning_mode(self, mode=False):
        self.panning_mode = mode
        if self.panning_mode:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def get_current_nodes_positions(self):
        position_dict = {}
        for node_label, data in self.nx_graph.nodes(data=True):
            position_dict[node_label] = (data['item'].pos().x(), data['item'].pos().y())
        return position_dict

    def set_scale_factor(self, scale_factor):
        self._scale_factor = scale_factor

    def item_moved(self):
        if not self.timer_id:
            self.timer_id = self.startTimer(1000 / 25)

    def add_node(self, label=None, position=None, tipo=None):
        if label is None:
            node_label = u"Node %s" % len(self.nx_graph.nodes())
        elif isinstance(label, QString):
            node_label = unicode(label.toUtf8(), encoding="UTF-8")
        else:
            node_label = unicode(str(label), encoding="UTF-8")
        if label not in self.nx_graph.nodes():
            node = QNodeGraphicItem(self, node_label, tipo=tipo)
            self.nx_graph.add_node(node_label, item=node, tipo=tipo)
            self.scene.addItem(node)
            if position and isinstance(position, tuple):
                node.setPos(QPointF(position[0], position[1]))
        else:
            # TODO: raise exception
            pass

    def get_node(self, label):
        if label in self.nx_graph.nodes():
            return self.nx_graph.node[str(label)]
        else:
            return None

    def add_edge(self, label=None, first_node=None, second_node=None, node_tuple=None, label_visible=True):
        if node_tuple:
            node1_label, node2_label = node_tuple
            if not isinstance(node1_label, unicode):
                node1_label = unicode(str(node1_label), encoding="UTF-8")
            if not isinstance(node2_label, unicode):
                node2_label = unicode(str(node2_label), encoding="UTF-8")
            if node1_label in self.nx_graph.nodes() and node2_label in self.nx_graph.nodes():
                node1 = self.nx_graph.node[node1_label]['item']
                node2 = self.nx_graph.node[node2_label]['item']
        elif first_node and second_node:
            if isinstance(first_node, basestring) and first_node in self.nx_graph.nodes():
                node1_label = first_node
                node1 = self.nx_graph.node[first_node]['item']
            elif isinstance(first_node, QNodeGraphicItem):
                node1 = first_node
                node1_label = unicode(node1.label.toPlainText().toUtf8(), encoding="UTF-8")
            elif isinstance(first_node, QString):
                node1_label = unicode(first_node.toUtf8(), encoding="UTF-8")
                node1 = self.nx_graph.node[node1_label]['item']
            else:
                raise Exception("Nodes must be existing labels on the graph or QNodeGraphicItem")
            if isinstance(second_node, basestring):
                node2_label = second_node
                node2 = self.nx_graph.node[second_node]['item']
            elif isinstance(second_node, QNodeGraphicItem):
                node2 = second_node
                node2_label = unicode(node2.label.toPlainText().toUtf8(), encoding="UTF-8")
            elif isinstance(second_node, QString):
                node2_label = unicode(second_node.toUtf8(), encoding="UTF-8")
                node2 = self.nx_graph.node[node2_label]['item']
            else:
                raise Exception("Nodes must be existing labels on the graph or QNodeGraphicItem")

        edge = QEdgeGraphicItem(first_node=node1, second_node=node2, label=label, directed=self.is_directed,
                                label_visible=label_visible)
        edge.adjust()
        if edge and edge.label.toPlainText() not in self.nx_graph.edges():
            self.nx_graph.add_edge(node1_label, node2_label, item=edge)
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

        # If right button, avoid unselecting nodes not passing the event to the parent
        if not event.buttons() & Qt.RightButton:
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
            self.setDragMode(QGraphicsView.RubberBandDrag)

        QGraphicsView.mouseReleaseEvent(self, event)

    def timerEvent(self, event):
        items_moved = False
        for label, data in self.nx_graph.nodes(data=True):
            data['item'].calculate_forces()
            if data['item'].advance():
                items_moved = True

        if not items_moved:
            self.killTimer(self.timer_id)
            self.timer_id = 0

    def wheelEvent(self, event):
        self.scale_view(math.pow(2.0, -event.delta() / 640.0))

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        # self.centerOn(self.mapToScene(0, 0))
        self.resize_scene()
        if self.particle_background:
            self.particle_background.recalculate_new_pos()

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
        for label, data in self.nx_graph.nodes(data=True):
            data['item'].set_size(size)
        for label1, label2, data in self.nx_graph.edges(data=True):
            data['item'].adjust()

    def animate_nodes(self, animate):
        for label, data in self.nx_graph.nodes(data=True):
            data['item'].animate_node(animate)
            if animate:
                data['item'].calculate_forces()
                data['item'].advance()

    def stop_animation(self):
        self.animate_nodes(False)

    def start_animation(self):
        self.animate_nodes(True)

    def set_node_positions(self, position_dict):
        for node_str, position in position_dict.items():
            if not isinstance(node_str, unicode):
                node_str = unicode(str(node_str), encoding="UTF-8")
            if node_str in self.nx_graph.nodes():
                node = self.nx_graph.node[node_str]['item']
                node.setPos(position[0], position[1])
                node.update()
                for edge in node.edges():
                    edge.adjust()
                    edge.update()

    def resize_nodes_to_minimum_label_width(self):
        node_label_width_list = []
        for label, data in self.nx_graph.nodes(data=True):
            node_label_width_list.append(data['item'].node_label_width())
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
            for label, data in self.nx_graph.nodes(data=True):
                data['item'].add_context_menu(options)
        if "edges" in related_classes:
            for label1, label2, data in self.nx_graph.edges(data=True):
                data['item'].add_context_menu(options)
        if "graph" in related_classes:
            for option_string, callback in options.items():
                instance, method = callback
                action1 = QAction(option_string, self)
                action1.triggered.connect(getattr(instance, method))
                self.menu.addAction(action1)

    def delete_graph(self):
        for label, data in self.nx_graph.nodes(data=True):
            self.scene.removeItem(data['item'])
        for label1, label2, data in self.nx_graph.edges(data=True):
            self.scene.removeItem(data['item'])
        self.nx_graph.clear()

    def clear(self):
        self.delete_graph()

    def contextMenuEvent(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            event.setAccepted(False)
            super(QNetworkxWidget, self).contextMenuEvent(event)
            return

        # if the user has right clicked on an item other than the background, this code
        # will pop up the correct context menu and return
        object = self.itemAt(event.pos())

        if object:
            event.setAccepted(False)
            super(QNetworkxWidget, self).contextMenuEvent(event)
            return

        # if the user has right clicked in the background, this will pop up the general context menu
        if self.menu:
            if not self.selected_nodes():
                self.node_groups_menu.setEnabled(False)
                self.node_groups_menu.setToolTip(u'Some node have to be selected')
            else:
                self.node_groups_menu.setEnabled(True)
                self.node_groups_menu.setToolTip(u'')
            self.last_menu_position = self.mapToScene(event.pos())
            self.menu.exec_(event.globalPos())
            event.setAccepted(True)
        else:
            event.setAccepted(False)
            super(QNetworkxWidget, self).contextMenuEvent(event)
            self._logger.warning("No menu defined yet for QNetworkxWidget. Use add_context_menu.")

    # def contextMenuEvent(self, event):
    #     self._logger.debug("ContextMenuEvent received on node %s" % str(self.label.toPlainText()))
    #     selection_path = QPainterPath()
    #     selection_path.addPolygon(self.mapToScene(self.boundingRect()))
    #     if event.modifiers() & Qt.CTRL:
    #         selection_path += self.scene().selectionArea()
    #     else:
    #         self.scene().clearSelection()
    #     self.scene().setSelectionArea(selection_path)
    #     if self.menu:
    #         if self.selected_nodes():
    #             self.node_groups_menu.setEnabled(True)
    #             self.node_groups_menu.setToolTip(u'')
    #         else:
    #             self.node_groups_menu.setEnabled(False)
    #             self.node_groups_menu.setToolTip(u'Some node have to be selected')
    #         self.menu.exec_(event.screenPos())
    #         event.setAccepted(True)
    #     else:
    #         self._logger.warning("No QNodeGraphicItem defined yet. Use add_context_menu.")

    def set_nodes_shape(self, shape):
        for label, data in self.nx_graph.nodes(data=True):
            data['item'].set_node_shape(shape)

    def networkx_positions_to_pixels(self, position_dict):
        pixel_positions = {}
        minimum = min(map(min, zip(*position_dict.values())))
        maximum = max(map(max, zip(*position_dict.values())))
        for node, pos in position_dict.items():
            s_r = self.scene.sceneRect()
            if minimum != maximum:
                m = interp1d([minimum, maximum], [s_r.y(), s_r.y() + s_r.height()])
                pixel_positions[node] = (m(pos[0]), m(pos[1]))
            else:
                pixel_positions[node] = (s_r.center().x(), s_r.center().y())
        return pixel_positions


#############################################################
# Classes for testing and checking the behavior of the graph#
#############################################################

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

        initial_pos = self.graph_widget.networkx_positions_to_pixels(initial_pos)
        self.graph_widget.set_node_positions(initial_pos)

    def set_elements_context_menus(self, options_dict, elements):
        self.graph_widget.add_context_menu(options_dict, elements)

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
        pos = self.network_controller.graph_widget.networkx_positions_to_pixels(pos)
        self.graph_widget.set_node_positions(pos)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    qsrand(QTime(0, 0, 0).secsTo(QTime.currentTime()))
    window = QNetworkxWindowExample()
    window.showMaximized()

    sys.exit(app.exec_())
