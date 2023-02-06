from PIL import Image, ImageFilter
from bs4 import BeautifulSoup
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

currentCard = 1

#}


def crop(cropPosition):
    global currentCard
    global webcamImage
    img = webcamImage
    global cardOnePos
    global cardTwoPos
    global cardWidth
    convertToGrayscale = False
    if currentCard == 1:
        cardPos = list(cardOnePos)
    elif currentCard == 2:
        cardPos = list(cardTwoPos)
    else:
        print("invalid card to crop, should be card 1 or 2")
    cropX = cardPos[0] + cardWidth
    if cropPosition == "whole":
        cropY = cardWidth * 1.4 + cardPos[1]
    elif cropPosition == "bottom":
        convertToGrayscale = True
        cardPos[1] = cardWidth * 1.3 + cardPos[1]
        cropY = cardWidth * 0.1 + cardPos[1]
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

def getCleanTextFrom(img):
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
    global currentCard
    global numTexts
    global searchableText
    #response = requests.get(f'https://api.scryfall.com/cards/named?exact={searchableText}')
    if(versionSpecific):
        if(autofindVersion):
            version = findVersion()
            if version != -1:
                response = requests.get(f'https://api.scryfall.com/cards/{version}')
            else:
                response = requests.get(f'https://api.scryfall.com/cards/named?exact={searchableText}')
        else:
            print("")
            # prompt user to pick a version here
    data = json.loads(response.text)
    wantedProperties = ["name", "set_name", "colors", "released_at", "cmc", "type_line", "legalities", "collector_number", "rarity", "reprint", "prices"]
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


def findVersion():
    # first get all needed data from all card versions
    global currentCard
    global searchableText
    response = requests.get(f'https://scryfall.com/search?as=grid&order=released&q=%21%22{searchableText}%22+include%3Aextras&unique=prints')
    htmlData = BeautifulSoup(response.content, 'html.parser')
    elements = htmlData.find_all(attrs={"data-card-id": True})
    cardIDs = []
    for element in elements:
        card_id = element["data-card-id"]
        cardIDs.append(card_id)
    versionIDs = []
    versionSets = []
    versionCollectorNums = []
    versionArtists = []
    versionYears = []
    for ID in cardIDs:
        response = requests.get(f'https://api.scryfall.com/cards/{ID}')
        data = json.loads(response.text)
        if "paper" not in data["games"] or data["oversized"]:
            continue
        else:
            versionIDs.append(ID)
            versionSets.append(data["set"])
            versionCollectorNums.append(int(re.findall(r'\d+', data["collector_number"])[0]))
            versionArtists.append(data["artist"])
            versionDate = data["released_at"]
            versionYears.append(versionDate[:-6])
    # get data from the image
    img = crop("bottom")
    text = pytesseract.image_to_string(img)

    # check for a valid collectors number in card data
    collectorNumbers = re.findall(r'\d+/\d+', text)
    if len(collectorNumbers) > 0:
        collectorNumbersSplit = re.findall(r'\d+', collectorNumbers[0])
        if len(collectorNumbers[0]) <= 7 and int(collectorNumbersSplit[1]) <= 999 and len(collectorNumbers) == 1 and len(collectorNumbersSplit) == 2:
            print(f'valid collectors number found as {collectorNumbersSplit[0]}')
            validCollectorNumber = collectorNumbersSplit[0]
        else:
            print('no valid collector number found')
            validCollectorNumber = "nope"
    else:
        print('no valid collector number found')
        validCollectorNumber = "nope"

    # check for a valid year in card data
    validYear = "nope"
    potentialYears = re.findall(r'\d+', text)
    for year in potentialYears:
        if int(year) >= 1994 and int(year) <= 2050:
            print(f'valid year found as {year}')
            validYear = year
            break
    if validYear == "nope":
        print("no valid year found")

    # check for a verified set code
    found = False
    textSplit = text.split()
    verifiedCardData = []
    for Set in versionSets:
        for word in textSplit:
            similarity = fuzz.ratio(word.upper(), Set.upper())
            if similarity >= minSureness:
                print(f'the set was verified as {Set}')
                verifiedCardData.append(Set)
                found = True
                break
        if found:
            break

    # check for a verified artist
    found = False
    artistName = ""
    for artist in versionArtists:
        names = artist.split()
        if len(names) < 2:
            continue
        firstName = names[0]
        lastName = names[1]
        for word in textSplit:
            similarityFirstName = fuzz.ratio(word.upper(), firstName.upper())
            similarityLastname = fuzz.ratio(word.upper(), lastName.upper())
            if similarityFirstName >= minSureness:
                artistName += firstName
            if similarityLastname >= minSureness and len(artistName) > 0:
                artistName += " "
                artistName += lastName
                print(f'full name verified as {artistName}')
                verifiedCardData.append(artistName)
                found = True
                break
        if found:
            break
            
    # attempt to verify a valid collectors number
    if validCollectorNumber != "nope":
        for number in versionCollectorNums:
            if int(collectorNumbersSplit[0]) == int(number):
                print(f'the valid collecters number, {validCollectorNumber} was verified')
                verifiedCardData.append(int(number))
                break

    # attempt to verify a valid year
    if validYear != "nope":
        for year in versionYears:
            if int(year) == int(validYear):
                print(f'the valid year, {validYear} was verified')
                verifiedCardData.append(year)
                break

    # match all verified card data with a specific version
    found = False
    print(verifiedCardData)
    for i in range(len(versionIDs)):
        matchingData = 0
        for data in verifiedCardData:
            if data == versionArtists[i] or data == int(versionCollectorNums[i]) or data == versionYears[i] or data == versionSets[i]:
                matchingData += 1
            if matchingData == len(verifiedCardData):
                print(f'version Matched !!! the card id is {versionIDs[i]}')
                found = True
                return versionIDs[i]
    print("no specific version could be automatically found")
    return -1

getCardData(verifyCard(getCleanTextFrom(thresholdImageBlackText(crop("top")))))