# PDU1800 - Raspberry Pi Dashboard Display for Assetto Corsa - Data Provider

This is the PDU1800 Data Provider which acts as as compagnon app for the [PDU1800](https://github.com/sumpfgottheit/pdu1800). 
It is a Python Assetto Corsa Plugin and _should_ run as 32Bit or 64Bit plugin, but has only been tested on 64Bit.

## Installation

* Download and place it within a directory 'pdu1800_data_provider' within the $assettocorsa/apps/python/ directory
* Edit the 'config.ini' to suit your needs
* Enable it from the 'General' Tab.
* Take a look at the debug window which can be started ingame as application from the right application bar

## Configuration

The config.ini looks like this:
```
[pdu1800]
button_forward = -1          # not yet used, but can be used to flip pages on the pi
raspberry_udp_port = 18877   # must match the pdu1800/config.py setting on your raspberry
hz = 30                      # How often shall the data be sent (30 hz seems to be quite good)
button_back = -1             # not yet used, but can be used to flip pages on the pi
raspberry_ip = 127.0.0.1     # The ip address of the raspberry, should match the pi....
show_debug_window = True     # Whether the debug window should be created
```

## Interesting Python points

I convert all original CamelCaseSharedMemoryNames to pythonic lower_case_with_underscores. Therefore, the `wheelAngularSpeed` becomes a `wheel_angular_speed`. See the `convert_to_lowercase_and_underscore(name)` function.

The structs are converted to hashes and the data sent to the pi is `{'physics': physics_hash, 'graphics': graphics_hash ....}`. The conversion is done using the `struct_to_hash(s)` function.
