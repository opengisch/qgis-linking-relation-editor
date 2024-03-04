from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsProject,
    QgsRelation,
    QgsVectorLayer,
)
from qgis.gui import QgsGui
from qgis.PyQt.QtWidgets import QWidget
from qgis.testing import start_app, unittest

from linking_relation_editor.gui.linking_relation_editor_widget_factory import (
    LinkingRelationEditorWidget,
)

start_app()


class TestRelationEditorMultiedit(unittest.TestCase):

    def setUp(self):
        pass
        # QgsApplication.init()
        QgsApplication.initQgis()
        QgsGui.editorWidgetRegistry().initEditors()

    def tearDown(self):
        return
        QgsApplication.exitQgis()

    @classmethod
    def setUpClass(cls):

        cls.mLayer1 = None
        cls.mLayer2 = None
        cls.mLayerJoin = None
        cls.mRelation = None
        cls.mRelation1N = None
        cls.mRelationNM = None

        # create layer
        cls.mLayer1 = QgsVectorLayer("LineString?field=pk:int&field=fk:int", "vl1", "memory")
        cls.mLayer1.setDisplayExpression("'Layer1-' || pk")
        QgsProject.instance().addMapLayer(cls.mLayer1, False)

        cls.mLayer2 = QgsVectorLayer("LineString?field=pk:int", "vl2", "memory")
        cls.mLayer2.setDisplayExpression("'Layer2-' || pk")
        QgsProject.instance().addMapLayer(cls.mLayer2, False)

        cls.mLayerJoin = QgsVectorLayer(
            "LineString?field=pk:int&field=fk_layer1:int&field=fk_layer2:int", "join_layer", "memory"
        )
        cls.mLayerJoin.setDisplayExpression("'LayerJoin-' || pk")
        QgsProject.instance().addMapLayer(cls.mLayerJoin, False)

        # create relation
        cls.mRelation = QgsRelation()
        cls.mRelation.setId("vl1.vl2")
        cls.mRelation.setName("vl1.vl2")
        cls.mRelation.setReferencingLayer(cls.mLayer1.id())
        cls.mRelation.setReferencedLayer(cls.mLayer2.id())
        cls.mRelation.addFieldPair("fk", "pk")
        assert cls.mRelation.isValid()
        QgsProject.instance().relationManager().addRelation(cls.mRelation)

        # create nm relations
        cls.mRelation1N = QgsRelation()
        cls.mRelation1N.setId("join_layer.vl1")
        cls.mRelation1N.setName("join_layer.vl1")
        cls.mRelation1N.setReferencingLayer(cls.mLayerJoin.id())
        cls.mRelation1N.setReferencedLayer(cls.mLayer1.id())
        cls.mRelation1N.addFieldPair("fk_layer1", "pk")
        assert cls.mRelation1N.isValid()
        QgsProject.instance().relationManager().addRelation(cls.mRelation1N)

        cls.mRelationNM = QgsRelation()
        cls.mRelationNM.setId("join_layer.vl2")
        cls.mRelationNM.setName("join_layer.vl2")
        cls.mRelationNM.setReferencingLayer(cls.mLayerJoin.id())
        cls.mRelationNM.setReferencedLayer(cls.mLayer2.id())
        cls.mRelationNM.addFieldPair("fk_layer2", "pk")
        assert cls.mRelationNM.isValid()
        QgsProject.instance().relationManager().addRelation(cls.mRelationNM)

        # add features
        ft0 = QgsFeature(cls.mLayer1.fields())
        ft0.setAttribute("pk", 0)
        ft0.setAttribute("fk", 10)
        cls.mLayer1.startEditing()
        cls.mLayer1.addFeature(ft0)
        cls.mLayer1.commitChanges()

        ft1 = QgsFeature(cls.mLayer1.fields())
        ft1.setAttribute("pk", 1)
        ft1.setAttribute("fk", 11)
        cls.mLayer1.startEditing()
        cls.mLayer1.addFeature(ft1)
        cls.mLayer1.commitChanges()

        ft2 = QgsFeature(cls.mLayer2.fields())
        ft2.setAttribute("pk", 10)
        cls.mLayer2.startEditing()
        cls.mLayer2.addFeature(ft2)
        cls.mLayer2.commitChanges()

        ft3 = QgsFeature(cls.mLayer2.fields())
        ft3.setAttribute("pk", 11)
        cls.mLayer2.startEditing()
        cls.mLayer2.addFeature(ft3)
        cls.mLayer2.commitChanges()

        ft4 = QgsFeature(cls.mLayer2.fields())
        ft4.setAttribute("pk", 12)
        cls.mLayer2.startEditing()
        cls.mLayer2.addFeature(ft4)
        cls.mLayer2.commitChanges()

        # Add join features
        jft1 = QgsFeature(cls.mLayerJoin.fields())
        jft1.setAttribute("pk", 101)
        jft1.setAttribute("fk_layer1", 0)
        jft1.setAttribute("fk_layer2", 10)
        cls.mLayerJoin.startEditing()
        cls.mLayerJoin.addFeature(jft1)
        cls.mLayerJoin.commitChanges()

        jft2 = QgsFeature(cls.mLayerJoin.fields())
        jft2.setAttribute("pk", 102)
        jft2.setAttribute("fk_layer1", 1)
        jft2.setAttribute("fk_layer2", 11)
        cls.mLayerJoin.startEditing()
        cls.mLayerJoin.addFeature(jft2)
        cls.mLayerJoin.commitChanges()

        jft3 = QgsFeature(cls.mLayerJoin.fields())
        jft3.setAttribute("pk", 102)
        jft3.setAttribute("fk_layer1", 0)
        jft3.setAttribute("fk_layer2", 11)
        cls.mLayerJoin.startEditing()
        cls.mLayerJoin.addFeature(jft3)
        cls.mLayerJoin.commitChanges()

    @classmethod
    def tearDownClass(cls):
        QgsProject.instance().removeMapLayer(cls.mLayer1)
        QgsProject.instance().removeMapLayer(cls.mLayer2)
        QgsProject.instance().removeMapLayer(cls.mLayerJoin)

    def testMultiEdit1N(self):
        # Init a relation editor widget
        parent = QWidget()
        relationEditorWidget = LinkingRelationEditorWidget({}, parent)
        relationEditorWidget.setRelations(self.mRelation, QgsRelation())

        self.assertFalse(relationEditorWidget.multiEditModeActive())

        featureIds = list()
        for feature in self.mLayer2.getFeatures():
            featureIds.append(feature.id())

        relationEditorWidget.setMultiEditFeatureIds(featureIds)

        # Update ui
        relationEditorWidget.updateUiMultiEdit()

        self.assertTrue(relationEditorWidget.multiEditModeActive())

        setParentItemsText = set()
        setChildrenItemsText = set()
        for parentIndex in range(relationEditorWidget.mMultiEditTreeWidget.topLevelItemCount()):
            parentItem = relationEditorWidget.mMultiEditTreeWidget.topLevelItem(parentIndex)
            setParentItemsText.add(parentItem.text(0))
            self.assertEqual(
                parentItem.data(0, (LinkingRelationEditorWidget.MultiEditTreeWidgetRole.FeatureType)),
                (LinkingRelationEditorWidget.MultiEditFeatureType.Parent),
            )
            for childIndex in range(parentItem.childCount()):
                childItem = parentItem.child(childIndex)
                setChildrenItemsText.add(childItem.text(0))
                self.assertEqual(
                    childItem.data(0, (LinkingRelationEditorWidget.MultiEditTreeWidgetRole.FeatureType)),
                    (LinkingRelationEditorWidget.MultiEditFeatureType.Child),
                )

                if childItem.text(0) == "Layer1-0":
                    self.assertEqual(parentItem.text(0), "Layer2-10")

                if childItem.text(0) == "Layer1-1":
                    self.assertEqual(parentItem.text(0), "Layer2-11")

        self.assertEqual(setParentItemsText, {"Layer2-10", "Layer2-11", "Layer2-12"})
        self.assertEqual(setChildrenItemsText, {"Layer1-0", "Layer1-1"})

    def testMultiEditNM(self):
        # Init a relation editor widget
        parent = QWidget()
        relationEditorWidget = LinkingRelationEditorWidget({}, parent)
        relationEditorWidget.setRelations(self.mRelation1N, self.mRelationNM)

        self.assertFalse(relationEditorWidget.multiEditModeActive())

        featureIds = list()
        for feature in self.mLayer1.getFeatures():
            featureIds.append(feature.id())
        relationEditorWidget.setMultiEditFeatureIds(featureIds)

        # Update ui
        relationEditorWidget.updateUiMultiEdit()

        self.assertTrue(relationEditorWidget.multiEditModeActive())

        setParentItemsText = set()
        listChildrenItemsText = list()
        for parentIndex in range(relationEditorWidget.mMultiEditTreeWidget.topLevelItemCount()):
            parentItem = relationEditorWidget.mMultiEditTreeWidget.topLevelItem(parentIndex)
            setParentItemsText.add(parentItem.text(0))
            self.assertEqual(
                parentItem.data(0, (LinkingRelationEditorWidget.MultiEditTreeWidgetRole.FeatureType)),
                (LinkingRelationEditorWidget.MultiEditFeatureType.Parent),
            )

            for childIndex in range(parentItem.childCount()):
                childItem = parentItem.child(childIndex)
                listChildrenItemsText.append(childItem.text(0))
                self.assertEqual(
                    childItem.data(0, (LinkingRelationEditorWidget.MultiEditTreeWidgetRole.FeatureType)),
                    (LinkingRelationEditorWidget.MultiEditFeatureType.Child),
                )

                if childItem.text(0) == "Layer2-10":
                    self.assertEqual(parentItem.text(0), "Layer1-0")

                if childItem.text(0) == "Layer2-11":
                    possibleParents = list()
                    possibleParents.append("Layer1-0")
                    possibleParents.append("Layer1-1")
                    self.assertTrue(parentItem.text(0), possibleParents)

        self.assertEqual(setParentItemsText, {"Layer1-0", "Layer1-1"})

        listChildrenItemsText.sort()
        self.assertEqual(listChildrenItemsText, ["Layer2-10", "Layer2-11", "Layer2-11"])
