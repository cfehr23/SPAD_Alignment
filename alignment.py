
#Main file and algorithm for SPAD alignment

from pylablib.devices import Thorlabs
import math

#constant values that define scan process
#_______________________________________________________________________________
#Factor to compare device dark current to measured signal current
sigFact = input("Enter noise exceedance factor for measurement comparison\
(recommended value: 2)")

#Dimensions of the planar scan area [millimetres]
dim = 24.984

#Absolute center position of a stage [encoder counts]
centPos = 428800

#Coarse step size for scan and alignment processes [micrometres]
stepC = input("Enter coarse step size (\u03BC" + "m) for incremental movements\
 (recommended values:)")

#Limit that controls maximum number of steps in certain direction for
#single-axis optimization
stepLim = input("Enter step limit for single-axis optimization\
(recommended values:)")

#Limit that controls number of optimization cylces for multi-axis Realignment
opt = input("Enter cycle count limit for multi-axis optimization\
 (recommended values:)")

#Threshold factor to define appropriate decline in photocurrent during alignment
threshFact = input("Enter relative intensity factor to set as device\
 photocurrent threshold (recommended value: 0.9)")

#Minimum resolution for actuators (defined limit for (actuator name) ) [micrometres]
minRes = 0.05
#_______________________________________________________________________________

#Serial numbers for x, y, z translation stages (to be set based on recieved
#stages)
serX =
serY =
serZ =

 #Initialize list to store actuator/stage instances
s = []

#Configure stages and store in list for access
stageX = Thorlabs.KinesisMotor(serX)
s.append(stageX)

stageY = Thorlabs.KinesisMotor(serY)
s.append(stageY)

stageZ = Thorlabs.KinesisMotor(serZ)
s.append(stageZ)

#Ensure that all stages are centred prior to alignment
for stage in s:
    stage._move_to(centPos)

#Boolean that indicates whether to continue prompting the user
prompt = True

#Prompt user to manually align stage until they are satisfied or decide to
#end entire process
while prompt:
    input("Manually align with DUT - Press any key to initiate calibration")

    #Gets dark current for DUT
    darkCur = calibrate()

    print("Measured dark current for DUT is " + str(darkCur))

    #Boolean that indicates if user has selected option
    select = False

    response = input("Redo manual alignment: type 'a', proceed to\
     signal detection: type 'b', terminate protocol: type 'c'")

    #Poll for user action
    while not select:

        if response == "a":
            select = True

        elif response == "b":
            select = True
            prompt = False

        elif response == "c":
            end()

        else:
            response = input()

#Initiate Planar Scan
#_______________________________________________________________________________

#Compute number of complete x & y translation sets possible
cycleStop = 2*math.floor(dim/(2*stepC))


plnrScan(stepC, cycleStop, darkCur, sigFact):


#Initiate Multi-Axis Scan (Coarse Scan)
#_______________________________________________________________________________

#value for stage selection
ID = 0

#Scan type to be performed
coarseScan = True

#Assign names for each axis/stage
s[0].name = "x"
s[1].name = "y"
s[2].name = "z"

print("Starting multi-axis scan for laser alignment")

print("Initiating coarse scan process")

#Set initial position for comparison to current position for each axis
s[0].pos1 = s[0].posCur
s[1].pos1 = s[1].posCur
s[2].pos1 = centPos

#Set initial optimization status for each axis to False (not optimized)
s[0].status = s[1].status = s[2].status = False

#Loop that continues until all axes are optimized according to coarse step
while coarseScan:

    #Informs user of the current axis being optimized
    print("Optimizing " + str(s[ID%3].name))

    #Checks if number of optimization cycles exceeds limit for convergence
    if(ID > opt):

        #Terminate coarse scan process
        break

    #Attempt to optimize a given axis
    if not optimizeC(ID, stepC, threshFact, stepLim):

        #Terminate coarse scan process
        break

    #Check if position along axis after optimization is within single
    #coarse step of initial position
    if abs(s[ID%3].pos2-s[ID%3].pos1) <= stepC:

        #Set previous position for comparion to new  position along axis
        #determined by optimization
        s[ID%3].pos1 = s[ID%3].pos2

        #Current axis optimized (individually)
        print(str(s[ID%3].name + " passes"))

        #Update status of axis to indicate a pass
        s[ID%3].status = True

        #Check if all axes are omptimized
        if s[0].status && s[1].status && s[2].status:

            #Change scan state
            coarseScan = False

            #Signify start of fine scan process
            print("\nAll axes passed - Initiating Fine Scan Process")

    else:

        #Set previous position for comparion to new  position along axis
        #determined by optimization
        s[ID%3].pos1 = s[ID%3].pos2

        #Current axis was not optimized (individually)
        print(str(s[ID%3].name + " fails - reset all"))
        print()

        #Reset all axes to non-optimized state
        s[0].status = s[1].status = s[2].status = False

    #Increment index to optimize next stage (round robin order)
    ID += 1

#Check if termination occurence does not correspond to switching scan types
if coarseScan:

    if s[ID%3].posCur <=0 or s[ID%3].posCur >= 857600:

        #Display Realignment message to user
        print("Stage limit reached - manual Realignment required")
        end()

        #Display paremeter selection message to user
        print("Not converging to position - Change parameter choice")
        end()



#Proceed with Multi-Axis Scan (fine optimization)
#_______________________________________________________________________________

#Perform fine optimization on each axis
for ID in range(3):

    #Optimize a single axis
    optimizeF(ID, step, threshFact, minRes)

    #Inform user that process was successful
    print("Alignment process successfully completed")
