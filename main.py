from PIL import ImageGrab
import win32gui
import time
import pyautogui
import numpy as np
import math

### Fixing the cutoff in the PyCharm Console
import pandas as pd
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 10)
np.set_printoptions(linewidth=400)
###

gridSize = 50
cols = 21
rows = 12
pathColor = (96, 34, 23)
woodTownColor = (98, 100, 57)
banditColor = (175, 145, 86)

pyautogui.PAUSE = 0.1
CARD_TYPES = ("Arsenal", "Cemetery", "Forest", "Grove", "Oblivion", "Outpost", "River", "Thicket", "Vampire", "Village")



def find_hwnd():
    toplist, winlist = [], []
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)
    lh = [(hwnd, title) for hwnd, title in winlist if 'loop hero v1' in title.lower()]
    # just grab the hwnd for first window matching firefox
    lh = lh[0]
    return lh[0]

def SearchTile(x,y,img, color, rangex = 50, rangey = 50):
    for pixelx in range(rangex):
        for pixely in range(rangey):
            currentPixelColor = img.getpixel((x * gridSize + pixelx, y * gridSize + pixely))
            if (currentPixelColor == color):
                return True

def PrintState(mapGrid, hand):
    for r in mapGrid:
        for c in r:
            print (c,end = " ")
        print()
    print ()
    #print ("Hand::" + str(hand))

def GetHand(region):
    hand = {}
    for cardType in CARD_TYPES:
        allCards = pyautogui.locateAllOnScreen('%s.png' % cardType, grayscale=True, region=region)
        for card in allCards:
            hand[card] = cardType
    handArray = []
    for card in hand:
        handArray.append((card, hand[card]))
    return sorted(handArray, key=lambda t: t[0][0])

def click(x, y):
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown()
    time.sleep(0.001)
    pyautogui.mouseUp()

def rightclick(x,y):
    pyautogui.moveTo(x,y)
    pyautogui.mouseDown(button='right')
    time.sleep(0.001)
    pyautogui.mouseUp(button='right')

# Wrapper for clicking middle of a rectangle
def click_card(card):
    click(card[0][0] + (card[0][2] / 2), card[0][1] + (card[0][3] / 2))

def screenbitmap(hwnd, focus=False):
    if (focus):
        win32gui.SetForegroundWindow(hwnd)
    bbox = win32gui.GetWindowRect(hwnd)
    time.sleep(1)
    img = ImageGrab.grab(bbox)
    img = img.crop((8, 81, 8 + cols * gridSize, 81 + rows * gridSize + 70))
    #img.save("Capture.png")
    return img

def find_grid(data, search):
    index = np.where(data == search)
    try:
        return (index[0][0], index[1][0])
    except IndexError:
        raise IndexError

# Find next river tile
def update_riverline_initial(mapgrid):
    # Trees are placed upperleft-lowerright, so lets find the starting spot on the left
    for (x, column) in enumerate(mapgrid.T):
        for (y, value) in enumerate(column):
            count = 0
            if value == "r":
                if y > 0:
                    if mapgrid[y-1][x] == "r":
                        count = count + 1
                if y < rows-1:
                    if mapgrid[y+1][x] == "r":
                        count = count + 1
                if x > 0:
                    if mapgrid[y][x-1] == "r":
                        count = count + 1
                if x < cols-1:
                    if mapgrid[y][x+1] == "r":
                        count = count + 1
                if count <= 1:
                    mapgrid[y][x] = "R"
                    return mapgrid
    return mapgrid

def update_riverline(mapgrid):
    for (y, row) in enumerate(mapgrid):
        for (x, value) in enumerate(row):
            count = 0
            if value == "r":
                if y > 0:
                    if mapgrid[y-1][x] == "S":
                        mapgrid[y][x] = "R"
                        return mapgrid
                if y < rows-1:
                    if mapgrid[y+1][x] == "S":
                        mapgrid[y][x] = "R"
                        return mapgrid
                if x > 0:
                    if mapgrid[y][x-1] == "S":
                        mapgrid[y][x] = "R"
                        return mapgrid
                if x < cols-1:
                    if mapgrid[y][x+1] == "S":
                        mapgrid[y][x] = "R"
                        return mapgrid
    return mapgrid

def riverline_fullline(curdirection, location):
    retArray = []
    if curdirection == "U":
        while location[0] > 0:
            location = (location[0] - 1, location[1])
            retArray.append(location)
        curdirection = "D"
    else:
        while location[0] < 11:
            location = (location[0] + 1, location[1])
            retArray.append(location)
        curdirection = "U"
    return (retArray,curdirection, location)

def riverline_helper(riverArray, direction, location):
    retArray = [location]
    newLocation = location
    curDirection = direction
    while (20 >= newLocation[1] >= 0):
        if curDirection[1] == "U":
            if riverArray[newLocation[1]][1] == 12:
                break
            elif riverArray[newLocation[1]][1] > 2:
                # Go up till location = riverarray-1
                while (13 - newLocation[0]) < riverArray[newLocation[1]][1]:
                    newLocation = (newLocation[0] - 1, newLocation[1])
                    retArray.append(newLocation)

            if curDirection[0] == "L":
                newLocation = (newLocation[0], newLocation[1] - 1)
            else:
                newLocation = (newLocation[0], newLocation[1] + 1)
            retArray.append(newLocation)
        else:
            if riverArray[newLocation[1]][0] == 12:
                break
            elif riverArray[newLocation[1]][0] > 2:
                # Go down till location = riverarray-1
                while (newLocation[0]+2) < riverArray[newLocation[1]][0]:
                    newLocation= (newLocation[0] + 1,  newLocation[1])
                    retArray.append(newLocation)
            if curDirection[0] == "L":
                newLocation = (newLocation[0], newLocation[1]-1)
            else:
                newLocation = (newLocation[0], newLocation[1]+1)
            retArray.append(newLocation)

    # "Done"
    if curDirection[0] == "L":
        while newLocation[1] >= 0:
            vals = riverline_fullline(curDirection[1], newLocation)
            retArray = retArray + vals[0]
            curDirection = (curDirection[0], vals[1])
            newLocation = vals[2]
            if newLocation[1] >= 2:
                newLocation = (newLocation[0], newLocation[1]-1)
                retArray.append(newLocation)
                newLocation = (newLocation[0], newLocation[1]-1)
                retArray.append(newLocation)
            else:
                break
    else:
        while newLocation[1] <= 20:
            vals = riverline_fullline(curDirection[1], newLocation)
            retArray = retArray + vals[0]
            curDirection = (curDirection[0], vals[1])
            newLocation = vals[2]
            if newLocation[1] <= 18:
                newLocation = (newLocation[0], newLocation[1]+1)
                retArray.append(newLocation)
                newLocation = (newLocation[0], newLocation[1]+1)
                retArray.append(newLocation)
            else:
                break
    return retArray

def riverline(gridmap):
    riverArray = []
    # Enumerate over Map vertically
    for (y, row) in enumerate(gridmap.T):
        first = 0
        last = 0
        for (x, value) in enumerate(row):
            if value == '0':
                first = first + 1
            else:
                break
        for (x, value) in enumerate(reversed(row)):
            if value == '0':
                last = last + 1
            else:
                break
        riverArray.append((first, last))
    lowtop = (99,-1,0)
    lowbot = (99,-1,0)
    count = -1
    for count, pair in enumerate(riverArray):
        count = count + 1
        if pair[0] < lowtop[0]:
            lowtop = (pair[0], count, 0)
        elif lowtop[0] == pair[0]:
            lowtop = (lowtop[0], lowtop[1],lowtop[2]+1)
        if pair[1] < lowbot[0]:
            lowbot = (pair[1], count,0)
        elif lowbot[0] == pair[1]:
            lowbot = (lowbot[0], lowbot[1],lowbot[2]+1)
    if lowtop[0] == 0 and lowbot[0] == 0: # No river path
        return False

    bot = False
    riverLine = []
    if lowtop[0] == lowbot[0]:
        if lowbot[2] <= lowtop[2]:
            bot = True
    elif lowtop[0] < lowbot[0]:
        bot = True
    elif lowtop[0] > lowbot[0]:
        bot = False

    if bot:
        # Cross Bottom
        line = riverline_helper(riverArray, ("L", "U"), (11, lowbot[1]))
        if line:
            riverLine = riverLine + line
            riverLine = riverLine + (riverline_helper(riverArray, ("R", "U"), (11, lowbot[1])))
        else:
            print ("Riverline Failed (Bot)")
            return False
    else:
        # Cross Top
        line = riverline_helper(riverArray, ("L", "D"), (0, lowtop[1]))
        if line:
            riverLine = riverLine + line
            riverLine = riverLine + (riverline_helper(riverArray, ("R", "D"), (0, lowtop[1])))
        else:
            print ("Riverline Failed (Top)")
            return False
    for coord in riverLine:
        gridmap[coord[0]][coord[1]] = 'r'
    return True


def read_map(img):
    mapGrid = np.full((rows, cols), "0")
    whiteSquare = False
    for (y, row) in enumerate(mapGrid):
        for (x, value) in enumerate(row):
            if (y == 11):
                mapGrid[y][x] = '0'
                break
            success = False
            for pixelx in range(50):
                for pixely in range(50):
                    currentPixelColor = img.getpixel((x * gridSize + pixelx, y * gridSize + pixely))
                    if (currentPixelColor == pathColor):
                        #Path
                        mapGrid[y][x] = '1'
                        success = True
                        if (whiteSquare):
                            break
                    if (currentPixelColor == (255, 255, 255)):
                        #Campsite
                        mapGrid[y][x] = '9'
                        success = True
                        whiteSquare = True
                        break
                if whiteSquare and success:
                    break
            if (not success):
                mapGrid[y][x] = '0'

    for (y, row) in enumerate(mapGrid):
        for (x, value) in enumerate(row):
            if (mapGrid[y][x] == '0'):
                if (y != 0):
                    if (mapGrid[y - 1][x] == '1' or mapGrid[y - 1][x] == '9'):
                        mapGrid[y][x] = '2'
                if (y != 11):
                    if (mapGrid[y + 1][x] == '1' or mapGrid[y + 1][x] == '9'):
                        mapGrid[y][x] = '2'
                if (x != 0):
                    if (mapGrid[y][x - 1] == '1' or mapGrid[y][x - 1] == '9'):
                        mapGrid[y][x] = '2'
                if (x != 20):
                    if (mapGrid[y][x + 1] == '1' or mapGrid[y][x + 1] == '9'):
                        mapGrid[y][x] = '2'
    success = riverline(mapGrid)
    if not success:
        return ([], False)
    mapGrid = update_riverline_initial(mapGrid)
    print("Starting Map::")
    PrintState(mapGrid, [])
    return (mapGrid, True)

def playCard(card, mapgrid, target, replace, BOARD_CORNER, CURSOR_CORNER):
    try:
        x,y = find_grid(mapgrid.T, target)
    except IndexError:
        #print("Cannot place card")  # TODO: Figure out what to do here (update cardstoplay list?)
        return (mapgrid, False)
    click_card(card)
    click(BOARD_CORNER[0] + 25 + (50 * x), BOARD_CORNER[1] + 25 + (50 * y))
    mapgrid[y][x] = replace
    pyautogui.moveTo(CURSOR_CORNER)
    return (mapgrid, True)

def oblivion_card(card, mapgrid, BOARD_CORNER, CURSOR_CORNER):
    (mapgrid, success) = playCard(card, mapgrid, "B", "2", BOARD_CORNER, CURSOR_CORNER)
    if success:
        return mapgrid
    else:
        (mapgrid, success) = playCard(card, mapgrid, "W", "1", BOARD_CORNER, CURSOR_CORNER)
        return mapgrid

def findBandits(mapgrid, img):
    for (y, row) in enumerate(mapgrid):
        for (x, value) in enumerate(row):
            if value == "v":
                if y > 0:
                    if mapgrid[y-1][x] == "2":
                        if SearchTile(x,y-1,img,banditColor,40,40):
                            mapgrid[y-1][x] = "B"
                            return mapgrid
                if y < rows-1:
                    if mapgrid[y+1][x] == "2":
                        if SearchTile(x, y+1,img,banditColor,40,40):
                            mapgrid[y+1][x] = "B"
                            return mapgrid
                if x > 0:
                    if mapgrid[y][x-1] == "2":
                        if SearchTile(x-1, y,img,banditColor,40,40):
                            mapgrid[y][x-1] = "B"
                            return mapgrid
                if x < cols-1:
                    if mapgrid[y][x+1] == "2":
                        if SearchTile(x+1, y,img,banditColor,40,40):
                            mapgrid[y][x+1] = "B"
                            return mapgrid
    print ("FAILURE to find bandits")
    return mapgrid

def findWoodTown(mapgrid, img):
    for (y, row) in enumerate(mapgrid):
        for (x, value) in enumerate(row):
            if value == "1":
                if SearchTile(x, y, img, woodTownColor,40,40):
                    mapgrid[y][x] = "W"
                    return mapgrid
    print ("FAILURE to find woodtown")
    return mapgrid

def main():
    hwnd = find_hwnd()
    img = screenbitmap(hwnd, True)
    region = pyautogui.locateOnScreen("sun.png") # How make sure it's not covered by mouse?
    if region is None:
        raise Exception('Could not find game on screen. Is the game visible?')
    topLeftX = region[0]
    topLeftY = region[1]
    GAME_REGION = (topLeftX, topLeftY, 1300, 750)
    HAND_REGION = (topLeftX+12, topLeftY + 648, 1000, 5)
    PAUSE_REGION = (topLeftX + 370, topLeftY - 5, 75, 75)
    BATTLE_REGION = (topLeftX + 480, topLeftY + 90, 90, 90)
    CURSOR_CORNER = (topLeftX + 1200, topLeftY + 700)
    BOARD_CORNER = (topLeftX - 2, topLeftY + 48)
    pyautogui.moveTo(CURSOR_CORNER)

    (mapGrid, success) = read_map(img)
    if not success:
        raise Exception("No river line found") # if no line can go left-right just give up on run.
    hand = []
    thickets = 0
    villages = 0
    battled = True
    while (True):
        if (pyautogui.locateOnScreen("Paused.png", region=PAUSE_REGION)):
            #rightclick(CURSOR_CORNER[0], CURSOR_CORNER[1])
            continue
        if (pyautogui.locateOnScreen("Battle.png", region=BATTLE_REGION)):
            battled = True
        else:
            if battled:
                rightclick(CURSOR_CORNER[0], CURSOR_CORNER[1])
                cards = GetHand(HAND_REGION)  # Can this run in a separate thread? : return list of new cards to play
                # Play cards if possible
                for card in reversed(cards):
                    if card[1] == "Arsenal":
                        (mapGrid, success) = playCard(card, mapGrid, "2", "A", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Arsenal")
                    elif card[1] == "Cemetery":
                        (mapGrid, success) = playCard(card, mapGrid, "1", "C", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Cemetery")
                    elif card[1] == "Forest" or card[1] == "Thicket":
                        (mapGrid, success) = playCard(card, mapGrid, "0", "T", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Forest/Thicket")
                        else:
                            thickets = thickets + 1
                            if thickets % 10 == 0:
                                # Make sure it gets past the spawn animation
                                time.sleep(0.5)
                                mapGrid = findWoodTown(mapGrid, screenbitmap(hwnd))
                    elif card[1] == "Grove":
                        (mapGrid, success) = playCard(card, mapGrid, "1", "G", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Grove")
                    elif card[1] == "Oblivion":
                        # Delete bandits and woodtowns
                        mapGrid = oblivion_card(card, mapGrid, BOARD_CORNER, CURSOR_CORNER)
                    elif card[1] == "Outpost":
                        (mapGrid, success) = playCard(card, mapGrid, "2", "P", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Outpost")
                    elif card[1] == "River":
                        (mapGrid, success) = playCard(card, mapGrid, "R", "S", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play River")
                        else:
                            mapGrid = update_riverline(mapGrid)
                    elif card[1] == "Vampire":
                        (mapGrid, success) = playCard(card, mapGrid, "2", "V", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Vampire Mansion")
                    elif card[1] == "Village":
                        (mapGrid, success) = playCard(card, mapGrid, "1", "v", BOARD_CORNER, CURSOR_CORNER)
                        if not success:
                            print ("Failed to play Village")
                        else:
                            villages = villages + 1
                            if villages % 2 == 0:
                                # Make sure it gets past the spawn animation
                                time.sleep(0.5)
                                mapGrid = findBandits(mapGrid, screenbitmap(hwnd))
                battled = False
                rightclick(CURSOR_CORNER[0], CURSOR_CORNER[1])
                PrintState(mapGrid, [])


if __name__ == "__main__":
    main()