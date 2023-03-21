# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'etlContral.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!
from lens import Lens
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *

class Ui_MainWindow(QMainWindow):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(400, 590)
        font = QtGui.QFont()
        font.setPointSize(9)
        MainWindow.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("C:/Users/holol/Desktop/icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")


        self.textBrowser_nD = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_nD.setGeometry(QtCore.QRect(280, 460, 70, 34))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.textBrowser_nD.setFont(font)
        self.textBrowser_nD.setObjectName("textBrowser_nD")


        self.label_step = QtWidgets.QLabel(self.centralwidget)
        self.label_step.setGeometry(QtCore.QRect(20, 210, 160, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_step.setFont(font)
        self.label_step.setObjectName("label_step")


        self.textEdit_minNum = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_minNum.setGeometry(QtCore.QRect(180, 170, 80, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.textEdit_minNum.setFont(font)
        self.textEdit_minNum.setObjectName("textEdit_minNum")


        self.label_minNum = QtWidgets.QLabel(self.centralwidget)
        self.label_minNum.setGeometry(QtCore.QRect(20, 170, 160, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_minNum.setFont(font)
        self.label_minNum.setObjectName("label_minNum")


        self.pushButton_reset = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_reset.setGeometry(QtCore.QRect(80, 360, 80, 30))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.pushButton_reset.setFont(font)
        self.pushButton_reset.setObjectName("pushButton_reset")

        self.pushButton_reset.clicked.connect(self.reset)


        self.label_nD = QtWidgets.QLabel(self.centralwidget)
        self.label_nD.setGeometry(QtCore.QRect(200, 460, 90, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_nD.setFont(font)
        self.label_nD.setObjectName("label_nD")


        self.textBrowser_temperature = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_temperature.setGeometry(QtCore.QRect(80, 510, 70, 34))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.textBrowser_temperature.setFont(font)
        self.textBrowser_temperature.setObjectName("textBrowser_temperature")


        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setGeometry(QtCore.QRect(0, 50, 400, 20))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")


        self.label_firmwareVersion = QtWidgets.QLabel(self.centralwidget)
        self.label_firmwareVersion.setGeometry(QtCore.QRect(30, 420, 81, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_firmwareVersion.setFont(font)
        self.label_firmwareVersion.setObjectName("label_firmwareVersion")


        self.label_inputFNum = QtWidgets.QLabel(self.centralwidget)
        self.label_inputFNum.setGeometry(QtCore.QRect(20, 70, 160, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_inputFNum.setFont(font)
        self.label_inputFNum.setObjectName("label_inputFNum")


        self.line_systemInformation = QtWidgets.QFrame(self.centralwidget)
        self.line_systemInformation.setGeometry(QtCore.QRect(0, 390, 400, 30))
        self.line_systemInformation.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_systemInformation.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_systemInformation.setObjectName("line_systemInformation")


        self.label_pD = QtWidgets.QLabel(self.centralwidget)
        self.label_pD.setGeometry(QtCore.QRect(20, 460, 90, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_pD.setFont(font)
        self.label_pD.setObjectName("label_pD")


        self.textBrowser_pD = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_pD.setGeometry(QtCore.QRect(110, 460, 70, 34))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.textBrowser_pD.setFont(font)
        self.textBrowser_pD.setObjectName("textBrowser_pD")


        self.label_lensSN = QtWidgets.QLabel(self.centralwidget)
        self.label_lensSN.setGeometry(QtCore.QRect(170, 510, 81, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_lensSN.setFont(font)
        self.label_lensSN.setObjectName("label_lensSN")


        self.pushButton_input = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_input.setGeometry(QtCore.QRect(290, 70, 80, 30))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.pushButton_input.setFont(font)
        self.pushButton_input.setObjectName("pushButton_input")

        self.pushButton_input.clicked.connect(self.getValueInput)

        self.label_showNum = QtWidgets.QLabel(self.centralwidget)
        self.label_showNum.setGeometry(QtCore.QRect(70, 310, 150, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_showNum.setFont(font)
        self.label_showNum.setObjectName("label_showNum")


        self.label_temperature = QtWidgets.QLabel(self.centralwidget)
        self.label_temperature.setGeometry(QtCore.QRect(20, 510, 51, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_temperature.setFont(font)
        self.label_temperature.setObjectName("label_temperature")


        self.label_cycle = QtWidgets.QLabel(self.centralwidget)
        self.label_cycle.setGeometry(QtCore.QRect(20, 250, 160, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_cycle.setFont(font)
        self.label_cycle.setObjectName("label_cycle")


        self.textEdit_cycle = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_cycle.setGeometry(QtCore.QRect(180, 250, 80, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.textEdit_cycle.setFont(font)
        self.textEdit_cycle.setObjectName("textEdit_cycle")


        self.textEdit_maxNum = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_maxNum.setGeometry(QtCore.QRect(180, 130, 80, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.textEdit_maxNum.setFont(font)
        self.textEdit_maxNum.setObjectName("textEdit_maxNum")


        self.pushButton_close = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_close.setGeometry(QtCore.QRect(260, 360, 80, 30))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.pushButton_close.setFont(font)
        self.pushButton_close.setObjectName("pushButton_close")


        self.line_cycleSystem = QtWidgets.QFrame(self.centralwidget)
        self.line_cycleSystem.setGeometry(QtCore.QRect(0, 280, 400, 30))
        self.line_cycleSystem.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_cycleSystem.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_cycleSystem.setObjectName("line_cycleSystem")


        self.textEdit_step = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_step.setGeometry(QtCore.QRect(180, 210, 80, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.textEdit_step.setFont(font)
        self.textEdit_step.setObjectName("textEdit_step")


        self.line_inputCycle = QtWidgets.QFrame(self.centralwidget)
        self.line_inputCycle.setGeometry(QtCore.QRect(0, 100, 400, 30))
        self.line_inputCycle.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_inputCycle.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_inputCycle.setObjectName("line_inputCycle")


        self.label_COM = QtWidgets.QLabel(self.centralwidget)
        self.label_COM.setGeometry(QtCore.QRect(20, 10, 200, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_COM.setFont(font)
        self.label_COM.setObjectName("label_COM")


        self.textBrowser_showNum = QtWidgets.QTextEdit(self.centralwidget)
        self.textBrowser_showNum.setGeometry(QtCore.QRect(260, 310, 80, 34))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.textBrowser_showNum.setFont(font)
        self.textBrowser_showNum.setObjectName("textBrowser_showNum")


        self.textBrowser_lensSN = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_lensSN.setGeometry(QtCore.QRect(260, 510, 100, 34))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.textBrowser_lensSN.setFont(font)
        self.textBrowser_lensSN.setObjectName("textBrowser_lensSN")


        self.label_maxNum = QtWidgets.QLabel(self.centralwidget)
        self.label_maxNum.setGeometry(QtCore.QRect(20, 130, 160, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.label_maxNum.setFont(font)
        self.label_maxNum.setObjectName("label_maxNum")


        self.pushButton_cycle = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_cycle.setGeometry(QtCore.QRect(290, 160, 80, 30))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.pushButton_cycle.setFont(font)
        self.pushButton_cycle.setObjectName("pushButton_cycle")

        self.pushButton_cycle.clicked.connect(self.getValueCycle)

        self.textBrowser_firmwareVersion = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_firmwareVersion.setGeometry(QtCore.QRect(120, 420, 231, 34))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.textBrowser_firmwareVersion.setFont(font)
        self.textBrowser_firmwareVersion.setObjectName("textBrowser_firmwareVersion")


        self.textEdit_inputFNum = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_inputFNum.setGeometry(QtCore.QRect(180, 70, 80, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.textEdit_inputFNum.setFont(font)
        self.textEdit_inputFNum.setObjectName("textEdit_inputFNum")

        self.textEdit_inputFNum.setText('0')


        self.textEdit_com = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_com.setGeometry(QtCore.QRect(240, 10, 60, 34))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.textEdit_com.setFont(font)
        self.textEdit_com.setObjectName("textEdit_com")

        self.textEdit_com.setText('3')

        self.pushButton_comOk = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_comOk.setGeometry(QtCore.QRect(320, 10, 50, 30))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.pushButton_comOk.setFont(font)
        self.pushButton_comOk.setObjectName("pushButton_comOk")


        self.pushButton_comOk.clicked.connect(self.getValueInfo)

        self.pushButton_cycleStop = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_cycleStop.setGeometry(QtCore.QRect(290, 220, 80, 30))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(13)
        self.pushButton_cycleStop.setFont(font)
        self.pushButton_cycleStop.setObjectName("pushButton_cycleStop")

        self.pushButton_cycleStop.clicked.connect(self.stopCycle)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 400, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)



        self.retranslateUi(MainWindow)
        self.pushButton_close.clicked.connect(MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.textEdit_com, self.pushButton_comOk)
        MainWindow.setTabOrder(self.pushButton_comOk, self.textEdit_inputFNum)
        MainWindow.setTabOrder(self.textEdit_inputFNum, self.pushButton_input)
        MainWindow.setTabOrder(self.pushButton_input, self.textEdit_maxNum)
        MainWindow.setTabOrder(self.textEdit_maxNum, self.textEdit_minNum)
        MainWindow.setTabOrder(self.textEdit_minNum, self.textEdit_step)
        MainWindow.setTabOrder(self.textEdit_step, self.textEdit_cycle)
        MainWindow.setTabOrder(self.textEdit_cycle, self.pushButton_cycle)
        MainWindow.setTabOrder(self.pushButton_cycle, self.pushButton_cycleStop)
        MainWindow.setTabOrder(self.pushButton_cycleStop, self.textBrowser_showNum)
        MainWindow.setTabOrder(self.textBrowser_showNum, self.pushButton_reset)
        MainWindow.setTabOrder(self.pushButton_reset, self.pushButton_close)
        MainWindow.setTabOrder(self.pushButton_close, self.textBrowser_firmwareVersion)
        MainWindow.setTabOrder(self.textBrowser_firmwareVersion, self.textBrowser_pD)
        MainWindow.setTabOrder(self.textBrowser_pD, self.textBrowser_nD)
        MainWindow.setTabOrder(self.textBrowser_nD, self.textBrowser_temperature)
        MainWindow.setTabOrder(self.textBrowser_temperature, self.textBrowser_lensSN)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Optotune Contral v1.0"))
        self.label_step.setText(_translate("MainWindow", "间  隔 STEP"))
        self.label_minNum.setText(_translate("MainWindow", "MIN Diopter"))
        self.pushButton_reset.setText(_translate("MainWindow", "RESET"))
        self.label_nD.setText(_translate("MainWindow", "- Diopter"))
        self.label_firmwareVersion.setText(_translate("MainWindow", "固件版本："))
        self.label_inputFNum.setText(_translate("MainWindow", "Diopter Input"))
        self.label_pD.setText(_translate("MainWindow", "+ Diopter"))
        self.label_lensSN.setText(_translate("MainWindow", "Lens SN："))
        self.pushButton_input.setText(_translate("MainWindow", "INPUT"))
        self.label_showNum.setText(_translate("MainWindow", "实时电流显示(mA)"))
        self.label_temperature.setText(_translate("MainWindow", "温度："))
        self.label_cycle.setText(_translate("MainWindow", "周  期 (s) CYCLE"))
        self.pushButton_close.setText(_translate("MainWindow", "CLOSE"))
        self.label_COM.setText(_translate("MainWindow", "COM选择 (填入数字即可)"))
        self.label_maxNum.setText(_translate("MainWindow", "MAX Diopter"))
        self.pushButton_cycle.setText(_translate("MainWindow", "CYCLE"))
        self.pushButton_comOk.setText(_translate("MainWindow", "OK"))
        self.pushButton_cycleStop.setText(_translate("MainWindow", "STOP"))

#define signal to geT Vale from self.testEdit_com
    def getValueInfo(self):
        com = self.textEdit_com.toPlainText()
        com = 'com'+str(com)
        if com:
            lens = Lens(com, debug=False)  # set debug to True to see a serial communication log

            if lens.comNum == 0:
                    QMessageBox.information(self,'Notice', u'请输入正确COM')
            elif lens.comNum == 1:

                self.clearAll()
                self.textBrowser_firmwareVersion.append(str(lens.firmware_version))
                self.textBrowser_lensSN.append( str(lens.lens_serial))
                temperature = str(lens.get_temperature())
                temperature = float(temperature)
                temperature = round(temperature,2)
                temperature = str(temperature)
                self.textBrowser_temperature.append(temperature)

                min_fp, max_fp = lens.to_focal_power_mode()

                self.textBrowser_pD.append(str(max_fp))
                self.textBrowser_nD.append(str(min_fp))




    def getValueInput(self):
        com = self.textEdit_com.toPlainText()
        com = 'com'+str(com)
        lens = Lens(com, debug=False)  # set debug to True to see a serial communication log
        if lens.comNum == 0:
            QMessageBox.information(self, 'Notice', u'请输入正确COM')
        elif lens.comNum == 1:
            inputNum = self.textEdit_inputFNum.toPlainText()
            inputNum = int(inputNum)
            min_fp,max_fp = lens.to_focal_power_mode()
            if inputNum < max_fp and inputNum > min_fp:
                self.clearshowNum()
                lens.set_diopter(inputNum)
                self.textBrowser_showNum.setText(str(lens.get_diopter()))

            else:
                QMessageBox.information(self,'Notice', u'输入数值应该在 -Diopter 与 +Diopter 之间')



    def getValueCycle(self):
        com = self.textEdit_com.toPlainText()
        com = 'com'+str(com)
        lens = Lens(com, debug=False)  # set debug to True to see a serial communication log
        if lens.comNum == 0:
            QMessageBox.information(self, 'Notice', u'请输入正确COM')
        elif lens.comNum == 1:

            min_fp, max_fp = lens.to_focal_power_mode()
            max_cycle = self.textEdit_maxNum.toPlainText()
            min_cycle = self.textEdit_minNum.toPlainText()
            step = self.textEdit_step.toPlainText()
            cycle = self.textEdit_cycle.toPlainText()

            max_cycle = float(max_cycle)
            min_cycle = float(min_cycle)
            step = float(step)
            cycle = float(cycle)

            if max_cycle<max_fp and min_cycle>min_fp:
                    a = max_cycle
                    w = True
                    self.flag = True

                    while self.flag:
                        t = cycle / (2 * (max_cycle - min_cycle))
                        time.sleep(t)
                        if a >= max_cycle:
                            z = True
                        else:
                            z = False
                        if a <= min_cycle:
                            y = True
                        else:
                            y = False
                        x = z or y
                        if x == True:
                            w = not w
                        else:
                            w = w
                        if w == True:
                            a = a + step
                        else:
                            a = a - step

                        lens.set_diopter(a)

                        QApplication.processEvents()
                        self.clearshowNum()
                        self.textBrowser_showNum.append(str(lens.get_diopter()))

                        # if not self.flag:
                        #     break
                        # if self.pushButton_cycleStop.clicked: #??????????????????????????????????????????????????
                        #     break
                        # else:
                        #     continue
            else:
                QMessageBox.information(self,'Notice', u'输入数值应该在 -Diopter 与 +Diopter 之间')

    def reset(self):
        com = self.textEdit_com.toPlainText()
        com = 'com'+str(com)
        lens = Lens(com, debug=False)  # set debug to True to see a serial communication log
        if lens.comNum == 0:
            QMessageBox.information(self, 'Notice', u'请输入正确COM')
        elif lens.comNum == 1:

            lens.to_focal_power_mode()
            lens.set_diopter(0)
            self.clearshowNum()
            self.textBrowser_showNum.append(str(lens.get_diopter()))

    def clearAll(self):
        for browser in [self.textBrowser_firmwareVersion,  self.textBrowser_lensSN,  self.textBrowser_nD,
                          self.textBrowser_pD, self.textBrowser_temperature]:
            browser.clear()

    def clearshowNum(self):
        for browser in [self.textBrowser_showNum]:
            browser.clear()

    def stopCycle(self):
        self.flag = False
