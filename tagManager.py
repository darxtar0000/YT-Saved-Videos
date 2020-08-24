from PyQt5.QtWidgets import QDialog
from PyQt5.QtSql import QSqlQuery, QSqlQueryModel
from uiTagManager import Ui_TagManager
from filterProxyModel import FilterProxyModel

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
        self.tagSortDropDown.currentTextChanged['QString'].connect(self.tagListsUpdate)
        self.tagSortDirDropDown.currentTextChanged['QString'].connect(self.tagListsUpdate)

        self.tagSearchBar.textChanged['QString'].connect(self.tagSearchBarTextChanged)
        self.tagSearchBar.returnPressed.connect(self.tagSearchBarReturnPressed)
        self.newTagName.textChanged['QString'].connect(self.renameTagButtonUpdate)
        self.removeTagButton.clicked.connect(self.removeTagButtonClicked)
        self.renameTagButton.clicked.connect(self.renameTagButtonClicked)

        self.parentTagSearchBar.textChanged['QString'].connect(self.parentTagListAlphaUpdate)
        self.parentTagListAlpha.doubleClicked.connect(self.parentTagListAlphaDoubleClicked)
        self.parentTagListBeta.doubleClicked.connect(self.parentTagListBetaDoubleClicked)

        self.okButton.clicked.connect(self.okButtonClicked)
        self.applyButton.clicked.connect(self.applyButtonClicked)
        self.cancelButton.clicked.connect(self.cancelButtonClicked)

        # Initialization
        self.tagType = 0
        self.childTag = ""
        self.parentTags = set()
        self.removeTagButton.setDisabled(True)
        self.renameTagButton.setDisabled(True)
        self.beginTransaction()
        self.tagListUpdate()
        self.parentTagListAlphaUpdate()

    def beginTransaction(self):
        return self.db.transaction()

    def tagTypeDropDownChanged(self):
        self.tagType = self.tagTypeDropDown.currentIndex()
        self.tagListsUpdate()

    def tagSearchBarTextChanged(self):
        self.tagListUpdate()
        self.removeTagButtonUpdate()

    def tagSearchBarReturnPressed(self):
        tagName = self.tagSearchBar.text()
        if len(tagName) == 0:
            return
        self.importer.addTags([tagName], yt_tags=self.tagType)
        self.tagListUpdate()

    def removeTagButtonClicked(self):
        tagList = [index.siblingAtColumn(0).data() for index in self.tagList.selectionModel().selectedIndexes()]
        self.importer.removeTags(tagList, yt_tags=self.tagType)
        self.tagListUpdate()
        self.tagListSelectionChanged()

    def renameTagButtonClicked(self):
        self.importer.renameTag(self.childTag, self.newTagName.text(), yt_tags=self.tagType)
        self.newTagName.clear()
        self.tagListUpdate()
        self.oldTagNameUpdate()

    def parentTagListAlphaDoubleClicked(self):
        parentTag = self.parentTagListAlpha.currentIndex().siblingAtColumn(0).data()
        self.importer.addParentChild(parentTag, self.childTag, yt_tags=self.tagType)
        self.updateSelectedChildParent()
        self.parentTagListAlphaUpdate()
        self.parentTagListBetaUpdate()

    def parentTagListBetaDoubleClicked(self):
        parentTag = self.parentTagListBeta.currentIndex().siblingAtColumn(0).data()
        self.importer.removeParentChild(parentTag, self.childTag, yt_tags=self.tagType)
        self.updateSelectedChildParent()
        self.parentTagListAlphaUpdate()
        self.parentTagListBetaUpdate()

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
        self.tagList.selectionModel().selectionChanged.connect(self.tagListSelectionChanged)

    def updateSelectedChildParent(self):
        parents = ["tags_parent", "yt_tags_parent"]
        queryTemplate = f"""SELECT parent_tag FROM {parents[self.tagType]} WHERE child_tag = (?)"""
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(self.tagList.currentIndex().siblingAtColumn(0).data())
        query.exec()
        parentTags = set()
        while query.next():
            parentTags.add(query.value(0))
        self.parentTags = parentTags
        self.childTag = self.tagList.currentIndex().siblingAtColumn(0).data()

    def tagListSelectionChanged(self):
        self.updateSelectedChildParent()
        self.removeTagButtonUpdate()
        self.oldTagNameUpdate()
        self.parentTagListAlphaUpdate()
        self.parentTagListBetaUpdate()

    def oldTagNameUpdate(self):
        self.oldTagName.setText(self.childTag)

    def removeTagButtonUpdate(self):
        if self.tagList.selectionModel().hasSelection():
            self.removeTagButton.setEnabled(True)
        else:
            self.removeTagButton.setDisabled(True)

    def renameTagButtonUpdate(self):
        if self.tagList.selectionModel().hasSelection() and len(self.newTagName.text()) > 0:
            self.renameTagButton.setEnabled(True)
        else:
            self.renameTagButton.setDisabled(True)

    def parentTagListAlphaUpdate(self):
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
        searchText = self.parentTagSearchBar.text()
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(f"%{searchText}%")
        query.exec()
        model = QSqlQueryModel()
        model.setQuery(query)
        pmodel = FilterProxyModel()
        pmodel.setSourceModel(model)
        filteredSet = self.parentTags
        filteredSet.add(self.childTag)
        pmodel.setFilteredSet(filteredSet)
        self.parentTagListAlpha.setModel(pmodel)
        self.parentTagListAlpha.setModelColumn(1)
        self.parentTagListAlpha.show()

    def parentTagListBetaUpdate(self):
        typesLink = ["videos_tags_link", "videos_yt_tags_link"]
        parents = ["tags_parent", "yt_tags_parent"]
        sort = ["P.parent_tag", "ct"]
        sortDir = ["ASC", "DESC"]
        queryTemplate = f"""SELECT P.parent_tag, P.parent_tag || '  (' || IFNULL(ct, 0) || ')', ct
                            FROM (
                                SELECT parent_tag
                                FROM {parents[self.tagType]}
                                WHERE child_tag = (?)
                                GROUP BY 1
                            ) P LEFT JOIN (
                                SELECT tag_name, count(*) as ct
                                FROM {typesLink[self.tagType]}
                                WHERE tag_name = (?)
                                GROUP BY 1
                            ) C
                            ON P.parent_tag = C.tag_name
                            ORDER BY {sort[self.tagSortDropDown.currentIndex()]} {sortDir[self.tagSortDirDropDown.currentIndex()]}"""
        query = QSqlQuery()
        query.prepare(queryTemplate)
        childTag = self.childTag
        query.addBindValue(childTag)
        query.addBindValue(childTag)
        query.exec()
        model = QSqlQueryModel()
        model.setQuery(query)
        self.parentTagListBeta.setModel(model)
        self.parentTagListBeta.setModelColumn(1)
        self.parentTagListBeta.show()

    def tagListsUpdate(self):
        self.tagListUpdate()
        self.parentTagListAlphaUpdate()
        self.parentTagListBetaUpdate()

    def okButtonClicked(self):
        self.db.commit()
        self.accept()

    def applyButtonClicked(self):
        return self.db.commit()

    def cancelButtonClicked(self):
        self.db.rollback()
        self.reject()


'''
Shit to wire up:
tagChildDropDown -> filter tagList for only tags that have parents
(DONE) oldTagName -> set to current selected tag in tagList
(DONE) newTagName -> gray out renameTag if empty
(DONE) renameTagButton -> send old tag name and new tag name to importer
(DONE) parentTagSearchBar -> filter parentTagListAlpha

(DONE) parentTagListAlpha -> double click to add parent child tag relationship, update parentTagListBeta
(DONE) CHECK FOR CYCLES
(DONE) parentTagListBeta -> double click to remove parent child tag relationship, update parentTagListAlpha

(DONE) parentTagListAlphaUpdate
(DONE) parentTagListBetaUpdate

(DONE) (update importer to add recursively add parent tags)
'''
