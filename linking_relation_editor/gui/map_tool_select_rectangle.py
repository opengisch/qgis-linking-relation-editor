from qgis.core import QgsPointXY, QgsRectangle, QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsMapCanvas, QgsMapToolEmitPoint, QgsRubberBand
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor


class MapToolSelectRectangle(QgsMapToolEmitPoint):

    signal_selection_finished = pyqtSignal(list)

    def __init__(self, canvas: QgsMapCanvas, layer: QgsVectorLayer):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self._layer = layer
        self.rubberBand = QgsRubberBand(self.canvas, True)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setFillColor(QColor(254, 178, 76, 63))
        self.rubberBand.setStrokeColor(QColor(254, 58, 29, 100))
        self.rubberBand.setWidth(1)
        self.reset()

        self.deactivated.connect(self._deactivated)

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(True)

    def keyPressEvent(self, keyEvent):
        if keyEvent.key() == Qt.Key_Escape:
            self.reset()
            self.signal_selection_finished.emit(list())

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showRect(self.startPoint, self.endPoint)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False

        geometry = self.geometry()

        if not geometry:
            self.signal_selection_finished.emit(list())
            return

        if isinstance(geometry, QgsRectangle):
            features = list()
            for feature in self._layer.getFeatures(geometry):
                features.append(feature)

            self.signal_selection_finished.emit(features)
            return

        if isinstance(geometry, QgsPointXY):

            search_radius = self.searchRadiusMU(self.canvas)
            search_rectangle = QgsRectangle(
                geometry.x() - search_radius,
                geometry.y() - search_radius,
                geometry.x() + search_radius,
                geometry.y() + search_radius,
            )

            for feature in self._layer.getFeatures(search_rectangle):
                self.signal_selection_finished.emit([feature])
                return

            self.signal_selection_finished.emit(list())
            return

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPointXY(startPoint.x(), startPoint.y())
        point2 = QgsPointXY(startPoint.x(), endPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)  # true to update canvas
        self.rubberBand.show()

    def geometry(self):
        if self.startPoint is None or self.endPoint is None:
            return None

        if self.startPoint == self.endPoint:
            return self.startPoint

        if self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def _deactivated(self):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
