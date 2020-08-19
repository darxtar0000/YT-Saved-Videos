from PyQt5.QtWidgets import QDialog
from PyQt5.QtSql import QSqlQuery, QSqlQueryModel
from uiTagManager import Ui_TagManager

class TagManager(QDialog):
    def __init__(self, mainWindow=None):
        super(TagManager, self).__init__()
        self.ui = Ui_TagManager()
        self.ui.setupUi(self)
        self.mainWindow = mainWindow
        self.db = self.mainWindow.db
        self.importer = self.mainWindow.importer

        # Naming convenience
        self.tagChildDropDown = self.ui.tagChildDropDown
        self.tagTypeDropDown = self.ui.tagTypeDropDown
        self.tagSortDropDown = self.ui.tagSortDropDown
        self.tagSortDirDropDown = self.ui.tagSortDirDropDown

        self.tagSearchBar = self.ui.tagSearchBar
        self.tagList = self.ui.tagList
        self.oldTagName = self.ui.oldTagName
        self.newTagName = self.ui.newTagName
        self.removeTagButton = self.ui.removeTagButton
        self.renameTagButton = self.ui.renameTagButton

        self.parentTagSearchBar = self.ui.parentTagSearchBar
        self.parentTagListAlpha = self.ui.parentTagListAlpha
        self.parentTagListBeta = self.ui.parentTagListBeta

        self.okButton = self.ui.okButton
        self.applyButton = self.ui.applyButton
        self.cancelButton = self.ui.cancelButton

        # Signals
        self.tagTypeDropDown.currentTextChanged['QString'].connect(self.tagTypeDropDownChanged)
        self.tagSortDropDown.currentTextChanged['QString'].connect(self.tagListUpdate)
        self.tagSortDirDropDown.currentTextChanged['QString'].connect(self.tagListUpdate)
        self.tagSearchBar.textChanged['QString'].connect(self.tagSearchBarTextChanged)
        self.tagSearchBar.returnPressed.connect(self.tagSearchBarReturnPressed)
        self.removeTagButton.clicked.connect(self.removeTagButtonClicked)
        self.okButton.clicked.connect(self.okButtonClicked)
        self.applyButton.clicked.connect(self.applyButtonClicked)
        self.cancelButton.clicked.connect(self.cancelButtonClicked)

        # Initialization
        self.tagType = 0
        self.removeTagButton.setDisabled(True)
        self.renameTagButton.setDisabled(True)
        self.oldTagName.setText("Old tag name")
        self.beginTransaction()
        self.tagListUpdate()

    def beginTransaction(self):
        return self.db.transaction()

    def tagTypeDropDownChanged(self):
        self.tagType = self.tagTypeDropDown.currentIndex()
        self.tagListUpdate()

    def tagSearchBarTextChanged(self):
        self.tagListUpdate()

    def tagSearchBarReturnPressed(self):
        tag_name = self.tagSearchBar.text()
        self.importer.addTags([tag_name], yt_tags=self.tagType)
        self.tagSearchBar.clear()
        self.tagListUpdate()

    def removeTagButtonClicked(self):
        tag_list = [index.siblingAtColumn(0).data() for index in self.tagList.selectionModel().selectedIndexes()]
        self.importer.removeTags(tag_list, yt_tags=self.tagType)
        self.tagListUpdate()

    def okButtonClicked(self):
        self.db.commit()
        self.accept()

    def applyButtonClicked(self):
        return self.db.commit()

    def cancelButtonClicked(self):
        self.db.rollback()
        self.reject()

    def tagListUpdate(self):
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
        searchText = self.tagSearchBar.text()
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(f"%{searchText}%")
        query.exec()
        model = QSqlQueryModel()
        model.setQuery(query)
        self.tagList.setModel(model)
        self.tagList.setModelColumn(1)
        self.tagList.show()
        self.tagList.selectionModel().selectionChanged.connect(self.removeTagButtonUpdate)

    def removeTagButtonUpdate(self):
        if self.tagList.selectionModel().hasSelection():
            self.removeTagButton.setEnabled(True)
        else:
            self.removeTagButton.setDisabled(True)


'''
Shit to wire up:
tagChildDropDown -> filter tagList for only tags that have parents
oldTagName -> set to current selected tag in tagList
newTagName -> gray out renameTag if empty
parentTagSearchBar -> filter parentTagListAlpha
parentTagListAlpha -> double click to add parent child tag relationship, update parentTagListBeta
    CHECK FOR CYCLES
parentTagListBeta -> double click to remove parent child tag relationship, update parentTagListAlpha

(update importer to add recursively add parent tags)
'''
