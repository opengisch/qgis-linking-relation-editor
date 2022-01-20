
import os
from qgis.PyQt.QtCore import QTemporaryDir
from qgis.core import (
    QgsFeature,
    QgsRelation,
    QgsVectorLayer
)
from qgis.testing import (
    unittest,
    start_app
)
from enhanced_relation_editor_widget.gui.relation_editor_link_child_manager_dialog import RelationEditorLinkChildManagerDialog

start_app()


class TestRelationEditorLinkChildManagerDialog(unittest.TestCase):

    def test_Instantiate(self):

        childLayer = QgsVectorLayer('Point?crs=epsg:4326&field=int:integer&field=int2:integer',
                                    'childLayer',
                                    'memory')
        self.assertTrue(childLayer.isValid())

        parentLayer = QgsVectorLayer('Point?crs=epsg:4326&field=int:integer&field=int2:integer',
                                     'parentLayer',
                                     'memory')
        self.assertTrue(parentLayer.isValid())

        dialog = RelationEditorLinkChildManagerDialog(childLayer,
                                                      parentLayer,
                                                      QgsFeature(),
                                                      QgsRelation(),
                                                      QgsRelation(),
                                                      None)

        self.assertEqual(dialog.mLayerNameLabel.text(), childLayer.name())

