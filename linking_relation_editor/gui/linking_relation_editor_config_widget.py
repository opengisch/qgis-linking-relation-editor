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

from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QComboBox
from qgis.PyQt.uic import loadUiType

from qgis.gui import (
    QgsAbstractRelationEditorConfigWidget,
    QgsRelationEditorConfigWidget
)


WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__),
                                      '../ui/linking_relation_editor_config_widget.ui'))


class LinkingRelationEditorConfigWidget(QgsRelationEditorConfigWidget):

    USER_DATA_ONE_TO_ONE = "one_to_one"

    def __init__(self, relation, parent):
        super().__init__(relation, parent)

        self.__relation_cardinality_combobox = None
        comboboxes = self.parent().findChildren(QComboBox)
        for combobox in comboboxes:
            if combobox.objectName() == "mRelationCardinalityCombo":
              self.__relation_cardinality_combobox = combobox
              break

        self.__relation_cardinality_combobox.addItem("One to one",
                                                     LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE)
    
    def setConfig(self, config):
        one_to_one = config.get("one_to_one",
                                False)

        if one_to_one:
            index = self.__relation_cardinality_combobox.findData(LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE)
            if index != -1:
                self.__relation_cardinality_combobox.setCurrentIndex(index)

        config = super().setConfig(config)

    def config(self):
        config = super().config()
        config["one_to_one"] = self.__relation_cardinality_combobox.currentData() == LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE
        return config
