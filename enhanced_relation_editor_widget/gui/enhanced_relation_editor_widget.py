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
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsFeature, QgsApplication, QgsMessageLog
from qgis.gui import QgsAbstractRelationEditorWidget, QgsAttributeForm, QgsScrollArea

WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), '../ui/enhanced_relation_editor_widget.ui'))

Debug = True

class EnhancedRelationEditorWidget(QgsAbstractRelationEditorWidget, WidgetUi):

    def __init__(self, config, parent):
        super().__init__(config, parent)
        self.updateUiTimer = QTimer()
        self.updateUiTimer.setSingleShot(True)
        self.updateUiTimer.timeout.connect(self.updateUiTimeout)
        self.setupUi(self)
        self.addFeatureToolButton.setIcon(QgsApplication.getThemeIcon('/mActionNewTableRow.svg'))
        self.addFeatureToolButton.clicked.connect(self.addFeature)
        self.deleteFeatureToolButton.setIcon(QgsApplication.getThemeIcon('/mActionDeleteSelected.svg'))
        self.attribute_form = None

        print('__init__ EnhancedRelationEditorWidget')

        self.ordering_field = str()
        self.image_path = str()
        self.description = str()

    def config(self):
        return {}

    def setConfig(self, config):
        self.ordering_field = config['ordering_field']
        self.image_path = config['image_path']
        self.description = config['description']

    def updateUi(self):
        self.updateUiTimer.start(200)

    def updateUiTimeout(self):
        if Debug:
            QgsMessageLog.logMessage("updateUiTimeout()")

        # we defer attribute form creation on the first valid feature passed on
        if self.attribute_form:
            self.attribute_form.deleteLater()

    def parentFormValueChanged(self, attribute, newValue):
        if self.attribute_form:
            self.attribute_form.parentFormValueChanged(attribute, newValue)
