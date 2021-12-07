import unittest
from server.state_machine import *

current_path = os.path.split(os.path.realpath(__file__))[0]

class TestSpeakAction(unittest.TestCase):
    def test_exec(self):
        init_database(os.path.join(current_path, "robot.db"))
        UserVariableSet.test1 = Int(default=0)
        UserVariableSet.test2 = Float(default=0.0)
        UserVariableSet.test3 = Unicode(default="default")
        UserVariableSet.column_type["test1"] = "Int"
        UserVariableSet.column_type["test2"] = "Real"
        UserVariableSet.column_type["test3"] = "Text"
        store = Store(get_database())
        store.execute(
            "CREATE TABLE user_variable (username TEXT PRIMARY KEY, passwd TEXT, test1 INTEGER, test2 REAL, test3 TEXT)")
        store.commit()
        store.close()

        user_state = UserState()
        user_state.register("test", "")

        action = SpeakAction(["\"233\"", "\"你好\"", "Copy", "$username", "$test1"])
        result = []
        action.exec(user_state, result, "我说的话")
        self.assertEqual(["233你好我说的话test0"], result)

        with self.assertRaises(GrammarError):
            SpeakAction(["$vvv"])

        os.remove(os.path.join(current_path, "robot.db"))


if __name__ == '__main__':
    unittest.main()
