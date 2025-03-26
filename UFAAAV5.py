import json
import os
import random
import shutil
import time
import pyautogui
import paho.mqtt.client as mqtt

import threading

file_lock = threading.Lock()
CURRENT_USER_FILE_PATH = r"C:\Shared\loggedUser.json"
COMPUTER_ID_FILE_PATH = r"C:\Shared\computerID.json"
LOG_FILE_PATH = r"C:\Shared\logging.json"

# MQTT Configuration
BROKER = "192.168.109.155"
PORT = 1883
TOPIC = "logs/ual"
USERNAME = "testuser"
PASSWORD = "testpass"

# Path to ual.json in the Publisher VM
UAL_JSON_PATH = r"C:\Users\janva\Downloads\ual.json"

class User:
    def __init__(self, username, role, directoryAccessList):
        self.username = username
        self.role = role
        directoryAccessList = (directoryAccessList + ["C:\\Users\\janva\\Downloads\\ExternalDrive"] +
                               [f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder"])
        self.directoryAccessList = directoryAccessList
        self.nFrequencyOfFileAccessAttemptTypes = {
            'nOpenCF': 0,
            'nModifyCF': 0,
            'nMoveCF': 0,
            'nCopyCF': 0,
            'nDeleteCF': 0,
            'nOpenNonCF': 0,
            'nModifyNonCF': 0,
            'nMoveNonCF': 0,
            'nCopyNonCF': 0,
            'nDeleteNonCF': 0
        }
        self.nFileCounts = {
            # Copy operations
            'COPY_INTERNAL': 1,
            'COPY_EXTERNAL': 1,
            'COPY_NON_INTERNAL': 1,
            'COPY_NON_EXTERNAL': 1,
            'COPY_OTHERS': 1,
            'COPY_NON_OTHERS': 1,

            # Delete operations
            'DELETE': 1,
            'DELETE_NON': 1,

            # Move operations
            'MOVE_INTERNAL': 1,
            'MOVE_EXTERNAL': 1,
            'MOVE_NON_INTERNAL': 1,
            'MOVE_NON_EXTERNAL': 1,
            'MOVE_OTHERS': 1,
            'MOVE_NON_OTHERS': 1
        }

        self.nFileAccessAttempts = 0

    def getRole(self):
        return self.role

    def getUsername(self):
        return self.username

    def getNFileAccessAttempts(self):
        return self.nFileAccessAttempts

    def printStats(self):
        print(f"Username: {self.username}")
        print(f"Role: {self.role}")
        print("File Access Attempt Statistics:")
        for fileAccessAttemptType, count in self.nFrequencyOfFileAccessAttemptTypes.items():
            print(f"  {fileAccessAttemptType}: {count}")
        print(f"Total File Access Attempts: {self.nFileAccessAttempts}")

    def openFile(self, directory):
        os.startfile(directory)
        self.sleepProgram(3)

    def closeFile(self):
        pyautogui.hotkey('alt', 'f4')

    def saveFile(self):
        pyautogui.hotkey("ctrl", "s")

    def sleepProgram(self, seconds):
        time.sleep(seconds)

    def updateFileAccess(self, username, role, actionType, count):
        try:
            with open(LOG_FILE_PATH, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Could not load JSON file.")
            return

        if username in data[role]:
            data[role][username][actionType] += count
            data[role][username]["TotalAttempts"] += count

        if "Total" in data[role] and username in data[role]["Total"]:
            data[role]["Total"][username] += count

        data["Overall"][role]["Total Attempts"] += count
        data["Overall"]["Total Attempts"] += count

        with open(LOG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)

    def updateFileTransfer(self, username, role, actionType, transferType, count):
        try:
            with open(LOG_FILE_PATH, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Could not load JSON file.")
            return

        if username in data[role]:
            data[role][username][actionType] += count
            data[role][username][transferType] += count
            data[role][username]["TotalAttempts"] += count

            if transferType in [
                "nMoveNonCFToAS", "nMoveNonCFToManagers", "nMoveNonCFToDirectors",
                "nMoveCFToAS", "nMoveCFToManagers", "nMoveCFToDirectors"
            ]:
                toOthersKey = "nMoveNonCFToOthers" if "NonCF" in transferType else "nMoveCFToOthers"
                data[role][username][toOthersKey] += count

            if transferType in [
                "nCopyNonCFToAS", "nCopyNonCFToManagers", "nCopyNonCFToDirectors",
                "nCopyCFToAS", "nCopyCFToManagers", "nCopyCFToDirectors"
            ]:
                toOthersKey = "nCopyNonCFToOthers" if "NonCF" in transferType else "nCopyCFToOthers"
                data[role][username][toOthersKey] += count

        if "Total" in data[role] and username in data[role]["Total"]:
            data[role]["Total"][username] += count

        data["Overall"][role]["Total Attempts"] += count
        data["Overall"]["Total Attempts"] += count

        with open(LOG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)

    def typeTextAndSave(self, amountOfModifies, directory):
        for i in range(amountOfModifies):
            pyautogui.typewrite("f")
            self.saveFile()
            self.sleepProgram(1)

        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nModifyNonCF', amountOfModifies)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nModifyCF', amountOfModifies)

    def simulateOpen(self, directory):
        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenNonCF', 1)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenCF', 1)
        self.openFile(directory)
        self.closeFile()

    def simulateOpenWithModify(self, amountOfModifies, directory):
        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenNonCF', 1)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenCF', 1)
        self.openFile(directory)
        self.typeTextAndSave(1, directory)
        self.closeFile()

    def deleteFile(self, directory):
        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nDeleteNonCF', 1)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nDeleteCF', 1)
        os.remove(directory)

    def moveFile(self, sourceDirectory, destinationDirectory):
        if 'NON' in sourceDirectory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nMoveNonCF', 1)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nMoveCF', 1)
        shutil.move(sourceDirectory, destinationDirectory)

    def moveFiles(self, sourceDirectory, destinationDirectory, transferType):
        shutil.move(sourceDirectory, destinationDirectory)
        if 'NON' in sourceDirectory:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nMoveNonCF', transferType, 1)
        else:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nMoveCF', transferType, 1)


    def copyFile(self, sourceDirectory, destinationDirectory):
        if 'NON' in sourceDirectory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nCopyNonCF', 1)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nCopyCF', 1)
        shutil.copy2(sourceDirectory, destinationDirectory)

    def copyFiles(self, sourceDirectory, destinationDirectory, transferType):
        shutil.copy2(sourceDirectory, destinationDirectory)
        if 'NON' in sourceDirectory:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nCopyNonCF', transferType, 1)
        else:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nCopyCF', transferType, 1)


class UserFileAccessAttemptAutomator:
    def __init__(self):
        self.userList = []
        self.roleFunctions = {
            "Authorized": {
                "Administrative Staff": [
                    # 0 Administrative staff opening non-confidential files without permission from the manager or director.
                     self.simulateOpenNonConfidentialFile,
                    # ======================================================================
                    # 1 Managers and Administrative Staff modifying non-confidential files
                    self.simulateOpenNonConfidentialFileWithModify,
                    # ======================================================================
                    # 2 Administrative Staff copy non-confidential files to internal storage (self) without permission from the Manager or Director
                    self.simulateCopyNonConfidentialFileInternal,
                    # ======================================================================
                ],
                "Administrative Staff M-Req": [
                    # 0 Administrative staff opening confidential files with permission from the manager or director.
                    self.simulateOpenConfidentialFile,
                    # ======================================================================
                    # 1 Administrative Staff move non-confidential files to internal storage (self) with permission from the Manager or Director
                    self.simulateMoveNonConfidentialFileInternal,
                    # ======================================================================
                    # 2 Administrative Staff copy confidential files to internal storage (self) of with permission from a Manager or Director
                    self.simulateCopyConfidentialFileInternal,
                    # ======================================================================
                    # 3 4 Administrative Staff copy non-confidential and confidential files to external storages with permission from Manager or Director.
                    self.simulateCopyNonConfidentialFileExternal,
                    self.simulateCopyConfidentialFileExternal,
                    # ======================================================================
                ],
                "Administrative Staff D-Req": [
                    # 0 Administrative staff opening confidential files with permission from the manager or director.
                    self.simulateOpenConfidentialFile,
                    # ======================================================================
                    # 1 Managers and Administrative Staff modifying confidential files with permission of the director
                    self.simulateOpenConfidentialFileWithModify,
                    # ======================================================================
                    # 2 3 Managers and administrative staff deleting confidential and non-confidential files with the permission from the Director
                    self.simulateDeleteNonConfidentialFile,
                    self.simulateDeleteConfidentialFile,
                    # ======================================================================
                    # 4 Administrative Staff move non-confidential files to internal storage (self) with permission from the Manager or Director
                    self.simulateMoveNonConfidentialFileInternal,
                    # ======================================================================
                    # 5 Administrative Staff copy confidential files to internal storage (self) of with permission from a Manager or Director
                    self.simulateCopyConfidentialFileInternal,
                    # ======================================================================
                    # 6 Administrative Staff move confidential files to internal storage (self) of with permission from the Director
                    self.simulateMoveConfidentialFileInternal,
                    # ======================================================================
                    # 7 8 Administrative Staff copy non-confidential and confidential files to external storages with permission from Manager or Director.
                    self.simulateCopyNonConfidentialFileExternal,
                    self.simulateCopyConfidentialFileExternal,
                    # ======================================================================
                    # 9 10  Administrative Staff move non-confidential and confidential files to external storages with permission from Director.
                    self.simulateMoveNonConfidentialFileExternal,
                    self.simulateMoveConfidentialFileExternal,
                    # ======================================================================
                ],
                "Manager": [
                    # 0 1 Directors and managers opening confidential and non-confidential files
                    self.simulateOpenNonConfidentialFile,
                    self.simulateOpenConfidentialFile,
                    # ======================================================================
                    # 2 Managers and Administrative Staff modifying non-confidential files
                    self.simulateOpenNonConfidentialFileWithModify,
                    # ======================================================================
                    # 3 4 5 6 Managers copy both confidential and non-confidential files to internal storages (Self ,Staff) without permission from the Director
                    self.simulateCopyNonConfidentialFileInternal,
                    self.simulateCopyConfidentialFileInternal,
                    self.simulateCopyNonConfidentialFileToOthers,
                    self.simulateCopyConfidentialFileToOthers,
                    # ======================================================================
                    # 7 8 Managers copy non-confidential or confidential files to external storages without permission from the Director
                    self.simulateCopyNonConfidentialFileExternal,
                    self.simulateCopyConfidentialFileExternal,
                    # ======================================================================
                ],
                "Manager D-Req": [
                    # 0 Managers and Administrative Staff modifying confidential files with permission of the director
                    self.simulateOpenConfidentialFileWithModify,
                    # ======================================================================
                    # 1 2 Managers and administrative staff deleting confidential and non-confidential files with the permission from the Director
                    self.simulateDeleteNonConfidentialFile,
                    self.simulateDeleteConfidentialFile,
                    # ======================================================================
                    # 3 4 5 6 Managers move both confidential and non-confidential files to internal storages (Self, Staff) with permission from the Director
                    self.simulateMoveNonConfidentialFileInternal,
                    self.simulateMoveConfidentialFileInternal,
                    self.simulateMoveNonConfidentialFileToOthers,
                    self.simulateMoveConfidentialFileToOthers,
                    # ======================================================================
                    # 7 8 Managers move non-confidential or confidential files to external storages with permission from the Director
                    self.simulateMoveNonConfidentialFileExternal,
                    self.simulateMoveConfidentialFileExternal,
                    # ======================================================================
                ],
                "Director": [
                    # 0 1 Directors and managers opening confidential and non-confidential files
                    self.simulateOpenNonConfidentialFile,
                    self.simulateOpenConfidentialFile,
                    # ======================================================================
                    # 2 3 Directors editing non-confidential and confidential files
                    self.simulateOpenNonConfidentialFileWithModify,
                    self.simulateOpenConfidentialFileWithModify,
                    # ======================================================================
                    # 4 5 Directors deleting confidential and non-confidential files
                    self.simulateDeleteNonConfidentialFile,
                    self.simulateDeleteConfidentialFile,
                    # ======================================================================
                    # 6 7 8 9 10 11 12 13 Directors copy and move both non-confidential and confidential files to internal storages (Self, Manager, Staff)
                    self.simulateMoveNonConfidentialFileInternal,
                    self.simulateMoveConfidentialFileInternal,
                    self.simulateMoveNonConfidentialFileToOthers,
                    self.simulateMoveConfidentialFileToOthers,
                    self.simulateCopyNonConfidentialFileInternal,
                    self.simulateCopyConfidentialFileInternal,
                    self.simulateCopyNonConfidentialFileToOthers,
                    self.simulateCopyConfidentialFileToOthers,
                    # ======================================================================
                    # 14 15 16 17 Directors move and copy confidential or non-confidential files to external storages
                    self.simulateMoveNonConfidentialFileExternal,
                    self.simulateMoveConfidentialFileExternal,
                    self.simulateCopyNonConfidentialFileExternal,
                    self.simulateCopyConfidentialFileExternal,
                    # ======================================================================
                ]
            },
            "Unauthorized": {
                "Administrative Staff WO M-Req": [
                    # 0 Administrative staff opening confidential files without permission from the manager or director
                    self.simulateOpenConfidentialFile,
                    # ======================================================================
                    # 1 Administrative Staff move non-confidential files to internal storage (self) of without permission from a Manager or Director
                    self.simulateMoveNonConfidentialFileInternal,
                    # ======================================================================
                    # 2 Administrative Staff copy confidential files to internal storage (self) of without permission from a Manager or Director
                    self.simulateCopyConfidentialFileInternal,
                    # ======================================================================
                    # 3 4 Administrative Staff copy non-confidential and confidential files to external storages without permission from Manager or Director.
                    self.simulateCopyNonConfidentialFileExternal,
                    self.simulateCopyConfidentialFileExternal,
                    # ======================================================================
                ],
                "Administrative Staff WO D-Req": [
                    # 0  Administrative staff opening confidential files without permission from the manager or director
                    self.simulateOpenConfidentialFile,
                    # ======================================================================
                    # 1 Managers and Administrative Staff modifying confidential files without permission of the director
                    self.simulateOpenConfidentialFileWithModify,
                    # ======================================================================
                    # 2 3 Managers and administrative staff deleting confidential and non-confidential files without the permission from the Director
                    self.simulateDeleteNonConfidentialFile,
                    self.simulateDeleteConfidentialFile,
                    # ======================================================================
                    # 4 Administrative Staff move non-confidential files to internal storage (self) of without permission from a Manager or Director
                    self.simulateMoveNonConfidentialFileInternal,
                    # ======================================================================
                    # 5 Administrative Staff copy confidential files to internal storage (self) of without permission from a Manager or Director
                    self.simulateCopyConfidentialFileInternal,
                    # ======================================================================
                    # 6 Administrative Staff move confidential files to internal storage (self) of without permission from the Director
                    self.simulateMoveConfidentialFileInternal,
                    # ======================================================================
                    # 7 8 Administrative Staff copy non-confidential and confidential files to external storages without permission from Manager or Director.
                    self.simulateCopyNonConfidentialFileExternal,
                    self.simulateCopyConfidentialFileExternal,
                    # ======================================================================
                    # 9 10 Administrative Staff move non-confidential and confidential files to external storages without permission from Director.
                    self.simulateMoveNonConfidentialFileExternal,
                    self.simulateMoveConfidentialFileExternal,
                    # ======================================================================
                ],
                "Manager WO D-Req": [
                    # 0 Managers and Administrative Staff modifying confidential files without permission of the director
                    self.simulateOpenConfidentialFileWithModify,
                    # ======================================================================
                    # 1 2 Managers and administrative staff deleting confidential and non-confidential files without the permission from the Director
                    self.simulateDeleteNonConfidentialFile,
                    self.simulateDeleteConfidentialFile,
                    # ======================================================================
                    # 3 4 5 6 Managers move both confidential and non-confidential files to internal storages (Self, Staff) without permission from the director
                    self.simulateMoveConfidentialFileInternal,
                    self.simulateMoveNonConfidentialFileInternal,
                    self.simulateMoveNonConfidentialFileToOthers,
                    self.simulateMoveConfidentialFileToOthers,
                    # ======================================================================
                    # 7 8 Managers move non-confidential or confidential files to external storages without permission from the Director.
                    self.simulateMoveNonConfidentialFileExternal,
                    self.simulateMoveConfidentialFileExternal,
                    # ======================================================================
                ],
                "Director": [

                ]
            }
        }
        self.nTotalFileAccessAttempts = 0
        self.nTotalAdministrativeStaff = 0
        self.nTotalManagers = 0
        self.nTotalDirectors = 0
        self.staffDirectories = []
        self.managerDirectories = []
        self.directorDirectories = []
        self.client = mqtt.Client()
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.userList = []
        self.client.connect(BROKER, PORT)
        self.client.loop_start()

    def createAdministrativeStaff(self):
        self.nTotalAdministrativeStaff += 1
        ASUsername = f"AS{self.nTotalAdministrativeStaff}"
        directory = f"C:\\Users\\janva\\Downloads\\{ASUsername}"
        self.staffDirectories.append(directory)
        user = User(ASUsername, "Administrative Staff", [directory])
        self.userList.append(user)
        self.updateManagerAndDirectorDirectories()

    def createManager(self):
        self.nTotalManagers += 1
        ManagerUsername = f"Manager{self.nTotalManagers}"
        directory = f"C:\\Users\\janva\\Downloads\\{ManagerUsername}"
        self.managerDirectories.append(directory)
        directories = [directory] + self.staffDirectories
        user = User(ManagerUsername, "Manager", directories)
        self.userList.append(user)
        self.updateDirectorDirectories()

    def createDirector(self):
        self.nTotalDirectors += 1
        DirectorUsername = f"Director{self.nTotalDirectors}"
        directory = f"C:\\Users\\janva\\Downloads\\{DirectorUsername}"
        self.directorDirectories.append(directory)
        directories = [directory] + self.managerDirectories + self.staffDirectories
        user = User(DirectorUsername, "Director", directories)
        self.userList.append(user)

    def updateManagerAndDirectorDirectories(self):
        for user in self.userList:
            if user.role == "Manager":
                user.directoryAccessList = [user.directoryAccessList[0]] + self.staffDirectories
            elif user.role == "Director":
                user.directoryAccessList = [user.directoryAccessList[
                                                0]] + self.managerDirectories + self.staffDirectories

    def updateDirectorDirectories(self):
        for user in self.userList:
            if user.role == "Director":
                user.directoryAccessList = [user.directoryAccessList[
                                                0]] + self.managerDirectories + self.staffDirectories

    def writeLoggedInUserToFile(self, username):
        try:
            with open(CURRENT_USER_FILE_PATH, "w") as file:
                json.dump({"username": username}, file)
        except Exception as e:
            print(f"Error writing to file: {e}")

    def getUser(self, index):
        return self.userList[index]

    def generateRandomNumberOfModifies(self):
        return random.randint(1, 5)

    # OPEN CONFIDENTIAL, NON-CONFIDENTIAL
    def simulateOpenNonConfidentialFile(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, "_OPEN_NON")
        filePath = directory + "\\" + fileName
        user.simulateOpen(filePath)

    def simulateOpenConfidentialFile(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, "_OPEN")
        filePath = directory + "\\" + fileName
        user.simulateOpen(filePath)

    # MODIFY CONFIDENTIAL, NON-CONFIDENTIAL
    def simulateOpenNonConfidentialFileWithModify(self, index):
        user: User = self.getUser(index)
        amountOfModifies = self.generateRandomNumberOfModifies()
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, "_OPENWMOD_NON")
        filePath = directory + "\\" + fileName
        user.simulateOpenWithModify(amountOfModifies, filePath)

    def simulateOpenConfidentialFileWithModify(self, index):
        user: User = self.getUser(index)
        amountOfModifies = self.generateRandomNumberOfModifies()
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, "_OPENWMOD")
        filePath = directory + "\\" + fileName
        user.simulateOpenWithModify(amountOfModifies, filePath)

    # DELETE CONFIDENTIAL, NON-CONFIDENTIAL
    def simulateDeleteNonConfidentialFile(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        deleteCount = user.nFileCounts['DELETE_NON']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_DELETE_NON_{deleteCount}")
        filePath = directory + "\\" + fileName

        user.deleteFile(filePath)
        user.nFileCounts['DELETE_NON'] += 1

    def simulateDeleteConfidentialFile(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        deleteCount = user.nFileCounts['DELETE']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_DELETE_{deleteCount}")
        filePath = directory + "\\" + fileName

        user.deleteFile(filePath)
        user.nFileCounts['DELETE'] += 1

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL TO INTERNAL
    def simulateMoveNonConfidentialFileInternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        moveCount = user.nFileCounts['MOVE_NON_INTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_MOVE_NON_INTERNAL_{moveCount}")
        filePath = directory + "\\" + fileName

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder", "nMoveNonCFMainToInternal")
        user.nFileCounts['MOVE_NON_INTERNAL'] += 1

    def simulateMoveConfidentialFileInternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        moveCount = user.nFileCounts['MOVE_INTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_MOVE_INTERNAL_{moveCount}")
        filePath = directory + "\\" + fileName

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder", "nMoveCFMainToInternal")
        user.nFileCounts['MOVE_INTERNAL'] += 1

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL TO EXTERNAL
    def simulateMoveNonConfidentialFileExternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        moveCount = user.nFileCounts['MOVE_NON_EXTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_MOVE_NON_EXTERNAL_{moveCount}")
        filePath = directory + "\\" + fileName

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\ExternalDrive", "nMoveNonCFToExternal")
        user.nFileCounts['MOVE_NON_EXTERNAL'] += 1

    def simulateMoveConfidentialFileExternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        moveCount = user.nFileCounts['MOVE_EXTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_MOVE_EXTERNAL_{moveCount}")
        filePath = directory + "\\" + fileName

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\ExternalDrive", "nMoveCFToExternal")
        user.nFileCounts['MOVE_EXTERNAL'] += 1

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL TO OTHERS
    def simulateMoveNonConfidentialFileToOthers(self, index, permissionUsername):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        moveCount = user.nFileCounts['MOVE_NON_OTHERS']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_MOVE_NON_OTHERS_{moveCount}")
        filePath = directory + "\\" + fileName

        permissionRole = self.getUserRole(permissionUsername)

        if permissionRole == "Administrative Staff":
            transferType = "nMoveNonCFToAS"
        elif permissionRole == "Manager":
            transferType = "nMoveNonCFToManagers"
        elif permissionRole == "Director":
            transferType = "nMoveNonCFToDirectors"

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}", transferType)
        user.nFileCounts['MOVE_NON_OTHERS'] += 1

    def simulateMoveConfidentialFileToOthers(self, index, permissionUsername):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        moveCount = user.nFileCounts['MOVE_OTHERS']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_MOVE_OTHERS_{moveCount}")
        filePath = directory + "\\" + fileName

        permissionRole = self.getUserRole(permissionUsername)

        if permissionRole == "Administrative Staff":
            transferType = "nMoveCFToAS"
        elif permissionRole == "Manager":
            transferType = "nMoveCFToManagers"
        elif permissionRole == "Director":
            transferType = "nMoveCFToDirectors"

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}", transferType)
        user.nFileCounts['MOVE_OTHERS'] += 1

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL TO INTERNAL  (MIGHT NEED COPY-ONLY PURPOSE FILES)
    def simulateCopyNonConfidentialFileInternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        copyCount = user.nFileCounts['COPY_NON_INTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_COPY_NON_INTERNAL_{copyCount}")
        filePath = directory + "\\" + fileName

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder", "nCopyNonCFMainToInternal")
        user.nFileCounts['COPY_NON_INTERNAL'] += 1

    def simulateCopyConfidentialFileInternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        copyCount = user.nFileCounts['COPY_INTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_COPY_INTERNAL_{copyCount}")
        filePath = directory + "\\" + fileName

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder", "nCopyCFMainToInternal")
        user.nFileCounts['COPY_INTERNAL'] += 1

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL TO EXTERNAL  (MIGHT NEED COPY-ONLY PURPOSE FILES)
    def simulateCopyNonConfidentialFileExternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        copyCount = user.nFileCounts['COPY_NON_EXTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_COPY_NON_EXTERNAL_{copyCount}")
        filePath = directory + "\\" + fileName

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\ExternalDrive", "nCopyNonCFToExternal")
        user.nFileCounts['COPY_NON_EXTERNAL'] += 1

    def simulateCopyConfidentialFileExternal(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        copyCount = user.nFileCounts['COPY_EXTERNAL']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_COPY_EXTERNAL_{copyCount}")
        filePath = directory + "\\" + fileName

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\ExternalDrive", "nCopyCFToExternal")
        user.nFileCounts['COPY_EXTERNAL'] += 1

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL TO OTHERS
    def simulateCopyNonConfidentialFileToOthers(self, index, permissionUsername):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        copyCount = user.nFileCounts['COPY_NON_OTHERS']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_COPY_NON_OTHERS_{copyCount}")
        filePath = directory + "\\" + fileName

        permissionRole = self.getUserRole(permissionUsername)
        if permissionRole == "Administrative Staff":
            transferType = "nCopyNonCFToAS"
        elif permissionRole == "Manager":
            transferType = "nCopyNonCFToManagers"
        elif permissionRole == "Director":
            transferType = "nCopyNonCFToDirectors"
        else:
            transferType = "nCopyNonCFToOthers"

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}", transferType)
        user.nFileCounts['COPY_NON_OTHERS'] += 1

    def simulateCopyConfidentialFileToOthers(self, index, permissionUsername):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)

        copyCount = user.nFileCounts['COPY_OTHERS']

        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = self.getFileByAccessType(directory, username, f"_COPY_OTHERS_{copyCount}")
        filePath = directory + "\\" + fileName

        permissionRole = self.getUserRole(permissionUsername)
        if permissionRole == "Administrative Staff":
            transferType = "nCopyCFToAS"
        elif permissionRole == "Manager":
            transferType = "nCopyCFToManagers"
        elif permissionRole == "Director":
            transferType = "nCopyCFToDirectors"
        else:
            transferType = "nCopyCFToOthers"

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}", transferType)
        user.nFileCounts['COPY_OTHERS'] += 1

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL INTERNAL TO MAIN
    def simulateMoveNonConfidentialFileInternalToMain(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder"
        fileName = self.getRandomNonConfidentialFileFromDirectory(directory)
        filePath = directory + "\\" + fileName
        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}", "nMoveNonCFInternalToMain")

    def simulateMoveConfidentialFileInternalToMain(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder"
        fileName = self.getRandomConfidentialFileFromDirectory(directory)
        filePath = directory + "\\" + fileName
        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}", "nMoveCFInternalToMain")

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL INTERNAL TO MAIN (MIGHT NEED COPY-ONLY PURPOSE FILES)
    def simulateCopyNonConfidentialFileInternalToMain(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder"
        fileName = self.getRandomNonConfidentialFileFromDirectory(directory)
        filePath = directory + "\\" + fileName
        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}", "nCopyNonCFInternalToMain")

    def simulateCopyConfidentialFileInternalToMain(self, index):
        user: User = self.getUser(index)
        username = user.getUsername()
        self.writeLoggedInUserToFile(username)
        directory = f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder"
        fileName = self.getRandomConfidentialFileFromDirectory(directory)
        filePath = directory + "\\" + fileName
        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}", "nCopyCFInternalToMain")

    def getFilesFromDirectory(self, directory):
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return []

            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            return files
        except Exception as e:
            print(f"Error getting files from directory: {e}")
            return []

    def getRandomFileFromDirectory(self, directory):
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return []

            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            return random.choice(files)
        except Exception as e:
            print(f"Error getting random file from directory: {e}")
            return []

    def getRandomConfidentialFileFromDirectory(self, directory):
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return None

            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and "NON" not in f]
            return random.choice(files) if files else None
        except Exception as e:
            print(f"Error getting random confidential file from directory: {e}")
            return None

    def getRandomNonConfidentialFileFromDirectory(self, directory):
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return None

            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and "NON" in f]
            return random.choice(files) if files else None
        except Exception as e:
            print(f"Error getting random non-confidential file from directory: {e}")
            return None

    def getFileByAccessType(self, directory, username, fileAccessAttemptType):
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return None

            for f in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, f)) and f.startswith(username) and fileAccessAttemptType in f:
                    return f

            print(f"No file with {fileAccessAttemptType} found for {username} in {directory}.")
            return None
        except Exception as e:
            print(f"Error getting file with {fileAccessAttemptType}: {e}")
            return None

    def getNonConfidentialFilenameToOpen(self, directory, username):
        try:
            if not os.path.exists(directory):
                print(f"Directory does not exist: {directory}")
                return None

            for f in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, f)) and f.startswith(username) and "_OPEN_NON" in f:
                    return f

            print(f"No non-confidential file to open found for {username} in {directory}.")
            return None
        except Exception as e:
            print(f"Error getting non-confidential file to open: {e}")
            return None

    def getRandomIndexForAS(self):
        ASIndices = [i for i, user in enumerate(self.userList) if user.getRole() == "Administrative Staff"]
        return random.choice(ASIndices) if ASIndices else None

    def getRandomIndexForManagers(self):
        managerIndices = [i for i, user in enumerate(self.userList) if user.getRole() == "Manager"]
        return random.choice(managerIndices) if managerIndices else None

    def getRandomIndexForDirectors(self):
        directorIndices = [i for i, user in enumerate(self.userList) if user.getRole() == "Director"]
        return random.choice(directorIndices) if directorIndices else None

    def getRandomUsernameByAS(self):
        ASUsers = [user.username for user in self.userList if user.role == "Administrative Staff"]
        return random.choice(ASUsers) if ASUsers else None

    def getRandomUsernameByManager(self):
        managerUsers = [user.username for user in self.userList if user.role == "Manager"]
        return random.choice(managerUsers) if managerUsers else None

    def getRandomUsernameByDirector(self):
        directorUsers = [user.username for user in self.userList if user.role == "Director"]
        return random.choice(directorUsers) if directorUsers else None

    def getUserRoleAndIndex(self, username):
        for index, user in enumerate(self.userList):
            if user.username == username:
                if username.startswith("AS"):
                    return "Administrative Staff", index
                elif username.startswith("Manager"):
                    return "Manager", index
                elif username.startswith("Director"):
                    return "Director", index

        return None

    def getUserRole(self, username):
        if username.startswith("AS"):
            return "Administrative Staff"
        elif username.startswith("Manager"):
            return "Manager"
        elif username.startswith("Director"):
            return "Director"

    def getUserRoles(self, room):
        users = self.getUsers(room)
        user_roles = {}

        for user in users:
            if user.startswith("AS"):
                user_roles[user] = "Administrative Staff"
            elif user.startswith("M"):
                user_roles[user] = "Manager"
            elif user.startswith("D"):
                user_roles[user] = "Director"

        return user_roles

    def getRoomAUserRoles(self):
        return self.getUserRoles("Room A")

    def getRoomBUserRoles(self):
        return self.getUserRoles("Room B")

    def getRoomCUserRoles(self):
        return self.getUserRoles("Room C")
    def getRoomDUserRoles(self):
        return self.getUserRoles("Room D")

    def getUsers(self, room):
        return self.loadRooms().get(room, [])

    def getRoomAUsers(self):
        return self.getUsers("Room A")

    def getRoomBUsers(self):
        return self.getUsers("Room B")

    def getRoomCUsers(self):
        return self.getUsers("Room C")

    def getRoomDUsers(self):
        return self.getUsers("Room D")

    def getRandomUserIndex(self):
        return random.randint(0, len(self.userList) - 1) if self.userList else None

    def automateFileAccess(self):
        actions = [
            self.simulateOpenConfidentialFileWithModify
        ]
        while True:
            user_index = self.getRandomUserIndex()
            if user_index is not None:
                action = random.choice(actions)
                action(user_index)

    def checkFlag(self):
        communicator_path = r'C:\Users\janva\Downloads\communicator.json'

        try:
            with open(communicator_path, "r") as file:
                comm_data = json.load(file)

            if comm_data.get("flag") == 1:
                print("🚀 Automator detected a move!")

                comm_data["flag"] = 0
                with open(communicator_path, "w") as file:
                    json.dump(comm_data, file, indent=4)

        except FileNotFoundError:
            print("Error: communicator.json not found!")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in communicator.json!")

    def executeRoleActionByIndex(automator, role, position, index):
        actions = automator.roleFunctions.get(role, {}).get(position, [])

        if 0 <= index < len(actions):
            action = actions[index]

            method = getattr(automator, action, None)
            if method:
                method()
            else:
                print(f"Method {action} not found.")
        else:
            print("Invalid index or no actions found for this role and position.")

    def getAuthorizationStatus(self):
        return random.choice(["Authorized", "Unauthorized"])

    def getRandomRoleFromStatus(self, status):
        if status == "Authorized":
            return random.choice([
                "Administrative Staff",
                "Administrative Staff M-Req",
                "Administrative Staff D-Req",
                "Manager",
                "Manager D-Req",
                "Director"
            ])
        elif status == "Unauthorized":
            return random.choice([
                "Administrative Staff WO M-Req",
                "Administrative Staff WO D-Req",
                "Manager WO D-Req",
                "Director"
            ])

    def getUserRoomIndices(self, room, targetRole):
        #room = {'AS1': 'Administrative Staff', 'AS2': 'Administrative Staff', 'M1': 'Manager'}
        #targetRole = Administrative Staff M-Req
        matchedIndices = []

        primaryRole = targetRole.split(" WO")[0].split(" M-Req")[0].split(" D-Req")[0]

        for index, user in enumerate(self.userList):
            for key in room:
                if user.username == key and user.role == primaryRole:
                    matchedIndices.append(index)
                    break

                elif (user.username[0] == key[0] and user.username[-1] == key[-1] and user.role == primaryRole):
                    matchedIndices.append(index)
                    break

        return matchedIndices

    def checkRoles(self, roles, authorization):
        hasAdministrativeStaff = any(key.startswith('AS') for key in roles)
        hasManager = any(key.startswith('M') for key in roles)
        hasDirector = any(key.startswith('D') for key in roles)

        if authorization == "Authorized":
            if hasAdministrativeStaff and not hasManager and not hasDirector: #Staff only
                return "Administrative Staff"
            elif hasManager and not hasAdministrativeStaff and not hasDirector: #Manager only
                return "Manager"
            elif hasDirector and not hasAdministrativeStaff and not hasManager: #Director only
                return "Director"
            elif hasAdministrativeStaff and hasManager and not hasDirector: #Staff and Manager
                return random.choice(["Administrative Staff", "Manager", "Administrative Staff M-Req"])
            elif hasAdministrativeStaff and hasDirector and not hasManager: #Staff and Director
                return random.choice(["Administrative Staff", "Director", "Administrative Staff D-Req"])
            elif hasManager and hasDirector and not hasAdministrativeStaff: # Manager and Director
                return random.choice(["Manager", "Director", "Manager D-Req"])
            elif hasAdministrativeStaff and hasManager and hasDirector: #All
                return random.choice(["Administrative Staff", "Manager", "Director", "Administrative Staff M-Req",
                                      "Administrative Staff D-Req", "Manager D-Req"])
        elif authorization == "Unauthorized":
            if hasAdministrativeStaff and not hasManager and not hasDirector: #Staff only
                return random.choice(["Administrative Staff WO M-Req", "Administrative Staff WO D-Req"])
            elif hasManager and not hasAdministrativeStaff and not hasDirector: #Manager only
                return "Manager WO D-Req"
            elif hasAdministrativeStaff and hasManager and not hasDirector: #Staff and Manager
                return "Administrative Staff WO D-Req"
            elif hasAdministrativeStaff and hasDirector and not hasManager: #Staff and Director
                return "Administrative Staff WO M-Req"

    def getRandomAdministrativeStaff(self, userRoles):
        as_users = [key for key in userRoles if key.startswith('AS')]
        return random.choice(as_users) if as_users else None  # Return None if no AS found

    def getRandomManager(self, userRoles):
        m_users = [key for key in userRoles if key.startswith('M')]
        return random.choice(m_users) if m_users else None  # Return None if no Manager found

    def writeComputerIDToFile(self, roomNumber):
        with open(UAL_JSON_PATH, "r") as file:
            roomAssignments = json.load(file)

        room_map = {0: "Room A", 2: "Room C", 3: "Room D"}
        default_choices = {
            "Room A": ["Computer A0", "Computer A1"],
            "Room C": ["Computer C0", "Computer C1"],
            "Room D": ["Computer D"]
        }

        current_room = room_map[roomNumber]

        possible_alternatives = [
            room for room, users in roomAssignments.items()
            if users and room in default_choices and room != current_room
        ]

        # 5% chance: Pick from an occupied alternative room
        if random.random() <= 0.05 and possible_alternatives:
            alternative_room = random.choice(possible_alternatives)
            computerID = random.choice(default_choices[alternative_room])
        else:
            # 95% chance: Pick from the assigned room
            computerID = random.choice(default_choices[current_room])

        # Write to file
        with open(COMPUTER_ID_FILE_PATH, "w") as file:
            json.dump({"ComputerID": computerID}, file)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("🔗 Connected to MQTT Broker!")
            client.subscribe(TOPIC)
            print(f"Subscribed to topic: {TOPIC}")
        else:
            print(f"Connection failed, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            received_data = json.loads(msg.payload.decode())
            # print(f"Received updated UAL data: {received_data}")

            with file_lock:
                with open(UAL_JSON_PATH, "w", encoding="utf-8") as file:
                    json.dump(received_data, file, indent=4)

            self.automatorSimulation()

        except json.JSONDecodeError:
            print("Error: Failed to parse JSON from received message.")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT Broker.")
        if rc != 0:
            print("Unexpected disconnection. Attempting to reconnect...")
            self.reconnect()

    def reconnect(self):
        attempts = 0
        while attempts < 5:
            try:
                self.client.reconnect()
                print("Reconnected successfully!")
                return
            except Exception:
                attempts += 1
                print(f"Reconnect attempt {attempts}/5 failed. Retrying...")
        print("Could not reconnect after multiple attempts. Exiting.")

    def loadRooms(self):
        try:
            with open(UAL_JSON_PATH, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: File not found")
            return {}
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
            return {}

    def getRandomNonEmptyRoomIndex(self):
        rooms = self.loadRooms()
        valid_indexes = {0, 2, 3}  # Only these room indexes have computers

        # Filter rooms that are non-empty AND have valid computer indexes
        nonEmptyComputerRooms = [(index, room) for index, (room, users) in enumerate(rooms.items())
                                 if len(users) > 0 and index in valid_indexes]

        if not nonEmptyComputerRooms:
            return 1  # Indicating all users are in Room B

        chosenIndex, chosenRoom = random.choice(nonEmptyComputerRooms)
        return chosenIndex

    def automatorSimulation(self):
        roomNumber = self.getRandomNonEmptyRoomIndex() # RANDOM ROOM NUMBER BY INDEX
        # roomNumber = 0 # DEBUGGER
        print(roomNumber)
        self.writeComputerIDToFile(roomNumber)

        if roomNumber == 0:
            roomAUserRoles = self.getRoomAUserRoles() # GETS THE USER ROLES INSIDE ROOM A
            authorization = self.getAuthorizationStatus() #GET RANDOM AUTHORIZATION (AUTH OR UNAUTH)

            # Check if there are AS, Managers, and Directors
            hasAdministrativeStaff = any(key.startswith('AS') for key in roomAUserRoles)
            hasManager = any(key.startswith('M') for key in roomAUserRoles)
            hasDirector = any(key.startswith('D') for key in roomAUserRoles)

            # AUTHORIZATION WILL BE AUTH BY DEFAULT IN THESE CASES
            if hasDirector and not hasAdministrativeStaff and not hasManager:  # Director only
                authorization = "Authorized"
            if hasAdministrativeStaff and hasManager and hasDirector:  # All
                authorization = "Authorized"
            if hasManager and hasDirector and not hasAdministrativeStaff:  # Manager and Director
                authorization = "Authorized"

            # authorization = "Authorized" # DEBUGGER

            # GET THE ROLE AUTHORIZATION CONTEXT BASED ON USER ROLES IN ROOM A AND AUTH
            # authorization = auth:
            #   Administrative Staff, Manager, Director, Administrative Staff M-Req, Administrative Staff D-Req, Manager D-Req
            # authorization = unauth:
            #   Administrative Staff WO M-Req, Administrative Staff WO D-Req, Manager WO D-Req
            roles = self.checkRoles(roomAUserRoles, authorization)
            # GET A VALID RANDOM USER INDEX FROM THE USERS INSIDE ROOM A BASED ON USERS AND THEIR ROLES
            # roles = "Director"  # DEBUGGER
            user = random.choice(self.getUserRoomIndices(roomAUserRoles, roles))

            print(f"User Room Indices: {self.getUserRoomIndices(roomAUserRoles, roles)}")
            print(f"Room A User Roles: {roomAUserRoles}")
            print(f"Authorization Status: {authorization}")
            print(f"Roles to Check: {roles}")
            print(f"Selected User Index: {user}")

            # AUTH CASE
            if authorization == "Authorized":
                 # IF AUTH CONTEXT IS (AS ONLY, AS WITH MANAGER, AS WITH DIRECTOR, OR AS WITH MANAGER AND DIRECTOR)
                 if roles == "Administrative Staff" or roles == "Administrative Staff M-Req" or roles == "Administrative Staff D-Req":
                     length = len(self.roleFunctions[authorization][roles])
                     # print(f"Length of function array list: {length}")
                     randomIndex = random.randint(0, length - 1)
                     print(f"Random Function Index: {randomIndex}\n")
                     # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT
                     self.roleFunctions[authorization][roles][randomIndex](user) # DEBUGGER
                 elif roles == "Manager":
                     length = len(self.roleFunctions[authorization][roles])
                     randomIndex = random.randint(0, length - 1)
                     print(f"Random Function Index: {randomIndex}\n")
                     if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT
                        self.roleFunctions[authorization][roles][randomIndex](user)
                     else:
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
                 elif roles == "Director":
                     length = len(self.roleFunctions[authorization][roles])
                     randomIndex = random.randint(0, length - 1)
                     print(f"Random Function Index: {randomIndex}\n")
                     # # DEBUGGER
                     #
                     # try:
                     #     with open(r"C:\Shared\n.text", "r") as file:
                     #         indexValue = file.read().strip()
                     #         if indexValue.isdigit():
                     #             fixedIndex = int(indexValue)
                     #         else:
                     #             fixedIndex = 0
                     # except FileNotFoundError:
                     #     fixedIndex = 0
                     #
                     # try:
                     #     with open(r"C:\Shared\user.txt", "r") as file:
                     #         userN = file.read().strip()
                     # except FileNotFoundError:
                     #     userN = "Lol"  # Default value if the file doesn't exist
                     #
                     # self.roleFunctions[authorization][roles][fixedIndex](4)

                     if randomIndex != 8 and randomIndex != 9 and randomIndex != 12 and randomIndex != 13:
                        # RANDOM FUNCTION THAT CAN BE DONE BY DIRECTOR BASED ON THE ROLE AUTHORIZATION CONTEXT
                        self.roleFunctions[authorization][roles][randomIndex](user)
                     else:
                        randomUser = random.randint(0, 1)
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        if randomUser == 0:
                            randomAS = self.getRandomUsernameByAS()
                            self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
                        else:
                            randomManager = self.getRandomUsernameByManager()
                            self.roleFunctions[authorization][roles][randomIndex](user, randomManager)
                 elif roles == "Manager D-Req":
                     length = len(self.roleFunctions[authorization][roles])
                     randomIndex = random.randint(0, length - 1)
                     print(f"Random Function Index: {randomIndex}\n")
                     if randomIndex != 5 and randomIndex != 6:
                         # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT
                         self.roleFunctions[authorization][roles][randomIndex](user)
                     else:
                         # self.simulateMoveNonConfidentialFileToOthers,
                         # self.simulateMoveConfidentialFileToOthers,
                         randomAS = self.getRandomUsernameByAS()
                         self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
            elif authorization == "Unauthorized":
                if roles == "Administrative Staff WO M-Req" or roles == "Administrative Staff WO D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT
                    self.roleFunctions[authorization][roles][randomIndex](user) # DEBUGGER
                elif roles == "Manager WO D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)

        elif roomNumber == 2:
            roomCUserRoles = self.getRoomCUserRoles()
            authorization = self.getAuthorizationStatus()

            hasAdministrativeStaff = any(key.startswith('AS') for key in roomCUserRoles)
            hasManager = any(key.startswith('M') for key in roomCUserRoles)
            hasDirector = any(key.startswith('D') for key in roomCUserRoles)

            if hasDirector and not hasAdministrativeStaff and not hasManager:  # Director only
                authorization = "Authorized"
            if hasAdministrativeStaff and hasManager and hasDirector:  # All
                authorization = "Authorized"
            if hasManager and hasDirector and not hasAdministrativeStaff:  # Manager and Director
                authorization = "Authorized"

            roles = self.checkRoles(roomCUserRoles, authorization)
            user = random.choice(self.getUserRoomIndices(roomCUserRoles, roles))

            print(f"User Room Indices: {self.getUserRoomIndices(roomCUserRoles, roles)}")
            print(f"Room C User Roles: {roomCUserRoles}")
            print(f"Authorization Status: {authorization}")
            print(f"Roles to Check: {roles}")
            print(f"Selected User Index: {user}")

            if authorization == "Authorized":
                if roles == "Administrative Staff" or roles == "Administrative Staff M-Req" or roles == "Administrative Staff D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    self.roleFunctions[authorization][roles][randomIndex](user)
                elif roles == "Manager":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
                elif roles == "Director":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 8 and randomIndex != 9 and randomIndex != 12 and randomIndex != 13:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomUser = random.randint(0, 1)
                        if randomUser == 0:
                            randomAS = self.getRandomUsernameByAS()
                            self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
                        else:
                            randomManager = self.getRandomUsernameByManager()
                            self.roleFunctions[authorization][roles][randomIndex](user, randomManager)
                elif roles == "Manager D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
            elif authorization == "Unauthorized":
                if roles == "Administrative Staff WO M-Req" or roles == "Administrative Staff WO D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    self.roleFunctions[authorization][roles][randomIndex](user)
                elif roles == "Manager WO D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)

        elif roomNumber == 3:
            roomDUserRoles = self.getRoomDUserRoles()
            authorization = self.getAuthorizationStatus()

            hasAdministrativeStaff = any(key.startswith('AS') for key in roomDUserRoles)
            hasManager = any(key.startswith('M') for key in roomDUserRoles)
            hasDirector = any(key.startswith('D') for key in roomDUserRoles)

            if hasDirector and not hasAdministrativeStaff and not hasManager:  # Director only
                authorization = "Authorized"
            if hasAdministrativeStaff and hasManager and hasDirector:  # All
                authorization = "Authorized"
            if hasManager and hasDirector and not hasAdministrativeStaff:  # Manager and Director
                authorization = "Authorized"

            roles = self.checkRoles(roomDUserRoles, authorization)
            user = random.choice(self.getUserRoomIndices(roomDUserRoles, roles))

            print(f"User Room Indices: {self.getUserRoomIndices(roomDUserRoles, roles)}")
            print(f"Room D User Roles: {roomDUserRoles}")
            print(f"Authorization Status: {authorization}")
            print(f"Roles to Check: {roles}")
            print(f"Selected User Index: {user}")

            if authorization == "Authorized":
                if roles == "Administrative Staff" or roles == "Administrative Staff M-Req" or roles == "Administrative Staff D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    self.roleFunctions[authorization][roles][randomIndex](user)
                elif roles == "Manager":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
                elif roles == "Director":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 8 and randomIndex != 9 and randomIndex != 12 and randomIndex != 13:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomUser = random.randint(0, 1)
                        if randomUser == 0:
                            randomAS = self.getRandomUsernameByAS()
                            self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
                        else:
                            randomManager = self.getRandomUsernameByManager()
                            self.roleFunctions[authorization][roles][randomIndex](user, randomManager)
                elif roles == "Manager D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)
            elif authorization == "Unauthorized":
                if roles == "Administrative Staff WO M-Req" or roles == "Administrative Staff WO D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    self.roleFunctions[authorization][roles][randomIndex](user)
                elif roles == "Manager WO D-Req":
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.randint(0, length - 1)
                    print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        self.roleFunctions[authorization][roles][randomIndex](user)
                    else:
                        randomAS = self.getRandomUsernameByAS()
                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS)

at = UserFileAccessAttemptAutomator()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createManager()
at.createManager()
at.createDirector()
at.createDirector()

while True:
    time.sleep(1)


# print(at.getRandomUsernameByManager())
# print(at.getRandomNonEmptyRoomIndex())
# at.writeComputerIDToFile(0)

# at.simulateOpenNonConfidentialFile(0)

# at.automatorSimulation()


# at.checkRoles(at.getRoomAUserRoles())
# print(at.getUserRoomIndices(at.getRoomAUserRoles()))
# print(at.getRandomRoleFromStatus(at.getAuthorizationStatus()))

# at.roleFunctions["Authorized"]["Administrative Staff"][1](0)
# while True:
#     at.checkFlag()
#     time.sleep(1)


# at.simulateMoveConfidentialFileToOthers(0, "AS2")
# print(at.getRoomAUsers())  # Expected Output: ["AS1", "AS2"]
# print(at.getRoomBUsers())  # Expected Output: ["M1"]
# print(at.getRoomCUsers())  # Expected Output: ["D1"]
# print(at.getRoomDUsers())  # Expected Output: ["D2", "M2"]
#

# print(at.getRoomAUserRoles())  # Expected Output: {"AS1": "Administrative Staff", "AS2": "Administrative Staff"}
# print(at.getRoomBUserRoles())  # Expected Output: {"M1": "Manager"}
# print(at.getRoomCUserRoles())  # Expected Output: {"D1": "Director"}
# print(at.getRoomDUserRoles())  # Expected Output: {"D2": "Director", "M2": "Manager"}

# at.simulateOpenNonConfidentialFile(0)
# print(at.getRandomUsernameByAS())
# at.simulateCopyRandomFileInternal(0)
# at.automateFileAccess()
# print(at.getRandomUserIndex())

# for user in at.userList:
#      print(f"User: {user.username}, Role: {user.role}, Access: {user.directoryAccessList}")

# at.simulateMoveFileInternal(0)
# at.simulateMoveFileInternalToMain(0)
# #
# # # time.sleep(4)
# at.getUser(0).printStats()

# print(at.getRandomFileFromDirectory(f"C:\\Shared\\janva\\AS1"))


# at.getUser(1).deleteFile(r"C:\Users\janva\Downloads\TF1\asdasd_CONFIDENTIAL.docx")
# at.getUser(1).printStats()

# simulateOpen(r"C:\Users\janva\Downloads\TF1\a.docx")
# deleteFile(r"C:\Users\janva\Downloads\TF1\a.docx")
# moveFile(r"C:\Users\janva\Downloads\TF1\a.docx", r"C:\Users\janva\Downloads\TF2")
# copyFile(r"C:\Users\janva\Downloads\TF1\a.docx", r"C:\Users\janva\Downloads\TF2")
