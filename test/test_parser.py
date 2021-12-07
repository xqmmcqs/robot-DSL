import os
import unittest
from pyparsing import ParseException
from server.parser import RobotLanguage

current_path = os.path.split(os.path.realpath(__file__))[0]


class TestRobotLanguage(unittest.TestCase):
    def test_parse_files(self):
        with open(os.path.join(current_path, "parser/result1.txt"), "r") as f:
            result = f.readline().strip()
            self.assertEqual(repr(RobotLanguage.parse_files([os.path.join(current_path, "parser/case1.txt")])), result)
        with open(os.path.join(current_path, "parser/result2.txt"), "r") as f:
            result = f.readline().strip()
            self.assertEqual(repr(RobotLanguage.parse_files([os.path.join(current_path, "parser/case2.txt")])), result)
        with self.assertRaises(ParseException):
            RobotLanguage.parse_files([os.path.join(current_path, "parser/case3.txt")]),
        with self.assertRaises(ParseException):
            RobotLanguage.parse_files([os.path.join(current_path, "parser/case4.txt")]),
        with self.assertRaises(ParseException):
            RobotLanguage.parse_files([os.path.join(current_path, "parser/case5.txt")]),


if __name__ == '__main__':
    unittest.main()
