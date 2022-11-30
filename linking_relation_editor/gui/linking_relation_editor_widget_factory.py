# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Linking Relation Editor Plugin
# Copyright (C) 2021 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from qgis.gui import QgsAbstractRelationEditorWidgetFactory

from linking_relation_editor.gui.linking_relation_editor_config_widget import (
    LinkingRelationEditorConfigWidget,
)
from linking_relation_editor.gui.linking_relation_editor_widget import (
    LinkingRelationEditorWidget,
)

WIDGET_TYPE = "linking_relation_editor"


class LinkingRelationEditorWidgetFactory(QgsAbstractRelationEditorWidgetFactory):
    def type(self):
        return WIDGET_TYPE

    def name(self):
        return "Linking relation editor widget"

    def create(self, config, parent):
        return LinkingRelationEditorWidget(config, parent)

    def configWidget(self, relation, parent):
        return LinkingRelationEditorConfigWidget(relation, parent)
