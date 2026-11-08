import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import cpu_temp_display as m

class TestPacket(unittest.TestCase):
    def test_packet(self):
        p = m.telemetry_packet(67, 15)
        self.assertEqual(len(p),64)
        self.assertEqual(list(p[:8]),[7,0,6,7,0x10,0,1,5])
        self.assertTrue(all(x == 0 for x in p[8:]))
    def test_fahrenheit(self):
        p=m.telemetry_packet(125,78,fahrenheit=True,size=65)
        self.assertEqual(list(p[:8]),[7,1,2,5,0x11,0,7,8])
        self.assertEqual(len(p),65)
    def test_clamp(self):
        self.assertEqual(list(m.telemetry_packet(5000,999)[:8]),[7,9,9,9,0x10,1,0,0])
    def test_invalid_size(self):
        with self.assertRaises(ValueError):m.telemetry_packet(30,20,size=2)
    def test_hid_ioctl(self):
        self.assertEqual(m.hid_iocsfeature(64),0xC0404806)
    def test_usb_id(self):
        self.assertEqual(m.parse_hid_id('DRIVER=hid-generic\nHID_ID=0003:00001A2C:00004984\n'),(0x1a2c,0x4984))
    def test_temperature(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'temp1_input'
            f.write_text('53500')
            self.assertEqual(m.read_temp_c(f),53.5)
            f.write_text('999999')
            self.assertIsNone(m.read_temp_c(f))


class TestDiscovery(unittest.TestCase):
    def test_match_verified_interface(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            good=root/'hidraw4'
            bad=root/'hidraw3'
            for directory, desc, iface in [(bad, b'\x85\x02\xb1\x02', '00'),
                                           (good, b'\x85\x07\x09\x03\xb1\x02', '01')]:
                dev=directory/'device'
                dev.mkdir(parents=True)
                (dev/'uevent').write_text('HID_ID=0003:00001A2C:00004984\n')
                (dev/'report_descriptor').write_bytes(desc)
                (dev/'bInterfaceNumber').write_text(iface)
            with patch.object(m, 'SYS_HIDRAW', root):
                devices=m.discover_hidraw()
                self.assertEqual(len(devices),2)
                self.assertEqual(str(m.select_device()),'/dev/hidraw4')

class TestDescriptorSafety(unittest.TestCase):
    def test_same_report_id_owns_feature(self):
        self.assertTrue(m.descriptor_has_feature_report(b'\x85\x07\x09\x03\xb1\x02', 7))
    def test_feature_belongs_to_other_report_id(self):
        self.assertFalse(m.descriptor_has_feature_report(b'\x85\x07\x81\x02\x85\x02\xb1\x02', 7))
    def test_truncated_descriptor(self):
        self.assertFalse(m.descriptor_has_feature_report(b'\x85', 7))
    def test_global_push_pop(self):
        self.assertTrue(m.descriptor_has_feature_report(b'\x85\x07\xa4\x85\x02\xb4\xb1\x02', 7))
    def test_no_match(self):
        self.assertFalse(m.descriptor_has_feature_report(b'\x85\x02\xb1\x02', 7))

