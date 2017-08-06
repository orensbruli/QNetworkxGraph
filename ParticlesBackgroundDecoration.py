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
        self.speed = 1
        self.next_pos = QPointF(0,0)
        self.animated = True
        self.max_speed = 3.0
        self.color = QColor(0,0,0,50)
        # self.change_position_timer = QTimer()
        # self.change_position_timer.setInterval(5000)
        # self.change_position_timer.timeout.connect(self.calculate_next_pos)

    def animate(self, bool):
        self.animated = bool

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
            xvel -= (dx * self.speed) / l
            yvel -= (dy * self.speed) / l
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
        self.speed *= random.uniform(0.1,2.0)
        self.speed %= self.max_speed
        # print self.speed

    def advance(self):
        if self.animated:
            self.calculate_forces()
            if self.newPos == self.pos():
                return False

            self.setPos(self.newPos)
            return True
        else:
            return False

    def paint(self, painter, options, widget=None):
        # painter.drawRect(self.boundingRect())
        painter.setBrush(self.color)
        painter.setPen(self.color)
        painter.drawEllipse(-self.width/2,-self.height/2,self.width,self.height)

    def boundingRect(self):
        return QRectF(-self.width/2,-self.height/2,self.width,self.height)

    def reduce_speed(self, factor=0.9):
        if factor < 1 and factor > 0:
            self.speed *= factor

    def increase_speed(self, factor=1.1):
        if factor > 1:
            self.speed *= factor

    def set_color(self, color):
        self.color = color

    def instant_pos_change(self):
        particle_x = random.uniform(-self.scene().sceneRect().width() / 2, self.scene().sceneRect().width() / 2)
        particle_y = random.uniform(-self.scene().sceneRect().height() / 2, self.scene().sceneRect().height() / 2)
        self.setPos(QPointF(particle_x, particle_y))
        self.next_pos = QPointF(particle_x, particle_y)


class ParticlesBackgroundDecoration:
    def __init__(self, scene= None):
        self.scene = scene
        self.particles = []

    def generate_particles(self, count=20):
        assert self.scene, "No scene defined in ParticlesBackgroundDecoration"
        for x in xrange(count):
            particle = Particle()
            self.scene.addItem(particle)
            particle_x = random.uniform(-self.scene.sceneRect().width() / 2, self.scene.sceneRect().width() / 2)
            particle_y = random.uniform(-self.scene.sceneRect().height() / 2, self.scene.sceneRect().height() / 2)
            particle.setPos(particle_x, particle_y)
            particle.calculate_next_pos()
            self.particles.append(particle)

    def add_particles(self, particles=None):
        if particles is None:
            if self.particles:
                particles = self.particles
        if self.scene:
            for particle in particles:
                self.scene.addItem(particle)
        else:
            raise Exception("No scene defined in ParticlesBackgroundDecoration")

    def set_scene(self, scene):
        if isinstance(scene, QGraphicsScene):
            if self.scene:
                self.remove_particles()
            self.scene = scene
            self.add_particles(self.particles)
        else:
            raise Exception("scene parameter must be of the type QGraphicsScene")

    def remove_particles(self, count=0):
        if count==0:
            count= len(self.particles)
        for particle in self.particles[:count]:
            self.scene.removeItem(particle)

    def animate(self, boolean):
        for particle in self.particles:
            particle.animate(boolean)

    def reduce_speed(self, factor=0.9):
        for particle in self.particles:
            particle.reduce_speed(factor)

    def increase_speed(self, factor=1.1):
        for particle in self.particles:
            particle.increase_speed(factor)

    def set_color(self, color):
        for particle in self.particles:
            particle.set_color(color)

    def recalculate_new_pos(self):
        for particle in self.particles:
            particle.instant_pos_change()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    scene.setSceneRect(-400, -400.0, 800.0, 800.0)
    particle_background = ParticlesBackgroundDecoration(scene)
    view = QGraphicsView(scene )
    view.showMaximized()
    scene.setSceneRect(view.mapToScene(view.viewport().geometry()).boundingRect())
    particle_background.generate_particles(200)
    particle_background.reduce_speed(0.3)
    print scene.sceneRect()
    app.exec_()