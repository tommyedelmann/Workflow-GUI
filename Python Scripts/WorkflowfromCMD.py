import PySimpleGUI as sg
import xml.etree.ElementTree as ET
import os
import webbrowser
import zipfile
from datetime import datetime
import sys
import getopt
import sys, getopt

#versioncontrolsystem
#switchstatements
#github
#newGUI

#This is the main argument function. All code except for the execution is in here,
#including a while-loop that keeps the GUI open.

def main(argv):
   #This block allows/requires the user to start the file from the command prompt by
   #specifying the name of the Python script, the directory for the .xml file, and the .xml file name
   #To run this program, type $python <python file name> -d <xml directory> -f <xml file name>
   inputfile = ''
   outputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hd:f:",["dfile=","ffile="])
   except getopt.GetoptError:
      print('python <python file name> -d <xml directory> -f <xml file name>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
          print('python <python file name> -d <xml directory> -f <xml file name>')
          sys.exit()
      elif opt in ("-d", "--dfile"):
         inputfile = arg
      elif opt in ("-f", "--ffile"):
         outputfile = arg

# ------- XML PARSING/SETUP
   os.chdir(inputfile)
   mytree = ET.parse(outputfile)
   myroot = mytree.getroot()

    #These for loops create lists for the different categories I am drawing from the .xml file
   tasks = []
   for i in myroot.findall('task'):
       tasks.append(i.get('name'))
   maindirlist = []
   for i in myroot.findall('config'):
       maindirlist.append(i.get('maindir'))
   d1d2 = []
   for i in myroot.findall('config'):
       d1d2.append(i.get('D1files'))
       d1d2.append(i.get('D2files'))
   deftheme = []
   for i in myroot.findall('config'):
       deftheme.append(i.get('deftheme'))
   themestring = deftheme[0]
   sg.theme(themestring)

    #The taskcall function goes into the .xml file and can output attributes. i is the
   #index of the task, and key is the name of the attribute.
   def taskcall(i, key):
       return myroot[i].get(key)


# ------- DATA SETUP
   #The following blocks set up all of the starting data for the GUI.
   headings = ['Command', 'Description', 'Status', 'Start Date/Time', 'Logging']
   maindir = maindirlist[0]
   info = [[j for j in range(len(headings))] for i in range(len(tasks))]

   for i in range(len(tasks)):
       info[i][0] = taskcall(i, 'name')
       info[i][2] = 'Pending'
       info[i][3], info[i][4] = '', ''

   for i in range(len(tasks)):
       if taskcall(i, 'type') == 'prod':
           info[i][1] = "Produce two files, '.log' and '.err', in " + maindir + taskcall(i, 'path')
       if taskcall(i, 'type') == 'zip':
           info[i][1] = "Zip all '.log' and '.err' files in " + maindir + taskcall(i, 'path')
       if taskcall(i, 'type') == 'check':
           info[i][1] = "Check if the produced and zipped '.log' and '.err' files exist in " + maindir + taskcall(i,
                                                                                                                  'path') + taskcall(
               i, 'zip')
   original = info[:]

   indexfix = 0
   pausenums = []
   for i in range(len(tasks)):
       if taskcall(i, 'pauseafter') == '1':
           info.insert(i + indexfix + 1,
                       ['Userpause', "To start on next task, press 'Continue " + str(indexfix + 1) + ".'", 'Pending',
                        '', ''])
           pausenums.append(int(i + indexfix + 1))
           indexfix += 1
   newtasknames = []
   for i in range(len(info)):
       newtasknames.append(info[i][0])


# ------- PAUSE SETUP
    #The following code sets up indexes for the program to know where the userpauses will be.
   pauselist = []
   for i in range(0, len(tasks)):
       if taskcall(i, 'pauseafter') == '1':
           pauselist.append(int(taskcall(i, 'id')))
   pauseindex = [[0, pauselist[0]]]
   for i in range(1, len(pauselist)):
       pauseindex.append([pauseindex[i - 1][1] + 1, pauselist[i]])
   pauseindex.append([pauseindex[-1][1] + 1, len(tasks) - 1])

# ------- LAYOUT SETUP
   #This code creates the GUI layout, including where the table and buttons will go.
   menu = [['Edit', ['Change Theme']]]
   layout = [[sg.Menu(menu, )],
             [sg.Button('Start'), sg.Button('Stop')],
             [sg.Table(values=info, headings=headings, max_col_width=60,
                       auto_size_columns=True, justification='left', alternating_row_color='lightblue',

                       key='-TABLE-', change_submits=True)]]
   buttons = []
   for i in range(0, indexfix):
       buttons.append(sg.Button('Continue ' + str(i + 1)))
   layout.append(buttons)

   window = sg.Window('Workflow Manager', layout)

# ------- UPDATE FUNCTIONS
   pausestat = []
   for i in range(0, len(pausenums)):
       pausestat.append('Pending')

   pausetime = []
   for i in range(0, len(pausenums)):
       pausetime.append('')

    #the printtime function allows for easy calling of the date and time.
   #Special parts of this function include 'PM' and 'AM' insertion and the change from a 24 hour clock to a 12 hour one.
   def printtime():
       now = datetime.now()
       if int(now.strftime("%H")) < 12:
           if int(now.strftime("%H")) == 0:
               dt_string = str(now.strftime("%d/%m/%Y 12:%M:%S AM"))
           if int(now.strftime("%H")) > 0:
               dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S AM"))
       if int(now.strftime("%H")) > 12:
           pmhour = str(int(now.strftime("%H")) - 12)
           dt_string = str(now.strftime("%d/%m/%Y " + pmhour + ":%M:%S PM"))
       if int(now.strftime("%H")) == 12:
           dt_string = str(now.strftime("%d/%m/%Y %H:%M:%S PM"))
       return dt_string

    #The update function allows for simpler updates to the GUI while it is running.
   #'loc' is the key of what is being updated, and 'text' is what will be inserted into the spot.
   def Update(loc, text):
       window[loc].update(text)

    #The updatelayout function is very important - it updates the data set without messing up
   #the indexes for pauses.
   def updatelayout(x, y, value):
       original[x][y] = value
       indexfix = 0
       updateinfo = original[:]
       for i in range(len(tasks)):
           if taskcall(i, 'pauseafter') == '1':
               updateinfo.insert(i + indexfix + 1,
                                 ['Userpause', "To start on next task, press 'Continue " + str(indexfix + 1) + ".'",
                                  str(pausestat[indexfix]), pausetime[indexfix], ''])
               indexfix += 1
       Update('-TABLE-', updateinfo)

    #The updatetask function is an easy way to update a task on the GUI after it runs.
   #It will put in the status, print time, and directory for output files.
   def updatetask(status):
       updatelayout(i, 2, status)
       updatelayout(i, 3, printtime())
       updatelayout(i, 4, maindir + taskcall(i, 'path'))

# ------- RUN FUNCTIONS
   progresscounter = 0
    #The runtasks function is what executes the tasks. The special part is that it takes the
   #Type of task (listed as an attribute in the xml) and executes it accordingly.
   def runtasks(i):
       if taskcall(i, 'type') == 'prod':
           os.chdir(maindir + taskcall(i, 'path'))
           os.system(taskcall(i, 'batch'))
           if os.system(taskcall(i, 'batch')) == 0:
               updatetask('Done')
           else:
               updatetask('Failed')
       if taskcall(i, 'type') == 'zip':
           os.chdir(maindir + taskcall(i, 'path'))
           os.system(taskcall(i, 'batch'))
           if os.system(taskcall(i, 'batch')) == 0:
               updatetask('Done')
           else:
               updatetask('Failed')
       if taskcall(i, 'type') == 'check':
           os.chdir(maindir + taskcall(2, 'path'))
           z = zipfile.ZipFile(taskcall(2, 'zip'))
           ziplist = z.namelist()
           if taskcall(2, 'log') in ziplist:
               if taskcall(2, 'error') in ziplist:
                   updatetask('Done')
               else:
                   updatetask('Failed')
           else:
               updatetask('Failed')

# ------- OPEN GUI
   #This section is what runs the GUI and what keeps it open.
   #It includes the prompts for what to do when a particular button is pushed.
   while True:
       event, values = window.read()
       if event == 'Start':
           progresscounter = 0
           for i in range(pauseindex[0][0], pauseindex[0][1] + 1):
               runtasks(i)
               progresscounter += 1

       if event == 'Stop':
           break

       if event == 'Continue 1':
           pausestat[0] = 'Done'
           pausetime[0] = printtime()
           progresscounter += 1
           for i in range(pauseindex[1][0], pauseindex[1][1] + 1):
               runtasks(i)
               progresscounter += 1

       if event == 'Continue 2':
           pausestat[1] = 'Done'
           pausetime[1] = printtime()
           progresscounter += 1
           for i in range(pauseindex[1][0], pauseindex[2][1] + 1):
               runtasks(i)
               progresscounter += 1

       if event == 'Continue 3':
           pausestat[2] = 'Done'
           pausetime[2] = printtime()
           progresscounter += 1
           for i in range(pauseindex[1][0], pauseindex[3][1] + 1):
               runtasks(i)
               progresscounter += 1

       if event == 'Continue 4':
           pausestat[3] = 'Done'
           pausetime[3] = printtime()
           progresscounter += 1
           for i in range(pauseindex[1][0], pauseindex[4][1] + 1):
               runtasks(i)
               progresscounter += 1

       if event == 'Change Theme':
           event, values = changetheme().read(close=True)
           if event == 'Save':
               sg.Print(values['theme'])

    #This 'if event' statement opens the directory file when the user presses on a task row.
    #It will only open the directory if the task has already run, thanks to the 'progresscounter'
       if event == '-TABLE-':
           for i in values['-TABLE-']:
               for f in range(len(tasks)):
                   if i < progresscounter:
                       if newtasknames[i] == taskcall(f, 'name'):
                           webbrowser.open(os.path.realpath((maindir + taskcall(f, 'path'))))
                           sg.Print('Directory from ' + taskcall(f, 'name') + ':   ' + maindir + taskcall(f, 'path'))
                           if taskcall(i, 'path') == 'D1':
                               sg.Print('File names: ' + d1d2[0])
                           if taskcall(i, 'path') == 'D2':
                               sg.Print('File names: ' + d1d2[1])

#Run the main function.
main(sys.argv[1:])
