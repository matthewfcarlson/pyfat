import io
import struct
import uuid
import os
from typing import BinaryIO
from datetime import datetime
from collections import namedtuple


class VhdData():

    _struct_items = None
    _struct_alignment = '@'
    _struct_names = list()

    def __init__(self):
        
        self._struct_format = VhdData._create_struct_format(self._struct_items, self._struct_alignment)
        self._struct_size =  struct.calcsize(self._struct_format)
        
        self._dirty = False
        for item in self._struct_items:
            item_name = item[0]
            item_value = item[2]
            included = True if len(item) < 4 else item[3]
            if item_name not in self._struct_names and included:
                self._struct_names.append(item_name)
            self.__setattr__(item_name, item_value)
        self._dirty = False

    def __setattr__(self, key, value):
        if key in self._struct_names:
            self._dirty = True
        super().__setattr__(key, value)

    def __getattr__(self, key):
        super().__getattr__(key)

    @staticmethod
    def _create_struct_format(struct_data, alignment = "@"):
        struct_format = [alignment, ]

        for item in struct_data:
            struct_format.append(item[1])
        struct_format_string = "".join(struct_format)
        return struct_format_string

    @classmethod
    def read(cls, stream):
        data_obj = cls()
        byte_data = stream.read(data_obj.get_struct_size())
        data = data_obj._unpack(byte_data)
        for struct_item in data_obj.get_struct_names():
            new_value = getattr(data, struct_item)
            data_obj.__setattr__(struct_item, new_value)
        data_obj.validate()
        data_obj._dirty = False
        return data_obj

    def _unpack(self, data):
        print(self._struct_format)
        struct_items = " ".join(self._struct_names)
        struct_tuple = namedtuple(type(self).__name__, struct_items)
        unpacked_data = struct.unpack(self._struct_format, data)
        named_data = struct_tuple._make(unpacked_data)
        return named_data

    @classmethod
    def write(cls, stream):
        raise RuntimeError()

    @classmethod
    def get_struct_items(cls):
        return cls._struct_items

    @classmethod
    def get_struct_names(cls):
        return cls._struct_names

    def get_struct_size(self):
        return self._struct_size

    def get_struct_data(self):
        data = {}
        for key in self.get_struct_names():
            data[key] = self.__getattribute__(key)
        return data

    def __eq__(self, other):
        ''' determines if something is equal to another '''
        if not isinstance(other, VhdDataFooter):
            return False
        for item in self.get_struct_items():
            item_name = item[0]
            if self.__getattribute__(item_name) != other.__getattribute__(item_name):
                return False
        return True

class VhdDataFooter(VhdData):
    '''
    The footer data format follows 
    | Hard disk footer fields | Size (bytes) | Data |
    |  ---- | ---- | ---- |
    | Cookie | 8 | conectix |
    | Features | 4 |
    | File Format Version | 4 |
    | Data Offset | 8 |
    | Time Stamp | 4 |
    | Creator Application | 4 |
    | Creator Version | 4 |
    | Creator Host OS | 4 |
    | Original Size | 8 |
    | Current Size | 8 |
    | Disk Geometry | 4 |
    | Disk Type | 4 |
    | Checksum | 4 |
    | Unique Id | 16 |
    | Saved State | 1 |
    | Reserved | 427 |
    '''
    # network format (big-endian)
    _struct_alignment = '!'
    _default_creator_host_os = 0x5769326B if os.name == 'nt' else 0x4D616320
    _struct_items = [
        ('cookie', '8s', b'conectix'),
        ('features', 'L', 0x2),
        ('file_format_version', 'L', 0x00010000),
        ('data_offset', 'Q', 0xFFFFFFFF),
        ('time_stamp', 'L', None),
        ('creator_application', '4s', b'vpc'),
        ('creator_version', 'L', 0x00050000),
        ('creator_host_os', 'L', _default_creator_host_os),
        ('original_size', 'Q', None),
        ('current_size', 'Q', None),
        ('disk_geometry_cyl', 'H', None),
        ('disk_geometry_heads', 'B', None),
        ('disk_geometry_spt', 'B', None),
        ('disk_type', 'L', None),
        ('checksum', 'L', None),
        ('unique_id', '16s', None),
        ('saved_state', 'B', None),
        ('reserved', '427x', None, False)
    ]

    def validate(self):
        if self.cookie != b'conectix':
            raise ValueError('Footer cookie is bad')
        return True

    def get_timestamp(self):
        return datetime.fromtimestamp(self.time_stamp + 946080000)
    # @classmethod
    # def read(cls, stream):
    #     footer = VhdDataFooter()
    #     byte_data = stream.read(footer.get_struct_size())
    #     data = footer._unpack(byte_data)
    #     print(data)

    #     ## TODO: get the values out and set them

    # @classmethod
    # def write(cls, stream):
    #     raise RuntimeError()
