import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

plt.rcParams['image.cmap'] = 'gray'
plt.ion()


class ScaleDisplay(object):
    """Class for selecting a scale. Last two clicks are stored in scale_markers.

        Attributes:
            fig:
            ax:
            img:
            axim:
            scale_markers:
    """

    def __init__(self, fig, ax, img):
        self.fig = fig
        self.ax = ax

        self.img = img

        self.axim = ax.imshow(self.img, cmap='gray')
        # create connections
        self.fig.canvas.mpl_connect('button_press_event', self.onclick)

        # recording of clicks
        self.scale_markers = []

    def onclick(self, event):
        """Prints and saves the click location.
        """
        x = event.xdata
        y = event.ydata
        print('{}, {}'.format(int(np.round(x)), int(np.round(y))))
        if len(self.scale_markers) < 2:
            self.scale_markers.append(x)
        else:
            print('Cleared last selection.')
            self.scale_markers = [x]


def select_scale(img, scale_boundaries=(0.6, 0.93)):
    """
	Creates axes and plots the image for selecting the scale.
	
	Args:
	scale_boundaries=tuple(fx, fy) 
	Defines image region where scale bar is visible, 
	with (fx, fy) defining the upper left corner of the 
	scale bar region as fraction of the SEM image size.
	"""
    fig, ax = plt.subplots(1, 1, figsize=[10, 4])
    img1 = img[int(img.shape[0] * scale_boundaries[1]):, int(img.shape[1] * scale_boundaries[0]):]
    tracker = ScaleDisplay(fig, ax, img1)
    return tracker
