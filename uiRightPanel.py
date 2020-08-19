# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/rightPanel.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RightPanel(object):
    def setupUi(self, RightPanel):
        RightPanel.setObjectName("RightPanel")
        RightPanel.resize(300, 720)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(RightPanel.sizePolicy().hasHeightForWidth())
        RightPanel.setSizePolicy(sizePolicy)
        self.rightPanelVertLayout = QtWidgets.QVBoxLayout(RightPanel)
        self.rightPanelVertLayout.setContentsMargins(6, 0, 0, 0)
        self.rightPanelVertLayout.setObjectName("rightPanelVertLayout")
        self.thumbnail = QtWidgets.QLabel(RightPanel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.thumbnail.sizePolicy().hasHeightForWidth())
        self.thumbnail.setSizePolicy(sizePolicy)
        self.thumbnail.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.thumbnail.setText("")
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.thumbnail.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.thumbnail.setObjectName("thumbnail")
        self.rightPanelVertLayout.addWidget(self.thumbnail)
        self.videoDetails = QtWidgets.QTextBrowser(RightPanel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.videoDetails.sizePolicy().hasHeightForWidth())
        self.videoDetails.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.videoDetails.setFont(font)
        self.videoDetails.setOpenExternalLinks(True)
        self.videoDetails.setObjectName("videoDetails")
        self.rightPanelVertLayout.addWidget(self.videoDetails)
        self.notes = QtWidgets.QTextEdit(RightPanel)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.notes.sizePolicy().hasHeightForWidth())
        self.notes.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.notes.setFont(font)
        self.notes.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextEditable|QtCore.Qt.TextEditorInteraction|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.notes.setObjectName("notes")
        self.rightPanelVertLayout.addWidget(self.notes)
        self.notesSaveButton = QtWidgets.QPushButton(RightPanel)
        self.notesSaveButton.setObjectName("notesSaveButton")
        self.rightPanelVertLayout.addWidget(self.notesSaveButton)

        self.retranslateUi(RightPanel)
        QtCore.QMetaObject.connectSlotsByName(RightPanel)

    def retranslateUi(self, RightPanel):
        _translate = QtCore.QCoreApplication.translate
        RightPanel.setWindowTitle(_translate("RightPanel", "Form"))
        self.notes.setPlaceholderText(_translate("RightPanel", "Notes"))
        self.notesSaveButton.setText(_translate("RightPanel", "Save notes"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    RightPanel = QtWidgets.QWidget()
    ui = Ui_RightPanel()
    ui.setupUi(RightPanel)
    RightPanel.show()
    sys.exit(app.exec_())
