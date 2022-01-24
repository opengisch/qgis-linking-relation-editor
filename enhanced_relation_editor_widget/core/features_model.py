# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

import os
from enum import IntEnum
from itertools import groupby
from operator import itemgetter
from qgis.PyQt.QtGui import QIcon
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

    class FeatureState(IntEnum):
        Linked = 1,
        Unlinked = 2,
        ToBeLinked = 3,
        ToBeUnlinked = 4

    class FeaturesModelElement(object):
        def __init__(self,
                     feature: QgsFeature,
                     featureState,
                     layer: QgsVectorLayer):
            self._displayString = QgsVectorLayerUtils.getFeatureDisplayString(layer, feature)
            self._featureState = featureState

        def featureState(self):
            return self._featureState

        def setFeatureState(self,
                            featureState):
            self._featureState = featureState

        def displayString(self):
            return self._displayString

        def displayIcon(self):
            if self._featureState == FeaturesModel.FeatureState.Unlinked or self._featureState == FeaturesModel.FeatureState.Linked:
                return QIcon()
            elif self._featureState == FeaturesModel.FeatureState.ToBeLinked:
                return QIcon(os.path.join(os.path.dirname(__file__), '../images/mActionToBeLinked.svg'))
            elif self._featureState == FeaturesModel.FeatureState.ToBeUnlinked:
                return QIcon(os.path.join(os.path.dirname(__file__), '../images/mActionToBeUnlinked.svg'))

            return QIcon()

    def __init__(self,
                 features,
                 featureState,
                 layer: QgsVectorLayer,
                 parentView,
                 parent: QObject = None):
        super().__init__(parent)

        self._layer = layer
        self._modelFeatures = []
        self._parentView = parentView
        self.setFeatures(features,
                         featureState)

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

        if role == Qt.DecorationRole:
            return self._modelFeatures[index.row()].displayIcon()

        return None

    def removeRows(self,
                   row: int = ...,
                   count: int = ...,
                   index: QModelIndex = ...):

        if row + count > self.rowCount():
            return False

        self.beginRemoveRows(QModelIndex(),
                             row,
                             row + count - 1)
        self._modelFeatures[row:(row + count)] = []
        self.endRemoveRows()
        return True

    def supportedDropActions(self):
        return Qt.MoveAction

    def setFeatures(self,
                    features,
                    featuresState):
        self.beginResetModel()

        self._modelFeatures = []
        for feature in features:
            self._modelFeatures.append(FeaturesModel.FeaturesModelElement(feature,
                                                                          featuresState,
                                                                          self._layer))

        self.endResetModel()

    def addFeaturesModelElements(self,
                                 featureModelElements):
        self.beginInsertRows(QModelIndex(),
                             self.rowCount(),
                             self.rowCount() + len(featureModelElements))
        self._modelFeatures.extend(featureModelElements)
        self.endInsertRows()

    def takeSelected(self):
        indexes = [modelIndex.row() for modelIndex in self._parentView.selectedIndexes()]
        if not indexes:
            return []

        indexes.sort()

        # Clear selection to avoid widget accessing invalid indexes
        self._parentView.selectionModel().clear()

        self.beginResetModel()

        featureModelElements = []

        indexesMap = enumerate(indexes)
        indexesMap = sorted(indexesMap, reverse=True)
        print("indexesMap: {}".format(indexesMap))
        for k, g in groupby(indexesMap, lambda x: x[0] - x[1]):
            group = (map(itemgetter(1), g))
            group = list(map(int, group))

            # self.beginRemoveRows(QModelIndex(),
            #                      group[-1],
            #                      len(group))

            featureModelElements.extend(self._modelFeatures[group[-1]:group[0] + 1])
            del self._modelFeatures[group[-1]:group[0] + 1]

            # self.endRemoveRows()

        self.endResetModel()

        return featureModelElements

    def takeAll(self):
        self.beginResetModel()
        featureModelElements = self._modelFeatures
        self._modelFeatures = []
        self.endResetModel()
        return featureModelElements
