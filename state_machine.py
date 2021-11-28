from parser import robot_language
from storm.locals import *
from abc import ABCMeta, abstractmethod
import os
from threading import Lock


class LoginException(Exception):
    pass


class UserVariable:
    __storm_table__ = 'uservariable'
    username = Unicode(primary=True)
    passwd = Unicode()

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd


if "robot.db" in os.listdir("./"):
    os.remove("./robot.db")
database = create_database("sqlite:./robot.db")


class UserState:
    def __init__(self):
        self.state = 0
        self.login = False
        self.last_time = 0
        self.lock = Lock()
        store = Store(database)
        self.variable = store.find(UserVariable, UserVariable.username == "Guest").one()
        store.close()

    def register(self, username, passwd) -> bool:
        store = Store(database)
        if not store.find(UserVariable, UserVariable.username == username).is_empty():
            return False
        with self.lock:
            self.variable = UserVariable(username, passwd)
            self.login = True
        store.add(self.variable)
        store.commit()
        store.close()
        return True

    def login(self, username, passwd) -> bool:
        if username == "Guest":
            return False
        store = Store(database)
        variable = store.find(UserVariable, UserVariable.username == username)
        store.close()
        if variable.is_empty():
            return False
        variable = variable.one()
        if variable.passwd == passwd:
            with self.lock:
                self.variable = variable
            return True
        return False


class Condition(metaclass=ABCMeta):
    @abstractmethod
    def check(self, check_string: str) -> bool:
        pass


class LengthCondition(Condition):
    def __init__(self, op, length):
        self.op = op
        self.length = length

    def __repr__(self):
        return f"Length {self.op} {self.length}"

    def check(self, check_string: str) -> bool:
        if self.op == "<":
            return len(check_string) < self.length
        elif self.op == ">":
            return len(check_string) > self.length
        elif self.op == "<=":
            return len(check_string) <= self.length
        elif self.op == ">=":
            return len(check_string) >= self.length
        elif self.op == "=":
            return len(check_string) == self.length


class ContainCondition(Condition):
    def __init__(self, string):
        self.string = string

    def __repr__(self):
        return f"Contain {self.string}"

    def check(self, check_string: str) -> bool:
        return check_string in self.string


class TypeCondition(Condition):
    def __init__(self, type_):
        self.type = type_

    def __repr__(self):
        return f"Type {self.type}"

    def check(self, check_string: str) -> bool:
        if self.type == "Int":
            return check_string.isdigit()
        elif self.type == "Real":
            try:
                float(check_string)
                return True
            except ValueError:
                return False


class EqualCondition(Condition):
    def __init__(self, string):
        self.string = string

    def __repr__(self):
        return f"Equal {self.string}"

    def check(self, check_string: str) -> bool:
        return check_string.strip() == self.string.strip()


class Action(metaclass=ABCMeta):
    @abstractmethod
    def exec(self, user_state: UserState, response: list, request: str) -> None:
        pass


class ExitAction(Action):
    def __repr__(self):
        return "Exit"

    def exec(self, user_state: UserState, response: list, request: str) -> None:
        with user_state.lock:
            user_state.state = -1


class GotoAction(Action):
    def __init__(self, next_state: int, verified: bool):
        self.next = next_state
        self.verified = verified

    def __repr__(self):
        return f"Goto {self.next}"

    def exec(self, user_state: UserState, response: list, request: str) -> None:
        if not user_state.login and self.verified:
            raise LoginException
        with user_state.lock:
            user_state.state = self.next


class UpdateAction(Action):
    def __init__(self, variable: str, op: str, value, value_check: str):
        if getattr(UserVariable, variable, None) is None:
            raise Exception(f"{variable} 变量名不存在")
        if isinstance(getattr(UserVariable, variable), Int):
            if value == "Copy":
                if value_check != "Int":
                    raise Exception("使用Update Copy时变量类型检查出错")
            elif not isinstance(value, int):
                raise Exception("Update的值和变量类型不同")
        elif isinstance(getattr(UserVariable, variable), Float):
            if value == "Copy":
                if not (value_check == "Real" or value_check == "Int"):
                    raise Exception("使用Update Copy时变量类型检查出错")
            elif not (isinstance(value, float) or isinstance(value, int)):
                raise Exception("Update的值和变量类型不同")
        elif isinstance(getattr(UserVariable, variable), Unicode):
            if value == "Copy":
                if value_check is not None:
                    raise Exception("使用Update Copy时变量类型检查出错")
            if not isinstance(value, str):
                raise Exception("Update的值和变量类型不同")
            if op != "Set":
                raise Exception("Update字符串变量只允许使用Set操作")

        self.variable = variable
        self.op = op
        self.value = value

    def __repr__(self):
        return f"Update {self.variable} {self.op} {self.value}"

    def exec(self, user_state: UserState, response: list, request: str) -> None:
        if self.op == "Add":
            value = getattr(user_state, self.variable)
            if self.value == "Copy":
                if isinstance(getattr(UserState, self.variable), Int):
                    setattr(user_state, self.variable, value + int(request))
                elif isinstance(getattr(UserState, self.variable), Float):
                    setattr(user_state, self.variable, value + float(request))
            else:
                setattr(user_state, self.variable, value + self.value)
        elif self.op == "Sub":
            value = getattr(user_state, self.variable)
            if self.value == "Copy":
                if isinstance(getattr(UserState, self.variable), Int):
                    setattr(user_state, self.variable, value - int(request))
                elif isinstance(getattr(UserState, self.variable), Float):
                    setattr(user_state, self.variable, value - float(request))
            else:
                setattr(user_state, self.variable, value - self.value)
        elif self.op == "Set":
            if self.value == "Copy":
                if isinstance(getattr(UserState, self.variable), Int):
                    setattr(user_state, self.variable, int(request))
                elif isinstance(getattr(UserState, self.variable), Float):
                    setattr(user_state, self.variable, float(request))
                elif isinstance(getattr(UserState, self.variable), Unicode):
                    setattr(user_state, self.variable, request)
            else:
                if isinstance(getattr(UserState, self.variable), Unicode):
                    setattr(user_state, self.variable, self.value[1:-1])
                else:
                    setattr(user_state, self.variable, self.value)


class SpeakAction(Action):
    def __init__(self, contents: list):
        self.contents = contents

    def __repr__(self):
        return "Speak " + " + ".join(self.contents)

    def exec(self, user_state: UserState, response: list, request: str) -> None:
        res = ""
        for content in self.contents:
            if content[0] == '$':
                if getattr(UserVariable, content[1:], None) is None:
                    raise Exception(f"{content[1:]} 变量名不存在")
                res += str(getattr(user_state.variable, content[1:]))
            elif content[0] == '"' and content[-1] == '"':
                res += content[1:-1]
            elif content == "Copy":
                res += request
        response.append(res)


class CaseClause:
    def __init__(self, condition):
        self.condition = condition
        self.actions = []

    def __repr__(self):
        return repr(self.condition) + ": " + "; ".join([repr(i) for i in self.actions])


class StateMachine:
    def _action_constructor(self, language_list: list, target_list: list, index: int, verified: list, value_check):
        for language in language_list:
            if language[0] == "Exit":
                target_list.append(ExitAction())
            elif language[0] == "Goto":
                if language[1] not in self.states:
                    raise Exception("Goto状态不存在")
                target_list.append(GotoAction(self.states.index(language[1]), verified[self.states.index(language[1])]))
            elif language[0] == "Update":
                if not verified[index]:
                    raise Exception("不能在非验证的状态执行Update语句")
                target_list.append(UpdateAction(language[1][1:], language[2], language[3], value_check))
            elif language[0] == "Speak":
                target_list.append(SpeakAction(language[1]))

    def __init__(self, files):
        result = []
        for file in files:
            if len(file) == 0:
                continue
            result += robot_language.parse_file(file, parse_all=True).as_list()
        self.states = []
        verified = []
        create_table_statement = "CREATE TABLE uservariable (username TEXT PRIMARY KEY, passwd TEXT, "
        for definition in result:
            if definition[0] == "Variable":
                for clause in definition[1]:
                    if getattr(UserVariable, clause[0], None) is not None:
                        raise Exception("变量命名冲突")
                    if clause[1] == "Int":
                        setattr(UserVariable, clause[0][1:], Int(default=clause[2]))
                        create_table_statement += f"{clause[0][1:]} INT, "
                    elif clause[1] == "Real":
                        setattr(UserVariable, clause[0][1:], Float(default=clause[2]))
                        create_table_statement += f"{clause[0][1:]} REAL, "
                    elif clause[1] == "Text":
                        setattr(UserVariable, clause[0][1:], Unicode(default=clause[2][1:-1]))
                        create_table_statement += f"{clause[0][1:]} TEXT, "
            elif definition[0] == "State":
                if definition[1] not in self.states:
                    self.states.append(definition[1])
                    if len(definition[2]) == 0:
                        verified.append(False)
                    else:
                        verified.append(True)
                else:
                    raise Exception("状态命名冲突")

        if "Welcome" not in self.states:
            raise Exception("没有Welcome状态")
        else:
            welcome_index = self.states.index("Welcome")
            if verified[welcome_index]:
                raise Exception("Welcome状态必须不为Verified")
            verified[welcome_index] = verified[0]
            verified[0] = False
            self.states[welcome_index] = self.states[0]
            self.states[0] = "Welcome"

        create_table_statement = create_table_statement[:-2] + ')'
        store = Store(database)
        store.execute(create_table_statement)
        store.add(UserVariable("Guest", ''))
        store.commit()
        store.close()

        self.speak = []
        self.case = []
        self.default = []
        self.timeout = []
        state_index = -1
        for definition in result:
            if definition[0] != "State":
                continue
            state_index += 1

            # Speak子句
            self.speak.append([])
            if len(definition[3]) != 0:
                self._action_constructor(definition[3], self.speak[-1], state_index, verified, None)

            # Case子句
            self.case.append([])
            if len(definition[4]) != 0:
                for case_list in definition[4]:
                    value_check = None
                    if case_list[1] == "Length":
                        self.case[-1].append(CaseClause(LengthCondition(case_list[2], case_list[3])))
                    elif case_list[1] == "Contain":
                        self.case[-1].append(CaseClause(ContainCondition(case_list[2][1:-1])))
                    elif case_list[1] == "Type":
                        self.case[-1].append(CaseClause(TypeCondition(case_list[2])))
                        if case_list[2] == "Int" or case_list[2] == "Real":
                            value_check = case_list[2]
                    elif case_list[1][0] == '"' and case_list[1][-1] == '"':
                        self.case[-1].append(CaseClause(EqualCondition(case_list[1][1:-1])))

                    self._action_constructor(case_list[-1], self.case[-1][-1].actions, state_index, verified,
                                             value_check)

            # Default子句
            self.default.append([])
            self._action_constructor(definition[5][1], self.default[-1], state_index, verified, None)

            # Timeout子句
            self.timeout.append(dict())
            if len(definition[6]) != 0:
                for timeout_list in definition[6]:
                    self.timeout[-1][timeout_list[1]] = []
                    self._action_constructor(timeout_list[-1], self.timeout[-1][timeout_list[1]],
                                             state_index, verified, None)

    def hello(self, user_state: UserState) -> list:
        response = []
        for action in self.speak[user_state.state]:
            action.exec(user_state, response, "")
        return response

    def condition_transform(self, user_state: UserState, msg: str) -> list:
        response = []
        old_state = user_state.state
        for case in self.case[user_state.state]:
            if case.condition.check(msg):
                for action in case.actions:
                    action.exec(user_state, response, msg)
                if user_state.state != old_state:
                    response += self.hello(user_state)
                return response
        for action in self.default[user_state.state]:
            action.exec(user_state, response, msg)
        if user_state.state != old_state:
            response += self.hello(user_state)
        return response

    def timeout_transform(self, user_state: UserState, now_seconds: int) -> list:
        response = []
        with user_state.lock:
            last_seconds = user_state.last_time
            user_state.last_time = now_seconds
        old_state = user_state.state
        for timeout_sec in self.timeout[user_state.state].keys():
            if last_seconds < timeout_sec <= now_seconds:
                for action in self.timeout[user_state.state][timeout_sec]:
                    action.exec(user_state, response, None)
                if user_state.state != old_state:
                    response += self.hello(user_state)
        return response


if __name__ == '__main__':
    m = StateMachine(["grammar.txt"])
    print(m.states)
    print(m.speak)
    print(m.case)
    print(m.default)
    print(m.timeout)
