# -*- coding: utf-8 -*-
# @Author  : XinZhe Xie
# @University  : ZheJiang University

import torch
import torch.nn as nn
from torchvision import transforms
import numpy as np
import os
import net
import glob
import cv2
from PIL import Image
import re
from numba import jit
from numba.typed import List

class stack_fusion():
    def __init__(self,img_stack_path,output_path,model_path,k_size,use_post_process,use_fuzzy,width,height,source_format,target_format,remove_noise):
        self.img_stack_path=img_stack_path
        self.output_path=output_path
        self.model_path=model_path
        self.use_post_process=use_post_process
        self.use_fuzzy=use_fuzzy
        self.width=width
        self.height=height
        self.source_format=source_format
        self.target_format=target_format
        self.remove_noise=remove_noise
        self.k_size = k_size
        #执行函数并且返回保存图片的名字给类对象用于读取！！！
        self.name_path=self.main_fusion()
    def main_fusion(self):
        img_source_type='*'+str(self.source_format)
        #获取图像列表
        pic_sequence_list = glob.glob(os.path.join(self.img_stack_path,img_source_type))
        #根据文件名排序，送入的图片文件名事先需要排序
        # pic_sequence_list.sort(key=lambda x: int(str(re.findall("\d+", x)[0])))  # Sort by the number in the file name
        pic_sequence_list.sort(
            key=lambda x: int(str(re.findall("\d+", x.split('/')[-1])[-1])))  # Sort by the number in the file name
        #创建空列表
        img_cv_list = [None] * (len(pic_sequence_list))
        img_list = [None] * (len(pic_sequence_list))
        sf_list = [None] * (len(pic_sequence_list))
        #定义网络
        model = net.DNWithCA(trainmode=False)
        data_transforms = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])])
        #todo
        # model = nn.DataParallel(model)
        #获取可用的gpu
        num_gpus = torch.cuda.device_count()
        if num_gpus > 1:
            device = torch.device("cuda")
        else:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model.to(device)
        model.load_state_dict(torch.load(self.model_path, map_location=device),strict=False)

        model.eval()

        #read sf list
        for i in range(len(pic_sequence_list)):
            img_list[i] = Image.open(pic_sequence_list[i]).convert('L').resize((self.width, self.height),
                                                                               Image.Resampling.BILINEAR)
            if self.remove_noise == True:
                img_list[i] = np.array(img_list[i])
                img_list[i] = cv2.medianBlur(img_list[i], 5)
                img_list[i] = Image.fromarray(img_list[i].astype('uint8'))
            else:
                pass
            img_list[i] = data_transforms(img_list[i]).unsqueeze(0).to(device)
            sf_list[i] = model(img_list[i]).cpu().numpy()
            print('finish send no.{} pic into the net'.format(str(i)))

        # generate initial decision map
        decisionmap_numpy, sf_numpy = Generate_decisionmap(sf_list,self.height, self.width)

        # Optimization Decision Map
        if self.use_post_process == True:
            decisionmap_np_afterprocess = decisionmap_process(decisionmap_numpy, k_size=self.k_size,
                                                              use_fuzzy_op=self.use_fuzzy)
        else:
            decisionmap_np_afterprocess = decisionmap_numpy

        # fusion step1:create pic list which could be read by cv2
        for i in range(len(pic_sequence_list)):
            img_cv_list[i] = cv2.imread(pic_sequence_list[i])
            img_cv_list[i] = cv2.resize(img_cv_list[i], (self.width, self.height))

        # fusion step2:create final pic
        pic_fusion = Final_fusion(img_cv_list, decisionmap_np_afterprocess, self.height, self.width)
        filename = "fusion_result.{}".format(self.target_format)  # 想要的文件名

        i = 1  # 序号,防止覆盖别的
        while os.path.exists(os.path.join(self.output_path,filename)):  # 检查文件名是否已经存在
            filename = "fusion_result{}.{}".format(str(i),self.target_format)
            i += 1  # 序号加一
        save_path=os.path.join(self.output_path,filename)
        cv2.imwrite(save_path, pic_fusion)
        print('Fusion Done!,and save in {}'.format(save_path))
        return save_path

@jit(nopython=True, cache=True)
def decisionmap_process(input_dm_np, k_size=None, use_fuzzy_op=None):
    img_height, img_width = input_dm_np.shape[0], input_dm_np.shape[1]
    padding_len = k_size // 2
    pad_img = np.zeros((img_height + 2 * padding_len, img_width + 2 * padding_len)).astype(np.int64)
    for i in range(pad_img.shape[1]):
        for j in range(pad_img.shape[0]):
            if i > padding_len - 1 and j > padding_len - 1 and i < pad_img.shape[1] - padding_len and j < \
                    pad_img.shape[0] - padding_len:
                pad_img[j][i] = int(input_dm_np[j - padding_len][i - padding_len])
            else:
                pad_img[j][i] = -1
    new_img = np.zeros((img_height, img_width)).astype(np.int64)
    for i in range(img_height):
        for j in range(img_width):
            # get original Value
            original_Value = pad_img[i + padding_len, j + padding_len]
            # get matrix
            moving_matrix = pad_img[i:i + 2 * padding_len + 1, j:j + 2 * padding_len + 1].flatten()
            # delete pidding value -1
            moving_matrix = moving_matrix[moving_matrix != -1]
            # get max min ,med,most_fre
            moving_most_fre = np.argmax(np.bincount(moving_matrix))
            if use_fuzzy_op == True:
                new_img[i][j] = int(np.median(moving_matrix))
            else:
                if original_Value == moving_most_fre:
                    new_img[i][j] = original_Value
                else:
                    new_img[i][j] = moving_most_fre
    return new_img

#这三个函数不能放在类里面,numba不支持
@jit(nopython=True, cache=True)
def Final_fusion(in_img_cv_list, in_decisionmap, height, width):  # Function is compiled and runs in machine code
    pic_fusion = np.zeros((height, width, 3), dtype=np.int64)
    pic_fusion_height = pic_fusion.shape[0]
    pic_fusion_width = pic_fusion.shape[1]
    pic_fusion_channels = pic_fusion.shape[2]
    for row in range(pic_fusion_height):
        for col in range(pic_fusion_width):
            for channel in range(pic_fusion_channels):
                pic_fusion[row, col, channel] = in_img_cv_list[in_decisionmap[row, col]][row, col, channel]
    return pic_fusion


@jit(nopython=True, cache=True)
def Generate_decisionmap(sf_list,height,width):
    sf_numba_list = List(sf_list)
    sf_num_np = np.zeros(shape=((height, width)))
    decisionmap_np = np.zeros((height, width), dtype=np.int64)
    for i in range(len(sf_numba_list)):
        for a in range(sf_num_np.shape[0]):
            for b in range(sf_num_np.shape[1]):
                if sf_numba_list[i][a][b] >= sf_num_np[a][b]:
                    sf_num_np[a][b] = sf_numba_list[i][a][b]
                    decisionmap_np[a][b] = int(i)
    return decisionmap_np, sf_num_np
