import os
import time
import json
import win32serviceutil
import win32service
import win32event
import threading
from threading import Lock

class Simplifier:
    def __init__(self, filePath, simplified_file_path):
        self.filePath = filePath
        self.simplifiedFilePath = simplified_file_path
        self.lastProcessedLength = 0
        self.fileLock = Lock()
        self.idleTime = 0.5

    def readNewEntries(self):
        with self.fileLock:
            with open(self.filePath, "r") as f:
                try:
                    data = json.load(f)
                    newEntries = data[self.lastProcessedLength:]
                    self.lastProcessedLength = len(data)
                    return newEntries
                except json.JSONDecodeError:
                    return []

    def simplifyCut(self, entries):
        expectedPattern = ['File Deletion', 'File Creation', 'File Modification']

        if len(entries) == 3 and entries[0]['fileAccessType'] == expectedPattern[0] and \
                entries[1]['fileAccessType'] == expectedPattern[1] and entries[2]['fileAccessType'] == \
                expectedPattern[2]:
            entries[2]['fileAccessType'] = 'File Move'
            return [entries[2]]

        return entries

    def simplifyCopy(self, entries):
        expectedPattern1 = ['File Creation', 'File Modification']
        expectedPattern2 = ['File Deletion', 'File Creation']

        if len(entries) == 2:
            if entries[0]['fileAccessType'] == expectedPattern1[0] and entries[1]['fileAccessType'] == expectedPattern1[
                1]:
                entries[1]['fileAccessType'] = 'File Copy'
                return [entries[1]]

            elif entries[0]['fileAccessType'] == expectedPattern2[0] and entries[1]['fileAccessType'] == \
                    expectedPattern2[1]:
                entries[1]['fileAccessType'] = 'File Move'
                return [entries[1]]

        return entries

    def appendToSimplifiedLogs(self, simplifiedLogs):
        with self.fileLock:
            with open(self.simplifiedFilePath, 'r') as f:
                try:
                    existingLogs = json.load(f)
                except json.JSONDecodeError:
                    existingLogs = []

            existingLogs.extend(simplifiedLogs)

            with open(self.simplifiedFilePath, 'w') as f:
                json.dump(existingLogs, f, indent=4)

    def listen(self):
        while True:
            newEntries = self.readNewEntries()
            if newEntries:
                time.sleep(0.2)
                updatedEntries = self.readNewEntries()
                if updatedEntries:
                    newEntries.extend(updatedEntries)

                if len(newEntries) == 1:
                    self.appendToSimplifiedLogs(newEntries)

                elif len(newEntries) == 3:
                    simplified_logs = self.simplifyCut(newEntries)
                    self.appendToSimplifiedLogs(simplified_logs)

                elif len(newEntries) == 2:
                    simplified_logs = self.simplifyCopy(newEntries)
                    self.appendToSimplifiedLogs(simplified_logs)

                self.idleTime = 0.01
            else:
                self.idleTime = min(self.idleTime + 0.1, 0.5)
            time.sleep(self.idleTime)

class ComputerAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FileLogSimplifierService"
    _svc_display_name_ = "File Log Simplifier Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.listener_thread = None
        self.simplifier = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.listener_thread:
            self.listener_thread.join()

    def SvcDoRun(self):
        self.start_listener()

    def start_listener(self):
        filePath = r"C:\Shared\save.json"
        simplifiedFilePath = r"C:\Shared\save_simplified.json"
        self.simplifier = Simplifier(filePath, simplifiedFilePath)

        self.listener_thread = threading.Thread(target=self.simplifier.listen)
        self.listener_thread.start()

        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

        if self.listener_thread:
            self.listener_thread.join()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ComputerAgentService)
