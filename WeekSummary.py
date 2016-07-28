#!/bin/python

import json
import sys
from datetime import datetime, timedelta

SAVE_FILE = "TASK_MEMORY.json"

class Task():
    _DateFormat = '%Y-%m-%dT%H:%M:%S' #2009-05-13T19:19:30
    End = None

    def __init__(self, name, starttime=None, endtime=None):
        self.Name = name
        if starttime is None:
            starttime = datetime.now()
        if type(starttime) is not datetime:
            raise Exception("Argument Error: Start time is not a datetime object!")
        self.Start = starttime
        if type(endtime) is datetime:
            if endtime > starttime:
                self.End = endtime
            else:
                raise Exception("Argument Error: End time cannot be less than start time!")

    def __str__(self):
        ret = "Name={0}\nStarted={1}".format(self.getName(), Task.dateTimeToDateTimeString(self.getStartTime()))
        e = self.getEndTime()
        if e is not None:
            ret += "\nEnded={0}".format(Task.dateTimeToDateTimeString(e))
        return ret

    @staticmethod
    def secondsToHours(seconds):
        return (seconds / 60 / 60)

    @staticmethod
    def dateTimeStringToDateTime(dtString):
        return datetime.strptime(dtString, Task._DateFormat)

    @staticmethod
    def dateTimeToDateTimeString(dt):
        return dt.strftime(Task._DateFormat)

    def toDict(self):
        export = {}
        export["TaskName"] = self.getName()
        export["TaskStart"] = Task.dateTimeToDateTimeString(self.getStartTime())
        tEnd = self.getEndTime()
        if tEnd is not None:
            tEnd = Task.dateTimeToDateTimeString(tEnd)
        export["TaskEnd"] = tEnd
        return export

    #TODO Possible exception when self.End is None
    def getDurationInSeconds(self, toTime=None):
        if toTime is None or type(toTime) is not datetime:
            toTime = self.End
        return (toTime - self.Start).total_seconds()

    #TODO Possible exception when self.End is None
    def getDurationInHours(self, toTime=None):
        durInSecs = self.getDurationInSeconds(toTime)
        hours = Task.secondsToHours(durInSecs)
        return hours

    def getStartTime(self):
        return self.Start

    def setEndTime(self, newVal):
        self.End = newVal

    def getEndTime(self):
        return self.End

    def getName(self):
        return self.Name


class TaskManager():
    Tasks = {} # { TaskName: [ Task1, Task2, Task3 ] }

    def add(self, task):
        if task.getName() not in self.Tasks.keys():
            self.Tasks[task.getName()] = [task]
            return
        self.Tasks[task.getName()].append(task)

    def get(self, taskName):
        if taskName not in self.Tasks.keys():
            return None
        return self.Tasks[taskName]

    def set(self, taskName, taskData):
        self.Tasks[taskName] = taskData

    def calculateAveragePay(self, taskList, hourlyPay, incomeTax):
        ret = 0
        for task in taskList:
            try:
                ret += (task.getDurationInHours() * hourlyPay * (1 - incomeTax))
            except Exception:
                pass
        return ret

    def punchIn(self, taskName):
        tlist = self.get(taskName)
        if tlist is None:
            task = Task(taskName)
            self.add(task)
            return task
        notPunchedOut = self.firstNotPunchedOut(tlist)
        if notPunchedOut is None:
            task = Task(taskName)
            self.add(Task(taskName))
            return task
        raise Exception("Argument Exception: The task '{0}' must be punched out of before you can punch in!".format(taskName))

    def punchOut(self, taskName):
        tlist = self.get(taskName)
        if tlist is None:
            raise Exception("Argument Exception: The task '{0}' must exist to be punched out of!".format(taskName))
        notPunchedOut = self.firstNotPunchedOut(tlist)
        if notPunchedOut is None:
            raise Exception("Argument Exception: The task '{0}' must be punched in before you can punch out!".format(taskName))
        notPunchedOut.setEndTime(datetime.now())
        return notPunchedOut

    def firstNotPunchedOut(self, taskList):
        for task in taskList:
            if task.getEndTime() is None:
                return task
        return None

    def __str__(self):
        temp = ""
        for x in self.Tasks.keys():
            temp += x.upper()
            for y in self.Tasks[x]:
                temp += '\n' + str(y) + '\n'
            temp += '\n'
        return temp

    def toJson(self, Indent=None):
        Root = []
        for taskList in self.Tasks.values():
            for task in taskList:
                Root.append(task.toDict())
        return json.dumps(Root, indent=Indent)

    def fromJson(self, tasksData):
        data = json.loads(tasksData)
        errorList = []
        if type(data) is not list:
            raise Exception("Format Exception: Root of in file isn't a list!")
        for i in data:
            if type(i) is not dict:
                errorList.append(Exception("Format Exception: Element under root list wasn't a dictionary!"))
                continue
            try:
                tStart = Task.dateTimeStringToDateTime(i["TaskStart"])
                tEnd = i.get("TaskEnd")
                if tEnd is not None:
                    tEnd = Task.dateTimeStringToDateTime(tEnd)
                self.add(Task(i["TaskName"], tStart, tEnd))
            except Exception as e:
                errorList.append(e)
        for x in errorList:
            print(x)

    def store(self, storePath):
        with open(storePath, 'w') as outF:
            outF.write(self.toJson())

    def load(self, loadPath):
        data = None
        with open(loadPath, 'r') as inF:
            data = inF.read()
        if data is None:
            raise Exception("Error Loading Data: Wasn't able to load anything from '{0}'!".format(loadPath))
        self.fromJson(data)

    def run(self):
        global SAVE_FILE
        try:
            self.load(SAVE_FILE)
        except Exception:
            print("Warning: Loading from save file '{0}' failed!".format(SAVE_FILE))

        #Figure out the day of the week, get ctimes between monday and sunday
        #Print summary based on selected task and times that fit between start and end of week
        minimumStartTime = self.getCurrentWeekStart() #get start of week days
        minimumStartTime = datetime(minimumStartTime.year, minimumStartTime.month, minimumStartTime.day) #reset the time to beginning of day
        maximumEndTime = minimumStartTime + timedelta(days=7) #add 24 * 7 hours.. this could be wrong
        hoursThisWeek = 0
        for task in self.get("work"):
            if task.getStartTime() >= minimumStartTime:
                dur = 0
                if task.getEndTime() is not None:
                    if task.getEndTime() <= maximumEndTime:
                        dur = task.getDurationInHours()
                    else:
                        continue
                else:
                    dur = task.getDurationInHours(datetime.now())
                hoursThisWeek += dur
        print("So far this week you have put in {0} hours of work.".format(hoursThisWeek))

    def getCurrentWeekStart(self):
        dt = datetime.now()
        return dt - timedelta(days=dt.weekday())

    def getCurrentWeekEnd(self):
        dt = datetime.now()
        start = dt - timedelta(days=dt.weekday())
        return start + timedelta(days=6)

def main():
    tm = TaskManager()
    tm.run() # feed arguments to task manager to run

if __name__ == "__main__":
    main()
