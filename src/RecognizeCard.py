from PIL import Image, ImageFilter
from fuzzywuzzy import fuzz
import pytesseract
import requests
import json
import copy
import re
import os

# hard coded variables {

# options for including different card versions
autofindVersion = True
versionSpecific = True

# minimum similarity value for a fuzzy string comparison
minSureness = 75

# position is used as the center of the curve on the top left corner
# width is used as the distance between the position and the top right corner equivalent
# units are in pixels
cardOnePos = (9, 9)
cardTwoPos = (9, 9)
cardWidth = 654

# grayscale values below this threshold will be considered black
thresholdBlack = 128
# grayscale calues above this threshold will be considered white
thresholdWhite = 220

# directory specific
numTexts = len(os.listdir('src/Text_Output_Storage'))
numImage = len(os.listdir('src/Image_Storage')) - 1
webcamImage = Image.open(f'src/Image_Storage/Unprocessed{numImage}.png')

#}

def cropCardOne(img):
    img = img.crop((cardOnePos[0], cardOnePos[1], cardWidth+cardOnePos[0], (cardWidth*1.4)+cardOnePos[1]))
    numImage += 1
    img.save(f'src/Image_Storage/Card1Raw{numImage}.png')
    return img

def cropCardOneTop(img):
    img = img.convert("L")
    img = img.crop((cardOnePos[0], cardOnePos[1]+(cardWidth * 1.3), cardWidth+cardOnePos[0], cardWidth*1.4))
    return img

def cropCardOneBottom(img):
    img = img.convert("L")
    img = img.crop((cardOnePos[0], cardOnePos[1], cardWidth+cardOnePos[0], (cardWidth/7.5)+cardOnePos[1]))
    return img

def crop(cropPosition, card, img):
    global cardOnePos
    global cardTwoPos
    global cardWidth
    convertToGrayscale = False
    if card == 1:
        cardPos = list(cardOnePos)
    elif card == 2:
        cardPos = list(cardTwoPos)
    else:
        print("invalid card to crop, should be card 1 or 2")
    cropX = cardPos[0] + cardWidth
    if cropPosition == "whole":
        cropY = cardWidth * 1.4 + cardPos[1]
    elif cropPosition == "bottom":
        convertToGrayscale = True
        cardPos[1] = cardWidth * 1.32 + cardPos[1]
        cropY = cardWidth * 0.08 + cardPos[1]
    elif cropPosition == "top":
        convertToGrayscale = True
        cardPos[0] = cardPos[0] + 0.059 * cardWidth
        cardPos[1] = cardPos[1] + 0.045 * cardWidth
        cropX = cropX - 0.15 * cardWidth
        cropY = cardWidth / 12 + cardPos[1]
    else:
        print("you did not select a valid cropping position")
        return -1
    img = img.crop((cardPos[0], cardPos[1], cropX, cropY))
    if convertToGrayscale:
        img = img.convert("L")
    img.show()
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
    cleanedText = re.sub(r"[^\w\s,']", '', lines[0])
    return cleanedText

def verifyCard(text):

    # check for entire string (fast)
    global minSureness
    global searchableText
    searchableText = text.replace(" ", "+")
    response = requests.get(f'https://data.tcgplayer.com/autocomplete?q={searchableText}')
    data = json.loads(response.text)
    for i in range(len(data["products"])):
        similarity = fuzz.ratio(text, data["products"][i]["product-name"])
        if(similarity >= minSureness and data["products"][i]["product-line-name"] == "Magic: The Gathering"):
            print("The card was verified as:")
            print(data["products"][i]["product-name"])
            return data["products"][i]["product-name"]
    print("The card could not be verified with an exact search")

    # check for each word (medium)
    textWords = text.split()
    for i in range(len(textWords)):
        response = requests.get(f'https://data.tcgplayer.com/autocomplete?q={textWords[i]}')
        data = json.loads(response.text)
        for j in range(len(data["products"])):
            similarity = fuzz.ratio(text, data["products"][j]["product-name"])
            if(similarity >= minSureness and data["products"][j]["product-line-name"] == "Magic: The Gathering"):
                print("The card was verified as:")
                print(data["products"][j]["product-name"])
                return data["products"][j]["product-name"]
    print("The card could not be verified by searching it's words")

    # check for each amount of characters before/after each word (slow)
    startingPoints = []
    startingPoints.append(0)
    for i in range(len(textWords)-1):
        startingPoints.append(len(textWords[i])+1)
    for i in range(len(startingPoints)):
        for j in range(startingPoints[i], len(searchableText)+1):
            currentSearch = searchableText[startingPoints[i]:j]
            response = requests.get(f'https://data.tcgplayer.com/autocomplete?q={currentSearch}')
            data = json.loads(response.text)
            for k in range(len(data["products"])):
                similarity = fuzz.ratio(text, data["products"][k]["product-name"])
                if(similarity >= minSureness and data["products"][k]["product-line-name"] == "Magic: The Gathering"):
                    print("The card was verified as:")
                    print(data["products"][k]["product-name"])
                    return data["products"][k]["product-name"]
    print("The card could not be verified.")
    return -1

def getCardData(cardName):
    global numTexts
    global searchableText
    response = requests.get(f'https://api.scryfall.com/cards/named?exact={searchableText}')
    data = json.loads(response.text)
    if(data["reprint"] and versionSpecific):
        if(autofindVersion):
            print("")
            # attempt to find card version here
        else:
            print("")
            # prompt user to pick a version here
    wantedProperties = ["name", "set_name", "colors", "released_at", "cmc", "type_line", "legalities", "collector_number", "rarity", "reprint"]
    gottenProperties = []
    tcgplayerFix = data["purchase_uris"]["tcgplayer"]
    gottenProperties.append(f'"purchase_uris":"{tcgplayerFix}"')
    for i in range(len(wantedProperties)):
        gottenProperties.append(f'"{wantedProperties[i]}":"{data[wantedProperties[i]]}"')
    jsonString = ','.join(gottenProperties)
    jsonData = json.dumps(jsonString)
    jsonData = jsonData.replace("\\", "")
    jsonData = jsonData.lstrip()[1:].rstrip()[:-1]
    jsonData = '{' + jsonData + '}'
    with open(f'src/Text_Output_Storage/card{numTexts}.json', "w") as json_file:
        json_file.write(jsonData)
    numTexts += 1


temp = crop("top", 1, webcamImage)

#temp = getTextFrom(thresholdImageBlackText(cropCardOne(webcamImage)))
#print(temp)

#temp2 = verifyCard(temp)
#getCardData(temp2)