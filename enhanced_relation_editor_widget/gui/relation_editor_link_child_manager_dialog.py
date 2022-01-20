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
from enhanced_relation_editor_widget.core.features_model import FeaturesModel


WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), '../ui/relation_editor_link_child_manager_dialog.ui'))


class RelationEditorLinkChildManagerDialog(QDialog, WidgetUi):

    def __init__(self,
                 layer: QgsVectorLayer,
                 parentLayer: QgsVectorLayer,
                 parentFeature: QgsFeature,
                 relation: QgsRelation,
                 nmRelation: QgsRelation,
                 parent=None):
        super().__init__(parent)

        self._layer = layer
        self._parentLayer = parentLayer
        self._parentFeature = parentFeature
        self._relation = relation
        self._nmRelation = nmRelation

        # Ui setup
        self.setupUi(self)

        # Actions
        self.actionLinkSelected = QAction(QgsApplication.getThemeIcon("/mActionArrowRight.svg"),
                                          self.tr("Link selected"))
        self.actionUnlinkSelected = QAction(QgsApplication.getThemeIcon("/mActionArrowLeft.svg"),
                                            self.tr("Unlink seleted"))
        self.actionLinkAll = QAction(QgsApplication.getThemeIcon("/mActionDoubleArrowRight.svg"),
                                     self.tr("Link all"))
        self.actionUnlinkAll = QAction(QgsApplication.getThemeIcon("/mActionDoubleArrowLeft.svg"),
                                       self.tr("Unlink all"))

        # Tool buttons
        self.mLinkSelectedButton.setDefaultAction(self.actionLinkSelected)
        self.mLinkSelectedButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mUnlinkSelectedButton.setDefaultAction(self.actionUnlinkSelected)
        self.mUnlinkSelectedButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mLinkAllButton.setDefaultAction(self.actionLinkAll)
        self.mLinkAllButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mUnlinkAllButton.setDefaultAction(self.actionUnlinkAll)
        self.mUnlinkAllButton.setToolButtonStyle(Qt.ToolButtonIconOnly)

        # ListView menu
        self.mFeaturesListViewLeft.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.mFeaturesListViewLeft.addAction(self.actionLinkSelected)
        self.mFeaturesListViewLeft.addAction(self.actionLinkAll)
        self.mFeaturesListViewRight.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.mFeaturesListViewRight.addAction(self.actionUnlinkSelected)
        self.mFeaturesListViewRight.addAction(self.actionUnlinkAll)

        displayString = QgsVectorLayerUtils.getFeatureDisplayString(self._parentLayer,
                                                                    self._parentFeature)
        self.setWindowTitle(self.tr("Manage linked features for parent {0} \"{1}\"").format(self._parentLayer.name(),
                                                                                            displayString))

        self.mLayerNameLabel.setText(self._layer.name())

        linkedFeatures, unlinkedFeatures = self._getAllFeatures()

        self._featuresModelLeft = FeaturesModel(unlinkedFeatures,
                                                self._layer,
                                                self)
        self.mFeaturesListViewLeft.setModel(self._featuresModelLeft)

        self._featuresModelRight = FeaturesModel(linkedFeatures,
                                                 self._layer,
                                                 self)
        self.mFeaturesListViewRight.setModel(self._featuresModelRight)

        # Signal slots
        self.actionLinkSelected.triggered.connect(self._linkSelected)
        self.actionUnlinkSelected.triggered.connect(self._unlinkSelected)
        self.actionLinkAll.triggered.connect(self._linkAll)
        self.actionUnlinkAll.triggered.connect(self._unlinkAll)

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
        pass

    def _unlinkSelected(self):
        pass

    def _linkAll(self):
        pass

    def _unlinkAll(self):
        pass
