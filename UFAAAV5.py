import json, random, time, threading
from threading import Lock
from datetime import datetime, timedelta
from filelock import FileLock

file_lock = threading.Lock()
CURRENT_USER_FILE_PATH = r"C:\Shared\loggedUser.json"
COMPUTER_ID_FILE_PATH = r"C:\Shared\computerID.json"
RAW_LOG_FILE_PATH = r'C:\Shared\logs.json'
LOG_FILE_PATH = r"C:\Shared\logging.json"
USER_STATUS_TRACKER_FILE_PATH = r"C:\Shared\breakTracker.json"

SNAP_UAL_FILE_PATH = r"C:\Shared\snapUal.json"
UAL_JSON_PATH = r"C:\Users\janva\Downloads\ual.json"

ASORManager_Weights = [0.67, 0.33]

# randomIndex = random.choices(range(length), weights=Director_Weights_Authorized, k=1)[0]

class User:
    def __init__(self, username, role):
        self.username = username
        self.role = role
        self.shiftRanges = {
            "AS1": ("07:00", "14:00"),
            "AS2": ("07:00", "14:00"),
            "AS3": ("07:00", "14:00"),
            "AS4": ("07:00", "14:00"),
            "Manager1": ("07:00", "14:00"),
            "AS5": ("14:00", "21:00"),
            "AS6": ("14:00", "21:00"),
            "AS7": ("14:00", "21:00"),
            "AS8": ("14:00", "21:00"),
            "Manager2": ("14:00", "21:00"),
            "Director1": ("07:00", "21:00")
        }
        self.breakRangesMap = {
            "AS1": [("10:00", "11:00")],
            "AS2": [("10:00", "11:00")],
            "AS3": [("11:00", "12:00")],
            "AS4": [("11:00", "12:00")],
            "Manager1": [("11:00", "12:00")],
            "AS5": [("17:00", "18:00")],
            "AS6": [("17:00", "18:00")],
            "AS7": [("18:00", "19:00")],
            "AS8": [("18:00", "19:00")],
            "Manager2": [("18:00", "19:00")],
            "Director1": [("10:00", "11:00"), ("17:00", "18:00")]
        }
        self.transferTypeMove = [
            "nMoveNonCFToAS", "nMoveNonCFToManagers", "nMoveNonCFToDirectors",
            "nMoveCFToAS", "nMoveCFToManagers", "nMoveCFToDirectors"
        ]
        self.transferTypeCopy = [
            "nCopyNonCFToAS", "nCopyNonCFToManagers", "nCopyNonCFToDirectors",
            "nCopyCFToAS", "nCopyCFToManagers", "nCopyCFToDirectors"
        ]

        self.nMoveNonCFToOthers = "nMoveNonCFToOthers"
        self.nMoveCFToOthers = "nMoveCFToOthers"
        self.nCopyNonCFToOthers = "nCopyNonCFToOthers"
        self.nCopyCFToOthers = "nCopyCFToOthers"
        self.nonCF = "NonCF"

    def getRole(self):
        return self.role

    def getUsername(self):
        return self.username

    def updateFileAccess(self, username, role, actionType, count, authorization):
        try:
            with open(LOG_FILE_PATH, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Could not load JSON file.")
            return

        if username in data[role]:
            data[role][username][actionType + authorization] += count
            data[role][username]["TotalAttempts" + authorization] += count
            data[role][username]["TotalAttempts"] += count

        if "Total" in data[role] and username in data[role]["Total"]:
            data[role]["Total"][username + authorization] += count
            data[role]["Total"][username] += count

        data["Overall"][role]["Total Attempts" + authorization] += count
        data["Overall"][role]["Total Attempts"] += count
        data["Overall"]["Total Attempts" + authorization] += count
        data["Overall"]["Total Attempts"] += count

        with open(LOG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)

    def updateFileTransfer(self, username, role, actionType, transferType, count, authorization):
        try:
            with open(LOG_FILE_PATH, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Could not load JSON file.")
            return

        if username in data[role]:
            data[role][username][actionType + authorization] += count
            data[role][username][transferType + authorization] += count
            data[role][username]["TotalAttempts" + authorization] += count
            data[role][username]["TotalAttempts"] += count

            if transferType in self.transferTypeMove:
                toOthersKey = self.nMoveNonCFToOthers if self.nonCF in transferType else self.nMoveCFToOthers
                data[role][username][toOthersKey + authorization] += count

            if transferType in self.transferTypeCopy:
                toOthersKey = self.nCopyNonCFToOthers if self.nonCF in transferType else self.nCopyCFToOthers
                data[role][username][toOthersKey + authorization] += count

        if "Total" in data[role] and username in data[role]["Total"]:
            data[role]["Total"][username + authorization] += count
            data[role]["Total"][username] += count

        data["Overall"][role]["Total Attempts" + authorization] += count
        data["Overall"][role]["Total Attempts"] += count
        data["Overall"]["Total Attempts" + authorization] += count
        data["Overall"]["Total Attempts"] += count

        with open(LOG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)

    def getComputerID(self):
        try:
            with open(COMPUTER_ID_FILE_PATH, "r") as file:
                data = json.load(file)
                return data.get("ComputerID")
        except Exception as e:
            return None

    def appendLogToFile(self, logData):
        try:
            with open(RAW_LOG_FILE_PATH, "r") as file:
                data = json.load(file)
            data.append(logData)
            with open(RAW_LOG_FILE_PATH, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            return None

    def getTime(self):
        accessTime = time.time()
        return accessTime

    def formatEventAsJSON(self, eventType, fileDestDir, timestamp, username, breakStatus):
        eventData = {
            "Timestamp": timestamp,
            "Username": username,
            "ComputerID": self.getComputerID(),
            "fileAccessType": eventType,
            "fileDestinationDirectory": fileDestDir,
            "breakStatus": breakStatus
        }
        return eventData

    def simulateOpen(self, directory, authorization, simulatedTimestamp, breakStatus):
        formattedTimestamp = simulatedTimestamp.strftime("%Y-%m-%d %H:%M:%S")
        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenNonCF', 1, authorization)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenCF', 1, authorization)
        JSONOutput = self.formatEventAsJSON("File Opening", directory, formattedTimestamp, self.getUsername(), breakStatus)
        self.appendLogToFile(JSONOutput)

    def simulateModify(self, directory, authorization, simulatedTimestamp):
        formattedTimestamp = simulatedTimestamp.strftime("%Y-%m-%d %H:%M:%S")
        randomGapTime = random.randint(5, 10)
        fileOpenTimeStamp = simulatedTime - timedelta(seconds=randomGapTime)
        formattedFileOpenTimeStamp = fileOpenTimeStamp.strftime("%Y-%m-%d %H:%M:%S")

        fileModifyBreakStatus = self.isOnBreak2(simulatedTimestamp, self.getUsername())
        fileOpenBreakStatus = self.isOnBreak2(fileOpenTimeStamp, self.getUsername())
        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenNonCF', 1, authorization)
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nModifyNonCF', 1, authorization)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nOpenCF', 1, authorization)
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nModifyCF', 1, authorization)

        JSONOutput1 = self.formatEventAsJSON("File Opening", directory, formattedFileOpenTimeStamp, self.getUsername(), fileOpenBreakStatus)
        JSONOutput2 = self.formatEventAsJSON("File Modification", directory, formattedTimestamp, self.getUsername(), fileModifyBreakStatus)
        self.appendLogToFile(JSONOutput1)
        self.appendLogToFile(JSONOutput2)

    def deleteFile(self, directory, authorization, simulatedTimestamp, breakStatus):
        formattedTimestamp = simulatedTimestamp.strftime("%Y-%m-%d %H:%M:%S")
        if 'NON' in directory:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nDeleteNonCF', 1, authorization)
        else:
            self.updateFileAccess(self.getUsername(), self.getRole(), 'nDeleteCF', 1, authorization)
        JSONOutput = self.formatEventAsJSON("File Deletion", directory, formattedTimestamp, self.getUsername(), breakStatus)
        self.appendLogToFile(JSONOutput)

    def moveFiles(self, sourceDirectory, destinationDirectory, transferType, authorization, simulatedTimestamp, breakStatus):
        formattedTimestamp = simulatedTimestamp.strftime("%Y-%m-%d %H:%M:%S")
        if 'NON' in sourceDirectory:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nMoveNonCF', transferType, 1, authorization)
        else:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nMoveCF', transferType, 1, authorization)
        JSONOutput = self.formatEventAsJSON("File Move", destinationDirectory, formattedTimestamp, self.getUsername(), breakStatus)
        self.appendLogToFile(JSONOutput)

    def copyFiles(self, sourceDirectory, destinationDirectory, transferType, authorization, simulatedTimestamp, breakStatus):
        formattedTimestamp = simulatedTimestamp.strftime("%Y-%m-%d %H:%M:%S")
        if 'NON' in sourceDirectory:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nCopyNonCF', transferType, 1, authorization)
        else:
            self.updateFileTransfer(self.getUsername(), self.getRole(), 'nCopyCF', transferType, 1, authorization)
        JSONOutput = self.formatEventAsJSON("File Copy", destinationDirectory, formattedTimestamp, self.getUsername(), breakStatus)
        self.appendLogToFile(JSONOutput)

    def isOnBreak2(self, currentTime, role):
        shiftStart, shiftEnd = self.shiftRanges[role]
        shiftStartTime = datetime.strptime(shiftStart, "%H:%M").time()
        shiftEndTime = datetime.strptime(shiftEnd, "%H:%M").time()
        currentT = currentTime.time()

        if not (shiftStartTime <= currentT < shiftEndTime):
            return 2  # Outside shift

        for startStr, endStr in self.breakRangesMap[role]:
            start = datetime.strptime(startStr, "%H:%M").time()
            end = datetime.strptime(endStr, "%H:%M").time()
            if start <= currentT < end:
                return 1  # On break

        return 0  # In shift but not on break


class  UserFileAccessAttemptAutomator:
    def __init__(self):
        self.userList = []
        self.roleFunctions = {
            "Authorized": {
                "Administrative Staff": [  # Administrative Staff-only Action
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
                "Administrative Staff M-Req": [  # Administrative Staff + Manager-only Action
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
                "Administrative Staff D-Req": [  # Administrative Staff + Director-only Action
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
                "Manager": [  # Manager-only Action
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
                "Manager D-Req": [  # Manager + Director-only Action
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
                "Director": [  # Director-only Action
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
            "Unauthorized": {  # Administrative Staff-only Action without Manager & Director
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
                "Administrative Staff WO D-Req": [  # Administrative Staff-only Action without Director
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
                "Manager WO D-Req": [  # Manager-only Action without Director
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
        self.userStatusList = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.validIndexes = {0, 2, 3}  # Only these room indexes have computers
        self.indexToRole = {
            0: "AS1",
            1: "AS2",
            2: "AS3",
            3: "AS4",
            4: "AS5",
            5: "AS6",
            6: "AS7",
            7: "AS8",
            8: "Manager1",
            9: "Manager2",
            10: "Director1"
        }

        self.RoomAUsualUsersByIndex = [0, 1, 4, 5]
        self.RoomCUsualUsersByIndex = [2, 3, 6, 7]
        self.AllUsersByIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.RoomAandRoomC = ["Room A", "Room C"]

        self.RoomA = "Room A"
        self.RoomC = "Room C"
        self.RoomD = "Room D"
        self.ComputerA2 = "Computer A2"
        self.ComputerC2 = "Computer C2"
        self.ComputerD = "Computer D"

        self.roomMap = {0: "Room A", 2: "Room C", 3: "Room D"}
        self.defaultChoices = {
            "Room A": ["Computer A0", "Computer A1", "Computer A2"],
            "Room C": ["Computer C0", "Computer C1", "Computer C2"],
            "Room D": ["Computer D"]
        }
        self.shiftRanges = {
            "AS1": ("07:00", "14:00"),
            "AS2": ("07:00", "14:00"),
            "AS3": ("07:00", "14:00"),
            "AS4": ("07:00", "14:00"),
            "Manager1": ("07:00", "14:00"),
            "AS5": ("14:00", "21:00"),
            "AS6": ("14:00", "21:00"),
            "AS7": ("14:00", "21:00"),
            "AS8": ("14:00", "21:00"),
            "Manager2": ("14:00", "21:00"),
            "Director1": ("07:00", "21:00")
        }
        self.roleToIndex = {
            "AS1": 0,
            "AS2": 1,
            "AS3": 2,
            "AS4": 3,
            "AS5": 4,
            "AS6": 5,
            "AS7": 6,
            "AS8": 7,
            "Manager1": 8,
            "Manager2": 9,
            "Director1": 10
        }

        self.RoomAUsualUsersByIndex = [0, 1, 4, 5]
        self.RoomCUsualUsersByIndex = [2, 3, 6, 7]
        self.AllUsersByIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        self.AS_Weights_Authorized = [0.50, 0.35, 0.15]
        self.AS_MReqWeights_Authorized = [0.40, 0.20, 0.20, 0.10, 0.10]
        self.AS_DReqWeights_Authorized = [0.20, 0.14, 0.07, 0.05, 0.12, 0.07, 0.06, 0.12, 0.05, 0.07, 0.05]
        self.Manager_Weights_Authorized = [0.20, 0.15, 0.15, 0.15, 0.10, 0.08, 0.04, 0.08, 0.05]
        self.Director_Weights_Authorized = [0.10, 0.08, 0.10, 0.08, 0.06, 0.05, 0.08, 0.06, 0.04, 0.03, 0.07, 0.05,
                                            0.03, 0.02, 0.03,
                                            0.02, 0.03, 0.02]
        self.Manager_DReqWeights_Authorized = [0.22, 0.05, 0.05, 0.12, 0.12, 0.15, 0.15, 0.07, 0.07]
        self.ASORManager_Weights = [0.67, 0.33]
        self.AS_WOMReqWeights_Unauthorized = [0.25, 0.20, 0.15, 0.20, 0.20]
        self.AS_WODReqWeights_Unauthorized = [0.15, 0.10, 0.05, 0.05, 0.083, 0.083, 0.084, 0.10, 0.10, 0.10, 0.10]
        self.Manager_WODReqWeights_Unauthorized = [0.20, 0.05, 0.05, 0.15, 0.15, 0.05, 0.05, 0.15, 0.15]

        self.nonEmptyRoomsProbabilities3 = [1 / 3, 1 / 3, 1 / 3]
        self.nonEmptyRoomsProbabilities2 = [0.5, 0.5]
        self.nonEmptyRoomsProbabilities1 = [1.0]

        self.AS = "Administrative Staff"
        self.Manager = "Manager"
        self.Director = "Director"
        self.ASManagerASMReq = ["Administrative Staff", "Manager", "Administrative Staff M-Req"]
        self.ASDirectorASDReq = ["Administrative Staff", "Director", "Administrative Staff D-Req"]
        self.ManagerDirectorManagerDReq = ["Manager", "Director", "Manager D-Req"]
        self.AllRoles = ["Administrative Staff", "Manager", "Director", "Administrative Staff M-Req",
                         "Administrative Staff D-Req", "Manager D-Req"]
        self.ASWOMReqAndDReq = ["Administrative Staff WO M-Req", "Administrative Staff WO D-Req"]
        self.ManagerWODReq = "Manager WO D-Req"
        self.ASWODReq = "Administrative Staff WO D-Req"

        self.ASRolesAuthorized = ["Administrative Staff", "Administrative Staff M-Req", "Administrative Staff D-Req"]
        self.ManagerRoleAuthorized = "Manager"
        self.DirectorRoleAuthorized = "Director"
        self.ManagerDReqRoleAuthorized = "Manager D-Req"

        self.ASRolesUnauthorized = ["Administrative Staff WO M-Req", "Administrative Staff WO D-Req"]
        self.ManagerRoleUnauthorized = "Manager WO D-Req"

        self.AS_Weights_Authorized_Actions = [
            "opened a non-confidential file",
            "opened a non-confidential file with modify",
            "copied a non-confidential file to internal storage"
        ]

        self.AS_MReqWeights_Authorized_Actions = [
            "opened a confidential file with permission from Manager",
            "moved a non-confidential file to internal storage with permission from Manager",
            "copied a confidential file to internal storage with permission from Manager",
            "copied a non-confidential file to external storage with permission from Manager",
            "copied a confidential file to external storage with permission from Manager"
        ]

        self.AS_DReqWeights_Authorized_Actions = [
            "opened a confidential file with permission from Director",
            "modified a confidential file with permission from Director",
            "deleted a non-confidential file with permission from Director",
            "deleted a confidential file with permission from Director",
            "moved a non-confidential file to internal storage with permission from Director",
            "copied a confidential file to internal storage with permission from Director",
            "moved a confidential file to internal storage with permission from Director",
            "copied a non-confidential file to external storage with permission from Director",
            "copied a confidential file to external storage with permission from Director",
            "moved a non-confidential file to external storage with permission from Director",
            "moved a confidential file to external storage with permission from Director"
        ]

        self.Manager_Weights_Authorized_Actions = [
            "opened a non-confidential file",
            "opened a confidential file",
            "modified a non-confidential file",
            "copied a non-confidential file to internal storage",
            "copied a confidential file to internal storage",
            "copied a non-confidential file to ",
            "copied a confidential file to ",
            "copied a non-confidential file to external storage",
            "copied a confidential file to external storage"
        ]

        self.Director_Weights_Authorized_Actions = [
            "opened a non-confidential file",
            "opened a confidential file",
            "modified a non-confidential file",
            "modified a confidential file",
            "deleted a non-confidential file",
            "deleted a confidential file",
            "moved a non-confidential file to internal storage",
            "moved a confidential file to internal storage",
            "moved a non-confidential file to ",
            "moved a confidential file to ",
            "copied a non-confidential file to internal storage",
            "copied a confidential file to internal storage",
            "copied a non-confidential file to ",
            "copied a confidential file to ",
            "moved a non-confidential file to external storage",
            "moved a confidential file to external storage",
            "copied a non-confidential file to external storage",
            "copied a confidential file to external storage"
        ]

        self.Manager_DReqWeights_Authorized_Actions = [
            "modified a confidential file with permission from Director",
            "deleted a non-confidential file with permission from Director",
            "deleted a confidential file with permission from Director",
            "moved a non-confidential file to internal storage with permission from Director",
            "moved a confidential file to internal storage with permission from Director",
            "moved a non-confidential file with permission from Director to ",
            "moved a confidential file with permission from Director to ",
            "moved a non-confidential file to external storage with permission from Director",
            "moved a confidential file to external storage with permission from Director"
        ]

        self.AS_WOMReqWeights_Unauthorized_Actions = [
            "opened a confidential file without permission from Manager",
            "moved a non-confidential file to internal storage without permission from Manager",
            "copied a confidential file to internal storage without permission from Manager",
            "copied a non-confidential file to external storage without permission from Manager",
            "copied a confidential file to external storage without permission from Manager"
        ]

        self.AS_WODReqWeights_Unauthorized_Actions = [
            "opened a confidential file without permission from Director",
            "modified a confidential file without permission from Director",
            "deleted a non-confidential file without permission from Director",
            "deleted a confidential file without permission from Director",
            "moved a non-confidential file to internal storage without permission from Director",
            "copied a confidential file to internal storage without permission from Director",
            "moved a confidential file to internal storage without permission from Director",
            "copied a non-confidential file to external storage without permission from Director",
            "copied a confidential file to external storage without permission from Director",
            "moved a non-confidential file to external storage without permission from Director",
            "moved a confidential file to external storage without permission from Director"
        ]

        self.Manager_WODReqWeights_Unauthorized_Actions = [
            "modified a confidential file without permission from Director",
            "deleted a non-confidential file without permission from Director",
            "deleted a confidential file without permission from Director",
            "moved a confidential file to internal storage without permission from Director",
            "moved a non-confidential file to internal storage without permission from Director",
            "moved a non-confidential file without permission from Director to ",
            "moved a confidential file without permission from Director to ",
            "moved a non-confidential file to external storage without permission from Director",
            "moved a confidential file to external storage without permission from Director"
        ]

        self.nTotalAdministrativeStaff = 0
        self.nTotalManagers = 0
        self.nTotalDirectors = 0
        self.userList = []
        self.computerIDLock = Lock()

    def createAdministrativeStaff(self):
        self.nTotalAdministrativeStaff += 1
        ASUsername = f"AS{self.nTotalAdministrativeStaff}"
        user = User(ASUsername, "Administrative Staff")
        self.userList.append(user)

    def createManager(self):
        self.nTotalManagers += 1
        ManagerUsername = f"Manager{self.nTotalManagers}"
        user = User(ManagerUsername, "Manager")
        self.userList.append(user)

    def createDirector(self):
        self.nTotalDirectors += 1
        DirectorUsername = f"Director{self.nTotalDirectors}"
        user = User(DirectorUsername, "Director")
        self.userList.append(user)

    def writeLoggedInUserToFile(self, username):
        try:
            with open(CURRENT_USER_FILE_PATH, "w") as file:
                json.dump({"username": username}, file)
        except Exception as e:
            print(f"Error writing to file: {e}")

    def getUser(self, index):
        return self.userList[index]

    # OPEN CONFIDENTIAL, NON-CONFIDENTIAL
    def simulateOpenNonConfidentialFile(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_OPEN_NON.docx"
        filePath = directory + "\\" + fileName
        user.simulateOpen(filePath, authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateOpenConfidentialFile(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_OPEN.docx"
        filePath = directory + "\\" + fileName
        user.simulateOpen(filePath, authorization, simulatedTimestamp, self.userStatusList[index])

    # MODIFY CONFIDENTIAL, NON-CONFIDENTIAL
    def simulateOpenNonConfidentialFileWithModify(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_OPENWMOD_NON.docx"
        filePath = directory + "\\" + fileName
        user.simulateModify(filePath, authorization, simulatedTimestamp)

    def simulateOpenConfidentialFileWithModify(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_OPENWMOD.docx"
        filePath = directory + "\\" + fileName
        user.simulateModify(filePath, authorization, simulatedTimestamp)

    # DELETE CONFIDENTIAL, NON-CONFIDENTIAL
    def simulateDeleteNonConfidentialFile(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_DELETE_NON.docx"
        filePath = directory + "\\" + fileName
        user.deleteFile(filePath, authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateDeleteConfidentialFile(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_DELETE.docx"
        filePath = directory + "\\" + fileName
        user.deleteFile(filePath, authorization, simulatedTimestamp, self.userStatusList[index])

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL TO INTERNAL
    def simulateMoveNonConfidentialFileInternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_MOVE_NON_INTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder\\{fileName}",
                       "nMoveNonCFMainToInternal", authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateMoveConfidentialFileInternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_MOVE_INTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder\\{fileName}",
                       "nMoveCFMainToInternal", authorization, simulatedTimestamp, self.userStatusList[index])

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL TO EXTERNAL
    def simulateMoveNonConfidentialFileExternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_MOVE_NON_EXTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_ExternalDrive\\{fileName}",
                       "nMoveNonCFToExternal", authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateMoveConfidentialFileExternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_MOVE_EXTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_ExternalDrive\\{fileName}",
                       "nMoveCFToExternal", authorization, simulatedTimestamp, self.userStatusList[index])

    # MOVE CONFIDENTIAL, NON-CONFIDENTIAL TO OTHERS
    def simulateMoveNonConfidentialFileToOthers(self, index, permissionUsername, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_MOVE_NON_OTHERS.docx"
        filePath = directory + "\\" + fileName

        permissionRole = self.getUserRole(permissionUsername)

        if permissionRole == "Administrative Staff":
            transferType = "nMoveNonCFToAS"
        elif permissionRole == "Manager":
            transferType = "nMoveNonCFToManagers"
        elif permissionRole == "Director":
            transferType = "nMoveNonCFToDirectors"

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}\\{fileName}", transferType,
                       authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateMoveConfidentialFileToOthers(self, index, permissionUsername, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_MOVE_OTHERS.docx"
        filePath = directory + "\\" + fileName

        permissionRole = self.getUserRole(permissionUsername)

        if permissionRole == "Administrative Staff":
            transferType = "nMoveCFToAS"
        elif permissionRole == "Manager":
            transferType = "nMoveCFToManagers"
        elif permissionRole == "Director":
            transferType = "nMoveCFToDirectors"

        user.moveFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}\\{fileName}", transferType,
                       authorization, simulatedTimestamp, self.userStatusList[index])

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL TO INTERNAL  (MIGHT NEED COPY-ONLY PURPOSE FILES)
    def simulateCopyNonConfidentialFileInternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_COPY_NON_INTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder\\{fileName}",
                       "nCopyNonCFMainToInternal", authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateCopyConfidentialFileInternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_COPY_INTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_InternalFolder\\{fileName}",
                       "nCopyCFMainToInternal", authorization, simulatedTimestamp, self.userStatusList[index])

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL TO EXTERNAL  (MIGHT NEED COPY-ONLY PURPOSE FILES)
    def simulateCopyNonConfidentialFileExternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_COPY_NON_EXTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_ExternalDrive\\{fileName}",
                       "nCopyNonCFToExternal", authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateCopyConfidentialFileExternal(self, index, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_COPY_EXTERNAL.docx"
        filePath = directory + "\\" + fileName
        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{username}_ExternalDrive\\{fileName}",
                       "nCopyCFToExternal", authorization, simulatedTimestamp, self.userStatusList[index])

    # COPY CONFIDENTIAL, NON-CONFIDENTIAL TO OTHERS
    def simulateCopyNonConfidentialFileToOthers(self, index, permissionUsername, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_COPY_NON_OTHERS.docx"
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

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}\\{fileName}", transferType,
                       authorization, simulatedTimestamp, self.userStatusList[index])

    def simulateCopyConfidentialFileToOthers(self, index, permissionUsername, authorization, simulatedTimestamp):
        user: User = self.getUser(index)
        username = user.getUsername()
        directory = f"C:\\Users\\janva\\Downloads\\{username}"
        fileName = username + "_COPY_OTHERS.docx"
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

        user.copyFiles(filePath, f"C:\\Users\\janva\\Downloads\\{permissionUsername}\\{fileName}", transferType,
                       authorization, simulatedTimestamp, self.userStatusList[index])

    def getRandomUsernameByAS(self):
        ASUsers = [user.username for user in self.userList if user.role == "Administrative Staff"]
        return random.choice(ASUsers) if ASUsers else None

    def getRandomUsernameByManager(self):
        managerUsers = [user.username for user in self.userList if user.role == "Manager"]
        return random.choice(managerUsers) if managerUsers else None

    def getUserRole(self, username):
        if username.startswith("AS"):
            return "Administrative Staff"
        elif username.startswith("Manager"):
            return "Manager"
        elif username.startswith("Director"):
            return "Director"

    def getUserRoles(self, room):
        users = self.getUsers(room)
        userRoles = {}

        for user in users:
            if user.startswith("AS"):
                userRoles[user] = "Administrative Staff"
            elif user.startswith("M"):
                userRoles[user] = "Manager"
            elif user.startswith("D"):
                userRoles[user] = "Director"

        return userRoles

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

    def getAuthorizationStatus(self, weights=(0.384, 0.616)):
        return random.choices(
            ["Authorized", "Unauthorized"],
            weights=weights,
            k=1
        )[0]

    def getUserRoomIndices(self, room, targetRole):
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
            if hasAdministrativeStaff and not hasManager and not hasDirector:  # Staff only
                return self.AS # "Administrative Staff"
            elif hasManager and not hasAdministrativeStaff and not hasDirector:  # Manager only
                return self.Manager # "Manager"
            elif hasDirector and not hasAdministrativeStaff and not hasManager:  # Director only
                return self.Director # "Director"
            elif hasAdministrativeStaff and hasManager and not hasDirector:  # Staff and Manager
                return random.choice(self.ASManagerASMReq) # ["Administrative Staff", "Manager", "Administrative Staff M-Req"]
            elif hasAdministrativeStaff and hasDirector and not hasManager:  # Staff and Director
                return random.choice(self.ASDirectorASDReq) # ["Administrative Staff", "Director", "Administrative Staff D-Req"]
            elif hasManager and hasDirector and not hasAdministrativeStaff:  # Manager and Director
                return random.choice(self.ManagerDirectorManagerDReq) # ["Manager", "Director", "Manager D-Req"]
            elif hasAdministrativeStaff and hasManager and hasDirector:
                return random.choice(self.AllRoles) # ["Administrative Staff", "Manager", "Director", "Administrative Staff M-Req", "Administrative Staff D-Req", "Manager D-Req"]
        elif authorization == "Unauthorized":
            if hasAdministrativeStaff and not hasManager and not hasDirector:  # Staff only
                return random.choice(self.ASWOMReqAndDReq) # ["Manager", "Director", "Manager D-Req"]
            elif hasManager and not hasAdministrativeStaff and not hasDirector:  # Manager only
                return self.ManagerWODReq # "Manager WO D-Req"
            elif hasAdministrativeStaff and hasManager and not hasDirector:  # Staff and Manager
                return self.ASWODReq # "Administrative Staff WO D-Req"

            # DOES NOT MAKE SENSE SINCE DIRECTOR CAN GIVE PERMISSION FOR ALL ACCESS ATTEMPTS
            # elif hasAdministrativeStaff and hasDirector and not hasManager: #Staff and Director
            # return "Administrative Staff WO M-Req"

    def loadRooms(self):
        try:
            with open(r"C:\Shared\snapUal.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: File not found")
            return {}
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
            return {}

    def getRandomNonEmptyRoomIndex(self):
        rooms = self.loadRooms()
        # print(f"All rooms: {rooms}")
        # print(rooms)

        # Filter rooms that are non-empty AND have valid computer indexes
        nonEmptyComputerRooms = [(index, room) for index, (room, users) in enumerate(rooms.items())
                                 if len(users) > 0 and index in self.validIndexes]

        # print(f"Nonempty rooms: {rooms}")

        # print(nonEmptyComputerRooms)

        if not nonEmptyComputerRooms:
            return 1

        length = len(nonEmptyComputerRooms)

        # print(length)
        if length == 3:
            weights = self.nonEmptyRoomsProbabilities3
        elif length == 2:
            weights = self.nonEmptyRoomsProbabilities2
        else:  # length == 1
            weights = self.nonEmptyRoomsProbabilities1

        chosenIndex, chosenRoom = random.choices(nonEmptyComputerRooms, weights=weights, k=1)[0]
        # print(f"Chosen Index: {chosenIndex}")
        return chosenIndex

    def writeComputerIDToFile2(self, roomNumber, userIndex):
        with self.computerIDLock:
            with open(r"C:\Shared\snapUal.json", "r") as file:
                roomAssignments = json.load(file)
        # PURPOSE OF ROOM NUMBER IS TO GET THE EXACT LOCATION WHERE THE USER IS LOCATED
        # print(f"\nRoom Assignments: {roomAssignments}")
        # role = self.indexToRole[userIndex]
        status = self.userStatusList[userIndex]

        currentRoom = self.roomMap[roomNumber]
        # print(currentRoom)
        # print(f"Current Room: {currentRoom}")
        rand = None

        possibleAlternatives = [
            room for room, users in roomAssignments.items()
            if users and room in self.defaultChoices and room != currentRoom
        ]

        # print(f"Possible Alts.: {possibleAlternatives}")
        # print(f"User index: {userIndex} Current Room: {currentRoom}")

        newRoomNumber = roomNumber
        if status == 0: # NOT ON BREAK
            if random.random() <= 0.05 and possibleAlternatives:
                alternativeRoom = random.choice(possibleAlternatives)
                computerID = random.choice(self.defaultChoices[alternativeRoom])
                newRoomNumber = next(k for k, v in self.roomMap.items() if v == alternativeRoom)
                # print(f"Mismatch CID: {computerID}")
            else:
                # self.RoomAUsualUsersByIndex = [0, 1, 4, 5]
                # self.RoomCUsualUsersByIndex = [2, 3, 6, 7]
                # self.AllUsersByIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                # self.RoomAandRoomC = ["Room A", "Room C"]
                #
                # self.RoomA = "Room A"
                # self.RoomC = "Room C"
                # self.RoomD = "Room D"
                # self.ComputerA2 = "Computer A2"
                # self.ComputerC2 = "Computer C2"
                # self.ComputerD = "Computer D"

                if userIndex in self.RoomAUsualUsersByIndex and currentRoom == self.RoomA:
                    computerID = f"Computer A{userIndex % 2}"
                elif userIndex in self.RoomCUsualUsersByIndex and currentRoom == self.RoomC:
                    computerID = f"Computer C{userIndex % 2}"
                elif userIndex == 8 and currentRoom in self.RoomAandRoomC:
                    computerID = self.ComputerA2 if currentRoom == self.RoomA else self.ComputerC2
                elif userIndex == 9 and currentRoom in self.RoomAandRoomC:
                    computerID = self.ComputerA2 if currentRoom == self.RoomA else self.ComputerC2
                elif userIndex in self.RoomAUsualUsersByIndex and currentRoom == self.RoomC:
                    computerID = self.ComputerC2
                elif userIndex in self.RoomCUsualUsersByIndex and currentRoom == self.RoomA:
                    computerID = self.ComputerA2
                elif userIndex == 10 and currentRoom == self.RoomC:
                    computerID = self.ComputerC2
                elif userIndex == 10 and currentRoom == self.RoomA:
                    computerID = self.ComputerA2
                elif userIndex in self.AllUsersByIndex and currentRoom == self.RoomD:
                    computerID = self.ComputerD
        if status == 1 or status == 2: #ON BREAK OR OUT OF SHIFT
            if status == 1:
                rand = 0.1
            elif status == 2:
                rand = 0.03
            if random.random() <= rand and possibleAlternatives:
                alternativeRoom = random.choice(possibleAlternatives)
                computerID = random.choice(self.defaultChoices[alternativeRoom])
                newRoomNumber = next(k for k, v in self.roomMap.items() if v == alternativeRoom)
                # print(f"Mismatch CID: {computerID}")
            else:
                # self.RoomAUsualUsersByIndex = [0, 1, 4, 5]
                # self.RoomCUsualUsersByIndex = [2, 3, 6, 7]
                # self.AllUsersByIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                # self.RoomAandRoomC = ["Room A", "Room C"]
                #
                # self.RoomA = "Room A"
                # self.RoomC = "Room C"
                # self.RoomD = "Room D"
                # self.ComputerA2 = "Computer A2"
                # self.ComputerC2 = "Computer C2"
                # self.ComputerD = "Computer D"

                if userIndex in self.RoomAUsualUsersByIndex and currentRoom == self.RoomA:
                    computerID = f"Computer A{userIndex % 2}"
                elif userIndex in self.RoomCUsualUsersByIndex and currentRoom == self.RoomC:
                    computerID = f"Computer C{userIndex % 2}"
                elif userIndex == 8 and currentRoom in self.RoomAandRoomC:
                    computerID = self.ComputerA2 if currentRoom == self.RoomA else self.ComputerC2
                elif userIndex == 9 and currentRoom in self.RoomAandRoomC:
                    computerID = self.ComputerA2 if currentRoom == self.RoomA else self.ComputerC2
                elif userIndex in self.RoomAUsualUsersByIndex and currentRoom == self.RoomC:
                    computerID = self.ComputerC2
                elif userIndex in self.RoomCUsualUsersByIndex and currentRoom == self.RoomA:
                    computerID = self.ComputerA2
                elif userIndex == 10 and currentRoom == self.RoomC:
                    computerID = self.ComputerC2
                elif userIndex == 10 and currentRoom == self.RoomA:
                    computerID = self.ComputerA2
                elif userIndex in self.AllUsersByIndex and currentRoom == self.RoomD:
                    computerID = self.ComputerD
                # print(f"Match CID: {computerID}")
        with open(COMPUTER_ID_FILE_PATH, "w") as file:
            json.dump({"ComputerID": computerID}, file)

        return newRoomNumber

    def getRoleIndex(self, role):
        return self.roleToIndex.get(role, -1)  # Returns the index, or -1 if role is invalid

    def isOnBreak(self, breakRanges, currentTime, role):
        # userStatusList is where we will update the break status
        # Each index represents a specific user as per the mapping you've shown earlier.

        # Shift time ranges for users
        # Get the user's shift range
        shiftStart, shiftEnd = self.shiftRanges[role]
        shiftStartTime = datetime.strptime(shiftStart, "%H:%M").time()
        shiftEndTime = datetime.strptime(shiftEnd, "%H:%M").time()

        # Get the current time as a time object
        currentT = currentTime.time()

        # If the user is outside their shift time, return 2 (out of shift)
        if not (shiftStartTime <= currentT < shiftEndTime):
            # Find the index of the user based on the role and update userStatusList
            roleIndex = self.getRoleIndex(role)
            self.userStatusList[roleIndex] = 2  # Update user status to 2 (out of shift)
            return 2  # Outside shift

        # Check if the user is on break
        for startStr, endStr in breakRanges:
            start = datetime.strptime(startStr, "%H:%M").time()
            end = datetime.strptime(endStr, "%H:%M").time()
            if start <= currentT < end:
                # Find the index of the user based on the role and update userStatusList
                roleIndex = self.getRoleIndex(role)
                self.userStatusList[roleIndex] = 1  # Update user status to 1 (on break)
                return 1  # On break

        # If the user is not on break and is within shift hours, return 0 (working)
        roleIndex = self.getRoleIndex(role)
        self.userStatusList[roleIndex] = 0  # Update user status to 0 (working)
        return 0  # In shift but not on break

    def automatorSimulation(self, simulatedTimestamp):
        logAmount = 1 # DEFAULT LOG AMOUNT
        roomNumber = self.getRandomNonEmptyRoomIndex()  # RANDOM NON-EMPTY ROOM NUMBER BY INDEX


        if roomNumber == 1:  # Room B has no Computers
            return 0 # NO LOGS

        roomLetter = None
        roomLetterConfirm = None

        if roomNumber == 0:
            roomAUserRoles = self.getRoomAUserRoles()  # GETS THE USER ROLES INSIDE ROOM A
            # print(f"Room A users: {roomAUserRoles}")
            authorization = self.getAuthorizationStatus()  # GET RANDOM AUTHORIZATION (AUTH OR UNAUTH)

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
            if hasAdministrativeStaff and hasDirector and not hasManager:
                authorization = "Authorized"

            # authorization = "Authorized" # DEBUGGER

            # GET THE ROLE AUTHORIZATION CONTEXT BASED ON USER ROLES IN ROOM A AND AUTH
            # authorization = auth:
            #   Administrative Staff, Manager, Director, Administrative Staff M-Req, Administrative Staff D-Req, Manager D-Req
            # authorization = unauth:
            #   Administrative Staff WO M-Req, Administrative Staff WO D-Req, Manager WO D-Req
            roles = self.checkRoles(roomAUserRoles, authorization)
            # print(f"Check: {roles}\n")
            # GET A VALID RANDOM USER INDEX FROM THE USERS INSIDE ROOM A BASED ON USERS AND THEIR ROLES
            # roles = "Director"  # DEBUGGER
            user = random.choice(self.getUserRoomIndices(roomAUserRoles, roles))
            # print(f"Check user: {user}\n")

            # print(f"User Room Indices: {self.getUserRoomIndices(roomAUserRoles, roles)}")
            # print(f"Room A User Roles: {roomAUserRoles}")
            # print(f"Authorization Status: {authorization}")
            # print(f"Roles to Check: {roles}")
            # print(f"Selected User Index: {user}")

            # roles = "Manager" #DEBUGGER
            # AUTH CASE
            if authorization == "Authorized":
                # IF AUTH CONTEXT IS (AS ONLY, AS WITH MANAGER, AS WITH DIRECTOR, OR AS WITH MANAGER AND DIRECTOR)
                # if roles == "Administrative Staff" or roles == "Administrative Staff M-Req" or roles == "Administrative Staff D-Req":
                if roles in self.ASRolesAuthorized:
                    length = len(self.roleFunctions[authorization][roles])

                    if length == 3:  # Administrative Staff
                        randomIndex = random.choices(range(length), weights=self.AS_Weights_Authorized, k=1)[0]
                        fileAccessType = self.AS_Weights_Authorized_Actions[randomIndex]
                        # self.AS_Weights_Authorized_Actions = [
                        #     "opened a non-confidential file",
                        #     "opened a non-confidential file with modify",
                        #     "copied a non-confidential file to internal storage"
                        # ]
                    elif length == 5:  # Administrative Staff M-Req
                        randomIndex = random.choices(range(length), weights=self.AS_MReqWeights_Authorized, k=1)[0]
                        fileAccessType = self.AS_MReqWeights_Authorized_Actions[randomIndex]
                        # self.AS_MReqWeights_Authorized_Actions = [
                        #     "opened a confidential file with permission from Manager",
                        #     "moved a non-confidential file to internal storage with permission from Manager",
                        #     "copied a confidential file to internal storage with permission from Manager",
                        #     "copied a non-confidential file to external storage with permission from Manager",
                        #     "copied a confidential file to external storage with permission from Manager"
                        # ]
                    elif length == 11:  # Administrative Staff D-Req
                        randomIndex = random.choices(range(length), weights=self.AS_DReqWeights_Authorized, k=1)[0]
                        fileAccessType = self.AS_DReqWeights_Authorized_Actions[randomIndex]
                        if randomIndex == 1:
                            logAmount = 2
                        # self.AS_DReqWeights_Authorized_Actions = [
                        #     "opened a confidential file with permission from Director",
                        #     "modified a confidential file with permission from Director",
                        #     "deleted a non-confidential file with permission from Director",
                        #     "deleted a confidential file with permission from Director",
                        #     "moved a non-confidential file to internal storage with permission from Director",
                        #     "copied a confidential file to internal storage with permission from Director",
                        #     "moved a confidential file to internal storage with permission from Director",
                        #     "copied a non-confidential file to external storage with permission from Director",
                        #     "copied a confidential file to external storage with permission from Director",
                        #     "moved a non-confidential file to external storage with permission from Director",
                        #     "moved a confidential file to external storage with permission from Director"
                        # ]

                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    # roomCheckNumber = self.writeComputerIDToFile3(roomNumber,
                    #                                               user, simulatedTimestamp)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if roomLetter == roomLetterConfirm:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                    else:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        authLogging = "Unauthorized"

                    self.roleFunctions[authorization][roles][randomIndex](user, authLogging,
                                                                          simulatedTimestamp)  # DEBUGGER

                elif roles == self.ManagerRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_Weights_Authorized, k=1)[0]
                    fileAccessType = self.Manager_Weights_Authorized_Actions[randomIndex]
                    if randomIndex == 2:
                        logAmount = 2
                    # self.Manager_Weights_Authorized_Actions = [
                    #     "opened a non-confidential file",
                    #     "opened a confidential file",
                    #     "modified a non-confidential file",
                    #     "copied a non-confidential file to internal storage",
                    #     "copied a confidential file to internal storage",
                    #     "copied a non-confidential file to ",
                    #     "copied a confidential file to ",
                    #     "copied a non-confidential file to external storage",
                    #     "copied a confidential file to external storage"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT

                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()

                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                              simulatedTimestamp)

                elif roles == self.DirectorRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Director_Weights_Authorized, k=1)[0]
                    fileAccessType = self.Director_Weights_Authorized_Actions[randomIndex]
                    if randomIndex == 2 or randomIndex == 3:
                        logAmount = 2
                    # self.Director_Weights_Authorized_Actions = [
                    #     "opened a non-confidential file",
                    #     "opened a confidential file",
                    #     "modified a non-confidential file",
                    #     "modified a confidential file",
                    #     "deleted a non-confidential file",
                    #     "deleted a confidential file",
                    #     "moved a non-confidential file to internal storage",
                    #     "moved a confidential file to internal storage",
                    #     "moved a non-confidential file to ",
                    #     "moved a confidential file to ",
                    #     "copied a non-confidential file to internal storage",
                    #     "copied a confidential file to internal storage",
                    #     "copied a non-confidential file to ",
                    #     "copied a confidential file to ",
                    #     "moved a non-confidential file to external storage",
                    #     "moved a confidential file to external storage",
                    #     "copied a non-confidential file to external storage",
                    #     "copied a confidential file to external storage"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 8 and randomIndex != 9 and randomIndex != 12 and randomIndex != 13:
                        # RANDOM FUNCTION THAT CAN BE DONE BY DIRECTOR BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Director (ID: {user}) {fileAccessType.ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Director (ID: {user}) {fileAccessType.ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        randomUser = random.randint(0, 1)  # AS or Manager
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        if randomUser == 0:
                            randomAS = self.getRandomUsernameByAS()


                            if roomLetter == roomLetterConfirm:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomAS).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                            else:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomAS).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                                authLogging = "Unauthorized"

                            self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                                  simulatedTimestamp)
                        else:
                            randomManager = self.getRandomUsernameByManager()


                            if roomLetter == roomLetterConfirm:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomManager).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                            else:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomManager).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                                authLogging = "Unauthorized"

                            self.roleFunctions[authorization][roles][randomIndex](user, randomManager, authLogging,
                                                                                  simulatedTimestamp)
                elif roles == self.ManagerDReqRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_DReqWeights_Authorized, k=1)[0]
                    fileAccessType = self.Manager_DReqWeights_Authorized_Actions[randomIndex]
                    if randomIndex == 0:
                        logAmount = 2
                    # self.Manager_DReqWeights_Authorized_Actions = [
                    #     "modified a confidential file with permission from Director",
                    #     "deleted a non-confidential file with permission from Director",
                    #     "deleted a confidential file with permission from Director",
                    #     "moved a non-confidential file to internal storage with permission from Director",
                    #     "moved a confidential file to internal storage with permission from Director",
                    #     "moved a non-confidential file with permission from Director to ",
                    #     "moved a confidential file with permission from Director to ",
                    #     "moved a non-confidential file to external storage with permission from Director",
                    #     "moved a confidential file to external storage with permission from Director"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT

                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()

                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                              simulatedTimestamp)
            elif authorization == "Unauthorized":
                # if roles == "Administrative Staff WO M-Req" or roles == "Administrative Staff WO D-Req":
                if roles == self.ASRolesUnauthorized:
                    length = len(self.roleFunctions[authorization][roles])

                    if length == 5:  # Administrative Staff WO M-Req
                        randomIndex = random.choices(range(length), weights=self.AS_WOMReqWeights_Unauthorized, k=1)[0]
                        fileAccessType = self.AS_WOMReqWeights_Unauthorized_Actions[randomIndex]
                        # self.AS_WOMReqWeights_Unauthorized_Actions = [
                        #     "opened a confidential file without permission from Manager",
                        #     "moved a non-confidential file to internal storage without permission from Manager",
                        #     "copied a confidential file to internal storage without permission from Manager",
                        #     "copied a non-confidential file to external storage without permission from Manager",
                        #     "copied a confidential file to external storage without permission from Manager"
                        # ]
                    elif length == 11:  # Administrative Staff WO D-Req
                        randomIndex = random.choices(range(length), weights=self.AS_WODReqWeights_Unauthorized, k=1)[0]
                        fileAccessType = self.AS_WODReqWeights_Unauthorized_Actions[randomIndex]
                        if randomIndex == 1:
                            logAmount = 2
                        # self.AS_WODReqWeights_Unauthorized_Actions = [
                        #     "opened a confidential file without permission from Director",
                        #     "modified a confidential file without permission from Director",
                        #     "deleted a non-confidential file without permission from Director",
                        #     "deleted a confidential file without permission from Director",
                        #     "moved a non-confidential file to internal storage without permission from Director",
                        #     "copied a confidential file to internal storage without permission from Director",
                        #     "moved a confidential file to internal storage without permission from Director",
                        #     "copied a non-confidential file to external storage without permission from Director",
                        #     "copied a confidential file to external storage without permission from Director",
                        #     "moved a non-confidential file to external storage without permission from Director",
                        #     "moved a confidential file to external storage without permission from Director"
                        # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    # roomCheckNumber = self.writeComputerIDToFile3(roomNumber,
                    #                                               user,
                    #                                               simulatedTimestamp)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)
                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT


                    if roomLetter == roomLetterConfirm:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                    else:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                    self.roleFunctions[authorization][roles][randomIndex](user, authorization,
                                                                          simulatedTimestamp)  # DEBUGGER
                elif roles == self.ManagerRoleUnauthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_WODReqWeights_Unauthorized, k=1)[0]
                    fileAccessType = self.Manager_WODReqWeights_Unauthorized_Actions[randomIndex]
                    if randomIndex == 0:
                        logAmount = 2
                    # self.Manager_WODReqWeights_Unauthorized_Actions = [
                    #     "modified a confidential file without permission from Director",
                    #     "deleted a non-confidential file without permission from Director",
                    #     "deleted a confidential file without permission from Director",
                    #     "moved a confidential file to internal storage without permission from Director",
                    #     "moved a non-confidential file to internal storage without permission from Director",
                    #     "moved a non-confidential file without permission from Director to ",
                    #     "moved a confidential file without permission from Director to ",
                    #     "moved a non-confidential file to external storage without permission from Director",
                    #     "moved a confidential file to external storage without permission from Director"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    # print(f"Random Function Index: {randomIndex}\n")
                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT

                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                        self.roleFunctions[authorization][roles][randomIndex](user, authorization, simulatedTimestamp)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authorization,
                                                                              simulatedTimestamp)

        elif roomNumber == 2:
            roomCUserRoles = self.getRoomCUserRoles()
            # print(f"Room C users: {roomCUserRoles}")
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
            if hasAdministrativeStaff and hasDirector and not hasManager:
                authorization = "Authorized"

            roles = self.checkRoles(roomCUserRoles, authorization)
            # print(f"Check: {roles}")
            user = random.choice(self.getUserRoomIndices(roomCUserRoles, roles))
            # print(f"Check user: {user}\n")

            # print(f"User Room Indices: {self.getUserRoomIndices(roomCUserRoles, roles)}")
            # print(f"Room C User Roles: {roomCUserRoles}")
            # print(f"Authorization Status: {authorization}")
            # print(f"Roles to Check: {roles}")
            # print(f"Selected User Index: {user}")

            if authorization == "Authorized":
                # IF AUTH CONTEXT IS (AS ONLY, AS WITH MANAGER, AS WITH DIRECTOR, OR AS WITH MANAGER AND DIRECTOR)
                # if roles == "Administrative Staff" or roles == "Administrative Staff M-Req" or roles == "Administrative Staff D-Req":
                if roles in self.ASRolesAuthorized:
                    length = len(self.roleFunctions[authorization][roles])

                    if length == 3:  # Administrative Staff
                        randomIndex = random.choices(range(length), weights=self.AS_Weights_Authorized, k=1)[0]
                        fileAccessType = self.AS_Weights_Authorized_Actions[randomIndex]
                        # self.AS_Weights_Authorized_Actions = [
                        #     "opened a non-confidential file",
                        #     "opened a non-confidential file with modify",
                        #     "copied a non-confidential file to internal storage"
                        # ]
                    elif length == 5:  # Administrative Staff M-Req
                        randomIndex = random.choices(range(length), weights=self.AS_MReqWeights_Authorized, k=1)[0]
                        fileAccessType = self.AS_MReqWeights_Authorized_Actions[randomIndex]
                        # self.AS_MReqWeights_Authorized_Actions = [
                        #     "opened a confidential file with permission from Manager",
                        #     "moved a non-confidential file to internal storage with permission from Manager",
                        #     "copied a confidential file to internal storage with permission from Manager",
                        #     "copied a non-confidential file to external storage with permission from Manager",
                        #     "copied a confidential file to external storage with permission from Manager"
                        # ]
                    elif length == 11:  # Administrative Staff D-Req
                        randomIndex = random.choices(range(length), weights=self.AS_DReqWeights_Authorized, k=1)[0]
                        fileAccessType = self.AS_DReqWeights_Authorized_Actions[randomIndex]
                        if randomIndex == 1:
                            logAmount = 2
                        # self.AS_DReqWeights_Authorized_Actions = [
                        #     "opened a confidential file with permission from Director",
                        #     "modified a confidential file with permission from Director",
                        #     "deleted a non-confidential file with permission from Director",
                        #     "deleted a confidential file with permission from Director",
                        #     "moved a non-confidential file to internal storage with permission from Director",
                        #     "copied a confidential file to internal storage with permission from Director",
                        #     "moved a confidential file to internal storage with permission from Director",
                        #     "copied a non-confidential file to external storage with permission from Director",
                        #     "copied a confidential file to external storage with permission from Director",
                        #     "moved a non-confidential file to external storage with permission from Director",
                        #     "moved a confidential file to external storage with permission from Director"
                        # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT


                    if roomLetter == roomLetterConfirm:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                    else:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        authLogging = "Unauthorized"

                    self.roleFunctions[authorization][roles][randomIndex](user, authLogging,
                                                                          simulatedTimestamp)  # DEBUGGER

                elif roles == self.ManagerRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_Weights_Authorized, k=1)[0]
                    fileAccessType = self.Manager_Weights_Authorized_Actions[randomIndex]
                    if randomIndex == 2:
                        logAmount = 2
                    # self.Manager_Weights_Authorized_Actions = [
                    #     "opened a non-confidential file",
                    #     "opened a confidential file",
                    #     "modified a non-confidential file",
                    #     "copied a non-confidential file to internal storage",
                    #     "copied a confidential file to internal storage",
                    #     "copied a non-confidential file to ",
                    #     "copied a confidential file to ",
                    #     "copied a non-confidential file to external storage",
                    #     "copied a confidential file to external storage"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                              simulatedTimestamp)

                elif roles == self.DirectorRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Director_Weights_Authorized, k=1)[0]
                    fileAccessType = self.Director_Weights_Authorized_Actions[randomIndex]
                    if randomIndex == 2 or randomIndex == 3:
                        logAmount = 2
                    # self.Director_Weights_Authorized_Actions = [
                    #     "opened a non-confidential file",
                    #     "opened a confidential file",
                    #     "modified a non-confidential file",
                    #     "modified a confidential file",
                    #     "deleted a non-confidential file",
                    #     "deleted a confidential file",
                    #     "moved a non-confidential file to internal storage",
                    #     "moved a confidential file to internal storage",
                    #     "moved a non-confidential file to ",
                    #     "moved a confidential file to ",
                    #     "copied a non-confidential file to internal storage",
                    #     "copied a confidential file to internal storage",
                    #     "copied a non-confidential file to ",
                    #     "copied a confidential file to ",
                    #     "moved a non-confidential file to external storage",
                    #     "moved a confidential file to external storage",
                    #     "copied a non-confidential file to external storage",
                    #     "copied a confidential file to external storage"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 8 and randomIndex != 9 and randomIndex != 12 and randomIndex != 13:
                        # RANDOM FUNCTION THAT CAN BE DONE BY DIRECTOR BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Director (ID: {user}) {fileAccessType.ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Director (ID: {user}) {fileAccessType.ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        randomUser = random.randint(0, 1)  # AS or Manager
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        if randomUser == 0:
                            randomAS = self.getRandomUsernameByAS()


                            if roomLetter == roomLetterConfirm:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomAS).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                            else:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomAS).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                                authLogging = "Unauthorized"

                            self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                                  simulatedTimestamp)
                        else:
                            randomManager = self.getRandomUsernameByManager()


                            if roomLetter == roomLetterConfirm:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomManager).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                            else:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomManager).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                                authLogging = "Unauthorized"

                            self.roleFunctions[authorization][roles][randomIndex](user, randomManager, authLogging,
                                                                                  simulatedTimestamp)
                elif roles == self.ManagerDReqRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_DReqWeights_Authorized, k=1)[0]
                    fileAccessType = self.Manager_DReqWeights_Authorized_Actions[randomIndex]
                    if randomIndex == 0:
                        logAmount = 2
                    # self.Manager_DReqWeights_Authorized_Actions = [
                    #     "modified a confidential file with permission from Director",
                    #     "deleted a non-confidential file with permission from Director",
                    #     "deleted a confidential file with permission from Director",
                    #     "moved a non-confidential file to internal storage with permission from Director",
                    #     "moved a confidential file to internal storage with permission from Director",
                    #     "moved a non-confidential file with permission from Director to ",
                    #     "moved a confidential file with permission from Director to ",
                    #     "moved a non-confidential file to external storage with permission from Director",
                    #     "moved a confidential file to external storage with permission from Director"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                              simulatedTimestamp)
            elif authorization == "Unauthorized":
                # if roles == "Administrative Staff WO M-Req" or roles == "Administrative Staff WO D-Req":
                if roles == self.ASRolesUnauthorized:
                    length = len(self.roleFunctions[authorization][roles])

                    if length == 5:  # Administrative Staff WO M-Req
                        randomIndex = random.choices(range(length), weights=self.AS_WOMReqWeights_Unauthorized, k=1)[0]
                        fileAccessType = self.AS_WOMReqWeights_Unauthorized_Actions[randomIndex]
                        # self.AS_WOMReqWeights_Unauthorized_Actions = [
                        #     "opened a confidential file without permission from Manager",
                        #     "moved a non-confidential file to internal storage without permission from Manager",
                        #     "copied a confidential file to internal storage without permission from Manager",
                        #     "copied a non-confidential file to external storage without permission from Manager",
                        #     "copied a confidential file to external storage without permission from Manager"
                        # ]
                    elif length == 11:  # Administrative Staff WO D-Req
                        randomIndex = random.choices(range(length), weights=self.AS_WODReqWeights_Unauthorized, k=1)[0]
                        fileAccessType = self.AS_WODReqWeights_Unauthorized_Actions[randomIndex]
                        if randomIndex == 1:
                            logAmount = 2
                        # self.AS_WODReqWeights_Unauthorized_Actions = [
                        #     "opened a confidential file without permission from Director",
                        #     "modified a confidential file without permission from Director",
                        #     "deleted a non-confidential file without permission from Director",
                        #     "deleted a confidential file without permission from Director",
                        #     "moved a non-confidential file to internal storage without permission from Director",
                        #     "copied a confidential file to internal storage without permission from Director",
                        #     "moved a confidential file to internal storage without permission from Director",
                        #     "copied a non-confidential file to external storage without permission from Director",
                        #     "copied a confidential file to external storage without permission from Director",
                        #     "moved a non-confidential file to external storage without permission from Director",
                        #     "moved a confidential file to external storage without permission from Director"
                        # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT


                    if roomLetter == roomLetterConfirm:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                    else:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                    self.roleFunctions[authorization][roles][randomIndex](user, authorization,
                                                                          simulatedTimestamp)  # DEBUGGER
                elif roles == self.ManagerRoleUnauthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_WODReqWeights_Unauthorized, k=1)[0]
                    fileAccessType = self.Manager_WODReqWeights_Unauthorized_Actions[randomIndex]
                    if randomIndex == 0:
                        logAmount = 2
                    # self.Manager_WODReqWeights_Unauthorized_Actions = [
                    #     "modified a confidential file without permission from Director",
                    #     "deleted a non-confidential file without permission from Director",
                    #     "deleted a confidential file without permission from Director",
                    #     "moved a confidential file to internal storage without permission from Director",
                    #     "moved a non-confidential file to internal storage without permission from Director",
                    #     "moved a non-confidential file without permission from Director to ",
                    #     "moved a confidential file without permission from Director to ",
                    #     "moved a non-confidential file to external storage without permission from Director",
                    #     "moved a confidential file to external storage without permission from Director"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                        self.roleFunctions[authorization][roles][randomIndex](user, authorization, simulatedTimestamp)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authorization,
                                                                              simulatedTimestamp)

        elif roomNumber == 3:
            roomDUserRoles = self.getRoomDUserRoles()
            # print(f"Room D users: {roomDUserRoles}")
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
            if hasAdministrativeStaff and hasDirector and not hasManager:
                authorization = "Authorized"

            roles = self.checkRoles(roomDUserRoles, authorization)
            # print(f"Check: {roles}")
            user = random.choice(self.getUserRoomIndices(roomDUserRoles, roles))
            # print(f"Check user: {user}\n")

            # print(f"User Room Indices: {self.getUserRoomIndices(roomDUserRoles, roles)}")
            # print(f"Room D User Roles: {roomDUserRoles}")
            # print(f"Authorization Status: {authorization}")
            # print(f"Roles to Check: {roles}")
            # print(f"Selected User Index: {user}")

            if authorization == "Authorized":
                # IF AUTH CONTEXT IS (AS ONLY, AS WITH MANAGER, AS WITH DIRECTOR, OR AS WITH MANAGER AND DIRECTOR)
                # if roles == "Administrative Staff" or roles == "Administrative Staff M-Req" or roles == "Administrative Staff D-Req":
                if roles in self.ASRolesAuthorized:
                    length = len(self.roleFunctions[authorization][roles])

                    if length == 3:  # Administrative Staff
                        randomIndex = random.choices(range(length), weights=self.AS_Weights_Authorized, k=1)[0]
                        fileAccessType = self.AS_Weights_Authorized_Actions[randomIndex]
                        # self.AS_Weights_Authorized_Actions = [
                        #     "opened a non-confidential file",
                        #     "opened a non-confidential file with modify",
                        #     "copied a non-confidential file to internal storage"
                        # ]
                    elif length == 5:  # Administrative Staff M-Req
                        randomIndex = random.choices(range(length), weights=self.AS_MReqWeights_Authorized, k=1)[0]
                        fileAccessType = self.AS_MReqWeights_Authorized_Actions[randomIndex]
                        # self.AS_MReqWeights_Authorized_Actions = [
                        #     "opened a confidential file with permission from Manager",
                        #     "moved a non-confidential file to internal storage with permission from Manager",
                        #     "copied a confidential file to internal storage with permission from Manager",
                        #     "copied a non-confidential file to external storage with permission from Manager",
                        #     "copied a confidential file to external storage with permission from Manager"
                        # ]
                    elif length == 11:  # Administrative Staff D-Req
                        randomIndex = random.choices(range(length), weights=self.AS_DReqWeights_Authorized, k=1)[0]
                        fileAccessType = self.AS_DReqWeights_Authorized_Actions[randomIndex]
                        if randomIndex == 1:
                            logAmount = 2
                        # self.AS_DReqWeights_Authorized_Actions = [
                        #     "opened a confidential file with permission from Director",
                        #     "modified a confidential file with permission from Director",
                        #     "deleted a non-confidential file with permission from Director",
                        #     "deleted a confidential file with permission from Director",
                        #     "moved a non-confidential file to internal storage with permission from Director",
                        #     "copied a confidential file to internal storage with permission from Director",
                        #     "moved a confidential file to internal storage with permission from Director",
                        #     "copied a non-confidential file to external storage with permission from Director",
                        #     "copied a confidential file to external storage with permission from Director",
                        #     "moved a non-confidential file to external storage with permission from Director",
                        #     "moved a confidential file to external storage with permission from Director"
                        # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT
                    authLogging = authorization

                    # print(f"Administrative Staff (ID: {user}) {fileAccessType} in Room A - Authorized")
                    # print(f"Administrative Staff (ID: {user}) {fileAccessType.ljust(max_length)} in Room A - Authorized")
                    if roomLetter == roomLetterConfirm:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                    else:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        authLogging = "Unauthorized"

                    self.roleFunctions[authorization][roles][randomIndex](user, authLogging,
                                                                          simulatedTimestamp)  # DEBUGGER

                elif roles == self.ManagerRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_Weights_Authorized, k=1)[0]
                    fileAccessType = self.Manager_Weights_Authorized_Actions[randomIndex]
                    if randomIndex == 2:
                        logAmount = 2
                    # self.Manager_Weights_Authorized_Actions = [
                    #     "opened a non-confidential file",
                    #     "opened a confidential file",
                    #     "modified a non-confidential file",
                    #     "copied a non-confidential file to internal storage",
                    #     "copied a confidential file to internal storage",
                    #     "copied a non-confidential file to ",
                    #     "copied a confidential file to ",
                    #     "copied a non-confidential file to external storage",
                    #     "copied a confidential file to external storage"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                              simulatedTimestamp)

                elif roles == self.DirectorRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Director_Weights_Authorized, k=1)[0]
                    fileAccessType = self.Director_Weights_Authorized_Actions[randomIndex]
                    if randomIndex == 2 or randomIndex == 3:
                        logAmount = 2
                    # self.Director_Weights_Authorized_Actions = [
                    #     "opened a non-confidential file",
                    #     "opened a confidential file",
                    #     "modified a non-confidential file",
                    #     "modified a confidential file",
                    #     "deleted a non-confidential file",
                    #     "deleted a confidential file",
                    #     "moved a non-confidential file to internal storage",
                    #     "moved a confidential file to internal storage",
                    #     "moved a non-confidential file to ",
                    #     "moved a confidential file to ",
                    #     "copied a non-confidential file to internal storage",
                    #     "copied a confidential file to internal storage",
                    #     "copied a non-confidential file to ",
                    #     "copied a confidential file to ",
                    #     "moved a non-confidential file to external storage",
                    #     "moved a confidential file to external storage",
                    #     "copied a non-confidential file to external storage",
                    #     "copied a confidential file to external storage"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 8 and randomIndex != 9 and randomIndex != 12 and randomIndex != 13:
                        # RANDOM FUNCTION THAT CAN BE DONE BY DIRECTOR BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Director (ID: {user}) {fileAccessType.ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Director (ID: {user}) {fileAccessType.ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        randomUser = random.randint(0, 1)  # AS or Manager
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        # self.simulateCopyNonConfidentialFileToOthers,
                        # self.simulateCopyConfidentialFileToOthers,
                        if randomUser == 0:
                            randomAS = self.getRandomUsernameByAS()


                            if roomLetter == roomLetterConfirm:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomAS).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                            else:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomAS).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                                authLogging = "Unauthorized"

                            self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                                  simulatedTimestamp)
                        else:
                            randomManager = self.getRandomUsernameByManager()


                            if roomLetter == roomLetterConfirm:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomManager).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                            else:
                                print(
                                    f"Director (ID: {user}) {(fileAccessType + randomManager).ljust(92)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                                authLogging = "Unauthorized"

                            self.roleFunctions[authorization][roles][randomIndex](user, randomManager, authLogging,
                                                                                  simulatedTimestamp)
                elif roles == self.ManagerDReqRoleAuthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_DReqWeights_Authorized, k=1)[0]
                    fileAccessType = self.Manager_DReqWeights_Authorized_Actions[randomIndex]
                    if randomIndex == 0:
                        logAmount = 2
                    # self.Manager_DReqWeights_Authorized_Actions = [
                    #     "modified a confidential file with permission from Director",
                    #     "deleted a non-confidential file with permission from Director",
                    #     "deleted a confidential file with permission from Director",
                    #     "moved a non-confidential file to internal storage with permission from Director",
                    #     "moved a confidential file to internal storage with permission from Director",
                    #     "moved a non-confidential file with permission from Director to ",
                    #     "moved a confidential file with permission from Director to ",
                    #     "moved a non-confidential file to external storage with permission from Director",
                    #     "moved a confidential file to external storage with permission from Director"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    authLogging = authorization

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY MANAGER BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, authLogging, simulatedTimestamp)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Authorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                            authLogging = "Unauthorized"

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authLogging,
                                                                              simulatedTimestamp)
            elif authorization == "Unauthorized":
                # if roles == "Administrative Staff WO M-Req" or roles == "Administrative Staff WO D-Req":
                if roles == self.ASRolesUnauthorized:
                    length = len(self.roleFunctions[authorization][roles])

                    if length == 5:  # Administrative Staff WO M-Req
                        randomIndex = random.choices(range(length), weights=self.AS_WOMReqWeights_Unauthorized, k=1)[0]
                        fileAccessType = self.AS_WOMReqWeights_Unauthorized_Actions[randomIndex]
                        # self.AS_WOMReqWeights_Unauthorized_Actions = [
                        #     "opened a confidential file without permission from Manager",
                        #     "moved a non-confidential file to internal storage without permission from Manager",
                        #     "copied a confidential file to internal storage without permission from Manager",
                        #     "copied a non-confidential file to external storage without permission from Manager",
                        #     "copied a confidential file to external storage without permission from Manager"
                        # ]
                    elif length == 11:  # Administrative Staff WO D-Req
                        randomIndex = random.choices(range(length), weights=self.AS_WODReqWeights_Unauthorized, k=1)[0]
                        fileAccessType = self.AS_WODReqWeights_Unauthorized_Actions[randomIndex]
                        if randomIndex == 1:
                            logAmount = 2
                        # self.AS_WODReqWeights_Unauthorized_Actions = [
                        #     "opened a confidential file without permission from Director",
                        #     "modified a confidential file without permission from Director",
                        #     "deleted a non-confidential file without permission from Director",
                        #     "deleted a confidential file without permission from Director",
                        #     "moved a non-confidential file to internal storage without permission from Director",
                        #     "copied a confidential file to internal storage without permission from Director",
                        #     "moved a confidential file to internal storage without permission from Director",
                        #     "copied a non-confidential file to external storage without permission from Director",
                        #     "copied a confidential file to external storage without permission from Director",
                        #     "moved a non-confidential file to external storage without permission from Director",
                        #     "moved a confidential file to external storage without permission from Director"
                        # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT


                    if roomLetter == roomLetterConfirm:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                    else:
                        print(
                            f"Administrative Staff (ID: {user}) {fileAccessType.ljust(80)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                    self.roleFunctions[authorization][roles][randomIndex](user, authorization,
                                                                          simulatedTimestamp)  # DEBUGGER
                elif roles == self.ManagerRoleUnauthorized:
                    length = len(self.roleFunctions[authorization][roles])
                    randomIndex = random.choices(range(length), weights=self.Manager_WODReqWeights_Unauthorized, k=1)[0]
                    fileAccessType = self.Manager_WODReqWeights_Unauthorized_Actions[randomIndex]
                    if randomIndex == 0:
                        logAmount = 2
                    # self.Manager_WODReqWeights_Unauthorized_Actions = [
                    #     "modified a confidential file without permission from Director",
                    #     "deleted a non-confidential file without permission from Director",
                    #     "deleted a confidential file without permission from Director",
                    #     "moved a confidential file to internal storage without permission from Director",
                    #     "moved a non-confidential file to internal storage without permission from Director",
                    #     "moved a non-confidential file without permission from Director to ",
                    #     "moved a confidential file without permission from Director to ",
                    #     "moved a non-confidential file to external storage without permission from Director",
                    #     "moved a confidential file to external storage without permission from Director"
                    # ]

                    if roomNumber == 0:
                        roomLetter = self.RoomA
                    elif roomNumber == 2:
                        roomLetter = self.RoomC
                    elif roomNumber == 3:
                        roomLetter = self.RoomD

                    roomCheckNumber = self.writeComputerIDToFile2(roomNumber,
                                                                  user)  # HAS A CHANCE TO GIVE A ROOM MISMATCH TO SIMULATE ROOM MISMATCH LOCATION

                    if roomCheckNumber == 0:
                        roomLetterConfirm = self.RoomA
                    elif roomCheckNumber == 2:
                        roomLetterConfirm = self.RoomC
                    elif roomCheckNumber == 3:
                        roomLetterConfirm = self.RoomD

                    if randomIndex != 5 and randomIndex != 6:
                        # RANDOM FUNCTION THAT CAN BE DONE BY AS BASED ON THE ROLE AUTHORIZATION CONTEXT


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {fileAccessType.ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                        self.roleFunctions[authorization][roles][randomIndex](user, authorization, simulatedTimestamp)
                    else:
                        # self.simulateMoveNonConfidentialFileToOthers,
                        # self.simulateMoveConfidentialFileToOthers,
                        randomAS = self.getRandomUsernameByAS()


                        if roomLetter == roomLetterConfirm:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")
                        else:
                            print(
                                f"Manager (ID: {user}) {(fileAccessType + randomAS).ljust(93)} in {roomLetterConfirm} but actually in {roomLetter} - Unauthorized")

                        self.roleFunctions[authorization][roles][randomIndex](user, randomAS, authorization,
                                                                              simulatedTimestamp)
        return logAmount


at = UserFileAccessAttemptAutomator()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createAdministrativeStaff()
at.createManager()
at.createManager()
at.createDirector()
# at.createDirector()

# user: User = at.userList[0]
# print(user.getIsOnBreak())

# user: User = at.getUser(0)
# print(user.getIsOnBreak())

# at.writeComputerIDToFile(0)
# a = at.loadRooms()
# print(a)



ualLock = UAL_JSON_PATH + ".lock"
a = FileLock(ualLock)
d = Lock()

simulatedTime = datetime.strptime("2025-04-28 07:00:00", "%Y-%m-%d %H:%M:%S")

maxLogs = 100000
currentLogs = 0

while currentLogs < maxLogs:
    # Skip weekends
    if simulatedTime.weekday() >= 5:
        simulatedTime += timedelta(days=1)
        simulatedTime = simulatedTime.replace(hour=7, minute=0, second=0)
        continue

    # Skip to next weekday if past 9:00 PM
    if simulatedTime.hour >= 21:
        simulatedTime += timedelta(days=1)
        simulatedTime = simulatedTime.replace(hour=7, minute=0, second=0)
        continue


    try:
        with a.acquire(timeout=1):
            with open(UAL_JSON_PATH, "r") as ualFile:
                roomAssignments = json.load(ualFile)

            with open(SNAP_UAL_FILE_PATH, "w") as snapFile:
                json.dump(roomAssignments, snapFile, indent=4)

    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: ual.json not found or invalid.")
        continue

    # Advance simulated time
    gapSeconds = random.randint(30, 300)
    simulatedTime += timedelta(seconds=gapSeconds)

    breakStatus = {
        "currentTime": simulatedTime.strftime("%Y-%m-%d %H:%M:%S"),
        "AS1": at.isOnBreak([("10:00", "11:00")], simulatedTime, "AS1"),
        "AS2": at.isOnBreak([("10:00", "11:00")], simulatedTime, "AS2"),
        "AS3": at.isOnBreak([("11:00", "12:00")], simulatedTime, "AS3"),
        "AS4": at.isOnBreak([("11:00", "12:00")], simulatedTime, "AS4"),
        "Manager1": at.isOnBreak([("11:00", "12:00")], simulatedTime, "Manager1"),
        "AS5": at.isOnBreak([("17:00", "18:00")], simulatedTime, "AS5"),
        "AS6": at.isOnBreak([("17:00", "18:00")], simulatedTime, "AS6"),
        "AS7": at.isOnBreak([("18:00", "19:00")], simulatedTime, "AS7"),
        "AS8": at.isOnBreak([("18:00", "19:00")], simulatedTime, "AS8"),
        "Manager2": at.isOnBreak([("18:00", "19:00")], simulatedTime, "Manager2"),
        "Director1": at.isOnBreak([("10:00", "11:00"), ("17:00", "18:00")], simulatedTime, "Director1")
    }

    with d:
        with open(USER_STATUS_TRACKER_FILE_PATH, "w") as f:
            json.dump(breakStatus, f, indent=4)

    logsGenerated = at.automatorSimulation(simulatedTime)
    currentLogs += logsGenerated  # Must return number of logs per call
    # print(simulatedTime)
    # print(at.userStatusList)
    time.sleep(1)



