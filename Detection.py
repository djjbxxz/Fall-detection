import sys
import cv2
import numpy as np
from config import get_openpose_config
from enum import Enum


DEBUG = True
show_safe_text = True

try:
    sys.path.append('/openpose')
    import pyopenpose as op
    print("Openpose loaded!")
except ImportError as e:
    print('Error: OpenPose library could not be found. Did you enable `BUILD_PYTHON` in CMake and have this Python script in the right folder?')
    raise e


class FALL_STATU(Enum):
    """
        `STANDING` or `NOT_FALL` = `0` \n
        `FALL` = `1` \n
        `NOT_DETECTED` = `2`
    """
    STANDING = 0
    NOT_FALL = 0
    FALL = 1
    NOT_DETECTED = 2


def get_bounding_box(data):
    ''' 
    * Args: Sequence of points
    * Return: Bounding box of set of points
    '''
    if data.shape == (0,):  # Not enough body part
        return
    x = data[:, 0]
    y = data[:, 1]
    return np.array([[min(x), min(y)], [max(x), max(y)]])


def get_point_map(data, option, model):
    """
    Arg:(   `data` 
            `option`:`head`,`upper`,`lower` 
            `model`:`COCO`,`BODY_25`)
    Return: Pick body part `option` from `data` using `model`

    """
    if model == "COCO":
        head = [0, 14, 15, 16, 17]
        upper = range(1, 8)
        lower = range(8, 14)
    elif model == "BODY_25":
        head = [0, 15, 16, 17, 18]
        upper = range(1, 8)
        lower = [8, 9, 10, 11, 12, 13, 14, 19, 20, 21, 22, 23, 24]
    if option == "head":
        to_map = head
    elif option == "upper":
        to_map = upper
    elif option == "lower":
        to_map = lower
    return np.array([data[x] for x in to_map if data[x].all() != 0])


def draw_line_kb(img, k, b):
    intersection = []
    x_edge = [0, img.shape[1]]
    y_edge = [0, img.shape[0]]
    for x in x_edge:
        y = k * x + b
        if y < 0 or y > img.shape[0]:
            continue
        else:
            intersection.append(np.array([x, y]).astype(int))
    for y in y_edge:
        x = (y - b) / k
        if x < 0 or x > img.shape[1]:
            continue
        else:
            intersection.append(np.array([x, y]).astype(int))
    point1, point2 = intersection
    cv2.line(img, (point1[0], point1[1]),
             (point2[0], point2[1]), (255, 0, 0), 2)



def draw_line_vertical(img, x):
    cv2.line(img, (x, 0), (x, img.shape[0]), (255, 0, 0), 2)


def is_fall(img, data, model):
    if data is None or data.shape == ():  # Not detected
        return img, FALL_STATU.NOT_DETECTED,0
    data = data[:, :, 0:2].astype(int)
    for i in range(data.shape[0]):
        centrl_point = []
        # for part in ["head", "upper", "lower"]:
        #     bbox = get_bounding_box(get_point_map(data[i], part, model))
        #     if DEBUG:
        #         cv2.rectangle(img, tuple(bbox[0]), tuple(
        #             bbox[1]), color=(255, 255, 255), thickness=2)
        #     centrl_point.append(
        #         np.array([(bbox[0, 0] + bbox[1, 0]) / 2, (bbox[0, 1] + bbox[1, 1]) / 2]))
        centrl_point=[data[0][1],data[0][8]]
        if centrl_point[0].all()==0 or centrl_point[1].all()==0:
            return img, FALL_STATU.NOT_DETECTED,0
        centrl_point = np.array(centrl_point).astype(int)
        # draw dot
        if DEBUG:
            for x in centrl_point:
                cv2.circle(img, (x[0], x[1]), 1, (0, 0, 255), -1)
        x = centrl_point[:, 0]
        y = centrl_point[:, 1]
        _, index = np.unique(x, return_index=True)
        x, y = x[index], y[index]
        if len(x) >= 2:
            k, b = np.polyfit(x, y, 1)
            # print(f"k:{k}")
            gradient = 90-abs(np.arctan(k)/np.pi*180)
            fall = FALL_STATU.FALL if gradient > 45 else FALL_STATU.NOT_FALL
            if DEBUG:
                draw_line_kb(img, k, b)
            return img, fall,gradient
        else:   #totally vertically
            if DEBUG:
                draw_line_vertical(img,x[0])
            return img, FALL_STATU.STANDING,0


class Detector:

    def __init__(self) -> None:
        self._config = get_openpose_config()
        self.opWrapper = op.WrapperPython()

    def start(self):
        self.opWrapper.configure(self._config)
        self.opWrapper.start()

    def get_config(self):
        return self._config

    def config(self, key, value):
        self._config[key] = value

    def openpose(self, cv_img):
        try:
            datum = op.Datum()
            datum.cvInputData = cv_img
            self.opWrapper.emplaceAndPop([datum])
        except Exception as e:
            print(e)
            sys.exit(-1)
        else:
            return datum.poseKeypoints, datum.cvOutputData

    def postprocess(self, data, img, last_fall=None):
        img, fall,gradient = is_fall(img=img, data=data,
                            model=self._config['model_pose'])
        # use last sign if not detected
        if fall is FALL_STATU.NOT_DETECTED and last_fall is not FALL_STATU.NOT_DETECTED:
            fall = last_fall
        #show safe/fall text
        if DEBUG:
            if fall is not FALL_STATU.NOT_DETECTED:
                param = dict(
                    thickness=2, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.2)
                if fall is FALL_STATU.FALL:
                    fall_str = "Fall"
                    fall_color = (0, 0, 255)  # Red
                    _color = fall_color
                    _str = fall_str
                    cv2.putText(img, _str, org=(0, 30), color=_color, **param)
                elif fall is FALL_STATU.NOT_FALL and show_safe_text:
                    not_fall_str = "Safe"
                    not_fall_color = (0, 255, 0)  # Green
                    _color = not_fall_color
                    _str = not_fall_str
                    cv2.putText(img, _str, org=(0, 30), color=_color, **param)

        return img, fall,gradient

    def inference(self, img, fall):
        data, img = self.openpose(cv_img=img)
        img, fall,gradient = self.postprocess(data, img, fall)
        return img, fall,gradient

    def detect(self, source, show, logger):
        fall = None
        while source.read_thread.is_alive() or not source.images.empty():
            img = source.images.get(block=True, timeout=10)
            img, fall = self.inference(img, fall)
            show(img)
            # sleep(1/60)
            logger.add(fall)
        print("second exit")


if __name__ == "__main__":
    data, img = openpose()
    print(data)
    # img, fall = postprocess(data, img, model)
    cv2.imwrite("result.png", img)
