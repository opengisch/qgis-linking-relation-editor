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
from enum import IntEnum
from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    QT_VERSION_STR
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QSplitter
)
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeatureRequest,
    QgsGeometry,
    QgsLogger,
    QgsMessageLog,
    QgsProject,
    QgsRelation,
    QgsVectorLayer,
    QgsVectorLayerUtils,
    QgsWkbTypes,
    metaEnumFromValue
)
from qgis.gui import (
    QgsAbstractRelationEditorWidget,
    QgsDualView,
    QgsMessageBar,
    QgsRelationEditorWidget
)
from linking_relation_editor.core.plugin_helper import PluginHelper
from linking_relation_editor.gui.filtered_selection_manager import FilteredSelectionManager
from linking_relation_editor.gui.linking_child_manager_dialog import LinkingChildManagerDialog

WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__),
                                      '../ui/linking_relation_editor_widget.ui'))

Debug = True


class LinkingRelationEditorWidget(QgsAbstractRelationEditorWidget, WidgetUi):

    class MultiEditFeatureType(IntEnum):
        Parent = 1,
        Child = 2

    class MultiEditTreeWidgetRole(IntEnum):
        FeatureType = Qt.UserRole + 1,
        FeatureId = Qt.UserRole + 2

    def __init__(self, config, parent):
        super().__init__(config, parent)

        self.mViewMode = QgsDualView.AttributeEditor
        self.mFeatureSelectionMgr = None

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
        self.mDualViewInitialized = False
        self.mDualView = QgsDualView(self)
        self.mDualView.setView(self.mViewMode)
        self.mDualView.showContextMenuExternally.connect(self.showContextMenu)

        self.mStackedWidget.addWidget(self.mDualView)

        if QT_VERSION_STR < '5.15.0':
            self.mViewModeButtonGroup.buttonClicked.connect(self.setViewModeButton)
        else:
            self.mViewModeButtonGroup.idClicked.connect(self.setViewMode)
        self.mToggleEditingButton.clicked.connect(self.toggleEditing)
        self.mSaveEditsButton.clicked.connect(self.saveEdits)
        self.mAddFeatureButton.clicked.connect(self.addFeature)
        self.mAddFeatureGeometryButton.clicked.connect(self.addFeatureGeometry)
        self.mDuplicateFeatureButton.clicked.connect(self.duplicateSelectedFeatures)
        self.mDeleteFeatureButton.clicked.connect(self.deleteSelectedFeatures)
        self.mLinkFeatureButton.clicked.connect(self._execLinkFeatureDialog)
        self.mUnlinkFeatureButton.clicked.connect(self.unlinkSelectedFeatures)
        self.mZoomToFeatureButton.clicked.connect(self.zoomToSelectedFeatures)
        self.mMultiEditTreeWidget.itemSelectionChanged.connect(self.multiEditItemSelectionChanged)

        self.mOneToOne = False

        # Set initial state for add / remove etc.buttons
        self.updateButtons()

    def config(self):
        return {"buttons": metaEnumFromValue(QgsRelationEditorWidget.Button.AllButtons).valueToKeys(self.visibleButtons()),
                "show_first_feature": self.mShowFirstFeature,
                "one_to_one": self.mOneToOne}

    def setConfig(self, config):
        metaEnumButtons = metaEnumFromValue(QgsRelationEditorWidget.Button.AllButtons)
        (self.mButtonsVisibility, ok) = metaEnumButtons.keysToValue(config.get("buttons",
                                                                               metaEnumButtons.valueToKeys(QgsRelationEditorWidget.Button.AllButtons)))
        self.mShowFirstFeature = config.get("show_first_feature", True)
        self.mOneToOne = config.get("one_to_one")
        self.updateButtons()

    def initDualView(self, layer, request):
        if self._multiEditModeActive():
            QgsLogger.warning(self.tr("Dual view should not be used in multiple edit mode"))
            return

        ctx = self.editorContext()
        ctx.setParentFormFeature(self.feature())

        # showFirstFeature available since QGIS 3.24
        if Qgis.QGIS_VERSION_INT < 32400:
            self.mDualView.init(layer, self.editorContext().mapCanvas(), request, ctx, True)
        else:
            showFirstFeature = self.mShowFirstFeature

            # For one to one always show the first feature
            if self.mOneToOne:
                showFirstFeature = True

            self.mDualView.init(layer, self.editorContext().mapCanvas(), request, ctx, True, showFirstFeature)

        self.mFeatureSelectionMgr = FilteredSelectionManager(layer, request, self.mDualView)
        self.mDualView.setFeatureSelectionManager(self.mFeatureSelectionMgr)
        self.mDualViewInitialized = True

        self.mFeatureSelectionMgr.selectionChanged.connect(self.updateButtons)

        icon = QIcon()
        text = str()
        if layer.geometryType() == QgsWkbTypes.PointGeometry:
            icon = QgsApplication.getThemeIcon("/mActionCapturePoint.svg")
            text = self.tr("Add Point Child Feature")
        elif layer.geometryType() == QgsWkbTypes.LineGeometry:
            icon = QgsApplication.getThemeIcon("/mActionCaptureLine.svg")
            text = self.tr("Add Line Child Feature")
        elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            icon = QgsApplication.getThemeIcon("/mActionCapturePolygon.svg")
            text = self.tr("Add Polygon Child Feature")

        self.mAddFeatureGeometryButton.setIcon(icon)
        self.mAddFeatureGeometryButton.setText(text)
        self.mAddFeatureGeometryButton.setToolTip(text)

        self.updateButtons()

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

        if self.mDualViewInitialized and self.mOneToOne:
            featureLinked = self.mDualView.featureCount() > 0
            canAdd &= not featureLinked
            canAddGeometry &= not featureLinked
            canLink &= not featureLinked

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
    
        self.mLinkFeatureButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.Link))
        self.mUnlinkFeatureButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.Unlink))
        self.mSaveEditsButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.SaveChildEdits) and not self._layerInSameTransactionGroup)
        self.mAddFeatureButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.AddChildFeature) and not spatial)
        self.mAddFeatureGeometryButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.AddChildFeature) and bool(self.editorContext().mapCanvas()) and bool(self.editorContext().cadDockWidget()) and spatial)
        self.mDuplicateFeatureButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.DuplicateChildFeature) and not self.mOneToOne)
        self.mDeleteFeatureButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.DeleteChildFeature))
        self.mZoomToFeatureButton.setVisible(bool(self.mButtonsVisibility & QgsRelationEditorWidget.Button.ZoomToChildFeature) and bool(self.editorContext().mapCanvas()) and spatial)

        splitter_name = "mAttributeEditorViewSplitter"
        splitter_found = False
        splitters = self.mDualView.findChildren(QSplitter)
        for splitter in splitters:
            if splitter.objectName() == splitter_name:
                if self.mOneToOne:
                    splitter.setSizes([0, 1])
                else:
                    splitter.setSizes([1, 1])
                break

        if not splitter_found:
            QgsLogger.warning(self.tr("QSplitter with object name '{}' not found".format(splitter_name)))

    def updateUi(self):
        self._updateUiTimer.start(200)

    def updateUiTimeout(self):
        if Debug:
            QgsMessageLog.logMessage("updateUiTimeout()")

        # we defer attribute form creation on the first valid feature passed on
        #if self.attribute_form:
        #    self.attribute_form.deleteLater()

        if not self.relation().isValid() or not self.feature().isValid():
            return

        if not self.isVisible():
            return

        if self._multiEditModeActive():
            self.updateUiMultiEdit()
        else:
            self.updateUiSingleEdit()

    def parentFormValueChanged(self, attribute, newValue):
        if Debug:
            QgsMessageLog.logMessage("parentFormValueChanged()")
        pass
        #if self.attribute_form:
        #    self.attribute_form.parentFormValueChanged(attribute, newValue)

    def updateUiSingleEdit(self):

        self.mFormViewButton.setVisible(not self.mOneToOne)
        self.mTableViewButton.setVisible(not self.mOneToOne)
        self.mMultiEditInfoLabel.setVisible(False)

        self.mStackedWidget.setCurrentWidget(self.mDualView)

        request = self.relation().getRelatedFeaturesRequest(self.feature())
        if self.nmRelation().isValid():
            filters = []
            for feature in self.relation().referencingLayer().getFeatures(request):
                referenced_request = self.nmRelation().getReferencedFeatureRequest(feature)
                filter = referenced_request.filterExpression().expression()
                filters.append('('+filter+')')

            nmRequest = QgsFeatureRequest()
            nmRequest.setFilterExpression(" OR ".join(filters))

            self.initDualView(self.nmRelation().referencedLayer(), nmRequest)

        elif self.relation().referencingLayer():
            self.initDualView(self.relation().referencingLayer(), request)

        if self.mOneToOne:
            self.setViewMode(QgsDualView.AttributeEditor)

            if self.nmRelation().isValid():
                self.nmRelation().referencedLayer().selectByIds(self.mDualView.filteredFeatures())
            else:
                self.relation().referencingLayer().selectByIds(self.mDualView.filteredFeatures())


    def updateUiMultiEdit(self):
        self.mFormViewButton.setVisible(False)
        self.mTableViewButton.setVisible(False)
        self.mMultiEditInfoLabel.setVisible(True)
        self.mStackedWidget.setCurrentWidget(self.mMultiEditStackedWidgetPage)
        parentTreeWidgetItems = []
        featureIdsMixedValues = []
        multimapChildFeatures = dict()
        self.mMultiEditTreeWidget.clear()
        for featureParent in self.mFeatureList:
            treeWidgetItem = self.createMultiEditTreeWidgetItem(featureParent, self.relation().referencedLayer(), self.MultiEditFeatureType.Parent)
            # Parent feature items are not selectable
            treeWidgetItem.setFlags(Qt.ItemIsEnabled)
            parentTreeWidgetItems.append(treeWidgetItem)
            # Get child features
            request = self.relation().getRelatedFeaturesRequest(featureParent)
            for featureChild in self.relation().referencingLayer().getFeatures(request):
                if self.nmRelation().isValid():
                    requestFinalChild = self.nmRelation().getReferencedFeatureRequest(featureChild)
                    for featureChildChild in self.nmRelation().referencedLayer().getFeatures(requestFinalChild):
                        treeWidgetItemChild = self.createMultiEditTreeWidgetItem(featureChildChild, self.nmRelation().referencedLayer(), self.MultiEditFeatureType.Child)
                        treeWidgetItem.addChild(treeWidgetItemChild)
                        featureIdsMixedValues.insert(featureChildChild.id())

                        if treeWidgetItem in multimapChildFeatures:
                            multimapChildFeatures[treeWidgetItem].append(featureChildChild.id())
                        else:
                            multimapChildFeatures[treeWidgetItem] = [featureChildChild.id()]

                else:
                    treeWidgetItemChild = self.createMultiEditTreeWidgetItem(featureChild, self.relation().referencingLayer(), MultiEditFeatureType.Child)
                    treeWidgetItem.addChild(treeWidgetItemChild)
                    featureIdsMixedValues.insert(featureChild.id())

            self.mMultiEditTreeWidget.addTopLevelItem(treeWidgetItem)
            treeWidgetItem.setExpanded(True)

        # Set mixed values indicator (Green or Orange)
        #
        # Green:
        #     n:m and 1:n: 0 child features available
        #     n:m with no mixed values
        # Orange:
        #     n:m with mixed values
        #     1:n always, including when we pseudo know that feature are related (just added feature)
        #
        # See https://github.com/qgis/QGIS/pull/45703
        #
        if self.nmRelation().isValid():
            for featureIdMixedValue in featureIdsMixedValues[:]:
                mixedValues = True
                for parentTreeWidgetItem in parentTreeWidgetItems:
                    if featureIdMixedValue in multimapChildFeatures[parentTreeWidgetItem]:
                        mixedValues = True
                        break

                if not mixedValues:
                    iterator = featureIdsMixedValues.remove(featureIdMixedValue)
                    continue

        # Set multiedit info label
        if featureIdsMixedValues.isEmpty():
            icon = QgsApplication.getThemeIcon("/multieditSameValues.svg")
            self.mMultiEditInfoLabel.setPixmap(icon.pixmap(self.mMultiEditInfoLabel.height(),
                                               self.mMultiEditInfoLabel.height()))
            self.mMultiEditInfoLabel.setToolTip(self.tr("All features in selection have equal relations"))

        else:
            icon = QgsApplication.getThemeIcon("/multieditMixedValues.svg")
            self.mMultiEditInfoLabel.setPixmap(icon.pixmap(self.mMultiEditInfoLabel.height(),
                                               self.mMultiEditInfoLabel.height()))
            self.mMultiEditInfoLabel.setToolTip(self.tr("Some features in selection have different relations"))
            # Set italic font for mixed values
            fontItalic = self.mMultiEditTreeWidget.font()
            fontItalic.setItalic(True)
            for parentTreeWidgetItem in parentTreeWidgetItems:
                for childIndex in range(parentTreeWidgetItem.childCount()):
                    childItem = parentTreeWidgetItem.child(childIndex)
                    featureIdCurrentItem = childItem.data(0, self.MultiEditTreeWidgetRole.FeatureId)
                    if featureIdCurrentItem in featureIdsMixedValues:
                        childItem.setFont(0, fontItalic)

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
        self.editorContext().mapCanvas().keyPressed.connect(self.onKeyPressed)

        if self.editorContext().mainMessageBar():
            displayString = QgsVectorLayerUtils.getFeatureDisplayString(layer, self.mFeatureList.first())
            title = self.tr("Create child feature for parent {0} \"{1}\"").format(self.relation().referencedLayer().name(), displayString)
            msg = self.tr("Digitize the geometry for the new feature on layer {0}. Press &ltESC&gt to cancel.").format(layer.name())
            self.mMessageBarItem = QgsMessageBar.createMessage(title, msg, self)
            self.editorContext().mainMessageBar().pushItem(self.mMessageBarItem)

    def deleteSelectedFeatures(self):
        self.deleteFeatures(self.selectedChildFeatureIds())

    def duplicateFeatures(self, fids):
        layer = self.relation().referencingLayer()

        for feature in layer.getFeatures(QgsFeatureRequest().setFilterFids(fids)):
            QgsVectorLayerUtils.duplicateFeature(layer, feature, QgsProject.instance(), QgsVectorLayerUtils.QgsDuplicateFeatureContext)

        self.relatedFeaturesChanged()

    def duplicateSelectedFeatures(self):
        self.duplicateFeatures(self.mFeatureSelectionMgr.selectedFeatureIds())

    def _execLinkFeatureDialog(self):

        layer = None

        if self.nmRelation().isValid():
            layer = self.nmRelation().referencedLayer()
        else:
            if self._multiEditModeActive():
                QgsLogger.warning(self.tr("For 1:n relations is not possible to link to multiple features"))
                return

            layer = self.relation().referencingLayer()

        relationEditorLinkChildManagerDialog = LinkingChildManagerDialog(layer,
                                                                         self.relation().referencedLayer(),
                                                                         self.feature(),
                                                                         self.relation(),
                                                                         self.nmRelation(),
                                                                         self.editorContext(),
                                                                         self)
        relationEditorLinkChildManagerDialog.accepted.connect(self._relationEditorLinkChildManagerDialogAccepted)
        relationEditorLinkChildManagerDialog.show()

    def _linkFeatures(self,
                      featureIds):

        if len(featureIds) == 0:
            return

        if self.nmRelation().isValid():
            # only normal relations support m:n relation
            assert(self.nmRelation().type() == QgsRelation.Normal)

            # Fields of the linking table
            fields = self.relation().referencingLayer().fields()

            linkAttributes = dict()

            if self.relation().type() == QgsRelation.Generated:
                polyRel = self.relation().polymorphicRelation()
                assert(polyRel.isValid())

                linkAttributes.insert(fields.indexFromName(polyRel.referencedLayerField()),
                                      polyRel.layerRepresentation(self.relation().referencedLayer()))

            linkFeatureDataList = []
            for relatedFeature in self.nmRelation().referencedLayer().getFeatures(QgsFeatureRequest().setFilterFids(featureIds)
                                                                                                     .setSubsetOfAttributes(self.nmRelation().referencedFields())):
                for editFeature in self._featureList():
                    for referencingField, referencedField in self.relation().fieldPairs().items():
                        index = fields.indexOf(referencingField)
                        linkAttributes[index] = editFeature.attribute(referencedField)

                    for referencingField, referencedField in self.nmRelation().fieldPairs().items():
                        index = fields.indexOf(referencingField)
                        linkAttributes[index] = relatedFeature.attribute(referencedField)

                    linkFeatureDataList.append(QgsVectorLayerUtils.QgsFeatureData(QgsGeometry(), linkAttributes))

            # Expression context for the linking table
            context = self.relation().referencingLayer().createExpressionContext()

            linkFeaturesList = QgsVectorLayerUtils.createFeatures(self.relation().referencingLayer(),
                                                                  linkFeatureDataList,
                                                                  context)

            self.relation().referencingLayer().addFeatures(linkFeaturesList)
            ids = []
            for f in linkFeaturesList:
                ids.append(f.id())
            self.relation().referencingLayer().selectByIds(ids)
        else:
            if self._multiEditModeActive():
                QgsLogger.warning(self.tr("For 1:n relations is not possible to link to multiple features"))
                return

            keys = dict()
            for referencingField, referencedField in self.relation().fieldPairs().items():
                idx = self.relation().referencingLayer().fields().lookupField(referencingField)
                val = self.feature().attribute(referencedField)
                keys[idx] = val

            for fid in featureIds:
                referencingLayer = self.relation().referencingLayer()
                if self.relation().type() == QgsRelation.Generated:
                    polyRel = self.relation().polymorphicRelation()

                    assert(polyRel.isValid())

                    self.relation().referencingLayer().changeAttributeValue(fid,
                                                                            referencingLayer.fields().indexFromName(polyRel.referencedLayerField()),
                                                                            polyRel.layerRepresentation(self.relation().referencedLayer()))

                for key, value in keys.items():
                    referencingLayer.changeAttributeValue(fid,
                                                          key,
                                                          value)

        self.updateUi()

        # relatedFeaturesChanged available since QGIS 3.24
        if Qgis.QGIS_VERSION_INT >= 32400:
            self.relatedFeaturesChanged.emit()

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

                    if treeWidgetItem.data(0, self.MultiEditTreeWidgetRole.FeatureType).toInt() != self.MultiEditFeatureType.Child:
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

    def setViewModeButton(self, button):
        mode = QgsDualView.AttributeEditor
        if button == self.mTableViewButton:
            mode = QgsDualView.AttributeTable
        
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
        if self.editorContext().mapCanvas():
            layer = self.relation().referencingLayer()
            if self.nmRelation().isValid():
                layer = self.nmRelation().referencedLayer()

            self.editorContext().mapCanvas().zoomToFeatureIds(layer, self.mFeatureSelectionMgr.selectedFeatureIds())

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

    def _featureList(self):
        # featureList available since QGIS 3.24
        if Qgis.QGIS_VERSION_INT < 32400:
            return [self.feature()]
        else:
            return self.features()

    def _relationEditorLinkChildManagerDialogAccepted(self):
        relationEditorLinkChildManagerDialog = self.sender()
        self.unlinkFeatures(relationEditorLinkChildManagerDialog.get_feature_ids_to_unlink())
        self._linkFeatures(relationEditorLinkChildManagerDialog.get_feature_ids_to_link())
        relationEditorLinkChildManagerDialog.deleteLater()
