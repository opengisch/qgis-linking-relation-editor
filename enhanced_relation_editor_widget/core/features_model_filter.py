
from qgis.PyQt.QtCore import (
    Qt,
    QModelIndex,
    QObject,
    QSortFilterProxyModel
)


class FeaturesModelFilter(QSortFilterProxyModel):

    def __init__(self,
                 parent: QObject = None):
        super().__init__(parent)

        self._filter = str()

    def set_filter(self,
                   filter: str):
        self._filter = filter
        self.invalidateFilter()

    def clear_filter(self):
        self._filter = str()
        self.invalidateFilter()

    def filterAcceptsRow(self,
                         sourceRow: int,
                         sourceParent: QModelIndex()):

        if len(self._filter) == 0:
            return True

        index = self.sourceModel().index(sourceRow, 0, sourceParent)

        if not self.sourceModel().data(index,
                                       Qt.DisplayRole):
            return False

        return self._filter in self.sourceModel().data(index,
                                                       Qt.DisplayRole)


