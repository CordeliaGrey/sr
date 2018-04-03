# coding: utf-8



from __future__ import print_function, absolute_import, division

import argparse
import numpy as np
import torch
from PIL import Image
from torch.autograd import Variable
from torchvision.transforms import ToTensor, ToPILImage

from sr.algorithm.model import Generator
from website.settings import BASE_DIR
import os
import hashlib
import time


from concurrent.futures.thread import ThreadPoolExecutor

from skimage.io import imread, imsave
from skimage.transform import resize
from skimage.measure import compare_psnr
import numpy as np


def get_range(length, segment_length):
    times = length // segment_length
    ret = []
    for i in range(times):
        ret.append((i*segment_length, (i+1) * segment_length))
    if length % segment_length != 0:
        ret.append((times*segment_length, length))
    return ret


def crop_image(image):
    ret = []
    image = imread(image)

    height = image.shape[0]
    width = image.shape[1]
    # print("width", width)
    # print("height", height)
    width_ranges = get_range(width, 320)
    height_ranges = get_range(height, 240)
    for height_range in height_ranges:
        for width_range in width_ranges:

            ret.append(image[height_range[0]:height_range[1], width_range[0]:width_range[1], :])
    return ret, height_ranges, width_ranges, image.shape


def compose_image(images, origin_shape, scale_factor, height_range, width_range):
    width = origin_shape[1] * scale_factor
    height = origin_shape[0] * scale_factor
    ret = np.zeros((height, width, 3))
    print(ret.shape)
    for h in range(len(height_range)):
        for w in range(len(width_range)):

            # print("height_range[h][0]*2:", height_range[h][0]*2)
            # print("height_range[h][1]*2:", height_range[h][1]*2)
            # print("width_range[w][0]*2:", width_range[w][0]*2)
            # print("width_range[w][1]*2:", width_range[w][1]*2)
            # print("\n")
            ret[height_range[h][0]*2: height_range[h][1]*2, width_range[w][0]*2: width_range[w][1]*2, :] = images[h*len(width_range) + w]

    return ret

class SuperResolutioner(object):



    def __init__(self, mode):

        #self.model_paths = model_paths
        print("base dir: {}".format(BASE_DIR))
        self.isFinished = False
        self.mode = mode
        self.model = {}
        self.model["2"] = self._initModel(2, mode)
        self.model["4"] = self._initModel(4, mode)
        self.model["8"] = self._initModel(8, mode)
        self.workers = ThreadPoolExecutor(max_workers=4)
        self.md5 = hashlib.md5()



    def _initModel(self, upscale_factor, mode):
        model = Generator(upscale_factor).eval()
        if mode == "gpu":
            if torch.cuda.is_available():
                model = model.cuda()
            model.load_state_dict(torch.load(r"{}/sr/algorithm/models/netG_epoch_{}_100.pth".format(BASE_DIR, upscale_factor)))
        else:
            model.load_state_dict(torch.load(r"{}/sr/algorithm/models/netG_epoch_{}_100.pth".format(BASE_DIR, upscale_factor), map_location=lambda storage, loc: storage))
        return model

    def proc(self, image_filname, upscale_factor=2):
        self.future = self.workers.submit(self._proc, image_filname, upscale_factor)
        # print('result:%s' % self.future.result()[1])
        return self.future.result()



    def _proc(self, image_filename, upscale_factor=2):
        print("starting process........")
        self.isFinished = False
        if self.mode == "gpu":
            if torch.cuda.is_available():
                print("using cuda.......")
                image = image.cuda()
        images, height_range, width_range, origin_shape = crop_image(image_filename)
        out_images = []
        for image in images:
            image = Variable(ToTensor()(image), volatile=True).unsqueeze(0)
            out = self.model[str(upscale_factor)](image)
            out_images.append(np.array(ToPILImage()(out[0].data.cpu())))

        resized_image = compose_image(out_images, origin_shape, 2, height_range, width_range)
        image_PIL = Image.fromarray(np.uint8(resized_image))
        try:
            self.md5.update(str(time.time()).encode("utf8"))
            saved_image_filename = os.path.join(BASE_DIR, "sr", "static", "processed", 'out_srf_' + str(upscale_factor) +
                                            '_' + str(self.md5.hexdigest()) + os.path.basename(image_filename))
            print("saved_filename: {}".format(saved_image_filename))
            image_PIL.save(saved_image_filename)
        except Exception as e:
            print(e)
        self.isFinished = True
        print("ending process........")
        return True, saved_image_filename


        '''
        原来的代码
        '''
        # print("starting process........")
        # self.isFinished = False
        # image = Image.open(image_filename)
        # image = Variable(ToTensor()(image), volatile=True).unsqueeze(0)
        #
        # if self.mode == "gpu":
        #     if torch.cuda.is_available():
        #         print("using cuda.......")
        #         image = image.cuda()
        # print("processing.......")
        # out = self.model[str(upscale_factor)](image)
        # print("processed.....")
        # try:
        #     out_img = ToPILImage()(out[0].data.cpu())
        #     self.md5.update(str(time.time()).encode("utf8"))
        #     saved_image_filename = os.path.join(BASE_DIR, "sr", "static", "processed", 'out_srf_' + str(upscale_factor) +
        #                                     '_' + str(self.md5.hexdigest()) + os.path.basename(image_filename))
        #     print("saved_filename: {}".format(saved_image_filename))
        #     out_img.save(saved_image_filename)
        # except Exception as e:
        #     print(e)
        # self.isFinished = True
        # print("ending process........")
        # return True, saved_image_filename

    def IsFinished(self):
        return self.isFinished

    def GetSavedFilename(self):
        if not self.IsFinished():
            return None
        else:
            return os.path.basename(self.future.result()[1])
            # return os.path.join(BASE_DIR, "sr", "static", "processed", os.path.basename(self.future.result()[1]))



if __name__ == "__main__":
    sr = SuperResolutioner("cpu")
    start_time = time.time()
    sr.proc("{}/upload/y_1.jpg".format(BASE_DIR))
    end_time = time.time()
    print('处理时间：%d' % (end_time-start_time))



