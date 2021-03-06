# -*- coding: utf-8 -*-
"""end-to-end.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16zk33xwYSHV_gM9DSV7QuSEsm2sNUwkS
"""

from google.colab import drive
drive.mount('/content/a')

import zipfile

file_name = ['/content/a/My Drive/lip_train.zip']
for file in file_name:
  fz = zipfile.ZipFile(file, 'r')
  for each in fz.namelist():
    fz.extract(each,r'.')
  fz.close()

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Function
import torch.nn.init as init


class ConvFrontend(nn.Module):
    def __init__(self):
        super(ConvFrontend, self).__init__()
        self.conv = nn.Conv3d(3, 64, (5,7,7),stride=(1,2,2),padding=(2,3,3))
        self.norm = nn.BatchNorm3d(64)
        self.pool = nn.MaxPool3d((1,3,3),stride=(1,2,2),padding=(0,1,1))
#         self.conv1 = nn.Conv3d(
#             1,
#             64,
#             kernel_size=7,
#             stride=(1, 2, 2),
#             padding=(3, 3, 3),
#             bias=False)
#         self.bn1 = nn.BatchNorm3d(64)
#         self.relu = nn.ReLU(inplace=True)
#         self.maxpool = nn.MaxPool3d(kernel_size=(3, 3, 3), stride=2, padding=1)

    def forward(self, input):
        #return self.conv(input)
        output = self.pool(F.relu(self.norm(self.conv(input))))
        return output
      
      
      
      
      
      
class NLLSequenceLoss(nn.Module):
    """
    Custom loss function.
    Returns a loss that is the sum of all losses at each time step.
    """
    def __init__(self):
        super(NLLSequenceLoss, self).__init__()
        self.criterion = nn.NLLLoss()

    def forward(self, input, target):
        loss = 0.0

        transposed = input.transpose(0, 1).contiguous()

        for i in range(0, 24):
            loss += self.criterion(transposed[i], target)

        return loss

def _validate(modelOutput, labels):

    averageEnergies = torch.sum(modelOutput.data, 1)

    maxvalues, maxindices = torch.max(averageEnergies, 1)

    count = 0

    for i in range(0, labels.squeeze(1).size(0)):

        if maxindices[i] == labels.squeeze(1)[i]:
            count += 1

    return count

############ LSTM beck-end ###############
class LSTMBackend(nn.Module):
    def __init__(self):
        super(LSTMBackend, self).__init__()
        self.Module1 = nn.LSTM(input_size=256,
                                hidden_size=256,
                                num_layers=2,
                                batch_first=True,
                                bidirectional=True)
        self.drop_layer = nn.Dropout(p=0.2)

        self.fc = nn.Linear(256 * 2, 313)

        self.softmax = nn.LogSoftmax(dim=2)

        self.loss = NLLSequenceLoss()

        self.validator = _validate

    def forward(self, input):

        temporalDim = 1

        lstmOutput, _ = self.Module1(input)
        dropout = self.drop_layer(lstmOutput)
        output = self.fc(dropout)
        output = self.softmax(output)

        return output

        
def _validate2(modelOutput, labels):
    maxvalues, maxindices = torch.max(modelOutput.data, 1)

    count = 0

    for i in range(0, labels.squeeze(1).size(0)):

        if maxindices[i] == labels.squeeze(1)[i]:
            count += 1

    return count
      
      
######### CNN back-end ############
class ConvBackend(nn.Module):
    def __init__(self):
        super(ConvBackend, self).__init__()

        bn_size = 256
        self.conv1 = nn.Conv1d(bn_size,2 * bn_size ,5, 2)
        self.norm1 = nn.BatchNorm1d(bn_size * 2)
        self.pool1 = nn.MaxPool1d(2, 2)

        self.conv2 = nn.Conv1d( 2* bn_size, 4* bn_size,5, 2)
        self.norm2 = nn.BatchNorm1d(bn_size * 4)

        self.linear = nn.Linear(4*bn_size, bn_size)
        self.norm3 = nn.BatchNorm1d(bn_size)
        self.linear2 = nn.Linear(bn_size, 313)

        self.loss = nn.CrossEntropyLoss()

        self.validator = _validate2

    def forward(self, input):

        transposed = input.transpose(1, 2).contiguous()

        output = self.conv1(transposed)
        output = self.norm1(output)
        output = F.relu(output)
        output = self.pool1(output)
        output = self.conv2(output)
        output = self.norm2(output)
        output = F.relu(output)
        output = output.mean(2)
        output = self.linear(output)
        output = self.norm3(output)
        output = F.relu(output)
        output =self.linear2(output)

        return output

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import math
from functools import partial

import torch.nn as nn
import math
import torch.utils.model_zoo as model_zoo


__all__ = ['ResNet', 'resnet18', 'resnet34', 'resnet50', 'resnet101',
           'resnet152']


model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
}


def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                     padding=1, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride,
                               padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class ResNet(nn.Module):

    def __init__(self, block, layers, num_classes=1000):
        self.inplanes = 64
        super(ResNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(4, stride=1)
        self.fc = nn.Linear(512 * block.expansion, num_classes)
        self.bn2 = nn.BatchNorm1d(num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x):

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
#         print(x.size())
        x = self.fc(x)
#         print(x.size())
        x = self.bn2(x)
#         print(x.size())

        return x


def resnet18(pretrained=False, **kwargs):
    """Constructs a ResNet-18 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet18']))
    return model


def resnet34(pretrained=False, **kwargs):
    """Constructs a ResNet-34 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet34']))
    return model


def resnet50(pretrained=False, **kwargs):
    """Constructs a ResNet-50 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet50']))
    return model


def resnet101(pretrained=False, **kwargs):
    """Constructs a ResNet-101 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 23, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet101']))
    return model


def resnet152(pretrained=False, **kwargs):
    """Constructs a ResNet-152 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 8, 36, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet152']))
    return model

class ResNetBBC(nn.Module):
    def __init__(self):
        super(ResNetBBC, self).__init__()
        self.inputdims = 256
        self.batchsize = 20

        self.resnetModel = resnet34(False, num_classes=self.inputdims)

    def forward(self, input):
        

        transposed = input.transpose(1, 2).contiguous()
        
        view = transposed.view(-1, 64, 31, 31)

        output = self.resnetModel(view)
#         print(output.size())
        output = output.view(self.batchsize, -1, 256)
#         print(output.size())

        return output

import torchvision.transforms.functional as functional
import random

class StatefulRandomCrop(object):
    def __init__(self, insize, outsize):
        self.size = outsize
        self.cropParams = self.get_params(insize, self.size)

    @staticmethod
    def get_params(insize, outsize):
        """Get parameters for ``crop`` for a random crop.
        Args:
            insize (PIL Image): Image to be cropped.
            outsize (tuple): Expected output size of the crop.
        Returns:
            tuple: params (i, j, h, w) to be passed to ``crop`` for random crop.
        """
        w, h = insize
        th, tw = outsize
        if w == tw and h == th:
            return 0, 0, h, w

        i = random.randint(0, h - th)
        j = random.randint(0, w - tw)
        return i, j, th, tw

    def __call__(self, img):
        """
        Args:
            img (PIL Image): Image to be cropped.
        Returns:
            PIL Image: Cropped image.
        """

        i, j, h, w = self.cropParams

        return functional.crop(img, i, j, h, w)

    def __repr__(self):
        return self.__class__.__name__ + '(size={0}, padding={1})'.format(self.size, self.padding)

class StatefulRandomHorizontalFlip(object):
    def __init__(self, p=0.5):
        self.p = p
        self.rand = random.random()

    def __call__(self, img):
        """
        Args:
            img (PIL Image): Image to be flipped.
        Returns:
            PIL Image: Randomly flipped image.
        """
        if self.rand < self.p:
            return functional.hflip(img)
        return img

    def __repr__(self):
        return self.__class__.__name__ + '(p={})'.format(self.p)

import os
import pandas as pd
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms


class ReadData(Dataset):

    def __init__(self, image_root, label_root, seq_max_lens, augment=True):
        self.seq_max_lens = seq_max_lens
        self.data = []
        self.data_root = image_root
        self.augmentation = augment
        with open(label_root, 'r', encoding='utf8') as f:
            lines = f.readlines()
            lines = [line.strip().split('\t') for line in lines]
            self.dictionary = sorted(np.unique([line[1] for line in lines])) 
            pic_path = [image_root + '/' + line[0] for line in lines] 
            self.lengths = [len(os.listdir(path)) for path in pic_path]
            
            save_dict = pd.DataFrame(self.dictionary, columns=['dict'])
            save_dict.to_csv('a/My Drive/lipreading_demo/dictionary/dictionary.csv', encoding='utf8', index=None)  #save dict

            self.data = [(line[0], self.dictionary.index(line[1]), length) for line, length in zip(lines, self.lengths)]
            self.data = list(filter(lambda sample: sample[-1] <= self.seq_max_lens, self.data))      


    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        (path, label, pic_nums) = self.data[idx]
        path = os.path.join(self.data_root, path)
        files = [os.path.join(path, ('{}' + '.png').format(i)) for i in range(1, pic_nums+1)]
        files = filter(lambda path: os.path.exists(path), files)
        frames = [cv2.imread(file) for file in files ] 
        frames_ = frames
        # frames_ = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in frames]
        # frames_ = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in frames]
        length = len(frames_)
        channels = 3
        picture_h_w = 124
        vlm = torch.zeros((channels, self.seq_max_lens, picture_h_w, picture_h_w))
        
        croptransform = transforms.CenterCrop((124, 148))
        if(self.augmentation):
          crop = StatefulRandomCrop((164, 164), (124, 148))
          flip = StatefulRandomHorizontalFlip(0.5)

          croptransform = transforms.Compose([
              flip,
              crop
          ])
        
        for i in range(len(frames_)):
            result = transforms.Compose([
                transforms.ToPILImage(),
                transforms.CenterCrop((164, 164)),
                croptransform,
                transforms.Resize((124,124)),
                transforms.ToTensor(),
                transforms.Normalize([0.3663,],[0.1445,]) 
            ])(frames_[i])
            vlm[:, i] = result
        
        return {'volume': vlm, 'label': torch.LongTensor([label]), 'length': length}

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

import re

# from .ConvFrontend import ConvFrontend
# from .ResNetBBC import ResNetBBC
# from .LSTMBackend import LSTMBackend
# from .ConvBackend import ConvBackend

class LipRead(nn.Module):
    def __init__(self):
        super(LipRead, self).__init__()
        self.frontend = ConvFrontend()
        self.resnet = ResNetBBC()
        self.backend = ConvBackend()
        self.lstm = LSTMBackend()

        self.type = "LSTM"

        # def freeze(m):
        #     m.requires_grad=False

        if(self.type == "LSTM-init"):
            # self.frontend.apply(freeze)
            # self.resnet.apply(freeze)
            for param in self.frontend.parameters():
              param.requires_grad = False
            for param in self.resnet.parameters():
              param.requires_grad = False


        # self.frontend.apply(freeze)
        # self.resnet.apply(freeze)

        #function to initialize the weights and biases of each module. Matches the
        #classname with a regular expression to determine the type of the module, then
        #initializes the weights for it.
        def weights_init(m):
            classname = m.__class__.__name__
            if re.search("Conv[123]d", classname):
                m.weight.data.normal_(0.0, 0.02)
            elif re.search("BatchNorm[123]d", classname):
                m.weight.data.fill_(1.0)
                m.bias.data.fill_(0)
            elif re.search("Linear", classname):
                m.bias.data.fill_(0)

        #Apply weight initialization to every module in the model.
        self.apply(weights_init)

    def forward(self, input):
        if(self.type == "temp-conv"):
#             output = self.backend(self.resnet(self.frontend(input)))
              output = self.backend(self.resnet(self.frontend(input)))
            
        if(self.type == "LSTM" or self.type == "LSTM-init"):
            output = self.lstm(self.resnet(self.frontend(input)))
        return output

    def loss(self):
        if(self.type == "temp-conv"):
            return self.backend.loss

        if(self.type == "LSTM" or self.type == "LSTM-init"):
            return self.lstm.loss

    def validator_function(self):
        if(self.type == "temp-conv"):
            return self.backend.validator

        if(self.type == "LSTM" or self.type == "LSTM-init"):
            return self.lstm.validator

import os
import torch
import torchvision
import torch.nn as nn
from datetime import datetime

from torch.utils.data import DataLoader
from torch.autograd import Variable
from torch.utils.data.sampler import SubsetRandomSampler

# from LipReadDataTrain import ReadData
# from LipNet import LipNet, LipSeqLoss
batchsize = 20

train_image_file = os.path.join(os.path.abspath('.'), "lip_train")
train_label_file = os.path.join(os.path.abspath('.'), "a/My Drive/lipreading_demo/data/lip_train.txt")
training_dataset = ReadData(train_image_file, train_label_file, seq_max_lens=24)
valid_dataset = ReadData(train_image_file, train_label_file, seq_max_lens=24, augment=False)

dataset_len = len(training_dataset.data)
indices = list(range(dataset_len))


dataset_len = len(training_dataset.data)
# Randomly splitting indices:
val = True # set to true if validation in local pc
if val:
  validation_split = 0.2
  val_len = int(np.floor(validation_split * dataset_len))
  np.random.seed(123)
  validation_idx = np.random.choice(indices, size=val_len, replace=False)
  train_idx = list(set(indices) - set(validation_idx))
  train_sampler = SubsetRandomSampler(train_idx)
  validation_sampler = SubsetRandomSampler(validation_idx)
  training_data_loader = DataLoader(training_dataset, batch_size=batchsize, sampler=train_sampler, shuffle=False, drop_last = True)
  validation_loader = DataLoader(valid_dataset, batch_size=batchsize, sampler=validation_sampler, shuffle=False, drop_last = True)
else:
  training_data_loader = DataLoader(training_dataset, batch_size=batchsize, shuffle=True, drop_last = True)

import gc
gc.collect()

# GPU
device = torch.device('cuda:0')
# # CPU 
#device = torch.device('cpu')

#Create the model.
model = LipRead().to(device)


if val:
  data_loaders = {"train": training_data_loader, "val": validation_loader}
  data_lengths = {"train": len(train_idx), "val": val_len}

pretrained_dict = torch.load("a/My Drive/lipreading_demo/lstm_init_new/cnn_full_data_epoch_5.pt")

model.load_state_dict(pretrained_dict)

for name, param in model.named_parameters():
    print('name: ', name)
    print(type(param))
    print('param.shape: ', param.shape)
    print('param.requires_grad: ', param.requires_grad)
    print('=====')

batchsize = 20
numworkers = 12
inputdim = 256
hiddendim = 256
numclasses = 313
numlstms = 2

epochs = 30
startepoch = 10
statsfrequency = 1000
learningrate = 0.0005
momentum = 0.9
weightdecay = 0.0001

# patience = 3
# early_stopping = EarlyStopping(patience=patience, verbose=True)

# optimizer = torch.optim.Adam(model.parameters(), lr=learningrate)

def learningRate(epoch):
        decay = math.floor(1 / 31)
        return learningrate * pow(0.5, decay)
    

for epoch in range(1,31):
    print(epoch)
    
    criterion = model.loss().to(device)
#     criterion = criterion.cuda()
    
#     model.train()
    learningrate = learningRate(epoch)
    optimizer = torch.optim.SGD(  model.parameters(),
                        lr = learningrate,
                        momentum = momentum,
                        weight_decay = weightdecay)
    if val:
      for phase in ['train', 'val']:
        count = 0
        total = 0
        if phase == 'train':
#             optimizer = scheduler(optimizer, epoch)
            
            model.train(True)  # Set model to training mode
        else:
            model.train(False)  # Set model to evaluate mode

        running_loss = 0.0
        
#       for i_batch, sample_batched in enumerate(training_data_loader):
        for i_batch, sample_batched in enumerate(data_loaders[phase]):
        
          input_data = Variable(sample_batched['volume']).to(device) 
          labels = Variable(sample_batched['label']).to(device)
          length = Variable(sample_batched['length']).to(device)
          validator_function = model.validator_function()
        
          optimizer.zero_grad()
          outputs = model(input_data) 
  

          
          loss = criterion(outputs, labels.squeeze(1))
          count += validator_function(outputs, labels)
          total += outputs.size(0)
          print(count)
          


          
          # backward + optimize only if in training phase
          if phase == 'train':
            loss.backward()
            # update the weights
            optimizer.step()
#         loss.backward()
#         optimizer.step()
      
        accuracy = count / total
        current_time = datetime.now()
        print("current time:", current_time)
        print("number of epoch:", epoch)
        print('{} Loss: {:.4f}'.format(phase, loss/24))
        print('{} Acc: {:.4f}'.format(phase, accuracy))
    else:
        count = 0
        total = 0
        model.train(True)  # Set model to training mode

        running_loss = 0.0
        
        for i_batch, sample_batched in enumerate(training_data_loader):
        
          input_data = Variable(sample_batched['volume']).to(device) 
          labels = Variable(sample_batched['label']).to(device)
          length = Variable(sample_batched['length']).to(device)
          validator_function = model.validator_function()
        
          optimizer.zero_grad()
          outputs = model(input_data) 
  

          
          loss = criterion(outputs, labels.squeeze(1))
          count += validator_function(outputs, labels)
          total += outputs.size(0)
          print(count)
          


          
          # backward + optimize only if in training phase
          loss.backward()
          # update the weights
          optimizer.step()
#         loss.backward()
#         optimizer.step()
      
        accuracy = count / total
        current_time = datetime.now()
        print("current time:", current_time)
        print("number of epoch:", epoch)
        print('train Loss: {:.4f}'.format(loss/24))
        print('train Acc: {:.4f}'.format(accuracy))
        
#         if phase != 'train':
#           early_stopping(loss, model)
          
#         if early_stopping.early_stop:
#           print("Early stopping")
#           torch.save(model.state_dict(), "a/My Drive/lipreading_demo/weight/checkpoint.pt".format(epoch))
#           break
          
                   
        # save model
        torch.save(model.state_dict(), "a/My Drive/lipreading_demo/lstm_new/end_to_end_epoch_{}.pt".format(epoch))

############################## if dead ###################################


# GPU
device = torch.device('cuda:0')
model = LipRead().to(device)

pretrained = "a/My Drive/lipreading_demo/lstm_new/dropout_final_epoch_29.pt"

model.load_state_dict(torch.load(pretrained))

last_epoch = 29
def myfunc(l,n):
  if n == 0:
    return l
  else:
    n = n - 1
    return l*pow(0.5,n/30)
learningrate = myfunc(0.0005, last_epoch)

learningrate

# patience = 3
# early_stopping = EarlyStopping(patience=patience, verbose=True)

# optimizer = torch.optim.Adam(model.parameters(), lr=learningrate)


def learningRate(epoch):
        decay = math.floor(1 / 31)
        return learningrate * pow(0.5, decay)
    

for epoch in range(last_epoch+1,31):
    print(epoch)
    
    criterion = model.loss().to(device)
#     criterion = criterion.cuda()
    
#     model.train()
    learningrate = learningRate(epoch)
    optimizer = torch.optim.SGD(  model.parameters(),
                        lr = learningrate,
                        momentum = momentum,
                        weight_decay = weightdecay)
  
    for phase in ['train', 'val']:
        count = 0
        total = 0
        if phase == 'train':
#             optimizer = scheduler(optimizer, epoch)
            
            model.train(True)  # Set model to training mode
        else:
            model.train(False)  # Set model to evaluate mode

        running_loss = 0.0
        
#       for i_batch, sample_batched in enumerate(training_data_loader):
        for i_batch, sample_batched in enumerate(data_loaders[phase]):
        
          input_data = Variable(sample_batched['volume']).to(device) 
          labels = Variable(sample_batched['label']).to(device)
          length = Variable(sample_batched['length']).to(device)
          validator_function = model.validator_function()
        
          optimizer.zero_grad()
          outputs = model(input_data) 
  

          
          loss = criterion(outputs, labels.squeeze(1))
          count += validator_function(outputs, labels)
          total += outputs.size(0)
          print(count)
          


          
          # backward + optimize only if in training phase
          if phase == 'train':
            loss.backward()
            # update the weights
            optimizer.step()
#         loss.backward()
#         optimizer.step()
      
        accuracy = count / total
        current_time = datetime.now()
        print("current time:", current_time)
        print("number of epoch:", epoch)
        print('{} Loss: {:.4f}'.format(phase, loss/24))
        print('{} Acc: {:.4f}'.format(phase, accuracy))
        
#         if phase != 'train':
#           early_stopping(loss, model)
          
#         if early_stopping.early_stop:
#           print("Early stopping")
#           torch.save(model.state_dict(), "a/My Drive/lipreading_demo/weight/checkpoint.pt".format(epoch))
#           break
          
                   
        # save model
        torch.save(model.state_dict(), "a/My Drive/lipreading_demo/lstm_new/dropout_final_epoch_{}.pt".format(epoch))
