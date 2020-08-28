from PyQt5.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QVariant, QModelIndex, QItemSelectionModel, QAbstractItemModel, pyqtSignal, QCoreApplication
from PyQt5.QtWidgets import QWidget, QCompleter, QLineEdit
from PyQt5.QtSql import QSqlQuery, QSqlQueryModel
from uiLeftPanel import Ui_LeftPanel
from filterProxyModel import FilterProxyModel

'''
Left Panel UI contents
filterListAlpha = QListView
filterListBeta = QListView
filterTypeDropDown = QComboBox
filterSearchBar = QLineEdit
tagListAlpha = QListView
tagListBeta = QListView
tagSearchBar = QLineEdit
tagTypeDropDown = QComboBox

Methods

filterListAlphaDoubleClicked()
filterListBetaDoubleClicked()
filterSearchBarChanged()
tagSearchBarChanged()
tagSearchBarReturnPressed()
tagListAlphaDoubleClicked()
tagListBetaDoubleClicked()

filterListAlphaUpdate()
filterListBetaUpdate()
tagListAlphaUpdate()
tagListBetaUpdate()
'''

class LineEditKeyboard(QLineEdit):
    keyUpPressed = pyqtSignal()
    keyDownPressed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.upPressed()
        if event.key() == Qt.Key_Down:
            self.downPressed()
        return super(LineEditKeyboard, self).keyPressEvent(event)
        
    def upPressed(self):
        self.keyUpPressed.emit()

    def downPressed(self):
        self.keyDownPressed.emit()


class LeftPanel(QWidget):
    def __init__(self, parent=None):
        super(LeftPanel, self).__init__(parent)
        self.ui = Ui_LeftPanel()
        self.ui.setupUi(self)
        self.mainWindow = parent
        self.importer = self.mainWindow.importer
        
        # Naming convenience
        self.filterTypeDropDown = self.ui.filterTypeDropDown
        self.filterSortDropDown = self.ui.filterSortDropDown
        self.filterSortDirDropDown = self.ui.filterSortDirDropDown
        self.filterSearchBar = self.ui.filterSearchBar
        self.filterListAlpha = self.ui.filterListAlpha
        self.filterListBeta = self.ui.filterListBeta
        self.tagListAlpha = self.ui.tagListAlpha
        self.tagListBeta = self.ui.tagListBeta
        # self.tagSearchBar = self.ui.tagSearchBar
        self.tagTypeDropDown = self.ui.tagTypeDropDown
        self.tagSortDropDown = self.ui.tagSortDropDown
        self.tagSortDirDropDown = self.ui.tagSortDirDropDown

        # UI layout setup
        self.tagSearchBar = LineEditKeyboard(self.ui.tagTab)
        self.tagSearchBar.setText("")
        self.tagSearchBar.setClearButtonEnabled(True)
        self.tagSearchBar.setObjectName("tagSearchBar")
        self.ui.tagTabVertLayout.insertWidget(2, self.tagSearchBar)

        _translate = QCoreApplication.translate
        self.tagSearchBar.setToolTip(_translate("LeftPanel", "<html><head/><body><p><span style=\" font-size:9pt;\">Search list of tags. Press enter to apply tag in search box, even if it doesn\'t exist yet</span></p></body></html>"))
        self.tagSearchBar.setPlaceholderText(_translate("LeftPanel", "Search tags"))

        # Signals
        self.filterTypeDropDown.currentTextChanged['QString'].connect(self.filterListBetaUpdate)
        self.filterSortDropDown.currentTextChanged['QString'].connect(self.filterListBetaUpdate)
        self.filterSortDirDropDown.currentTextChanged['QString'].connect(self.filterListBetaUpdate)
        self.filterListAlpha.doubleClicked['QModelIndex'].connect(self.filterListAlphaDoubleClicked)
        self.filterListBeta.doubleClicked['QModelIndex'].connect(self.filterListBetaDoubleClicked)
        self.filterSearchBar.textChanged['QString'].connect(self.filterSearchBarTextChanged)
        # self.filterSearchBar.returnPressed.connect(self.filterSearchBarReturnPressed)  # Don't see need for this input as of right now
        self.tagSearchBar.textChanged['QString'].connect(self.tagSearchBarTextChanged)
        self.tagSearchBar.returnPressed.connect(self.tagSearchBarReturnPressed)
        self.tagListAlpha.doubleClicked['QModelIndex'].connect(self.tagListAlphaDoubleClicked)
        self.tagListBeta.doubleClicked['QModelIndex'].connect(self.tagListBetaDoubleClicked)
        self.tagTypeDropDown.currentTextChanged['QString'].connect(self.tagListUpdate)
        self.tagSortDropDown.currentTextChanged['QString'].connect(self.tagListUpdate)
        self.tagSortDirDropDown.currentTextChanged['QString'].connect(self.tagListUpdate)

        # Initialization
        self.tagSearchBar.keyUpPressed.connect(self.tagSearchUp)
        self.tagSearchBar.keyDownPressed.connect(self.tagSearchDown)
        self.tagType = 0
        self.tagFilterSet = set()
        self.filterListAlphaModel = FilterListTableModel()
        self.filterListBetaUpdate()
        self.tagListBetaUpdate()

    def tagSearchUp(self):
        index = self.tagListBeta.currentIndex()
        if index.isValid() and index.row() > 0:
            self.tagListBeta.setCurrentIndex(index.siblingAtRow(index.row()-1))
        else:
            self.tagListBeta.setCurrentIndex(index.sibling(-1, 1))

    def tagSearchDown(self):
        index = self.tagListBeta.currentIndex()
        if index.isValid() and index.row() < self.tagListBeta.model().rowCount() - 1:
            self.tagListBeta.setCurrentIndex(index.siblingAtRow(index.row()+1))
        else:
            self.tagListBeta.setCurrentIndex(self.tagListBeta.model().index(0, 1))

    def filterListAlphaDoubleClicked(self):
        '''
        Remove row from filterListAlpha and update videoTable when filterListAlpha is double clicked
        '''
        row = self.filterListAlpha.currentIndex().row()
        self.filterListAlphaModel.removeFilter(row)
        self.filterListUpdate()
        self.mainWindow.videoTableUpdate(self.filterListAlphaModel.getFilters())
    
    def filterListBetaDoubleClicked(self):
        '''
        Update videoTable and filterListAlpha when item in filterListBeta is double clicked
        '''
        filterName = self.filterListBeta.currentIndex().siblingAtColumn(0).data()
        displayName = self.filterListBeta.currentIndex().siblingAtColumn(1).data()
        categoryIndex = self.filterTypeDropDown.currentIndex()
        self.filterListAlphaModel.insertFilter(filterName, displayName, categoryIndex)
        self.filterListUpdate()
        self.mainWindow.videoTableUpdate(self.filterListAlphaModel.getFilters())

    def filterSearchBarTextChanged(self):
        self.filterListBetaUpdate()

    def tagSearchBarTextChanged(self):
        self.tagListBetaUpdate()
        # self.tagListBeta.selectionModel().setCurrentIndex(0, QItemSelectionModel.Select)

    def tagSearchBarReturnPressed(self):
        if not self.mainWindow.videoTableHasSelection():
            return
        elif self.tagListBeta.selectionModel().hasSelection():
            tag_name = self.tagListBeta.currentIndex().siblingAtColumn(0).data()
        elif len(self.tagSearchBar.text()) == 0:
            return
        else:
            tag_name = self.tagSearchBar.text()
        video_ids = self.mainWindow.getVideoTableSelectionVideoIds()
        self.importer.addVideoTags(video_ids, [tag_name], yt_tags=self.tagType)
        self.tagSearchBar.clear()
        self.filterListUpdate()
        self.tagListUpdate()

    def tagListAlphaDoubleClicked(self):
        tag_name = self.tagListAlpha.currentIndex().siblingAtColumn(0).data()
        video_ids = self.mainWindow.getVideoTableSelectionVideoIds()
        self.importer.removeVideoTags(video_ids, [tag_name], yt_tags=self.tagType)
        self.tagListUpdate()

    def tagListBetaDoubleClicked(self):
        tag_name = self.tagListBeta.currentIndex().siblingAtColumn(0).data()
        video_ids = self.mainWindow.getVideoTableSelectionVideoIds()
        self.importer.addVideoTags(video_ids, [tag_name], yt_tags=self.tagType)
        self.tagListUpdate()

    def filterListUpdate(self):
        self.filterListAlphaUpdate()
        self.filterListBetaUpdate()

    def filterListAlphaUpdate(self):
        '''
        Updates filterListAlpha for sorting values and to send rows to videoTable
        '''
        pmodel = QSortFilterProxyModel()
        pmodel.setSourceModel(self.filterListAlphaModel)
        pmodel.sort(3, Qt.AscendingOrder)
        self.filterListAlpha.setModel(pmodel)
        self.filterListAlpha.setModelColumn(3)
        self.filterListAlpha.show()        

    def filterListBetaUpdate(self):
        '''
        Update filterListBeta to select the filters of category categoryIndex
        Displays the name of the filter with the count of how many videos the filter applies to
        '''
        filterDicts = {"select": ["A.playlist_id, B.playlist_title, ct, B.playlist_title",
                                  "A.channel_id, B.channel_title, ct, B.channel_title",
                                  "tag_name, tag_name, ct, tag_name",
                                  "tag_name, tag_name, ct, tag_name"],
                       "filterId": ["playlist_id", "channel_id",
                                    "tag_name", "tag_name"],
                       "filterName": ["B.playlist_title", "B.channel_title",
                                      "tag_name", "tag_name"],
                       "table": ["videos_playlists_link", "videos",
                                 "videos_tags_link", "videos_yt_tags_link"],
                       "innerJoin": [" A\nINNER JOIN playlists B ON\nA.playlist_id = B.playlist_id",
                                     " A\nINNER JOIN channels B ON\nA.channel_id = B.channel_id",
                                     "", ""],
                        "ct": ["ct", "ct", "ct", "ct"]  # Looks stupid for the purpose of matching the rest of the data structure
        }
        sort = ["filterName", "ct"]
        sortDir = ["ASC", "DESC"]
        categoryIndex = self.filterTypeDropDown.currentIndex()
        sortStr = filterDicts[sort[self.filterSortDropDown.currentIndex()]][categoryIndex]
        sortDirStr = sortDir[self.filterSortDirDropDown.currentIndex()]

        queryTemplate = f"""SELECT {filterDicts['select'][categoryIndex]} || '  (' || ct || ')'
                            FROM (
                                SELECT {filterDicts['filterId'][categoryIndex]}, count(*) as ct
                                FROM {filterDicts['table'][categoryIndex]}
                                GROUP BY 1
                            ){filterDicts['innerJoin'][categoryIndex]}
                            WHERE {filterDicts['filterName'][categoryIndex]} LIKE (?)
                            ORDER BY {sortStr} {sortDirStr}"""

        filterSearch = self.filterSearchBar.text()
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(f"%{filterSearch}%")
        query.exec()
        model = QSqlQueryModel()
        model.setQuery(query)
        pmodel = FilterProxyModel()
        pmodel.setSourceModel(model)
        filteredSets = self.filterListAlphaModel.getFilterSets()
        pmodel.setFilteredSet(filteredSets[categoryIndex])

        self.filterListBeta.setModel(pmodel)
        self.filterListBeta.setModelColumn(3)
        self.filterListBeta.show()

    def tagListUpdate(self):
        self.tagType = self.tagTypeDropDown.currentIndex()
        self.tagListAlphaUpdate()
        self.tagListBetaUpdate()

    def tagListAlphaUpdate(self):
        video_ids = self.mainWindow.getVideoTableSelectionVideoIds()
        typesLink = ["videos_tags_link", "videos_yt_tags_link"]
        sort = ["T.tag_name", "ct"]
        sortDir = ["ASC", "DESC"]
        queryTemplate = f"""SELECT T.tag_name, T.tag_name || '  (' || IFNULL(ct, 0) || ')', ct
                            FROM (
                                SELECT tag_name FROM {typesLink[self.tagType]}
                                WHERE video_id IN ({', '.join(['(?)' for video_id in video_ids])})
                                GROUP BY tag_name
                                HAVING count(*) = (?)
                            ) T LEFT JOIN (
                                SELECT tag_name, count(*) as ct
                                FROM {typesLink[self.tagType]}
                                GROUP BY 1
                            ) C
                            ON T.tag_name = C.tag_name
                            ORDER BY {sort[self.tagSortDropDown.currentIndex()]} {sortDir[self.tagSortDirDropDown.currentIndex()]}"""
        query = QSqlQuery()
        query.prepare(queryTemplate)
        for video_id in video_ids:
            query.addBindValue(video_id)
        query.addBindValue(len(video_ids))
        query.exec()
        self.tagFilterSet = set()
        while query.next():
            self.tagFilterSet.add(query.value(0))
        model = QSqlQueryModel()
        model.setQuery(query)
        self.tagListAlpha.setModel(model)
        self.tagListAlpha.setModelColumn(1)
        self.tagListAlpha.show()

    def tagListBetaUpdate(self):
        types = ["tags", "yt_tags"]
        typesLink = ["videos_tags_link", "videos_yt_tags_link"]
        sort = ["T.tag_name", "ct"]
        sortDir = ["ASC", "DESC"]
        queryTemplate = f"""SELECT T.tag_name, T.tag_name || '  (' || IFNULL(ct, 0) || ')', ct
                            FROM {types[self.tagType]} T LEFT JOIN (
                                SELECT tag_name, count(*) as ct
                                FROM {typesLink[self.tagType]}
                                GROUP BY 1
                                ) C
                            ON T.tag_name = C.tag_name
                            WHERE T.tag_name LIKE (?)
                            ORDER BY {sort[self.tagSortDropDown.currentIndex()]} {sortDir[self.tagSortDirDropDown.currentIndex()]}"""
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(f"%{self.tagSearchBar.text()}%")
        query.exec()
        model = QSqlQueryModel()
        model.setQuery(query)
        pmodel = FilterProxyModel()
        pmodel.setSourceModel(model)
        pmodel.setFilteredSet(self.tagFilterSet)
        self.tagListBeta.setModel(pmodel)
        self.tagListBeta.setModelColumn(1)
        self.tagListBeta.show()


class FilterListTableModel(QAbstractTableModel):
    '''
    Custom subclass of QAbstractTableModel for use in filterListAlpha
    '''
    def __init__(self):
        super().__init__()
        self.headers = ["filterId", "filterName", "categoryIndex", "displayText"]
        self.rows = []
        # Hard coded number needs to be changed if number of categories changes
        self.filterSets = {0: set(),
                           1: set(),
                           2: set(),
                           3: set()}

    def rowCount(self, parent):
        return len(self.rows)

    def columnCount(self, parent):
        return len(self.headers)

    def data(self, index, role):
        '''
        Return data at index
        '''
        if role != Qt.DisplayRole:
            return QVariant()
        return self.rows[index.row()][index.column()]

    def insertFilter(self, filterId, filterName, categoryIndex):
        '''
        Custom API to insert row into model
        '''
        # Hard coded categories needs to be changed if cats change
        categories = ["playlist->", "channel->", "tag->", "yt_tag->"]
        self.beginInsertRows(QModelIndex(), self.rowCount(QModelIndex()), self.rowCount(QModelIndex()))
        self.rows.append((filterId, filterName, categoryIndex, categories[categoryIndex] + filterName))
        self.filterSets[categoryIndex].add(filterId)
        self.endInsertRows()

    def removeFilter(self, row):
        '''
        Custom API to remove row from model
        '''
        self.beginRemoveRows(QModelIndex(), row, row)
        filterId, categoryIndex = self.rows[row][0], self.rows[row][2]
        del self.rows[row]
        self.filterSets[categoryIndex].remove(filterId)
        self.endRemoveRows()

    def getFilters(self):
        '''
        Returns copy of internal rows
        '''
        filters = [(r[0], r[2]) for r in self.rows]
        return filters

    def getFilterSets(self):
        '''
        Returns copy of internal filterSets dictionary
        '''
        filterSets = dict()
        for categoryIndex, fSet in self.filterSets.items():
            filterSets[categoryIndex] = set()
            for f in fSet:
                filterSets[categoryIndex].add(f)
        return filterSets
