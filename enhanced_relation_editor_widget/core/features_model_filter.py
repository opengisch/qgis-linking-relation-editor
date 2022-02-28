
from enum import IntEnum
from qgis.PyQt.QtCore import (
    Qt,
    QModelIndex,
    QObject,
    QSortFilterProxyModel
)
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import (
    QgsDistanceArea,
    QgsExpression,
    QgsExpressionContext,
    QgsFeatureRequest,
    QgsProject,
    QgsVectorLayer
)
from qgis.gui import QgsMapCanvas
from enhanced_relation_editor_widget.core.features_model import FeaturesModel


class FeaturesModelFilter(QSortFilterProxyModel):

    class FeatureFilter(IntEnum):
        ShowAll = 1,
        ShowSelected = 2,
        ShowVisible = 3,
        ShowEdited = 4,
        ShowFilteredList = 5

    def __init__(self,
                 layer: QgsVectorLayer,
                 canvas: QgsMapCanvas,
                 parent: QObject = None):
        super().__init__(parent)

        self._layer = layer
        self._canvas = canvas
        self._quick_filter = str()
        self._map_filter = list()
        self._feature_filter = FeaturesModelFilter.FeatureFilter.ShowAll
        self._feature_filter_expression = QgsExpression()
        self._feature_filter_expression_context = QgsExpressionContext()
        self._feature_filter_filtered_features = list()

        if self._canvas:
            self._canvas.extentsChanged.connect(self._extent_changed)

    def set_quick_filter(self,
                         filter: str):
        self._quick_filter = filter
        self.invalidateFilter()

    def clear_quick_filter(self):
        self._quick_filter = str()
        self.invalidateFilter()

    def quick_filter_active(self):
        return len(self._quick_filter) > 0

    def set_map_filter(self,
                       map_filter: list):
        self._map_filter = map_filter
        self.invalidateFilter()

    def clear_map_filter(self):
        self._map_filter = list()
        self.invalidateFilter()

    def map_filter_active(self):
        return len(self._map_filter) > 0

    def set_feature_filter(self,
                           mode):
        self._feature_filter = mode

        if self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowFilteredList:
            self._prepare_filtered_features()

        elif self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowVisible:
            self._prepare_filtered_by_visible_features()

        self.invalidateFilter()

    def set_feature_filter_expression(self,
                                      expression,
                                      context):
        self._feature_filter_expression = expression
        self._feature_filter_expression_context = context

        if self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowFilteredList:
            self._prepare_filtered_features()
            self.invalidateFilter()

    def filter_active(self):
        return self.quick_filter_active() or self.map_filter_active()

    def filterAcceptsRow(self,
                         sourceRow: int,
                         sourceParent: QModelIndex()):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        rowFeatureId = self.sourceModel().data(index,
                                               FeaturesModel.UserRole.FeatureId)
        if not rowFeatureId:
            return False

        if self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowAll:
            pass  # Nothing to do

        elif self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowSelected:
            if rowFeatureId not in self._layer.selectedFeatureIds():
                return False

        elif self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowVisible:
            if rowFeatureId not in self._feature_filter_filtered_features:
                return False

        elif self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowEdited:
            editBuffer = self._layer.editBuffer()
            if not editBuffer:
                return False

            if not (editBuffer.isFeatureAdded(rowFeatureId) or
                    editBuffer.isFeatureAttributesChanged(rowFeatureId) or
                    editBuffer.isFeatureGeometryChanged(rowFeatureId)):
                return False

        elif self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowFilteredList:
            if rowFeatureId not in self._feature_filter_filtered_features:
                return False

        if self._map_filter:
            if rowFeatureId not in self._map_filter:
                return False

        if len(self._quick_filter) == 0:
            return True

        rowDisplayRole = self.sourceModel().data(index,
                                                 Qt.DisplayRole)
        if not rowDisplayRole:
            return False

        return self._quick_filter in rowDisplayRole

    def _prepare_filtered_features(self):

        self._feature_filter_filtered_features = list()

        if not self._feature_filter_expression.isValid():
            return

        distanceArea = QgsDistanceArea()
        distanceArea.setSourceCrs(self._layer.crs(), QgsProject.instance().transformContext())
        distanceArea.setEllipsoid(QgsProject.instance().ellipsoid())

        fetchGeom = self._feature_filter_expression.needsGeometry()

        QApplication.setOverrideCursor(Qt.WaitCursor)

        self._feature_filter_expression.setGeomCalculator(distanceArea)
        self._feature_filter_expression.setDistanceUnits(QgsProject.instance().distanceUnits())
        self._feature_filter_expression.setAreaUnits(QgsProject.instance().areaUnits())

        # Record the first evaluation error
        error = str()

        for f in self._layer.getFeatures():
            self._feature_filter_expression_context.setFeature(f)
            if self._feature_filter_expression.evaluate(self._feature_filter_expression_context) != 0:
                self._feature_filter_filtered_features.append(f.id())

            # check if there were errors during evaluating
            if self._feature_filter_expression.hasEvalError() and error.isEmpty():
                error = self._feature_filter_expression.evalErrorString()

        QApplication.restoreOverrideCursor()

    def _prepare_filtered_by_visible_features(self):

        self._feature_filter_filtered_features = list()

        if not self._canvas:
            return

        rectangle = self._canvas.mapSettings().mapToLayerCoordinates(self._layer,
                                                                     self._canvas.extent())

        request = QgsFeatureRequest()
        request.setFilterRect(rectangle)

        for feature in self._layer.getFeatures(request):
            self._feature_filter_filtered_features.append(feature.id())

    def _extent_changed(self):
        if self._feature_filter == FeaturesModelFilter.FeatureFilter.ShowVisible:
            self._prepare_filtered_by_visible_features()

        self.invalidateFilter()

