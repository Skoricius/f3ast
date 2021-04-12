import numpy as np
from skimage import io
from skimage.color import rgb2gray
from skimage.filters import gaussian, threshold_minimum
from skimage.measure import label
from skimage.color import label2rgb


def read_image(file_path):
    return rgb2gray(io.imread(file_path))


def remove_bottom_bar(img, bottom_factor=0.07):
    return img[:int((1 - bottom_factor) * img.shape[0]), :]


def threshold_image(img, thresh=None, sigma=2):
    """Smooth and then threshold the image. If thresh is None, try to find the threshold using the Minimum method from skimage"""
    img_smooth = gaussian(img, sigma)
    if thresh is None:
        thresh = threshold_minimum(img_smooth)
    img_thresh = img_smooth > thresh
    return img_thresh


def get_labelled_image(img_thresh):
    """Takes the thresholded image and labels the closed areas"""
    # label image regions
    label_image = label(img_thresh)
    # get the representation of the labellng in overlay image
    image_label_overlay = label2rgb(label_image, image=img_thresh, bg_label=0)
    return label_image, image_label_overlay


def filter_small_labels(label_image, min_struct_size=300):
    labels = np.unique(label_image.flatten())
    labels = labels[labels != 0]

    # get rid of small labels
    min_struct_size = 300
    to_remove = []
    for l in labels:
        label_size = np.nonzero(label_image.flatten() == l)[0].size
        if label_size < min_struct_size:
            to_remove.append(l)
            label_image[label_image == l] = 0
    labels = [lbl for lbl in labels if lbl not in to_remove]
    return labels


def get_lengths_px(label_image, min_struct_size=300):
    labels = filter_small_labels(label_image, min_struct_size=min_struct_size)
    lengths_px = np.zeros(len(labels))
    for i, lbl in enumerate(labels):
        y_nonzero = np.nonzero(label_image == lbl)[0]
        y_range = np.max(y_nonzero) - np.min(y_nonzero)
        lengths_px[i] = y_range
    return lengths_px
