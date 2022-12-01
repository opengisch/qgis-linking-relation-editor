from qgis.testing import start_app, unittest

from linking_relation_editor.gui.linking_relation_editor_widget_factory import (
    LinkingRelationEditorWidgetFactory,
)

start_app()


class TestLinkingRelationEditorWidgetFactory(unittest.TestCase):
    def test_Instantiate(self):
        LinkingRelationEditorWidgetFactory()
