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
from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QObject, QLocale, QSettings
from qgis.gui import QgisInterface, QgsGui
from enhanced_relation_editor_widget.gui.enhanced_relation_editor_widget_factory import EnhancedRelationEditorWidgetFactory, WIDGET_TYPE

DEBUG = True


class EnhancedRelationEditorWidgetPlugin(QObject):

    plugin_name = "&Enhanced Relation Editor Widget"

    def __init__(self, iface: QgisInterface):
        QObject.__init__(self)
        self.iface = iface

        # initialize translation
        qgis_locale = QLocale(QSettings().value('locale/userLocale'))
        locale_path = os.path.join(os.path.dirname(__file__), 'i18n')
        self.translator = QTranslator()
        self.translator.load(qgis_locale, 'actions_for_relations', '_', locale_path)
        QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        QgsGui.relationWidgetRegistry().addRelationWidget(EnhancedRelationEditorWidgetFactory())

    def unload(self):
        QgsGui.relationWidgetRegistry().removeRelationWidget(WIDGET_TYPE)

