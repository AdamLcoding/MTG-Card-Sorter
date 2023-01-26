from fuzzywuzzy import fuzz
from PIL import Image, ImageFilter
import pytesseract
import requests
import json
import os

# hard coded variables
cardOnePos = (50, 50)
cardTwoPos = (50, 50)
cardWidth = 540
minSureness = 90

# below this threshold will be considered black
thresholdBlack = 128
# above this threshold will be considered white
thresholdWhite = 220

numImage = len(os.listdir('src/Image_Storage')) - 1
webcamImage = Image.open(f'src/Image_Storage/Unprocessed{numImage}.png')

def cropCardOne(img):
    img = img.convert("L")
    img = img.crop((cardOnePos[0], cardOnePos[1], cardWidth + cardOnePos[0], (cardWidth/7.5) + cardOnePos[1]))
    return img

def cropCardTwo():
    img = img.convert("L")
    img = img.crop((cardTwoPos[0], cardTwoPos[1], cardWidth + cardTwoPos[0], (cardWidth/7.5) + cardTwoPos[1]))
    return img

def thresholdImageBlackText(img):
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixel = img.getpixel((x, y))
            if pixel > thresholdBlack:
                img.putpixel((x, y), 255)
            else:
                img.putpixel((x, y), 0)
    global numImage
    numImage += 1
    img.save(f'src/Image_Storage/BlackText{numImage}.png')
    return img
    
def thresholdImageWhiteText(img):
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixel = img.getpixel((x, y))
            if pixel < thresholdWhite:
                img.putpixel((x, y), 255)
            else:
                img.putpixel((x, y), 0)
    global numImage
    numImage += 1
    img.save(f'src/Image_Storage/WhiteText{numImage}.png')
    return img

def getTextFrom(img):
    text = pytesseract.image_to_string(img)
    lines = text.split('\n')
    return lines[0]

def verifyCard(rawText):
    global minSureness

    # check for entire string
    searchableText = rawText.replace(" ", "+")
    response = requests.get(f'https://data.tcgplayer.com/autocomplete?q={searchableText}')
    data = json.loads(response.text)
    for i in range(len(data["products"])):
        similarity = fuzz.ratio(rawText, data["products"][i]["product-name"])
        if(similarity >= minSureness):
            print("The card was verified as:")
            print(data["products"][i]["product-name"])
        


temp = getTextFrom(thresholdImageBlackText(cropCardOne(webcamImage)))
print(temp)

verifyCard(temp)

#response = requests.get(f'https://data.tcgplayer.com/autocomplete?q={temp}')
#data = json.loads(response.text)
#print(data["products"][0]["product-name"])