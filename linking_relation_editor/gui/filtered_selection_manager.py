# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from linking_relation_editor.gui.vector_layer_selection_manager import VectorLayerSelectionManager


class FilteredSelectionManager(VectorLayerSelectionManager):

    def __init__(self, layer, request, parent):

        super().__init__(layer, parent)

        self.mRequest = request
        self.mSelectedFeatureIds = []

        if not layer:
            return

        for fid in layer.selectedFeatureIds():
            if self.mRequest.acceptFeature(layer.getFeature(fid)):
                self.mSelectedFeatureIds.append(fid)

        layer.selectionChanged.connect(self.onSelectionChanged)

    def selectedFeatureIds(self):
        return self.mSelectedFeatureIds

    def selectedFeatureCount(self):
        return len(self.mSelectedFeatureIds)

    def onSelectionChanged(self, selected, deselected, clearAndSelect):
        lselected = selected
        if clearAndSelect:
            self.mSelectedFeatureIds.clear()
        else:
            for fid in deselected:
                self.mSelectedFeatureIds.remove(fid)

        for fid in selected:
            if self.mRequest.acceptFeature(self.layer().getFeature(fid)):
                self.mSelectedFeatureIds.append(fid)
            else:
                lselected.remove(fid)

        self.selectionChanged.emit(lselected, deselected, clearAndSelect)
