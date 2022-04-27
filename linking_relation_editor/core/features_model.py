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
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsVectorLayer,
    QgsVectorLayerUtils
)


class FeaturesModel(QAbstractListModel):

    class UserRole(IntEnum):
        FeatureId = Qt.UserRole + 1

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
            self._layer = layer
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
                return QIcon(os.path.join(os.path.dirname(__file__), '../images/mNoAction.svg'))
            elif self._featureState == FeaturesModel.FeatureState.ToBeLinked:
                return QIcon(os.path.join(os.path.dirname(__file__), '../images/mActionToBeLinked.svg'))
            elif self._featureState == FeaturesModel.FeatureState.ToBeUnlinked:
                return QIcon(os.path.join(os.path.dirname(__file__), '../images/mActionToBeUnlinked.svg'))

            return QIcon()

        def tool_tip(self):
            subContext = QgsExpressionContext()
            subContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(self._layer))
            subContext.setFeature(self._feature)

            return QgsExpression.replaceExpressionText(self._layer.mapTipTemplate(),
                                                       subContext)

    def __init__(self,
                 features,
                 featureState,
                 layer: QgsVectorLayer,
                 parent: QObject = None):
        super().__init__(parent)

        self._layer = layer
        self._modelFeatures = []
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

        if role == Qt.ToolTipRole:
            return self._modelFeatures[index.row()].tool_tip()

        if role == FeaturesModel.UserRole.FeatureId:
            return self._modelFeatures[index.row()].feature_id()

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
                     features_state):
        self.beginResetModel()

        self._modelFeatures = []
        for feature in features:
            self._modelFeatures.append(FeaturesModel.FeaturesModelItem(feature,
                                                                       features_state,
                                                                       self._layer))

        self.endResetModel()

    def get_all_feature_items(self):
        return self._modelFeatures

    def add_features_model_items(self,
                                 feature_model_elements):
        self.beginInsertRows(QModelIndex(),
                             self.rowCount(),
                             self.rowCount() + len(feature_model_elements))
        self._modelFeatures.extend(feature_model_elements)
        self.endInsertRows()

    def take_all_items(self):
        self.beginResetModel()
        featureModelElements = self._modelFeatures
        self._modelFeatures = []
        self.endResetModel()
        return featureModelElements

    def take_item(self,
                  index: QModelIndex):

        if not index.isValid():
            return None

        self.beginRemoveRows(QModelIndex(),
                             index.row(),
                             index.row()+1)
        feature = self._modelFeatures[index.row()]
        del self._modelFeatures[index.row()]
        self.endRemoveRows()

        return feature

    def take_items(self,
                  indexes):

        if not indexes:
            return None
        features=[]
        rows_to_remove = []
        for index in indexes:
            row = index.row()
            features.append(self._modelFeatures[row])
            rows_to_remove.append(row)

        rows_to_remove.sort(reverse=True)
        for row in rows_to_remove:
            self.beginRemoveRows(QModelIndex(),
                                row,
                                row+1)
            del self._modelFeatures[row]
            self.endRemoveRows()

        return features

    def contains(self,
                 feature_id: int):
        for feature in self._modelFeatures:
            if feature.feature_id() == feature_id:
                return True
        return False

    def get_feature_index(self,
                          feature_id: int):
        for index in range(len(self._modelFeatures)):
            if self._modelFeatures[index].feature_id() == feature_id:
                return self.index(index, 0, QModelIndex())

        return QModelIndex()
