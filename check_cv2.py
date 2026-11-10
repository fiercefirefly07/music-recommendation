import os
import cv2

path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

print(path)
print(os.path.exists(path))