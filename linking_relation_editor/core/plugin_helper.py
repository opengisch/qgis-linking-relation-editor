# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Enhanced Relation Editor Widget Plugin
# Copyright (C) 2022 Damiano Lombardi
#
# licensed under the terms of GNU GPL 2
#
# -----------------------------------------------------------

from qgis.core import QgsDataSourceUri


class PluginHelper(object):
    @staticmethod
    def removeLayerIdOrName(layerUri):
        layerUriStripped = str()
        for toRemove in ["|layername=", "|layerid="]:
            pos = layerUri.find(toRemove)
            if pos >= 0:
                end = layerUri.find("|", pos + 1)
                if end >= 0:
                    layerUriStripped = layerUri[pos:end]
                else:
                    layerUriStripped = layerUri[0:pos]

        return layerUriStripped

    @staticmethod
    def connectionString(layerUri):
        connString = QgsDataSourceUri(layerUri).connectionInfo(False)
        # In the case of a OGR datasource, connectionInfo() will return an empty
        # string. In that case, use the layer->source() itself, and strip any
        # reference to layers from it.
        if len(connString) == 0:
            connString = PluginHelper.removeLayerIdOrName(layerUri)

        return connString
