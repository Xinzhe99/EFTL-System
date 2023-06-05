# -*- coding: utf-8 -*-
# @Author  : XinZhe Xie
# @University  : ZheJiang University
import PySpin
from PyQt5.QtGui import QImage, QPixmap, QIcon, QPainter, QPen
import os
from PyQt5.QtCore import QTimer, QThread, Qt, QRect
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QLabel
from tools import is_number,cal_clarity,max_y

import cv2
from lens import Lens
from PyQt5.QtWidgets import QApplication, QWidget
import time
import sys
from PyQt5 import uic
import numpy as np
from scipy.optimize import curve_fit
import serial.tools.list_ports

#允许多个进程同时使用OpenMP库
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

#定义支持的图片格式
support_format=[".jpg", ".png", ".bmp"]

# flag定义全局变量 图片保存的序号默认从1开始
flag_save_number = 1
# 检查屈光度更新的flag
diop_updata_flag=10000

#局部对焦flag
roi_flag=False


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        if getattr(sys,'frozen', False):
            ui_path = os.path.join(sys._MEIPASS, 'design_menu.ui')
        else:
            ui_path = 'design_menu.ui'

        self.ui = uic.loadUi(ui_path)

        if getattr(sys, 'frozen', False):
            ico_path = os.path.join(sys._MEIPASS, 'myico.ico')
        else:
            ico_path = 'myico.ico'
        self.ui.setWindowIcon(QIcon(ico_path))

        #启动按钮
        btn_start_capture=self.ui.btn_begin_caputre #获取相机画面按钮
        btn_start_capture.clicked.connect(self.start_capture)
        
        #停止按钮
        btn_stop_capture=self.ui.btn_stop_caputre#停止获取画面的按钮
        btn_stop_capture.clicked.connect(self.stop_capture)
        btn_stop_capture.setEnabled(False)

        # 显示图像的标签
        self.img_show_lable = self.ui.video_label
        # 创建一个QTimer对象
        self.timer_video = QTimer()
        # 连接定时器的timeout信号到update_image槽函数
        self.timer_video.timeout.connect(self.update_image)
        # 创建一个QTimer对象用于更新曝光时间的显示
        self.exp_show_timer = QTimer()
        # 连接定时器的timeout信号到槽函数
        self.exp_show_timer.timeout.connect(self.update_exp_label)
        # 创建一个QTimer对象用于更新gain的显示
        self.gain_show_timer = QTimer()
        # 连接定时器的timeout信号到槽函数
        self.gain_show_timer.timeout.connect(self.update_gain_label)
        # 创建一个QTimer对象用于更新fps的显示
        self.fps_show_timer = QTimer()
        # 连接定时器的timeout信号到槽函数
        self.fps_show_timer.timeout.connect(self.update_fps_label)
        # 创建一个QTimer对象用于保存图片
        self.img_save_timer = QTimer()
        # 连接定时器的timeout信号到槽函数
        self.img_save_timer.timeout.connect(self.save_one_img)
        # 显示相机信息的标签
        self.lb_video_inf = self.ui.video_inf
        # 显示相机数量的标签
        self.lb_num_cam = self.ui.video_num

        # 绑定自动曝光按钮
        self.btn_auto_exposure=self.ui.btn_Auto_Exposure
        # 自动曝光初始化默认开启
        self.btn_auto_exposure.setChecked(True)
        # 该按钮默认不能用，开始捕获图像后才可以
        self.btn_auto_exposure.setEnabled(False)

        #修改曝光模式
        self.btn_auto_exposure.stateChanged.connect(self.change_exposure_mode)
        self.exposure_time_slider=self.ui.exp_control#绑定手动调节曝光的slider
        self.exposure_time_slider.setRange(6, 30000.0)#初始化设置slider的上下限，不能删，删了报错
        self.exposure_time_slider.valueChanged.connect(self.set_exposure)#绑定曝光时间设置函数
        self.exposure_time_slider.setEnabled(False)  # 初始化冻结slider
        self.lb_exp_show=self.ui.exp_show#显示曝光时间

        # 绑定自动gain按钮
        self.btn_auto_gain = self.ui.btn_Auto_Gain  # 绑定gain按钮
        # 自动gain默认开启
        self.btn_auto_gain.setChecked(True)  # 自动gain初始化默认开启
        # 该按钮默认不能用，开始捕获图像后才可以
        self.btn_auto_gain.setEnabled(False)

        #修改gain模式
        self.btn_auto_gain.stateChanged.connect(self.change_gain_mode)
        self.gain_slider = self.ui.gain_control  # 绑定手动调节gain的slider
        self.gain_slider.setRange(0, 47.99)  # 初始化设置slider的上下限，不能删，删了会因为没有初值，下面代码报错，实际还会重新根据实际情况定新的值
        self.gain_slider.valueChanged.connect(self.set_gain)  # 绑定曝光时间设置函数
        self.gain_slider.setEnabled(False)# 初始化冻结slider
        self.lb_gain_show = self.ui.gain_show  # 绑定显示gain值

        #链接用于保存/手动停止保存图片的按钮
        self.btn_save_pictures=self.ui.btn_begin_save
        self.btn_save_pictures.clicked.connect(self.start_save_picture)
        self.btn_stop_save_pictures = self.ui.btn_stop_save
        self.btn_stop_save_pictures.clicked.connect(self.stop_save_picture)

        #用于保存图像的flag,默认情况不保存
        self.need_save_fig=False

        #初始情况下冻结以下按钮
        self.btn_save_pictures.setEnabled(False)
        self.btn_stop_save_pictures.setEnabled(False)

        #连接透镜按钮
        self.btn_connect_lens=self.ui.btn_begin_connect_len
        self.btn_connect_lens.clicked.connect(self.create_len)

        #设置屈光度按钮
        self.btn_to_set_diopter=self.ui.btn_set_diopter
        self.btn_to_set_diopter.clicked.connect(self.setdiopter)

        # 重置屈光度按钮
        self.btn_reset_len=self.ui.btn_Reset_diopter
        self.btn_reset_len.clicked.connect(self.reset_diopter)

        #屈光度循环开启按钮
        self.btn_begin_cycle=self.ui.btn_cycle_diopter
        self.btn_begin_cycle.clicked.connect(self.begin_cycle)

        #屈光度循环关闭按钮
        self.btn_stop_cycle=self.ui.btn_stop_cycle_diopter
        self.btn_stop_cycle.clicked.connect(self.stop_cycle)


        #用于绑定cycle用的编辑框，监听是否发生改变，计算图片数量用
        self.max_diopter_input=self.ui.max_diopter_input
        self.min_diopter_input=self.ui.min_diopter_input
        self.step_diopter_input=self.ui.step_diopter_input
        # 监听这两个edit,按下回车键或者失去焦点时触发，检查计算
        self.max_diopter_input.editingFinished.connect(self.updade_count_number)
        self.min_diopter_input.editingFinished.connect(self.updade_count_number)
        self.step_diopter_input.editingFinished.connect(self.updade_count_number)

        #绑定手动输入曝光和增益的按钮和编辑框初始化无法使用
        self.exp_edit=self.ui.exp_edit
        self.btn_exp_set=self.ui.exp_set
        self.gain_edit=self.ui.gain_edit
        self.btn_gain_set=self.ui.gain_set
        self.exp_edit.setEnabled(False)
        self.btn_exp_set.setEnabled(False)
        self.gain_edit.setEnabled(False)
        self.btn_gain_set.setEnabled(False)

        #绑定检查曝光时间和增益的两个函数
        self.exp_edit.editingFinished.connect(self.check_edit_exp)
        self.gain_edit.editingFinished.connect(self.check_edit_gain)

        #绑定设置曝光时间和增益的按钮
        self.btn_exp_set.clicked.connect(self.set_exposure_edit)
        self.btn_gain_set.clicked.connect(self.set_gain_edit)

        #绑定用于自动对焦的按钮
        self.btn_auto_focus=self.ui.btn_autofocus
        self.btn_auto_focus.clicked.connect(self.auto_focus)

        # 获取端口列表
        self.get_port_list()

        #绑定录像按钮
        self.btn_start_capture_video=self.ui.btn_begin_save_2
        self.btn_start_capture_video.clicked.connect(self.start_recording)

        #设置录制的flag,默认不录制
        self.record_flag = False

        #设置录像的帧列表
        self.frameslist=[]

        #绑定结束录像按钮
        self.btn_stop_capture_video = self.ui.btn_stop_save_2
        self.btn_stop_capture_video.clicked.connect(self.stop_recording)

        #防止误点，一开始冻结录像按钮
        self.btn_stop_capture_video.setEnabled(False)
        self.btn_start_capture_video.setEnabled(False)

        # 冻结透镜区域功能按钮
        self.ui.btn_set_diopter.setEnabled(False)
        self.ui.btn_Reset_diopter.setEnabled(False)
        self.ui.btn_cycle_diopter.setEnabled(False)
        self.ui.btn_stop_cycle_diopter.setEnabled(False)

        #冻结保存图像和图片的停止按钮
        self.ui.btn_stop_save.setEnabled(False)
        self.ui.btn_stop_save_2.setEnabled(False)

        #绑定双击局部聚焦
        self.ui.video_label.mouseDoubleClickEvent = self.roi_focus  # 绑定双击信号

        #绑定
        self.ui.btn_set_focus.clicked.connect(self.set_focus)

        #设置默认的对焦参数
        self.roi_height = 50
        self.roi_width = 50

        #框选区域进行自动对焦
        self.start_pos = None
        self.end_pos = None

        #绑定框选对焦
        self.ui.video_label.mousePressEvent = self.boxout_mousePressEvent
        self.ui.video_label.mouseReleaseEvent = self.boxout_mouseReleaseEvent
        self.ui.video_label.mouseMoveEvent = self.boxout_mouseMoveEvent

        # 鼠标移动中Flag,防止两个鼠标事件起冲突，效果和过滤器差不多
        self.move_flag = False

    #获取端口列表
    def get_port_list(self):
        plist = list(serial.tools.list_ports.comports())

        if len(plist) <= 0:
            QMessageBox.information(self, 'Notice', 'Cannot find any com can be used!')

        else:
            self.ui.comboBox_port.clear()
            for i in range(0, len(plist)):
                self.plist_0 = list(plist[i])
                self.ui.comboBox_port.addItem(str(self.plist_0[0]))

    # 用于手动设置编辑框输入的曝光值
    def set_exposure_edit(self):
        exp_to_set_text = self.exp_edit.text()
        if is_number(exp_to_set_text):
            exp_to_set=float(exp_to_set_text)
            self.cam.ExposureTime.SetValue(exp_to_set)
        else:
            QMessageBox.information(self, "notice", 'Please enter exposure value')

    # 用于手动设置编辑框输入的增益值
    def set_gain_edit(self):
        gain_to_set_text=self.gain_edit.text()
        if is_number(gain_to_set_text):
            gain_to_set = float(gain_to_set_text)
            self.cam.Gain.SetValue(gain_to_set)
        else:
            QMessageBox.information(self, "notice", 'Please enter gain value')


    #用于初始化相机并且开启定时器捕获图像
    def start_capture(self):
        try:
            self.camera_system = PySpin.System.GetInstance()
            self.cam_list = self.camera_system.GetCameras()
            self.cam = self.cam_list[0]
            self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()#
            self.sNodemap = self.cam.GetTLStreamNodeMap()#获取传输层流节点映射,传输层流是指相机和主机之间的数据流，它可以通过不同的传输协议来实现
            self.nodemap = self.cam.GetNodeMap()
        except Exception as e:
            # 输出异常信息
            print(e)
        # 获取相机数量,这里只支持一个!
        num_cameras = self.cam_list.GetSize()
        if num_cameras!=0:
            # 获取相机版本型号
            cam_version = self.camera_system.GetLibraryVersion()
            self.lb_video_inf.setText('Library version: %d.%d.%d.%d' % (
                cam_version.major, cam_version.minor, cam_version.type, cam_version.build))
            # 相机初始化
            self.cam.Init()
            # 使能按钮
            self.btn_save_pictures.setEnabled(True)
            self.btn_stop_save_pictures.setEnabled(True)
            self.btn_auto_exposure.setEnabled(True)
            self.btn_auto_gain.setEnabled(True)
            self.ui.btn_stop_caputre.setEnabled(True)
            self.lb_num_cam.setText('%d' % num_cameras)
            self.btn_stop_capture_video.setEnabled(False)
            self.btn_start_capture_video.setEnabled(True)
            # 创建节点对象，用于访问和修改流缓冲区处理模式的参数
            self.node_bufferhandling_mode = PySpin.CEnumerationPtr(self.sNodemap.GetNode('StreamBufferHandlingMode'))
            if not PySpin.IsAvailable(self.node_bufferhandling_mode) or not PySpin.IsWritable(
                    self.node_bufferhandling_mode):
                print('Unable to set stream buffer handling mode.. Aborting...')

            # 设置流缓冲区处理模式为最新模式
            node_newestonly = self.node_bufferhandling_mode.GetEntryByName('NewestOnly')
            if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
                print('Unable to set stream buffer handling mode.. Aborting...')
            self.node_newestonly_mode = node_newestonly.GetValue()

            # 设置流缓冲区处理模式为最新模式，它使用之前获取的最新模式的整数值，作为流缓冲区处理模式枚举节点的新值。 这样，相机就会只保留最新的图像，而丢弃旧的图像。
            self.node_bufferhandling_mode.SetIntValue(self.node_newestonly_mode)

            #获取相机的设备序列号
            node_device_serial_number = PySpin.CStringPtr(self.nodemap_tldevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                device_serial_number = node_device_serial_number.GetValue()
                print('Device serial number retrieved as %s...' % device_serial_number)

            #相机开始获取图像
            self.cam.BeginAcquisition()
            print('All initial finished,Begin to Acquisition')

            #获取实时fps
            self.real_fps = self.cam.AcquisitionResultingFrameRate.GetValue()

            #相机初始化自动曝光
            self.Reset_exposure()

            #相机初始化增益
            self.Reset_gain()

            #用定时器来获取新的图像
            self.timer_video.start(0)

            # 用定时器来更新曝光时间显示的标签
            self.exp_show_timer.start(0)

            # 用定时器来更新gain显示的标签
            self.gain_show_timer.start(0)

            # 用定时器来获取fps
            self.fps_show_timer.start(0)

            #关闭这个按钮，不然会报错
            self.ui.btn_begin_caputre.setEnabled(False)

            # 支持的曝光时间非常久，容易卡，这里手动设置为30000
            self.exposure_time_slider.setRange(self.cam.ExposureTime.GetMin(), 30000)

            #设置增益的slider上下限
            self.gain_slider.setRange(self.cam.Gain.GetMin(),self.cam.Gain.GetMax())

            self.ui.btn_stop_save_2.setEnabled(False)
            self.ui.btn_stop_save.setEnabled(False)
        else:
            QMessageBox.information(self, "notice", 'Please check if the camera is connected')
    #用于虚假关闭相机，其实还在
    def stop_capture(self):
        lb_video_inf = self.ui.video_inf
        lb_video_inf.setText('End EndAcquisition!')
        self.ui.video_num.setText('0')
        self.timer_video.stop()
        self.cam.EndAcquisition()
        #控制按钮，防止误点崩溃
        self.ui.btn_begin_caputre.setEnabled(True)
        self.ui.btn_stop_caputre.setEnabled(False)
        self.img_show_lable.clear()

        self.ui.btn_begin_save.setEnabled(False)
        self.ui.btn_begin_save_2.setEnabled(False)
        self.ui.btn_stop_save.setEnabled(False)
        self.ui.btn_stop_save_2.setEnabled(False)

        #关闭三个定时器，停止更新
        self.exp_show_timer.stop()
        self.gain_show_timer.stop()
        self.fps_show_timer.stop()
        self.ui.lb_show_fps.setText('')
        self.ui.exp_show.setText('')
        self.ui.gain_show.setText('')



        # 自动曝光初始化默认开启
        self.btn_auto_exposure.setChecked(True)
        # 该按钮默认不能用，开始捕获图像后才可以
        self.btn_auto_exposure.setEnabled(False)
        # 自动gain默认开启
        self.btn_auto_gain.setChecked(True)  # 自动gain初始化默认开启
        # 该按钮默认不能用，开始捕获图像后才可以
        self.btn_auto_gain.setEnabled(False)
        print('End EndAcquisition!')


    #用于定时器获取一张图像并显示出来
    def update_image(self):
        #获取实时gain
        real_gain=self.cam.Gain.GetValue()
        self.real_gain = round(real_gain,3)

        # 根据实时曝光时间调整等待时间
        timeout = 0
        real_exp_time = self.cam.ExposureTime.GetValue()  # us
        self.real_exp_time = real_exp_time

        if self.cam.ExposureTime.GetAccessMode() == PySpin.RW or self.cam.ExposureTime.GetAccessMode() == PySpin.RO:
            # The exposure time is retrieved in µs so it needs to be converted to ms to keep consistency with the unit being used in GetNextImage
            timeout = (int)(self.real_exp_time / 1000 + 1000)
        image_result = self.cam.GetNextImage(timeout)

        #检查图像完整性
        if image_result.IsIncomplete():
            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

        #格式转换
        image_data_np = image_result.GetNDArray()

        #如果同时需要保存下来,标志位由定时器控制,每x ms 置一次True,保存一张图片
        if self.need_save_fig == True:
            #开个子线程 保存图片 不然会拖慢进程 影响显示
            #判断是否手动选择了需要的格式，如果没有默认jpg
            format_need=self.ui.comboBox_output_format_2.currentText()
            self.save_img_sub_thread=Save_img(data=image_data_np,path=self.pic_save_path,save_format=format_need)#todo 代码写了，但没有测试是否可以支持保存rgb

            self.need_save_fig=False#保存flag置为False,等待下一次置为True
        #如果需要录制下来
        if self.record_flag==True:
            self.frameslist.append(image_result)

        #显示(灰度)
        if len(image_data_np.shape) == 2:
            image_pixmap = QPixmap.fromImage(QImage(image_data_np.data, image_data_np.shape[1], image_data_np.shape[0],
                                                    QImage.Format_Grayscale8))
            self.img_show_lable.setPixmap(image_pixmap)
            # 调整尺寸
            self.img_show_lable.setScaledContents(True)
            # 释放内存
            image_result.Release()
        # 显示(RGB)
        else:
            image_pixmap = QPixmap.fromImage(QImage(image_data_np.data, image_data_np.shape[1], image_data_np.shape[0], QImage.Format_RGB888))#todo 代码写了，但没有测试是否可以支持rgb
            self.img_show_lable.setPixmap(image_pixmap)
            #调整尺寸
            self.img_show_lable.setScaledContents(True)
            #释放内存
            image_result.Release()
        return image_data_np
    #用于重置相机曝光模式到自动
    def Reset_exposure(self):
        if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to enable automatic exposure (node retrieval). Non-fatal error...')

        self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)
        print('Automatic exposure enabled...')

    #用于相机曝光时间修改
    def set_exposure(self):
        if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to set exposure time. Aborting...')
        exposure_time_to_set = self.exposure_time_slider.value()
        self.cam.ExposureTime.SetValue(exposure_time_to_set)


    # 用于更新曝光时间显示的标签
    def update_exp_label(self):
        exp_time = self.real_exp_time
        self.lb_exp_show.setText(str(exp_time))

    #用于相机曝光模式改变
    def change_exposure_mode(self):
        if self.btn_auto_exposure.isChecked():
            self.Reset_exposure()
            self.exposure_time_slider.setEnabled(False)
            self.exp_edit.setEnabled(False)
            self.btn_exp_set.setEnabled(False)

        else:
            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.exposure_time_slider.setEnabled(True)
            self.exp_edit.setEnabled(True)
            self.btn_exp_set.setEnabled(True)

    #用于gain模式改变
    def change_gain_mode(self):
        #自动gain开启
        if self.btn_auto_gain.isChecked():
            self.Reset_gain()
            self.gain_slider.setEnabled(False)
            self.gain_edit.setEnabled(False)
            self.btn_gain_set.setEnabled(False)
        # 自动gain关闭
        else:
            self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            self.gain_slider.setEnabled(True)
            self.gain_edit.setEnabled(True)
            self.btn_gain_set.setEnabled(True)

    #用于手动设置gain
    def set_gain(self):
        gain_to_set = self.gain_slider.value()
        self.cam.Gain.SetValue(gain_to_set)

    # 用于gain显示的标签
    def update_gain_label(self):
        gain_num = self.real_gain
        self.lb_gain_show.setText(str(gain_num))

    # 用于重置相机gain模式到自动
    def Reset_gain(self):
        self.cam.GainAuto.SetValue(PySpin.GainAuto_Continuous)
        print('Automatic gain enabled...')

    #检查手动输入的曝光值是否是数字 是否在范围内,如果为空不判断
    def check_edit_exp(self):
        if is_number(self.exp_edit.text()) and float(self.exp_edit.text())<self.cam.ExposureTime.GetMax() and float(self.exp_edit.text())>self.cam.ExposureTime.GetMin():
            pass
        elif self.exp_edit.text()=='':
            pass
        else:
            QMessageBox.information(self, "notice", 'Please check if you have entered the correct exposure value')
        print(self.cam.ExposureTime.GetMax(),self.cam.ExposureTime.GetMin())

    # 检查手动输入的增益值是否是数字 是否在范围内,如果为空不判断
    def check_edit_gain(self):
        if is_number(self.gain_edit.text()) and float(self.gain_edit.text())<self.cam.Gain.GetMax() and float(self.gain_edit.text())>self.cam.Gain.GetMin():
            pass
        elif self.gain_edit.text()=='':
            pass
        else:
            QMessageBox.information(self, "notice", 'Please check if you have entered the correct exposure value')
        print(self.cam.Gain.GetMax(),self.cam.Gain.GetMin())

    # 用于获取相机fps
    def update_fps_label(self):
        fps_num=round(self.real_fps, 1)
        self.ui.lb_show_fps.setText(str(fps_num))

    #用于获取保存路径,并保存在类对象里,返回最终保存路径
    def get_save_path(self):
        self.pic_save_path=QFileDialog.getExistingDirectory(self, "choose save path")

        return self.pic_save_path

    # 用于图像开始保存
    def start_save_picture(self):
        self.get_save_path()# return self.pic_save_path

        text, ok = QInputDialog.getInt(self, "Save interval", "ms:")
        if ok:
            self.save_interval=int(text)
            self.img_save_timer.start(self.save_interval)#启动定时器用于更改保存flag
            self.ui.btn_stop_save.setEnabled(True)
            self.ui.label_show_save_inf.setText('Working')
        else:
            QMessageBox.information(self, "notice", 'Please check if you have entered the correct save interval')


    #用于获取一张图像并且保存下来
    def save_one_img(self):
        self.need_save_fig=True

    # 用于停止保存图像
    def stop_save_picture(self):
        #停止后说明保存结束，下次也从img1开始保存
        global flag_save_number
        flag_save_number=1
        #关闭定时器，关闭保存
        self.img_save_timer.stop()
        self.need_save_fig=False
        QMessageBox.information(self, "notice", 'All pictures have been saved in {}'.format(self.pic_save_path))
        self.ui.btn_stop_save.setEnabled(False)
        self.ui.label_show_save_inf.setText('Not Working')
    # 用于创建透镜子类，控制透镜
    def create_len(self):
        try:
            self.lens = Lens(self.ui.comboBox_port.currentText(), debug=False)
            if self.lens.comNum == 0:
                QMessageBox.information(self,'Notice', u'The connection has failed, please enter the correct port number and check if the hardware device is plugged in')

            elif self.lens.comNum == 1:
                #状态显示
                self.ui.lb_show_com.setText('Connected')

                #获取固件版本
                self.ui.lb_firmware_show.setText(str(self.lens.firmware_version))

                # 获取相机序列号
                self.ui.lb_lens_SN_show.setText(str(self.lens.lens_serial))

                #获取温度
                temperature = str(self.lens.get_temperature())
                temperature = float(temperature)
                temperature = round(temperature, 2)
                temperature = str(temperature)
                self.ui.lb_temp_show.setText(temperature)

                #获取最大和最小屈光度
                min_diop, max_diop = self.lens.to_focal_power_mode()
                self.ui.lb_posi_dip_show.setText(str(max_diop))
                self.ui.lb_neg_dip_show.setText(str(min_diop))

                #使能按钮
                self.ui.btn_set_diopter.setEnabled(True)
                self.ui.btn_Reset_diopter.setEnabled(True)
                self.ui.btn_cycle_diopter.setEnabled(True)
                self.ui.btn_stop_cycle_diopter.setEnabled(True)
        except:
            QMessageBox.critical(self, 'Notice', 'The com is not available or the driver is not installed')

    # 用于把透镜的屈光度设到某一值
    def setdiopter(self):
        if self.lens.comNum == 1:
            input_text=self.ui.diopter_input_edit.text()

            if is_number(input_text):
                input_diopter=float(self.ui.diopter_input_edit.text())
                min_diop, max_diop = self.lens.to_focal_power_mode()
                # 检查输入是否正确
                if input_diopter < max_diop and input_diopter > min_diop:
                    self.lens.set_diopter(input_diopter)
                    self.ui.lb_diop_show.setText(str(self.lens.get_diopter()))
                else:
                    QMessageBox.information(self, 'Notice',u'Please enter the correct diopter!Diopter value should be between {} and {}'.format(min_diop,max_diop))

            else:
                QMessageBox.information(self, 'Notice',
                                        u'Diopter should be number!')
        else:
            QMessageBox.information(self, 'Notice',
                                    u'You have not connected a lens')
    # 用于重置透镜屈光度
    def reset_diopter(self):
        if self.lens.comNum == 1:
            self.lens.set_diopter(0)
            self.ui.lb_diop_show.setText('0')
        else:
            QMessageBox.information(self, 'Notice',
                                    u'You have not connected a lens')

    # 用于屈光度变化循环
    def begin_cycle(self):
        #检查是否连接到了透镜
        if self.lens.comNum == 1:
            try:
                min_diop, max_diop = self.lens.to_focal_power_mode()
                max_cycle = self.ui.max_diopter_input.text()
                min_cycle = self.ui.min_diopter_input.text()
                step = self.ui.step_diopter_input.text()
                cycle = self.ui.cycle_diopter_input.text()
                max_cycle = float(max_cycle)
                min_cycle = float(min_cycle)
                step = float(step)
                #如果没有输入cycle，默认10s单程，防止崩溃
                if cycle=='':
                    cycle=10
                else:
                    cycle = float(cycle) #s

                #判断输入是否正确
                if max_cycle < max_diop and min_cycle > min_diop:
                    #flag表示需要进行循环
                    self.cycle_flag = True
                    self.ui.lb_show_zoom.setText('Zooming')
                    # 判断是否同时需要保存图像
                    save_check = self.ui.btn_save_pic_zoom.isChecked()  # bool
                    # 计算需要跳的次数
                    times = (max_cycle - min_cycle) / step
                    # 计算每次调节需要间隔的时间
                    every_time = (cycle * 1000) / times  # 计算出来的时间单位ms
                    if save_check == True:
                        self.get_save_path()  # 创建文件夹并且设置保存路径到类对象中

                        #定时器拍照用，每隔every_time拍一次
                        self.img_save_timer.start(every_time)

                        # 计数器清0
                        global flag_save_number
                        flag_save_number = 1

                    #如果需要来回拍而不是从头拍到尾
                    if not self.ui.btn_save_pic_zoom_2.isChecked():
                        #从最大开始拍到最小
                        real_diop = max_cycle

                        for i in range(int(times)):
                            if self.cycle_flag==False:
                                # 停止保存图像
                                self.img_save_timer.stop()
                                break
                            self.lens.set_diopter(real_diop)
                            real_diop-=step
                            time.sleep(every_time/1000)#time.sleep(s)
                            # 获取当前屈光度并显示
                            now_diop=self.lens.get_diopter()#获取屈光度
                            self.ui.lb_diop_show_2.setText(str(now_diop))
                            #防卡
                            QApplication.processEvents()
                        #停止保存图像
                        self.img_save_timer.stop()
                    #从头拍到尾
                    else:
                        # 先从最大开始拍到最小
                        real_diop = max_cycle
                        for i in range(int(times)):
                            if self.cycle_flag==False:
                                # 停止保存图像
                                self.img_save_timer.stop()
                                break
                            self.lens.set_diopter(real_diop)
                            real_diop-=step
                            time.sleep(every_time/1000)#time.sleep(s)
                            # 获取当前屈光度并显示
                            now_diop=self.lens.get_diopter()#获取屈光度
                            self.ui.lb_diop_show_2.setText(str(now_diop))
                            QApplication.processEvents()

                        # 再从最小开始拍到最大,这里不重复拍所以先加上step
                        real_diop = min_cycle+step
                        for i in range(int(times)):
                            if self.cycle_flag==False:
                                # 停止保存图像
                                self.img_save_timer.stop()
                                break
                            self.lens.set_diopter(real_diop)
                            real_diop+=step
                            time.sleep(every_time/1000)#time.sleep(s)
                            # 获取当前屈光度并显示
                            now_diop=self.lens.get_diopter()#获取屈光度
                            self.ui.lb_diop_show_2.setText(str(now_diop))
                            QApplication.processEvents()
                        # 停止保存图像
                        self.img_save_timer.stop()
                    self.ui.lb_show_zoom.setText('Finish zooming')
                else:
                    QMessageBox.information(self, 'Notice',
                                            u'Please enter the correct diopter!Diopter value should be between {} and {}'.format(
                                                min_diop, max_diop))
            except:
                QMessageBox.information(self, 'Notice',
                                        u'You have not enter correct diopter and step!')

        else:
            QMessageBox.information(self, 'Notice',
                                    u'You have not connected a lens')

    # 用于停止屈光度变化循环
    def stop_cycle(self):
        self.cycle_flag=False


    #用于计算cycle图像数量：
    def updade_count_number(self):
        #检查3个屈光度的输入是否有一个为空，如果为空，不必要更新
        if (self.max_diopter_input.text()=='' or self.min_diopter_input.text()=='' or self.step_diopter_input.text()==''):
            pass
        else:
            #如果都不是空的了，就检查是否都是数字
            if any(char.isdigit() for char in self.max_diopter_input.text())and any(char.isdigit() for char in self.min_diopter_input.text()) and any(char.isdigit() for char in self.step_diopter_input.text()):
                number_of_pic=int((float(self.max_diopter_input.text())-float(self.min_diopter_input.text()))//float(self.step_diopter_input.text()))
                self.ui.lb_pic_number_show.setText(str(number_of_pic))
            else:
                QMessageBox.information(self, 'Notice',
                                            u'Please check if you have entered the correct diopter and step!')



    # 用于安全退出，释放摄像头
    def closeEvent(self, event):
        self.cam.DeInit()
        del self.cam

        # Clear camera list before releasing system
        self.cam_list.Clear()

        # Release system instance
        self.system.ReleaseInstance()

        event.accept()

    # 用于自动调焦
    def auto_focus(self):
        #检查透镜和相机连接是否已经连接
        try:
            #获取最大和最小屈光度
            min_diop, max_diop = self.lens.to_focal_power_mode()
            min_diop=float(min_diop)
            max_diop=float(max_diop)
            tol=0.1

            # 定义一个函数fun(x)，这里假设它是单峰的
            def fun(diop):
                if self.lens.comNum == 1:
                    #设置屈光度
                    self.lens.set_diopter(diop)
                    #获取当前屈光度
                    current_diop=self.lens.get_diopter()
                    #设置的值和获取的值误差小于tol,说明设置成功，再计算清晰度
                    if abs(current_diop-diop)<=0.01:

                        #非ROI
                        global roi_flag
                        if roi_flag==False:
                            out = cal_clarity(self.update_image(), measure=self.ui.comboBox_focus_measure.currentText(),
                                              roi_point=None, label_height=None, roi_height=None,roi_width=None)
                        #局部自动对焦
                        else:
                            # 用于计算实际像素画面与label的比例
                            self.label_height = self.ui.video_label.height()
                            out = cal_clarity(self.update_image(), measure=self.ui.comboBox_focus_measure.currentText(),
                                            roi_point=self.roi_point,label_height=self.label_height,roi_height=self.roi_height,roi_width=self.roi_width)
                    #设置没有成功,加大时间延迟给透镜
                    else:
                        print('Diopter setting failure')
                        self.lens.set_diopter(diop)
                        time.sleep(0.1)

                else:
                    QMessageBox.information(self, 'Notice',
                                            u'You have not connected a lens')
                return out
            # 定义一个三分法的函数，输入是区间[a,b]和精度eps
            def ternary_search(a, b, eps):
                # 当区间长度小于eps时，停止循环
                while b - a > eps:
                    # 计算两个分割点
                    m1 = a + (b - a) / 3
                    m2 = b - (b - a) / 3
                    # 比较函数值，判断最大值在哪个区间内
                    if fun(m1) < fun(m2):
                        # 最大值在[m1, b]内，舍弃[a, m1]区间
                        a = m1
                    else:
                        # 最大值在[a, m2]内，舍弃[m2, b]区间
                        b = m2
                # 返回区间中点作为最大值的近似解
                return (a + b) / 2

            def hill_climb(min, max, step=0.1, max_iter=1000):
                x = np.random.uniform(min, max)
                for i in range(max_iter):
                    curr_val = fun(x)
                    next_x = x + np.random.uniform(-step, step)
                    next_val = fun(next_x)
                    if next_val > curr_val:
                        x, curr_val = next_x, next_val
                return x
            def curvefitting(min,max):
                # x和y数据
                step=0.1
                x = np.arange(min,max,step)
                #随机生成y，用于更新
                y = np.arange(min, max, step)
                #计算y
                for val in range(x.shape[0]):
                    y[val]=fun(val)
                # 需要拟合的二次函数
                def func(x, a, b, c):
                    return a*x*x+b*x+c
                popt, pcov = curve_fit(func, x, y)
                a,b,c=popt
                #求y最大值时候的x
                x=max_y(a,b,c,min_diop,max_diop)
                return x

            self.ui.lb_show_focus_inf.setText('Focusing')
            if self.ui.comboBox_focus_method.currentText() =='Trichotomy':
                best_diop = ternary_search(min_diop, max_diop, tol)
            elif self.ui.comboBox_focus_method.currentText()=='Climbing':
                best_diop = hill_climb(min_diop,max_diop,step=0.1,max_iter=1000)
            elif self.ui.comboBox_focus_method.currentText()=='Curve fitting':
                best_diop=curvefitting(min_diop,max_diop)
            self.lens.set_diopter(best_diop)
            self.ui.lb_show_focus_inf.setText('Finish')
            self.ui.lb_diop_show.setText(str(round(best_diop,2)))

        except:
            QMessageBox.information(self, 'Notice',
                                    u'Please connect the camera, lens!')
        finally:
            roi_flag == False
    #开始录像
    def start_recording(self):
        if self.cam_list.GetSize()!=0:

            try:
                self.video_save_path = QFileDialog.getExistingDirectory(self, "choose save path")
                self.recorder = PySpin.SpinVideo()
                if self.ui.comboBox_output_format_3.currentText()=='AVI':
                    self.option = PySpin.AVIOption()
                    self.option.frameRate =self.real_fps

                elif self.ui.comboBox_output_format_3.currentText()=='MPEG':
                    self.option = PySpin.MJPGOption()
                    self.option.frameRate = self.real_fps
                    text, ok = QInputDialog.getInt(self, "Image quality", "Percentage (0-100):")
                    if ok:
                        self.option.quality = int(text)
                self.recorder.Open(self.video_save_path + '/' + time.strftime('%Y-%m-%d_%H_%M_%S',
                                                                                  time.localtime(
                                                                                      time.time())),self.option)
                self.record_flag=True
                self.ui.btn_stop_save_2.setEnabled(True)

                self.ui.label_show_save_inf.setText('Working')
            except:
                QMessageBox.information(self, 'Notice',
                                        u'Something wrong!')

        else:
            QMessageBox.information(self, 'Notice',
                                    u'Please connect the camera!')


    # 结束录像
    def stop_recording(self):
        if self.record_flag == True:
            try:
                for i in range(len(self.frameslist)):
                    self.recorder.Append(self.frameslist[i])
                self.recorder.Close()

                del self.frameslist
                self.record_flag = False

                QMessageBox.information(self, 'Notice',
                                        u'Recording completed, video stored at {}'.format(self.video_save_path))
                self.ui.btn_stop_save_2.setEnabled(False)
                self.ui.label_show_save_inf.setText('Not Working')
            except:
                QMessageBox.information(self, 'Notice',
                                        u'Failed to save video!')

        else:
            QMessageBox.information(self, 'Notice',
                                    u'You have not started recording yet!')

    # 局部对焦
    def roi_focus(self, event):
        # 获取点击位置
        global roi_flag
        x = event.x()
        y = event.y()
        roi = (x, y)
        try:

            roi_flag = True
            self.roi_point = roi
            self.auto_focus()
        except:
            QMessageBox.information(self, 'Notice',
                                    u'Focusing failure')

    #设置roi_radius
    def set_focus(self):
        max_num = round(min(self.ui.video_label.width(),self.ui.video_label.height())/2)
        text, ok = QInputDialog.getInt(self, "Set ROI Radius", "Radius(0-{})  default=50".format(str(max_num)))
        if ok:
            self.roi_height = int(text)
            self.roi_width = int(text)
        else:
            QMessageBox.information(self, "notice", 'Please check if you have entered the correct Radius, default roi radius=50')

    def boxout_mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.move_flag = False

    def boxout_mouseMoveEvent(self, event):
        if not self.start_pos:
            return
        self.move_flag=True
        self.end_pos = event.pos()
        self.update()

    def boxout_mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_pos = event.pos()
            self.update()

            if self.move_flag==True:
                self.boxout_focus()
            else:
                pass

    def boxout_focus(self):
        print(self.start_pos, self.end_pos)
        x1 = self.start_pos.x()
        y1 = self.start_pos.y()
        x2 = self.end_pos.x()
        y2 = self.end_pos.y()
        self.roi_point = (round(x1 + x2) / 2, round(y1 + y2) / 2)
        self.roi_height = abs(round(y2 - y1))
        self.roi_width = abs(round(x2 - x1))
        global roi_flag
        roi_flag = True
        self.auto_focus()
        self.start_pos = None
        self.end_pos = None
        self.drawRectFlag = False
        self.draw_rect = QRect()
        self.update()

#子线程用来保存图片，不影响主线程显示
class Save_img(QThread):
    def __init__(self,data,path,save_format):
        self.data=data
        self.path=path
        self.save_format='.'+save_format
        self.save()
    # 重写run方法
    def save(self):
        global flag_save_number#定义在文件头
        cv2.imwrite(os.path.join(self.path,str(flag_save_number)+ self.save_format), self.data)
        print('{}{} has been saved in {}'.format(flag_save_number,self.save_format,self.path + '/'+str(flag_save_number)+'%s'%self.save_format))
        flag_save_number += 1#增量式创建，图片按先后排序


