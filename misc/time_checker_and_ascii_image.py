# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 14:05:03 2022.

@author: nyenah
"""
import time
from termcolor import colored
import PIL.Image

# =============================================================================
# WaterGAP Ascii Image
# =============================================================================
img_flag = True
path = './misc/watergap_logo.png'  # path to the image field

try:
    img = PIL.Image.open(path)
    img_flag = True
except FileNotFoundError:
    print(path, "Unable to find image ")


width, height = img.size
aspect_ratio = height/width
new_width = 120
new_height = aspect_ratio * new_width * 0.55
img = img.resize((new_width, int(new_height)))


img = img.convert('L')

chars = [" ", "*", "*", "%", "*", "P", "+", "*", "$", ",", "."]

pixels = img.getdata()
new_pixels = [chars[pixel//25] for pixel in pixels]
new_pixels = ''.join(new_pixels)
new_pixels_count = len(new_pixels)
ascii_image = [new_pixels[index:index + new_width]
               for index in range(0, new_pixels_count, new_width)]
ascii_image = "\n".join(ascii_image)


print("\n"*3 + ascii_image)


# =============================================================================
# Timer decorator
# =============================================================================
def check_time(func):
    """
    Check simulation time.

    Parameters
    ----------
    func : function
        input function to timer

    Returns
    -------
    inner : str
        return process time

    """
    def inner(*args, **kwargs):
        """
        Compute run time.

        Parameters
        ----------
        *args : arguments
           wrapper arguments
        **kwargs : key word arguments
           wrapper key word arguments

        Returns
        -------
        None.

        """
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        output_msg = \
            'WaterGAP run completed at %.2f minute(s)' % ((end-start)/60)
        print('\n' + colored(output_msg, 'green'))
    return inner
