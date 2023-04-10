from qgis.core import QgsFeature, QgsProject, QgsRelation, QgsVectorLayer
from qgis.gui import QgsAttributeEditorContext
from qgis.PyQt.QtCore import Qt
from qgis.testing import start_app, unittest

from linking_relation_editor.gui.linking_child_manager_dialog import (
    LinkingChildManagerDialog,
)

start_app()


class TestLinkingChildManagerDialog(unittest.TestCase):
    def setUp(self):
        # create layer
        self.mLayer1 = QgsVectorLayer(("LineString?field=pk:int&field=fk:int&field=name:string"), ("vl1"), ("memory"))
        self.mLayer1.setDisplayExpression(("'Layer1-' || pk || ': ' || name"))
        QgsProject.instance().addMapLayer(self.mLayer1, False)

        self.mLayer2 = QgsVectorLayer(("LineString?field=pk:int"), ("vl2"), ("memory"))
        self.mLayer2.setDisplayExpression(("'Layer2-' || pk"))
        QgsProject.instance().addMapLayer(self.mLayer2, False)

        self.mLayerJoin = QgsVectorLayer(
            ("LineString?field=pk:int&field=fk_layer1:int&field=fk_layer2:int"), ("join_layer"), ("memory")
        )
        self.mLayerJoin.setDisplayExpression(("'LayerJoin-' || pk"))
        QgsProject.instance().addMapLayer(self.mLayerJoin, False)

        # create relation
        self.mRelation = QgsRelation()
        self.mRelation.setId(("vl1.vl2"))
        self.mRelation.setName(("vl1.vl2"))
        self.mRelation.setReferencingLayer(self.mLayer1.id())
        self.mRelation.setReferencedLayer(self.mLayer2.id())
        self.mRelation.addFieldPair(("fk"), ("pk"))
        self.assertTrue(self.mRelation.isValid())
        QgsProject.instance().relationManager().addRelation(self.mRelation)

        # create nm relations
        self.mRelation1N = QgsRelation()
        self.mRelation1N.setId(("join_layer.vl1"))
        self.mRelation1N.setName(("join_layer.vl1"))
        self.mRelation1N.setReferencingLayer(self.mLayerJoin.id())
        self.mRelation1N.setReferencedLayer(self.mLayer1.id())
        self.mRelation1N.addFieldPair(("fk_layer1"), ("pk"))
        self.assertTrue(self.mRelation1N.isValid())
        QgsProject.instance().relationManager().addRelation(self.mRelation1N)

        self.mRelationNM = QgsRelation()
        self.mRelationNM.setId(("join_layer.vl2"))
        self.mRelationNM.setName(("join_layer.vl2"))
        self.mRelationNM.setReferencingLayer(self.mLayerJoin.id())
        self.mRelationNM.setReferencedLayer(self.mLayer2.id())
        self.mRelationNM.addFieldPair(("fk_layer2"), ("pk"))
        self.assertTrue(self.mRelationNM.isValid())
        QgsProject.instance().relationManager().addRelation(self.mRelationNM)

        # add features
        ft0 = QgsFeature(self.mLayer1.fields())
        ft0.setAttribute("pk", 0)
        ft0.setAttribute("fk", 10)
        ft0.setAttribute("name", "The Artist formerly known as Prince")
        self.mLayer1.startEditing()
        self.mLayer1.addFeature(ft0)
        self.mLayer1.commitChanges()

        ft1 = QgsFeature(self.mLayer1.fields())
        ft1.setAttribute("pk", 1)
        ft1.setAttribute("fk", 11)
        ft1.setAttribute("name", "Martina formerly known as Prisca")
        self.mLayer1.startEditing()
        self.mLayer1.addFeature(ft1)
        self.mLayer1.commitChanges()

        ft2 = QgsFeature(self.mLayer2.fields())
        ft2.setAttribute("pk", 10)
        self.mLayer2.startEditing()
        self.mLayer2.addFeature(ft2)
        self.mLayer2.commitChanges()

        ft3 = QgsFeature(self.mLayer2.fields())
        ft3.setAttribute("pk", 11)
        self.mLayer2.startEditing()
        self.mLayer2.addFeature(ft3)
        self.mLayer2.commitChanges()

        ft4 = QgsFeature(self.mLayer2.fields())
        ft4.setAttribute("pk", 12)
        self.mLayer2.startEditing()
        self.mLayer2.addFeature(ft4)
        self.mLayer2.commitChanges()

        # Add join features
        jft1 = QgsFeature(self.mLayerJoin.fields())
        jft1.setAttribute("pk", 101)
        jft1.setAttribute("fk_layer1", 0)
        jft1.setAttribute("fk_layer2", 10)
        self.mLayerJoin.startEditing()
        self.mLayerJoin.addFeature(jft1)
        self.mLayerJoin.commitChanges()

        jft2 = QgsFeature(self.mLayerJoin.fields())
        jft2.setAttribute("pk", 102)
        jft2.setAttribute("fk_layer1", 1)
        jft2.setAttribute("fk_layer2", 11)
        self.mLayerJoin.startEditing()
        self.mLayerJoin.addFeature(jft2)
        self.mLayerJoin.commitChanges()

        jft3 = QgsFeature(self.mLayerJoin.fields())
        jft3.setAttribute("pk", 102)
        jft3.setAttribute("fk_layer1", 0)
        jft3.setAttribute("fk_layer2", 11)
        self.mLayerJoin.startEditing()
        self.mLayerJoin.addFeature(jft3)
        self.mLayerJoin.commitChanges()

    def tearDown(self):
        QgsProject.instance().removeMapLayer(self.mLayer1)
        QgsProject.instance().removeMapLayer(self.mLayer2)
        QgsProject.instance().removeMapLayer(self.mLayerJoin)

    def test_Instantiate(self):
        childLayer = QgsVectorLayer("Point?crs=epsg:4326&field=int:integer&field=int2:integer", "childLayer", "memory")
        self.assertTrue(childLayer.isValid())

        parentLayer = QgsVectorLayer(
            "Point?crs=epsg:4326&field=int:integer&field=int2:integer", "parentLayer", "memory"
        )
        self.assertTrue(parentLayer.isValid())

        dialog = LinkingChildManagerDialog(
            childLayer,
            parentLayer,
            QgsFeature(),
            QgsRelation(),
            QgsRelation(),
            QgsAttributeEditorContext(),
            False,
            {},
            None,
        )

        self.assertEqual(dialog.mLayerNameLabel.text(), childLayer.name())

    def test_InstantiateRelation1N(self):
        parentFeature = QgsFeature()
        for feature in self.mLayer2.getFeatures():
            parentFeature = feature
            break

        self.assertTrue(parentFeature.isValid())

        dialog = LinkingChildManagerDialog(
            self.mLayer1,
            self.mLayer2,
            parentFeature,
            self.mRelation,
            QgsRelation(),
            QgsAttributeEditorContext(),
            False,
            {},
            None,
        )

        self.assertEqual(dialog.mLayerNameLabel.text(), self.mLayer1.name())

    def test_InstantiateRelationNM(self):
        parentFeature = QgsFeature()
        for feature in self.mLayer1.getFeatures():
            parentFeature = feature
            break

        self.assertTrue(parentFeature.isValid())

        dialog = LinkingChildManagerDialog(
            self.mLayer2,
            self.mLayer1,
            parentFeature,
            self.mRelation1N,
            self.mRelationNM,
            QgsAttributeEditorContext(),
            False,
            {},
            None,
        )

        self.assertEqual(dialog.mLayerNameLabel.text(), self.mLayer2.name())

    def test_quickFilter(self):
        # get a parent with no childs
        parentFeature = QgsFeature()
        for feature in self.mLayer2.getFeatures():
            if feature.attribute("pk") == 12:
                parentFeature = feature
                break

        self.assertTrue(parentFeature.isValid())

        dialog = LinkingChildManagerDialog(
            self.mLayer1,
            self.mLayer2,
            parentFeature,
            self.mRelation,
            QgsRelation(),
            QgsAttributeEditorContext(),
            False,
            {},
            None,
        )

        self.assertEqual(dialog.mLayerNameLabel.text(), self.mLayer1.name())

        # all entries
        # "Layer1-0: The Artist formerly known as Prince"
        # "Layer1-1: Martina formerly known as Prisca"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 2)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(1, 0), Qt.DisplayRole),
            "Layer1-1: Martina formerly known as Prisca",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("Prince")
        # "Layer1-0: The Artist formerly known as *Prince*"
        # no "Prince" in the other entry
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 1)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("formerly")
        # "Layer1-0: The Artist *formerly* known as Prince"
        # "Layer1-1: Martina *formerly* known as Prisca"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 2)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(1, 0), Qt.DisplayRole),
            "Layer1-1: Martina formerly known as Prisca",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("formerly Pri")
        # "Layer1-0: The Artist *formerly* known as *Pri*nce"
        # "Layer1-1: Martina *formerly* known as *Pri*sca"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 2)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(1, 0), Qt.DisplayRole),
            "Layer1-1: Martina formerly known as Prisca",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("formerly Pri art")
        # "Layer1-0: The *Art*ist *formerly* known as *Pri*nce"
        # "Layer1-1: M*art*ina *formerly* known as *Pri*sca"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 2)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(1, 0), Qt.DisplayRole),
            "Layer1-1: Martina formerly known as Prisca",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("formerly Pri art the")
        # "Layer1-0: *The* *Art*ist *formerly* known as *Pri*nce"
        # no "the" in the other entry
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 1)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("formerly Pri Mar")
        # "Layer1-1: *Mar*tina *formerly* known as *Pri*sca"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 1)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-1: Martina formerly known as Prisca",
        )

        dialog._featuresModelFilterLeft.set_quick_filter("formerly Pri Charles")
        # no "Charles"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 0)

        dialog._featuresModelFilterLeft.set_quick_filter("")
        # "Layer1-0: The Artist formerly known as Prince"
        # "Layer1-1: Martina formerly known as Prisca"
        self.assertEqual(dialog._featuresModelFilterLeft.rowCount(), 2)
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(0, 0), Qt.DisplayRole),
            "Layer1-0: The Artist formerly known as Prince",
        )
        self.assertEqual(
            dialog._featuresModelFilterLeft.data(dialog._featuresModelFilterLeft.index(1, 0), Qt.DisplayRole),
            "Layer1-1: Martina formerly known as Prisca",
        )
