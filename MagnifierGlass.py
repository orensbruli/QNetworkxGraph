import sys

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication, QGraphicsScene, QGraphicsView, QPainter, QPainterPath

from ParticlesBackgroundDecoration import ParticlesBackgroundDecoration


class MagnifierGlass(QGraphicsView):
    def paintEvent(self, QPaintEvent):
        p = QPainter(self.viewport())

        clipPath = QPainterPath()
        clipPath.addEllipse(0, 0, 100, 100)

        p.setRenderHint(QPainter.Antialiasing);
        p.setClipPath(clipPath)
        p.setClipping(False)
        p.setPen(Qt.gray);
        p.drawPath(clipPath)
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    scene.setSceneRect(-400, -400.0, 800.0, 800.0)
    particle_background = ParticlesBackgroundDecoration(scene)
    view = QGraphicsView(scene)
    view.showMaximized()
    magnifier = MagnifierGlass()
    magnifier.setScene(scene)
    scene.setSceneRect(view.mapToScene(view.viewport().geometry()).boundingRect())
    particle_background.generate_particles(200)
    particle_background.reduce_speed(0.3)
    magnifier.show()
    app.exec_()
