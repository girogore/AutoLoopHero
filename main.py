import threading
from enum import Enum

from PIL import ImageGrab, Image
import win32gui
import time
import pyautogui
import numpy as np

### Fixing the cutoff in the PyCharm Console
import pandas as pd
pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 10)
np.set_printoptions(linewidth=400)
###

gridSize = 50
offset_distance = -70
cols = 21
rows = 12
hwnd = 0
thickets = 0
villages = 0
pathColor = (96, 34, 23)
woodTownColor = (98, 100, 57)
banditColor = (175, 145, 86)
inventory_slots = {}
hand = {}

pyautogui.PAUSE = 0.1
CARD_TYPES = ("Arsenal", "Cemetery", "Forest", "Grove", "Oblivion", "Outpost", "River", "Thicket", "Vampire", "Village")
AMULET_TYPES = 10
ARMOR_TYPES = 10
BOOT_TYPES = 10
WEAPON_TYPES = 10
class ITEM_TYPES(Enum):
    Amulet = 1
    Armor = 2
    Boot = 3
    Weapon = 4

class regions():
    INVENTORY_TOPLEFTX = 1076
    INVENTORY_TOPLEFTY = 289
    MAP_REGION = (8, 81, 8 + cols * gridSize, 81 + rows * gridSize + 70)
    INVENTORY_REGION = (INVENTORY_TOPLEFTX, INVENTORY_TOPLEFTY, INVENTORY_TOPLEFTX+200, INVENTORY_TOPLEFTY+148)

    HAND_REGION = (12, 651,1000,2)
    PAUSE_REGION = (387,0,50,50)
    BATTLE_REGION = (498,112,55,55)
    BOARD_CORNER = (0, 50)
    INVENTORYSLOT_REGION = (1068, 279,50,5)
    LEVELUP_REGION = (964, 16, 4, 1)
    TEXTBOX_REGION = (703, 492, 1, 34)


    STAY_RETREAT_CORNER = (302, 250,0,0)
    MIDDLE_RETREAT = (212, 133, 1, 34)
    LEFT_RETREAT = (103, 136, 1, 82)
    STAY_REGION = (316, 136, 1, 52)
    RESURRECT_REGION = (626, 388, 1, 34)

    CURSOR_CORNER = (1158, 658)
    CURSOR_LEVELUP = (953, 25)
    CURSOR_TRAIT = (213, 155)
    CURSOR_RETREAT = (1023, 683)
    CURSOR_EXPEDITION = (1159, 62)
    CURSOR_START = (522, 673)
    CURSOR_REWARD = (484, 382)
    CURSOR_LEFT_RETREAT = ()
    CURSOR_MIDDLE_RETREAT = (224, 155)
    CURSOR_RESURRECT = (331, 155)

def find_hwnd():
    toplist, winlist = [], []
    def enum_cb(_hwnd, results):
        winlist.append((_hwnd, win32gui.GetWindowText(_hwnd)))
    win32gui.EnumWindows(enum_cb, toplist)
    lh = [(_hwnd, title) for _hwnd, title in winlist if 'loop hero v1' in title.lower()]
    # just grab the hwnd for first window matching loop hero
    lh = lh[0]
    return lh[0]

def search_tile(x, y, img, color, rangex = 50, rangey = 50):
    #'Pixels' are 2x2 pixels wide
    for pixelx in range(0,rangex,2):
        for pixely in range(0,rangey,2):
            currentPixelColor = img.getpixel((x * gridSize + pixelx, y * gridSize + pixely))
            if (currentPixelColor == color):
                return True

def search_inventory_tile(x, y, img):
    for pixelx in range(4,44,2):
        currentPixelColor = img.getpixel((x*gridSize+pixelx, y*gridSize+25))
        if (currentPixelColor != (0,0,0)):
            return True
    return False


def print_state(mapGrid):
    for r in mapGrid.T:
        for c in r:
            print (c,end = " ")
        print()
    print ()

def find_card(cardtype, region):
    global hand
    allCards = pyautogui.locateAllOnScreen('Tiles\%s.png' % cardtype, grayscale=True, region=region)
    for card in allCards:
        hand[card] = cardtype

def get_hand(region):
    global hand
    hand = {}
    for cardType in CARD_TYPES:
        t = threading.Thread(target=find_card, args=(cardType, region))
        t.start()

    main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()
    handArray = []
    for card in hand:
        handArray.append((card, hand[card]))
    return sorted(handArray, key=lambda l: l[0][0])

def click(region):
    pyautogui.moveTo(region[0], region[1])
    pyautogui.mouseDown()
    time.sleep(0.001)
    pyautogui.mouseUp()

def rightclick(region):
    pyautogui.moveTo(region[0],region[1])
    pyautogui.mouseDown(button='right')
    time.sleep(0.001)
    pyautogui.mouseUp(button='right')

# Wrapper for clicking middle of a rectangle
def click_card(card):
    click((card[0] + (card[2] / 2), card[1] + (card[3] / 2)))

def screenbitmap(region, focus=False):
    if (focus):
        win32gui.SetForegroundWindow(hwnd)
    bbox = win32gui.GetWindowRect(hwnd)
    time.sleep(1)
    img = ImageGrab.grab(bbox)
    img = img.crop(region)
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
    for (x, row) in enumerate(mapgrid):
        for (y, value) in enumerate(row):
            count = 0
            if value == "r":
                if y > 0:
                    if mapgrid[x][y-1] == "r":
                        count = count + 1
                if y < rows-1:
                    if mapgrid[x][y+1] == "r":
                        count = count + 1
                if x > 0:
                    if mapgrid[x-1][y] == "r":
                        count = count + 1
                if x < cols-1:
                    if mapgrid[x+1][y] == "r":
                        count = count + 1
                if count <= 1:
                    mapgrid[x][y] = "R"
                    return mapgrid
    return mapgrid

def update_riverline(mapgrid):
    for (x, row) in enumerate(mapgrid):
        for (y, value) in enumerate(row):
            if value == "r":
                if y > 0:
                    if mapgrid[x][y-1] == "S":
                        mapgrid[x][y] = "R"
                        return mapgrid
                if y < rows-1:
                    if mapgrid[x][y+1] == "S":
                        mapgrid[x][y] = "R"
                        return mapgrid
                if x > 0:
                    if mapgrid[x-1][y] == "S":
                        mapgrid[x][y] = "R"
                        return mapgrid
                if x < cols-1:
                    if mapgrid[x+1][y] == "S":
                        mapgrid[x][y] = "R"
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
    for (x, column) in enumerate(gridmap):
        first = 0
        last = 0
        for (y, value) in enumerate(column):
            if value == '0':
                first = first + 1
            else:
                break
        for (y, value) in enumerate(reversed(column)):
            if value == '0':
                last = last + 1
            else:
                break
        riverArray.append((first, last))
    lowtop = (99,-1,0)
    lowbot = (99,-1,0)
    for count, pair in enumerate(riverArray):
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
        gridmap[coord[1], coord[0]] = 'r'
    return True


def read_map(img):
    mapGrid = np.full((cols, rows), "0")
    whiteSquare = False
    for (x, column) in enumerate(mapGrid):
        for (y, value) in enumerate(column):
            if (y == 11):
                mapGrid[x][y] = '0'
                break
            success = False
            for pixelx in range(50):
                for pixely in range(50):
                    currentPixelColor = img.getpixel((x * gridSize + pixelx, y * gridSize + pixely))
                    if (currentPixelColor == pathColor):
                        #Path
                        mapGrid[x][y] = '1'
                        success = True
                        if (whiteSquare):
                            break
                    if (currentPixelColor == (255, 255, 255)):
                        #Campsite
                        mapGrid[x][y] = '9'
                        success = True
                        whiteSquare = True
                        break
                if whiteSquare and success:
                    break
            if (not success):
                mapGrid[x][y] = '0'

    for (x, column) in enumerate(mapGrid):
        for (y, value) in enumerate(column):
            if (mapGrid[x][y] == '0'):
                if (y != 0):
                    if (mapGrid[x][y - 1] == '1' or mapGrid[x][y - 1] == '9'):
                        mapGrid[x][y] = '2'
                if (y < rows-1):
                    if (mapGrid[x][y + 1] == '1' or mapGrid[x][y + 1] == '9'):
                        mapGrid[x][y] = '2'
                if (x != 0):
                    if (mapGrid[x - 1][y] == '1' or mapGrid[x - 1][y] == '9'):
                        mapGrid[x][y] = '2'
                if (x < cols-1):
                    if (mapGrid[x + 1][y] == '1' or mapGrid[x + 1][y] == '9'):
                        mapGrid[x][y] = '2'
    success = riverline(mapGrid)
    if not success:
        return ([], False)
    mapGrid = update_riverline_initial(mapGrid)
    print("Starting Map::")
    print_state(mapGrid)
    return (mapGrid, True)

def play_card(card, mapgrid, target, replace, offset):
    try:
        x,y = find_grid(mapgrid, target)
    except IndexError:
        #print("Cannot place card")  # TODO: Figure out what to do here (update cardstoplay list?)
        return (mapgrid, False)
    click_card(tuple(map(lambda  i, j: i+j, card[0], offset)))
    click((regions.BOARD_CORNER[0] + 25 + (50 * x), regions.BOARD_CORNER[1] + 25 + (50 * y)))
    mapgrid[x][y] = replace
    pyautogui.moveTo(regions.CURSOR_CORNER)
    return (mapgrid, True)

def find_bandits(mapgrid, img):
    for (x, column) in enumerate(mapgrid):
        for (y, value) in enumerate(column):
            if value == "v":
                if y > 0:
                    if mapgrid[x][y-1] == "2":
                        if search_tile(x, y - 1, img, banditColor, 40, 40):
                            mapgrid[x][y-1] = "B"
                            return mapgrid
                if y < rows-1:
                    if mapgrid[x][y+1] == "2":
                        if search_tile(x, y + 1, img, banditColor, 40, 40):
                            mapgrid[x][y+1] = "B"
                            return mapgrid
                if x > 0:
                    if mapgrid[x-1][y] == "2":
                        if search_tile(x - 1, y, img, banditColor, 40, 40):
                            mapgrid[x-1][y] = "B"
                            return mapgrid
                if x < cols-1:
                    if mapgrid[x+1][y] == "2":
                        if search_tile(x + 1, y, img, banditColor, 40, 40):
                            mapgrid[x+1][y] = "B"
                            return mapgrid
    print ("FAILURE to find bandits")
    return mapgrid

def find_woodtown(mapgrid, img):
    for (x, column) in enumerate(mapgrid):
        for (y, value) in enumerate(column):
            if value == "1":
                if search_tile(x, y, img, woodTownColor, 40, 40):
                    mapgrid[x][y] = "W"
                    return mapgrid
    print ("FAILURE to find woodtown")
    return mapgrid

def locate_in_region(target, screen_region):
    sx, sy = screen_region.size
    ix, iy = target.size
    for xstart in range(sx - ix+1):
        for ystart in range(sy - iy+1):
            # search for the pixel on the screen that equals the pixel at img[0:0]
            if target.getpixel((0, 0)) == screen_region.getpixel((xstart, ystart)):
                match = 1  # temporary
                for x in range(ix):  # check if first row of img is on this coords
                    if target.getpixel((x, 0))[3] == 0:
                        continue
                    elif target.getpixel((x, 0)) != screen_region.getpixel((xstart + x, ystart)):
                        match = 0  # if there's any difference, exit the loop
                        break
                if match == 1:  # otherwise, if this coords matches the first row of img
                    for x in range(ix):
                        for y in range(iy):
                            if target.getpixel((x, y))[3] == 0:
                                continue
                            # check every pixel of the img
                            elif target.getpixel((x, y)) != screen_region.getpixel((xstart + x, ystart + y)):
                                match = 0  # any difference - break
                                break
                    if match == 1: return (xstart, ystart)  # return top-left corner coordinates
    return None  # or this, if not found

def get_item_type(x,y):
    global inventory_slots
    slot_region = tuple(map(lambda  i, j: i+j, regions.INVENTORY_REGION, (x*50, y*50, 0, 0)))
    item_screen_region = (slot_region[0], slot_region[1]+21,slot_region[0]+46,slot_region[1]+21+2)
    number_square_region = (regions.INVENTORYSLOT_REGION[0]+(50*x),regions.INVENTORYSLOT_REGION[1]+(50*y)+18, 18, 1)
    item_image = screenbitmap(item_screen_region).convert('RGBA')
    #item_image.save("Capture%s.png" % x)
    item_level = 0
    found_numbers = []
    for number in range(0,10):
        fn = pyautogui.locateAllOnScreen('Numbers\%s.png' % number, grayscale=True, region=number_square_region)
        for num in fn:
            found_numbers.append((num,number))
    found_numbers = sorted(found_numbers, key=lambda numb: numb[0].left)
    for (count, digit) in enumerate(found_numbers):
        item_level += pow(10,len(found_numbers)-(count+1))*digit[1]
    #Amulet
    for count in range(1,AMULET_TYPES+1):
        inv = locate_in_region(Image.open('Amulets\Amulet_%s.png' % count), item_image)
        if inv is not None:
            inventory_slots[(x,y)] = (ITEM_TYPES.Amulet, item_level)
            return (ITEM_TYPES.Amulet, item_level)
    for count in range(1, ARMOR_TYPES+1):
        inv = locate_in_region(Image.open('Armor\Armor_%s.png' % count), item_image)
        if inv is not None:
            inventory_slots[(x, y)] = (ITEM_TYPES.Armor, item_level)
            return (ITEM_TYPES.Armor, item_level)
    for count in range(1, BOOT_TYPES+1):
        inv = locate_in_region(Image.open('Boots\Boot_%s.png' % count), item_image)
        if inv is not None:
            inventory_slots[(x, y)] = (ITEM_TYPES.Boot, item_level)
            return (ITEM_TYPES.Boot, item_level)
    for count in range(1, WEAPON_TYPES+1):
        inv = locate_in_region(Image.open('Weapons\Weapon_%s.png' % count), item_image)
        if inv is not None:
            inventory_slots[(x, y)] = (ITEM_TYPES.Weapon, item_level)
            return (ITEM_TYPES.Weapon, item_level)
    inventory_slots[(x, y)] = None
    return None

def equip_items(itemslots, equipment_slots):
    for slot in itemslots:
        t = threading.Thread(target=get_item_type, args=(slot[0], slot[1]))
        t.start()
    main_thread = threading.currentThread()

    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()
    for slot in itemslots:
        slot_center = (regions.INVENTORYSLOT_REGION[0] + 50*slot[0]+25, regions.INVENTORYSLOT_REGION[1] + 50*slot[1]+25)
        if not (inventory_slots[slot]):
            continue
        itemtype = inventory_slots[slot][0]
        if itemtype:
            itemlevel = inventory_slots[slot][1]
            if itemtype == ITEM_TYPES.Weapon:
                if equipment_slots[0][1] < equipment_slots[1][1]:
                    if (itemlevel > equipment_slots[0][1]):
                        click(slot_center)
                        click(equipment_slots[0][2])
                        equipment_slots[0][1] = itemlevel
                else:
                    if (itemlevel > equipment_slots[1][1]):
                        click(slot_center)
                        click(equipment_slots[1][2])
                        equipment_slots[1][1] = itemlevel
            elif itemtype == ITEM_TYPES.Armor:
                if (itemlevel > equipment_slots[2][1]):
                    click(slot_center)
                    click(equipment_slots[2][2])
                    equipment_slots[2][1] = itemlevel
            elif itemtype == ITEM_TYPES.Boot:
                if (itemlevel > equipment_slots[3][1]):
                    click(slot_center)
                    click(equipment_slots[3][2])
                    equipment_slots[3][1] = itemlevel
            elif itemtype == ITEM_TYPES.Amulet:
                if (itemlevel > equipment_slots[4][1]):
                    click(slot_center)
                    click(equipment_slots[4][2])
                    equipment_slots[4][1] = itemlevel

def play_hand(mapgrid):
    cur_offset = (0, 0, 0, 0)
    added_offset = (offset_distance,0,0,0)
    cards = get_hand(regions.HAND_REGION)  # Can this run in a separate thread? : return list of new cards to play
    # Play cards if possible
    for card in reversed(cards):
        if card[1] == "Arsenal":
            (mapgrid, success) = play_card(card, mapgrid, "2", "A", cur_offset)
            if not success:
                print("Failed to play Arsenal")
            else:
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Cemetery":
            (mapgrid, success) = play_card(card, mapgrid, "1", "C", cur_offset)
            if not success:
                print("Failed to play Cemetery")
            else:
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Forest" or card[1] == "Thicket":
            (mapgrid, success) = play_card(card, mapgrid, "0", "T", cur_offset)
            if not success:
                print("Failed to play Forest/Thicket")
            else:
                global thickets
                thickets += 1
                if thickets % 10 == 0:
                    # Make sure it gets past the spawn animation
                    time.sleep(0.5)
                    mapgrid = find_woodtown(mapgrid, screenbitmap(regions.MAP_REGION))
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Grove":
            (mapgrid, success) = play_card(card, mapgrid, "1", "G", cur_offset)
            if not success:
                print("Failed to play Grove")
            else:
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Oblivion":
            # Delete bandits and woodtowns
            (mapgrid, success) = play_card(card, mapgrid, "B", "2", cur_offset)
            if success:
                continue
            else:
                (mapgrid, success) = play_card(card, mapgrid, "W", "1", cur_offset)
            if (success):
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Outpost":
            (mapgrid, success) = play_card(card, mapgrid, "2", "P", cur_offset)
            if not success:
                print("Failed to play Outpost")
            else:
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "River":
            (mapgrid, success) = play_card(card, mapgrid, "R", "S", cur_offset)
            if not success:
                print("Failed to play River")
            else:
                mapgrid = update_riverline(mapgrid)
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Vampire":
            (mapgrid, success) = play_card(card, mapgrid, "2", "V", cur_offset)
            if not success:
                print("Failed to play Vampire Mansion")
            else:
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
        elif card[1] == "Village":
            (mapgrid, success) = play_card(card, mapgrid, "1", "v", cur_offset)
            if not success:
                print("Failed to play Village")
            else:
                global villages
                villages += 1
                if villages % 2 == 0:
                    # Make sure it gets past the spawn animation
                    time.sleep(0.5)
                    mapgrid = find_bandits(mapgrid, screenbitmap(regions.MAP_REGION))
                if len(cards) >= 11:
                    cur_offset = tuple(map(lambda  i, j: i+j, cur_offset, added_offset))
    return mapgrid

def start_game():
    click(regions.CURSOR_EXPEDITION)
    click(regions.CURSOR_START)
    time.sleep(1.5)
    rightclick(regions.CURSOR_CORNER)
    time.sleep(2)

def main():
    global hwnd
    hwnd = find_hwnd()
    #Box(left=1114, top=88, width=24, height=18)
    #Box(left=7, top=34, width=18, height=18)
    screenbitmap(regions.MAP_REGION, True)
    expedition = pyautogui.locateOnScreen("Misc\Ex.png") # How make sure it's not covered by mouse?
    if expedition is None:
        raise Exception('Could not find game on screen. Is the game visible?')
    game_region = (expedition[0] - 1109, expedition[1] - 56,0,0)

    regions.HAND_REGION = tuple(map(lambda  i, j: i+j, game_region, regions.HAND_REGION))
    regions.PAUSE_REGION = tuple(map(lambda  i, j: i+j, game_region, regions.PAUSE_REGION))
    regions.BATTLE_REGION = tuple(map(lambda  i, j: i+j, game_region, regions.BATTLE_REGION))
    regions.INVENTORYSLOT_REGION = tuple(map(lambda  i, j: i+j, game_region, regions.INVENTORYSLOT_REGION))
    regions.LEVELUP_REGION = tuple(map(lambda  i, j: i+j, game_region, regions.LEVELUP_REGION))
    regions.TEXTBOX_REGION = tuple(map(lambda  i, j: i+j, game_region, regions.TEXTBOX_REGION))

    regions.CURSOR_START = tuple(map(lambda i, j: i + j, game_region[:2], regions.CURSOR_START))
    regions.CURSOR_RETREAT = tuple(map(lambda i, j: i + j, game_region[:2], regions.CURSOR_RETREAT))
    regions.CURSOR_EXPEDITION = tuple(map(lambda i, j: i + j, game_region[:2], regions.CURSOR_EXPEDITION))
    regions.CURSOR_CORNER = tuple(map(lambda  i, j: i+j, game_region[:2], regions.CURSOR_CORNER))
    regions.CURSOR_TRAIT = tuple(map(lambda i, j: i + j, game_region[:2], regions.CURSOR_TRAIT))
    regions.BOARD_CORNER = tuple(map(lambda  i, j: i+j, game_region[:2], regions.BOARD_CORNER))
    regions.CURSOR_LEVELUP = tuple(map(lambda i, j: i + j, game_region[:2], regions.CURSOR_LEVELUP))
    regions.CURSOR_REWARD = tuple(map(lambda i, j: i + j, game_region[:2], regions.CURSOR_REWARD))

    regions.STAY_RETREAT_CORNER = tuple(map(lambda  i, j: i+j, game_region, regions.STAY_RETREAT_CORNER))
    regions.MIDDLE_RETREAT = tuple(map(lambda  i, j: i+j, regions.STAY_RETREAT_CORNER, regions.MIDDLE_RETREAT))
    regions.LEFT_RETREAT  = tuple(map(lambda  i, j: i+j, regions.STAY_RETREAT_CORNER, regions.LEFT_RETREAT))
    regions.STAY_REGION = tuple(map(lambda i, j: i + j, regions.STAY_RETREAT_CORNER, regions.STAY_REGION))
    regions.RESURRECT_REGION  = tuple(map(lambda i, j: i + j, regions.STAY_RETREAT_CORNER, regions.RESURRECT_REGION))
    regions.CURSOR_RESURRECT = tuple(map(lambda i, j: i + j, regions.STAY_RETREAT_CORNER, regions.CURSOR_RESURRECT))
    regions.CURSOR_MIDDLE_RETREAT = tuple(map(lambda i, j: i + j, regions.STAY_RETREAT_CORNER[:2], regions.CURSOR_MIDDLE_RETREAT))

    mapGrid = ()
    while (True):
        success = False
        equipment_slots = ([ITEM_TYPES.Weapon, 0, tuple(map(lambda i, j: i + j, game_region[:2], (1082, 76)))],
                           [ITEM_TYPES.Weapon, 0, tuple(map(lambda i, j: i + j, game_region[:2], (1082, 186)))],
                           [ITEM_TYPES.Armor, 0, tuple(map(lambda i, j: i + j, game_region[:2], (1137, 186)))],
                           [ITEM_TYPES.Boot, 0, tuple(map(lambda i, j: i + j, game_region[:2], (1192, 186)))],
                           [ITEM_TYPES.Amulet, 0, tuple(map(lambda i, j: i + j, game_region[:2], (1137, 131)))])
        while (not success):
            start_game()
            img = screenbitmap(regions.MAP_REGION, True)
            (mapGrid, success) = read_map(img)
            if not success:
                click(regions.CURSOR_RETREAT)
                time.sleep(2)
                ret = pyautogui.locateOnScreen("Misc\Left_Retreat.png", region=regions.LEFT_RETREAT)
                click(ret)
                time.sleep(2)
        battled = True
        game_running = True
        while (game_running):
            if (pyautogui.locateOnScreen("Misc\Paused.png", region=regions.PAUSE_REGION)):
                time.sleep(0.25)
                img = screenbitmap(regions.INVENTORY_REGION)
                if battled:
                    mapGrid= play_hand(mapGrid)
                    battled = False
                invslots = []
                for x in range(4):
                    for y in range(3):
                        if x == 3 and y == 2:
                            pass
                        else:
                            if search_inventory_tile(x, y, img):
                                invslots.append((x,y))
                # Sort it like a snake, thats the order items are shifted in the inventory
                invslots = sorted(invslots, key=lambda i: ((i[1],-i[0]) if i[1] == 1 else (i[1], i[0])), reverse=True)
                equip_items(invslots,equipment_slots)
                rightclick(regions.CURSOR_CORNER)

            if (pyautogui.locateOnScreen("Misc\Battle.png", region=regions.BATTLE_REGION)):
                battled = True
            else:
                if battled:
                    rightclick(regions.CURSOR_CORNER)

                    #Just taking the topmost trait
                    if (pyautogui.locateOnScreen("Misc\Levelup.png", region=regions.LEVELUP_REGION)):
                        click(regions.CURSOR_LEVELUP)
                        click(regions.CURSOR_TRAIT)
                        time.sleep(0.5)
                        click(regions.CURSOR_TRAIT)

                    mapGrid = play_hand(mapGrid)
                    battled = False
                    rightclick(regions.CURSOR_CORNER)
                    print_state(mapGrid)

            #Boss Fight
            boss = pyautogui.locateOnScreen("Misc\Stay.png", region=regions.STAY_REGION)
            if (boss):
                click(boss)
                time.sleep(2)
                #Textbox entry
                for l in range(5):
                    click(regions.CURSOR_CORNER)
                    time.sleep(1)
                while (True):
                    if (pyautogui.locateOnScreen("Misc\Battle.png", region=regions.BATTLE_REGION)):
                        break
                while (True):
                    if (pyautogui.locateOnScreen("Misc\Textbox.png", region=regions.TEXTBOX_REGION)):
                        #Textbox Outro
                        time.sleep(3)
                        for l in range(5):
                            click(regions.CURSOR_CORNER)
                            time.sleep(1)
                        time.sleep(1)
                        click(regions.CURSOR_REWARD)
                        time.sleep(0.5)
                        click(pyautogui.locateOnScreen("Misc\Left_Retreat.png", region=regions.LEFT_RETREAT))
                        time.sleep(2)
                        game_running = False
                        break

                #Defeat
            if (pyautogui.locateOnScreen("Misc\Middle_Retreat.png", region=regions.MIDDLE_RETREAT)):
                game_running = False
                click(regions.CURSOR_MIDDLE_RETREAT)
                time.sleep(2)

            if (pyautogui.locateOnScreen("Misc\Resurrect.png", region=regions.RESURRECT_REGION)):
                click(regions.CURSOR_RESURRECT)





if __name__ == "__main__":
    main()