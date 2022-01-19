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
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsVectorLayerUtils
from enhanced_relation_editor_widget.core.features_model import FeaturesModel


WidgetUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), '../ui/relation_editor_link_child_manager_dialog.ui'))


class RelationEditorLinkChildManagerDialog(QDialog, WidgetUi):

    def __init__(self, parent, layer, parentLayer, parentFeature):
        super().__init__(parent)

        # Ui setup
        self.setupUi(self)

        displayString = QgsVectorLayerUtils.getFeatureDisplayString(parentLayer, parentFeature)
        self.setWindowTitle(self.tr("Manage linked features for parent {0} \"{1}\"").format(parentLayer.name(),
                                                                                            displayString))

        self.mLayerNameLabel.setText(layer.name())

        linkedFeatures, unlinkedFeatures = self._getAllFeatures()

        self._featuresModelLeft = FeaturesModel(unlinkedFeatures,
                                                layer,
                                                self)
        self.mFeaturesListViewLeft.setModel(self._featuresModelLeft)

        self._featuresModelRight = FeaturesModel(linkedFeatures,
                                                 layer,
                                                 self)
        self.mFeaturesListViewRight.setModel(self._featuresModelRight)

    def _getAllFeatures(self):

        linkedFeatures = []
        unlinkedFeatures = []

        return linkedFeatures, unlinkedFeatures



