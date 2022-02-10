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

    class FeaturesModelItem(object):
        def __init__(self,
                     feature: QgsFeature,
                     featureState,
                     layer: QgsVectorLayer):
            self._feature = feature
            self._featureState = featureState
            self._displayString = QgsVectorLayerUtils.getFeatureDisplayString(layer, feature)

        def feature(self):
            return self._feature

        def feature_id(self):
            return self._feature.id()

        def feature_state(self):
            return self._featureState

        def set_feature_state(self,
                              featureState):
            self._featureState = featureState

        def display_string(self):
            return self._displayString

        def display_icon(self):
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
        self.set_features(features,
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
            return self._modelFeatures[index.row()].display_string()

        if role == Qt.DecorationRole:
            return self._modelFeatures[index.row()].display_icon()

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

    def set_features(self,
                     features,
                     featuresState):
        self.beginResetModel()

        self._modelFeatures = []
        for feature in features:
            self._modelFeatures.append(FeaturesModel.FeaturesModelItem(feature,
                                                                       featuresState,
                                                                       self._layer))

        self.endResetModel()

    def get_all_feature_items(self):
        return self._modelFeatures

    def get_selected_features(self):
        indexes = [modelIndex.row() for modelIndex in self._parentView.selectedIndexes()]
        if not indexes:
            return []

        selectedFeatures = []
        for index in indexes:
            selectedFeatures.append(self._modelFeatures[index].featureId())

        return selectedFeatures

    def add_features_model_items(self,
                                 featureModelElements):
        self.beginInsertRows(QModelIndex(),
                             self.rowCount(),
                             self.rowCount() + len(featureModelElements))
        self._modelFeatures.extend(featureModelElements)
        self.endInsertRows()

    def take_selected_items(self):
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

            featureModelElements.extend(self._modelFeatures[group[-1]:group[0] + 1])
            del self._modelFeatures[group[-1]:group[0] + 1]

            # self.endRemoveRows()

        self.endResetModel()

        return featureModelElements

    def take_all_items(self):
        self.beginResetModel()
        featureModelElements = self._modelFeatures
        self._modelFeatures = []
        self.endResetModel()
        return featureModelElements

    def contains(self,
                 featureId: int):
        for feature in self._modelFeatures:
            if feature.feature_id() == featureId:
                return True
        return False

    def get_feature_index(self,
                          featureId: int):
        for index in range(len(self._modelFeatures)):
            if self._modelFeatures[index].feature_id() == featureId:
                return self.index(index, 0, QModelIndex())

        return QModelIndex()
