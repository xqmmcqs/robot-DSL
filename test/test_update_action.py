import unittest
from server.state_machine import *

current_path = os.path.split(os.path.realpath(__file__))[0]

class TestUpdateAction(unittest.TestCase):
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

        action = UpdateAction("test1", "Set", 1, None)
        action.exec(user_state, None, None)
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").test1, 1)
        store.close()

        action = UpdateAction("test1", "Add", 1, "Int")
        action.exec(user_state, None, None)
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").test1, 2)
        store.close()

        action = UpdateAction("test2", "Sub", 1.5, "Real")
        action.exec(user_state, None, None)
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").test2, -1.5)
        store.close()

        action = UpdateAction("test3", "Set", "\"测试\"", None)
        action.exec(user_state, None, None)
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").test3, "测试")
        store.close()

        action = UpdateAction("test3", "Set", "Copy", "Text")
        action.exec(user_state, None, "testing")
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").test3, "testing")
        store.close()

        action = UpdateAction("test2", "Set", "Copy", "Real")
        action.exec(user_state, None, "2.2")
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").test2, 2.2)
        store.close()

        with self.assertRaises(GrammarError):
            UpdateAction("test4", "Set", "", None)
        with self.assertRaises(GrammarError):
            UpdateAction("test3", "Set", "Copy", None)
        with self.assertRaises(GrammarError):
            UpdateAction("test1", "Set", "Copy", "Text")
        with self.assertRaises(GrammarError):
            UpdateAction("test1", "Set", "Copy", "Real")
        with self.assertRaises(GrammarError):
            UpdateAction("test2", "Set", "Copy", "Text")
        with self.assertRaises(GrammarError):
            UpdateAction("test1", "Set", 2.2, None)
        with self.assertRaises(GrammarError):
            UpdateAction("test2", "Set", "\"12\"", None)
        with self.assertRaises(GrammarError):
            UpdateAction("test3", "Add", "\"12\"", None)

        os.remove(os.path.join(current_path, "robot.db"))


if __name__ == '__main__':
    unittest.main()
