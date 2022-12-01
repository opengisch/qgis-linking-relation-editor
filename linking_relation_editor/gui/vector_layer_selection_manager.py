# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from qgis.gui import QgsIFeatureSelectionManager


class VectorLayerSelectionManager(QgsIFeatureSelectionManager):
    def __init__(self, layer, parent):
        super().__init__(parent)

        self.mLayer = layer

        self.mLayer.selectionChanged.connect(self.onSelectionChanged)

    def selectedFeatureCount(self):
        return self.mLayer.selectedFeatureCount()

    def select(self, ids):
        self.mLayer.select(ids)

    def deselect(self, ids):
        self.mLayer.deselect(ids)

    def setSelectedFeatures(self, ids):
        self.mLayer.selectByIds(ids)

    def selectedFeatureIds(self):
        return self.mLayer.selectedFeatureIds()

    def layer(self):
        return self.mLayer

    def onSelectionChanged(self, selected, deselected, clearAndSelect):
        super().selectionChanged(selected, deselected, clearAndSelect)
