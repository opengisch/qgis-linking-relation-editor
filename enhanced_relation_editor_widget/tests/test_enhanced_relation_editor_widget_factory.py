
from qgis.testing import unittest, start_app
from enhanced_relation_editor_widget.gui.enhanced_relation_editor_widget_factory import EnhancedRelationEditorWidgetFactory

start_app()


class TestEnhancedRelationEditorWidgetFactory(unittest.TestCase):

    def test_instantiate(self):
        EnhancedRelationEditorWidgetFactory()

