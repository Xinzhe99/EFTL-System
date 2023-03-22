# -*- coding: utf-8 -*-
# @Author  : XinZhe Xie
# @University  : ZheJiang University

import torch
import torch.nn as nn
import torch.nn.functional as f

class h_sigmoid(nn.Module):
    def __init__(self, inplace=True):
        super(h_sigmoid, self).__init__()
        self.relu = nn.ReLU6(inplace=inplace)
    def forward(self, x):
        return self.relu(x + 3) / 6
class h_swish(nn.Module):
    def __init__(self, inplace=True):
        super(h_swish, self).__init__()
        self.sigmoid = h_sigmoid(inplace=inplace)
    def forward(self, x):
        return x * self.sigmoid(x)
class CoordAtt(nn.Module):
    def __init__(self, inp, oup, reduction=32, threshold=8):     # dafault=32, dafault=8
        super(CoordAtt, self).__init__()
        self.pool_h = nn.AdaptiveAvgPool2d((None, 1))
        self.pool_w = nn.AdaptiveAvgPool2d((1, None))
        mip = max(threshold, inp // reduction)
        self.conv1 = nn.Conv2d(inp, mip, kernel_size=1, stride=1, padding=0)
        self.bn1 = nn.BatchNorm2d(mip)
        self.act = h_swish()
        self.conv_h = nn.Conv2d(mip, oup, kernel_size=1, stride=1, padding=0)
        self.conv_w = nn.Conv2d(mip, oup, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        identity = x
        n, c, h, w = x.size()
        x_h = self.pool_h(x)
        x_w = self.pool_w(x).permute(0, 1, 3, 2)
        y = torch.cat([x_h, x_w], dim=2)
        y = self.conv1(y)
        y = self.bn1(y)
        y = self.act(y)
        x_h, x_w = torch.split(y, [h, w], dim=2)
        x_w = x_w.permute(0, 1, 3, 2)
        a_h = self.conv_h(x_h).sigmoid()
        a_w = self.conv_w(x_w).sigmoid()
        out = identity * a_w * a_h
        return out

class DNWithCA(nn.Module):
    def __init__(self , trainmode=True):
        super(DNWithCA, self).__init__()
        self.conv0=self.conv_block(1,16)
        self.conv1 = self.conv_block(16, 16)
        self.ca0_1=CoordAtt(16,16)
        self.conv2 = self.conv_block(16, 16)
        self.ca2 = CoordAtt(32, 32)
        self.conv3 = self.conv_block(32, 16)
        self.ca3 = CoordAtt(48, 48)
        self.conv4 = self.conv_block(48, 16)
        self.conv_decode_1 = self.conv_block(80,64)
        self.conv_decode_2 = self.conv_block(64,48)
        self.conv_decode_3 = self.conv_block(48,32)
        self.conv_decode_4 = self.conv_block(32,16)
        self.conv_decode_5 = self.conv_block(16, 1)
        if trainmode:
            self.phase = 'train'
        else:
            self.phase = 'fusion'
    def forward(self, img1, img2=None, kernel_radius=5):
        if self.phase=='train':
            conv_block0=self.conv0(img1)
            ca_block0=self.ca0_1(conv_block0)
            conv_block1=self.conv1(ca_block0)
            ca_block1=self.ca0_1(conv_block1)
            conv_block2=self.conv2(ca_block1)
            cat1=self.concat(conv_block2,ca_block0)
            ca_block2=self.ca2(cat1)
            conv_block3=self.conv3(ca_block2)
            cat2=self.concat(ca_block1,conv_block3)
            cat2 = self.concat(cat2, ca_block0)
            ca_block3 = self.ca3(cat2)
            conv_block4 = self.conv4(ca_block3)
            cat3 = self.concat(conv_block4,ca_block2)
            cat3 = self.concat(cat3, ca_block1)
            cat3 = self.concat(cat3, ca_block0)
            #decode
            decode_block1 = self.conv_decode_1(cat3)
            decode_block2 = self.conv_decode_2(decode_block1)
            decode_block3 = self.conv_decode_3(decode_block2)
            decode_block4= self.conv_decode_4(decode_block3)
            output = self.conv_decode_5(decode_block4)
            return output
        else:
            with torch.no_grad():
                #ENCODE
                conv_block0 = self.conv0(img1)
                ca_block0 = self.ca0_1(conv_block0)
                conv_block1 = self.conv1(ca_block0)
                ca_block1 = self.ca0_1(conv_block1)
                conv_block2 = self.conv2(ca_block1)
                cat1 = self.concat(conv_block2, ca_block0)
                ca_block2 = self.ca2(cat1)
                conv_block3 = self.conv3(ca_block2)
                cat2 = self.concat(ca_block1, conv_block3)
                cat2 = self.concat(cat2, ca_block0)
                ca_block3 = self.ca3(cat2)
                conv_block4 = self.conv4(ca_block3)
                cat3 = self.concat(conv_block4, ca_block2)
                cat3 = self.concat(cat3, ca_block1)
                cat3 = self.concat(cat3, ca_block0)
                # decode
                output = self.fusion_channel_sf(cat3, kernel_radius=kernel_radius)
                return output

    @staticmethod
    def fusion_channel_sf(f1, kernel_radius=5):#default=5
        """
        Perform channel sf fusion two features
        """
        device = f1.device
        b, c, h, w = f1.shape#假设[1,80,5,5]
        r_shift_kernel = torch.FloatTensor([[0, 0, 0], [1, 0, 0], [0, 0, 0]])\
            .reshape((1, 1, 3, 3)).repeat(c, 1, 1, 1).to(device) #卷积核weight.shape=[out_channels,in_channels,h,w]  这里c==out_channels
        b_shift_kernel = torch.FloatTensor([[0, 1, 0], [0, 0, 0], [0, 0, 0]])\
            .reshape((1, 1, 3, 3)).repeat(c, 1, 1, 1).to(device)  #需要输出维度个卷积核 所以要repeat成c个
        f1_r_shift = f.conv2d(f1, r_shift_kernel, padding=1, groups=c).to(device)#每组计算被in_channels/groups个channels的卷积核计算
        f1_b_shift = f.conv2d(f1, b_shift_kernel, padding=1, groups=c).to(device)#对输入tensor f1 进行卷积操作，卷积核为x_shift_kernel 且都用同一个卷积核计算
        f1_grad = torch.sqrt(torch.pow((f1_r_shift - f1), 2) + torch.pow((f1_b_shift - f1), 2)).to(device)#RF^2+CF^2  RF与SF 两幅特征图相加的图
        kernel_size = kernel_radius * 2 + 1   #2R+1
        add_kernel = torch.ones((c, 1, kernel_size, kernel_size)).float().to(device)#[80,1,11,11]
        kernel_padding = kernel_size // 2 #padding==5
        f1_sf = torch.sum(f.conv2d(f1_grad, add_kernel, padding=kernel_padding, groups=c), dim=1).to(device)
        f1_sf_np = f1_sf.squeeze().cpu().numpy()
        return f1_sf_np

    @staticmethod
    def concat(f1, f2):
        """
        Concat two feature in channel direction
        """
        return torch.cat((f1, f2), 1)
    @staticmethod
    def conv_block(in_channels, out_channels, kernel_size=3):
        """
        The conv block of common setting: conv -> relu -> bn
        In conv operation, the padding = 1
        :param in_channels: int, the input channels of feature
        :param out_channels: int, the output channels of feature
        :param kernel_size: int, the kernel size of feature
        :return:
        """
        block = torch.nn.Sequential(
                    torch.nn.Conv2d(kernel_size=kernel_size, in_channels=in_channels, out_channels=out_channels, padding=1),
                    torch.nn.ReLU(),
                    torch.nn.BatchNorm2d(out_channels),
                )
        return block
# img=torch.rand(1,1,5,5)
# print(img)
# net=DNWithCA(trainmode=False)
# out=net(img)
# print(out)
