import pygame.camera
import os

# hard coded variables
cameraNum = 0

pygame.camera.init()
camlist = pygame.camera.list_cameras()

if camlist:
    cam = pygame.camera.Camera(camlist[cameraNum], (1920, 1080))
    cam.start()
else:
    print("could not get camera")
    quit()

webcamImage = cam.get_image()
currentImage = len(os.listdir('src/Image_Storage'))
pygame.image.save(webcamImage, f'src/Image_Storage/Unprocessed{currentImage}.png')