import random
import sys

import math
from PyQt4 import QtCore

from PyQt4.QtCore import QRectF, Qt, QPointF, QTimer, QTimeLine
from PyQt4.QtGui import QGraphicsView, QGraphicsScene, QApplication, QGraphicsItem, QGraphicsBlurEffect, QBrush, QColor, \
    QGraphicsItemAnimation


class Particle(QGraphicsItem):
    def __init__(self, parent=None):
        super(Particle, self).__init__(parent)
        self.effect = QGraphicsBlurEffect()
        self.blur_radius = random.uniform(0.8, 1.6)
        self.effect.setBlurRadius(self.blur_radius)
        self.setGraphicsEffect(self.effect)
        self.height = random.uniform(1,6)
        self.width = random.uniform(1,6)
        self.depth = 1
        self.setZValue(self.depth)
        self.newPos = QPointF()
        self.animation_timer = QTimer()
        self.animation_timer.setInterval(1000 / 25)
        self.animation_timer.timeout.connect(self.advance)
        self.animation_timer.start()
        self.speed = 47
        self.next_pos = QPointF(0,0)
        # self.change_position_timer = QTimer()
        # self.change_position_timer.setInterval(5000)
        # self.change_position_timer.timeout.connect(self.calculate_next_pos)

    def calculate_forces(self):

        # Sum up all forces pushing this item away.
        xvel = 0.0
        yvel = 0.0

        line = QtCore.QLineF(self.next_pos,
                             self.pos())
        dx = line.dx()
        dy = line.dy()
        l = math.sqrt(math.pow(dx,2)+math.pow(dy,2))
        # l = 2.0 * (dx * dx + dy * dy)
        if l > 0:
            xvel -= (dx * 1) / l
            yvel -= (dy * 1) / l
        if l < 10:
            self.calculate_next_pos()

        scene_rect = self.scene().sceneRect()
        self.newPos = self.pos() + QtCore.QPointF(xvel, yvel)
        self.newPos.setX(min(max(self.newPos.x(), scene_rect.left() + 10), scene_rect.right() - 10))
        self.newPos.setY(min(max(self.newPos.y(), scene_rect.top() + 10), scene_rect.bottom() - 10))

    def calculate_next_pos(self):
        particle_x = random.uniform(-self.scene().sceneRect().width() / 2, self.scene().sceneRect().width() / 2)
        particle_y = random.uniform(-self.scene().sceneRect().height() / 2, self.scene().sceneRect().height() / 2)
        self.next_pos = QPointF(particle_x, particle_y)
        self.blur_radius = random.uniform(0.8, 1.6)
        self.effect.setBlurRadius(self.blur_radius)
        self.setGraphicsEffect(self.effect)
        self.height = random.uniform(1,6)
        self.width = random.uniform(1,6)
        self.depth = random.uniform(0,6)
        self.speed = random.uniform(47,100)

    def advance(self):
        self.calculate_forces()
        if self.newPos == self.pos():
            return False

        self.setPos(self.newPos)
        return True

    def paint(self, painter, options, widget=None):
        # painter.drawRect(self.boundingRect())
        color = QColor(0,0,0,50)
        painter.setBrush(QBrush(color))
        painter.setPen(QColor(color))
        painter.drawEllipse(-self.width/2,-self.height/2,self.width,self.height)

    def boundingRect(self):
        return QRectF(-self.width/2,-self.height/2,self.width,self.height)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    scene.setSceneRect(-400, -400.0, 800.0, 800.0)
    for x in xrange(500):
        particle = Particle()
        scene.addItem(particle)
        particle_x = random.uniform(-scene.sceneRect().width()/2, scene.sceneRect().width()/2)
        particle_y = random.uniform(-scene.sceneRect().height()/2, scene.sceneRect().height()/2)
        particle.setPos(particle_x, particle_y)
        particle.calculate_next_pos()
    view = QGraphicsView(scene )
    view.showMaximized()
    particle.calculate_next_pos()
    particle.advance()
    app.exec_()