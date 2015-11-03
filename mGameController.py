"""
mGameController 0.5
GitHub Page: https://github.com/thedixieflatline/mGameController
mGameController an app for the game Assetto Corsa.
Provides the ability to get control inputs from game devices in Assetto Corsa
App developed by David Trenear

Please submit bugs or requests to the Assetto Corsa forum
http://www.assettocorsa.net/forum/index.php

You will need to use the Pygame I have supplied in the source as it is compiled to run in Python 3.3

To activate copy mGameController folder to C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python

This app is more of a tutorial on how to do this. I have developed this for something I am working on in my own Assetto Corsa apps.
I started out to try to find a way to get keyboard an mouse events going with my apps
Pygame does support this through event but because it is based on SDL the event do not fire if there is not a render window running which I do not want to pop up when the game is going
But I found that becasue game devices are separate becasue they are usb they have an independent connection to the event queue they can run windowless
I did most of the code below trying to work out the issues and decide which way to use the features
I thought other app developers would appreciate knowing how to do this and perhaps even use the technique.
I will continue to develop this into a more generic class to handle a lot of this so developers can just plug and go on more easily integrate it into their own work if they wish.
If there is a lot of interest I might even look at adding in serial device support in the future
This code is setup to be a demo and also I have combined some logic together rather than split it all up to make it easier to read
Also some of the processing in the main loop could be moved out and some values stored on start up and not updated every frame
Again this was for readability and to make it easier to follow as well as to show beginners how to handle the inputs and how to scan for and work changes to capabilities of using different devices

I have commented throughout but the best place to start the tutorial from is the acUpdate function near the bottom
First read the comments in acUpdate that explain the 2 ways to get inputs and the pros and cons and features of each method
Then go and look at the 2 different class descriptions. Start with class GameController and then read class DisplayClass
Take note of what happens when each class is initialized and the secondary init of DisplayClass
DisplayClass also contains the 2 functions that run the program and do all of the work.

Here I have put the Pygame object method calls for convenience but you can check out the full docs here

Pygame docs online here http://www.pygame.org/docs/

Possible joystick event types: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
    JOYAXISMOTION    joy, axis, value
    JOYBALLMOTION    joy, ball, rel
    JOYHATMOTION     joy, hat, value
    JOYBUTTONUP      joy, button
    JOYBUTTONDOWN    joy, button

Top level joystick class methods
    pygame.joystick.init	—	Initialize the joystick module.
    pygame.joystick.quit	—	Uninitialize the joystick module.
    pygame.joystick.get_init	—	Returns True if the joystick module is initialized.
    pygame.joystick.get_count	—	Returns the number of joysticks.

joystick object instance methods
    pygame.joystick.Joystick.init	—	initialize the Joystick
    pygame.joystick.Joystick.quit	—	uninitialize the Joystick
    pygame.joystick.Joystick.get_init	—	check if the Joystick is initialized
    pygame.joystick.Joystick.get_id	—	get the Joystick ID
    pygame.joystick.Joystick.get_name	—	get the Joystick system name
    pygame.joystick.Joystick.get_numaxes	—	get the number of axes on a Joystick
    pygame.joystick.Joystick.get_axis	—	get the current position of an axis
    pygame.joystick.Joystick.get_numballs	—	get the number of trackballs on a Joystick
    pygame.joystick.Joystick.get_ball	—	get the relative position of a trackball
    pygame.joystick.Joystick.get_numbuttons	—	get the number of buttons on a Joystick
    pygame.joystick.Joystick.get_button	—	get the current button state
    pygame.joystick.Joystick.get_numhats	—	get the number of hat controls on a Joystick
    pygame.joystick.Joystick.get_hat —	get the position of a joystick hat
"""

""" Add Built In Modules"""
import sys
import os
import os.path
""" Add AC Modules"""
# Use acDevLibs for PyCharm Development from WarriorOfAvalon
# https://github.com/WarriorOfAvalon/AssettoCorsaDevLibs
try:
    import ac
except ImportError:
    from acDevLibs.acDev import ac as ac
try:
    import acsys
except ImportError:
    from acDevLibs.acsysDev import acsys as acsys

#
# Import correct ctypes depending on the platform
#
import os
import sys
import platform
if platform.architecture()[0] == "64bit":
    ctypes_dir = 'stdlib64'
    pygame_dir = 'pygame64'
else:
    ctypes_dir = 'stdlib'
    pygame_dir = 'pygame32'
for d in (ctypes_dir, pygame_dir):
    d = os.path.join(os.path.dirname(__file__), d)
    if d not in sys.path:
        sys.path.insert(0, d)
if '.' not in os.environ['PATH'].split(':'):
    os.environ['PATH'] = os.environ['PATH'] + ";."

import pygame

""" Uncomment CheckPythonPath() to send a list of the python paths to the AC console"""
def CheckPythonPath():
    """Report Modules on Python path"""
    for d in sys.path:
        ac.console("{0}".format(d))
#CheckPythonPath()

""" In this example I have 2 class definitions then create a single instance of each and use them to run the program
    The instance functions are called in the AC onUpdate function below read that first
    Then read through the classes starting with GameController then read DisplayClass

    The GameController class creates an instance that contains the device object as a property and also the total devices detected on the system
    self.device is a Pygame object which is getting the connected/detected game device properties and values from the operating system
    Once the object self.device is created we can call the objects methods from the instance we create of this class
    Most of the calls will be coming from the DisplayClass further down which will be calling the instance name like this gamedevice.device.get_name()

    We need a secondary setInitialStatus function to run after the instance is created and the instance init function has run because
    Pygame needs to be initialised and running first for the device object creation to work correctly"""
class GameController:
    """ Contains the device object and its initialize method """
    def __init__(self):
        """ Will contain the number of devices detected on the system."""
        self.device_count = None
        """ Will contain the device object"""
        self.device = None

    def setInitialStatus(self):
        """ Update the number of devices detected on the system
        You can access this next value I set here directly via (pygame.joystick.get_count()) but I am storing variable here to show how many devices are on the system
        also can be used in main loop (as I do using updateStatus below) to detect when devices are added and removed BUT not while the game is running (See Bellow)
        Because the device order and list would change when devices are added and changed or removed you would have to create support to detect and seup devices on app startup
        by match devices by ID name etc and handle the change of the number of devices and each set of control types in your code :)
        I am only supporting ONE DEVICE at a time in this test code. You can change to different devices if you have several connected (See Bellow)
        I probably will expand this later to handle multiple devices at the same time and switch between
        This is why I am just allowing to set a single device and report the number of devices so you can switch manually or write code to automate switching so I do not have to :)"""

        self.device_count = pygame.joystick.get_count()

        """ The following creates the device object in the specified variable. device number one is set below which is located at 0
            If you have several devices and you want to use a different device, steeering wheel, joystick or game pad change this number (if you have 3 devices connected they would be numbered 0,1,2)
            1st we make sure a compatible device is detected if not then do not create"""

        if (self.device_count == 0 or None):
            """ Here I do nothing if there is no device detected"""
            ac.log("No Gaming Devices detected")

            """ Handling device connect or disconnects at runtime
                I did a lot of testing trying to build a way to handle devices being added or removed in game in a live session
                But what happens is during a session once a wheel or other device is removed and then added back the connection to tyhe wheel gets lost and you have to exit and restart the session anyway
                You can have multiple devices (Up to 8 I think) in Pygame and create code to either statically or dynamically create objects on startup
                But the devices need to be plugged in and ready when the game session starts to be detected properly and if they get pulled during the session then this method of access to the devices breaks as well
                So all that is possible is no devices or a number of devices that are ready when the game starts
                You code must scan the device, query it's type and number of features and values (which will change for different devices) and then setup for your needs accordingly
                you will get errors trying to access properties that do not exist"""
        else:
            """ Create the device object at ID number 0 (the 1st/default device on your USB game device chain
                TO CHANGE TO A DIFFERENT DEVICE CHANGE THIS VALUE ie if you have 3 devices to use the third device set to (2)
                I am only supporting ONE DEVICE in this test code. I probably will expand this later to handle multiple devices at the same time and switch"""

            self.device = pygame.joystick.Joystick(0)

            """ Must initialize the device object before being used, The main reason this function (setInitialStatus) exists and is outside the instance init method is
                Pygame must be started and inititalised so this method will be called after pygame started which is at the bottome of acMain function below"""
            self.device.init()

class DisplayClass:
    """contains the app window, display elements labels and callback functions to run and update the 2 examples object method or event method """
    def __init__(self):
        self.appWindow = None
        """ The object method example properties"""
        self.object_label = None
        self.device_count_label = None
        self.device_get_id_label = None
        self.device_get_name_label = None
        self.device_get_numbuttons_label = None
        self.device_get_button_label = None
        self.axis_string = ""
        self.device_get_numaxes_label = None
        self.device_get_axis_label = None
        self.device_get_axis_label_1 = None
        self.device_get_axis_label_2 = None
        self.device_get_axis_label_3 = None
        self.device_get_axis_label_4 = None
        self.device_get_axis_label_5 = None
        self.device_get_numhats_label = None
        self.device_get_hat_label = None
        self.device_get_numballs_label = None
        self.device_get_ball_label = None
        """ The event method example properties"""
        self.event_label = None
        self.event_Controller_label = None
        self.event_Type_label = None
        self.event_Details_label = None
        self.event_Object_label = None
        """ Assetto Corsa library does not like setting class member functions for these calls so I use a class property which has global scope to point to the functions which works
            There is more information about why I do this below in self.AppActivatedFunction and self.AppDismissedFunction
        """
        self.AppActivated = self.AppActivatedFunction
        self.AppDismissed = self.AppDismissedFunction

    """ The Event method function example
        Both methods use the event queue in pygame but if different ways
        This methods we use the Pygame event system directly rather than getting values from an object instance
        The base Pygame event system requires you to call  pygame.event.pump() to get an event queue update which is a list of events
        You need to run this every frame in acUpdate to get input events every frame and not lose any event objects

        Event objects have an event type and a python dictionary of properties we can read see in the function for how to read an event object

        For this example I check the event queue directly each frame to see if any events have been posted
        We need to check the event queue each frame or we will miss an event as they expire after a while (1-5 seconds)
        After you have read an event list it is removed from the queue so you have to either deal with it straight away or build a system to store it process the results. I am processing event straight away

        The only advantages to the event queue example
        Quick and easy for simple events like buttons
        Offers one piece of information you do not get in the object example such as a separate button UP event (JOYBUTTONUP) as well as the down event

        If you do want to process results every frame for a reasonable number of inputs Pygame is running in its own thread different to AC
        It responds well on cpu and does not drag down the game even when a lot of events coming in

        I would use this method only for simple things like buttons and maybe a few simple readings from axis or hat trackball etc
        If you were going to use this method for simple app features like press a button just use the section grabbing the pygame.JOYBUTTONDOWN event object from the queue
        Read in the button number of the event object and do the rest of you code somewhere else

        More reasons this approach is only for simple things
        You are not aware of how many controllers are on the system and can only get their properties as events come on to the queue
        With the event method you get all the events at once and you have to process them straight away usually in the main loop
        Some information is difficult to get or impossible from the event queue like how manny buttons on a controller on startup
        The event queue can overflow when too many events happen at once so you have to write code for that
        If you write a system to store and process events after doing all of that you may still get into race conditions on event timings
        If for example you want to track all controls on a steering wheel you will have to write a lot of code to chase the main event queue
        when many events and of many types are firing at once and you have to process them each frame if you want real time data"""


    def updateEvent(self):
        """ Loop over all events that are in the queue each frame and process the results of them"""
        for event in pygame.event.get():
            """set display if no controller active"""
            ac.setFontColor(display.event_Controller_label, 1.0, 1.0, 1.0, 1)
            ac.setText(display.event_Controller_label, "Waiting For Event Controller")
            ac.setFontColor(display.event_Type_label, 1.0, 1.0, 1.0, 1)
            ac.setText(display.event_Type_label, "Waiting For Event Type")
            ac.setFontColor(display.event_Details_label, 1.0, 1.0, 1.0, 1)
            ac.setText(display.event_Details_label, "Waiting For Event Details")
            ac.setFontColor(display.event_Object_label, 1.0, 1.0, 1.0, 1)
            ac.setText(display.event_Object_label, "Waiting For Event Object")

            """ Pygame has internal constant names for it's events which when called with event.type return a number eg pygame.JOYBUTTONDOWN returns 10
                If you want a string of the objects name you call the Pygame method pygame.event.event_name(event.type) you must give the event.type which is the int that represents the event type
                The event object that you get will have different properties depending on which event type it is button state, axis, hat, or trackball
                The event object details are stored as a python dictionary that you can loop over or access the values directly.
                Using old school python dictionary access method
                event.dict['button']
                returns the button number pressed
                Using dot notation works as well
                event.button
                returns the button number pressed
                I will use both a few times below to show how it is done

                For reference here are examples of each event object type

                Button up - Event type is 11 (int) event name is JoyButtonUp (string) joy 0 (int) is the controller number that sent the event button (int) is the button number pressed
                <Event(11-JoyButtonUp{'joy':0,'button':5})>

                Button down
                <Event(10-JoyButtonDown{'joy':0,'button':5})>

                Axis movement- Event type is 7 (int) event name is JoyAxisMotion (string) axis (int) the axis that moved value returns a float joy 0 (int) is the controller number that sent the event
                <Event(7-JoyAxisMotion{'axis':0,'value':0,'joy':0})>

                Hat movement - Event type is 9 (int) event name is JoyHatMotion (string) joy 0 (int) is the controller number that sent the event
                value returns a tuple with 5 different states
                (0,0) no hat is pressed
                (1,0) pressed to the right
                (-1,0) pressed left
                (0,1) pressed up
                (0,-1) pressed down
                hat (int) the hat that moved
                <Event(9-JoyHatMotion{'joy':0,'value':(1,0),'hat':0})>

                Trackball movement - Event type is 9 (int) event name is JoyBallMotion joy 0 (int) is the controller number that sent the event (string)
                ball (int) in the trackball controller number that sent the event rel (float {not sure about this value I do not have a trackball perhaps somebody can tell me this}) the relative position of a trackball
                <Event(8-JoyBallMotion{'joy':0,'ball':0,'rel':0})>

                I have noticed in testing that the float values on the axis can sometimes be rounded using the event version and the values at other time differ slightly
                I figure this is becasue I am capturing the events at slightly different times for both the object and event method functions
                I assume if they were all processed together the values would be the same. Going to do some more testing of this later

                Get the event type and process it for the first one I will use old school python dict method to get values"""
            if(event.type == pygame.JOYBUTTONDOWN):
                ac.setFontColor(display.event_Controller_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Controller_label, "Controller {0}".format(event.dict['joy']))
                ac.setFontColor(display.event_Type_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Type_label, "Event Type: {0} --- Event Name: {1}".format(event.type,pygame.event.event_name(event.type)))
                ac.setFontColor(display.event_Details_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Details_label, "Button {0} Pressed from controller {1}".format(event.dict['button'],event.dict['joy']))
                ac.setFontColor(display.event_Object_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Object_label, "Event Object {0}".format(event))
                """Now I will use the dot notation method"""
            elif(event.type == pygame.JOYBUTTONUP ):
                ac.setFontColor(display.event_Controller_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Controller_label, "Controller {0}".format(event.joy))
                ac.setFontColor(display.event_Type_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Type_label, "Event Type: {0} --- Event Name: {1}".format(event.type,pygame.event.event_name(event.type)))
                ac.setFontColor(display.event_Details_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Details_label, "Button {0} Released from controller {1}".format(event.button,event.joy))
                ac.setFontColor(display.event_Object_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Object_label, "Event Object {0}".format(event))
            elif(event.type == pygame.JOYAXISMOTION ):
                ac.setFontColor(display.event_Controller_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Controller_label, "Controller {0}".format(event.joy))
                ac.setFontColor(display.event_Type_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Type_label, "Event Type: {0} --- Event Name: {1}".format(event.type,pygame.event.event_name(event.type)))
                ac.setFontColor(display.event_Details_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Details_label, "Axis Num: {0} Axis Value: {1}".format(event.axis,event.value))
                ac.setFontColor(display.event_Object_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Object_label, "Event Object {0}".format(event))
            elif(event.type == pygame.JOYHATMOTION ):
                ac.setFontColor(display.event_Controller_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Controller_label, "Controller {0}".format(event.joy))
                ac.setFontColor(display.event_Type_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Type_label, "Event Type: {0} --- Event Name: {1}".format(event.type,pygame.event.event_name(event.type)))
                ac.setFontColor(display.event_Details_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Details_label, "Hat Num: {0} Position: {1}".format(event.hat,event.value))
                ac.setFontColor(display.event_Object_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Object_label, "Event Object {0}".format(event))
            elif(event.type == pygame.JOYBALLMOTION ):
                ac.setFontColor(display.event_Controller_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Controller_label, "Controller {0}".format(event.joy))
                ac.setFontColor(display.event_Type_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Type_label, "Event Type: {0} --- Event Name: {1}".format(event.type,pygame.event.event_name(event.type)))
                ac.setFontColor(display.event_Details_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Details_label, "Ball Num: {0} Value: {1}".format(event.ball,event.rel))
                ac.setFontColor(display.event_Object_label, 0.0, 1.0, 0.1, 1)
                ac.setText(display.event_Object_label, "Event Object {0}".format(event))

    """ The object method function example
        This is the better of the two methods if you want to do more complex and reliable systems.
        This method still uses the Pygame event system
        We still need to refresh the Pygame event queue every frame in acUpdate using pygame.event.pump()
        Both approaches require this in the main loop to update events each frame from device inputs
        But our GameController instance gamedevice.device is now a global Pygame object that is semi independent of the event queue
        It takes care of it's own events and allows you to query them also it forwards it's status to the main event queue every time pygame.event.pump() is called

        The big difference between the object method and the event method then is
        Has global AC python method call returning properties on the object
        Is portable as a class object
        We do not have to write our own functions to get the data from events and ensure the accuracy of data and timing it is batteries included
        Does not need to be checked every frame if required, we just get the values when we need them and calling pygame.event.pump() in acUpdate means the value will always be current
        Provides information that is difficult to get or impossible from the event queue like how manny button on a controller
        Allows us to get all of the device properties and handle them on startup ready to be used in app even if the properties change because of using a different device
        Do not have to write a lot of code to chase the main event queue when many events and of many types are firing at once and you have to process them each frame

    """
    def updateObject(self):
        """Update the the gameController instance with the number of devices attached on the system You do not have to do this every frame but I am anyway
            If you read the gameController class information first you know now we cannot rescan changes to usb devices when the game is in a session we have to quit the session and restart
            So reading this in at the startup is probably all you will need"""
        gamedevice.device_count = pygame.joystick.get_count()
        """ I am only supporting ONE DEVICE at a time in this code. To change the device read the gameController class to see how to switch devices
            If at least one device is detected then get and update values and properties of device"""
        if(gamedevice.device_count != 0 or None):
            """Update label with the value from the number of devices connected value that we have in the gameController instance"""
            ac.setText(display.device_count_label, "Total Detected Devices : {0}".format(gamedevice.device_count))

            """Start to get the values from the device number one, created in setInitialStatus above (instance name is gamedevice.device)
                We can now call the instance methods (listed at the top of this script^^^^) on the device to get values for each of it's properties
                Set labels to show device id gamedevice.device.get_id() and device name gamedevice.device.get_name()"""
            ac.setText(display.device_get_id_label, "Device ID : {0}".format(gamedevice.device.get_id()))
            ac.setText(display.device_get_name_label, "Device Name : {0}".format(gamedevice.device.get_name()))

            """ Now we have to scan through the device features as each device will have a different set of buttons axis hats etc
                A lot of this could be done once on startup then just updated by the main loop
                I am doing it all here to make it more readable and easier to understand and the program logic better for beginners
                you could also split out the checking for event logic and display stuff out of the main loop
                into different functions and some of it does not need to be updated in the main loop all the time
                I have not built in support here for multiple keys pressed at the same time although it does work
                I might expand this script later to be more generic and to handle multiple devices at the same time and switch between
                So now I will scan down the available features and values and update the values to the labels and add in a little display logic to make it pretty
                Now we check to see if there are any buttons, I assume all controllers would have at least one but you never know!

                Check to see if there are any button controls
                Update labels with number of buttons detected if number of button controllers does not equal zero

                """
            if(gamedevice.device.get_numbuttons() != 0):
                """ This condition is where I will now take the number of reported button presses which we get as a boolean values for each button pressed
                    loop over the total reported buttons available for the device to see if I got a key press
                    Print the result to the label and change the label colour
                    Not supporting multiple keys press at same time in this code but first key is still there after the second is released works ok so far
                    Button event using this method is just button DOWN event
                    To get key UP event ou have to use the event example function so you need to use that as well if you want key UP events
                First we update label with the number of available buttons"""
                ac.setText(display.device_get_numbuttons_label, "Total Buttons : {0}".format(gamedevice.device.get_numbuttons()))

                """ Update label and colour if no buttons are being pressed right now"""
                ac.setText(display.device_get_button_label, "Press or Hold Button")
                ac.setFontColor(display.device_get_button_label, 1.0, 0.0, 0.0, 1)

                """ Now in this first button example I will use a for loop to go over only the number of buttons available on the device stored in gamedevice.device.get_numbuttons()
                    if a button has given a true boolean for being pressed then we set the label colour and display which number pressed
                    Run the loop which displays only the number of hats available"""
                for i in range(gamedevice.device.get_numbuttons()):
                    """If a button has been pressed"""
                    if(gamedevice.device.get_button(i)):
                        ac.setFontColor(display.device_get_button_label, 0.0, 1.0, 0.1, 1)
                        ac.setText(display.device_get_button_label, "Button {0} Pressed".format(i))
            else:
                """ Update labels and colours if no buttons detected on device"""
                ac.setText(display.device_get_numbuttons_label, "No Button Controller Found")
                ac.setFontColor(display.device_get_numbuttons_label, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_button_label, "No Button Controller Found")
                ac.setFontColor(display.device_get_button_label, 0.6, 0.6, 1.0, 1)

            """ Check to see if there are any axis controls
                Update labels with number of axis detected if number of axis controllers does not equal zero"""
            if(gamedevice.device.get_numaxes() != 0):
                """Update labels with number of axis detected if number of controllers does not equal zero"""
                ac.setText(display.device_get_numaxes_label, "Axis Count: {0}".format(gamedevice.device.get_numaxes()))

                """ Draw something if no axis is moving"""
                ac.setText(display.device_get_axis_label, "Move An Axis")
                ac.setFontColor(display.device_get_axis_label, 1.0, 0.0, 0.0, 1)

                """ Must reset the string variable here before the loop starts so that we only print 1 loop set of values or string will overflow with every single value ever detected"""
                self.axis_string = ""

                """ Run the loop example again which reads only the axis available on the device"""
                for i in range(gamedevice.device.get_numaxes()):
                    """ If axis is used"""
                    if(gamedevice.device.get_axis(i)):
                        """Add values found for all axis into string (self.axis_string) then display"""
                        ac.setFontColor(display.device_get_axis_label, 1.0, 1.0, 0.1, 1)
                        self.axis_string += "Axis {0} Value: {1} | ".format(i,gamedevice.device.get_axis(i))
                        ac.setText(display.device_get_axis_label, self.axis_string)

                """ This next code is to show an if/else condition statement example 5 axis controls
                    if there are more than 5 Axis on a device this would break or stop the script as there are not enough variables and display controls and checking for the valeus would give and error
                    You can write code in python to handle this but it is complicated
                    To use a conditional like this you would need to build in your own handler to scan a device proporties and controllers first
                    an have enough label objects and variables for the number of device axis reported by gamedevice.device.get_numaxes()
                    For now COMMENT THIS CONDITIONAL OUT IF YOU ARE USING A DEVICE WITH MORE THAN 5 AXIS or write in the extra objects :)

                If the first axis has a true condition because it was moved then display the value"""
                if(gamedevice.device.get_axis(0)):
                    """Get axis 1 value and set the label if an axis is used by the device"""
                    ac.setText(display.device_get_axis_label_1, "Axis 0 Value: {0}".format(gamedevice.device.get_axis(0)))
                elif(gamedevice.device.get_axis(0) == 0.0):
                    """Display this if an axis is NOT used by the device The value of the axis will give a value of 0.0 which means it is detected but not being used"""
                    ac.setText(display.device_get_axis_label_1, "Axis 0 Not Used")
                if(gamedevice.device.get_axis(1)):
                    ac.setText(display.device_get_axis_label_2, "Axis 1 Value: {0}".format(gamedevice.device.get_axis(1)))
                elif(gamedevice.device.get_axis(1) == 0.0):
                    ac.setText(display.device_get_axis_label_2, "Axis 1 Not Used")
                if(gamedevice.device.get_axis(2)):
                    ac.setText(display.device_get_axis_label_3, "Axis 2 Value: {0}".format(gamedevice.device.get_axis(2)))
                elif(gamedevice.device.get_axis(2) == 0.0):
                    ac.setText(display.device_get_axis_label_3, "Axis 2 Not Used")
                if(gamedevice.device.get_axis(3)):
                    ac.setText(display.device_get_axis_label_4, "Axis 3 Value: {0}".format(gamedevice.device.get_axis(3)))
                elif(gamedevice.device.get_axis(3) == 0.0):
                    ac.setText(display.device_get_axis_label_4, "Axis 3 Not Used")
                if(gamedevice.device.get_axis(4)):
                    ac.setText(display.device_get_axis_label_5, "Axis 4 Value: {0}".format(gamedevice.device.get_axis(4)))
                elif(gamedevice.device.get_axis(4) == 0.0):
                    ac.setText(display.device_get_axis_label_5, "Axis 4 Not Used")
            else:
                """ Update to this if no axis controller detected on device"""
                ac.setText(display.device_get_numaxes_label, "No Axis Controller Found")
                ac.setFontColor(display.device_get_numaxes_label, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_axis_label, "No Axis Found")
                ac.setFontColor(display.device_get_axis_label, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_axis_label_1, "Axis 1 Not Found")
                ac.setFontColor(display.device_get_axis_label_1, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_axis_label_2, "Axis 2 Not Found")
                ac.setFontColor(display.device_get_axis_label_2, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_axis_label_3, "Axis 3 Not Found")
                ac.setFontColor(display.device_get_axis_label_3, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_axis_label_4, "Axis 4 Not Found")
                ac.setFontColor(display.device_get_axis_label_4, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_axis_label_5, "Axis 5 Not Found")
                ac.setFontColor(display.device_get_axis_label_5, 0.6, 0.6, 1.0, 1)

            """ Check to see if there are any hat controls
                Update labels with number of hats detected if number of hat controllers does not equal zero"""
            if(gamedevice.device.get_numhats() != 0):
                """ Update label with number of hat detected """
                ac.setText(display.device_get_numhats_label, "Hat Count : {0}".format(gamedevice.device.get_numhats()))

                # """ Set label with this until a hat is pressed"""
                # ac.setText(display.device_get_hat_label, "Move The Hat")
                # ac.setFontColor(display.device_get_hat_label, 1.0, 0.0, 0.0, 1)

                """ Run the loop which reads in only the number of hats available"""
                for i in range(gamedevice.device.get_numhats()):
                    """If the hat had been pressed"""
                    if(gamedevice.device.get_hat(i)):
                        if (gamedevice.device.get_hat(i) == (0,0)):
                            """If the hat returns tuple of 0,0 no hat is pressed"""
                            ac.setText(display.device_get_hat_label, "Move The Hat")
                            ac.setFontColor(display.device_get_hat_label, 1.0, 0.0, 0.0, 1)
                        elif (gamedevice.device.get_hat(i) == (1,0)):
                            """"If the hat returns tuple of 1,0 hat is pressed to the right"""
                            ac.setText(display.device_get_hat_label, "Right Hat Pressed - Value : {0}".format(gamedevice.device.get_hat(i)))
                            ac.setFontColor(display.device_get_hat_label, 0.0, 1.0, 0.1, 1)
                        elif (gamedevice.device.get_hat(i) == (-1,0)):
                            """"If the hat gives returns tuple of -1,0 hat is pressed left"""
                            ac.setText(display.device_get_hat_label, "Left Hat Pressed - Value : {0}".format(gamedevice.device.get_hat(i)))
                            ac.setFontColor(display.device_get_hat_label, 0.0, 1.0, 0.1, 1)
                        elif (gamedevice.device.get_hat(i) == (0,1)):
                            """"If the hat returns tuple of 0,1 hat is pressed up"""
                            ac.setText(display.device_get_hat_label, "Up Hat Pressed - Value : {0}".format(gamedevice.device.get_hat(i)))
                            ac.setFontColor(display.device_get_hat_label, 0.0, 1.0, 0.1, 1)
                        elif (gamedevice.device.get_hat(i) == (0,-1)):
                            """"If the hat gives returns tuple of 0,-1 hat is pressed down"""
                            ac.setText(display.device_get_hat_label, "Down Hat Pressed - Value : {0}".format(gamedevice.device.get_hat(i)))
                            ac.setFontColor(display.device_get_hat_label, 0.0, 1.0, 0.1, 1)
            else:
                """ Update to this if no hat controller detected on device"""
                ac.setText(display.device_get_numhats_label, "No Hat Controller Detected")
                ac.setFontColor(display.device_get_numhats_label, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_hat_label, "No Hat Controller Detected")
                ac.setFontColor(display.device_get_hat_label, 0.6, 0.6, 1.0, 1)

            """Check to see if there are any trackball controls
                Update labels with number of buttons detected if number of button controllers does not equal zero"""
            if(gamedevice.device.get_numballs() != 0):
                """ Update label with number of trackballs detected"""
                ac.setText(display.device_get_numballs_label, "Track Ball Count : {0}".format(gamedevice.device.get_numballs()))
                """ Run the loop which reads in only the number of trackballs available"""
                for i in range(gamedevice.device.get_numballs()):
                    """If the trackball had been moved"""
                    if(gamedevice.device.get_ball(i)):
                        ac.setText(display.device_get_ball_label, "Track Ball Value : {0}".format(gamedevice.device.get_ball(i)))
            else:
                """ Update to this if no trackball controller detected on device"""
                ac.setText(display.device_get_numballs_label, "No Trackball Controller Detected")
                ac.setFontColor(display.device_get_numballs_label, 0.6, 0.6, 1.0, 1)
                ac.setText(display.device_get_ball_label, "No Trackball Controller Detected")
                ac.setFontColor(display.device_get_ball_label, 0.6, 0.6, 1.0, 1)
        else:
            """ If no device attached or detected only update the labels to display this"""
            ac.setText(display.device_count_label, "Total Detected Devices : {0}".format(gamedevice.device_count))
            ac.setText(display.device_get_id_label, "Device ID : No Compatible Device Connected")
            ac.setFontColor(display.device_get_id_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_name_label, "Device Name : No Compatible Device Connected")
            ac.setFontColor(display.device_get_name_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_numbuttons_label, "No Button Controller Detected")
            ac.setFontColor(display.device_get_numbuttons_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_button_label, "No Button Controller Detected")
            ac.setFontColor(display.device_get_button_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_numaxes_label, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_numaxes_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_axis_label, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_axis_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_axis_label_1, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_axis_label_1, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_axis_label_2, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_axis_label_2, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_axis_label_3, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_axis_label_3, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_axis_label_4, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_axis_label_4, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_axis_label_5, "No Axis Controller Detected")
            ac.setFontColor(display.device_get_axis_label_5, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_numhats_label, "No Hat Controller Detected")
            ac.setFontColor(display.device_get_numhats_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_hat_label, "No Hat Controller Detected")
            ac.setFontColor(display.device_get_hat_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_numballs_label, "No Trackball Controller Detected")
            ac.setFontColor(display.device_get_numballs_label, 0.6, 0.6, 1.0, 1)
            ac.setText(display.device_get_ball_label, "No Trackball Controller Detected")
            ac.setFontColor(display.device_get_ball_label, 0.6, 0.6, 1.0, 1)

    def AppActivatedFunction(self,val):
        """Restart Pygame"""
        pygame.init()
        """ Then set initial status on gamedevice instance which can now create the device object because pygame is running """
        gamedevice.setInitialStatus()

    def AppDismissedFunction(self,val):
        """on AppDismissed quit pygame so no crash or lockup."""
        pygame.quit()

        """ Only problem I have found with using classes in AC python is that display controls which use a callback function do not seem to have global scope when called directly and fail
            In those cases I create a class property (self.MySpinnerEvent) and pass internally to the function itself and then AC can call this function globally OK as a class property
            The function call requires the x argument (self,x) as a reference to the callback is passed and without it there it fails
            You can access x if you want or not but the function with run

            class MyClass:
                def __init__(self):
                    self.MySpinnerEvent = self.SpinnerEventFunction

                def SpinnerEventFunction(self,x):
                    ac.console("Spinner Said Hello World")

            theclass = MyClass()
            Spinner = ac.addSpinner(Display.appWindow, "A Spinner")
            ac.setPosition(Display.Spinner,32,62)
            ac.addOnValueChangeListener(Spinner,theclass.MySpinnerEvent)
        """

""" Create class instance objects - Do gamedevice first as it's properties are required by display instance """
gamedevice = GameController()
display = DisplayClass()

def acMain(ac_version):
    """ main init function which runs on game startup.
    Initialize AC display form in display class instance property display.appWindow
    Set the forms app Activated and Dismissed callback functions
    Initialize the AC widgets instance properties in the display instance
    """
    display.appWindow = ac.newApp("mGameController")
    ac.addOnAppActivatedListener(display.appWindow, display.AppActivated)
    ac.addOnAppDismissedListener(display.appWindow, display.AppDismissed)
    ac.setSize(display.appWindow, 1000, 550)

    display.object_label = ac.addLabel(display.appWindow, "The Object Properties Example - read mGameController.py for more detail")
    ac.setPosition(display.object_label, 10, 40)
    ac.setFontColor(display.object_label, 0.0, 0.85, 0.85, 1)
    ac.setFontAlignment(display.object_label,'left')

    display.device_count_label = ac.addLabel(display.appWindow, "device_count")
    ac.setPosition(display.device_count_label, 10, 60)
    ac.setFontColor(display.device_count_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_count_label,'left')

    display.device_get_id_label = ac.addLabel(display.appWindow, "device_get_id")
    ac.setPosition(display.device_get_id_label, 10, 80)
    ac.setFontColor(display.device_get_id_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_id_label,'left')

    display.device_get_name_label = ac.addLabel(display.appWindow, "device_get_name")
    ac.setPosition(display.device_get_name_label, 10, 100)
    ac.setFontColor(display.device_get_name_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_name_label,'left')

    display.device_get_numbuttons_label = ac.addLabel(display.appWindow, "device_get_numbuttons")
    ac.setPosition(display.device_get_numbuttons_label, 10, 130)
    ac.setFontColor(display.device_get_numbuttons_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_numbuttons_label,'left')

    display.device_get_button_label = ac.addLabel(display.appWindow, "device_get_button")
    ac.setPosition(display.device_get_button_label, 10, 150)
    ac.setFontColor(display.device_get_button_label, 1.0, 0.0, 0.0, 1)
    ac.setFontAlignment(display.device_get_button_label,'left')

    display.device_get_numaxes_label = ac.addLabel(display.appWindow, "device_get_numaxes")
    ac.setPosition(display.device_get_numaxes_label, 10, 180)
    ac.setFontColor(display.device_get_numaxes_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_numaxes_label,'left')

    display.device_get_axis_label = ac.addLabel(display.appWindow, "device_get_axis")
    ac.setPosition(display.device_get_axis_label, 10, 200)
    ac.setFontColor(display.device_get_axis_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_axis_label,'left')

    display.device_get_axis_label_1 = ac.addLabel(display.appWindow, "device_get_axis 1")
    ac.setPosition(display.device_get_axis_label_1, 10, 220)
    ac.setFontColor(display.device_get_axis_label_1, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_axis_label_1,'left')

    display.device_get_axis_label_2 = ac.addLabel(display.appWindow, "device_get_axis 2")
    ac.setPosition(display.device_get_axis_label_2, 10, 240)
    ac.setFontColor(display.device_get_axis_label_2, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_axis_label_2,'left')

    display.device_get_axis_label_3 = ac.addLabel(display.appWindow, "device_get_axis 3")
    ac.setPosition(display.device_get_axis_label_3, 10, 260)
    ac.setFontColor(display.device_get_axis_label_3, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_axis_label_3,'left')

    display.device_get_axis_label_4 = ac.addLabel(display.appWindow, "device_get_axis 4")
    ac.setPosition(display.device_get_axis_label_4, 10, 280)
    ac.setFontColor(display.device_get_axis_label_4, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_axis_label_4,'left')

    display.device_get_axis_label_5 = ac.addLabel(display.appWindow, "device_get_axis 5")
    ac.setPosition(display.device_get_axis_label_5, 10, 300)
    ac.setFontColor(display.device_get_axis_label_5, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_axis_label_5,'left')

    display.device_get_numhats_label = ac.addLabel(display.appWindow, "device_get_numhats")
    ac.setPosition(display.device_get_numhats_label, 10, 330)
    ac.setFontColor(display.device_get_numhats_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_numhats_label,'left')

    display.device_get_hat_label = ac.addLabel(display.appWindow, "device_get_hat_label")
    ac.setPosition(display.device_get_hat_label, 10, 350)
    ac.setFontColor(display.device_get_hat_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_hat_label,'left')

    display.device_get_numballs_label = ac.addLabel(display.appWindow, "device_get_numballs")
    ac.setPosition(display.device_get_numballs_label, 10, 380)
    ac.setFontColor(display.device_get_numballs_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_numballs_label,'left')

    display.device_get_ball_label = ac.addLabel(display.appWindow, "device_get_ball")
    ac.setPosition(display.device_get_ball_label, 10, 400)
    ac.setFontColor(display.device_get_ball_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.device_get_ball_label,'left')

    display.event_label = ac.addLabel(display.appWindow, "The Event Queue Example - read mGameController.py for more detail")
    ac.setPosition(display.event_label, 10, 440)
    ac.setFontColor(display.event_label, 0.0, 0.85, 0.85, 1)
    ac.setFontAlignment(display.event_label,'left')

    display.event_Type_label = ac.addLabel(display.appWindow, "event_Type")
    ac.setPosition(display.event_Type_label, 10, 460)
    ac.setFontColor(display.event_Type_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.event_Type_label,'left')

    display.event_Controller_label = ac.addLabel(display.appWindow, "event_Controller")
    ac.setPosition(display.event_Controller_label, 10, 480)
    ac.setFontColor(display.event_Controller_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.event_Controller_label,'left')

    display.event_Details_label = ac.addLabel(display.appWindow, "event_Details")
    ac.setPosition(display.event_Details_label, 10, 500)
    ac.setFontColor(display.event_Details_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.event_Details_label,'left')

    display.event_Object_label = ac.addLabel(display.appWindow, "event_Object")
    ac.setPosition(display.event_Object_label, 10, 520)
    ac.setFontColor(display.event_Object_label, 1.0, 1.0, 1.0, 1)
    ac.setFontAlignment(display.event_Object_label,'left')

    """ Must init Pygame now and must be first before trying to access the gamedevice.device object"""
    pygame.init()
    """ Then set initial status on gamedevice instance which can now create the device object because pygame is running """
    gamedevice.setInitialStatus()
    return "mGameController"

def acUpdate(deltaT):
    """main loop"""
    """ Pump/Update the event queue in Pygame and is REQUIRED by both methods if you want to keep you input events from devices up to date on each frame
        If you did not want tot do this you need to call pygame.event.pump() to update values before you call them
        Both approaches require this in the main loop to update events each frame from device inputs
        Both use it in different ways and have pros and cons which I will explain inside each function"""
    pygame.event.pump()
    """The event queue style approach - Go read the information in the class DisplayClass Use for simple things a few events from one device a button push or just to get some values etc"""
    display.updateEvent()
    """ The object property style approach - Go read the information in the class DisplayClass Better for more reliable real time input, more information, simpler, easier for more complex tasks"""
    display.updateObject()

def acShutdown():
    """on shut down quit pygame so no crash or lockup."""
    pygame.quit()