import telnetlib
import time
import os
import re
import shutil

# 0 = ?                                         # attempting login
# 1 = ?                                         # attempting signin
# 2 = ?                                         # ?
# 3 = ?                                         # ?
phase = 0

# Set these configurations as necessary
gameServerBatchFilePath = r"C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die"
gameServerBatchFileName = "startdedicated.bat"
gameServerTelnetPort = 8081
gameServerTelnetTimeout = 5
gameServerPassword = b"123456789"

gamePreferencesName = ""
gamePreferencesWorld = ""
gamePreferencesDatafolder = ""
gameSaveFolderPath = ""

el = b"\n"

deadPlayer = ""

gameLoop = 0

batchRun = False

commandGetGamePrefActive = False

t = telnetlib.Telnet()

while (True):
    if (phase == -1):
        print("Resetting variables")
        # Reset necessary variables
        batchRun = False
        gamePreferencesName = ""
        gamePreferencesWorld = ""
        gamePreferencesDatafolder = ""
        gameSaveFolderPath = ""
        deadPlayer = ""
        commandGetGamePrefActive = False        
        phase = 0
    elif (phase == 0):
        # Attempt a connection to an existing 7 Days server, or execute the batch file if an exception is thrown
        try:
            print("Attempting connection to 7 Days Server")
            t = telnetlib.Telnet("localhost", gameServerTelnetPort, gameServerTelnetTimeout)
        except:
            if (batchRun == False):
                print("Unable to connect! Launching server manually via batch file")
                os.chdir(gameServerBatchFilePath)
                os.startfile(gameServerBatchFileName)
                batchRun = True
            continue
        gameLoop += 1
        print("Connected to 7 Days server, beginning loop: " + str(gameLoop))
        phase = 1
    elif (phase == 1):
        lineRead = t.read_until(b"\r").decode("ascii")
        #print(lineRead)
        if ("Please enter password:" in lineRead):
            t.write(gameServerPassword + el)
        elif ("Press 'exit' to end session." in lineRead):
            phase = 2
            print("Connected to server")
    elif (phase == 2):
        if (commandGetGamePrefActive == False):
            print("Sending getgamepref for GameName, GameWorld, and UserDataFolder")
            t.write(b"getgamepref" + el)
            commandGetGamePrefActive = True
        lineRead = t.read_until(b"\r").decode("ascii")
        #print(lineRead)
        if ("GamePref.GameName = " in lineRead):
            gamePreferencesName = lineRead.partition("GamePref.GameName = ")[2].rstrip()
            print("Found GameName")
        elif ("GamePref.GameWorld = " in lineRead):
            gamePreferencesWorld = lineRead.partition("GamePref.GameWorld = ")[2].rstrip()
            print("Found GameWorld")
        elif ("GamePref.UserDataFolder = " in lineRead):
            gamePreferencesDatafolder = lineRead.partition("GamePref.UserDataFolder = ")[2].rstrip()
            print("Found UserDataFolder")
        elif ("GamePref.ZombiePlayers = " in lineRead):
            commandGetGamePrefActive = False

        if (gamePreferencesName != "" and gamePreferencesWorld != "" and gamePreferencesDatafolder != "" and commandGetGamePrefActive == False):
            gameSaveFolderPath = gamePreferencesDatafolder + "\\Saves\\" + gamePreferencesWorld + "\\" + gamePreferencesName
            print("Game save location found for current server configuration: " + gameSaveFolderPath)
            # C:\Users\DatapawWolf\AppData\Roaming\7DaysToDie\Saves\Navezgane\My Game
            doesExist = os.path.isdir(gameSaveFolderPath)
            print("Does folder exist: " + str(doesExist))
            if (doesExist == False):
                print("Error: save folder specified by server configuration does not exist. Terminating app")
                quit()
            print("Command completed, beginning game management")
            phase = 3
    elif (phase == 3):
        lineRead = t.read_until(b"\r").decode("ascii")
        #print(lineRead)
        deadPlayerSearch = re.search(".*GMSG: Player ('.*') died.*", lineRead)        
        if (deadPlayerSearch != None):
            print(lineRead)
            deadPlayer = deadPlayerSearch.group(1)
            print("Player " + deadPlayer + ".")
            phase = 4
        # If player name is somehow blank, we aren't handling it yet
    elif (phase == 4):
        print("Sending closing messages to server")
        t.write(b"say \"Player " + str.encode(deadPlayer) + b" has died, shutting down server in 5...\"" + el)
        time.sleep(1)
        t.write(b"say \"4...\"" + el)
        time.sleep(1)
        t.write(b"say \"3...\"" + el)
        time.sleep(1)
        t.write(b"say \"2...\"" + el)
        time.sleep(1)
        t.write(b"say \"1...\"" + el)
        time.sleep(1)
        phase = 5
    elif (phase == 5):
        # Send shutdown command to the server but wait for the return INF 
        t.write(b"shutdown" + el)
        t.read_until(b"INF OnApplicationQuit\r")
        # Sleep for a second to allow the server to finish closing
        time.sleep(1)
        t.close()
        print("Connection closed, server shut down")
        phase = 6
    elif (phase == 6):
        print("Deleting save game data directory from previous run")
        # Loop through folder previously obtained from game preferences and delete files within folder
        for filename in os.listdir(gameSaveFolderPath):
            file_path = os.path.join(gameSaveFolderPath, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print("Error: failed to delete %s. Reason: %s. Terminating app" % (file_path, e))
        print("Restarting process")
        phase = -1
    elif (phase == 7):
        break
    continue

# Closing may cause errors if the server is still sending data - we'll sleep for a couple seconds to prevent those
time.sleep(2)
t.close()