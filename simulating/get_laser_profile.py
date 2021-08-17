# from PIL import Image
# import numpy as np

# path_to_file = "C:\\Users\\willi\\OneDrive - University of Waterloo\\Single Quantum Systems\\SPAD_Alignment\\"
# im_frame = Image.open(path_to_file + 'laser_profile.png')
# np_frame = np.array(im_frame.getdata())

# print(np_frame.shape)

import cv2
import numpy as np

# Get the file paths
path = 'C:/Users/willi/OneDrive - University of Waterloo/Single Quantum Systems/SPAD_Alignment/simulating/'

cv2_img = cv2.imread(path+'laser_profile.png')

np_image = np.array(cv2_img)

np.save("laser_profile.npy", np_image)

