
from qgis.PyQt.QtCore import (
    Qt,
    QModelIndex,
    QObject,
    QSortFilterProxyModel
)
from enhanced_relation_editor_widget.core.features_model import FeaturesModel


class FeaturesModelFilter(QSortFilterProxyModel):

    def __init__(self,
                 parent: QObject = None):
        super().__init__(parent)

        self._filter = str()
        self._map_filter = list()

    def set_filter(self,
                   filter: str):
        self._filter = filter
        self.invalidateFilter()

    def clear_filter(self):
        self._filter = str()
        self.invalidateFilter()

    def set_map_filter(self,
                       map_filter: list()):
        self._map_filter = map_filter
        self.invalidateFilter()

    def clear_map_filter(self):
        self._map_filter = list()
        self.invalidateFilter()

    def filterAcceptsRow(self,
                         sourceRow: int,
                         sourceParent: QModelIndex()):
        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        if self._map_filter:
            rowFeatureId = self.sourceModel().data(index,
                                                   FeaturesModel.UserRole.FeatureId)

            if not rowFeatureId:
                return False

            if rowFeatureId not in self._map_filter:
                return False

        if len(self._filter) == 0:
            return True

        rowDisplayRole = self.sourceModel().data(index,
                                                 Qt.DisplayRole)
        if not rowDisplayRole:
            return False

        return self._filter in rowDisplayRole


