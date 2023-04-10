# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Linking Relation Editor
# Copyright (C) 2023 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

import os

from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType

from linking_relation_editor.gui.linking_child_manager_dialog import (
    CONFIG_SHOW_AND_EDIT_JOIN_TABLE_ATTRIBUTES,
)

WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), "../ui/linking_child_manager_dialog_config_widget.ui"))


class LinkingChildManagerDialogConfigWidget(QDialog, WidgetUi):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        # Ui setup
        self.setupUi(self)

    def setConfig(self, config):
        if config is None:
            config = {}

        self.mCheckBoxShowAndEditJoinTableAttributes.setChecked(
            config.get(CONFIG_SHOW_AND_EDIT_JOIN_TABLE_ATTRIBUTES, False)
        )

    def config(self):
        return {
            CONFIG_SHOW_AND_EDIT_JOIN_TABLE_ATTRIBUTES: self.mCheckBoxShowAndEditJoinTableAttributes.isChecked(),
        }
