from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtSql import QSqlQuery
from uiRightPanel import Ui_RightPanel
import os
import re
from datetime import datetime

'''
Right Panel UI contents
thumbnail = QLabel
videoDetails = QTextBrowser
notes = QTextEdit
notesSaveButton = QPushButton
'''
VIDEO_ID = 0
VIDEO_TITLE = 1
DESCRIPTION = 2
PUBLISH_DATE = 3
SAVE_DATE = 4
CHANNEL_ID = 5
NOTES = 6

class RightPanel(QWidget):
    def __init__(self, mainWindow=None):
        super(RightPanel, self).__init__()
        self.ui = Ui_RightPanel()
        self.ui.setupUi(self)
        self.mainWindow = mainWindow
        self.importer = self.mainWindow.importer

        # Naming convenience
        self.thumbnail = self.ui.thumbnail
        self.videoDetails = self.ui.videoDetails
        self.notes = self.ui.notes
        self.notesSaveButton = self.ui.notesSaveButton

        # Initialization
        self.video = (None, None, None, None, None, None, None)
        self.thumbnail.setMinimumSize(1, 1)
        self.launch = False  # Track first panel update

        # Signals
        self.notesSaveButton.clicked.connect(self.notesSaveButtonClicked)

    def loadFile(self, fileName):
        newImage = QPixmap(fileName)
        if newImage.isNull():
            newImage = QPixmap("thumbnails/black480x360.jpg")
        cropRect = QRect(0, 45, 480, 270)
        croppedImage = newImage.copy(cropRect)
        self.thumbnail.setPixmap(croppedImage.scaledToWidth(self.thumbnail.width(), Qt.SmoothTransformation))

    def thumbnailUpdate(self):
        if None in self.video:
            self.thumbnail.clear()
            return
        self.loadFile(os.path.join("thumbnails/v/", self.video[VIDEO_ID] + ".jpg"))

    def videoDetailsUpdate(self):
        if None in self.video:
            self.videoDetails.clear()
            return
        publishDateTime = datetime.fromisoformat(self.video[PUBLISH_DATE].replace("Z", "+00:00"))
        saveDateTime = datetime.fromisoformat(self.video[SAVE_DATE].replace("Z", "+00:00"))
        dateFormat = "%b %d, %Y"
        publish_date = publishDateTime.strftime(dateFormat)
        save_date = saveDateTime.strftime(dateFormat)
        description = self.video[DESCRIPTION].replace("\n", "<br>")

        pattern = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        description = re.sub(pattern, r'<a href="\g<0>">\g<0></a>', description)

        # Changing all external SQL calls to QtSqlQueries to avoid locking
        channel_title = self.importer.getChannelTitle(self.video[CHANNEL_ID])

        htmlText = f"""<h2 class="title style-scope ytd-video-primary-info-renderer"><a href="https://www.youtube.com/watch?v={self.video[VIDEO_ID]}">{self.video[VIDEO_TITLE]}</a></h2>
                       <div class="style-scope ytd-video-primary-info-renderer"><span id="dot" class="style-scope ytd-video-primary-info-renderer">Published: {publish_date}</span></div>
                       <div class="style-scope ytd-video-primary-info-renderer"><span class="style-scope ytd-video-primary-info-renderer">Saved: {save_date}</span></div>
                       <br>
                       <img src="thumbnails/c/{self.video[CHANNEL_ID] + ".jpg"}" alt="channel-thumbnail" width="45" height="45">
                       <h4 class="style-scope ytd-video-secondary-info-renderer"><a href="https://www.youtube.com/channel/{self.video[CHANNEL_ID]}">{channel_title}</a></h4>
                       <div class="style-scope ytd-video-secondary-info-renderer"><span class="style-scope yt-formatted-string" dir="auto">{description}</span></div>"""
        self.videoDetails.setHtml(htmlText)

    def notesUpdate(self):
        if None in self.video:
            self.notes.clear()
            return
        self.notes.setHtml(self.video[NOTES])


    def notesSaveButtonClicked(self):
        if None in self.video:
            return

        # Only used to reset notes with incorrect font size
        cursor = self.notes.textCursor()
        self.notes.selectAll()
        self.notes.setFontPointSize(10)
        self.notes.setTextCursor(cursor)

        # Save html to databse
        query = QSqlQuery()
        query.prepare("""UPDATE videos SET notes = (?) WHERE video_id = (?)""")
        query.addBindValue(self.notes.toHtml())
        query.addBindValue(self.video[VIDEO_ID])
        query.exec()

    def panelUpdate(self):
        if self.launch is False:  # Shitty fix to prevent first thumbnail when launching program to have width 100
            self.launch = True
            return
        self.video = self.mainWindow.getVideoTableCurrentVideo()
        self.thumbnailUpdate()
        self.videoDetailsUpdate()
        self.notesUpdate()

