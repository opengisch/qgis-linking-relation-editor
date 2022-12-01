# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from qgis.core import QgsLogger
from qgis.gui import QgsRelationEditorConfigWidget
from qgis.PyQt.QtWidgets import QComboBox


class LinkingRelationEditorConfigWidget(QgsRelationEditorConfigWidget):

    USER_DATA_ONE_TO_ONE = "one_to_one"

    def __init__(self, relation, parent):
        super().__init__(relation, parent)

        self.__relation_cardinality_combobox = None
        relation_cardinality_combobox_name = "mRelationCardinalityCombo"
        comboboxes = self.parent().findChildren(QComboBox)
        for combobox in comboboxes:
            if combobox.objectName() == relation_cardinality_combobox_name:
                self.__relation_cardinality_combobox = combobox
                break

        if self.__relation_cardinality_combobox is None:
            QgsLogger.warning(
                self.tr("QCombobox with object name '{}' not found".format(relation_cardinality_combobox_name))
            )
        else:
            self.__relation_cardinality_combobox.addItem(
                "One to one relation", LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE
            )

    def setConfig(self, config):
        one_to_one = config.get("one_to_one", False)

        if one_to_one:
            index = self.__relation_cardinality_combobox.findData(
                LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE
            )
            if index != -1:
                self.__relation_cardinality_combobox.setCurrentIndex(index)

        config = super().setConfig(config)

    def config(self):
        config = super().config()
        config["one_to_one"] = (
            self.__relation_cardinality_combobox.currentData() == LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE
        )
        return config
