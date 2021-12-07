import unittest
from server.state_machine import *

current_path = os.path.split(os.path.realpath(__file__))[0]

class TestStateMachine(unittest.TestCase):
    def test_state_machine(self):
        init_database(os.path.join(current_path, "robot.db"))
        with self.assertRaises(GrammarError):
            StateMachine([os.path.join(current_path, "state_machine/case1.txt")])
        with self.assertRaises(GrammarError):
            StateMachine([os.path.join(current_path, "state_machine/case2.txt")])
        with self.assertRaises(GrammarError):
            StateMachine([os.path.join(current_path, "state_machine/case3.txt")])

        m = StateMachine([os.path.join(current_path, "parser/case2.txt")])
        with open(os.path.join(current_path, "state_machine/result.txt"), "r") as f:
            line = f.readline().strip()
            self.assertEqual(line, repr(m.states))
            line = f.readline().strip()
            self.assertEqual(line, repr(m.speak))
            line = f.readline().strip()
            self.assertEqual(line, repr(m.case))
            line = f.readline().strip()
            self.assertEqual(line, repr(m.default))
            line = f.readline().strip()
            self.assertEqual(line, repr(m.timeout))

        user_state = UserState()

        with self.assertRaises(LoginError):
            m.condition_transform(user_state, "")

        user_state.register("test", "test")
        user_state.state = 2
        result = m.condition_transform(user_state, "nooooo")
        self.assertEqual(result, ["用户timeoutnooooo"])
        store = Store(get_database())
        self.assertEqual(store.get(UserVariableSet, "test").billing, 1.0)
        self.assertEqual(store.get(UserVariableSet, "test").name, "nooooo")
        store.close()

        user_state.state = 2
        user_state.last_time = 7
        result = m.timeout_transform(user_state, 20)
        self.assertEqual(result, (["test1nooooo1.00"], False, True))
        self.assertEqual(user_state.state, 1)

        os.remove(os.path.join(current_path, "robot.db"))


if __name__ == '__main__':
    unittest.main()
