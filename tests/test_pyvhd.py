# Copyright Matthew Carlson

import unittest
import tempfile
from io import BytesIO
from datetime import datetime
import re
from pyfat.PyVhd import VhdDataFooter

hex_re = re.compile(r'^([0-9A-fa-f]{2}[\s\|]*)+[\s\|]+')
def parse_hexdump(text_data, pad_to=None, min_length = None):
    bytes_stream = bytearray()
    lines = str(text_data).splitlines()
    for line in lines:
        match = hex_re.search(line.strip())
        if match is not None:
            matched = match.group(0).replace("|", " ")
            match_parts = [int(x, 16) for x in matched.split()]
            bytes_stream.extend(match_parts)
    while pad_to != None and len(bytes_stream) < pad_to:
        bytes_stream.append(0)
    if min_length is not None and len(bytes_stream) != min_length:
        raise IOError("Stream is too short")
    return bytes_stream


class TestFooter(unittest.TestCase):

    dyn_footer_data_text = '''
    63 6F 6E 65 63 74 69 78 00 00 00 02 00 01 00 00    conectix........
    00 00 00 00 00 00 02 00 27 37 14 7E 77 69 6E 20    ........'7.~win.
    00 0A 00 00 57 69 32 6B 00 00 00 00 00 50 00 00    ....Wi2k.....P..
    00 00 00 00 00 50 00 00 00 96 04 11 00 00 00 03    .....P..........
    FF FF F0 E5 45 43 48 08 24 B6 AC 4A B7 2A 43 45    ..peECH.$6,J7*CE
    97 E3 E1 39 00 00 00 00 00 00 00 00 00 00 00 00    .ca9............
    '''
    dyn_footer_data_gpt_fat_text = '''
    63 6f 6e 65 63 74 69 78 00 00 00 02 00 01 00 00    conectix000•0•00
    00 00 00 00 00 00 02 00 27 37 15 62 77 69 6e 20    000000•0'7•bwin
    00 0a 00 00 57 69 32 6b 00 00 00 00 00 50 00 00    0_00Wi2k00000P00
    00 00 00 00 00 50 00 00 00 96 04 11 00 00 00 03    00000P000×••000•
    ff ff f0 32 ba 7b 3f 32 25 ed 02 4b 86 c4 6b ba    ×××2×{?2%×•K××k×
    d7 21 cd 3a 00 00 00 00 00 00 00 00 00 00 00 00    ×!×:000000000000
    00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00    0000000000000000
    '''
    fixed_footer_data_text = '''
    63 6f 6e 65 63 74 69 78 00 00 00 02 00 01 00 00   conectix000•0•00
    ff ff ff ff ff ff ff ff 27 37 14 8e 77 69 6e 20   ××××××××'7•×win
    00 0a 00 00 57 69 32 6b 00 00 00 00 00 50 00 00   0_00Wi2k00000P00
    00 00 00 00 00 50 00 00 00 96 04 11 00 00 00 02   00000P000×••000•
    ff ff e8 29 71 e3 56 12 02 fd 43 49 9d 46 b8 53   ×××)q×V••×CI×F×S
    f3 19 71 aa 00 00 00 00 00 00 00 00 00 00 00 00   ×•q×000000000000
    00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   0000000000000000
    '''
    fixed_footer_data_gpt_text = '''
    63 6f 6e 65 63 74 69 78 00 00 00 02 00 01 00 00   conectix000•0•00
    ff ff ff ff ff ff ff ff 27 37 14 b1 77 69 6e 20   ××××××××'7•×win
    00 0a 00 00 57 69 32 6b 00 00 00 00 00 50 00 00   0_00Wi2k00000P00
    00 00 00 00 00 50 00 00 00 96 04 11 00 00 00 02   00000P000×••000•
    ff ff e7 8b 50 77 1c 32 f5 eb f4 4f 99 1c 51 c2   ××××Pw•2×××O×•Q×
    06 7b 96 c0 00 00 00 00 00 00 00 00 00 00 00 00   •{××000000000000
    00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   0000000000000000
    '''

    @classmethod
    def setUpClass(cls):
        cls.test_datum_dyn_text = [cls.dyn_footer_data_text, cls.dyn_footer_data_gpt_fat_text]
        cls.test_datum_fixed_text = [cls.fixed_footer_data_text, cls.fixed_footer_data_gpt_text]
        cls.test_datum_dyn = list([parse_hexdump(x, 512) for x in cls.test_datum_dyn_text])
        cls.test_datum_fixed = list([parse_hexdump(x, 512) for x in cls.test_datum_fixed_text])
        cls.test_datum = cls.test_datum_fixed + cls.test_datum_dyn

        for test_data in cls.test_datum:
            if len(test_data) != 512:
                print(test_data)
                raise IOError(f"Stream doesn't have footer: 512 != {len(test_data)}")

    def test_read(self):
        for data in self.test_datum:
            stream = BytesIO(data)
            footer = VhdDataFooter.read(stream)
            self.assertIsNotNone(footer)

    def test_read_fixed(self):
        data = parse_hexdump(self.fixed_footer_data_text, 512)
        stream = BytesIO(data)
        footer = VhdDataFooter.read(stream)
        print(hex(footer.data_offset))
        print(footer.get_struct_data())
        self.assertEqual(footer.cookie, b'conectix')
        self.assertEqual(footer.data_offset, 0xFFFFFFFF)

    def test_read_dynamic(self):
        data = parse_hexdump(self.dyn_footer_data_text, 512)
        stream = BytesIO(data)
        footer = VhdDataFooter.read(stream)
        self.assertEqual(footer.cookie, b'conectix')
        self.assertEqual(footer.features, 2)
        self.assertEqual(footer.data_offset, 512)
        self.assertEqual(footer.file_format_version, 0x00010000)
        self.assertEqual(footer.data_offset, 512)
        print(footer.get_struct_data())
        self.fail()
