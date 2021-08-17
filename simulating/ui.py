# William Losin
# 2021-07-11
# ui.py

import PySimpleGUI as sg
import sys
import math
import threading
from processes import *


def IButton(*args, **kwargs):
    return sg.Col([[sg.Button(*args, **kwargs)]], pad=(0,0))


class AlignmentUI:
    def __init__(self, dim=24.984, max_pos=857600, minRes=0.05):
        # the scan area is 24.984 because of motor movement hysteresis
        self.dim = dim  # mm
        # maximum number of encodings across an axis
        self.max_pos = max_pos # encoder counts
        self.minRes = minRes  # um


        # half of the max encoding
        self.centPos = self.max_pos/2  # encoder counts

        self.darkCur = None

        self.sigFact = ''
        self.stepC = ''
        self.stepLim = ''
        self.opt = ''
        self.threshFact = ''

    def win_init(self):
        """
        The UI that allows the user to input constant values that define
        the scan process
        """

        # Initialization text
        sigFact_text = "Noise exceedance factor (recommended value: 2)"
        stepC_text = "Coarse step size [\u03BCm] (recommended values:)"
        stepLim_text = "Step limit (recommended values:)"
        opt_text = "Cycle count limit (recommended values:)"
        threshFact_text = "Photocurrent threshold [%] (recommended value: 0.9)"

        info_text = """
Noise exceedance factor: Factor to compare device dark current to\
 measured signal current
        \nCoarse step size: for incremental movements in the scan and alignment process
        \nStep limit: Controls maximum number of steps in certain direction for\
 single-axis optimization
        \nCycle count limit: Controls the number of optimization cylces for\
 multi-axis Realignment
        \nPhotocurrent threshold: Factor to define appropriate decline in\
 photocurrent during alignment"""  # Maybe add more info here?

        # UI layout
        layout = [
            [sg.Text("Variable Initialization"), sg.Button("Info")],
            [sg.Text(sigFact_text)],
            [sg.Input(size=(8,1), key='-SIGFACT-')],
            [sg.Text(stepC_text)],
            [sg.Input(size=(8,1), key='-STEPC-')],
            [sg.Text(stepLim_text)],
            [sg.Input(size=(8,1), key='-STEPLIM-')],
            [sg.Text(opt_text)],
            [sg.Input(size=(8,1), key='-OPT-')],
            [sg.Text(threshFact_text)],
            [sg.Input(size=(8,1), key='-THRESHFACT-')],
            [sg.Submit('Submit')]
        ]

        # Initialize the new window
        window = sg.Window("SPAD Alignment", layout)

        # Event loop
        while True:
            # Get the events and input values
            event, values = window.read()

            # If the user closes the window, break out of the loop
            if event == sg.WIN_CLOSED or event == 'Exit':
                window.close()
                sys.exit()  # closes the entire application

            if event == "Info":
                sg.popup(info_text, title="Initialization Info")

            # When the user presses the submit button
            if event == 'Submit':

                ### error checking
                err_msgs = []
                err = False
                # checks if all the values are numbers
                for key, value in values.items():
                    try:
                        float(value)
                        #check if the photocurrent threshold is an acceptable percentage
                        if (key == '-THRESHFACT-') and not (0 < float(value) <= 1):
                            err_msgs.append("The photocurrent threshold entered is not an "
                                            "acceptable percentage")
                            err = True
                    except ValueError:
                        err_msgs.append('Not a number: "%s"'%(value))
                        err = True
                        #clear the invalid input text
                        window[key]('')

                # If there was not an error in the previous loop, break
                #  the event loop
                if err:
                    #popup window with the errors listed
                    sg.popup('\n'.join(err_msgs), title="Warning")
                else:
                    #set the instance variables
                    self.sigFact = float(values['-SIGFACT-'])
                    self.stepC = float(values['-STEPC-'])
                    self.stepLim = float(values['-STEPLIM-'])
                    self.opt = float(values['-OPT-'])
                    self.threshFact = float(values['-THRESHFACT-'])
                    break

        window.close()

    def win_manual_alignment(self, s):
        """
        Prompt user to manually align stage until they are satisfied
        """

        txt1 = "Manually align with DUT - Press any key to initiate calibration"
        calibrate_txt1 = "Close shutter/block laser - press any key once complete"
        txt2 = "Calibrating..."
        calibrate_txt2 = "Open shutter/unblock laser - press enter once complete\n"+\
                         "Measured dark current for DUT is "  #+ str(darkCur)

        # list for cycling between three text segments
        txts = [txt1, calibrate_txt1, txt2]
        txt_i = 0  # index for the cycling

        # UI layout
        layout = [
            [sg.Text("Manual Alignment")],
            [sg.Text(txts[0], key="-DIALOGUE-")],
            [IButton("Redo Alignment", key="-REDO-", visible=False),
                IButton("Next", key="-NEXT-", visible=False)],
            [sg.Button("Ok", key="-OK-")]
        ]

        # Initialize the new window. Include keyboard events to detect key press
        window = sg.Window("SPAD Alignment", layout, return_keyboard_events=True)

        s[0].posCur = self.centPos
        s[1].posCur = self.centPos
        # Event loop
        while True:
            # Get the events and input values
            event, values = window.read()

            # If the user closes the window, break out of the loop
            if event == sg.WIN_CLOSED or event == 'Exit':
                window.close()
                sys.exit()  # closes the entire application

            #on click or on pressing the "ok" button
            if (len(event) == 1) or event == "Ok":
                #move onto the next text option
                txt_i += 1
                window["-DIALOGUE-"](txts[txt_i])

                #to start calibrating
                if txt_i == 2:
                    self.darkCur = read_dmm(s[0].posCur, s[1].posCur)

                    # display the dark current
                    window["-DIALOGUE-"](calibrate_txt2 + str(self.darkCur))

                    #show the buttons to redo alignment or move on
                    window["-REDO-"].update(visible=True)
                    window["-NEXT-"].update(visible=True)
                    window["-OK-"].update(visible=False)
            # redo manual alignment
            if event == "-REDO-":
                window.close()
                return 0
            # move on to the next step
            elif event == "-NEXT-":
                window.close()
                return 1

    def win_planar_scan(self, s):
        """
        """

        # Initial value for stage slection
        ID = 0

        #Compute number of complete x & y translation sets possible
        cycleStop = 2*math.floor(self.dim/(2*self.stepC))

        #Compute number of incremental moves possible
        moves = cycleStop*(cycleStop+2)

        #Initial percentage of total scan area traversed
        percent = 0

        #Percentage increment with each step
        percentInc = 1/moves

        #text describing the current scan percent
        percent_text = "Scanning area traversed: %s %%"

        # UI layout
        layout = [
            [sg.Text("Planar scan running...")],
            [sg.Text(percent_text%(str(percent)), key="-PROGRESS-")]
        ]

        # Initialize the new window
        window = sg.Window("SPAD Alignment", layout)

        # The thread to keep up the UI while other processes are running.
        #  The function needs to be nested if using the global variable to
        #  kill the thread
        stop_thread = False

        def UI_thread():
            # Event loop
            while True:
                # Get the events and input values
                event, values = window.read()

                # If the user closes the window, break out of the loop
                if event == sg.WIN_CLOSED or event == 'Exit':
                    window.close()
                    sys.exit()  # closes the entire application

                # uses a global variable to kill the thread
                if stop_thread:
                    window.close()
                    break

        # Threading to ensure the UI can still be interacted with during the
        #  following processing steps
        UI_thread = threading.Thread(target=UI_thread)
        UI_thread.start()

        #Scan area in spiral pattern (for all complete cycles)
        for cycle in range(1, cycleStop+1):

            #Scan along x and y axes for each cycle
            for count in range(1, 3):

                #Perform intermediate translations/steps
                temp_percent = spiralTrnslt(ID, self.stepC, cycle, True, percent, percentInc,
                                            self.darkCur, self.sigFact, s, window)

                #update the window text with the new scan percent
                window["-PROGRESS-"](percent_text%(str(temp_percent)))  ### COLE
                # ^ is this necessary if this is updated in the spiralTrnslt function itself?

                #Checks if sufficient signal is found to begin multi-axis alignment
                if temp_percent:
                    break

                #Store percentage of scanning region covered so far
                percent = temp_percent

                #Toggle stage/axis of movement
                ID += 1

            #Checks if sufficient signal is found to begin multi-axis alignment
            if temp_percent is True:
                break

        #Perform intermediate translations/steps (for half cycle)
        temp_percent = spiralTrnslt(ID, self.stepC, cycleStop, not cycleStop%2, percent,
                                    percentInc, self.darkCur, self.sigFact, s, window)

        #stops the thread, as scan is complete
        stop_thread = True
        UI_thread.join()

        #Checks if sufficient signal to begin multi-axis alignment was not found
        #(during last half cycle) and (at endpoint of scan)
        if not temp_percent and not check(self.darkcur, self.sigFact, s):
            #alert for user
            sg.popup("Could not locate signal: Realignment required",
                     title="Warning")
            #return to the alignment step
            return 0
        #proceed
        sg.popup('Planar scan complete. Press "ok" to move onto multi-axis scan',
                 title="Planar scan complete")

        return 1

    def win_multi_axis_scan(self, s):
        """
        Performs a multi-axis scan (coarse scan)
        """

        # Initial value for stage selection
        ID = 0

        #Scan type to be performed
        coarseScan = True

        #Assign names for each axis/stage
        s[0].name = "x"
        s[1].name = "y"
        s[2].name = "z"

        #Set initial position for comparison to current position for each axis
        s[0].pos1 = s[0].posCur
        s[1].pos1 = s[1].posCur
        s[2].pos1 = self.centPos

        #Set initial optimization status for each axis to False (not optimized)
        s[0].status = s[1].status = s[2].status = False

        # text that displays which axis is being optimized
        optimize_text = "Optimizing %s"

        # UI layout
        layout = [
            [sg.Text("Multi-axis scan running...")],
            [sg.Text("", key="-OPTIMIZE-")],
        ]

        # Initialize the new window
        window = sg.Window("SPAD Alignment", layout)

        # The thread to keep up the UI while other processes are running.
        #  The function needs to be nested if using the global variable to
        #  kill the thread
        stop_thread = False

        def UI_thread():
            # Event loop
            while True:
                # Get the events and input values
                event, values = window.read()

                # If the user closes the window, break out of the loop
                if event == sg.WIN_CLOSED or event == 'Exit':
                    window.close()
                    sys.exit()  # closes the entire application

                # uses a global variable to kill the thread
                if stop_thread:
                    window.close()
                    break

        # Threading to ensure the UI can still be interacted with during the
        #  following processing steps
        UI_thread = threading.Thread(target=UI_thread)
        UI_thread.start()

        #Loop that continues until all axes are optimized according to coarse step
        while coarseScan:
            ID_i = ID%3
            #Informs user of the current axis being optimized
            window["-OPTIMIZE-"](optimize_text%(str(s[ID_i].name)))

            #Checks if number of optimization cycles exceeds limit for convergence
            if(ID > self.opt):
                #stops the thread, as scan is complete
                stop_thread = True
                UI_thread.join()

                #Terminate coarse scan process
                #Display paremeter selection message to user
                print("Not converging to position - Change parameter choice")

                return 0

            #Attempt to optimize a given axis
            if not optimizeC(ID, self.stepC, self.threshFact, self.stepLim, s):
            #if coarse_scan_result == 1:
                #Terminate coarse scan process
                break
            #if coarse_scan_result == 2:
                #Terminate coarse scan process
            #    break

            #Check if position along axis after optimization is within single
            #coarse step of initial position
            if abs(s[ID_i].pos2-s[ID_i].pos1) <= self.stepC:

                #Set previous position for comparion to new  position along axis
                #determined by optimization
                s[ID%3].pos1 = s[ID_i].pos2

                # current axis optimized (individually). No popup
                print(str(s[ID_i].name + " passes"))

                #Update status of axis to indicate a pass
                s[ID%3].status = True

                #Check if all axes are omptimized
                if all([obj.status for obj in s]):

                    #Change scan state
                    coarseScan = False

                    print()

                    #Signify start of fine scan process
                    sg.popup('All axes passed - Press "ok" to proceed '
                             'to the fine Scan Process', title="Multi-Axis Scan Complete")
                    #stops the thread, as scan is complete
                    stop_thread = True
                    UI_thread.join()

                    return 1

            else:

                #Set previous position for comparion to new position along axis
                #determined by optimization
                s[ID_i].pos1 = s[ID_i].pos2

                #Current axis was not optimized (individually)
                sg.popup(str(s[ID_i].name + " fails - resetting all axes"))

                #Reset all axes to non-optimized state
                s[0].status = s[1].status = s[2].status = False

            #Increment index to optimize next stage (round robin order)
            ID += 1

        #Check if termination occurence does not correspond to switching scan types
        if coarseScan:

            if s[ID_i].posCur <=0 or s[ID_i].posCur >= self.max_pos:

                #stops the thread, as scan is complete
                stop_thread = True
                UI_thread.join()

                #Display Realignment message to user
                print("Stage limit reached - manual Realignment required")

                return 0

    def win_fine_scan(self, s):
        """
        """

        # text that displays which axis is being optimized
        optimize_text = "Optimizing %s"

        # UI layout
        layout = [
            [sg.Text("Multi-axis fine scan running...")],
            [sg.Text("", key="-OPTIMIZE-")],
        ]

        # Initialize the new window
        window = sg.Window("SPAD Alignment", layout)

        # The thread to keep up the UI while other processes are running.
        #  The function needs to be nested if using the global variable to
        #  kill the thread
        stop_thread = False

        def UI_thread():
            # Event loop
            while True:
                # Get the events and input values
                event, values = window.read()

                # If the user closes the window, break out of the loop
                if event == sg.WIN_CLOSED or event == 'Exit':
                    window.close()
                    sys.exit()  # closes the entire application

                # uses a global variable to kill the thread
                if stop_thread:
                    window.close()
                    break

        # Threading to ensure the UI can still be interacted with during the
        #  following processing steps
        UI_thread = threading.Thread(target=UI_thread)
        UI_thread.start()

        for ID in range(3):
            #Informs user of the current axis being optimized
            window["-OPTIMIZE-"](optimize_text%(str(s[ID].name)))

            optimizeF(ID, step, self.threshFact, self.minRes, s)

        sg.popup("Alignment process successfully completed")

    # def win_manual_alignment(self):
    #     # UI layout
    #     layout = [

    #     ]

    #     # Initialize the new window
    #     window = sg.Window("SPAD Alignment", layout)

    #     # Event loop
    #     while True:
    #         # Get the events and input values
    #         event, values = window.read()

    #         # If the user closes the window, break out of the loop
    #         if event == sg.WIN_CLOSED or event == 'Exit':
    #           window.close()
    #           sys.exit()  # closes the entire application

class TestKinesisMotor:
    def __init__(self, serial):
        self.ser = serial
        self.name = ""
        #position before optimization
        self.pos1 = 0
        #position of the optimization
        self.pos2 = 0
        #current postion
        self.posCur = 0
        self.posEdge1 = 0
        self.posEdge2 = 0

    def _move_by(self, step):
        self.posCur += step

    def _move_to(self, location):
        self.posCur = location


def main():
    UI = AlignmentUI(max_pos=1000, minRes=1)

    # The loop is here so that the user can choose to realign without
    #  resetting the entire program
    aligning = True
    while aligning:
        UI.win_init()

        #Serial numbers for x, y, z translation stages (to be set based on recieved
        # #stages)
        serX = 0
        serY = 0
        serZ = 0

        # # # Initialize list to store actuator/stage instances
        s = []

        # #Configure stages and store in list for access
        stageX = Thorlabs.KinesisMotor(serX)
        s.append(stageX)

        # stageY = Thorlabs.KinesisMotor(serY)
        s.append(stageY)

        # stageZ = Thorlabs.KinesisMotor(serZ)
        s.append(stageZ)

        #Ensure that all stages are centred prior to alignment
        for stage in s:
            stage._move_to(UI.centPos)

        #Prompt user to manually align stage until they are satisfied or decide to
        #end entire process
        while True:
            # if False, redo alignment
            if UI.win_manual_alignment(s):
                break

        # Start the planar scan
        if not UI.win_planar_scan(s):
            # if scan fails, go back to manual alignment
            continue

        # # Start the Multi-Axis scan (Coarse Scan)
        # if not UI.win_multi_axis_scan(s):
        #     # if scan fails, go back to manual alignment
        #     continue

    # Proceed with Multi-Axis Scan (fine optimization)
    UI.win_fine_scan(s)

    print(s[0].posCur, s[1].posCur)


#complete
if __name__ == "__main__":
    main()
