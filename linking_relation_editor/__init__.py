# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2021 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------


def classFactory(iface):
    """Load plugin.
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from linking_relation_editor.core.linking_relation_editor_plugin import LinkingRelationEditorPlugin
    return LinkingRelationEditorPlugin(iface)
