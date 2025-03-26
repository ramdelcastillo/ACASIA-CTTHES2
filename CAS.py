import os
import time
import json
import win32serviceutil
import win32service
import win32event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Computer Agent Service

RAW_LOG_FILE_PATH = r'C:\Shared\save.json'
CURRENT_USER_FILE_PATH = r"C:\Shared\loggedUser.json"
COMPUTER_ID_FILE_PATH = r"C:\Shared\computerID.json"

def getCurrentUsername():
    try:
        with open(CURRENT_USER_FILE_PATH, "r") as file:
            data = json.load(file)
            return data.get("username")
    except Exception as e:
        return None

def getComputerID():
    try:
        with open(COMPUTER_ID_FILE_PATH, "r") as file:
            data = json.load(file)
            return data.get("ComputerID")
    except Exception as e:
        return None

def appendLogToFile(logData):
    try:
        with open(RAW_LOG_FILE_PATH, "r") as file:
            data = json.load(file)
        data.append(logData)
        with open(RAW_LOG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        return None

# computerID = getComputerID()

class FileAccessHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.lastEvents = {}
        self.lastDeletedEvents = {}
        self.lastOpenedEvents = {}

    def formatEventAsJSON(self, eventType, fileDestDir, timestamp):
        event_data = {
            "Timestamp": timestamp,
            "Username": getCurrentUsername(),
            "ComputerID": getComputerID(),
            "fileAccessType": eventType,
            "fileDestinationDirectory": fileDestDir
        }
        return event_data

    def on_modified(self, event):
        accessTime = time.time()
        fileName = event.src_path.split('\\')[-1]
        fileDir = event.src_path

        if fileName.endswith('.tmp'):
            return

        if fileName.startswith('~'):
            if event.src_path in self.lastOpenedEvents:
                lastOpenTime = self.lastOpenedEvents[event.src_path]
                timeDiff = (accessTime - lastOpenTime)
                if timeDiff < 1:
                    return

            self.lastOpenedEvents[event.src_path] = accessTime
            JSONOutput = self.formatEventAsJSON("File Opening", fileDir, accessTime)
            appendLogToFile(JSONOutput)
            return

        if event.src_path in self.lastEvents:
            lastEventTime = self.lastEvents[event.src_path]
            timeDiff = (accessTime - lastEventTime)
            if timeDiff < 1:
                return

        self.lastEvents[event.src_path] = accessTime
        JSONOutput = self.formatEventAsJSON("File Modification", fileDir, accessTime)
        appendLogToFile(JSONOutput)

    def on_deleted(self, event):
        accessTime = time.time()
        fileName = event.src_path.split('\\')[-1]
        fileDir = event.src_path

        if fileName.endswith('.tmp'):
            return

        if fileName.startswith('~'):
            return

        if event.src_path in self.lastDeletedEvents:
            lastDeletedTime = self.lastDeletedEvents[event.src_path]
            timeDiff = (accessTime - lastDeletedTime)
            if timeDiff < 1:
                return

        self.lastDeletedEvents[event.src_path] = accessTime
        JSONOutput = self.formatEventAsJSON("File Deletion", fileDir, accessTime)
        appendLogToFile(JSONOutput)

    def on_created(self, event):
        accessTime = time.time()
        fileName = event.src_path.split('\\')[-1]
        fileDir = event.src_path

        if fileName.endswith('.tmp') or fileName.startswith('~'):
            return

        if event.src_path in self.lastEvents:
            lastEventTime = self.lastEvents[event.src_path]
            timeDiff = (accessTime - lastEventTime)
            if timeDiff < 1:
                return

        JSONOutput = self.formatEventAsJSON("File Creation", fileDir, accessTime)
        print(JSONOutput)
        appendLogToFile(JSONOutput)

class ComputerAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FileComputerAgentService"
    _svc_display_name_ = "File Computer Agent Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.observer = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def SvcDoRun(self):
        self.startMonitoring()

    def startMonitoring(self):
        pathsToMonitor = [
            r"C:\Users\janva\Downloads\AS1",
            r"C:\Users\janva\Downloads\AS2",
            r"C:\Users\janva\Downloads\Manager1",
            r"C:\Users\janva\Downloads\Manager2",
            r"C:\Users\janva\Downloads\Director1",
            r"C:\Users\janva\Downloads\Director2",
            r"C:\Users\janva\Downloads\AS1_InternalFolder",
            r"C:\Users\janva\Downloads\AS2_InternalFolder",
            r"C:\Users\janva\Downloads\Manager1_InternalFolder",
            r"C:\Users\janva\Downloads\Manager2_InternalFolder",
            r"C:\Users\janva\Downloads\Director1_InternalFolder",
            r"C:\Users\janva\Downloads\Director2_InternalFolder",
            r"C:\Users\janva\Downloads\ExternalDrive",
        ]

        fileAccessHandler = FileAccessHandler()
        self.observer = Observer()

        for path in pathsToMonitor:
            self.observer.schedule(fileAccessHandler, path=path, recursive=True)

        self.observer.start()

        try:
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        finally:
            self.observer.stop()
            self.observer.join()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ComputerAgentService)