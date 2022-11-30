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

from qgis.gui import QgisInterface, QgsGui
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QObject, QSettings, QTranslator

from linking_relation_editor.gui.linking_relation_editor_widget_factory import (
    WIDGET_TYPE,
    LinkingRelationEditorWidgetFactory,
)

DEBUG = True


class LinkingRelationEditorPlugin(QObject):

    plugin_name = "&Linking Relation Editor"

    def __init__(self, iface: QgisInterface):
        QObject.__init__(self)
        self.iface = iface

        # initialize translation
        qgis_locale = QLocale(QSettings().value("locale/userLocale"))
        locale_path = os.path.join(os.path.dirname(__file__), "i18n")
        self.translator = QTranslator()
        self.translator.load(qgis_locale, "actions_for_relations", "_", locale_path)
        QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        QgsGui.relationWidgetRegistry().addRelationWidget(LinkingRelationEditorWidgetFactory())

    def unload(self):
        QgsGui.relationWidgetRegistry().removeRelationWidget(WIDGET_TYPE)
