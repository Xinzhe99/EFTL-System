from PyQt5 import uic
import PySpin
from PyQt5.QtGui import QImage, QPixmap
import os
from PyQt5.QtCore import QTimer,QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QApplication
from tools import config_model_dir
import cv2
from lens import Lens
import time
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
flag_save_number = 1  # flag定义全局变量 图片保存的序号默认从1开始

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('E:\图像融合系统\Codes\design_meun.ui')  # 加载designer设计的ui程序
        print(self.ui.__dict__)
        self.camera_system = PySpin.System.GetInstance()
        self.cam_list = self.camera_system.GetCameras()
        self.cam = self.cam_list[0]
        self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
        self.sNodemap = self.cam.GetTLStreamNodeMap()#获取传输层流节点映射,传输层流是指相机和主机之间的数据流，它可以通过不同的传输协议来实现

        #启动按钮
        btn_start_capture=self.ui.btn_begin_caputre #获取相机画面按钮
        btn_start_capture.clicked.connect(self.start_capture)
        #停止按钮
        btn_stop_capture=self.ui.btn_stop_caputre#停止获取画面的按钮
        btn_stop_capture.clicked.connect(self.stop_capture)
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
        # 创建一个QTimer对象用于保存图片
        self.img_save_timer = QTimer()
        # 连接定时器的timeout信号到槽函数
        self.img_save_timer.timeout.connect(self.save_one_img)
        # 显示相机信息的标签
        self.lb_video_inf = self.ui.video_inf
        # 显示相机数量的标签
        self.lb_num_cam = self.ui.video_num

        self.btn_autu_exposure=self.ui.btn_Auto_Exposure#绑定自动曝光按钮
        self.btn_autu_exposure.setChecked(True)#自动曝光初始化默认开启

        #修改曝光模式
        self.btn_autu_exposure.stateChanged.connect(self.change_exposure_mode)

        self.exposure_time_slider=self.ui.exp_control#绑定手动调节曝光的slider
        self.exposure_time_slider.setRange(0, 30000.0)#设置slider的上下限
        self.exposure_time_slider.valueChanged.connect(self.set_exposure)#绑定曝光时间设置函数
        self.exposure_time_slider.setEnabled(False)  # 初始化冻结slider
        self.lb_exp_show=self.ui.exp_show#显示曝光时间

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



    #用于初始化相机并且开启定时器捕获图像
    def start_capture(self):
        #获取相机版本型号
        cam_version = self.camera_system.GetLibraryVersion()
        self.lb_video_inf.setText('Library version: %d.%d.%d.%d' % (
            cam_version.major, cam_version.minor, cam_version.type, cam_version.build))

        # 获取相机数量,这里只支持一个!
        num_cameras = self.cam_list.GetSize()
        self.lb_num_cam.setText('%d' % num_cameras)

        #相机初始化
        self.cam.Init()
        print('camera finish init ')


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

        #用定时器来获取新的图像
        self.timer_video.start(0)

        # 用定时器来更新曝光时间显示的标签
        self.exp_show_timer.start(0)

        self.btn_save_pictures.setEnabled(True)
        self.btn_stop_save_pictures.setEnabled(True)
    #用于关闭相机
    def stop_capture(self):
        lb_video_inf = self.ui.video_inf
        lb_video_inf.setText('End EndAcquisition!')
        self.ui.video_num.setText('0')
        self.timer_video.stop()
        self.cam.EndAcquisition()
        print('End EndAcquisition!')

    #用于定时器获取一张图像并显示出来
    def update_image(self):
        #根据曝光时间调整获取延迟
        timeout = 0
        real_exp_time=self.cam.ExposureTime.GetValue()#us
        self.real_exp_time=real_exp_time
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
            self.save_img_sub_thread=Save_img(data=image_data_np,path=self.pic_save_path,save_format='jpg')
            self.need_save_fig=False#保存flag置为False,等待下一次置为True

        #显示
        image_pixmap = QPixmap.fromImage(QImage(image_data_np.data, image_data_np.shape[1], image_data_np.shape[0], QImage.Format_Grayscale8))
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
        if self.btn_autu_exposure.isChecked():
            self.exposure_time_slider.setValue(int(self.cam.ExposureTime.GetValue()))
            self.exposure_time_slider.setEnabled(False)
            self.Reset_exposure()
            print('自动曝光开启')
        else:
            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.exposure_time_slider.setEnabled(True)
            print('自动曝光关闭')

    #用于获取保存路径,并且创建保存文件夹,并保存在类对象里,返回最终保存路径
    def get_save_path(self):
        dialog_save_path = QFileDialog.getExistingDirectory(self, "choose save path")
        self.ui.label_save_path_state.setText('Save path is set')
        self.pic_save_path = config_model_dir(project_dir=dialog_save_path, resume=False, subdir_name='imagestacks')#增量式创文件夹，子文件夹名字叫imagestacks
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
        input_diopter=float(self.ui.diopter_input_edit.text())
        min_diop, max_diop = self.lens.to_focal_power_mode()
        # 检查输入是否正确
        if input_diopter < max_diop and input_diopter > min_diop:
            self.lens.set_diopter(input_diopter)
            self.ui.lb_diop_show.setText(str(self.lens.get_diopter()))
        else:
            QMessageBox.information(self, 'Notice',u'Please enter the correct diopter!Diopter value should be between {} and {}'.format(min_diop,max_diop))

    # 用于重置透镜屈光度
    def reset_diopter(self):
        self.lens.set_diopter(0)

    # 用于屈光度变化循环
    def begin_cycle(self):
        min_diop, max_diop = self.lens.to_focal_power_mode()
        max_cycle = self.ui.max_diopter_input.text()
        min_cycle = self.ui.min_diopter_input.text()
        step = self.ui.step_diopter_input.text()
        cycle = self.ui.cycle_diopter_input.text()

        max_cycle = float(max_cycle)
        min_cycle = float(min_cycle)
        step = float(step)
        cycle = float(cycle) #s

        #判断输入是否正确
        if max_cycle < max_diop and min_cycle > min_diop:
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

            #如果需要来回拍而不是从头拍到尾
            if not self.ui.btn_save_pic_zoom_2.isChecked():
                #从最大开始拍到最小
                real_diop = max_cycle

                for i in range(int(times)):
                    self.lens.set_diopter(real_diop)
                    real_diop-=step
                    time.sleep(every_time/1000)#time.sleep(s)
                    # 获取当前屈光度并显示
                    now_diop=self.lens.get_diopter()#获取屈光度
                    self.ui.lb_diop_show_2.setText(str(now_diop))
                    QApplication.processEvents()
                #停止保存图像
                self.img_save_timer.stop()
            #从头拍到尾
            else:
                # 先从最大开始拍到最小
                real_diop = max_cycle
                for i in range(int(times)):
                    self.lens.set_diopter(real_diop)
                    real_diop-=step
                    time.sleep(every_time/1000)#time.sleep(s)
                    # 获取当前屈光度并显示
                    now_diop=self.lens.get_diopter()#获取屈光度
                    self.ui.lb_diop_show_2.setText(str(now_diop))
                    QApplication.processEvents()

                # 再从最小开始拍到最大
                real_diop = min_cycle
                for i in range(int(times)):
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



#子线程用来保存图片，不影响主线程显示
class Save_img(QThread):
    # 定义一个信号，用于通知主线程任务完成
    def __init__(self,data,path,save_format):
        self.image=data
        self.save_path=path
        self.save_format='.'+save_format
        self.save()
    # 重写run方法
    def save(self):
        global flag_save_number#定义在文件头
        cv2.imwrite(os.path.join(self.save_path,str(flag_save_number)+ self.save_format), self.image)
        print('img{}.jpg has been saved in {}'.format(flag_save_number,self.save_path + '/'+str(flag_save_number)+'.jpg'))
        flag_save_number += 1#增量式创建，图片按先后排序

