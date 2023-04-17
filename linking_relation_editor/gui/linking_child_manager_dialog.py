# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Linking Relation Editor
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

import os

from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsFeatureRequest,
    QgsRelation,
    QgsVectorLayer,
    QgsVectorLayerUtils,
)
from qgis.gui import (
    QgsAttributeEditorContext,
    QgsAttributeForm,
    QgsHighlight,
    QgsIdentifyMenu,
    QgsMessageBar,
)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QAction, QDialog, QMessageBox, QTreeWidgetItem
from qgis.PyQt.uic import loadUiType
from qgis.utils import iface

from linking_relation_editor.core.features_model import FeaturesModel
from linking_relation_editor.core.features_model_filter import FeaturesModelFilter
from linking_relation_editor.gui.feature_filter_widget import FeatureFilterWidget
from linking_relation_editor.gui.map_tool_select_rectangle import MapToolSelectRectangle

WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), "../ui/linking_child_manager_dialog.ui"))

CONFIG_SHOW_AND_EDIT_JOIN_TABLE_ATTRIBUTES = "show_and_edit_join_table_attributes"


class LinkingChildManagerDialog(QDialog, WidgetUi):
    def __init__(
        self,
        layer: QgsVectorLayer,
        parentLayer: QgsVectorLayer,
        parentFeature: QgsFeature,
        relation: QgsRelation,
        nmRelation: QgsRelation,
        editorContext: QgsAttributeEditorContext,
        oneToOne: bool,
        linkingChildManagerDialogConfig: dict,
        parent=None,
    ):
        super().__init__(parent)

        self._layer = layer
        self._parentLayer = parentLayer
        self._parentFeature = parentFeature
        self._relation = relation
        self._nmRelation = nmRelation
        self._editorContext = editorContext
        self._oneToOne = oneToOne
        self._linkingChildManagerDialogConfig = linkingChildManagerDialogConfig

        self._mapToolSelect = None
        if self._canvas():
            self._mapToolSelect = MapToolSelectRectangle(self._canvas(), self._layer)

        self._highlight = []
        self._featureFormWidgets = []

        # Ui setup
        self.setupUi(self)

        # Actions
        self._actionLinkSelected = QAction(
            QgsApplication.getThemeIcon("/mActionArrowRight.svg"), self.tr("Link selected")
        )
        self._actionUnlinkSelected = QAction(
            QgsApplication.getThemeIcon("/mActionArrowLeft.svg"), self.tr("Unlink selected")
        )
        self._actionLinkAll = QAction(QgsApplication.getThemeIcon("/mActionDoubleArrowRight.svg"), self.tr("Link all"))
        self._actionUnlinkAll = QAction(
            QgsApplication.getThemeIcon("/mActionDoubleArrowLeft.svg"), self.tr("Unlink all")
        )
        self._actionQuickFilter = QAction(QgsApplication.getThemeIcon("/mIndicatorFilter.svg"), self.tr("Quick filter"))
        self._actionQuickFilter.setCheckable(True)
        self._actionMapFilter = QAction(
            QgsApplication.getThemeIcon("/mActionMapIdentification.svg"), self.tr("Select features on map")
        )
        self._actionMapFilter.setCheckable(True)
        self._actionZoomToSelectedLeft = QAction(
            QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"), self.tr("Zoom To Feature(s)")
        )
        self._actionZoomToSelectedLeft.setToolTip(self.tr("Zoom to selected child feature(s)"))
        self._actionZoomToSelectedRight = QAction(
            QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"), self.tr("Zoom To Feature(s)")
        )
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
        self.mFeaturesTreeWidgetRight.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.mFeaturesTreeWidgetRight.addAction(self._actionUnlinkSelected)
        self.mFeaturesTreeWidgetRight.addAction(self._actionUnlinkAll)
        if self._layer.isSpatial():
            self.mFeaturesListViewLeft.addAction(self._actionZoomToSelectedLeft)
            self.mFeaturesTreeWidgetRight.addAction(self._actionZoomToSelectedRight)

        displayString = QgsVectorLayerUtils.getFeatureDisplayString(self._parentLayer, self._parentFeature)
        self.setWindowTitle(
            self.tr('Manage linked features for parent {0} "{1}"').format(self._parentLayer.name(), displayString)
        )

        self.mLayerNameLabel.setText(self._layer.name())

        linkedFeatures, unlinkedFeatures, request = self._getAllFeatures()

        self._featuresModelLeft = FeaturesModel(
            unlinkedFeatures, FeaturesModel.FeatureState.Unlinked, self._layer, self
        )

        self._featuresModelFilterLeft = FeaturesModelFilter(self._layer, self._canvas(), self)
        self._featuresModelFilterLeft.setSourceModel(self._featuresModelLeft)

        self.mFeaturesListViewLeft.setModel(self._featuresModelFilterLeft)

        self._featuresModelRight = FeaturesModel(linkedFeatures, FeaturesModel.FeatureState.Linked, self._layer, self)
        self._updateFeaturesTreeWidgetRight()

        self.mQuickFilterLineEdit.setVisible(False)

        self._feature_filter_widget = FeatureFilterWidget(self)
        self.mFooterHBoxLayout.insertWidget(0, self._feature_filter_widget)
        if iface:  # TODO how to use iface in tests?
            self._feature_filter_widget.init(
                self._layer,
                self._editorContext,
                self._featuresModelFilterLeft,
                iface.messageBar(),
                QgsMessageBar.defaultMessageTimeout(),
            )
            self._feature_filter_widget.filterShowAll()

        # Signal slots
        self.accepted.connect(self._accepting)
        self.rejected.connect(self._rejecting)
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
        unlinkedFeatures = [
            unlinkedFeature for unlinkedFeature in unlinkedFeatures if unlinkedFeature.id() not in linkedFeatures
        ]

        return linkedFeatures.values(), unlinkedFeatures, request

    def _linkSelected(self):
        selected_indexes = self.mFeaturesListViewLeft.selectedIndexes()[:]

        if self._oneToOne:
            if self._featuresModelRight.rowCount() >= 1 or len(selected_indexes) > 1:
                QMessageBox.critical(
                    self._canvas().window(),
                    self.tr("One to one"),
                    self.tr(
                        "In one to one mode only one feature at the time can be linked. If it should not be in one to one mode, then change the cardinality in the relation editor configuration."
                    ),
                )
                return

        source_model_indexes = [
            self._featuresModelFilterLeft.mapToSource(model_index) for model_index in selected_indexes
        ]
        featuresModelElements = self._featuresModelLeft.take_items(source_model_indexes)

        if not featuresModelElements:
            return

        self._featuresModelFilterLeft.invalidate()

        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeUnlinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Linked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeLinked)

        self._featuresModelRight.add_features_model_items(featuresModelElements)
        self._updateFeaturesTreeWidgetRight()

    def _unlinkSelected(self):
        indexes = self.mFeaturesTreeWidgetRight.selectedIndexes()[:]
        featuresModelElements = self._featuresModelRight.take_items(indexes)

        if not featuresModelElements:
            return

        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeLinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Unlinked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeUnlinked)

        self._featuresModelLeft.add_features_model_items(featuresModelElements)

        self._updateFeaturesTreeWidgetRight()

    def _linkAll(self):
        if self._oneToOne:
            if self._featuresModelRight.rowCount() >= 1 or self._featuresModelFilterLeft.rowCount() > 1:
                QMessageBox.critical(
                    self._canvas().window(),
                    self.tr("One to one"),
                    self.tr(
                        "In one to one mode only one feature at the time can be linked. If it should not be in one to one mode, then change the cardinality in the relation editor configuration."
                    ),
                )
                return

        featuresModelElements = []
        if self._featuresModelFilterLeft.filter_active():
            source_model_indexes = [
                self._featuresModelFilterLeft.mapToSource(self._featuresModelFilterLeft.index(row, 0))
                for row in range(self._featuresModelFilterLeft.rowCount())
            ]
            featuresModelElements = self._featuresModelLeft.take_items(source_model_indexes)

        else:
            featuresModelElements = self._featuresModelLeft.take_all_items()

        if not featuresModelElements:
            return

        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeUnlinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Linked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeLinked)

        self._featuresModelRight.add_features_model_items(featuresModelElements)
        self._updateFeaturesTreeWidgetRight()

    def _unlinkAll(self):
        featuresModelElements = self._featuresModelRight.take_all_items()

        if not featuresModelElements:
            return

        for featuresModelElement in featuresModelElements:
            if featuresModelElement.feature_state() == FeaturesModel.FeatureState.ToBeLinked:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.Unlinked)
            else:
                featuresModelElement.set_feature_state(FeaturesModel.FeatureState.ToBeUnlinked)

        self._featuresModelLeft.add_features_model_items(featuresModelElements)
        self._updateFeaturesTreeWidgetRight()

    def _quick_filter_triggered(self, checked: bool):
        self.mQuickFilterLineEdit.setVisible(checked)
        if checked:
            self.mQuickFilterLineEdit.setFocus()
            self._featuresModelFilterLeft.set_quick_filter(self.mQuickFilterLineEdit.value())
        else:
            self._featuresModelFilterLeft.clear_quick_filter()

    def _quick_filter_value_changed(self, value: str):
        self._featuresModelFilterLeft.set_quick_filter(value)

    def _map_filter_triggered(self, checked: bool):
        if not self._canvas():
            return

        if checked:
            iface.actionSelect().trigger()
            self._setMapTool(self._mapToolSelect)

            title = self.tr("Relation {0} for {1}.").format(self._relation.name(), self._parentLayer.name())
            msg = self.tr("Select features of {0} to be considered. Press &lt;ESC&gt; to cancel.").format(
                self._layer.name()
            )
            self._messageBarItem = QgsMessageBar.createMessage(title, msg, self)
            iface.messageBar().pushItem(self._messageBarItem)

        else:
            self._featuresModelFilterLeft.clear_map_filter()

    def _zoomToSelectedLeft(self):
        if not self._canvas():
            return

        selectedFeatureIds = []
        for modelIndex in self.mFeaturesListViewLeft.selectedIndexes():
            selectedFeatureIds.append(self._featuresModelFilterLeft.data(modelIndex, FeaturesModel.UserRole.FeatureId))

        if len(selectedFeatureIds) == 0:
            return

        self._canvas().zoomToFeatureIds(self._layer, selectedFeatureIds)

    def _zoomToSelectedRight(self):
        if not self._canvas():
            return

        selectedFeatureIds = []
        for modelIndex in self.mFeaturesTreeWidgetRight.selectedIndexes():
            selectedFeatureIds.append(self._featuresModelRight.data(modelIndex, FeaturesModel.UserRole.FeatureId))

        if len(selectedFeatureIds) == 0:
            return

        self._canvas().zoomToFeatureIds(self._layer, selectedFeatureIds)

    def _map_tool_select_finished(self, features: list):
        self.mFeaturesListViewLeft.selectionModel().reset()

        already_linked_features = list()
        map_filter_features = list()
        for feature in features:
            # select this feature
            if not feature.isValid():
                continue

            if self._featuresModelRight.contains(feature.id()):
                already_linked_features.append(QgsVectorLayerUtils.getFeatureDisplayString(self._layer, feature))
                continue

            map_filter_features.append(feature.id())
            self._highlightFeature(feature)

        if already_linked_features:
            QMessageBox.warning(
                self._canvas().window(),
                self.tr("Feature already linked"),
                self.tr("Some feature(s) are already linked: '{0}'").format("', '".join(already_linked_features)),
            )

        if map_filter_features:
            self._featuresModelFilterLeft.set_map_filter(map_filter_features)
        else:
            self._actionMapFilter.setChecked(False)

        #  self.show()
        self._unsetMapTool()

    def _setMapTool(self, mapTool):
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

    def _highlightFeature(self, feature: QgsFeature):
        if not self._canvas():
            return

        if not feature.isValid():
            return

        if not feature.hasGeometry():
            return

        # Highlight selected features shortly
        highlight = QgsHighlight(self._canvas(), feature, self._layer)
        QgsIdentifyMenu.styleHighlight(highlight)
        highlight.show()
        self._highlight.append(highlight)
        QTimer.singleShot(3000, self._deleteHighlight)

    def _deleteHighlight(self):
        if not self._highlight:
            return

        self._highlight[0].hide()
        del self._highlight[0]

    def _canvas(self):
        if not self._editorContext:
            return None
        return self._editorContext.mapCanvas()

    def _rejecting(self):
        self._closing()

    def _accepting(self):
        # Save join features edits
        if self._linkingChildManagerDialogConfig.get(CONFIG_SHOW_AND_EDIT_JOIN_TABLE_ATTRIBUTES, False):
            for attributeFormWidget in self._featureFormWidgets:
                attributeFormWidget.save()

        self._closing()

    def _closing(self):
        self._deleteHighlight()
        self._unsetMapTool()

    def _updateFeaturesTreeWidgetRight(self):
        self.mFeaturesTreeWidgetRight.clear()
        self._featureFormWidgets = []

        for featureItem in self._featuresModelRight.get_all_feature_items():
            treeWidgetItem = QTreeWidgetItem(self.mFeaturesTreeWidgetRight)
            treeWidgetItem.setText(0, featureItem.display_string())
            treeWidgetItem.setIcon(0, featureItem.display_icon())
            self.mFeaturesTreeWidgetRight.addTopLevelItem(treeWidgetItem)

            if self._nmRelation.isValid() and self._linkingChildManagerDialogConfig.get(
                CONFIG_SHOW_AND_EDIT_JOIN_TABLE_ATTRIBUTES, False
            ):
                treeWidgetItemChildren = QTreeWidgetItem(treeWidgetItem)
                treeWidgetItem.addChild(treeWidgetItemChildren)

                joinLayer = self._nmRelation.referencingLayer()
                joinFeature = QgsFeature()

                if featureItem.feature_state() == FeaturesModel.FeatureState.Linked:
                    request = self._nmRelation.getRelatedFeaturesRequest(featureItem.feature())
                    for jfeature in joinLayer.getFeatures(request):
                        joinFeature = jfeature

                attributeForm = QgsAttributeForm(joinLayer, joinFeature)

                self.mFeaturesTreeWidgetRight.setItemWidget(treeWidgetItemChildren, 0, attributeForm)

                self._featureFormWidgets.append(attributeForm)
