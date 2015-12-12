"""
Assetto Corsa shared memory for Python applications

_ctypes.pyd must be somewhere in sys.path, because AC doesn't include all Python binaries.

Usage. Let's say you have following folder structure::

    some_app
        DLLs
            _ctypes.pyd
        some_app.py

some_app.py::

    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'DLLs'))

    from sim_info import info

    print(info.graphics.tyreCompound, info.physics.rpms, info.static.playerNick)


Do whatever you want with this code!
WBR, Rombik :)

Florian Sachs aka Sumpfgottheit, 2015-12-21:
  - Added new shared memory variables from AC 1.3.x
  - converted original Shared Memory CamelCase names to lowercase-separated-by-underscores (phytonic variables)
    using http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case


"""
import mmap
import ctypes
from ctypes import c_int32, c_float, c_wchar


AC_STATUS = c_int32
AC_OFF = 0
AC_REPLAY = 1
AC_LIVE = 2
AC_PAUSE = 3

AC_SESSION_TYPE = c_int32
AC_UNKNOWN = -1
AC_PRACTICE = 0
AC_QUALIFY = 1
AC_RACE = 2
AC_HOTLAP = 3
AC_TIME_ATTACK = 4
AC_DRIFT = 5
AC_DRAG = 6

AC_FLAG_TYPE = c_int32
AC_NO_FLAG = 0
AC_BLUE_FLAG = 1
AC_YELLOW_FLAG = 2
AC_BLACK_FLAG = 3
AC_WHITE_FLAG = 4
AC_CHECKERED_FLAG = 5
AC_PENALTY_FLAG = 6

# class SPageFilePhysics(ctypes.Structure):
#     _pack_ = 4
#     _fields_ = [
#         ('packetId', c_int32),
#         ('gas', c_float),
#         ('brake', c_float),
#         ('fuel', c_float),
#         ('gear', c_int32),
#         ('rpms', c_int32),
#         ('steerAngle', c_float),
#         ('speedKmh', c_float),
#         ('velocity', c_float * 3),
#         ('accG', c_float * 3),
#         ('wheelSlip', c_float * 4),
#         ('wheelLoad', c_float * 4),
#         ('wheelsPressure', c_float * 4),
#         ('wheelAngularSpeed', c_float * 4),
#         ('tyreWear', c_float * 4),
#         ('tyreDirtyLevel', c_float * 4),
#         ('tyreCoreTemperature', c_float * 4),
#         ('camberRAD', c_float * 4),
#         ('suspensionTravel', c_float * 4),
#         ('drs', c_float),
#         ('tc', c_float),
#         ('heading', c_float),
#         ('pitch', c_float),
#         ('roll', c_float),
#         ('cgHeight', c_float),
#         ('carDamage', c_float * 5),
#         ('numberOfTyresOut', c_int32),
#         ('pitLimiterOn', c_int32),
#         ('abs', c_float),
#         ('kersCharge', c_float),
#         ('kersInput', c_float),
#         ('autoShifterOn', c_int32),
#         ('rideHeight', c_float * 2),
#     ]
#
#
# class SPageFileGraphic(ctypes.Structure):
#     _pack_ = 4
#     _fields_ = [
#         ('packetId', c_int32),
#         ('status', AC_STATUS),
#         ('session', AC_SESSION_TYPE),
#         ('currentTime', c_wchar * 15),
#         ('lastTime', c_wchar * 15),
#         ('bestTime', c_wchar * 15),
#         ('split', c_wchar * 15),
#         ('completedLaps', c_int32),
#         ('position', c_int32),
#         ('iCurrentTime', c_int32),
#         ('iLastTime', c_int32),
#         ('iBestTime', c_int32),
#         ('sessionTimeLeft', c_float),
#         ('distanceTraveled', c_float),
#         ('isInPit', c_int32),
#         ('currentSectorIndex', c_int32),
#         ('lastSectorTime', c_int32),
#         ('numberOfLaps', c_int32),
#         ('tyreCompound', c_wchar * 33),
#
#         ('replayTimeMultiplier', c_float),
#         ('normalizedCarPosition', c_float),
#         ('carCoordinates', c_float * 3),
#         ('penaltyTime', c_float),
#         ('flag', AC_FLAG_TYPE),
#         ('idealLineOn', c_int32),
#     ]
#
#
# class SPageFileStatic(ctypes.Structure):
#     _pack_ = 4
#     _fields_ = [
#         ('_smVersion', c_wchar * 15),
#         ('_acVersion', c_wchar * 15),
#         # session static info
#         ('numberOfSessions', c_int32),
#         ('numCars', c_int32),
#         ('carModel', c_wchar * 33),
#         ('track', c_wchar * 33),
#         ('playerName', c_wchar * 33),
#         ('playerSurname', c_wchar * 33),
#         ('playerNick', c_wchar * 33),
#         ('sectorCount', c_int32),
#
#         # car static info
#         ('maxTorque', c_float),
#         ('maxPower', c_float),
#         ('maxRpm', c_int32),
#         ('maxFuel', c_float),
#         ('suspensionMaxTravel', c_float * 4),
#         ('tyreRadius', c_float * 4),
#     ]

class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('packet_id', c_int32),
        ('gas', c_float),
        ('brake', c_float),
        ('fuel', c_float),
        ('gear', c_int32),
        ('rpms', c_int32),
        ('steer_angle', c_float),
        ('speed_kmh', c_float),
        ('velocity', c_float * 3),
        ('acc_g', c_float * 3),
        ('wheel_slip', c_float * 4),
        ('wheel_load', c_float * 4),
        ('wheels_pressure', c_float * 4),
        ('wheel_angular_speed', c_float * 4),
        ('tyre_wear', c_float * 4),
        ('tyre_dirty_level', c_float * 4),
        ('tyre_core_temperature', c_float * 4),
        ('camber_rad', c_float * 4),
        ('suspension_travel', c_float * 4),
        ('drs', c_float),
        ('tc', c_float),
        ('heading', c_float),
        ('pitch', c_float),
        ('roll', c_float),
        ('cg_height', c_float),
        ('car_damage', c_float * 5),
        ('number_of_tyres_out', c_int32),
        ('pit_limiter_on', c_int32),
        ('abs', c_float),
        ('kers_charge', c_float),
        ('kers_input', c_float),
        ('auto_shifter_on', c_int32),
        ('ride_height', c_float * 2),
    ]


class SPageFileGraphic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('packet_id', c_int32),
        ('status', AC_STATUS),
        ('session', AC_SESSION_TYPE),
        ('current_time', c_wchar * 15),
        ('last_time', c_wchar * 15),
        ('best_time', c_wchar * 15),
        ('split', c_wchar * 15),
        ('completed_laps', c_int32),
        ('position', c_int32),
        ('i_current_time', c_int32),
        ('i_last_time', c_int32),
        ('i_best_time', c_int32),
        ('session_time_left', c_float),
        ('distance_traveled', c_float),
        ('is_in_pit', c_int32),
        ('current_sector_index', c_int32),
        ('last_sector_time', c_int32),
        ('number_of_laps', c_int32),
        ('tyre_compound', c_wchar * 33),

        ('replay_time_multiplier', c_float),
        ('normalized_car_position', c_float),
        ('car_coordinates', c_float * 3),
        ('penalty_time', c_float),
        ('flag', AC_FLAG_TYPE),
        ('ideal_line_on', c_int32),
    ]


class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('_sm_version', c_wchar * 15),
        ('_ac_version', c_wchar * 15),
        # session static info
        ('number_of_sessions', c_int32),
        ('num_cars', c_int32),
        ('car_model', c_wchar * 33),
        ('track', c_wchar * 33),
        ('player_name', c_wchar * 33),
        ('player_surname', c_wchar * 33),
        ('player_nick', c_wchar * 33),
        ('sector_count', c_int32),

        # car static info
        ('max_torque', c_float),
        ('max_power', c_float),
        ('max_rpm', c_int32),
        ('max_fuel', c_float),
        ('suspension_max_travel', c_float * 4),
        ('tyre_radius', c_float * 4),
    ]



class SimInfo:
    def __init__(self):
        self._acpmf_physics = mmap.mmap(0, ctypes.sizeof(SPageFilePhysics), "acpmf_physics")
        self._acpmf_graphics = mmap.mmap(0, ctypes.sizeof(SPageFileGraphic), "acpmf_graphics")
        self._acpmf_static = mmap.mmap(0, ctypes.sizeof(SPageFileStatic), "acpmf_static")
        self.physics = SPageFilePhysics.from_buffer(self._acpmf_physics)
        self.graphics = SPageFileGraphic.from_buffer(self._acpmf_graphics)
        self.static = SPageFileStatic.from_buffer(self._acpmf_static)

    def close(self):
        self._acpmf_physics.close()
        self._acpmf_graphics.close()
        self._acpmf_static.close()

    def __del__(self):
        self.close()

info = SimInfo()


def demo():
    import time

    for _ in range(400):
        print(info.static.track, info.graphics.tyreCompound, info.graphics.currentTime,
              info.physics.rpms, info.graphics.currentTime, info.static.maxRpm, list(info.physics.tyreWear))
        time.sleep(0.1)


def do_test():
    for struct in info.static, info.graphics, info.physics:
        print(struct.__class__.__name__)
        for field, type_spec in struct._fields_:
            value = getattr(struct, field)
            if not isinstance(value, (str, float, int)):
                value = list(value)
            print(" {} -> {} {}".format(field, type(value), value))


if __name__ == '__main__':
    do_test()
    demo()
