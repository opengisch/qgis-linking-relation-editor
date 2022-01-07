# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2021 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

import os
from enum import Enum
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QButtonGroup
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeatureRequest,
    QgsLogger,
    QgsMessageLog,
    QgsProject,
    QgsRelation,
    QgsVectorLayer,
    QgsVectorLayerUtils
)
from qgis.gui import (
    QgsAbstractRelationEditorWidget,
    QgsDualView,
    QgsMessageBar,
    QgsRelationEditorWidget
)

WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), '../ui/enhanced_relation_editor_widget.ui'))

Debug = True

class EnhancedRelationEditorWidget(QgsAbstractRelationEditorWidget, WidgetUi):

    def __init__(self, config, parent):
        super().__init__(config, parent)

        self.mViewMode = QgsDualView.AttributeEditor
        self.mFeatureSelectionMgr = None # TODO

        self.mButtonsVisibility = QgsRelationEditorWidget.Button(QgsRelationEditorWidget.Button.AllButtons)

        self._nmRelation = QgsRelation()
        self._layerInSameTransactionGroup = False

        self._updateUiTimer = QTimer()
        self._updateUiTimer.setSingleShot(True)
        self._updateUiTimer.timeout.connect(self.updateUiTimeout)

        # Ui setup
        self.setupUi(self)

        # buttons
        # toggle editing
        self.mToggleEditingButton.setIcon(QgsApplication.getThemeIcon("/mActionToggleEditing.svg"))
        self.mToggleEditingButton.setText(self.tr("Toggle Editing"))
        self.mToggleEditingButton.setToolTip(self.tr("Toggle editing mode for child layer"))
        self.mToggleEditingButton.setCheckable(True)

        # save edits
        self.mSaveEditsButton.setIcon(QgsApplication.getThemeIcon("/mActionSaveEdits.svg"))
        self.mSaveEditsButton.setText(self.tr("Save Child Layer Edits"))
        self.mSaveEditsButton.setToolTip(self.tr("Save child layer edits"))

        # add feature
        self.mAddFeatureButton.setIcon(QgsApplication.getThemeIcon("/mActionNewTableRow.svg"))
        self.mAddFeatureButton.setText(self.tr("Add Child Feature"))
        self.mAddFeatureButton.setToolTip(self.tr("Add child feature"))

        # duplicate feature
        self.mDuplicateFeatureButton.setIcon(QgsApplication.getThemeIcon("/mActionDuplicateFeature.svg"))
        self.mDuplicateFeatureButton.setText(self.tr("Duplicate Child Feature(s)"))
        self.mDuplicateFeatureButton.setToolTip(self.tr("Duplicate selected child feature(s)"))

        # delete feature
        self.mDeleteFeatureButton.setIcon(QgsApplication.getThemeIcon("/mActionDeleteSelectedFeatures.svg"))
        self.mDeleteFeatureButton.setText(self.tr("Delete Child Feature(s)"))
        self.mDeleteFeatureButton.setToolTip(self.tr("Delete selected child feature(s)"))

        # link feature
        self.mLinkFeatureButton.setIcon(QgsApplication.getThemeIcon("/mActionLink.svg"))
        self.mLinkFeatureButton.setText(self.tr("Link Existing Feature(s)"))
        self.mLinkFeatureButton.setToolTip(self.tr("Link existing child feature(s)"))

        # unlink feature
        self.mUnlinkFeatureButton.setIcon(QgsApplication.getThemeIcon("/mActionUnlink.svg"))
        self.mUnlinkFeatureButton.setText(self.tr("Unlink Feature(s)"))
        self.mUnlinkFeatureButton.setToolTip(self.tr("Unlink selected child feature(s)"))

        # zoom to linked feature
        self.mZoomToFeatureButton.setIcon(QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"))
        self.mZoomToFeatureButton.setText(self.tr("Zoom To Feature(s)"))
        self.mZoomToFeatureButton.setToolTip(self.tr("Zoom to selected child feature(s)"))

        # form view
        self.mFormViewButton.setText(self.tr("Form View"))
        self.mFormViewButton.setToolTip(self.tr("Switch to form view"))
        self.mFormViewButton.setIcon(QgsApplication.getThemeIcon("/mActionPropertyItem.svg"))
        self.mFormViewButton.setCheckable(True)
        self.mFormViewButton.setChecked(self.mViewMode == QgsDualView.AttributeEditor)

        # table view
        self.mTableViewButton.setText(self.tr("Table View"))
        self.mTableViewButton.setToolTip(self.tr("Switch to table view"))
        self.mTableViewButton.setIcon(QgsApplication.getThemeIcon("/mActionOpenTable.svg"))
        self.mTableViewButton.setCheckable(True)
        self.mTableViewButton.setChecked(self.mViewMode == QgsDualView.AttributeTable)

        # button group
        self.mViewModeButtonGroup = QButtonGroup(self)
        self.mViewModeButtonGroup.addButton(self.mFormViewButton, QgsDualView.AttributeEditor)
        self.mViewModeButtonGroup.addButton(self.mTableViewButton, QgsDualView.AttributeTable)
   
        # multiedit info label
        self.mMultiEditInfoLabel.setText("")

        # add dual view(single feature content)
        self.mDualView = QgsDualView(self)
        self.mDualView.setView(self.mViewMode)
        self.mDualView.showContextMenuExternally.connect(self.showContextMenu)

        self.mStackedWidget.addWidget(self.mDualView)

        self.mViewModeButtonGroup.idClicked.connect(self.setViewMode)
        self.mToggleEditingButton.clicked.connect(self.toggleEditing)
        self.mSaveEditsButton.clicked.connect(self.saveEdits)
        self.mAddFeatureButton.clicked.connect(self.addFeature)
        self.mAddFeatureGeometryButton.clicked.connect(self.addFeatureGeometry)
        self.mDuplicateFeatureButton.clicked.connect(self.duplicateSelectedFeatures)
        self.mDeleteFeatureButton.clicked.connect(self.deleteSelectedFeatures)
        self.mLinkFeatureButton.clicked.connect(self.linkFeature)
        self.mUnlinkFeatureButton.clicked.connect(self.unlinkSelectedFeatures)
        self.mZoomToFeatureButton.clicked.connect(self.zoomToSelectedFeatures)
        self.mMultiEditTreeWidget.itemSelectionChanged.connect(self.multiEditItemSelectionChanged)

        # Set initial state for add / remove etc.buttons
        self.updateButtons()

    def config(self):
        return {}

    def setConfig(self, config):
        self.ordering_field = config['ordering_field']
        self.image_path = config['image_path']
        self.description = config['description']

    def updateButtons(self):
        toggleEditingButtonEnabled = False
        canAdd = False
        canAddGeometry = False
        canRemove = False
        canEdit = False
        canLink = False
        canUnlink = False
        spatial = False
    
        if self.relation().isValid():
            toggleEditingButtonEnabled = self.relation().referencingLayer().supportsEditing()
            canAdd = self.relation().referencingLayer().isEditable()
            canAddGeometry = self.relation().referencingLayer().isEditable()
            canRemove = self.relation().referencingLayer().isEditable()
            canEdit = self.relation().referencingLayer().isEditable()
            canLink = self.relation().referencingLayer().isEditable()
            canUnlink = self.relation().referencingLayer().isEditable()
            spatial = self.relation().referencingLayer().isSpatial()
    
        if self.nmRelation().isValid():
            toggleEditingButtonEnabled |= self.nmRelation().referencedLayer().supportsEditing()
            canAdd = self.nmRelation().referencedLayer().isEditable()
            canAddGeometry = self.nmRelation().referencedLayer().isEditable()
            canRemove = self.nmRelation().referencedLayer().isEditable()
            canEdit = self.nmRelation().referencedLayer().isEditable()
            spatial = self.nmRelation().referencedLayer().isSpatial()

        selectionNotEmpty = False
        if self.mFeatureSelectionMgr:
            selectionNotEmpty = self.mFeatureSelectionMgr.selectedFeatureCount() > 0

        if self._multiEditModeActive():
            multieditLinkedChildSelected = not self.selectedChildFeatureIds().isEmpty()

            canAddGeometry = False

            canRemove = canRemove and multieditLinkedChildSelected

            # In 1: n relations an element can be linked only to 1 feature
            canLink = canLink and self.nmRelation().isValid()
            canUnlink = canUnlink and multieditLinkedChildSelected
        else:
            canRemove = canRemove and selectionNotEmpty
            canUnlink = canUnlink and selectionNotEmpty

        self.mToggleEditingButton.setEnabled(toggleEditingButtonEnabled)
        self.mAddFeatureButton.setEnabled(canAdd)
        self.mAddFeatureGeometryButton.setEnabled(canAddGeometry)
        self.mDuplicateFeatureButton.setEnabled(canEdit and selectionNotEmpty)
        self.mLinkFeatureButton.setEnabled(canLink)
        self.mDeleteFeatureButton.setEnabled(canRemove)
        self.mUnlinkFeatureButton.setEnabled(canUnlink)
        self.mZoomToFeatureButton.setEnabled(selectionNotEmpty)
        self.mToggleEditingButton.setChecked(canEdit)
        self.mSaveEditsButton.setEnabled(canEdit or canLink or canUnlink)
    
        self.mToggleEditingButton.setVisible(not self._layerInSameTransactionGroup)
    
        self.mLinkFeatureButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.Link))
        self.mUnlinkFeatureButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.Unlink))
        self.mSaveEditsButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.SaveChildEdits) and not self._layerInSameTransactionGroup)
        self.mAddFeatureButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.AddChildFeature))
        self.mAddFeatureGeometryButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.AddChildFeature) and self.mEditorContext.mapCanvas() and self.mEditorContext.cadDockWidget() and spatial)
        self.mDuplicateFeatureButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.DuplicateChildFeature))
        self.mDeleteFeatureButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.DeleteChildFeature))
        self.mZoomToFeatureButton.setVisible(self.mButtonsVisibility.testFlag(QgsRelationEditorWidget.Button.ZoomToChildFeature ) and self.mEditorContext.mapCanvas() and spatial)

    def updateUi(self):
        self._updateUiTimer.start(200)

    def updateUiTimeout(self):
        if Debug:
            QgsMessageLog.logMessage("updateUiTimeout()")

        # we defer attribute form creation on the first valid feature passed on
        if self.attribute_form:
            self.attribute_form.deleteLater()

    def parentFormValueChanged(self, attribute, newValue):
        if self.attribute_form:
            self.attribute_form.parentFormValueChanged(attribute, newValue)

    def addFeatureGeometry(self):
        if self._multiEditModeActive():
            QgsLogger.warning(self.tr("Adding a geometry feature is not supported in multiple edit mode"))
            return

        layer = QgsVectorLayer()
        if (self.nmRelation().isValid()):
            layer = self.nmRelation().referencedLayer()
        else:
            layer = self.relation().referencingLayer()

        self.mMapToolDigitize.setLayer(layer)

        # window is always on top, so we hide it to digitize without seeing it
        self.window().setVisible(False)
        self.setMapTool(self.mMapToolDigitize)

        self.mMapToolDigitize.digitizingCompleted.connect(self.onDigitizingCompleted)
        self.mEditorContext.mapCanvas().keyPressed.connect(self.onKeyPressed)

        if self.mEditorContext.mainMessageBar():
            displayString = QgsVectorLayerUtils.getFeatureDisplayString(layer, self.mFeatureList.first())
            title = self.tr("Create child feature for parent %1 \"%2\"").arg(self.relation().referencedLayer().name(), displayString)
            msg = self.tr("Digitize the geometry for the new feature on layer %1. Press &ltESC&gt to cancel.").arg(layer.name() )
            self.mMessageBarItem = QgsMessageBar.createMessage(title, msg, self)
            self.mEditorContext.mainMessageBar().pushItem(self.mMessageBarItem)

    def deleteSelectedFeatures(self):
        self.deleteFeatures(self.selectedChildFeatureIds())

    def duplicateFeatures(self, fids):
        layer = self.relation().referencingLayer()

        for feature in layer.getFeatures(QgsFeatureRequest().setFilterFids(fids)):
            QgsVectorLayerUtils.duplicateFeature(layer, feature, QgsProject.instance(), QgsVectorLayerUtils.QgsDuplicateFeatureContext)

        self.relatedFeaturesChanged()

    def duplicateSelectedFeatures(self):
        self.duplicateFeatures(self.mFeatureSelectionMgr.selectedFeatureIds())

    def multiEditItemSelectionChanged(self):
        selectedItems = self.mMultiEditTreeWidget.selectedItems()

        # Select all items pointing to the same feature
        # but only if we are not deselecting.
        if selectedItems.size() == 1 and self.mMultiEditPreviousSelectedItems.size() <= 1:
            selectedItem = selectedItems[0]
            if selectedItem.data(0, self.MultiEditTreeWidgetRole.FeatureType).toInt() == self.MultiEditFeatureType.Child:
                self.mMultiEditTreeWidget.blockSignals(True)

                featureIdSelectedItem = selectedItem.data(0, self.MultiEditTreeWidgetRole.FeatureId).toInt()

                for i in range(self.mMultiEditTreeWidget.childCount()):
                    treeWidgetItem = self.mMultiEditTreeWidget.child(i)

                    if treeWidgetItem.data( 0, self.MultiEditTreeWidgetRole.FeatureType).toInt() != self.MultiEditFeatureType.Child:
                        continue

                    featureIdCurrentItem = treeWidgetItem.data(0, self.MultiEditTreeWidgetRole.FeatureId).toInt()
                    if self.nmRelation().isValid():
                        if featureIdSelectedItem == featureIdCurrentItem:
                            treeWidgetItem.setSelected(True)
                    else:
                        if featureIdSelectedItem not in self.mMultiEdit1NJustAddedIds:
                            break

                        if featureIdCurrentItem not in self.mMultiEdit1NJustAddedIds:
                            treeWidgetItem.setSelected(True)

                self.mMultiEditTreeWidget.blockSignals(False)

        self.mMultiEditPreviousSelectedItems = selectedItems
        self.updateButtons()

    def selectedChildFeatureIds(self):
        if self._multiEditModeActive():
            featureIds = set()
            for treeWidgetItem in self.mMultiEditTreeWidget.selectedItems():
                if treeWidgetItem.data(0, self.MultiEditTreeWidgetRole.FeatureType).toInt() != self.MultiEditFeatureType.Child:
                    continue

                featureIds.insert(treeWidgetItem.data(0, self.MultiEditTreeWidgetRole.FeatureId).toLongLong())
            return featureIds
        else:
            return self.mFeatureSelectionMgr.selectedFeatureIds()

    def setViewMode(self, mode: QgsDualView.ViewMode):
        self.mDualView.setView(mode)
        self.mViewMode = mode

    def showContextMenu(self, menu, fid):
        if not self.relation().referencingLayer().isEditable():
            return

        qAction = menu.addAction(QgsApplication.getThemeIcon("/mActionDeleteSelected.svg"), self.tr("Delete Feature"))
        qAction.triggered.connect(lambda state, fid=fid: self.deleteFeature(fid))

        qAction = menu.addAction(QgsApplication.getThemeIcon("/mActionUnlink.svg"), self.tr("Unlink Feature"))
        qAction.triggered.connect(lambda state, fid=fid: self.unlinkFeature(fid))

    def unlinkSelectedFeatures(self):
        self.unlinkFeatures(self.selectedChildFeatureIds())

    def zoomToSelectedFeatures(self):
        if self.mEditorContext.mapCanvas():
            layer = self.relation().referencingLayer()
            if self.nmRelation().isValid():
                layer = self.nmRelation().referencedLayer()

            self.mEditorContext.mapCanvas().zoomToFeatureIds(layer, self.mFeatureSelectionMgr.selectedFeatureIds())

    def afterSetRelations(self):
        self._nmRelation = QgsProject.instance().relationManager().relation(str(self.nmRelationId()))

        self._checkTransactionGroup()

        if self.relation().isValid():
            self.relation().referencingLayer().editingStopped.connect(self.updateButtons)
            self.relation().referencingLayer().editingStarted.connect(self.updateButtons)

        if self.nmRelation().isValid():
            self.nmRelation().referencedLayer().editingStarted.connect(self.updateButtons)
            self.nmRelation().referencedLayer().editingStopped.connect(self.updateButtons)

        self.updateButtons()

    def _checkTransactionGroup(self):

        self._layerInSameTransactionGroup = False
        connectionString = PluginHelper.connectionString(self.relation().referencedLayer().source())
        transactionGroup = QgsProject.instance().transactionGroup(self.relation().referencedLayer().providerType(),
                                                                  connectionString)

        if transactionGroup is None:
            return

        if self.nmRelation().isValid():
            if (self.relation().referencedLayer() in transactionGroup.layers() and
               self.relation().referencingLayer() in transactionGroup.layers() and
               self.nmRelation().referencedLayer() in transactionGroup.layers()):
                self._layerInSameTransactionGroup = True
        else:
            if (self.relation().referencedLayer() in transactionGroup.layers() and
               self.relation().referencingLayer() in transactionGroup.layers()):
                self._layerInSameTransactionGroup = True

    def _multiEditModeActive(self):
        # multiEditModeActive available since QGIS 3.24
        if Qgis.QGIS_VERSION_INT < 32400:
            return False
        else:
            return self.multiEditModeActive()
