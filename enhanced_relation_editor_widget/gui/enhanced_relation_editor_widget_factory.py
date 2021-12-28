# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2021 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from qgis.PyQt.QtCore import QObject
from qgis.gui import QgsAbstractRelationEditorWidgetFactory
from enhanced_relation_editor_widget.gui.enhanced_relation_editor_widget import EnhancedRelationEditorWidget
from enhanced_relation_editor_widget.gui.enhanced_relation_editor_widget_config_widget import EnhancedRelationEditorWidgetConfigWidget

WIDGET_TYPE = "enhanced_relation_editor_widget"


class EnhancedRelationEditorWidgetFactory(QgsAbstractRelationEditorWidgetFactory):
    def type(self):
        return WIDGET_TYPE

    def name(self):
        return "Enhanced relation editor widget"

    def create(self, config, parent):
        return EnhancedRelationEditorWidget(config, parent)

    def configWidget(self, relation, parent):
        return EnhancedRelationEditorWidgetConfigWidget(relation, parent)
