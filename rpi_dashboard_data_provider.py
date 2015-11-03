
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

#
# Import all other
#
import pickle
import socket
from collections import OrderedDict
from configparser import ConfigParser
from time import perf_counter
from pprint import pformat
from sim_info import info
from util import Label, validate_ip
import pygame
from mGameController import GameController


#
# Constants
#

APPNAME = "RPI Dashboard Data Provider"


BUTTON_FORWARD = 'button_forward'
BUTTON_BACK = 'button_back'
RASPBERRY_IP = 'raspberry_ip'
RASPBERRY_UDP_PORT = 'raspberry_udp_port'
HZ = 'hz'
INI_SECTION = 'rpi_dashboard_data_provider'
SHOW_DEBUG_WINDOW = 'show_debug_window'

SESSION_TYPE = ['Unbekannt', 'Practice', 'Qualifying', 'Race', 'Hotlap', 'TimeAttack', 'Drift', 'Drag']
INI_FILE = os.path.join(os.path.dirname(__file__), 'config.ini')
DEFAULT_CONFIG_DICT = {BUTTON_FORWARD: -1, BUTTON_BACK: -1, RASPBERRY_IP: '', RASPBERRY_UDP_PORT: 18877, HZ: 30, SHOW_DEBUG_WINDOW: False}

#
# Global Variables
#
app = None

def acMain(ac_version):
    global app, APPNAME
    try:
        """ Must init Pygame now and must be first before trying to access the gamedevice.device object"""
        pygame.init()
        app = RPIDashboardDataProvider(APPNAME)
        return APPNAME
    except Exception as e:
        ac.log("Error in acMain: {}".format(str(e)))
        ac.console("Error in acMain: {}".format(str(e)))

def acUpdate(deltaT):
    try:
        global app
        pygame.event.pump()
        app.update(deltaT)
    except Exception as e:
        ac.log("Error in acUpdate: {}".format(str(e)))

def acShutdown():
    """on shut down quit pygame so no crash or lockup."""
    pygame.quit()
    pass


class DataProviderIngameDebugWindow:
    vertical_spacing = 20

    def __init__(self, title, width=200, height=200):
        self._id = ac.newApp(title)
        self.set_size(width, height)
        self.labels = OrderedDict()

    def pack(self):
        """
        Iterate over all labels and place them all *vertical_spacing* pixels
        :return:
        """
        for i, label in enumerate(self.labels.values(), start=1):
            ac.setPosition(label.label_id, 0, self.vertical_spacing * i)

    def set_size(self, width, height):
        ac.setSize(self._id, width, height)

    def add_label(self, label):
        self.labels[label.name] = label

    @property
    def app_id(self):
        return self._id


class RPIDashboardDataProvider:
    def __init__(self, appname):

        self.appname = appname
        self.static_set = False

        #
        # Structures for Data Capture
        #
        self.info = info  # sim_info
        self.data = dict(max_rpm=0, rpms=0, car_model='', nickname='', trackname='', max_fuel=0.0,
                         fuel=0.0, gear=0, kmh=0, pit_limiter=True, drs=False, abs=False, tc=False,
                         session_type=-1, game_controller='', button_pressed=0, hz=0, interval=0, frames_skipped=0)
        #
        # GameController Fu
        #
        self.game_controller = GameController()
        self.game_controller.setInitialStatus()
        if self.game_controller.device is None:
            self.data['game_controller'] = 'No Game Controller found'
        else:
            self.data['game_controller'] = self.game_controller.device.get_name()

        #
        # Read the config
        #
        config_dict, self.valid_config = self.read_and_validate_config()
        self.button_forward = config_dict[BUTTON_FORWARD]
        self.button_backward = config_dict[BUTTON_BACK]
        self.raspberry_ip = config_dict[RASPBERRY_IP]
        self.raspberry_udp_port = config_dict[RASPBERRY_UDP_PORT]
        self.hz = config_dict[HZ]
        self.show_debug_window = config_dict[SHOW_DEBUG_WINDOW]

        ac.log("{} config: {}".format(self.appname, pformat(config_dict, indent=0, width=10000)))
        #
        # Set the Interval for Updates
        #
        self.interval = 1.0 / self.hz
        self.data['interval'] = self.interval
        self.data['hz'] = self.hz
        self.last_update_tick = 0
        self.frames_skipped = 0

        #
        # The Debugwindow as Application
        #
        if self.show_debug_window:
            self.debug_window = DataProviderIngameDebugWindow(self.appname, 300, 500)
            for name in self.data.keys():
                self.debug_window.add_label(Label(self.debug_window.app_id, name, '{}: N/A'.format(name)))
            self.debug_window.pack()

        #
        # create the UDP Socket
        #
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @staticmethod
    def read_and_validate_config():
        config = ConfigParser(defaults=DEFAULT_CONFIG_DICT, default_section=INI_SECTION)
        if not os.path.isfile(INI_FILE):
            with open(INI_FILE, 'w') as f:
                config.write(f)
        with open(INI_FILE) as f:
            config.read_file(f)

        bt_forward = config.get(INI_SECTION, BUTTON_FORWARD, fallback=DEFAULT_CONFIG_DICT[BUTTON_FORWARD])
        bt_back = config.get(INI_SECTION, BUTTON_BACK, fallback=DEFAULT_CONFIG_DICT[BUTTON_BACK])
        raspberry_ip = config.get(INI_SECTION, RASPBERRY_IP, fallback=DEFAULT_CONFIG_DICT[RASPBERRY_IP])
        raspberry_udp_port = config.get(INI_SECTION, RASPBERRY_UDP_PORT, fallback=DEFAULT_CONFIG_DICT[RASPBERRY_UDP_PORT])
        hz = config.get(INI_SECTION, HZ, fallback=DEFAULT_CONFIG_DICT[HZ])
        show_debug_window = config.getboolean(INI_SECTION, SHOW_DEBUG_WINDOW, fallback=False)

        try:
            bt_forward = int(bt_forward)
            bt_back = int(bt_back)
            raspberry_udp_port = int(raspberry_udp_port)
            hz = int(hz)
            if not validate_ip(raspberry_ip):
                raise Exception('IP for Raspberry PI is not valid')
            if not 1024 < raspberry_udp_port <= 65535:
                raise Exception('UDP Port for Raspberry PI is not valid')
        except Exception as e:
            ac.log(str(e))
            ac.console(str(e))
            return DEFAULT_CONFIG_DICT, False
        return dict(button_forward=bt_forward, button_back=bt_back, raspberry_ip=raspberry_ip,
                    raspberry_udp_port=raspberry_udp_port, hz=hz, show_debug_window=show_debug_window), True

    def update_labels_in_debug_window(self):
        for label_name, value in self.data.items():
            self.debug_window.labels[label_name].setText("{}: {}".format(label_name, value))

    def emit(self):
        self.udp_sock.sendto(pickle.dumps(self.data, protocol=2), (self.raspberry_ip, self.raspberry_udp_port))

    def update(self, deltaT):
        #
        # Reading the static section within the shared memory needs to be done within the acUpdate(), but the
        # first frame is all we need.
        #

        if not self.static_set:
            self.data['max_rpm'] = self.info.static.maxRpm
            self.data['car_model'] = self.info.static.carModel
            self.data['nickname'] = self.info.static.playerNick
            self.data['trackname'] = self.info.static.track
            self.data['max_fuel'] = self.info.static.maxFuel
            self.static_set = True

        #
        # Check if we should update
        #
        current_tick = perf_counter()
        if current_tick - self.last_update_tick < self.interval:
            self.frames_skipped += 1
            return
        self.last_update_tick = current_tick

        #
        # Dynamic updates
        #
        self.data['frames_skipped'] = self.frames_skipped
        self.frames_skipped = 0
        self.data['rpms'] = self.info.physics.rpms
        self.data['fuel'] = self.info.physics.fuel
        self.data['gear'] = self.info.physics.gear - 1
        self.data['kmh'] = self.info.physics.speedKmh
        self.data['pit_limiter'] = self.info.physics.pitLimiterOn == 1
        self.data['drs'] = self.info.physics.drs
        self.data['abs'] = self.info.physics.abs
        self.data['tc'] = self.info.physics.tc
        self.data['session_type'] = SESSION_TYPE[self.info.graphics.session + 1]

        #
        # Handle events
        #
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                self.data['button_pressed'] = event.dict['button']

        # if self.valid_config and self.i % 10 == 0:
        if self.valid_config:
            self.emit()

        # Only update the debugwindow if we haven't
        if self.show_debug_window:
            self.update_labels_in_debug_window()
