# coding: utf-8

from __future__ import print_function, absolute_import, division

import json
import os

import _thread
import cv2
import filetype
from django.http.response import HttpResponse
from django.shortcuts import render
from skimage.io import imread
from skimage.measure import compare_psnr, compare_ssim

from sr.algorithm.sr_algo import SuperResolutioner
from website.settings import BASE_DIR

# Create your views here.

print("initializing super resolutioner.....")
sr = SuperResolutioner('cpu')
print("super resolutioner has initialized......")


def shrink(ori_pic):
    img = cv2.imread(ori_pic,-1)
    if type(img) == 'NoneType':
        print("Error: could not load image")
        os._exit(0)

    height, width = img.shape[:2]
    size = (int(width * 0.5), int(height * 0.5))
    shrink = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    cv2.imwrite("{}/temp/shrink_pic.jpg".format(BASE_DIR), shrink, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

def GetPSNR_SSIM(groundtruth, test):
    gd = imread(groundtruth)
    tt = imread(test)
    return compare_psnr(gd, tt), compare_ssim(gd, tt, multichannel=True)


# sr = SuperResolutioner("cpu")
# start_time = time.time()
# pic_path = "{}/upload/y_1.jpg".format(BASE_DIR)
# # shrink(pic_path)
# sr.proc(pic_path)
# end_time = time.time()
# print('处理时间：%d' % (end_time - start_time))


def get_index(request):
    return render(request, "index.html")


def on_file_upload(request):
    ret = {}
    if len(request.FILES) == 0:
        return
    upload_file = request.FILES.get('file', None)
    if upload_file is None:
        return
    upload_file_name = upload_file.name
    file_handle = upload_file.file
    file_binary = file_handle.read()
    with open("{}/temp/ori_pic.jpg".format(BASE_DIR), 'wb') as f:
        f.write(file_binary)

    kind = filetype.guess("{}/temp/ori_pic.jpg".format(BASE_DIR))
    if kind is None:
        return

    shrink("{}/temp/ori_pic.jpg".format(BASE_DIR))


    print("to do super resolution.....")
    _thread.start_new_thread(sr_proc, ("{}/temp/shrink_pic.jpg".format(BASE_DIR),))
    # sr.proc("{}/temp/shrink_pic.jpg".format(BASE_DIR))
    # print("super resolution has is_finished")

    # os.remove("{}/temp/temp.jpg".format(BASE_DIR))

	
    ret['code'] = 200
    return HttpResponse(json.dumps(ret), content_type='application/json')

def sr_proc(pic):
    sr.proc(pic)
    return

def is_finished(request):
    ret = {}
    ret['code'] = 200
    ret['sr_status'] = sr.IsFinished()
    if sr.IsFinished():
        processed_filename = sr.GetSavedFilename()
        ret['processed_filename'] = processed_filename
        processed_filename_path = os.path.join(BASE_DIR, "sr", "static", "processed", processed_filename)
        print("文件路径为：", processed_filename_path)
        res = GetPSNR_SSIM("{}/temp/ori_pic.jpg".format(BASE_DIR), processed_filename_path)
        ret['psnr'] = res[0]
        ret['ssim'] = res[1]
    return HttpResponse(json.dumps(ret), content_type='application/json')

def on_query_processed_image(request):
    processed_filename = request.GET['processed_image_filename']
    ret = {}
    ret['processed_image_path'] = r"/static/processed/{}".format(processed_filename)
    return HttpResponse(json.dumps(ret), content_type='application/json')




