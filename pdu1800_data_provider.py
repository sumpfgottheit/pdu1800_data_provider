
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
import re

#
# Constants
#

APPNAME = "RPI Dashboard Data Provider"


BUTTON_FORWARD = 'button_forward'
BUTTON_BACK = 'button_back'
RASPBERRY_IP = 'raspberry_ip'
RASPBERRY_UDP_PORT = 'raspberry_udp_port'
HZ = 'hz'
INI_SECTION = 'pdu1800'
SHOW_DEBUG_WINDOW = 'show_debug_window'

SESSION_TYPE = ['Unbekannt', 'Practice', 'Qualifying', 'Race', 'Hotlap', 'TimeAttack', 'Drift', 'Drag']
INI_FILE = os.path.join(os.path.dirname(__file__), 'config.ini')
DEFAULT_CONFIG_DICT = {BUTTON_FORWARD: -1, BUTTON_BACK: -1, RASPBERRY_IP: '', RASPBERRY_UDP_PORT: 18877, HZ: 30, SHOW_DEBUG_WINDOW: False}

LUT_FIELDNAMES_TO_UNDERSCORE = {}

#
# Global Variables
#
app = None

def acMain(ac_version):
    global app, APPNAME
    try:
        """ Must init Pygame now and must be first before trying to access the gamedevice.device object"""
        pygame.init()
        app = PDU1800DataProvider(APPNAME)
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

def convert_to_lowercase_and_underscore(name):
    """
    The Shared Memory is in CamelCase - convert the names to Python Standard lowercase with underscores
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case

    I have already changed the names in sim_info.py, so this function is no longer used
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def struct_to_hash(s):
    """
    Convert the given struct to a python hash
    Args:
        struct: The sim_info-scruct

    Returns: The struct as hash. The fieldnames are converted to lowercase/underscore
    """
    h = {}
    d = [(field, getattr(s, field)) for field in [f[0] for f in s._fields_]]
    for field, value in d:
        if field not in LUT_FIELDNAMES_TO_UNDERSCORE:
            LUT_FIELDNAMES_TO_UNDERSCORE[field] = convert_to_lowercase_and_underscore(field)
        field_name = LUT_FIELDNAMES_TO_UNDERSCORE[field]
        if not isinstance(value, (str, float, int)):
            value = list(value)
        h[field_name] = value
    return h



def getit(key, h):
    """Return h[key]. If key has '.' in it like static.max_fuel, return h[static][max_fuel]
    getit('physics.tyre_wear', h') will get you h['physics']['tyre_wear'].
    It's just syntactic sugar, but easier to read.

    Exceptions are not catched
    """
    if '.' in key:
        keys = key.split('.')
        return h.get(keys[0]).get(keys[1])
    else:
        return h.get(key)

class PDU1800DataProvider:
    def __init__(self, appname):

        self.appname = appname
        self.static_set = False

        #
        # Structures for Data Capture
        #
        self.info = info  # sim_info
        self.data = dict()

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

        self.data['raspberry_ip'] = self.raspberry_ip
        self.data['raspberry_udp_port'] = self.raspberry_udp_port

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
        fields_from_static = ('max_rpm', 'car_model', 'nickname', 'max_fuel', 'num_cars')
        fields_from_physics = ('rpms', 'fuel', 'gear', 'speed_kmh', 'pit_limiter_on')
        fields_from_graphics = ('position', 'number_of_laps', 'completed_laps', 'i_current_time', 'i_last_time', 'i_best_time')

        self.field_shown_in_debug_window = (['static.{0}'.format(s) for s in fields_from_static] +
                                            ['physics.{0}'.format(s) for s in fields_from_physics] +
                                            ['graphics.{0}'.format(s) for s in fields_from_graphics] +
                                            ['frames_skipped', 'interval', 'raspberry_ip', 'raspberry_udp_port'])
        if self.show_debug_window:
            self.debug_window = DataProviderIngameDebugWindow(self.appname, 300, 500)
            for name in self.field_shown_in_debug_window:
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
        for label_name in self.field_shown_in_debug_window:
            self.debug_window.labels[label_name].setText("{}: {}".format(label_name, getit(label_name, self.data)))

    def emit(self):
        self.udp_sock.sendto(pickle.dumps(self.data, protocol=2), (self.raspberry_ip, self.raspberry_udp_port))

    def update(self, deltaT):
        #
        # Reading the static section within the shared memory needs to be done within the acUpdate(), but the
        # first frame is all we need.
        #


        if not self.static_set:
            self.data['static'] = struct_to_hash(self.info.static)
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
        self.data['delta'] = ac.getCarState(0, acsys.CS.PerformanceMeter)   # Delta gibts aus der Python API

        self.data['graphics'] = struct_to_hash(self.info.graphics)
        self.data['physics'] = struct_to_hash(self.info.physics)
        self.data['frames_skipped'] = self.frames_skipped
        self.frames_skipped = 0
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
