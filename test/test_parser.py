import unittest
from pyparsing import ParseException
from server.parser import RobotLanguage


class TestRobotLanguage(unittest.TestCase):
    def test_parse_files_case1(self):
        with open("./parser/result1.txt", "r") as f:
            result = f.readline()
            self.assertEqual(repr(RobotLanguage.parse_files(['./parser/case1.txt'])), result)

    def test_parse_files_case2(self):
        with open("./parser/result2.txt", "r") as f:
            result = f.readline()
            self.assertEqual(repr(RobotLanguage.parse_files(['./parser/case2.txt'])), result)

    def test_parse_files_case3(self):
        with self.assertRaises(ParseException):
            RobotLanguage.parse_files(['./parser/case3.txt']),

    def test_parse_files_case4(self):
        with self.assertRaises(ParseException):
            RobotLanguage.parse_files(['./parser/case4.txt']),

    def test_parse_files_case5(self):
        with self.assertRaises(ParseException):
            RobotLanguage.parse_files(['./parser/case5.txt']),


if __name__ == '__main__':
    unittest.main()
