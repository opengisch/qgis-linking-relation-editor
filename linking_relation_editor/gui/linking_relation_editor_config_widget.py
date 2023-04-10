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
from qgis.PyQt.QtWidgets import QComboBox, QFormLayout

from linking_relation_editor.gui.linking_child_manager_dialog_config_widget import (
    LinkingChildManagerDialogConfigWidget,
)
from linking_relation_editor.gui.linking_relation_editor_widget import (
    CONFIG_LINKING_CHILD_MANAGER_DIALOG,
    CONFIG_ONE_TO_ONE,
)


class LinkingRelationEditorConfigWidget(QgsRelationEditorConfigWidget):
    USER_DATA_ONE_TO_ONE = "one_to_one"

    def __init__(self, relation, parent):
        super().__init__(relation, parent)

        # Setup cardinality combobox with additional entry for one to one
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

        # Insert the linking dialog config widget in the layout
        self.linkingChildManagerDialogConfigWidget = None
        formLayout = None
        formLayoutName = "formLayout"
        formLayouts = self.parent().findChildren(QFormLayout)
        for layout in formLayouts:
            if layout.objectName() == formLayoutName:
                formLayout = layout
                break

        if formLayout is None:
            QgsLogger.warning(self.tr("QFormLayout with object name '{}' not found".format(formLayout)))
        else:
            self.linkingChildManagerDialogConfigWidget = LinkingChildManagerDialogConfigWidget()

            formLayout.insertRow(5, self.linkingChildManagerDialogConfigWidget)

    def setConfig(self, config):
        one_to_one = config.get(CONFIG_ONE_TO_ONE, False)
        if one_to_one:
            index = self.__relation_cardinality_combobox.findData(
                LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE
            )
            if index != -1:
                self.__relation_cardinality_combobox.setCurrentIndex(index)

        if self.linkingChildManagerDialogConfigWidget:
            self.linkingChildManagerDialogConfigWidget.setConfig(config.get(CONFIG_LINKING_CHILD_MANAGER_DIALOG))

        config = super().setConfig(config)

    def config(self):
        config = super().config()
        config[CONFIG_ONE_TO_ONE] = (
            self.__relation_cardinality_combobox.currentData() == LinkingRelationEditorConfigWidget.USER_DATA_ONE_TO_ONE
        )
        if self.linkingChildManagerDialogConfigWidget:
            config[CONFIG_LINKING_CHILD_MANAGER_DIALOG] = self.linkingChildManagerDialogConfigWidget.config()
        return config
