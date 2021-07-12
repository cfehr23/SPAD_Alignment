# William Losin
# 2021-07-11
# ui.py

import PySimpleGUI as sg
import sys
import math
import threading
# from processes import spiralTrnslt

def IButton(*args, **kwargs):
    return sg.Col([[sg.Button(*args, **kwargs)]], pad=(0,0))

#temp
def check(current, caliFact):
    read = read_dmm()
    
    if(read/current>=caliFact):
        return True
    else:
        return False
#temp
def read_dmm():
    return 1
#temp
def spiralTrnslt(ID, step, limit, pstvDir, percent, percentInc, current, sigFact, s):

    #Checks if direction movement along current axis is positive
    if not pstvDir:

        #Sets mode to increment or decrement
        step *= -1

    #Takes number of coarse steps based on cycle count
    for stepNum in range(1, limit+1):

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


class AlignmentUI:
    def __init__(self, dim=24.984, centPos=428800, minRes=0.05):
        #do we want to let the user change these?
        self.dim = dim  # mm
        self.centPos = centPos  # encoder counts
        self.minRes = minRes  # um

        self.darkCur = None

        # self.sigFact = ''
        # self.stepC = ''
        # self.stepLim = ''
        # self.opt = ''
        # self.threshFact = ''

        #TEMPORARY
        self.sigFact = 1
        self.stepC = 1
        self.stepLim = 1
        self.opt = 1
        self.threshFact = 1

    def win_init(self):
        """
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
         photocurrent during alignment
        """  # Maybe add more info here?

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
                for key in values:
                    value = values[key]
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

    def win_manual_alignment(self):
        """
        """

        txt1 = "Manually align with DUT - Press any key to initiate calibration"
        calibrate_txt1 = "Close shutter/block laser - press any key once complete"
        txt2 = "Calibrating..."
        calibrate_txt2 = "Open shutter/unblock laser - press enter once complete\n"+\
                         "Measured dark current for DUT is "  #+ str(darkCur)

        txts = [txt1, calibrate_txt1, txt2]
        txt_i = 0

        # UI layout
        layout = [
            [sg.Text("Manual Alignment")],
            [sg.Text(txts[0], key="-DIALOGUE-")],
            [IButton("Redo Alignment", key="-REDO-", visible=False),
                IButton("Next", key="-NEXT-", visible=False)],
            [sg.Button("Ok", key="-OK-")]
        ]

        # Initialize the new window
        window = sg.Window("SPAD Alignment", layout, return_keyboard_events=True)

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
                    self.darkCur = read_dmm()  ###!!! ENABLE

                    # display the dark current
                    window["-DIALOGUE-"](calibrate_txt2 + str(self.darkCur))

                    #show the buttons to redo alignment or move on
                    window["-REDO-"].update(visible=True)
                    window["-NEXT-"].update(visible=True)
                    window["-OK-"].update(visible=False)

            if event == "-REDO-":
                window.close()
                return 0
            elif event == "-NEXT-":
                window.close()
                return 1

    def win_planar_scan(self, s):
        #value for stage selection (index of stage in list)
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
        percent_text = "Scanning are traversed: %s %%"

        # UI layout
        layout = [
            [sg.Text("Planar Scan Running")],
            [sg.Text(percent_text%(str(percent)), key="-PERCENT-")]
        ]

        # Initialize the new window
        window = sg.Window("SPAD Alignment", layout)

        def UI_thread():
            # Event loop
            while True:
                # Get the events and input values
                event, values = window.read()

                # If the user closes the window, break out of the loop
                if event == sg.WIN_CLOSED or event == 'Exit':
                    window.close()
                    sys.exit()  # closes the entire application

                # using a global variable to kill the thread
                if stop_thread:
                    break

        # Threading to ensure the UI can still be interacted with during the
        #  following processing steps
        stop_thread = False
        UI_thread = threading.Thread(target=UI_thread)
        UI_thread.start()

        #Scan area in spiral pattern (for all complete cycles)
        for cycle in range(1, cycleStop+1):

            #Scan along x and y axes for each cycle
            for count in range(1, 3):

                #Perform intermediate translations/steps
                temp_percent = spiralTrnslt(ID, self.stepC, cycle, True, percent, percentInc,
                                            self.darkCur, self.sigFact, s)

                window["-PERCENT-"](percent_text%(str(temp_percent)))

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
                                    percentInc, self.darkCur, self.sigFact, s)

        #stops the thread
        stop_thread = True
        UI_thread.join()

        #Checks if sufficient signal  to begin multi-axis alignment was not found
        #(during last half cycle)
        #Checks if sufficient signal  to begin multi-axis alignment was not found
        #(at endpoint of scan)
        if not temp_percent and not check(self.darkcur, self.sigFact):
            #alert for user
            sg.popup("Could not locate signal: Realignment required",
                     title="Warning")
            #return to the alignment step
            return 0
        #proceed
        return 1

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


def um():
    UI = AlignmentUI()
    #UI.win_init()

    #Serial numbers for x, y, z translation stages (to be set based on recieved
    #stages)
    # serX =
    # serY =
    # serZ =

    # Initialize list to store actuator/stage instances
    s = []

    #Configure stages and store in list for access
    # stageX = Thorlabs.KinesisMotor(serX)
    # s.append(stageX)

    # stageY = Thorlabs.KinesisMotor(serY)
    # s.append(stageY)

    # stageZ = Thorlabs.KinesisMotor(serZ)
    # s.append(stageZ)

    aligning = True
    while aligning:
        #Ensure that all stages are centred prior to alignment
        for stage in s:
            stage._move_to(UI.centPos)

        #Prompt user to manually align stage until they are satisfied or decide to
        #end entire process
        # while True:
        #     # if False, redo alignment
        #     if UI.win_manual_alignment():
        #         break

        #value for stage selection (index of stage in list)
        ID = 0

        if not UI.win_planar_scan(s):
            aligning = False

    #Initiate Multi-Axis Scan (Coarse Scan)





um()
