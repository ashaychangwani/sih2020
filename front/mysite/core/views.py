import keras.backend.tensorflow_backend as tb
tb._SYMBOLIC_SCOPE.value = True
from segmentation_models import get_preprocessing
from keras.models import model_from_json
from keras.preprocessing.image import ImageDataGenerator
import keras
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage

import cv2,os
from keras.models import load_model
import numpy as np
from keras.preprocessing import image

import glob
import shutil
import random
from PIL import Image
import PIL

import send_email


import warnings
warnings.filterwarnings("ignore")


json_file = open(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_binary.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model_binary = model_from_json(loaded_model_json)
model_binary.load_weights(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_binary.h5")



json_file = open(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_multi.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model_multi = model_from_json(loaded_model_json)
model_multi.load_weights(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_multi.h5")


json_file = open(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_1.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model_segment_1 = model_from_json(loaded_model_json)
model_segment_1.load_weights(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_1.h5")


json_file = open(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_2.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model_segment_2 = model_from_json(loaded_model_json)
model_segment_2.load_weights(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_2.h5")


json_file = open(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_3.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model_segment_3 = model_from_json(loaded_model_json)
model_segment_3.load_weights(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_3.h5")


json_file = open(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_4.json", 'r')
loaded_model_json = json_file.read()
json_file.close()
model_segment_4 = model_from_json(loaded_model_json)
model_segment_4.load_weights(
    "C:/Users/Ashay/content/drive/My Drive/severstal_february/severstal_model/model_segment_4.h5")


preprocess = get_preprocessing('efficientnetb1')


class test_DataGenerator_3(keras.utils.Sequence):
    def __init__(self, df, batch_size=1, image_path='C:/Users/Ashay/content/raw_data/',
                 preprocess=None, info={}):
        super().__init__()
        self.df = df
        self.batch_size = batch_size
        self.preprocess = preprocess
        self.info = info
        self.data_path = image_path
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.df) / self.batch_size))

    def on_epoch_end(self):
        self.indexes = np.arange(len(self.df))

    def __getitem__(self, index):
        '''
        The DataGenerator takes ImageIds of batch size 1 and returns Image array to the model.
        With the help of ImageIds the DataGenerator locates the Image file in the path, the image is read and resized from
        256x1600 to 256x800.
        '''
        X = np.empty((self.batch_size, 256, 800, 3), dtype=np.float32)
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
        for i, f in enumerate(self.df['ImageId'].iloc[indexes]):
            self.info[index*self.batch_size+i] = f
            X[i, ] = Image.open(self.data_path + f).resize((800, 256))
        if self.preprocess != None:
            X = self.preprocess(X)
        return X


def area(i):
    '''
    Input: EncodedPixels (str)
    Output: number of pixels having the defect
    '''
    return sum([int(k) for k in i.split(' ')[1::2]])


def pred_classification(X):
    '''
    Input: ImageIds in form of a dataframe
    Return: Predictions of classification models
    '''

    data_generator= ImageDataGenerator(rescale=1./255).flow_from_dataframe(dataframe=X, directory='C:\\Users\\Ashay\\content\\raw_data\\',x_col="ImageId", class_mode=None,target_size=(256, 512), batch_size=1, shuffle=False)
    data_preds_binary = model_binary.predict_generator(
        data_generator, verbose=0)
    data_preds_multi_label = model_multi.predict_generator(
        data_generator, verbose=0)
    data_classification = pd.DataFrame(data_preds_multi_label, columns=[
                                       'defect_1', 'defect_2', 'defect_3', 'defect_4'])
    data_classification['hasDefect'] = data_preds_binary
    data_classification['ImageId'] = X['ImageId']
    return data_classification[['ImageId', 'hasDefect', 'defect_1', 'defect_2', 'defect_3', 'defect_4']]


def rle2mask(mask_rle, shape=(1600, 256)):
    '''
    mask_rle: run-length as string formated (start length)
    shape: (width,height) of array to return 
    Returns numpy array, 1 - mask, 0 - background

    '''
    s = mask_rle.split()
    starts, lengths = [np.asarray(x, dtype=int)
                       for x in (s[0:][::2], s[1:][::2])]
    starts -= 1
    ends = starts + lengths
    img = np.zeros(shape[0]*shape[1], dtype=np.uint8)
    for lo, hi in zip(starts, ends):
        img[lo:hi] = 1
    return img.reshape(shape).T


def mask2rle(img):
    '''
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formated
    '''
    pixels = img.T.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return ' '.join(str(x) for x in runs)


def pred_segmentation(X):

    # Train dataset prediction visualization
    ep1 = model_segment_1.predict_generator(
        test_DataGenerator_3(X, preprocess=preprocess), verbose=1)
    ep2 = model_segment_2.predict_generator(
        test_DataGenerator_3(X, preprocess=preprocess), verbose=1)
    ep3 = model_segment_3.predict_generator(
        test_DataGenerator_3(X, preprocess=preprocess), verbose=1)
    ep4 = model_segment_4.predict_generator(
        test_DataGenerator_3(X, preprocess=preprocess), verbose=1)

    '''
    ep1 = mask2rle(np.array((Image.fromarray((test_preds_1[0,:,:,0])>=0.5)).resize((1600,256))).astype(int))
    ep2 = mask2rle(np.array((Image.fromarray((test_preds_2[0,:,:,0])>=0.5)).resize((1600,256))).astype(int))
    ep3 = mask2rle(np.array((Image.fromarray((test_preds_3[0,:,:,0])>=0.5)).resize((1600,256))).astype(int))
    ep4 = mask2rle(np.array((Image.fromarray((test_preds_4[0,:,:,0])>=0.5)).resize((1600,256))).astype(int))
    
    #tmp=[X.ImageId.iloc[0],ep1,ep2,ep3,ep4]
    

    #return pd.DataFrame(tmp,columns=['ImageId','EncodedPixels_1','EncodedPixels_2','EncodedPixels_3','EncodedPixels_4'])
    
    fig, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(20, 13))
    c1 = Image.fromarray(test_preds_3[0,:,:,0])
    ax3.imshow(np.array(c1.resize((1600,256)))>0.5)
    ax3.set_title('Predicted Mask')
    plt.show()
    '''
    tmp = [X.ImageId[0], ep1, ep2, ep3, ep4]

    return pd.DataFrame([tmp], columns=['ImageId', 'EncodedPixels_1', 'EncodedPixels_2', 'EncodedPixels_3', 'EncodedPixels_4'])


def pred_combined(X):
    '''
    Input: ImageId (dataframe)
    Return: Comdined dataframe of output of pred_classification function and pred_segmentation function
    '''
    return (pred_classification(X).merge(pred_segmentation(X), on=['ImageId']))


def steel_prediction(X):
    '''
    Function-1:
    Input: ImageId(dataframe)
    Process: Calls pred_combined which calls pred_classification and pred_segmentation
            Applies thresholds -> area and classification probability
    Return: DataFrame (columns = ImageId_ClassId,EncodedPixels)
    
    '''
    p = pred_combined(X).iloc[0]
    tmp = []
    j, b, m1, m2, m3, m4, ep1, ep2, ep3, ep4 = p
    # randomly selected classification threshold values to get high recall
    # for no defect binary classifier and high precision for multi-label classifier
    # while not compromising much on other metrics

    hasDef = []
    ogImage = cv2.imread('C:\\Users\\Ashay\\front\\media\\'+j)          # output always has to go in mysite\static\images
    # area thresholds are determined from EDA performed only on train dataset
    aEp1 = area(mask2rle(np.array(
        (Image.fromarray((ep1[0, :, :, 0]) >= 0.5)).resize((1600, 256))).astype(int)))
    if aEp1 >= 500 and b >= 0.5 and m1 >= 0.3:
        c1 = Image.fromarray(ep1[0, :, :, 0])
        img = (np.array(c1.resize((1600, 256))))
        img = img[..., np.newaxis]
        blank_image = np.zeros((256, 1600, 1), np.uint8)
        for i in range(256):
            for j in range(1600):
                t = img[i][j]*255
                if(t < 0):
                    blank_image[i][j] = 0
                else:
                    blank_image[i][j] = t

        ret, thresh = cv2.threshold(blank_image, 127, 255, 0)
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        ogImage = cv2.drawContours(ogImage, contours, -1, (0, 255, 0), 3)

    aEp2 = area(mask2rle(np.array(
        (Image.fromarray((ep2[0, :, :, 0]) >= 0.5)).resize((1600, 256))).astype(int)))
    if aEp2 >= 700 and b >= 0.5 and m2 >= 0.3:
        c1 = Image.fromarray(ep2[0, :, :, 0])
        img = (np.array(c1.resize((1600, 256))))
        img = img[..., np.newaxis]
        blank_image = np.zeros((256, 1600, 1), np.uint8)
        for i in range(256):
            for j in range(1600):
                t = img[i][j]*255
                if(t < 0):
                    blank_image[i][j] = 0
                else:
                    blank_image[i][j] = t

        ret, thresh = cv2.threshold(blank_image, 127, 255, 0)
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        ogImage = cv2.drawContours(ogImage, contours, -1, (255, 0, 0), 3)

    aEp3 = area(mask2rle(np.array(
        (Image.fromarray((ep3[0, :, :, 0]) >= 0.5)).resize((1600, 256))).astype(int)))
    if aEp3 >= 1100 and b >= 0.5 and m3 >= 0.45:
        c1 = Image.fromarray(ep3[0, :, :, 0])
        img = (np.array(c1.resize((1600, 256))))
        img = img[..., np.newaxis]
        blank_image = np.zeros((256, 1600, 1), np.uint8)
        for i in range(256):
            for j in range(1600):
                t = img[i][j]*255
                if(t < 0):
                    blank_image[i][j] = 0
                else:
                    blank_image[i][j] = t

        ret, thresh = cv2.threshold(blank_image, 127, 255, 0)
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        ogImage = cv2.drawContours(ogImage, contours, -1, (0, 0, 255), 3)

    aEp4 = area(mask2rle(np.array(
        (Image.fromarray((ep4[0, :, :, 0]) >= 0.5)).resize((1600, 256))).astype(int)))
    if aEp4 >= 2800 and b >= 0.5 and m4 >= 0.3:
        c1 = Image.fromarray(ep4[0, :, :, 0])
        img = (np.array(c1.resize((1600, 256))))
        img = img[..., np.newaxis]
        blank_image = np.zeros((256, 1600, 1), np.uint8)
        for i in range(256):
            for j in range(1600):
                t = img[i][j]*255
                if(t < 0):
                    blank_image[i][j] = 0
                else:
                    blank_image[i][j] = t

        ret, thresh = cv2.threshold(blank_image, 127, 255, 0)
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        ogImage = cv2.drawContours(ogImage, contours, -1, (0, 0, 0), 3)
    
    cv2.putText(ogImage, 'Edge wave', (0, 25), cv2.FONT_HERSHEY_SIMPLEX , 0.5, (0,255,0), 1);
    cv2.putText(ogImage, 'Buckle', (0, 50), cv2.FONT_HERSHEY_SIMPLEX , 0.5, (255,0,0), 1);
    cv2.putText(ogImage, 'Bruises/Roll marks', (0, 75), cv2.FONT_HERSHEY_SIMPLEX , 0.5, (0,0,255), 1);
    cv2.putText(ogImage, 'Pinchers', (0, 100), cv2.FONT_HERSHEY_SIMPLEX , 0.5,(0,0,0), 1);
    cv2.imwrite('C:\\Users\\Ashay\\front\\mysite\\static\\images\\test.jpg', ogImage)
    


#Pratik Original code
def load_image(img_path, show=False):
	# (height, width, channels)
    img = image.load_img(img_path, target_size=(224, 224, 3))
    # (1, height, width, channels), add a dimension because the model expects this shape: (batch_size, height, width)
    img_tensor = image.img_to_array(img)
    img_tensor = np.expand_dims(img_tensor, axis=0)
    img_tensor /= 255.
    if show:
        pyplot.imshow(img_tensor[0])
        pyplot.axis('off')
        pyplot.show()
    return img_tensor


# def accuracy():
#     acc_count = 0
#     f_defect = glob.glob("C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\original\\Defect_images\\*.png")
#     print(len(f_defect))
#     f_noDefect = glob.glob("C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\original\\NODefect_images\\*.png")
#     model = load_model("C:\\Users\\Ashay\\Desktop\\SIH\\model.h5")
#     for img in f_noDefect:
#         test_image = load_image(img)
#         pred = model.predict(test_image)
#         if pred > 0.5:
#             acc_count += 1
#     for img in f_defect:
#         test_image = load_image(img)
#         pred = model.predict(test_image)
#         if pred < 0.5:
#             acc_count += 1
    
#     print("Total Testing Accuracy: ", acc_count /  len(f_noDefect))
#     print(len(f_defect) + len(f_noDefect))
# accuracy()

def home(request):
    global count
    context = {}
    files = glob.glob('C:\\Users\\Ashay\\front\\media\\*')
    for f in files:
        os.remove(f)
    if request.method == 'POST':
        uploaded_file = request.FILES['video']
        fs = FileSystemStorage()
        name = fs.save(uploaded_file.name, uploaded_file)
        context['url'] = fs.url(name)
    return render(request, 'base.html', context)


def result(request):
    print(request.POST['algorithm'])
    material = str(request.POST['algorithm'])
    files1 = glob.glob('C:\\Users\\Ashay\\front\\mysite\\static\\images\\*')
    for f in files1:
        os.remove(f)
    files = glob.glob('C:\\Users\\Ashay\\front\\media\\*')
    img_path = files[0]
    test_image = load_image(img_path)
    # im = Image.open(r""+img_path)
    # im = im.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])

    if material == "Fabric":
        model = load_model("C:\\Users\\Ashay\\Desktop\\SIH\\model.h5")
        if(img_path[-3:] != "png"):
            send_email.error_email(img_path)
            return render(request, 'wrong.html', {'message':'The entered image is of the wrong type'})

        pred = model.predict(test_image)
        
        if pred > 0.5:
            # for f in files:
            #     os.remove(f)
            im = Image.open(r""+img_path)
            im = im.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])
            return render(request, 'misclass.html', {'category': material, 'faults': 'has no', 'original': 'images\\og_'+img_path[-15:], 'message' : 'Since the fault is not present, there is no output image'})
        else:
            try:
                op_image = img_path[-15:]
                im1 = Image.open(r"C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\results\\"+img_path[-15:])
                im1 = im1.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\result_"+img_path[-15:])
                im2 = Image.open(r""+img_path)
                im2 = im2.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])
                # for f in files:
                #     os.remove(f)
                send_email.email_alert()
                return render(request, 'result.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-15:], 'op': 'images\\result_'+img_path[-15:], 'message': 'The output image shows localisation!'})
            except:
                fault_message = 'There is no output image as this is a misclassification.'
                return render(request, 'misclass.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-15:], 'message': fault_message})


        
    else:
        files = glob.glob("C:\\Users\\Ashay\\front\\media\\*")
        img_path = files[0]
        print(files)
        print('THIS IS A TEST',img_path[-3:])
        if(img_path[-3:] != "jpg"):
            send_email.error_email(img_path)
            return render(request, 'wrong.html', {'message':'The entered image is of the wrong type'})
        img = img_path[-13:]
        data = [[img]]
        X = pd.DataFrame(data, columns=['ImageId'])
        
        ret = steel_prediction(X) #ret=[true, true, false, false]
        
        '''if pred == 0:           # no defect
            # img_path = the og input path ie. media folder
            im2 = Image.open(r""+img_path)
            im2 = im2.save("C:\\project\\front\\mysite\\static\\images\\"+img_path[-13:])
            return render(request, 'misclass.html', {'category': material, 'faults': 'has no', 'original': 'images\\'+img_path[-13:], 'message': 'Since the fault is not present, there is no output image'})'''
           # im1 = Image.open(r"C:\\Users\\Ashay\\front\\mysite\\static\\images\test.jpg")  #res will always be called test.jpg only. ok wait
            #im1 = im1.save("C:\\project\\front\\mysite\\static\\images\\result_"+img_path[-13:])
        im2 = Image.open(r""+img_path)  #cool? no no. that is already there in img_path toh fir me kya karu? done? should i try? yes
        im2 = im2.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\"+img_path[-13:])
        return render(request, 'result.html', {'category': material, 'faults': 'has', 'original': 'images\\'+img_path[-13:], 'op': 'images\\test.jpg', 'message': 'The output image shows localisation!'})   # try this quotes ka issue hai is this proper? yes
        

        '''
        if pred == 0:           # no defect
            return render(request, 'misclass.html', {'category': material, 'faults': 'has no', 'original': 'images\\'+img_path[-13:], 'message': 'Since the fault is not present, there is no output image'})
        else:
            im2 = Image.open(r""+img_path)
            im2 = im2.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-13:])
            return render(request, 'result.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-13:], 'op': 'images\\'+img_path[-13:], 'message': 'The output image shows localisation!'})
        '''
        #return render(request, 'misclass.html', {'category': material, 'faults': 'has no', 'original': 'images\\'+img_path[-13:], 'message': 'Since the fault is not present, there is no output image'})




def local(request):
     print(request.POST['algorithm'])
     material = str(request.POST['algorithm'])
     var = 'steven-lu-CIyDU5WLxxw-unsplash.jpg'
     old_path = ''
     new_path = os.path.join('images', var)
     os.rename(new_path, old_path)
     return render(request, 'local.html', {'category': "images/"+var})


def randomise(request):
    material = 'Fabric'
    model = load_model("C:\\Users\\Ashay\\Desktop\\SIH\\model.h5")
    class_of_image = random.randint(0,1)
    files1 = glob.glob('C:\\Users\\Ashay\\front\\mysite\\static\\images\\*.png')
    for f in files1:
        os.remove(f)
    if class_of_image == 0:
        defect_files = glob.glob("C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\original\\Defect_images\\*.png")   
        rand_image = random.randint(0,len(defect_files)-1)
        img_path = defect_files[rand_image]
        im = Image.open(r""+img_path)
        im = im.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])
        test_image = load_image(img_path)
        #model = load_model("C:\\Users\\Ashay\\Desktop\\SIH\\model.h5") 
        pred = model.predict(test_image)
        if pred > 0.5:
            # for f in files:
            #     os.remove(f)
            return render(request, 'misclass.html', {'category': material, 'faults': 'has no', 'original': 'images\\og_'+img_path[-15:], 'message': 'Since the fault is not present, there is no output image'})
        else:
            try:
                op_image = img_path[-15:]
                im1 = Image.open(r"C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\results\\"+img_path[-15:])
                im1 = im1.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\result_"+img_path[-15:])
                im2 = Image.open(r""+img_path)
                im2 = im2.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])
                # for f in files:
                #     os.remove(f)
                send_email.email_alert()
                return render(request, 'result.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-15:], 'op': 'images\\result_'+img_path[-15:], 'message': 'The output image shows localisation!'})
            except:
                fault_message = 'There is no output image as this is a misclassification.'
                return render(request, 'misclass.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-15:], 'message': fault_message})

        
    else:
        no_defect_files = glob.glob("C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\original\\NODefect_images\\*.png")
        rand_image = random.randint(0, len(no_defect_files)-1)
        img_path = no_defect_files[rand_image]
        im = Image.open(r""+img_path)
        im = im.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])
        test_image = load_image(img_path)
        #model = load_model("C:\\Users\\Ashay\\Desktop\\SIH\\model.h5")
        pred = model.predict(test_image)
        if pred > 0.5:
            # for f in files:
            #     os.remove(f)
            return render(request, 'misclass.html', {'category': material, 'faults': 'has no', 'original': 'images\\og_'+img_path[-15:], 'message': 'Since the fault is not present, there is no output image'})
        else:
            try:
                op_image = img_path[-15:]
                im1 = Image.open(r"C:\\Users\\Ashay\\Desktop\\SIH\\dataset\\results\\"+img_path[-15:])
                im1 = im1.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\result_"+img_path[-15:])
                im2 = Image.open(r""+img_path)
                im2 = im2.save("C:\\Users\\Ashay\\front\\mysite\\static\\images\\og_"+img_path[-15:])
                # for f in files:
                #     os.remove(f)
                return render(request, 'result.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-15:], 'op': 'images\\result_'+img_path[-15:], 'message': 'The output image shows localisation!'})
            except:
                fault_message = 'There is no output image as this is a misclassification.'
                return render(request, 'misclass.html', {'category': material, 'faults': 'has', 'original': 'images\\og_'+img_path[-15:], 'message': fault_message})

        
    # return render(request, 'base.html')

