# -*- coding: utf-8 -*-
# @Author  : XinZhe Xie
# @University  : ZheJiang University
from PyQt5 import uic
import PySpin
from PyQt5.QtGui import QImage, QPixmap
import os
from PyQt5.QtCore import QTimer,QThread,Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from tools import get_pic_size_in_dir,get_first_image_format,judge_format,is_number,has_chinese_char
import cv2
from lens import Lens
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QLineEdit, QVBoxLayout
import time
import fusion
#允许多个进程同时使用OpenMP库
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

#定义支持的图片格式
support_format=[".jpg", ".png", ".bmp"]

# flag定义全局变量 图片保存的序号默认从1开始
flag_save_number = 1

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('design_meun.ui')  # 加载designer设计的ui程序
        try:
            self.camera_system = PySpin.System.GetInstance()
            self.cam_list = self.camera_system.GetCameras()
            self.cam = self.cam_list[0]
            self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()#
            self.sNodemap = self.cam.GetTLStreamNodeMap()#获取传输层流节点映射,传输层流是指相机和主机之间的数据流，它可以通过不同的传输协议来实现

        except Exception as e:
            # 输出异常信息
            print(e)

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

        #用于选择融合图像栈的路径
        self.btn_fusion_stack=self.ui.btn_select_fusion_path
        self.btn_fusion_stack.clicked.connect(self.set_fusion_path)

        #用于选择融合图像输出的路径
        self.btn_fusion_stack_output = self.ui.btn_select_output_path
        self.btn_fusion_stack_output.clicked.connect(self.set_fusion_output_path)

        # 用于选择model路径
        self.btn_select_model_path=self.ui.btn_select_model_path
        self.btn_select_model_path.clicked.connect(self.set_model_path)

        #用于开始融合按钮
        self.btn_start_fusion=self.ui.btn_start_fusion
        self.btn_start_fusion.clicked.connect(self.start_fusion)

        #用于绑定路径并且监听3个编辑框的内容是否发生了改变
        self.fusion_path_edit=self.ui.fusion_path_edit
        self.out_put_path_edit=self.ui.out_put_path_edit
        self.model_path_edit=self.ui.model_path_edit
        #监听三个path edit,按下回车键或者失去焦点时触发，检查并更新
        self.fusion_path_edit.editingFinished.connect(self.update_source_path)
        self.out_put_path_edit.editingFinished.connect(self.update_target_path)
        self.model_path_edit.editingFinished.connect(self.update_model_path)

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

    # 用于手动设置编辑框输入的曝光值
    def set_exposure_edit(self):
        exp_to_set = float(self.exp_edit.text())
        self.cam.ExposureTime.SetValue(exp_to_set)

    # 用于手动设置编辑框输入的增益值
    def set_gain_edit(self):
        gain_to_set = float(self.gain_edit.text())
        self.cam.Gain.SetValue(gain_to_set)

    #用于初始化相机并且开启定时器捕获图像
    def start_capture(self):
        #先使能按钮
        self.btn_save_pictures.setEnabled(True)
        self.btn_stop_save_pictures.setEnabled(True)
        self.btn_auto_exposure.setEnabled(True)
        self.btn_auto_gain.setEnabled(True)
        self.ui.btn_stop_caputre.setEnabled(True)

        #获取相机版本型号
        cam_version = self.camera_system.GetLibraryVersion()
        self.lb_video_inf.setText('Library version: %d.%d.%d.%d' % (
            cam_version.major, cam_version.minor, cam_version.type, cam_version.build))

        # 获取相机数量,这里只支持一个!
        num_cameras = self.cam_list.GetSize()
        self.lb_num_cam.setText('%d' % num_cameras)

        #相机初始化
        self.cam.Init()

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
    #用于关闭相机
    def stop_capture(self):
        lb_video_inf = self.ui.video_inf
        lb_video_inf.setText('End EndAcquisition!')
        self.ui.video_num.setText('0')
        self.timer_video.stop()
        self.cam.EndAcquisition()
        #控制按钮，防止误点崩溃
        self.ui.btn_begin_caputre.setEnabled(True)
        self.ui.btn_stop_caputre.setEnabled(False)
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
        self.ui.label_save_path_state.setText('Save path is set')
        return self.pic_save_path

    # 用于图像开始保存
    def start_save_picture(self):
        self.get_save_path()# return self.pic_save_path
        print(self.ui.interval_input.text())
        if self.ui.interval_input.text().isdigit():
            self.save_interval = int(self.ui.interval_input.text())#这里保存int类型，单位是ms
            self.img_save_timer.start(self.save_interval)#启动定时器用于更改保存flag
        else:
            QMessageBox.information(self, "notice", 'The time interval "%s" for saving images is not a number' % str(self.ui.interval_input.text()))

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

    # 用于创建透镜子类，控制透镜
    def create_len(self):
        if not self.ui.com_input_edit.text().isdigit():
            QMessageBox.information(self, "Notice", 'You haven\'t entered the correct port number')
        else:
            com=self.ui.com_input_edit.text()
            com = 'com' + str(com)
            self.lens = Lens(com, debug=False)
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

    # 用于把透镜的屈光度设到某一值
    def setdiopter(self):
        if self.ui.lb_show_com.text()=='Connected':
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
                                    u'You have not connected a lens')
    # 用于重置透镜屈光度
    def reset_diopter(self):
        if self.ui.lb_show_com.text() == 'Connected':
            self.lens.set_diopter(0)
            self.ui.lb_diop_show.setText('0')
        else:
            QMessageBox.information(self, 'Notice',
                                    u'You have not connected a lens')

    # 用于屈光度变化循环
    def begin_cycle(self):
        #检查是否连接到了透镜
        if self.ui.lb_show_com.text() == 'Connected':
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
                QMessageBox.information(self, 'Notice',u'Please enter the correct diopter!Diopter value should be between {} and {}'.format(min_diop,max_diop))
        else:
            QMessageBox.information(self, 'Notice',
                                    u'You have not connected a lens')

    # 用于停止屈光度变化循环
    def stop_cycle(self):
        self.cycle_flag=False

    #用于设置融合图像栈路径
    def set_fusion_path(self):
        path = QFileDialog.getExistingDirectory(self, "Choose image stack path")
        flag_have_pic = False
        if os.path.isdir(path):  # 检查path是否为一个存在的文件夹
            #检查是否包含图片
            image_formats = support_format  # 定义常见的图片格式
            files = os.listdir(path)  # 获取文件夹中的所有文件名
            for file in files:  # 遍历每个文件名
                for format in image_formats:  # 遍历每种图片格式
                    if file.endswith(format):  # 如果文件名以图片格式结尾
                        flag_have_pic=True
                        break  # 跳出内层循环，继续下一个文件名
            if flag_have_pic==False:
                QMessageBox.information(self, 'Notice',
                                        u'No pictures in this folder')
            else:
                self.fusion_dir_path = path
                self.ui.fusion_path_edit.setText(path)
        else:
            QMessageBox.information(self, 'Notice',
                                    u'Not a directory')

    #用于设置融合图像输出的文件夹
    def set_fusion_output_path(self):
        path = QFileDialog.getExistingDirectory(self, "Choose output path")
        self.fusion_output_path=path
        self.ui.out_put_path_edit.setText(path)

    #用于设置模型文件路径
    def set_model_path(self):
        path = QFileDialog.getOpenFileName(self, "Select model")
        if os.path.isdir(path[0]):
            QMessageBox.information(self, 'Notice',
                                    u'Please do not select the folder, select the model file')
        else:
            self.model_path = path[0]
            print(self.model_path)
            self.ui.model_path_edit.setText(path[0])

    #用于edit更新输入图像栈路径
    def update_source_path(self):
        path_fusion_dir_path=self.ui.fusion_path_edit.text()
        #检查输入图像栈文件夹是否正确且包含的全是图片
        flag_have_pic = False
        if os.path.isdir(path_fusion_dir_path):  # 检查path是否为一个存在的文件夹
            # 检查是否包含图片
            image_formats = support_format  # 定义常见的图片格式
            files = os.listdir(path_fusion_dir_path)  # 获取文件夹中的所有文件名
            for file in files:  # 遍历每个文件名
                for format in image_formats:  # 遍历每种图片格式
                    if file.endswith(format):  # 如果文件名以图片格式结尾
                        flag_have_pic = True
                        break  # 跳出内层循环，继续下一个文件名
            if flag_have_pic == False:
                QMessageBox.information(self, 'Notice',
                                        u'No pictures in this folder')
            else:
                self.fusion_dir_path = path_fusion_dir_path

        else:
            QMessageBox.information(self, 'Notice',
                                    u'Not a directory')
        QMessageBox.information(self, 'Notice',
                                u'Please make sure that the images in the folder are renamed in ordery')

    #用于edit更新输入图像栈路径
    def update_target_path(self):
        # 检查输出路径是否是一个文件夹
        path_out_dir_path = self.ui.out_put_path_edit.text()
        if os.path.isdir(path_out_dir_path):  # 检查path是否为一个存在的文件夹
            if has_chinese_char(path_out_dir_path):
                QMessageBox.information(self, 'Notice',
                                        u'Output path does not support Chinese characters')
            else:
                self.fusion_output_path=path_out_dir_path
        else:
            QMessageBox.information(self, 'Notice',
                                    u'Not a directory')

    #用于edit更新模型栈路径
    def update_model_path(self):
        #检查模型路径是否正确
        model_path=self.ui.model_path_edit.text()
        if judge_format(model_path):
            self.model_path = model_path
        else:
            QMessageBox.information(self, 'Notice',
                                    u'Not a correct model!')

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

    #用于融合图像栈
    def start_fusion(self):
        #定义确认参数
        CONFIRM=True

        # 进度条置0！表示重新开始融合
        self.ui.fusion_progress.setValue(0)

        #判断必须要的参数是否设置完全
        if not os.path.isdir(self.fusion_dir_path):
            QMessageBox.information(self, 'Notice',
                                    u'Please make sure the path of the image stack folder to be fused is correct')
            CONFIRM=False
        if not os.path.isdir(self.fusion_output_path):
            CONFIRM=False
            QMessageBox.information(self, 'Notice',
                                    u'Please make sure that the output path of the fused image is correct')
        if not (self.model_path.endswith(".ckpt") or self.model_path.endswith(".pth")or self.model_path.endswith(".pt")):
            CONFIRM=False
            QMessageBox.information(self, 'Notice',
                                    u'Please check if the model file is correct')
        #如果必须要的参数都输入了，继续执行
        if CONFIRM==True:
            #确认参数
            img_stack_path=self.fusion_dir_path
            output_path=self.fusion_output_path
            model_path=self.model_path

            #确认输出图像的宽高，如果没有手动输入输出图像的宽高，自动获取，如果手动输入输出图片的宽高，使用手动输入的值
            if self.ui.output_width.text()=='':
                width=get_pic_size_in_dir(img_stack_path)[0]
                height=get_pic_size_in_dir(img_stack_path)[1]
            else:
                width=int(self.ui.output_width.text())
                height=int(self.ui.output_height.text())

            #确认k_size，如果有手动设置的k_size,使用手动设置的k_size，没有则使用自动的1/20 min(width,height)
            if self.ui.edit_kernel.text()!='':
                k_size=int(self.ui.edit_kernel.text())
            else:
                k_size=min(height,width)//20 if (min(height,width)//20)%2!=0 else (min(height,width)//20)+1

            #确认是否使用后处理
            use_post_process=self.ui.btn_post_process.isChecked()
            if use_post_process==True:
                #确认是否使用模糊优化
                use_fuzzy=self.ui.btn_fuzzy.isChecked()
            else:
                use_fuzzy=False

            #确认输入图片的类型,这是是'.xxx'
            source_format=get_first_image_format(img_stack_path)

            #确认输出图片的类型,这是是'xxx'
            target_format=self.ui.comboBox_output_format.currentText()

            #确认是否去噪
            remove_noise=self.ui.btn_remove_noise.isChecked()

            # 进度条置为10,表示数据检查完成开始融合！
            self.ui.fusion_progress.setValue(10)

            #在子进程里面开始融合，融合成功会返回路径地址
            self.fusion_thread = FusionThread(img_stack_path=img_stack_path,output_path=output_path,
                                model_path=model_path,k_size=k_size,use_post_process=use_post_process,
                                use_fuzzy=use_fuzzy,width=width,height=height,source_format=source_format,
                                target_format=target_format,remove_noise=remove_noise)
            save_path=self.fusion_thread.path
            #进度条显示100%
            self.ui.fusion_progress.setValue(100)
        else:
            QMessageBox.information(self, 'Notice',
                                    u'Please check if the input and output are correct')
        QMessageBox.information(self, 'Notice',
                                u'Fusion done,img is save in {}'.format(save_path))

    # 用于安全退出，释放摄像头
    def closeEvent(self, event):
        self.cam.DeInit()
        del self.cam

        # Clear camera list before releasing system
        self.cam_list.Clear()

        # Release system instance
        self.system.ReleaseInstance()

        event.accept()

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

#子对话框用于询问手动设置的k_size
class Ask_k_size_Dialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set kernel")
        self.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint)  # 设置对话框的窗口标志
        self.edit = QLineEdit() # 创建编辑框
        self.button = QPushButton("OK") # 创建按钮
        self.button.clicked.connect(self.accept) # 连接按钮的点击信号和对话框的接受槽函数
        layout = QVBoxLayout() # 创建垂直布局
        layout.addWidget(self.edit) # 添加编辑框到布局中
        layout.addWidget(self.button) # 添加按钮到布局中
        self.setLayout(layout) # 设置对话框的布局

#子线程用于防止主界面卡,但是貌似在cpu环境下貌似还是会卡
class FusionThread(QThread):
    def __init__(self,img_stack_path,output_path,
                                model_path,k_size,use_post_process,
                                use_fuzzy,width,height,source_format,
                                target_format,remove_noise):
        super().__init__()
        self.img_stack_path=img_stack_path
        self.output_path=output_path
        self.model_path=model_path
        self.k_size=k_size
        self.use_post_process=use_post_process
        self.use_fuzzy=use_fuzzy
        self.width=width
        self.height=height
        self.source_format=source_format
        self.target_format=target_format
        self.remove_noise=remove_noise
        self.path=self.fusion()
    def fusion(self):
        path=fusion.stack_fusion(img_stack_path=self.img_stack_path, output_path=self.output_path,
                     model_path=self.model_path, k_size=self.k_size, use_post_process=self.use_post_process,
                     use_fuzzy=self.use_fuzzy, width=self.width, height=self.height, source_format=self.source_format,
                     target_format=self.target_format, remove_noise=self.remove_noise)
        return path.name_path





