# -- coding: utf-8 --

import os
from qgis.PyQt.QtCore import (
    Qt,
    QTimer
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QMenu,
    QToolButton,
    QWidget
)
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    QgsApplication,
    QgsDistanceArea,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsProject,
    QgsVectorLayer
)
from qgis.gui import (
    QgsAttributeEditorContext,
    QgsAttributeForm,
    QgsAttributeTableFilterModel,
    QgsDualView,
    QgsExpressionBuilderDialog,
    QgsGui,
    QgsMessageBar
)
from enhanced_relation_editor_widget.core.features_model_filter import FeaturesModelFilter


WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__),
                                      '../ui/feature_filter_widget.ui'))


class FeatureFilterWidget(QWidget,
                          WidgetUi):

    def __init__(self,
                 parent: QWidget):
        super().__init__(parent)

        # Ui setup
        self.setupUi(self)

        self.mFilterQueryTimer = QTimer()
        self.mCurrentSearchWidgetWrapper = None
        self._features_model_filter = None
        self.mLayer = None
        self.mEditorContext = None
        self.mMessageBar = None

        # Initialize filter gui elements
        self.mFilterColumnsMenu = QMenu(self)
        self.mActionFilterColumnsMenu.setMenu(self.mFilterColumnsMenu)
        self.mStoredFilterExpressionMenu = QMenu(self)
        self.mActionStoredFilterExpressions.setMenu(self.mStoredFilterExpressionMenu)

        # Set filter icon in a couple of places
        self.mActionEditStoredFilterExpression.setIcon(QgsApplication.getThemeIcon("/mActionHandleStoreFilterExpressionChecked.svg"))
        self.mActionSaveAsStoredFilterExpression.setIcon(QgsApplication.getThemeIcon("/mActionHandleStoreFilterExpressionUnchecked.svg"))
        self.mActionHandleStoreFilterExpression.setIcon(QgsApplication.getThemeIcon("/mActionHandleStoreFilterExpressionUnchecked.svg"))
        self.mActionStoredFilterExpressions.setIcon(QgsApplication.getThemeIcon("/mActionHandleStoreFilterExpressionChecked.svg"))
        self.mActionShowAllFilter.setIcon(QgsApplication.getThemeIcon("/mActionOpenTable.svg"))
        self.mActionAdvancedFilter.setIcon(QgsApplication.getThemeIcon("/mActionFilter2.svg"))
        self.mActionSelectedFilter.setIcon(QgsApplication.getThemeIcon("/mActionOpenTableSelected.svg"))
        self.mActionVisibleFilter.setIcon(QgsApplication.getThemeIcon("/mActionOpenTableVisible.svg"))
        self.mActionEditedFilter.setIcon(QgsApplication.getThemeIcon("/mActionOpenTableEdited.svg"))

        # Set button to store or delete stored filter expressions
        self.mStoreFilterExpressionButton.setDefaultAction(self.mActionHandleStoreFilterExpression)
        self.mActionSaveAsStoredFilterExpression.triggered.connect(self.saveAsStoredFilterExpression)
        self.mActionEditStoredFilterExpression.triggered.connect(self.editStoredFilterExpression)
        self.mActionHandleStoreFilterExpression.triggered.connect(self.handleStoreFilterExpression)
        self.mApplyFilterButton.setDefaultAction(self.mActionApplyFilter)

        # Connect filter signals
        self.mActionAdvancedFilter.triggered.connect(self.filterExpressionBuilder)
        self.mActionShowAllFilter.triggered.connect(self.filterShowAll)
        self.mActionSelectedFilter.triggered.connect(self.filterSelected)
        self.mActionVisibleFilter.triggered.connect(self.filterVisible)
        self.mActionEditedFilter.triggered.connect(self.filterEdited)
        self.mFilterQuery.returnPressed.connect(self.filterQueryAccepted)
        self.mActionApplyFilter.triggered.connect(self.filterQueryAccepted)
        self.mFilterQuery.textChanged.connect(self.onFilterQueryTextChanged)

    def init(self,
             layer: QgsVectorLayer,
             context: QgsAttributeEditorContext,
             features_model_filter: FeaturesModelFilter,
             messageBar: QgsMessageBar,
             messagebarTimeout: int):
        self._features_model_filter = features_model_filter
        self.mLayer = layer
        self.mEditorContext = context
        self.mMessageBar = messageBar

        self.mLayer.attributeAdded.connect(self.columnBoxInit)
        self.mLayer.attributeDeleted.connect(self.columnBoxInit)

        # Set delay on entering text
        self.mFilterQueryTimer.setSingleShot(True)
        self.mFilterQueryTimer.timeout.connect(self.updateCurrentStoredFilterExpression)

        self.columnBoxInit()
        self.storedFilterExpressionBoxInit()
        self.storeExpressionButtonInit()

    def filterShowAll(self):
        self.mFilterButton.setDefaultAction(self.mActionShowAllFilter)
        self.mFilterButton.setPopupMode(QToolButton.InstantPopup)
        self.mFilterQuery.setVisible(False)
        self.mFilterQuery.setText(str())
        if self.mCurrentSearchWidgetWrapper:
            self.mCurrentSearchWidgetWrapper.widget().setVisible(False)

        self.mApplyFilterButton.setVisible(False)
        self.mStoreFilterExpressionButton.setVisible(False)
        self._features_model_filter.set_legacy_filter(FeaturesModelFilter.LegacyFilter.ShowAll)

    def filterSelected(self):
        self.mFilterButton.setDefaultAction(self.mActionSelectedFilter)
        self.mFilterButton.setPopupMode(QToolButton.InstantPopup)
        self.mFilterQuery.setVisible(False)
        self.mApplyFilterButton.setVisible(False)
        self.mStoreFilterExpressionButton.setVisible(False)
        self._features_model_filter.set_legacy_filter(FeaturesModelFilter.LegacyFilter.ShowSelected)

    def filterVisible(self):
        if not self.mLayer.isSpatial():
            filterShowAll()
            return

        self.mFilterButton.setDefaultAction(self.mActionVisibleFilter)
        self.mFilterButton.setPopupMode(QToolButton.InstantPopup)
        self.mFilterQuery.setVisible(False)
        self.mApplyFilterButton.setVisible(False)
        self.mStoreFilterExpressionButton.setVisible(False)
        self._features_model_filter.set_legacy_filter(FeaturesModelFilter.LegacyFilter.ShowVisible)

    def filterEdited(self):
        self.mFilterButton.setDefaultAction(self.mActionEditedFilter)
        self.mFilterButton.setPopupMode(QToolButton.InstantPopup)
        self.mFilterQuery.setVisible(False)
        self.mApplyFilterButton.setVisible(False)
        self.mStoreFilterExpressionButton.setVisible(False)
        self._features_model_filter.set_legacy_filter(FeaturesModelFilter.LegacyFilter.ShowEdited)

    def filterQueryAccepted(self):
        if ((self.mFilterQuery.isVisible() and len(self.mFilterQuery.text()) == 0) or
            (self.mCurrentSearchWidgetWrapper and self.mCurrentSearchWidgetWrapper.widget().isVisible()
             and self.mCurrentSearchWidgetWrapper.expression().isEmpty())):
            self.filterShowAll()
            return

        self.filterQueryChanged(self.mFilterQuery.text())

    def filterQueryChanged(self,
                           query: str):
        if self.mFilterButton.defaultAction() == self.mActionAdvancedFilter:
            queryString = query

        elif self.mCurrentSearchWidgetWrapper:
            queryString = self.mCurrentSearchWidgetWrapper.expression()

        self.setFilterExpression(queryString,
                                 QgsAttributeForm.ReplaceFilter,
                                 False)

    def columnBoxInit(self):
        for action in self.mFilterColumnsMenu.actions()[:]:
            self.mFilterColumnsMenu.removeAction(action)
            self.mFilterButton.removeAction(action)
            action.deleteLater()

        self.mFilterButton.addAction(self.mActionShowAllFilter)
        self.mFilterButton.addAction(self.mActionSelectedFilter)
        if self.mLayer.isSpatial():
            self.mFilterButton.addAction(self.mActionVisibleFilter)

        self.mFilterButton.addAction(self.mActionEditedFilter)
        self.mFilterButton.addAction(self.mActionFilterColumnsMenu)
        self.mFilterButton.addAction(self.mActionAdvancedFilter)
        self.mFilterButton.addAction(self.mActionStoredFilterExpressions)

        for field in self.mLayer.fields().toList():
            idx = self.mLayer.fields().lookupField(field.name())
            if idx < 0:
                continue

            if QgsGui.editorWidgetRegistry().findBest(self.mLayer, field.name()).type() != "Hidden":
                icon = self.mLayer.fields().iconForField(idx)
                alias = self.mLayer.attributeDisplayName(idx)

                # Generate action for the filter popup button
                filterAction = QAction(icon, alias, self.mFilterButton)
                filterAction.setData(field.name())

                filterAction.triggered.connect(self._filter_action_triggered)
                self.mFilterColumnsMenu.addAction(filterAction)

    def _filter_action_triggered(self):
        self.filterColumnChanged(self.sender())

    def handleStoreFilterExpression(self):
        if not self.mActionHandleStoreFilterExpression.isChecked():
            self.mLayer.storedExpressionManager().removeStoredExpression(self.mActionHandleStoreFilterExpression.data())

        else:
            self.mLayer.storedExpressionManager().addStoredExpression(self.mFilterQuery.text(), self.mFilterQuery.text())

        self.updateCurrentStoredFilterExpression()
        self.storedFilterExpressionBoxInit()

    def storedFilterExpressionBoxInit(self):
        for action in self.mStoredFilterExpressionMenu.actions()[:]:
            self.mStoredFilterExpressionMenu.removeAction(action)
            action.deleteLater()

        for storedExpression in self.mLayer.storedExpressionManager().storedExpressions():
            storedExpressionAction = QAction(storedExpression.name, self.mFilterButton)
            storedExpressionAction.triggered.connect(lambda checked, storedExpression=storedExpression:
                                                     self.setFilterExpression(storedExpression.expression,
                                                                              QgsAttributeForm.ReplaceFilter,
                                                                              True))
            self.mStoredFilterExpressionMenu.addAction(storedExpressionAction)

    def storeExpressionButtonInit(self):
        if self.mActionHandleStoreFilterExpression.isChecked():
            self.mActionHandleStoreFilterExpression.setToolTip(self.tr("Delete stored expression"))
            self.mActionHandleStoreFilterExpression.setText(self.tr("Delete Stored Expression"))
            self.mActionHandleStoreFilterExpression.setIcon(QgsApplication.getThemeIcon("mActionHandleStoreFilterExpressionChecked.svg"))
            self.mStoreFilterExpressionButton.removeAction(self.mActionSaveAsStoredFilterExpression)
            self.mStoreFilterExpressionButton.addAction(self.mActionEditStoredFilterExpression)

        else:
            self.mActionHandleStoreFilterExpression.setToolTip(self.tr("Save expression with the text as name"))
            self.mActionHandleStoreFilterExpression.setText(self.tr("Save Expression"))
            self.mActionHandleStoreFilterExpression.setIcon(QgsApplication.getThemeIcon("mActionHandleStoreFilterExpressionUnchecked.svg"))
            self.mStoreFilterExpressionButton.addAction(self.mActionSaveAsStoredFilterExpression)
            self.mStoreFilterExpressionButton.removeAction(self.mActionEditStoredFilterExpression)

    def filterColumnChanged(self,
                            filterAction: QAction):
        self.mFilterButton.setDefaultAction(filterAction)
        self.mFilterButton.setPopupMode(QToolButton.InstantPopup)
        # replace the search line edit with a search widget that is suited to the selected field
        # delete previous widget
        if self.mCurrentSearchWidgetWrapper:
            self.mCurrentSearchWidgetWrapper.widget().setVisible(False)
            self.mCurrentSearchWidgetWrapper.deleteLater()

        fieldName = self.mFilterButton.defaultAction().data()
        # get the search widget
        fldIdx = self.mLayer.fields().lookupField(fieldName)
        if fldIdx < 0:
            return

        setup = QgsGui.editorWidgetRegistry().findBest(self.mLayer, fieldName)
        self.mCurrentSearchWidgetWrapper = QgsGui.editorWidgetRegistry().createSearchWidget(setup.type(),
                                                                                            self.mLayer,
                                                                                            fldIdx,
                                                                                            setup.config(),
                                                                                            self.mFilterContainer)
        if self.mCurrentSearchWidgetWrapper.applyDirectly():
            self.mCurrentSearchWidgetWrapper.expressionChanged.connect(self.filterQueryChanged)
            self.mApplyFilterButton.setVisible(False)
            self.mStoreFilterExpressionButton.setVisible(False)

        else:
            self.mCurrentSearchWidgetWrapper.expressionChanged.connect(self.filterQueryAccepted)
            self.mApplyFilterButton.setVisible(True)
            self.mStoreFilterExpressionButton.setVisible(True)

        self.replaceSearchWidget(self.mFilterQuery, self.mCurrentSearchWidgetWrapper.widget())

    def filterExpressionBuilder(self):
        # Show expression builder
        context = QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(self.mLayer))

        dlg = QgsExpressionBuilderDialog(self.mLayer,
                                         self.mFilterQuery.text(),
                                         self,
                                         "generic",
                                         context)
        dlg.setWindowTitle(self.tr("Expression Based Filter"))

        myDa = QgsDistanceArea()
        myDa.setSourceCrs(self.mLayer.crs(), QgsProject.instance().transformContext())
        myDa.setEllipsoid(QgsProject.instance().ellipsoid())
        dlg.setGeomCalculator(myDa)

        if dlg.exec() == QDialog.Accepted:
            self.setFilterExpression(dlg.expressionText(), QgsAttributeForm.ReplaceFilter, True)

    def saveAsStoredFilterExpression(self):
        dlg = QgsDialog(self, Qt.WindowFlags(), QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        dlg.setWindowTitle(self.tr("Save Expression As"))
        layout = QVBoxLayout(dlg.layout())
        dlg.resize(std.max(400, self.width() / 2), dlg.height())

        nameLabel = QLabel(self.tr("Name"), dlg)
        nameEdit = QLineEdit(dlg)
        layout.addWidget(nameLabel)
        layout.addWidget(nameEdit)
        nameEdit.setFocus()

        if dlg.exec() == QDialog.Accepted:
            self.mLayer.storedExpressionManager().addStoredExpression(nameEdit.text(), self.mFilterQuery.text())

            updateCurrentStoredFilterExpression()
            storedFilterExpressionBoxInit()

    def editStoredFilterExpression(self):
        dlg = QgsDialog(self, Qt.WindowFlags(), QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        dlg.setWindowTitle(self.tr("Edit expression"))
        layout = QVBoxLayout(dlg.layout())
        dlg.resize(std.max(400, self.width() / 2), dlg.height())

        nameLabel = QLabel(self.tr("Name"),
                           dlg)
        nameEdit = QLineEdit(self.mLayer.storedExpressionManager().storedExpression(self.mActionHandleStoreFilterExpression.data()).name,
                             dlg)
        expressionLabel = QLabel(self.tr("Expression"),
                                 dlg)
        expressionEdit = QgsExpressionLineEdit(dlg)
        expressionEdit.setExpression(self.mLayer.storedExpressionManager().storedExpression(self.mActionHandleStoreFilterExpression.data()).expression)

        layout.addWidget(nameLabel)
        layout.addWidget(nameEdit)
        layout.addWidget(expressionLabel)
        layout.addWidget(expressionEdit)
        nameEdit.setFocus()

        if dlg.exec() == QDialog.Accepted:
            # Update stored expression
            self.mLayer.storedExpressionManager().updateStoredExpression(self.mActionHandleStoreFilterExpression.data(), nameEdit.text(), expressionEdit.expression(), QgsStoredExpression.Category.FilterExpression)

            # Update text
            self.mFilterQuery.setValue(expressionEdit.expression())

            storedFilterExpressionBoxInit()

    def updateCurrentStoredFilterExpression(self):
        currentStoredExpression = self.mLayer.storedExpressionManager().findStoredExpressionByExpression(self.mFilterQuery.value())

        # Set checked when it's an existing stored expression
        self.mActionHandleStoreFilterExpression.setChecked(len(currentStoredExpression.id) > 0)

        self.mActionHandleStoreFilterExpression.setData(currentStoredExpression.id)
        self.mActionEditStoredFilterExpression.setData(currentStoredExpression.id)

        # Update bookmark button
        self.storeExpressionButtonInit()

    def setFilterExpression(self,
                            filterString: str,
                            type: QgsAttributeForm.FilterType,
                            alwaysShowFilter: bool):
        filter = str()
        if self.mFilterQuery.text() and filterString:
            if type == QgsAttributeForm.ReplaceFilter:
                filter = filterString

            elif type == QgsAttributeForm.FilterAnd:
                filter = "({0}) AND ({1})".format(self.mFilterQuery.text(), filterString)

            elif type == QgsAttributeForm.FilterOr:
                filter = "({0}) OR ({1})".format(self.mFilterQuery.text(), filterString)

        elif filterString:
            filter = filterString

        else:
            filterShowAll()
            return

        self.mFilterQuery.setText(filter)

        if alwaysShowFilter or not self.mCurrentSearchWidgetWrapper or not self.mCurrentSearchWidgetWrapper.applyDirectly():

            self.mFilterButton.setDefaultAction(self.mActionAdvancedFilter)
            self.mFilterButton.setPopupMode(QToolButton.MenuButtonPopup)
            self.mFilterQuery.setVisible(True)
            self.mApplyFilterButton.setVisible(True)
            self.mStoreFilterExpressionButton.setVisible(True)
            if self.mCurrentSearchWidgetWrapper:
                # replace search widget widget with the normal filter query line edit
                self.replaceSearchWidget(self.mCurrentSearchWidgetWrapper.widget(), self.mFilterQuery)

        # parse search string and build parsed tree
        filterExpression = QgsExpression(filter)
        if filterExpression.hasParserError():
            self.mMessageBar.pushMessage(self.tr("Parsing error"), filterExpression.parserErrorString(), Qgis.MessageLevel.Warning)
            return

        context = QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(self.mLayer))

        if not filterExpression.prepare(context):
            self.mMessageBar.pushMessage(self.tr("Evaluation error"), filterExpression.evalErrorString(), Qgis.MessageLevel.Warning)

        self._features_model_filter.set_legacy_filter_expression(filterExpression, context)
        self._features_model_filter.set_legacy_filter(FeaturesModelFilter.LegacyFilter.ShowFilteredList)

    def replaceSearchWidget(self,
                            oldw: QWidget,
                            neww: QWidget):
        self.mFilterLayout.removeWidget(oldw)
        oldw.setVisible(False)
        self.mFilterLayout.addWidget(neww, 0, 0)
        neww.setVisible(True)
        neww.setFocus()

    def onFilterQueryTextChanged(self,
                                 value: str):
        self.mFilterQueryTimer.start(300)
