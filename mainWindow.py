from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QSplitter, QApplication
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel 
from uiMainWindow import Ui_MainWindow
from leftPanel import LeftPanel
from rightPanel import RightPanel
from tagManager import TagManager
from videoImporter import VideoImporter
from dbSchema import initializeDb

'''
Main Window UI contents
videoTable = QTableView
'''
DBPATH = "saved.db"

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.connectDatabase(DBPATH)
        self.importer = VideoImporter()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Naming convenience
        self.videoTable = self.ui.videoTable
        self.tableSearchBar = self.ui.tableSearchBar
        self.menubar = self.ui.menubar
        self.actionImport_playlists = self.ui.actionImport_playlists
        self.actionManage_tags = self.ui.actionManage_tags
        self.tableSortDropDown = self.ui.tableSortDropDown
        self.tableSortDirDropDown = self.ui.tableSortDirDropDown

        # UI layout setup
        self.horizontalLayout = QHBoxLayout(self.ui.mainWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QSplitter(self.ui.mainWidget)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.leftPanel = LeftPanel(self)
        self.splitter.addWidget(self.leftPanel)
        self.splitter.addWidget(self.ui.centralPanel)
        self.rightPanel = RightPanel(self)
        self.splitter.addWidget(self.rightPanel)
        self.horizontalLayout.addWidget(self.splitter)

        # Initialization
        self.launch = False  # Track first panel update
        self.videoTableUpdate()
        self.lastUsedFilters = []

        # Signals
        self.splitter.splitterMoved.connect(self.rightPanel.thumbnailUpdate)
        self.actionImport_playlists.triggered.connect(self.importPlaylists)
        self.actionManage_tags.triggered.connect(self.openTagManager)
        self.tableSearchBar.returnPressed.connect(self.tableUpdateTriggered)
        self.tableSortDropDown.currentTextChanged['QString'].connect(self.tableUpdateTriggered)
        self.tableSortDirDropDown.currentTextChanged['QString'].connect(self.tableUpdateTriggered)

    def connectDatabase(self, path):
        '''
        Connect to SQLite database
        '''
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        initializeDb(DBPATH, self.db)

    def openTagManager(self):
        tagManager = TagManager(self)
        tagManager.exec()
        self.leftPanel.filterListUpdate()
        self.leftPanel.tagListUpdate()

    def videoTableUpdate(self, filters=[]):
        '''
        Generate SQL query from filters (filterName, categoryIndex)
        '''
        tableSorts = ["publish_date", "save_date", "video_title", "C.channel_title"]
        sortDirs = ["ASC", "DESC"]

        self.lastUsedFilters = filters
        queries = []
        search = self.tableSearchBar.text()
        query = QSqlQuery()

        if len(filters) == 0 and len(search) == 0:
            queryTemplate = """SELECT video_id, video_title, publish_date, save_date, C.channel_title
                               FROM videos V INNER JOIN channels C
                               ON V.channel_id = C.channel_id
                               ORDER BY """ + f"{tableSorts[self.tableSortDropDown.currentIndex()]} {sortDirs[self.tableSortDirDropDown.currentIndex()]}"
            query.prepare(queryTemplate)

        else:
            if len(filters) > 0:
                filterTables = ["videos_playlists_link", "videos", "videos_tags_link", "videos_yt_tags_link"]
                filterColumns = ["playlist_id", "channel_id", "tag_name", "tag_name"]
                # queryTemplates = ["SELECT video_id FROM videos_playlists_link WHERE playlist_id = (?)",
                #                   "SELECT video_id FROM videos WHERE channel_id = (?)",
                #                   "SELECT video_id FROM videos_tags_link WHERE tag_name = (?)",
                                  # "SELECT video_id FROM videos_yt_tags_link WHERE tag_name = (?)"]
                selections = []
                for filterName, categoryIndex in filters:
                    selections.append(f"SELECT video_id FROM {filterTables[categoryIndex]} WHERE {filterColumns[categoryIndex]} = (?)")
                    # selections.append(queryTemplates[categoryIndex])
                queryTemplate = "\nINTERSECT\n".join(selections)
                queryTemplate = """SELECT video_id, video_title, publish_date, save_date, C.channel_title
                                   FROM videos V INNER JOIN channels C
                                   ON V.channel_id = C.channel_id
                                   WHERE video_id IN (\n""" + queryTemplate + "\n)"
                queries.append(queryTemplate)

            if len(search) > 0:
                searchQuery = """SELECT video_id FROM videos WHERE channel_id IN (
                                 SELECT channel_id FROM channels WHERE channel_title LIKE (?)
                                 )
                                 UNION
                                 SELECT video_id FROM videos_playlists_link WHERE playlist_id IN (
                                     SELECT playlist_id FROM playlists WHERE playlist_title LIKE (?)
                                 )
                                 UNION
                                 SELECT video_id FROM videos WHERE video_title LIKE (?) OR description LIKE (?) OR notes LIKE (?)
                                 UNION
                                 SELECT video_id FROM videos_tags_link WHERE tag_name LIKE (?)
                                 UNION
                                 SELECT video_id FROM videos_yt_tags_link WHERE tag_name LIKE (?)"""
                searchQuery = """SELECT video_id, video_title, publish_date, save_date, C.channel_title
                                 FROM videos V INNER JOIN channels C
                                 ON V.channel_id =C.channel_id
                                 WHERE video_id IN (\n""" + searchQuery + "\n)"
                queries.append(searchQuery)

            preQuery = "\nINTERSECT\n".join(queries) + f"\nORDER BY {tableSorts[self.tableSortDropDown.currentIndex()]} {sortDirs[self.tableSortDirDropDown.currentIndex()]}"
            query.prepare(preQuery)

            if len(filters) > 0:
                for filterName, categoryIndex in filters:
                    query.addBindValue(filterName)

            if len(search) > 0:
                for _ in range(7):
                    query.addBindValue(f"%{search}%")

        query.exec()
        self.videoTableQuery(query)

    def tableUpdateTriggered(self):
        self.videoTableUpdate(self.lastUsedFilters)

    def videoTableQuery(self, query):
        '''
        Updates videoTable with query
        '''
        model = QSqlQueryModel()
        model.setQuery(query)
        self.videoTable.setModel(model)
        self.videoTable.show()

        if self.launch is False:  # Shitty fix to prevent inconsistent behavior when launching
            self.launch = True
        else:
            self.videoTable.selectRow(0)

        self.videoTable.selectionModel().selectionChanged.connect(self.videoTableSelectionChanged)  # Not placed under signals because selectionModel changes
        self.videoTableSelectionChanged()

    def videoTableSelectionChanged(self):
        '''
        Updates tagListAlpha with list of selected video_ids when selection changes
        '''
        # update preview panel with currentIndex()
        self.leftPanel.tagListUpdate()
        self.rightPanel.panelUpdate()

    def getVideoTableSelectionVideoIds(self):
        return [index.data() for index in self.videoTable.selectionModel().selectedRows(0)]

    def videoTableHasSelection(self):
        return self.videoTable.selectionModel().hasSelection()

    def getVideoTableCurrentVideo(self):
        # rewrite to allow for table custom view
        video_id = self.videoTable.selectionModel().currentIndex().siblingAtColumn(0).data()
        query = QSqlQuery()
        query.prepare("SELECT * FROM videos WHERE video_id = (?)")
        query.addBindValue(video_id)
        query.exec()
        query.first()
        video = [query.value(0),
                 query.value(1),
                 query.value(2),
                 query.value(3),
                 query.value(4),
                 query.value(5),
                 query.value(6)]
        return video

    def importPlaylists(self):
        self.importer.importVideosFromAllPlaylists()
        self.leftPanel.filterListBetaUpdate()
        self.videoTableUpdate()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = MainWindow()
    MainWindow.show()
    sys.exit(app.exec_())

'''
TODO LIST
finish filter sorting
rich text editor -> tabs? dialog for editting?
ignored videos table
rename tag feature in tag manager
    create new tag -> add new tag to videos in link -> delete tag from link -> delete from tags
parent tag:
    when adding tag, check up parent tree and add all ancestor tags
    when adding parent child relationship, check for cycle
    when deleting tag, -> delete relationship -> delete from videos_tags_link -> delete from tags
    should deleted tag's parents and children be linked?
tag autocomplete
import video duration
display video duration
'''
