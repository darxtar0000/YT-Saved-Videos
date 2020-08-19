from PyQt5.QtCore import QSortFilterProxyModel
class FilterProxyModel(QSortFilterProxyModel):
    '''
    Custom subclass of QSortFilterProxyModel to filter out
    items from one listView that are present in another
    '''
    def __init__(self):
        super().__init__()
        self.filteredSet = set()

    def setFilteredSet(self, qset):
        self.filteredSet = qset.copy()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        item = self.sourceModel().index(sourceRow, 0, sourceParent).data()
        return False if item in self.filteredSet else True
