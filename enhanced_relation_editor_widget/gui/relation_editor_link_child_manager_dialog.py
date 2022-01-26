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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QDialog,
    QAction
)
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsFeatureRequest,
    QgsRelation,
    QgsVectorLayer,
    QgsVectorLayerUtils
)
from qgis.gui import QgsAttributeEditorContext
from enhanced_relation_editor_widget.core.features_model import FeaturesModel


WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), '../ui/relation_editor_link_child_manager_dialog.ui'))


class RelationEditorLinkChildManagerDialog(QDialog, WidgetUi):

    def __init__(self,
                 layer: QgsVectorLayer,
                 parentLayer: QgsVectorLayer,
                 parentFeature: QgsFeature,
                 relation: QgsRelation,
                 nmRelation: QgsRelation,
                 editorContext: QgsAttributeEditorContext,
                 parent=None):
        super().__init__(parent)

        self._layer = layer
        self._parentLayer = parentLayer
        self._parentFeature = parentFeature
        self._relation = relation
        self._nmRelation = nmRelation
        self._editorContext = editorContext

        # Ui setup
        self.setupUi(self)

        # Actions
        self._actionLinkSelected = QAction(QgsApplication.getThemeIcon("/mActionArrowRight.svg"),
                                           self.tr("Link selected"))
        self._actionUnlinkSelected = QAction(QgsApplication.getThemeIcon("/mActionArrowLeft.svg"),
                                             self.tr("Unlink seleted"))
        self._actionLinkAll = QAction(QgsApplication.getThemeIcon("/mActionDoubleArrowRight.svg"),
                                      self.tr("Link all"))
        self._actionUnlinkAll = QAction(QgsApplication.getThemeIcon("/mActionDoubleArrowLeft.svg"),
                                        self.tr("Unlink all"))
        self._actionZoomToSelectedLeft = QAction(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"),
                                                 self.tr("Zoom To Feature(s)"))
        self._actionZoomToSelectedLeft.setToolTip(self.tr("Zoom to selected child feature(s)"))
        self._actionZoomToSelectedRight = QAction(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"),
                                                  self.tr("Zoom To Feature(s)"))
        self._actionZoomToSelectedRight.setToolTip(self.tr("Zoom to selected child feature(s)"))

        # Tool buttons
        self.mLinkSelectedButton.setDefaultAction(self._actionLinkSelected)
        self.mLinkSelectedButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mUnlinkSelectedButton.setDefaultAction(self._actionUnlinkSelected)
        self.mUnlinkSelectedButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mLinkAllButton.setDefaultAction(self._actionLinkAll)
        self.mLinkAllButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mUnlinkAllButton.setDefaultAction(self._actionUnlinkAll)
        self.mUnlinkAllButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mZoomToFeatureLeftButton.setDefaultAction(self._actionZoomToSelectedLeft)
        self.mZoomToFeatureLeftButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mZoomToFeatureLeftButton.setVisible(self._layer.isSpatial())
        self.mZoomToFeatureRightButton.setDefaultAction(self._actionZoomToSelectedRight)
        self.mZoomToFeatureRightButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mZoomToFeatureRightButton.setVisible(self._layer.isSpatial())

        # ListView menu
        self.mFeaturesListViewLeft.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.mFeaturesListViewLeft.addAction(self._actionLinkSelected)
        self.mFeaturesListViewLeft.addAction(self._actionLinkAll)
        self.mFeaturesListViewRight.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.mFeaturesListViewRight.addAction(self._actionUnlinkSelected)
        self.mFeaturesListViewRight.addAction(self._actionUnlinkAll)
        if self._layer.isSpatial():
            self.mFeaturesListViewLeft.addAction(self._actionZoomToSelectedLeft)
            self.mFeaturesListViewRight.addAction(self._actionZoomToSelectedRight)

        displayString = QgsVectorLayerUtils.getFeatureDisplayString(self._parentLayer,
                                                                    self._parentFeature)
        self.setWindowTitle(self.tr("Manage linked features for parent {0} \"{1}\"").format(self._parentLayer.name(),
                                                                                            displayString))

        self.mLayerNameLabel.setText(self._layer.name())

        linkedFeatures, unlinkedFeatures = self._getAllFeatures()

        self._featuresModelLeft = FeaturesModel(unlinkedFeatures,
                                                FeaturesModel.FeatureState.Unlinked,
                                                self._layer,
                                                self.mFeaturesListViewLeft,
                                                self)
        self.mFeaturesListViewLeft.setModel(self._featuresModelLeft)

        self._featuresModelRight = FeaturesModel(linkedFeatures,
                                                 FeaturesModel.FeatureState.Linked,
                                                 self._layer,
                                                 self.mFeaturesListViewRight,
                                                 self)
        self.mFeaturesListViewRight.setModel(self._featuresModelRight)

        # Signal slots
        self._actionLinkSelected.triggered.connect(self._linkSelected)
        self._actionUnlinkSelected.triggered.connect(self._unlinkSelected)
        self._actionLinkAll.triggered.connect(self._linkAll)
        self._actionUnlinkAll.triggered.connect(self._unlinkAll)
        self._actionZoomToSelectedLeft.triggered.connect(self._zoomToSelectedLeft)
        self._actionZoomToSelectedRight.triggered.connect(self._zoomToSelectedRight)

    def getFeatureIdsToUnlink(self):
        featureIdsToUnlink = []
        for featureModelItem in self._featuresModelLeft.getAllFeatureItems():
            if featureModelItem.featureState() == FeaturesModel.FeatureState.ToBeUnlinked:
                featureIdsToUnlink.append(featureModelItem.feature().id())

        return featureIdsToUnlink

    def getFeatureIdsToLink(self):
        featureIdsToLink = []
        for featureModelItem in self._featuresModelRight.getAllFeatureItems():
            if featureModelItem.featureState() == FeaturesModel.FeatureState.ToBeLinked:
                featureIdsToLink.append(featureModelItem.feature().id())

        return featureIdsToLink

    def _getAllFeatures(self):

        if not self._relation.isValid() or not self._parentFeature.isValid():
            return [], []

        linkedFeatures = dict()
        layer = self._relation.referencingLayer()
        request = self._relation.getRelatedFeaturesRequest(self._parentFeature)
        for feature in layer.getFeatures(request):
            linkedFeatures[feature.id()] = feature

        if self._nmRelation.isValid():
            filters = []
            for joinTableFeature in feature_list:
                referencedFeatureRequest = self._nmRelation.getReferencedFeatureRequest(joinTableFeature)
                filterExpression = referencedFeatureRequest.filterExpression()
                filters.append("(" + filterExpression.expression() + ")")

            nmRequest = QgsFeatureRequest()
            nmRequest.setFilterExpression(" OR ".join(filters))

            linkedFeatures = dict()
            layer = self._nmRelation.referencedLayer()
            for documentFeature in layer.getFeatures(nmRequest):
                linkedFeatures[documentFeature.id()] = documentFeature

        unlinkedFeatures = list(layer.getFeatures())
        unlinkedFeatures = [unlinkedFeature for unlinkedFeature in unlinkedFeatures if unlinkedFeature.id() not in linkedFeatures]

        return linkedFeatures.values(), unlinkedFeatures

    def _linkSelected(self):
        featuresModelElements = self._featuresModelLeft.takeSelectedItems()
        for featuresModelElement in featuresModelElements:
            if featuresModelElement.featureState() == FeaturesModel.FeatureState.ToBeUnlinked:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.Linked)
            else:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.ToBeLinked)

        self._featuresModelRight.addFeaturesModelItems(featuresModelElements)

    def _unlinkSelected(self):
        featuresModelElements = self._featuresModelRight.takeSelectedItems()
        for featuresModelElement in featuresModelElements:
            if featuresModelElement.featureState() == FeaturesModel.FeatureState.ToBeLinked:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.Unlinked)
            else:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.ToBeUnlinked)

        self._featuresModelLeft.addFeaturesModelItems(featuresModelElements)

    def _linkAll(self):
        featuresModelElements = self._featuresModelLeft.takeAllItems()
        for featuresModelElement in featuresModelElements:
            if featuresModelElement.featureState() == FeaturesModel.FeatureState.ToBeUnlinked:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.Linked)
            else:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.ToBeLinked)

        self._featuresModelRight.addFeaturesModelItems(featuresModelElements)

    def _unlinkAll(self):
        featuresModelElements = self._featuresModelRight.takeAllItems()
        for featuresModelElement in featuresModelElements:
            if featuresModelElement.featureState() == FeaturesModel.FeatureState.ToBeLinked:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.Unlinked)
            else:
                featuresModelElement.setFeatureState(FeaturesModel.FeatureState.ToBeUnlinked)

        self._featuresModelLeft.addFeaturesModelItems(featuresModelElements)

    def _zoomToSelectedLeft(self):
        if not self._editorContext.mapCanvas():
            return

        selectedFeatureIds = self._featuresModelLeft.getSelectedFeatures()
        if len(selectedFeatureIds) == 0:
            return

        self._editorContext.mapCanvas().zoomToFeatureIds(self._layer,
                                                         selectedFeatureIds)

    def _zoomToSelectedRight(self):
        if not self._editorContext.mapCanvas():
            return

        selectedFeatureIds = self._featuresModelRight.getSelectedFeatures()
        if len(selectedFeatureIds) == 0:
            return

        self._editorContext.mapCanvas().zoomToFeatureIds(self._layer,
                                                         selectedFeatureIds)
