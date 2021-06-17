import logging
import struct
import threading
import time
import tkinter as tk
from collections import defaultdict
from functools import partial
from tkinter import ttk

import pymodbus.exceptions
import serial
from pymodbus.client.sync import ModbusSerialClient
from serial.tools.list_ports import comports

logger = logging.getLogger()


def get_avaliable_comports():
    return tuple(map(lambda x: x.device, comports()))


class Module:
    def __init__(self, port=None, data_variable=None):
        self.stopped = True
        self.data_variable = data_variable
        self.client = ModbusSerialClient(port=port,
                                         method="rtu",
                                         baudrate=9600,
                                         parity=serial.PARITY_NONE,
                                         stopbits=1)

    def open(self) -> bool:
        return self.client.connect()

    def set_port(self, port):
        self.client.port = port

    def close(self):
        self.client.close()

    def is_open(self) -> bool:
        return self.client.is_socket_open()

    def get_holding_registers(self):
        try:
            registers = self.client.read_holding_registers(0, 8, unit=5).registers
        except pymodbus.exceptions.ModbusException as e:
            logger.error(str(e))
        else:
            return (self.from_registers_to_float(*registers[0:2]),
                    self.from_registers_to_float(*registers[2:4]),
                    registers[4],
                    self.from_registers_to_int32(*registers[5:7]))

    @staticmethod
    def from_registers_to_float(*values):
        return struct.unpack("<f", struct.pack("<HH", *values))[0]

    @staticmethod
    def from_registers_to_int32(*values):
        return struct.unpack("<I", struct.pack("<HH", *values))[0]

    def start_cycle(self):
        if self.stopped and self.is_open():
            self.stopped = False
            thread = threading.Thread(target=self.while_cycle)
            thread.daemon = True
            thread.start()
            return 0
        else:
            logger.debug("Already started or closed port")
            return 1

    def while_cycle(self):
        logger.info("Starting cycle")
        while not self.stopped:
            results = str(self.get_holding_registers())
            logger.info(results)
            self.data_variable.set(results)
            time.sleep(1)
        logger.info("Stopping cycle")

    def stop(self):
        self.stopped = True


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super(MainWindow, self).__init__(master=master)
        self.com_port_properties = PropertiesFrame(master=self, frametext="Connection")
        logger.debug(get_avaliable_comports())
        self.com_port_properties.add_row(0, "COM Port:", values=get_avaliable_comports())
        self.com_port_properties.pack()

        self.info_variable = tk.StringVar(master=self)
        self.data_variable = tk.StringVar(master=self)

        self.module = Module(data_variable=self.data_variable)

        buttons_properties = tk.LabelFrame(master=self, text="Controls")
        connect_button = tk.Button(master=buttons_properties, text="Connect", command=self.connect_module)
        connect_button.pack(side=tk.LEFT)
        check_button = tk.Button(master=buttons_properties, text="Check", command=self.check_connection)
        check_button.pack(side=tk.LEFT)
        start_button = tk.Button(master=buttons_properties, text="Start", command=self.start_cycle)
        start_button.pack(side=tk.LEFT)
        stop_button = tk.Button(master=buttons_properties, text="Stop", command=self.stop_cycle)
        stop_button.pack(side=tk.LEFT)
        buttons_properties.pack()

        info_label = tk.Label(master=self, textvariable=self.info_variable, relief=tk.SUNKEN)
        info_label.pack(padx=1)

        data_label = tk.Label(master=self, textvariable=self.data_variable)
        data_label.pack(padx=1)

    def connect_module(self):
        self.module.set_port(self.com_port_properties.get_entry_value(0))
        self.module.open()
        self.check_connection()

    def check_connection(self):
        if self.module.is_open():
            self.info_message("Serial opened")
        else:
            self.info_message("Serial closed")

    def start_cycle(self):
        if self.module.start_cycle():
            self.info_message("Not started")
        else:
            self.info_message("Started")

    def stop_cycle(self):
        self.module.stop()
        self.info_message("Cycle stopped")

    def info_message(self, message):
        self.info_variable.set(message)


class PropertiesFrame(tk.LabelFrame):
    def __init__(self, master=None, frametext=None):
        super(PropertiesFrame, self).__init__(master=master, text=frametext)
        self.label_dict = dict()
        self.entry_dict = dict()
        self.entry_textvariable_dict = defaultdict(partial(tk.StringVar, self))

    def add_entry(self, row):
        self.entry_dict[row] = tk.Entry(master=self, textvariable=self.entry_textvariable_dict[row])
        self.entry_dict[row].grid(row=row, column=1, padx=(0, 10), pady=(3, 1))

    def get_entry(self, row):
        return self.entry_dict[row]

    def get_entry_value(self, row):
        return self.entry_textvariable_dict[row].get()

    def add_label(self, row, text):
        self.label_dict[row] = tk.Label(master=self, text=text)
        self.label_dict[row].grid(row=row, column=0, padx=(10, 0), pady=(3, 1))

    def add_combobox(self, row, values):
        self.entry_dict[row] = ttk.Combobox(master=self, textvariable=self.entry_textvariable_dict[row],
                                            values=values)
        self.entry_dict[row].grid(row=row, column=1, padx=(0, 10), pady=(3, 1))

    def add_row(self, row, text, values=None):
        self.add_label(row, text)
        if values is None:
            self.add_entry(row)
        else:
            self.add_combobox(row, values)
