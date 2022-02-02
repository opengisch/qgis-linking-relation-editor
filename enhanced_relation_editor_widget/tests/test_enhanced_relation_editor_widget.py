

from qgis.PyQt.QtWidgets import QWidget
from qgis.core import (
    QgsFeature,
    QgsProject,
    QgsRelation,
    QgsVectorLayer
)
from qgis.testing import (
    unittest,
    start_app
)
from enhanced_relation_editor_widget.gui.enhanced_relation_editor_widget_factory import EnhancedRelationEditorWidget

start_app()


class TestEnhancedRelationEditorWidgetFactory(unittest.TestCase):

    def setUp(self):
        # create layer
        self.mLayer1 = QgsVectorLayer(("LineString?field=pk:int&field=fk:int"), ("vl1"), ("memory"))
        self.mLayer1.setDisplayExpression(("'Layer1-' || pk"))
        QgsProject.instance().addMapLayer(self.mLayer1, False)

        self.mLayer2 = QgsVectorLayer(("LineString?field=pk:int"), ("vl2"), ("memory"))
        self.mLayer2.setDisplayExpression(("'Layer2-' || pk"))
        QgsProject.instance().addMapLayer(self.mLayer2, False)

        self.mLayerJoin = QgsVectorLayer(("LineString?field=pk:int&field=fk_layer1:int&field=fk_layer2:int"), ("join_layer"), ("memory"))
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
        self.mLayer1.startEditing()
        self.mLayer1.addFeature(ft0)
        self.mLayer1.commitChanges()

        ft1 = QgsFeature(self.mLayer1.fields())
        ft1.setAttribute(("pk"), 1)
        ft1.setAttribute(("fk"), 11)
        self.mLayer1.startEditing()
        self.mLayer1.addFeature(ft1)
        self.mLayer1.commitChanges()

        ft2 = QgsFeature(self.mLayer2.fields())
        ft2.setAttribute(("pk"), 10)
        self.mLayer2.startEditing()
        self.mLayer2.addFeature(ft2)
        self.mLayer2.commitChanges()

        ft3 = QgsFeature(self.mLayer2.fields())
        ft3.setAttribute(("pk"), 11)
        self.mLayer2.startEditing()
        self.mLayer2.addFeature(ft3)
        self.mLayer2.commitChanges()

        ft4 = QgsFeature(self.mLayer2.fields())
        ft4.setAttribute(("pk"), 12)
        self.mLayer2.startEditing()
        self.mLayer2.addFeature(ft4)
        self.mLayer2.commitChanges()

        # Add join features
        jft1 = QgsFeature(self.mLayerJoin.fields())
        jft1.setAttribute(("pk"), 101)
        jft1.setAttribute(("fk_layer1"), 0)
        jft1.setAttribute(("fk_layer2"), 10)
        self.mLayerJoin.startEditing()
        self.mLayerJoin.addFeature(jft1)
        self.mLayerJoin.commitChanges()

        jft2 = QgsFeature(self.mLayerJoin.fields())
        jft2.setAttribute(("pk"), 102)
        jft2.setAttribute(("fk_layer1"), 1)
        jft2.setAttribute(("fk_layer2"), 11)
        self.mLayerJoin.startEditing()
        self.mLayerJoin.addFeature(jft2)
        self.mLayerJoin.commitChanges()

        jft3 = QgsFeature(self.mLayerJoin.fields())
        jft3.setAttribute(("pk"), 102)
        jft3.setAttribute(("fk_layer1"), 0)
        jft3.setAttribute(("fk_layer2"), 11)
        self.mLayerJoin.startEditing()
        self.mLayerJoin.addFeature(jft3)
        self.mLayerJoin.commitChanges()

    def tearDown(self):
        QgsProject.instance().removeMapLayer(self.mLayer1)
        QgsProject.instance().removeMapLayer(self.mLayer2)
        QgsProject.instance().removeMapLayer(self.mLayerJoin)

    def test_InstantiateRelation1N(self):
        # Init a relation editor widget
        parentWidget = QWidget()
        relationEditorWidget = EnhancedRelationEditorWidget({},
                                                            parentWidget)
        relationEditorWidget.setRelations(self.mRelation,
                                          QgsRelation())

        for feature in self.mLayer2.getFeatures():
            relationEditorWidget.setFeature(feature)
            break

        # Update ui
        relationEditorWidget.updateUi()

    def test_InstantiateRelation1N_linkFeatures(self):

        # Init a relation editor widget
        parentWidget = QWidget()
        relationEditorWidget = EnhancedRelationEditorWidget({},
                                                            parentWidget)
        relationEditorWidget.setRelations(self.mRelation,
                                          QgsRelation())

        for feature in self.mLayer2.getFeatures():
            relationEditorWidget.setFeature(feature)
            break

        # Update ui
        relationEditorWidget.updateUi()

        relationEditorWidget._linkFeatures([feature.id()])

    def test_InstantiateRelationNM(self):
        # Init a relation editor widget
        parentWidget = QWidget()
        relationEditorWidget = EnhancedRelationEditorWidget({},
                                                            parentWidget)
        relationEditorWidget.setRelations(self.mRelation1N,
                                          self.mRelationNM)

        for feature in self.mLayer1.getFeatures():
            relationEditorWidget.setFeature(feature)
            break

        # Update ui
        relationEditorWidget.updateUi()

    def test_InstantiateRelationNM_linkFeatures(self):
        # Init a relation editor widget
        parentWidget = QWidget()
        relationEditorWidget = EnhancedRelationEditorWidget({},
                                                            parentWidget)
        relationEditorWidget.setRelations(self.mRelation1N,
                                          self.mRelationNM)

        for feature in self.mLayer1.getFeatures():
            relationEditorWidget.setFeature(feature)
            break

        # Update ui
        relationEditorWidget.updateUi()

        relationEditorWidget._linkFeatures([feature.id()])
