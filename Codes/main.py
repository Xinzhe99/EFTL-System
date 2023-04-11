# -*- coding: utf-8 -*-
# @Author  : XinZhe Xie
# @University  : ZheJiang University

import sys
from PyQt5.QtWidgets import QApplication
import main_window

if __name__ == '__main__':

    app = QApplication(sys.argv)

    my_window = main_window.MyWindow()
    my_window.ui.show()

    sys.exit(app.exec_())

