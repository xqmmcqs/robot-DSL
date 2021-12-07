import unittest
from server.state_machine import *

current_path = os.path.split(os.path.realpath(__file__))[0]


class TestWithDatabase(unittest.TestCase):
    def setUp(self):
        init_database(os.path.join(current_path, "robot.db"))
        store = Store(get_database())
        store.execute(
            "CREATE TABLE user_variable (username TEXT PRIMARY KEY, passwd TEXT)")
        store.commit()
        store.close()

    def tearDown(self):
        os.remove(os.path.join(current_path, "robot.db"))


class TestUserState(TestWithDatabase):
    def test_register(self):
        user_state = UserState()
        self.assertTrue(user_state.register("test1", "test1"))
        self.assertEqual(user_state.username, "test1")
        self.assertTrue(user_state.have_login)

    def test_login(self):
        user_state = UserState()
        user_state.register("test2", "test2")
        user_state = UserState()
        self.assertFalse(user_state.login("test2", "tt"))
        self.assertFalse(user_state.login("233", "233"))
        self.assertTrue(user_state.login("test2", "test2"))
        self.assertEqual(user_state.username, "test2")
        self.assertTrue(user_state.have_login)


class TestLengthCondition(unittest.TestCase):
    def test_check(self):
        condition = LengthCondition("<", 3)
        self.assertTrue(condition.check(""))
        self.assertFalse(condition.check("aaa"))
        condition = LengthCondition(">=", 5)
        self.assertTrue(condition.check("aaaaa"))
        self.assertFalse(condition.check("bb"))


class TestContainCondition(unittest.TestCase):
    def test_check(self):
        condition = ContainCondition("a string")
        self.assertTrue(condition.check(""))
        self.assertTrue(condition.check(" "))
        self.assertFalse(condition.check("b"))


class TestTypeCondition(unittest.TestCase):
    def test_check(self):
        condition = TypeCondition("Int")
        self.assertTrue(condition.check("3"))
        self.assertFalse(condition.check("3.3"))
        self.assertFalse(condition.check("s"))
        condition = TypeCondition("Real")
        self.assertTrue(condition.check("3"))
        self.assertTrue(condition.check("3.3"))
        self.assertFalse(condition.check("s"))


class TestEqualCondition(unittest.TestCase):
    def test_check(self):
        condition = EqualCondition("string")
        self.assertTrue(condition.check("string"))
        self.assertFalse(condition.check(""))


class TestExitAction(TestWithDatabase):
    def test_exec(self):
        action = ExitAction()
        user_state = UserState()
        action.exec(user_state, None, None)
        self.assertEqual(user_state.state, -1)


class TestGotoAction(TestWithDatabase):
    def test_exec(self):
        action = GotoAction(2, False)
        user_state = UserState()
        action.exec(user_state, None, None)
        self.assertEqual(user_state.state, 2)
        action = GotoAction(2, True)
        user_state.state = 1
        with self.assertRaises(LoginError):
            action.exec(user_state, None, None)
        user_state.have_login = True
        action.exec(user_state, None, None)
        self.assertEqual(user_state.state, 2)


if __name__ == '__main__':
    unittest.main()
