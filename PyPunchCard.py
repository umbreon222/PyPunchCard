#!/bin/python

import json
import sys
from datetime import datetime, timedelta

# Needs an option to check time of currently punched in task

SAVE_FILE = "TASK_MEMORY.json"
HELP_DOC = "{0}\n\n    Punch (in|out|i|o) [TaskName]    -    Punch in or out of a task\n\n    List Tasks                       -    Lists currently created tasks\n\n    List Task [TaskName]             -    Lists punch clock records for the task\n\n    Print Summary                    -    Prints a summary of all tasks\n\n    Print Summary [TaskName]         -    Prints a summary of the task\n\n    Display Tasks                    -    Displays a punch card graph of all tasks\n\n    Display Task [TaskName]          -    Displays a punch card graph of the task\n\n    Calc Avg Pay [TaskName] \n    [HourlyWage] \n    (Optional)[IncomeTax]            -    Displays a rough average net income for \n                                          a task\n"


class Task:
    _DateFormat = '%Y-%m-%dT%H:%M:%S'  # 2009-05-13T19:19:30
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
        ret = "Name={0}\nStarted={1}".format(self.get_name(), Task.date_time_to_date_time_string(self.get_start_time()))
        e = self.get_end_time()
        if e is not None:
            ret += "\nEnded={0}".format(Task.date_time_to_date_time_string(e))
        return ret

    @staticmethod
    def seconds_to_hours(seconds):
        return seconds / 60 / 60

    @staticmethod
    def date_time_string_to_date_time(dtstring):
        return datetime.strptime(dtstring, Task._DateFormat)

    @staticmethod
    def date_time_to_date_time_string(dt):
        return dt.strftime(Task._DateFormat)

    def to_dict(self):
        export = dict()
        export["TaskName"] = self.get_name()
        export["TaskStart"] = Task.date_time_to_date_time_string(self.get_start_time())
        t_end = self.get_end_time()
        if t_end is not None:
            t_end = Task.date_time_to_date_time_string(t_end)
        export["TaskEnd"] = t_end
        return export

    # TODO Possible exception when self.End is None
    def get_duration_in_seconds(self, to_time=None):
        if to_time is None or type(to_time) is not datetime:
            to_time = self.End
        return (to_time - self.Start).total_seconds()

    # TODO Possible exception when self.End is None
    def get_duration_in_hours(self, to_time=None):
        hours = Task.seconds_to_hours(self.get_duration_in_seconds(to_time))
        return hours

    def get_start_time(self):
        return self.Start

    def set_end_time(self, new_val):
        self.End = new_val

    def get_end_time(self):
        return self.End

    def get_name(self):
        return self.Name


class PunchCardGrapher:
    '''Construct a punchcard.
    Quick'n dirty way.
    Parameters
    ==========
    - timeData: Dictionary of quantities to display.
            They are indexed by key of type (val1,val2) with
            val1 included in ax1 and val2 included in ax2.
    - ax1: list
            Possible values for first axis (if different than days)
    - ax2: list
            Possible values for second axis (if different than hours)
    - ax1_ticks: list
            Value to display in ticks of first axis (if different than days)
    - ax2_ticks: list
            Value to display in ticks of second axis (if different than days)
    - ax1_label: String
            Value to give to first axis (if different than day)
    - ax2_label: String
            Value to give to second axis (if different than day)
    '''
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    DAY = "Day"
    HOUR = "Hour"
    HOURS_IN_DAY = 24
    CIRCLE_COLOR = "GREEN"

    @staticmethod
    def convertTasksToTimeData(taskList):
        # this is what would normally be fed into the graph
        data = {}
        for task in taskList:
            if task.get_end_time() is None:
                continue
            if task.get_start_time().weekday() != task.get_end_time().weekday():
                continue
            if task.get_start_time().hour > task.get_end_time().hour:
                continue #you cant end a task before it begins
            wd = task.get_start_time().weekday()
            for x in range(task.get_start_time().hour, task.get_end_time().hour + 1):
                key = (wd, x)
                if key not in data.keys():
                    data[key] = 0
                data[key] += 1
        return data

    def __init__(self, taskList):
        # Import these here because they take forever to import and aren't needed anywhere else
        import matplotlib.pyplot as plot
        import numpy as np
        ax1=range(len(self.DAYS))
        ax2=range(self.HOURS_IN_DAY)
        ax1_ticks=self.DAYS
        ax2_ticks=range(self.HOURS_IN_DAY)
        ax1_label=self.DAY
        ax2_label=self.HOUR
        timeData = PunchCardGrapher.convertTasksToTimeData(taskList)
        # build the array which contains the values
        data = np.zeros((len(ax1),len(ax2)))
        for key in timeData:
            data[key[0],key[1]] = timeData[key]
        data_ax1 = np.sum(data, axis=1)
        data_ax2 = np.sum(data, axis=0)
        data_ax1.shape=(-1,1)
        data_ax2.shape=(1,-1)
        data = data/float(np.max(data))
        data_ax1 = data_ax1/float(np.max(data_ax1))
        data_ax2 = data_ax2/float(np.max(data_ax2))

        # Assign plot to class instance variable
        self.plot = plot
        # shape ratio
        r = float(data.shape[1])/data.shape[0]
        # Draw the punchcard (create one circle per element)
        # Ugly normalisation allows to obtain perfect circles instead of ovals....
        for y in range(data.shape[0]):
            for x in range(data.shape[1]):
                circle = self.plot.Circle((x/float(data.shape[1])*data.shape[0],y/r),#(X,Y)
                                    data[y][x]/float(data.shape[1])*data.shape[0]/2,#Radius
                                    color=self.CIRCLE_COLOR)#DEBUG
                print(circle)#DEBUG
                print("alpha=" + str((data[y][x]/float(data.shape[1])*data.shape[0]/2)*10) + '\n')
                self.plot.gca().add_artist(circle)

        self.plot.ylim(0-0.5,  data.shape[0]-0.5)
        self.plot.xlim(0, data.shape[0])
        self.plot.yticks(np.arange(0,len(ax1)/r-.1,1/r), ax1_ticks)
        self.plot.xticks(np.linspace(0,len(ax1), len(ax2))+0.5/float(data.shape[1]), ax2_ticks)
        self.plot.xlabel(ax1_label)
        self.plot.ylabel(ax2_label)
        self.plot.gca().invert_yaxis()

        # make sure the axes are equal, and resize the canvas to fit the plot
        # self.plot.axis('equal') #Commented out to fix infinite zooming on horizontal stretch
        self.plot.axis([0, 7.02, 7/r, -.5])
        scale = 0.5
        self.plot.gcf().set_size_inches(data.shape[1]*scale,data.shape[0]*scale, forward=True)

    def show(self):
        self.plot.show()

class TaskManager():
    Tasks = {} # { TaskName: [ Task1, Task2, Task3 ] }

    def add(self, task):
        if task.get_name() not in self.Tasks.keys():
            self.Tasks[task.get_name()] = [task]
            return
        self.Tasks[task.get_name()].append(task)

    def get(self, taskName):
        if taskName not in self.Tasks.keys():
            return None
        return self.Tasks[taskName]

    def set(self, taskName, taskData):
        self.Tasks[taskName] = taskData

    def getCurrentWeekStart(self):
        dt = datetime.now()
        return dt - timedelta(days=dt.weekday())

    def getCurrentWeekEnd(self):
        dt = datetime.now()
        start = dt - timedelta(days=dt.weekday())
        return start + timedelta(days=6)

    def calculateHoursSpentInCurrentWeek(self, taskName):
        #Figure out the day of the week, get ctimes between monday and sunday
        #Print summary based on selected task and times that fit between start and end of week
        minimumStartTime = self.getCurrentWeekStart() #get start of week days
        minimumStartTime = datetime(minimumStartTime.year, minimumStartTime.month, minimumStartTime.day) #reset the time to beginning of day
        maximumEndTime = minimumStartTime + timedelta(days=7) #add 24 * 7 hours.. this could be wrong
        hoursThisWeek = 0
        for task in self.get(taskName):
            if task.get_start_time() >= minimumStartTime:
                dur = 0
                if task.get_end_time() is not None:
                    if task.get_end_time() <= maximumEndTime:
                        dur = task.get_duration_in_hours()
                    else:
                        continue
                else:
                    dur = task.get_duration_in_hours(datetime.now())
                hoursThisWeek += dur
        return hoursThisWeek

    def calculateAveragePay(self, taskList, hourlyPay, incomeTax):
        ret = 0
        for task in taskList:
            try:
                ret += (task.get_duration_in_hours() * hourlyPay * (1 - incomeTax))
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
            if task.get_end_time() is None:
                return task
        return None

    def __str__(self):
        return str(self.Tasks)

    def toJson(self, Indent=None):
        Root = []
        for taskList in self.Tasks.values():
            for task in taskList:
                Root.append(task.to_dict())
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
                tStart = Task.date_time_string_to_date_time(i["TaskStart"])
                tEnd = i.get("TaskEnd")
                if tEnd is not None:
                    tEnd = Task.date_time_string_to_date_time(tEnd)
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

    def run(self, args):
        global SAVE_FILE
        if len(args) <= 1:
            print(HELP_DOC)
            return
        try:
            self.load(SAVE_FILE)
        except Exception:
            print("Warning: Loading from save file '{0}' failed!".format(SAVE_FILE))
        first = args[0].lower()
        if first == "punch":
            self.handlePunchArg(args[1:])
        elif first == "list":
            self.handleListArg(args[1:])
        elif first == "print":
            self.handlePrintArg(args[1:])
        elif first == "display":
            self.handleDisplayArg(args[1:])
        elif first == "calc":
            self.handleCalcArg(args[1:])
        else:
            print("Argument Error: Unknown argument '{0}' was specified!".format(first))
            print(HELP_DOC)
        try:
            self.store(SAVE_FILE)
        except Exception as e:
            print("IO Error: Exporting to save file '{0}' failed!".format(SAVE_FILE))

    def handleListArg(self, args):
        first = args[0].lower()
        if first == "tasks":
            print("Tasks:\n")
            for t in self.Tasks.keys():
                print('    "' + t + '"')
            print()
            return
        elif first == "task":
            if len(args) == 2:
                if args[1] in self.Tasks.keys():
                    print("Listing '{0}'\n".format(args[1]))
                    for t in self.Tasks[args[1]]:
                        for l in str(t).split('\n'):
                            print("    " + l)
                        print()
                    return
        print("Argument Error: No argument given to list!")
        print(HELP_DOC)

    def handlePunchArg(self, args):
        if len(args) == 2:
            if args[0][0].lower() == "i":
                try:
                    self.punchIn(args[1])
                except Exception as e:
                    print("Error Punching in: " + str(e))
            elif args[0][0].lower() == "o":
                try:
                    task = self.punchOut(args[1])
                    print("Task Duration = {0} Hrs.".format(task.getDurationInHours()))
                except Exception as e:
                    print("Error Punching out: " + str(e))
            else:
                print("Argument Error: Didn't specify to print in or out!")
                print(HELP_DOC)
        else:
            print("Argument Error: No argument given to punch in or out of!")
            print(HELP_DOC)

    #TODO Actually use the variable avgDurationInSeconds
    #TODO Average start time and end time are broken, you can't Average
    # dates with different days.
    def getTaskSummary(self, taskName):
        try:
            taskList = self.Tasks[taskName]
        except:
            raise Exception("Task {0} doesn't exist!".format(taskName))
        runningTasks = []
        entireDurationInSeconds = 0
        avgStartTimeInSeconds = 0
        avgEndTimeInSeconds = 0
        taskCount = 0
        for t in taskList:
            taskCount += 1
            if t.get_end_time() is None:
                runningTasks.append(t)
                continue
            avgStartTimeInSeconds -= avgStartTimeInSeconds / taskCount
            avgStartTimeInSeconds += t.get_start_time().timestamp() / taskCount
            avgEndTimeInSeconds -= avgEndTimeInSeconds / taskCount
            avgEndTimeInSeconds += t.get_end_time().timestamp() / taskCount
            entireDurationInSeconds += t.get_duration_in_seconds()
        avgDurationInSeconds = (entireDurationInSeconds / taskCount) if taskCount != 0 else 0
        retString = str(taskCount) + " Total Sub-Tasks\n"
        retString += "    {0} Finished\n".format(taskCount - len(runningTasks))
        if len(runningTasks) > 0:
            retString += "    {0} Running\n".format(len(runningTasks))
        for i in range(len(runningTasks)):
            retString += "        Running Sub-Task #{0}\n".format(i + 1)
            retString += "            Started: {0}\n".format(runningTasks[i].get_start_time())
            retString += "            Duration: {0} Hrs.\n".format(runningTasks[i].get_duration_in_hours(datetime.now()))
        retString += "Hours Spent This Week = {0}\n".format(self.calculateHoursSpentInCurrentWeek(taskName))
        retString += "Total Duration = {0}".format(entireDurationInSeconds)
        return retString

    def handlePrintArg(self, args):
        if len(args) >= 1 and args[0].lower() == "summary":
            if len(args) == 1:
                for key in self.Tasks.keys():
                    print("Summary of task '{0}'".format(key))
                    print(self.getTaskSummary(key))
                    print()
            elif len(args) == 2:
                try:
                    tSummary = self.getTaskSummary(args[1])
                    print("Summary of task '{0}'".format(args[1]))
                    print(tSummary)
                    print()
                except Exception as e:
                    print(e)
            else:
                print("Argument Error: Too many arguments given while printing summaries!")

    def handleDisplayArg(self, args):
        if len(args) >= 1 and args[0].lower() == "tasks":
            if len(args) == 1:
                allTasks = []
                for y in self.Tasks.values():
                    for x in y:
                        allTasks.append(x)
                plt = PunchCardGrapher(allTasks)
                plt.show()
            elif len(args) == 2:
                taskList = self.get(args[1])
                if taskList is None:
                    print("Argument Error: The task '{0}' doesn't exist!".format(args[1]))
                    print(HELP_DOC)
                    return
                plt = PunchCardGrapher(taskList)
                plt.show()
            else:
                print("Argument Error: Too many arguments given while displaying tasks!")
                print(HELP_DOC)

    def handleCalcArg(self, args):
        if len(args) >= 4:
            incomeTax = 0
            if len(args) > 5:
                print("Argument Error: Too many arguments given while calculating average pay!")
                print(HELP_DOC)
                return
            elif len(args) == 5:
                try:
                    incomeTax = float(args[4])
                except Exception:
                    pass
            try:
                taskList = self.get(args[2])
                if taskList is None:
                    raise Exception("Argument Error: The task '{0}' doesn't exist!".format(args[2]))
                hourlyPay = float(args[3])
                if hourlyPay < 0 or incomeTax < 0 or incomeTax > 1:
                    raise Exception("Argument Error: Hourly pay must be positive and income tax must be between 1 and 0!")
                print("Your average pay is {0:00}$".format(self.calculateAveragePay(taskList, hourlyPay, incomeTax)))
            except Exception as e:
                print("Calculation Error: " + str(e))
                print(HELP_DOC)
        else:
            print("Argument Error: Not enough arguments given to calculate average pay")
            print(HELP_DOC)

def main():
    global HELP_DOC
    tm = TaskManager()
    HELP_DOC = HELP_DOC.format(sys.argv[0]) # Inject file name into help documentation
    tm.run(sys.argv[1:]) # feed arguments to task manager to run

if __name__ == "__main__":
    main()
