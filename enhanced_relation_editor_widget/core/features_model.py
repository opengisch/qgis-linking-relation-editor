# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------


from qgis.PyQt.QtCore import (
    Qt,
    QAbstractListModel,
    QModelIndex,
    QObject
)
from qgis.core import (
    QgsFeature,
    QgsVectorLayer,
    QgsVectorLayerUtils
)


class FeaturesModel(QAbstractListModel):

    class FeaturesModelElement(object):
        def __init__(self,
                     feature: QgsFeature,
                     layer: QgsVectorLayer):
            self._displayString = QgsVectorLayerUtils.getFeatureDisplayString(layer, feature)

        def displayString(self):
            return self._displayString

    def __init__(self,
                 features,
                 layer: QgsVectorLayer,
                 parent: QObject = None):
        super().__init__(parent)

        self._layer = layer
        self._modelFeatures = []
        self.setFeatures(features)

    def rowCount(self,
                 index: QModelIndex = ...) -> int:
        return len(self._modelFeatures)

    def data(self,
             index: QModelIndex,
             role: int = ...):

        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return self._modelFeatures[index.row()].displayString()

        return None

    def setFeatures(self,
                    features):
        self.beginResetModel()

        self._modelFeatures = []
        for feature in features:
            self._modelFeatures.append(FeaturesModel.FeaturesModelElement(feature,
                                                                          self._layer))

        self.endResetModel()
