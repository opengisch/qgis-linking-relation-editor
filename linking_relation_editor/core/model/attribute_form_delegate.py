# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Linking Relation Editor
# Copyright (C) 2023 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from qgis.PyQt.QtWidgets import QItemDelegate


class AttributeFormDelegate(QItemDelegate):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._model = model
        self._attributeForm = None

    def createEditor(self, parent, option, index):
        item = index.internalPointer()
        self._attributeForm = item.createAttributeForm(parent)
        self.sizeHintChanged.emit(index)
        return self._attributeForm

    def setModelData(self, editor, model, index):
        print("setModelData")

    def setEditorData(self, editor, index):
        print("setEditorData")

    def sizeHint(self, option, index):
        # No parent -> normal item
        if not self._model.parent(index).isValid():
            return super().sizeHint(option, index)

        if self._attributeForm is None:
            return super().sizeHint(option, index)

        return self._attributeForm.sizeHint()
