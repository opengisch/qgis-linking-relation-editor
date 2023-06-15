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

from qgis.core import (
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsGeometry,
    QgsRelation,
    QgsVectorLayer,
    QgsVectorLayerUtils,
)
from qgis.PyQt.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt
from qgis.PyQt.QtGui import QIcon


class FeaturesModel(QAbstractItemModel):
    class UserRole(IntEnum):
        FeatureId = Qt.UserRole + 1

    class FeatureState(IntEnum):
        Linked = (1,)
        Unlinked = (2,)
        ToBeLinked = (3,)
        ToBeUnlinked = 4

    class FeaturesModelItem(object):
        def __init__(self, feature: QgsFeature, featureState, model):
            self._feature = feature
            self._featureState = featureState
            self._model = model

            self._displayString = QgsVectorLayerUtils.getFeatureDisplayString(self._model.layer, feature)
            self._childItem = None

            if self._model.handleJoinFeatures:
                joinLayer = self._model.nmRelation.referencingLayer()
                joinFeature = QgsFeature()

                if self._featureState == FeaturesModel.FeatureState.Linked:
                    request = self._model.nmRelation.getRelatedFeaturesRequest(self._feature)
                    for jfeature in joinLayer.getFeatures(request):
                        joinFeature = jfeature
                        break
                else:
                    # Expression context for the linking table
                    context = joinLayer.createExpressionContext()
                    joinFeature = QgsVectorLayerUtils.createFeature(joinLayer, QgsGeometry(), {}, context)

                    # Fields of the linking table
                    fields = joinLayer.fields()

                    if self._model.relation.type() == QgsRelation.Generated:
                        polyRel = self._model.relation.polymorphicRelation()
                        assert polyRel.isValid()

                        joinFeature[fields.indexFromName(polyRel.referencedLayerField())] = polyRel.layerRepresentation(
                            self.relation().referencedLayer()
                        )

                    for referencingField, referencedField in self._model.relation.fieldPairs().items():
                        index = fields.indexOf(referencingField)
                        joinFeature[index] = self._model.parentFeature.attribute(referencedField)

                    for referencingField, referencedField in self._model.nmRelation.fieldPairs().items():
                        index = fields.indexOf(referencingField)
                        joinFeature[index] = self._feature.attribute(referencedField)

                self._childItem = FeaturesModel.JoinFeaturesModelItem(joinFeature, joinLayer, self)

        def feature(self):
            return self._feature

        def feature_id(self):
            return self._feature.id()

        def feature_state(self):
            return self._featureState

        def set_feature_state(self, featureState):
            self._featureState = featureState

        def display_string(self):
            return self._displayString

        def display_icon(self):
            if (
                self._featureState == FeaturesModel.FeatureState.Unlinked
                or self._featureState == FeaturesModel.FeatureState.Linked
            ):
                return QIcon(os.path.join(os.path.dirname(__file__), "../../images/mNoAction.svg"))
            elif self._featureState == FeaturesModel.FeatureState.ToBeLinked:
                return QIcon(os.path.join(os.path.dirname(__file__), "../../images/mActionToBeLinked.svg"))
            elif self._featureState == FeaturesModel.FeatureState.ToBeUnlinked:
                return QIcon(os.path.join(os.path.dirname(__file__), "../../images/mActionToBeUnlinked.svg"))

            return QIcon()

        def tool_tip(self):
            subContext = QgsExpressionContext()
            subContext.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(self._model.layer))
            subContext.setFeature(self._feature)

            return QgsExpression.replaceExpressionText(self._model.layer.mapTipTemplate(), subContext)

        def childItem(self):
            return self._childItem

        def row(self) -> int:
            return 0

    class JoinFeaturesModelItem(object):
        def __init__(self, joinFeature: QgsFeature, joinLayer: QgsVectorLayer, parentItem):
            self._feature = joinFeature
            self._layer = joinLayer
            self._parentItem = parentItem
            self._attributeForm = None

        def parentItem(self):
            return self._parentItem

        def row(self) -> int:
            return 0  # There is alway only one link feature

        def childItem(self):
            return None

        def feature(self):
            return self._feature

        def layer(self):
            return self._layer

        def setAttributeForm(self, attributeForm):
            self._attributeForm = attributeForm

        def attributeForm(self):
            return self._attributeForm

    def __init__(
        self,
        features,
        featureState,
        layer: QgsVectorLayer,
        handleJoinFeatures: bool,
        parentFeature=QgsFeature,
        relation=QgsRelation,
        nmRelation=QgsRelation,
        parent: QObject = None,
    ):
        super().__init__(parent)
        self.layer = layer
        self._modelFeatures = []
        self.handleJoinFeatures = handleJoinFeatures
        self.parentFeature = parentFeature
        self.relation = relation
        self.nmRelation = nmRelation

        self.set_features(features, featureState)

    def featureItems(self):
        return self._modelFeatures

    def rowCount(self, index=QModelIndex()) -> int:
        if index.isValid():
            parentItem = index.internalPointer()
            if parentItem.childItem() is None:
                return 0
            else:
                return 1

        return len(self._modelFeatures)

    def columnCount(self, index: QModelIndex = ...) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = ...):
        if not index.isValid():
            return None

        childItem = index.internalPointer()

        if isinstance(childItem, FeaturesModel.FeaturesModelItem):
            if role == Qt.DisplayRole:
                return self._modelFeatures[index.row()].display_string()

            if role == Qt.DecorationRole:
                return self._modelFeatures[index.row()].display_icon()

            if role == Qt.ToolTipRole:
                return self._modelFeatures[index.row()].tool_tip()

            if role == FeaturesModel.UserRole.FeatureId:
                return self._modelFeatures[index.row()].feature_id()

        return None

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            print("Return invalid QModelIndex")
            return QModelIndex()

        parentItem = None
        if parent.isValid():
            parentItem = parent.internalPointer()

        print("----------------------------------------------------------------")

        print(
            "Row/Col: {}/{} Parent row/col: {}/{} PARENT: {}".format(
                row, column, parent.row(), parent.column(), parentItem
            )
        )

        if parentItem is None:
            print(
                "PARENT createIndex(row={}, column={}, self._modelFeatures[row]={})".format(
                    row, column, self._modelFeatures[row]
                )
            )
            return self.createIndex(row, column, self._modelFeatures[row])

        print(
            "Row/Col: {}/{} Parent row/col: {}/{} CHILD: {}".format(
                row, column, parent.row(), parent.column(), parentItem.childItem()
            )
        )

        # print("self._modelFeatures[parent.row()].childItem(): {}, parentItem.childItem(): {}".format(self._modelFeatures[parent.row()].childItem(), parentItem.childItem()))

        print(
            "CHILDREN createIndex(row={}, column={}, parentItem.childItem()={})".format(
                row, column, parentItem.childItem()
            )
        )
        # return self.createIndex(row, column, self._modelFeatures[row].childItem())
        return self.createIndex(row, column, parentItem.childItem())

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        if isinstance(childItem, FeaturesModel.FeaturesModelItem):
            return QModelIndex()

        parentItem = childItem.parentItem()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        childItem = index.internalPointer()
        if isinstance(childItem, FeaturesModel.FeaturesModelItem):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def getItem(self, index: QModelIndex):
        if not index.isValid():
            return None

        # No parent -> normal item
        if not self.parent(index).isValid():
            return self._modelFeatures[index.row()]

        # Otherwise, join item
        return self._modelFeatures[index.row()].childItem()

    def removeRows(self, row: int = ..., count: int = ..., index: QModelIndex = ...):
        if row + count > self.rowCount():
            return False

        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        self._modelFeatures[row : (row + count)] = []
        self.endRemoveRows()
        return True

    def supportedDropActions(self):
        return Qt.MoveAction

    def set_features(self, features, features_state):
        self.beginResetModel()

        self._modelFeatures = []
        for feature in features:
            featureItem = FeaturesModel.FeaturesModelItem(feature, features_state, self)
            self._modelFeatures.append(featureItem)

        self.endResetModel()

    def get_all_feature_items(self):
        return self._modelFeatures

    def add_features_model_items(self, feature_model_elements):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(feature_model_elements))
        self._modelFeatures.extend(feature_model_elements)
        self.endInsertRows()

    def take_all_items(self):
        self.beginResetModel()
        featureModelElements = self._modelFeatures
        self._modelFeatures = []
        self.endResetModel()
        return featureModelElements

    def take_item(self, index: QModelIndex):
        if not index.isValid():
            return None

        self.beginRemoveRows(QModelIndex(), index.row(), index.row() + 1)
        feature = self._modelFeatures[index.row()]
        del self._modelFeatures[index.row()]
        self.endRemoveRows()

        return feature

    def take_items(self, indexes):
        if not indexes:
            return []

        features = []
        rows_to_remove = []
        for index in indexes:
            row = index.row()
            features.append(self._modelFeatures[row])
            rows_to_remove.append(row)

        rows_to_remove.sort(reverse=True)
        for row in rows_to_remove:
            self.beginRemoveRows(QModelIndex(), row, row + 1)
            del self._modelFeatures[row]
            self.endRemoveRows()

        return features

    def contains(self, feature_id: int):
        for feature in self._modelFeatures:
            if feature.feature_id() == feature_id:
                return True
        return False

    def get_feature_index(self, feature_id: int):
        for index in range(len(self._modelFeatures)):
            if self._modelFeatures[index].feature_id() == feature_id:
                return self.index(index, 0, QModelIndex())

        return QModelIndex()
