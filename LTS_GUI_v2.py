#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Liquid thermal shock tester front end using Tkinter GUI framework.

Written by: M. Payne
Last modified: 2016-04-14

"""


from Tkinter import Tk, Frame, Label, Button, Text, IntVar
from Tkinter import BOTH, END, CENTER, LEFT, RIGHT, TOP, X, Y, E
from tkFont import Font
import tkMessageBox
from LTS_GUI_Utilities_v2 import *
import subprocess
import threading
import Queue
import sys
from datetime import datetime
import multiprocessing


class TopLevel(Frame):


    def __init__(self, parent):
        Frame.__init__(self, parent, background="gray")
        self.parent = parent
        self.initGlobalVars()
        self.initUI()
        self.detectDebugMode()
        self.set_state_stopped()


    def initGlobalVars(self):
        self.switch_status = 'none'
        self.home_result = IntVar()
        self.move_result = IntVar()
        self.timer_active = IntVar()
        self.test_active = False
        self.test_paused = False

        self.timer = [0, 0]
        self.timer_reset_val = [0, 0]

        #self.active_cycle = 0
        #self.active_temp = 'foo'
        #self.up_motor_res = 2
        #self.right_motor_res = 2
        
        self.move_motor_resolution = 2

        self.up_full_steps = 3200
        self.right_full_steps = 7200
        
        self.debugMode = False
        
        self.event_schedule = []
        
        self.move_total_duration = 0
        self.move_direction = ''
        self.move_started_time = datetime.now()
        self.pause_time = datetime.now()
        self.resume_time = datetime.now()
        self.planned_steps = 0


    def initUI(self):

        self.parent.title('Liquid Thermal Shock Tester v0.2')
        self.pack(fill=BOTH, expand=True)
        options_frame = Frame(self, background='gray', pady=5, padx=5)
        options_frame.pack(side=LEFT, fill=BOTH, expand=True)

        options_label = Label(options_frame, text='Test Setup', background='gray',
                              font=('Courier', 22, 'bold'), justify=LEFT)
        ul_bold_font = Font(options_label, options_label.cget('font'))
        ul_bold_font.configure(underline=True)
        options_label.configure(font=ul_bold_font)
        options_label.pack(anchor=CENTER, side=TOP, padx=5, pady=5)

        cycles_frame = Frame(options_frame, background='gray', pady=5)
        cycles_frame.pack(side=TOP, fill=BOTH, expand=True)
        cycles_frame.columnconfigure(0, weight=1)
        cycles_frame.columnconfigure(1, weight=1)
        cycles_frame.rowconfigure(0, weight=1)
        cycles_frame.rowconfigure(1, weight=1)
        cycles_frame.rowconfigure(2, weight=1)

        cycles_label = Label(cycles_frame, text='# of cycles', background='gray',
                             font=('Courier', 12), justify=CENTER)
        cycles_label.grid(row=0, column=0, rowspan=1, columnspan=2, sticky='news')
        ul_plain_font = Font(cycles_label, cycles_label.cget('font'))
        ul_plain_font.configure(underline=True)
        cycles_label.configure(font=ul_plain_font)

        self.cycles_select_disp = Label(cycles_frame, text='5', background='white',
                                        font=('Courier', 32))
        self.cycles_select_disp.grid(row=1, column=0, rowspan=2, columnspan=1,
                                     sticky='wens', padx=5, pady=5)

        self.cycles_increase_button = Button(cycles_frame, text=u'\u25b2',
                                             font=('Courier', 18, 'bold'),
                                             command=self.cycles_increment)
        self.cycles_increase_button.grid(row=1, column=1, rowspan=1, columnspan=1,
                                         sticky='wens', padx=5, pady=5)

        self.cycles_decrease_button = Button(cycles_frame, text=u'\u25BC',
                                             font=('Courier', 18, 'bold'),
                                             command=self.cycles_decrement)
        self.cycles_decrease_button.grid(row=2, column=1, rowspan=1, columnspan=1,
                                         sticky='wens', padx=5, pady=5)

        self.fix_grid(cycles_frame)

        soak_time_frame = Frame(options_frame, background='gray', pady=5)
        soak_time_frame.pack(side=TOP, fill=BOTH, expand=True)

        soak_time_label = Label(soak_time_frame, text='Minutes per Soak', background='gray',
                                font=('Courier', 12), justify=CENTER)
        soak_time_label.grid(row=0, column=0, rowspan=1, columnspan=2, sticky='news')
        soak_time_label.configure(font=ul_plain_font)

        self.soak_time_disp = Label(soak_time_frame, text='5', background='white',
                                        font=('Courier', 32))
        self.soak_time_disp.grid(row=1, column=0, rowspan=2, columnspan=1,
                                     sticky='wens', padx=5, pady=5)

        self.soak_time_increment_button = Button(soak_time_frame, text=u'\u25b2',
                                             font=('Courier', 18, 'bold'),
                                             command=self.soak_time_increment)
        self.soak_time_increment_button.grid(row=1, column=1, rowspan=1, columnspan=1,
                                            sticky='wens', padx=5, pady=5)

        self.soak_time_decrement_button = Button(soak_time_frame, text=u'\u25BC',
                                                font=('Courier', 18, 'bold'),
                                                command=self.soak_time_decrement)
        self.soak_time_decrement_button.grid(row=2, column=1, rowspan=1, columnspan=1,
                                            sticky='wens', padx=5, pady=5)

        self.fix_grid(soak_time_frame)

        controls_frame = Frame(self, background='gray')
        controls_frame.pack(side=LEFT, fill=BOTH, expand=True)

        run_pause_frame = Frame(controls_frame, background='gray')
        run_pause_frame.pack(side=TOP, fill=BOTH, expand=True, pady=5)

        self.run_button = Button(run_pause_frame, text='RUN', background='green',
                            activebackground='green',
                            font=('Courier', 30, 'bold'), width=5,
                            command=self.run_init)
        self.run_button.grid(row=0, column=0, sticky='wens', padx=5, pady=5)

        self.pause_button = Button(run_pause_frame, text='PAUSE', background='orange',
                            activebackground='orange',
                            font=('Courier', 30, 'bold'), width=5,
                            command=self.pause_button_pressed)
        self.pause_button.grid(row=0, column=1, sticky='wens', padx=5, pady=5)
        self.fix_grid(run_pause_frame)

        stop_button = Button(controls_frame, text='STOP', background='red',
                             activebackground='red',
                             font=('Courier', 36, 'bold'),
                             command=self.stop_test)
        stop_button.pack(side=TOP, fill=BOTH, expand=True, padx=5)

        jog_frame = Frame(controls_frame, background='gray')
        jog_frame.pack(side=TOP, fill=BOTH, expand=True, pady=5)

        jog_label= Label(jog_frame, text='Motor\rjog',
                         font=('Courier', 12, 'bold'),
                         background='gray')
        jog_label.grid(row=1, column=1)

        self.jog_up_button = Button(jog_frame, text=u'\u25b2',
                                    font=('Courier', 18, 'bold'))
        self.jog_up_button.grid(row=0, column=1, rowspan=1, columnspan=1,
                                sticky='wens', padx=5, pady=5)
        self.jog_up_button.bind("<Button-1>", self.jog_up_on)
        self.jog_up_button.bind("<ButtonRelease-1>", self.jog_off)

        self.jog_left_button = Button(jog_frame, text=u'\u25C4',
                                      font=('Courier', 18, 'bold'))
        self.jog_left_button.grid(row=1, column=0, rowspan=1, columnspan=1,
                                  sticky='wens', padx=5, pady=5)
        self.jog_left_button.bind("<Button-1>", self.jog_left_on)
        self.jog_left_button.bind("<ButtonRelease-1>", self.jog_off)

        self.jog_right_button = Button(jog_frame, text=u'\u25BA',
                                       font=('Courier', 18, 'bold'))
        self.jog_right_button.grid(row=1, column=2, rowspan=1, columnspan=1,
                                   sticky='wens', padx=5, pady=5)
        self.jog_right_button.bind("<Button-1>", self.jog_right_on)
        self.jog_right_button.bind("<ButtonRelease-1>", self.jog_off)

        self.jog_down_button = Button(jog_frame, text=u'\u25BC',
                                      font=('Courier', 18, 'bold'))
        self.jog_down_button.grid(row=2, column=1, rowspan=1, columnspan=1,
                                  sticky='wens', padx=5, pady=5)
        self.jog_down_button.bind("<Button-1>", self.jog_down_on)
        self.jog_down_button.bind("<ButtonRelease-1>", self.jog_off)

        self.fix_grid(jog_frame)

        status_frame = Frame(self, background='gray')
        status_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        status_label = Label(status_frame, text='Tester Status', background='gray',
                              font=('Courier', 22, 'bold'), justify=LEFT)
        status_label.configure(font=ul_bold_font)
        status_label.pack(anchor=CENTER, side=TOP, padx=5, pady=5)

        self.status_disp = Text(status_frame)
        self.status_disp.pack(side=TOP, fill=BOTH, padx=5, pady=5)
        self.status_disp.configure(state='disabled')

        self.power_button = Button(status_frame, text='POWER OFF',
                                   font=('Courier', 24, 'bold'),
                                   background="red", activebackground="red",
                                   command=self.shutdown, height=2)
        self.power_button.pack(side=TOP, fill=BOTH, padx=5, pady=5)

        # # Create status variables
        # self.switch_status = 'none'
        # self.home_result = IntVar()
        # self.move_result = IntVar()
        # self.timer_active = IntVar()
        # self.test_active = False

        # self.timer = [0, 0]
        # self.timer_reset_val = [0, 0]

        # self.active_cycle = 0
        # self.active_temp = 'foo'


    def fix_grid(self, target_frame):
        [columns, rows] = target_frame.grid_size()
        for i in range(rows):
            target_frame.rowconfigure(i, weight=1)
        for j in range(columns):
            target_frame.columnconfigure(j, weight=1)


    def detectDebugMode(self):
        if str(sys.argv[0]) == 'debug':
            self.update_status('Tester is in debug mode.', 'newline')
            self.update_status('', 'newline')
            self.update_status('The tester will run with a 6 second', 'newline')
            self.update_status('  soak time regardless of the soak', 'newline')
            self.update_status('  time selected in the GUI.', 'newline')
            self.debugMode = True
        else:
            self.update_status('Welcome to the Liquid Thermal Shock', 'newline')
            self.update_status('  Tester. Select the number of', 'newline')
            self.update_status('  cycles and the soak time per cycle', 'newline')
            self.update_status('  to begin testing. Please ensure', 'newline')
            self.update_status('  that the limit switches are free', 'newline')
            self.update_status('  from obstructions prior to running', 'newline')
            self.update_status('  a test.', 'newline')            
            self.debugMode = False


    def cycles_increment(self):
        """ Increments the number of cycles per test. """

        str_num_cycles = self.cycles_select_disp.cget('text')
        num_cycles = int(str_num_cycles)
        num_cycles += 1
        self.cycles_select_disp.configure(text=str(num_cycles))


    def cycles_decrement(self):
        """ Decrements the number of cycles per test. """

        str_num_cycles = self.cycles_select_disp.cget('text')
        num_cycles = int(str_num_cycles)

        # Check for attempts to set num_cycles < 1.
        if num_cycles <= 1:
            self.cycles_select_disp.configure(text=str(num_cycles))
        else:
            num_cycles -= 1
            self.cycles_select_disp.configure(text=str(num_cycles))


    def soak_time_increment(self):
        """ Increments the soak time. """

        str_soak_time = self.soak_time_disp.cget('text')
        soak_time = int(str_soak_time)
        soak_time += 1
        self.soak_time_disp.configure(text=str(soak_time))
        self.reset_timer()


    def soak_time_decrement(self):
        """ Decrements the soak time. """

        str_soak_time = self.soak_time_disp.cget('text')
        soak_time = int(str_soak_time)

        # Check for attempts to set soak time < 1.
        if soak_time <= 1:
            self.soak_time_disp.configure(text=str(soak_time))
        else:
            soak_time -= 1
            self.soak_time_disp.configure(text=str(soak_time))
        self.reset_timer()


    def reset_timer(self):
        """ Resets the timer to whatever is displayed in the
            soak time window."""

        str_soak_time = self.soak_time_disp.cget('text')

        if self.debugMode:
            self.timer = [0, 6]
        else:
            self.timer = [int(str_soak_time), 0]

        # Use line below for tester debugging -- forces a 5 second soak time.
        # Comment out for normal operations.
        # self.timer = [0, 5]


    # Callback functions for manual motor jog
    def jog_off(self, event):
        motorsOff()

    def jog_up_on(self, event):
        jog_motor('up')

    def jog_down_on(self, event):
        jog_motor('down')

    def jog_left_on(self, event):
        jog_motor('left')

    def jog_right_on(self, event):
        jog_motor('right')


    # Shuts down the tester
    def shutdown(self):
        motorsOff()
        confirm_string = "Do you really want to power down the tester?"
        confirm = tkMessageBox.askokcancel("Shutdown", confirm_string)
        if confirm:
            subprocess.call("sudo poweroff", shell=True)
        else:
            pass


    # Updates the test status window
    def update_status(self, new_text, writemode):
        self.status_disp.configure(state='normal')
        if writemode == 'overwrite':
            #self.status_disp.mark_set('insert', 'end')
            #self.status_disp.delete('current linestart', 'current lineend')
            self.status_disp.delete('end-1c linestart', 'end')
        self.status_disp.insert('end', '\n' + new_text)
        self.status_disp.see(END)
        self.status_disp.configure(state='disabled')


    def append_event(self, cycle, type, destination, direction, steps, duration):
        self.event_schedule.append({'Cycle': cycle,
                                    'Event type': type,
                                    'Destination': destination,
                                    'Direction': direction,
                                    'Steps': steps,
                                    'Duration': duration})


    def start_homing_move(self, direction):
        print('Hello!')        
        self.queue.put_nowait(findHome(direction))  
        

    def find_home(self, direction):
        self.update_status('Finding ' + direction + ' home position...', 'newline')
        self.status_disp.update()
        self.home_result.set(0)
        self.queue = Queue.Queue()
        #self.queue = multiprocessing.Queue()        
        Find_Home_Nonblocking(self.queue, direction).start()
        
#        self.homing_proc = Find_Home_Nonblocking(self.queue, direction)
#        self.homing_proc.run()
        
        self.master.after(100, self.process_homing_queue)
        self.wait_variable(self.home_result)
        if self.home_result.get() == 0:
            self.update_status('Homing error. Test aborted.', 'newline')
            return
        else:
            self.update_status(direction.capitalize() + ' home position found.', 'newline')


    def run_init(self):
        """ Run button callback.  Collects run parameters, creates event
            schedule, then runs the series of scheduled events
        """
        
        self.set_state_running()
        
        # Set number of steps for each motor move. Depends on motor resolution
        # set in static variables section.
        up_steps = self.up_full_steps * (2 ** self.move_motor_resolution)
        right_steps = self.right_full_steps * (2 ** self.move_motor_resolution)

        # Get the total number of cycles
        total_cycles_str = self.cycles_select_disp.cget('text')
        total_cycles_int = int(total_cycles_str)
        
        # Get the soak time in minutes. This is forced to 0.1 minutes when
        # the GUI is launched in debug mode
        if self.debugMode:
            soak_time_str = '0.1'
            soak_time_float = 0.1
        else:
            soak_time_str = self.soak_time_disp.cget('text')
            soak_time_float = float(soak_time_str)
        
        self.event_schedule = []

        for i in range(1, total_cycles_int+1):
            self.append_event(i, 'move', 'hot', 'down', up_steps, up_steps/2000.0)
            self.append_event(i, 'soak', 'hot', '', '', soak_time_float)
            self.append_event(i, 'move', 'cold', 'up', up_steps, up_steps/2000.0)
            self.append_event(i, 'move', 'cold', 'left', right_steps, right_steps/2000.0)
            self.append_event(i, 'move', 'cold', 'down', up_steps, up_steps/2000.0)
            self.append_event(i, 'soak', 'cold', '', '', soak_time_float)
            self.append_event(i, 'move', 'hot', 'up', up_steps, up_steps/2000.0)
            self.append_event(i, 'move', 'hot', 'right', right_steps, right_steps/2000.0)

        self.event_schedule[-2]['Destination'] = 'complete'
        self.event_schedule[-1]['Destination'] = 'complete'
        self.event_schedule[-1]['Steps'] = right_steps/2
        self.event_schedule[-1]['Duration'] = self.event_schedule[-1]['Steps']/2000.0

        self.test_active = True

        # Print initial runtime message to status window
        if soak_time_float == 1.0:
            soak_time_out = '1 minute'
        else:
            soak_time_out = soak_time_str + ' minutes'
        
        self.update_status('', 'newline')
        self.update_status('Test started.', 'newline')
        out_string = 'The tester will run for ' + total_cycles_str + ' cycles, '
        self.update_status(out_string, 'newline')        
        out_string = soak_time_out + ' per cycle.'
        self.update_status(out_string, 'newline')

        if self.test_active == True:
            self.find_home('up')
        if self.test_active == True:
            self.find_home('right')

        self.update_status('Moving to hot position...', 'newline')
        self.run_scheduled_events()


    def run_scheduled_events(self):
        
        #total_cycles = int(self.cycles_select_disp.cget('text'))

        if self.test_active == True:
            
            current_event = self.event_schedule.pop(0)
#            print('Running scheduled event: ')
#            print(current_event)
            #print(current_event)
            #raw_input('breakpoint, enter to continue:')

            if current_event['Event type'] == 'soak':
                self.set_state_running()
                self.reset_timer()
                cycle = str(current_event['Cycle'])
                temperature = current_event['Destination']
                self.timer_active.set(1)
                self.countdown_timer(cycle, temperature)
                self.wait_variable(self.timer_active)

            elif current_event['Event type'] == 'move':

                # Output status message if initiating a move to the next
                # soak position (i.e. when the move direction is 'up')
                if current_event['Direction'] == 'up':
                    self.set_state_running()
                    if current_event['Destination'] == 'complete':
                        out_string = 'Test complete, moving to neutral '
                        out_string += '      position...'
                        self.update_status(out_string, 'newline')
                    else:
                        out_string = 'Moving to ' + current_event['Destination']
                        out_string += ' position...'
                        self.update_status(out_string, 'newline')

                elif current_event['Direction'] == 'down':
                    self.set_state_running()
                        
                else:
                    self.pause_button.config(state='normal')
                    self.move_direction = current_event['Direction']
                    self.move_total_duration = current_event['Duration']
                    self.planned_steps = current_event['Steps']

#                    print('Move planned duration: ')
#                    print(self.move_total_duration)
#                    print('Move planned steps: ')
#                    print(self.planned_steps)

                # Move motor (wrap this in the 'if' statement below to skip the 
                # up & down moves)
                #if current_event['Direction'] == 'right' or current_event['Direction'] == 'left':
                self.move_result.set(0)
                self.queue = Queue.Queue()
#                print('Move start timestamp: ')
                self.move_started_time = datetime.now()
#                print(self.move_started_time)
                Move_Motor_Nonblocking(self.queue, current_event['Direction'],
                                       self.move_motor_resolution,
                                       current_event['Steps']).start()
                self.master.after(100, self.process_move_queue)
                self.wait_variable(self.move_result)
                motorsOff()
                
        # If there are any events left in the schedule, run the next scheduled
        # event.  Otherwise, show 'test complete' message.
        if self.event_schedule:
            self.after(1000, self.run_scheduled_events)
        elif self.move_result.get() == 1:
            self.update_status('Test complete.', 'overwrite')
            self.set_state_stopped()
        else:
            pass

    def set_state_running(self):
        """ Deactivates cycle time select, soak time select, motor jog
            and power off buttons.

            This is to stop users from changing test parameters during a
            running test, which could result in some difficult to handle
            undefined states.
        """
        self.cycles_increase_button.config(state='disabled')
        self.cycles_decrease_button.config(state='disabled')
        self.soak_time_increment_button.config(state='disabled')
        self.soak_time_decrement_button.config(state='disabled')
        self.run_button.config(state='disabled')
        self.jog_up_button.config(state='disabled')
        self.jog_down_button.config(state='disabled')
        self.jog_left_button.config(state='disabled')
        self.jog_right_button.config(state='disabled')
        self.power_button.config(state='disabled')
        self.pause_button.config(state='disabled')

        # This is absurd, but apparently setting a button to 'disabled' does
        # not actually disable the button event bindings, so all this crap
        # below is necessary.
        self.jog_up_button.bind("<Button-1>", self.do_nothing)
        self.jog_up_button.bind("<ButtonRelease-1>", self.do_nothing)
        self.jog_down_button.bind("<Button-1>", self.do_nothing)
        self.jog_down_button.bind("<ButtonRelease-1>", self.do_nothing)
        self.jog_left_button.bind("<Button-1>", self.do_nothing)
        self.jog_left_button.bind("<ButtonRelease-1>", self.do_nothing)
        self.jog_right_button.bind("<Button-1>", self.do_nothing)
        self.jog_right_button.bind("<ButtonRelease-1>", self.do_nothing)


    def set_state_stopped(self):
        """ Reactivates all of the buttons deactivated in the
            set_state_running function.
        """
        
        self.test_active = False
        self.test_paused = False

        self.cycles_increase_button.config(state='normal')
        self.cycles_decrease_button.config(state='normal')
        self.soak_time_increment_button.config(state='normal')
        self.soak_time_decrement_button.config(state='normal')
        self.run_button.config(state='normal')
        self.jog_up_button.config(state='normal')
        self.jog_down_button.config(state='normal')
        self.jog_left_button.config(state='normal')
        self.jog_right_button.config(state='normal')
        self.power_button.config(state='normal')
        self.pause_button.config(state='disabled')        
        self.pause_button.config(text='PAUSE', background='orange',
                                 activebackground='orange')

        self.jog_up_button.bind("<Button-1>", self.jog_up_on)
        self.jog_up_button.bind("<ButtonRelease-1>", self.jog_off)
        self.jog_down_button.bind("<Button-1>", self.jog_down_on)
        self.jog_down_button.bind("<ButtonRelease-1>", self.jog_off)
        self.jog_left_button.bind("<Button-1>", self.jog_left_on)
        self.jog_left_button.bind("<ButtonRelease-1>", self.jog_off)
        self.jog_right_button.bind("<Button-1>", self.jog_right_on)
        self.jog_right_button.bind("<ButtonRelease-1>", self.jog_off)
    
    
    def do_nothing(self, event):
        """ Does absolutely nothing. This is a workaround for the fact that
            button event bindings are not disabled when a button's state is
            set to 'disabled'.
        """
        pass

    
    def pause_timer(self):
        """ Displays the running duration of a test pause. """
        
        if self.test_paused:
            timer_string = '{0:1d}:{1:02d}'.format(self.timer[0],
                                                   self.timer[1])
                                                   
            out_string = 'Test paused for ' + timer_string
            self.update_status(out_string, 'overwrite')
            
            self.timer[1] += 1
            if self.timer[1] >= 60:
                self.timer[0] += 1
                self.timer[1] -= 60
                
            self.after(1000, self.pause_timer)
    

    def countdown_timer(self, cycle, temperature):
        """ Displays countdown timer and current cycle number/temperature
            information in status window.

            This function will only process if the timer_active flag is set to
            1. The function will then recursively call itself after a 1 second
            wait until the timer_active flag is set to zero.

            The timing is not precise because it will wait 1 full second between
            function calls, and therefore does not take into account the time
            necessary to process the function itself. However, over a typical
            soak time this will only amount to milliseconds, so it's certainly
            close enough for this application.
        """

        if self.timer_active.get() == 1:
            timer_string = '{0:1d}:{1:02d}'.format(self.timer[0],
                                                   self.timer[1])
            out_string = 'Cycle ' + cycle + ' of '
            out_string += self.cycles_select_disp.cget('text') + ', '
            out_string += temperature + '. ' + timer_string + ' remaining.'

            self.update_status(out_string, 'overwrite')

            # Decrement 1 second from timer. If this flips the seconds to a
            # negative value, decrement 1 minute and add 60 seconds
            self.timer[1] -= 1
            if self.timer[1] < 0:
                # If timer is run down to zero, display soak complete message
                # and set timer_active flag to zero.
                if self.timer[0] <= 0:
                    out_string = 'Cycle ' + cycle + ' of '
                    out_string += self.cycles_select_disp.cget('text') + ', '
                    out_string += temperature + ' complete.'
                    self.update_status(out_string, 'overwrite')
                    self.timer_active.set(0)
                else:
                    self.timer[0] -= 1
                    self.timer[1] += 60

            # Have the countdown_timer function recursively call itself
            # after 1000ms.
            self.after(1000, self.countdown_timer, cycle, temperature)


    def stop_test(self):
        """ Stop button callback.  Allows user to abort test sequence. """

        # Clear event schedule and toggle home and move result monitoring
        # variables. This helps prevent errors on restart
        motorsOff()        
        self.event_schedule = []
        self.home_result.set(0)
        self.move_result.set(0)
        
        if self.test_active:
            self.update_status('Test stopped by user.', 'newline')

        # Stop and reset timer, reactivate buttons (in case the test
        # needs to be restarted).
        self.timer_active.set(0)
        self.reset_timer()
        self.set_state_stopped()


    def pause_button_pressed(self):        
        if self.test_paused:
            self.test_paused = False            
            self.resume_test()
        else:
            self.test_paused = True
            self.timer = [0, 0]
            self.pause_test()
            
    
    def pause_test(self):
        motorsOff()
        self.pause_time = datetime.now()
#        print('Pause pressed timestamp:')
        
        self.pause_button.config(text='RESUME', background='green',
                                 activebackground='green')
        
#        print(self.pause_time)
        self.resume_schedule = self.event_schedule
        #print('Planned resume schedule: ')
        #for i in self.resume_schedule:
        #    print(i)
        
        self.event_schedule = []        
        self.move_result.set(0)
        pause_delta = self.pause_time - self.move_started_time
        pause_delta_seconds = float(pause_delta.seconds)
        pause_delta_seconds += pause_delta.microseconds/1000000.0

#        print('Move time before pause: ')
#        print(pause_delta_seconds)

        steps_prepause = int(pause_delta_seconds*2000)
#        print('Steps before pause: ')
#        print(steps_prepause)
        
        steps_remaining = self.planned_steps - steps_prepause
#        print('Steps remaining: ')
#        print(steps_remaining)
                
        
        move_time_remaining = self.move_total_duration - pause_delta_seconds
        # steps_remaining = int(move_time_remaining*2000)
        
        resume_event = {'Cycle': '',
                        'Event type': 'move',
                        'Destination': '',
                        'Direction': self.move_direction,
                        'Steps': steps_remaining,
                        'Duration': move_time_remaining}
                        
        self.resume_schedule.insert(0, resume_event)
        
        self.update_status('', 'newline')
        self.pause_timer()
        
        #print('Resume schedule: ')
        #for i in self.resume_schedule:
        #    print(i)

        
    def resume_test(self):
        self.pause_button.config(text='PAUSE', background='orange',
                                 activebackground='orange')
        self.resume_time = datetime.now()
#        print('Resume pressed:')
#        print(self.resume_time)
        self.event_schedule = self.resume_schedule
        
        pause_duration = self.resume_time - self.pause_time
#        print('Pause duration:')
        pause_duration_seconds = float(pause_duration.seconds)
        pause_duration_seconds += pause_duration.microseconds/1000000.0
#        print(str(pause_duration_seconds))
        
#        print('New event schedule: ')
#        for i in self.event_schedule:
#            print(i)
        
#        timer_string = '{0:1d}:{1:02d}'.format(self.timer[0],
#                                               self.timer[1])
#        out_string = 'Test resumed after ' + timer_string + '.'
        
        
        self.test_active = True
        self.update_status('Test resumed.', 'newline')
        self.run_scheduled_events()


    def process_homing_queue(self):
        """ Checks if homing function has returned a value. """

        # Try to read the first value in the queue. If nothing is there, then
        # the homing function has not yet returned a value and must still be
        # active. In this case, the function recursively calls itself after
        # 100ms. If there is something in the queue, the value is read into
        # the self.home_result variable and the function is not called again.
        try:
            ('Reading queue')            
            self.home_result.set(self.queue.get(0))
        except Queue.Empty:
            self.master.after(10, self.process_homing_queue)


    def process_move_queue(self):
        """ Checks if motor move queue as returned value. """

        # Try to read the first value in the queue. If nothing is there, then
        # the motor move function has not yet returned a value and must still be
        # active. In this case, the function recursively calls itself after
        # 100ms. If there is something in the queue, the value is read into
        # the self.move_result variable and the function is not called again.
        
        try:
            self.move_result.set(self.queue.get(0))
        except Queue.Empty:
            self.master.after(100, self.process_move_queue)
        



# The motor moves use the built in sleep function and will therefore lock the
# GUI if they are not spawned in separate threads. This is the only way I could
# figure out to move the motors while still allowing the 'STOP' button to be
# active. The homing and motor move functions return values to the queue, which
# can be checked in the main 'run_test' thread to see if the motor move has
# finished. This allows the (unlocked) GUI to pause and wait for either motor
# move completion or the user pressing the stop button. The interaction between
# threads is still a bit over my head, but it seems to be doing what I want it
# to.

class Find_Home_Nonblocking(threading.Thread):
    def __init__(self, queue, direction):
        threading.Thread.__init__(self)
        self.queue = queue
        self.direction = direction
    def run(self):
        self.queue.put(findHome(self.direction))


class Move_Motor_Nonblocking(threading.Thread):
    def __init__(self, queue, direction, resolution, num_steps):
        threading.Thread.__init__(self)
        self.queue = queue
        self.direction = direction
        self.resolution = resolution
        self.num_steps = num_steps
    def run(self):
        #print('Move start timestamp: ')
        #self.move_started_time = datetime.now()
        #print(self.move_started_time)
        self.queue.put(moveMotor(self.direction, self.resolution,
                                 self.num_steps))


def main():

    root = Tk()

    # Use the if/else statement below if you want to have different window
    # behavior on smaller screens vs. larger.  This will launch the application
    # fullscreen (no window close/minimize/etc. controls available) on screens
    # <= 800px wide (e.g. the 7" 800x480 touchscreen), or as a normal 800x480
    # floating window on larger screens (e.g. over SSH with X-forwarding on
    # a desktop PC).  Comment this block out if for some reason you want to
    # enforce a particular window behavior regardless of screen resolution.
    screen_width = root.winfo_screenwidth()
    if screen_width > 800:
        root.geometry('800x480')
    else:
        root.attributes('-fullscreen', True)

    # Use line below to always launch in fullscreen mode (no window close,
    # minimize or maximize controls available).
    #root.attributes('-fullscreen', True)

    # Use line below to launch as a normal 800x480px floating window.  This
    # should not be used for normal tester operation since it would allow
    # the user to close the GUI and have full access to the underlying OS.
    #root.geometry('800x480')

    app = TopLevel(root)
    root.mainloop()


if __name__ == '__main__':
    main()
