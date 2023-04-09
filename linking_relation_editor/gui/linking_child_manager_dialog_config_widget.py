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

        self.mCheckBoxAllowMultipleLinking.setChecked(config.get("allow_multiple_linking_of_same_feature", False))
        self.mCheckBoxShowAndEditJoinTableAttributes.setChecked(
            config.get("show_and_edit_join_table_attributes", False)
        )

    def config(self):
        return {
            "allow_multiple_linking_of_same_feature": self.mCheckBoxAllowMultipleLinking.isChecked(),
            "show_and_edit_join_table_attributes": self.mCheckBoxShowAndEditJoinTableAttributes.isChecked(),
        }
