
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

        self._quick_filter = str()
        self._map_filter = list()

    def set_quick_filter(self,
                         filter: str):
        self._quick_filter = filter
        self.invalidateFilter()

    def clear_quick_filter(self):
        self._quick_filter = str()
        self.invalidateFilter()

    def quick_filter_active(self):
        return len(self._quick_filter) > 0

    def set_map_filter(self,
                       map_filter: list()):
        self._map_filter = map_filter
        self.invalidateFilter()

    def clear_map_filter(self):
        self._map_filter = list()
        self.invalidateFilter()

    def map_filter_active(self):
        return len(self._map_filter) > 0

    def filter_active(self):
        return self.quick_filter_active() or self.map_filter_active()

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

        if len(self._quick_filter) == 0:
            return True

        rowDisplayRole = self.sourceModel().data(index,
                                                 Qt.DisplayRole)
        if not rowDisplayRole:
            return False

        return self._quick_filter in rowDisplayRole


