from pydmm.pydmm import read_dmm
import math

#_______________________________________________________________________________

#Obtains dark current for DUT (calibrates for specific DUT)
#No parameters

#Returns dark current
def calibrate():

    #Dark current measured with shutter closed (no light on DUT)
    input("Close shutter/block laser - press enter once complete")

    #Will be changed to source meter (placeholder for now)
    readVal = read_dmm()

    #Shutter needs to be reopened for position that results in maximum
    #DUT photocurrent to be located
    input("Open shutter/unblock laser - press enter once complete")

    #DUT dark current
    return readVal

#_______________________________________________________________________________

#Compares current signal to DUT dark current, and checks for exceedance by
#pre-defined factor (which is a good metric to determine signal sufficiency)

#Parameters: Current signal level, DUT dark count

#Returns boolean that indicates if signal is of sufficient strength
def check(current, caliFact):
    read = read_dmm()

    if(read/current>=caliFact):
        return True
    else:
        return False

#_______________________________________________________________________________

#Perform sets of x and y translations for spiral scan

#Parameters: Index of stage to be translated, coarse step size, boolean
#indicating direction of movement along axis, current percent of scan area
#covered, incremental percentage/step, dark current for DUT, noise exceedance
#factor for signal comparison

#Returns True if sufficient signal found, or the percentage of the scan area
#covered otherwise

def spiralTrnslt(ID, step, limit, pstvDir, percent, percentInc, current,\
 sigFact):

    #Checks if direction movement along current axis is positive
    if not pstvDir:

        #Sets mode to increment or decrement
        step *= -1

    #Takes number of coarse steps based on cycle count
    for stepNum in range (1, limit+1):

        #Checks if sufficient signal is found to begin multi-axis alignment
        if check(current, sigFact):
            return True

        #Take coarse step
        s[ID%2]._move_by(step*34.304)

        #Increment/decrement position for current stage based on coarse step
        #and direction
        s[ID%2].posCur += step*34.304

        #Increment percent of area scanned
        percent += percentInc

        print("Scanning area traversed:" + str(percent) + "%")

    #Percentage of scanning area covered
    return percent

#_______________________________________________________________________________

#Perform single-axis coarse optimization/alignment with DUT

#Parameters: Index of stage to be translated,coarse step size,threshold
#factor to define appropriate decline in photocurrent during alignment, step
#count limit

#Returns true if coarse alignment process was uninterupted and false otherwise

def optimizeC(ID, stepC, threshFact, limit):

    #Initialize variables to store current signal reading (at given position),
    #maximum signal level for specific optimization, new optimized position,
    #and edge points beyond which signal intensity is <= 90% of its maximum
    val = max = pos2 = posEdge1 = posEdge2 = 0

    #Initialize variables that define whether previous maximum should be
    #updated, whether the current direction is forward, and if the first edge
    #found (in the positive direction) is correct
    updateMax = forward = edgeCorrect = True

    #Initialize lists to store lists of position-signal reading pairs
    l1 = l2 = []

    #List that stores a single position-signal reading pair
    ltemp = [0,0]

    #Boolean that states whether both boundaries are found
    edgeFind = False

    #Boolean that states whether both true boundaries are found (in the event
    #that they needed to be determined)
    edgeFindTrue = False

    steps = 0

    #Scan along axis until both edge boundaries have been located
    while not edgeFind or steps < limit:

        #Checks if previous maximum can be updated
        if updateMax:

            #Reads and stores value of signal intensity
            val = read_dmm()

        if val > max or not updateMax:

            #Stores current position and signal reading in temporary list
            ltemp[0] = s[ID%3].posCur
            ltemp[1] = val

            #Checks if the current scan direction is forwards
            if forward:

                #Stores list of current position and signal reading into
                #master list containing positions in the positive direction
                #(relative to starting position of optimization)
                l1.append(ltemp)

                #updates current position
                s[ID%3].posCur += stepC*34.304

                #Checks if move would cause stage to exceed its positive limit
                if s[ID%3].posCur >= 857600:

                    #Terminate function
                    return False

                #Makes relative move of coarse step size in positive direction
                s[ID%3]._move_by(stepC*34.304)


            #Current scan direction is backwards
            else:

                #Checks if previous maximum can be updated
                if updateMax:

                    #First edge found was incorrect (determined)
                    edgeCorrect = False

                #Stores list of current position and signal reading into
                #master list containing positions in the negative direction
                #(relative to starting position of optimization)
                l2.append(ltemp)

                #updates current position
                s[ID%3].posCur -= stepC*34.304

                #Checks if move would cause stage to exceed its negative limit
                if s[ID%3].posCur <= 0:

                    #Terminate function
                    return False

                #Makes relative move of coarse step size in negative direction
                s[ID%3]._move_by(-stepC*34.304)

            #Checks if previous maximum can be updated
            if updateMax:

                #Updates maximum value
                max = val

            #Previous maximum cannot be updated
            else:

                updateMax = True

        #Checks if new signal reading is below or equal to a percentage of the
        #maximum reading found so far
        elif val <= max*threshFact:

            #Checks if the current scan direction is forwards
            if forward:

                #Sets positive boundary to current position
                posEdge1 =  s[ID%3].posCur

                #updates current position
                s[ID%3].posCur = s[ID%3].pos1-stepC*34.304

                #Checks if move would cause stage to exceed its negative limit
                if s[ID%3].posCur <= 0:

                    #Terminate function
                    return False

                #Moves to a single coarse step in the negative direction from
                #the optimization starting position
                s[ID%3]._move_to(if s[ID%3].posCur)

                #Sets the scanning direction to backwards
                forward = False

                #Resets step count for current direction
                steps = 0

            else:

                #Sets negative boundary to current position
                posEdge2 = s[ID%3].posCur

                #Both boundaries found
                edgeFind = True

        else:

            #Cannot update maximum value
            updateMax = False

        #Increment step count
        step+=1

    #Checks if loop termination resulted from exceeding iteration limit
    if not edgeFind:

        #Terminate function
        return False

    #New maximum was found after locating first boundary (first boundary
    #must be re-determined)
    if not edgeCorrect:

        #Searches through first list of location-reading pairs to find true
        #positve boundary
        for index in range(len(l1)):

            if l1[index][1] <= max*threshFact:

                posEdge1 = l1[index][0]

                #True edge was found
                edgeFindTrue = False

                break

        if not edgeFindTrue:

            #Searches through second list of location-reading pairs to find true
            #positve boundary
            for index in range(0, len(l2))

                if l2[index][1] <= max*threshFact:

                    posEdge1 = l2[index][0]

                    break

    #Sets coarse optimized position along axis to average of boundary positions
    #(must be centered)
    s[ID%3].pos2 = (s[ID%3].posEdge1 + s[ID%3].posEdge2)/2

    #Moves to coarse optimized position
    s[ID%3]._move_to(s[ID%3].pos2)

    #Updates current position
    s[ID%3].posCur = s[ID%3].pos2
    return True

#_______________________________________________________________________________

#Perform single-axis fine optimization/alignment with DUT

#Parameters: Index of stage to be translated,coarse step size,threshold
#factor to define appropriate decline in photocurrent during alignment, minimum
#actuator resolution
#No return

def optimizeF(ID, stepC, threshFact, minRes):

    #Initialize variables to store current signal reading (at given position),
    #positve boundary, and negative boundary
    val = posEdge1 = posEdge2 = 0

    #Initialize tempary step size to coarse step size
    stepTemp = stepC

    #Value that sets mode to increment or decrement stage position
    num = -1

    print("Optimizing " + str(s[ID].name))

    #Stores signal intensity reading at beginning position of fine scan
    max = read_dmm()

    #Moves to single coarse step from beginning position in positive direction
    s[ID]._move_by(stepC*34.304)

    #Update position
    s[ID].posCur += stepC*34.304

    #Locate both positive and negative edges
    for count in range(1, 3):

        #Performs fine optmization until the step size is reduced to the
        #actuator limit
        while stepTemp != minRes:

            #Decrease the step size by a factor of 2
            stepTemp /= 2

            #Check if new calculated step size is less than or equal to the
            #actuator limit
            if stepTemp <= minRes:

                #Sets new step size to actuator limit
                stepTemp = minRes

            #Reads and stores signal from sourcemeter
            val = read_dmm()

            #Checks if signal level is less than or equal to a percentage of
            #the signal level at the starting position of the fine optimization
            if val <= max*threshdrop:

                #Take step according to new step size
                s[ID]._move_by(num*stepTemp*34.304)

                #Increment or decrement current postition based on current
                #step size and stage direction
                s[ID].posCur += num*stepTemp*34.304


            else:

                #Take step according to new step size
                s[ID]._move_by(-1*num*stepTemp*34.304)

                #Increment or decrement current postition based on current
                #step size and stage direction
                s[ID].posCur += -1*num*stepTemp*34.304

            #Checks if the positive boundary is being located
            if count == 1:

                #Positve boundary is set to current position in positve
                #direction (relative to starting position)
                posEdge1 = s[ID].posCur

            #Negative boundary is being located
            else:

                #Negative boundary is set to current position in negative
                #direction (relative to starting position)
                posEdge2 = s[ID].posCur

        #Checks if the positive boundary has been located
        if count == 1:

            #Moves to single coarse step from beginning position in negative
            #direction
            s[ID]._move_to(s[ID].pos1-stepC*34.304)

            #Reset temporary step size to coarse step size
            stepTemp = step

            #Change incrementation/decrementation mode
            num  = 1

    #Sets fine optimized position along axis to average of boundary positions
    #(must be centered)
    s[ID].pos2 = (s[ID].posEdge1 + s[ID].posEdge2)/2

    #Moves to fine optimized position
    s[ID]._move_to(s[ID].pos2)

    #Updates the current position
    s[ID].posCur = s[ID].pos2

#_______________________________________________________________________________
