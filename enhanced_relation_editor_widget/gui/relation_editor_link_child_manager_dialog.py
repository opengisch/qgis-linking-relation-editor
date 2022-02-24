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
from qgis.PyQt.QtCore import (
    Qt,
    QItemSelectionModel,
    QTimer
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QMessageBox
)
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsFeatureRequest,
    QgsRelation,
    QgsVectorLayer,
    QgsVectorLayerCache,
    QgsVectorLayerUtils
)
from qgis.gui import (
    QgsAttributeEditorContext,
    QgsFilterLineEdit,
    QgsIdentifyMenu,
    QgsHighlight,
    QgsMessageBar
)
from qgis.utils import iface
from enhanced_relation_editor_widget.core.features_model import FeaturesModel
from enhanced_relation_editor_widget.core.features_model_filter import FeaturesModelFilter
from enhanced_relation_editor_widget.gui.feature_filter_widget import FeatureFilterWidget
from enhanced_relation_editor_widget.gui.map_tool_select_rectangle import MapToolSelectRectangle


WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__),
                                      '../ui/relation_editor_link_child_manager_dialog.ui'))


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

        self._mapToolSelect = None
        if self._canvas():
            self._mapToolSelect = MapToolSelectRectangle(self._canvas(),
                                                         self._layer)

        self._highlight = list()

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
        self._actionQuickFilter = QAction(QgsApplication.getThemeIcon("/mIndicatorFilter.svg"),
                                          self.tr("Quick filter"))
        self._actionQuickFilter.setCheckable(True)
        self._actionMapFilter = QAction(QgsApplication.getThemeIcon("/mActionMapIdentification.svg"),
                                        self.tr("Select features on map"))
        self._actionMapFilter.setCheckable(True)
        self._actionZoomToSelectedLeft = QAction(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"),
                                                 self.tr("Zoom To Feature(s)"))
        self._actionZoomToSelectedLeft.setToolTip(self.tr("Zoom to selected child feature(s)"))
        self._actionZoomToSelectedRight = QAction(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"),
                                                  self.tr("Zoom To Feature(s)"))
        self._actionZoomToSelectedRight.setToolTip(self.tr("Zoom to selected child feature(s)"))

        # Tool buttons
        self.mLinkSelectedButton.setDefaultAction(self._actionLinkSelected)
        self.mUnlinkSelectedButton.setDefaultAction(self._actionUnlinkSelected)
        self.mLinkAllButton.setDefaultAction(self._actionLinkAll)
        self.mUnlinkAllButton.setDefaultAction(self._actionUnlinkAll)
        self.mQuickFilterButton.setDefaultAction(self._actionQuickFilter)
        self.mSelectOnMapButton.setDefaultAction(self._actionMapFilter)
        self.mZoomToFeatureLeftButton.setDefaultAction(self._actionZoomToSelectedLeft)
        self.mZoomToFeatureRightButton.setDefaultAction(self._actionZoomToSelectedRight)

        self.mLinkSelectedButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mUnlinkSelectedButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mLinkAllButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mUnlinkAllButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mQuickFilterButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mSelectOnMapButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mZoomToFeatureLeftButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.mZoomToFeatureRightButton.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self.mSelectOnMapButton.setVisible(self._layer.isSpatial())
        self.mZoomToFeatureLeftButton.setVisible(self._layer.isSpatial())
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

        linkedFeatures, unlinkedFeatures, request = self._getAllFeatures()

        self._featuresModelLeft = FeaturesModel(unlinkedFeatures,
                                                FeaturesModel.FeatureState.Unlinked,
                                                self._layer,
                                                self)

        self._featuresModelFilterLeft = FeaturesModelFilter(self._layer,
                                                            request,
                                                            self)
        self._featuresModelFilterLeft.setSourceModel(self._featuresModelLeft)

        self.mFeaturesListViewLeft.setModel(self._featuresModelFilterLeft)

        self._featuresModelRight = FeaturesModel(linkedFeatures,
                                                 FeaturesModel.FeatureState.Linked,
                                                 self._layer,
                                                 self)
        self.mFeaturesListViewRight.setModel(self._featuresModelRight)

        self.mQuickFilterLineEdit.setVisible(False)

        self._feature_filter_widget = FeatureFilterWidget(self)
        self.mFooterHBoxLayout.insertWidget(0,
                                            self._feature_filter_widget)
        self._feature_filter_widget.init(self._layer,
                                         self._editorContext,
                                         self._featuresModelFilterLeft,
                                         iface.messageBar(),
                                         QgsMessageBar.defaultMessageTimeout())
        self._feature_filter_widget.filterShowAll()

        # Signal slots
        self.accepted.connect(self._closing)
        self.rejected.connect(self._closing)
        self._actionLinkSelected.triggered.connect(self._linkSelected)
        self._actionUnlinkSelected.triggered.connect(self._unlinkSelected)
        self._actionLinkAll.triggered.connect(self._linkAll)
        self._actionUnlinkAll.triggered.connect(self._unlinkAll)
        self._actionQuickFilter.triggered.connect(self._quick_filter_triggered)
        self._actionMapFilter.triggered.connect(self._map_filter_triggered)
        self._actionZoomToSelectedLeft.triggered.connect(self._zoomToSelectedLeft)
        self._actionZoomToSelectedRight.triggered.connect(self._zoomToSelectedRight)
        if self._mapToolSelect:
            self._mapToolSelect.signal_selection_finished.connect(self._map_tool_select_finished)
            self._mapToolSelect.deactivated.connect(self._mapToolDeactivated)

        self.mQuickFilterLineEdit.valueChanged.connect(self._quick_filter_value_changed)

    def get_feature_ids_to_unlink(self):
        featureIdsToUnlink = []
        for featureModelItem in self._featuresModelLeft.get_all_feature_items():
            if featureModelItem.feature_state() == FeaturesModel.FeatureState.ToBeUnlinked:
                featureIdsToUnlink.append(featureModelItem.feature().id())

        return featureIdsToUnlink

    def get_feature_ids_to_link(self):
        featureIdsToLink = []
        for featureModelItem in self._featuresModelRight.get_all_feature_items():
            if featureModelItem.feature_state() == FeaturesModel.FeatureState.ToBeLinked:
                featureIdsToLink.append(featureModelItem.feature().id())

        return featureIdsToLink

    def _getAllFeatures(self):

        if not self._relation.isValid() or not self._parentFeature.isValid():
            return [], [], QgsFeatureRequest()

        linkedFeatures = dict()
        layer = self._relation.referencingLayer()
        request = self._relation.getRelatedFeaturesRequest(self._parentFeature)
        for feature in layer.getFeatures(request):
            linkedFeatures[feature.id()] = feature

        if self._nmRelation.isValid():
            filters = []
            for joinTableFeatureId, joinTableFeature in linkedFeatures.items():
                referencedFeatureRequest = self._nmRelation.getReferencedFeatureRequest(joinTableFeature)
                filterExpression = referencedFeatureRequest.filterExpression()
                filters.append("(" + filterExpression.expression() + ")")

            request = QgsFeatureRequest()
            request.setFilterExpression(" OR ".join(filters))

            linkedFeatures = dict()
            layer = self._nmRelation.referencedLayer()
            for documentFeature in layer.getFeatures(request):
                linkedFeatures[documentFeature.id()] = documentFeature

        unlinkedFeatures = list(layer.getFeatures())
        unlinkedFeatures = [unlinkedFeature for unlinkedFeature in unlinkedFeatures if unlinkedFeature.id() not in linkedFeatures]

        return linkedFeatures.values(), unlinkedFeatures, request

    def _linkSelected(self):
        featuresModelElements = []
        for modelIndex in self.mFeaturesListViewLeft.selectedIndexes():
            featuresModelElements.append(self._featuresModelLeft.take_item(modelIndex))

        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeUnlinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Linked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeLinked)

        self._featuresModelRight.add_features_model_items(featuresModelElements)

    def _unlinkSelected(self):
        featuresModelElements = []
        for modelIndex in self.mFeaturesListViewRight.selectedIndexes():
            featuresModelElements.append(self._featuresModelRight.take_item(modelIndex))

        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeLinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Unlinked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeUnlinked)

        self._featuresModelLeft.add_features_model_items(featuresModelElements)

    def _linkAll(self):
        featuresModelElements = list()
        if self._featuresModelFilterLeft.filter_active():
            for row in reversed(range(self._featuresModelFilterLeft.rowCount())):
                modelIndex = self._featuresModelFilterLeft.index(row, 0)
                sourceModelIndex = self._featuresModelFilterLeft.mapToSource(modelIndex)
                featuresModelElements.append(self._featuresModelLeft.take_item(sourceModelIndex))
        else:
            featuresModelElements = self._featuresModelLeft.take_all_items()
        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeUnlinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Linked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeLinked)

        self._featuresModelRight.add_features_model_items(featuresModelElements)

    def _unlinkAll(self):
        featuresModelElements = self._featuresModelRight.take_all_items()
        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeLinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Unlinked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeUnlinked)

        self._featuresModelLeft.add_features_model_items(featuresModelElements)

    def _quick_filter_triggered(self,
                                checked: bool):
        self.mQuickFilterLineEdit.setVisible(checked)
        if checked:
            self.mQuickFilterLineEdit.setFocus()
            self._featuresModelFilterLeft.set_quick_filter(self.mQuickFilterLineEdit.value())
        else:
            self._featuresModelFilterLeft.clear_quick_filter()

    def _quick_filter_value_changed(self,
                                    value: str):
        self._featuresModelFilterLeft.set_quick_filter(value)

    def _map_filter_triggered(self,
                              checked: bool):
        if not self._canvas():
            return

        if checked:
            iface.actionSelect().trigger()
            self._setMapTool(self._mapToolSelect)

            title = self.tr("Relation {0} for {1}.").format(self._relation.name(),
                                                            self._parentLayer.name())
            msg = self.tr("Identify a feature of {0} to be associated. Press &lt;ESC&gt; to cancel.").format(self._layer.name())
            self._messageBarItem = QgsMessageBar.createMessage(title,
                                                               msg,
                                                               self)
            iface.messageBar().pushItem(self._messageBarItem)

        else:
            self._featuresModelFilterLeft.clear_map_filter()

    def _zoomToSelectedLeft(self):
        if not self._canvas():
            return

        selectedFeatureIds = []
        for modelIndex in self.mFeaturesListViewLeft.selectedIndexes():
            selectedFeatureIds.append(self._featuresModelFilterLeft.data(modelIndex,
                                                                         FeaturesModel.UserRole.FeatureId))

        if len(selectedFeatureIds) == 0:
            return

        self._canvas().zoomToFeatureIds(self._layer,
                                        selectedFeatureIds)

    def _zoomToSelectedRight(self):
        if not self._canvas():
            return

        selectedFeatureIds = []
        for modelIndex in self.mFeaturesListViewRight.selectedIndexes():
            selectedFeatureIds.append(self._featuresModelRight.data(modelIndex,
                                                                    FeaturesModel.UserRole.FeatureId))

        if len(selectedFeatureIds) == 0:
            return

        self._canvas().zoomToFeatureIds(self._layer,
                                        selectedFeatureIds)

    def _map_tool_select_finished(self,
                                       features: list):

        self.mFeaturesListViewLeft.selectionModel().reset()

        already_linked_features = list()
        map_filter_features = list()
        for feature in features:
            # select this feature
            if not feature.isValid():
                continue

            if self._featuresModelRight.contains(feature.id()):
                already_linked_features.append(str(feature.id()))
                continue

            map_filter_features.append(feature.id())
            self._highlightFeature(feature)

        if already_linked_features:
            QMessageBox.warning(self._canvas().window(),
                                self.tr("Feature already linked"),
                                self.tr("Some feature(s) are already linked: '{0}'").format(', '.join(already_linked_features)))

        if map_filter_features:
            self._featuresModelFilterLeft.set_map_filter(map_filter_features)
        else:
            self._actionMapFilter.setChecked(False)

        #  self.show()
        self._unsetMapTool()

    def _setMapTool(self,
                    mapTool):
        #  self.hide() TODO Is it possible to hide the parent feature form too?
        self._canvas().setMapTool(mapTool)
        self._canvas().window().raise_()
        self._canvas().activateWindow()
        self._canvas().setFocus()

    def _unsetMapTool(self):
        # this will call mapToolDeactivated
        self._canvas().unsetMapTool(self._mapToolSelect)

    def _mapToolDeactivated(self):

        self.window().raise_()
        self.window().activateWindow()

        iface.messageBar().popWidget(self._messageBarItem)

    def _highlightFeature(self,
                          feature: QgsFeature):

        if not self._canvas():
            return

        if not feature.isValid():
            return

        if not feature.hasGeometry():
            return

        # Highlight selected features shortly
        highlight = QgsHighlight(self._canvas(),
                                 feature,
                                 self._layer)
        QgsIdentifyMenu.styleHighlight(highlight)
        highlight.show()
        self._highlight.append(highlight)
        QTimer.singleShot(3000,
                          self._deleteHighlight)

    def _deleteHighlight(self):
        if not self._highlight:
            return

        highlight = self._highlight[0].hide()
        del self._highlight[0]

    def _canvas(self):
        if not self._editorContext:
            return None
        return self._editorContext.mapCanvas()

    def _closing(self):
        self._deleteHighlight()
        self._unsetMapTool()
