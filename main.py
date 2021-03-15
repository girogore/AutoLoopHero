from PIL import ImageGrab
import win32gui
import time
import pyautogui
import numpy as np
import math

gridSize = 50
cols = 21
rows = 12
targetColor = ((96, 34, 23))
pyautogui.PAUSE = 0.1
CARD_TYPES = ("Arsenal", "Cemetery", "Forest", "Grove", "Oblivion", "River", "Thicket", "Vampire", "Village")


def find_hwnd():
    toplist, winlist = [], []
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)
    lh = [(hwnd, title) for hwnd, title in winlist if 'loop hero v1' in title.lower()]
    # just grab the hwnd for first window matching firefox
    lh = lh[0]
    return lh[0]

def PrintState(mapGrid, hand):
    for r in mapGrid:
        for c in r:
            print (c,end = " ")
        print()
    print ()
    print ("Hand::" + str(hand))

def GetHand(region):
    hand = {}
    for cardType in CARD_TYPES:
        allCards = pyautogui.locateAllOnScreen('%s.png' % cardType, region=region)
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
    # img.save("Capture.png")
    return img

def find_grid(data, search):
    index = np.where(data == search)
    try:
        return (index[0][0], index[0][1])
    except IndexError:
        raise IndexError

def find_grid_old(data, search):
    for i, e in enumerate(data):
        try:
            return i, e.index(search)
        except ValueError:
            pass
    return False

# Find next river tile
def update_riverline(mapgrid):
    for (x, row) in enumerate(mapgrid):
        for (y, value) in enumerate(row):
            count = 0
            if value == "r":
                if x > 0:
                    if mapgrid[x-1][y] == "r":
                        count = count + 1
                if x < cols:
                    if mapgrid[x+1][y] == "r":
                        count = count + 1
                if y > 0:
                    if mapgrid[x][y-1] == "r":
                        count = count + 1
                if y > rows:
                    if mapgrid[x][y+1] == "r":
                        count = count + 1
            if count <= 1:
                mapgrid[x][y] = "R"
                return


def riverline_helper(riverArray, direction, location):
    retArray = [location]
    newLocation = location
    curDirection = direction
    while (20 >= newLocation[1] >= 0):
        if curDirection[1] == "U":
            if riverArray[newLocation[1]][1] > 2:
                # Go up till location = riverarray-1
                while (13 - newLocation[0]) < riverArray[newLocation[1]][1]:
                    newLocation = (newLocation[0] - 1, newLocation[1])
                    retArray.append(newLocation)
            elif riverArray[newLocation[1]][1] == 12:
                break
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
            if curDirection[1] == "U":
                while newLocation[0] > 0:
                    newLocation = (newLocation[0]-1, newLocation[1])
                    retArray.append(newLocation)
                curDirection = (curDirection[0], "D")
            else:
                while newLocation[0] < 11:
                    newLocation = (newLocation[0]+1, newLocation[1])
                    retArray.append(newLocation)
                curDirection = (curDirection[0], "U")
            if newLocation[1] >= 2:
                newLocation = (newLocation[0], newLocation[1]-1)
                retArray.append(newLocation)
                newLocation = (newLocation[0], newLocation[1]-1)
                retArray.append(newLocation)
            else:
                break

    else:
        while newLocation[1] <= 20:
            if curDirection[1] == "U":
                while newLocation[0] > 0:
                    newLocation = (newLocation[0]-1, newLocation[1])
                    retArray.append(newLocation)
                curDirection = (curDirection[0], "D")
            else:
                while newLocation[0] < 11:
                    newLocation = (newLocation[0]+1, newLocation[1])
                    retArray.append(newLocation)
                curDirection = (curDirection[0], "U")
            if newLocation[1] <= 18:
                newLocation = (newLocation[0], newLocation[1]+1)
                retArray.append(newLocation)
                newLocation = (newLocation[0], newLocation[1]+1)
                retArray.append(newLocation)
            else:
                break
    return retArray

def riverline(gridMap):
    riverArray = []
    # Enumerate over Map vertically
    for (x, row) in enumerate(gridMap.T):
        first = 0
        last = 0
        for (y, value) in enumerate(row):
            if value == '0':
                first = first + 1
            else:
                break
        for (y, value) in enumerate(reversed(row)):
            if value == '0':
                last = last + 1
            else:
                break
        riverArray.append((first, last))

    lowtop = (99,-1)
    lowbot = (99,-1)
    count = -1
    for pair in riverArray:
        count = count + 1
        if pair[0] < lowtop[0]:
            lowtop = (pair[0], count)
        if pair[1] < lowbot[0]:
            lowbot = (pair[1], count)

    bot = False
    riverLine = []
    if lowtop[0] == 0 and lowbot[0] == 0:
        return False
    if lowtop[0] == lowbot[0]:
        if lowbot[1] > lowtop[1]:
            bot = True

    if lowtop[0] < lowbot[0 or bot]:
        # Cross Bottom
        line = riverline_helper(riverArray, ("L", "U"), (11, lowbot[1]))
        if line:
            riverLine = riverLine + line
            riverLine = riverLine + (riverline_helper(riverArray, ("R", "U"), (11, lowbot[1])))
        else:
            return False
    elif lowtop[0] > lowbot[0]:
        # Cross Top
        line = riverline_helper(riverArray, ("L", "D"), (0, lowtop[1]))
        if line:
            riverLine = riverLine + line
            riverLine = riverLine + (riverline_helper(riverArray, ("R", "D"), (0, lowtop[1])))
        else:
            return False
    for coord in riverLine:
        gridMap[coord[0]][coord[1]] = 'r'
    return True


def read_map(img):
    mapGrid = np.full((rows, cols), "0")
    whiteSquare = False
    for (x, row) in enumerate(mapGrid):
        for (y, value) in enumerate(row):
            if (x == 11):
                mapGrid[x][y] = '0'
                break
            success = False
            for pixelx in range(50):
                for pixely in range(50):
                    currentPixelColor = img.getpixel((y * gridSize + pixely, x * gridSize + pixelx))
                    if (currentPixelColor == targetColor):
                        mapGrid[x][y] = '1'
                        success = True
                        if (whiteSquare):
                            break
                    if (currentPixelColor == (255, 255, 255)):
                        mapGrid[x][y] = '9'
                        success = True
                        whiteSquare = True
                        break
                if whiteSquare and success:
                    break
            if (not success):
                mapGrid[x][y] = '0'

    for (x, row) in enumerate(mapGrid):
        for (y, value) in enumerate(row):
            if (mapGrid[x][y] == '0'):
                if (x != 0):
                    if (mapGrid[x - 1][y] == '1' or mapGrid[x - 1][y] == '9'):
                        mapGrid[x][y] = '2'
                if (x != 11):
                    if (mapGrid[x + 1][y] == '1' or mapGrid[x + 1][y] == '9'):
                        mapGrid[x][y] = '2'
                if (y != 0):
                    if (mapGrid[x][y - 1] == '1' or mapGrid[x][y - 1] == '9'):
                        mapGrid[x][y] = '2'
                if (y != 20):
                    if (mapGrid[x][y + 1] == '1' or mapGrid[x][y + 1] == '9'):
                        mapGrid[x][y] = '2'
    success = riverline(mapGrid)
    if not success:
        return ([], False)
    print("Starting Map::")
    PrintState(mapGrid, [])
    return (mapGrid, True)

def main():
    hwnd = find_hwnd()
    img = screenbitmap(hwnd, True)
    region = pyautogui.locateOnScreen("sun.png") # How make sure it's not covered by mouse?
    if region is None:
        raise Exception('Could not find game on screen. Is the game visible?')
    topLeftX = region[0]
    topLeftY = region[1]
    GAME_REGION = (topLeftX, topLeftY, 1300, 750)
    HAND_REGION = (topLeftX, topLeftY + 450, 1300, 300)
    PAUSE_REGION = (topLeftX + 370, topLeftY - 5, 75, 75)
    BATTLE_REGION = (topLeftX + 480, topLeftY + 90, 90, 90)
    CURSOR_CORNER = (topLeftX + 1200, topLeftY + 700)
    BOARD_CORNER = (topLeftX - 2, topLeftY + 48)
    pyautogui.moveTo(CURSOR_CORNER)

    (mapGrid, success) = read_map(img)
    if not success:
        raise Exception("No river line found") # if no line can go left-right just give up on run.
    update_riverline(mapGrid)
    hand = []
    thickets = 0
    villages = 0
    while (True):
        cards = GetHand(HAND_REGION) # Can this run in a separate thread? : return list of new cards to play

        if (pyautogui.locateOnScreen("Paused.png", region=PAUSE_REGION)):
            #rightclick(CURSOR_CORNER[0], CURSOR_CORNER[1])
            pass

        if (pyautogui.locateOnScreen("Battle.png", region=BATTLE_REGION)):
            pass
        else:
            #if (len(cardsToPlay != 0)):
            #    rightclick(CURSOR_CORNER[0], CURSOR_CORNER[1])
            # Play cards if possible
            for card in reversed(cards):
                if card[1] == "Forest" or card[1] == "Thicket":
                    try:
                        x,y = find_grid(mapGrid, "0")
                    except IndexError:
                        print ("Cannot place card") # TODO: Figure out what to do here (update cardstoplay list?)
                        continue
                    click_card(card)
                    click (BOARD_CORNER[0]+25+(50*x), BOARD_CORNER[1]+25+(50*y))
                    mapGrid[x][y] = 'T'
                    thickets = thickets + 1
                    pyautogui.moveTo(CURSOR_CORNER)

                if card[1] == "River":
                    x,y = find_grid(mapGrid, "R")
                    if x == False:
                        print ("Cannot place card") # TODO: Figure out what to do here (update cardstoplay list?)
                        continue
                    click_card(card)
                    click (BOARD_CORNER[0]+25+(50*x), BOARD_CORNER[1]+25+(50*y))
                    mapGrid[x][y] = 'S'
                    update_riverline(mapGrid)
                    pyautogui.moveTo(CURSOR_CORNER)


if __name__ == "__main__":
    main()