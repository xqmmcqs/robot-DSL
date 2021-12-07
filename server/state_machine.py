"""状态机模块。

"""

import os
from abc import ABCMeta, abstractmethod
from threading import Lock
from typing import Any, Union
from storm.locals import create_database, Store
from storm.properties import Unicode, Int, Float
from pyparsing import ParseException
from server.parser import RobotLanguage


class LoginError(Exception):
    pass


class GrammarError(Exception):
    def __init__(self, msg: str, context: list[str]) -> None:
        self.msg = msg
        self.context = context


class UserVariableSet(object):
    __storm_table__ = 'user_variable'
    column_type = {"username": "Text", "passwd": "Text"}
    username = Unicode(primary=True)
    passwd = Unicode()

    def __init__(self, username: str, passwd: str) -> None:
        self.username = username
        self.passwd = passwd


class UserState(object):
    def __init__(self) -> None:
        self.state = 0
        self.have_login = False
        self.last_time = 0
        self.lock = Lock()
        self.username = "Guest"

    def register(self, username: str, passwd: str) -> bool:
        global database
        store = Store(database)
        if store.get(UserVariableSet, username) is not None:
            return False
        with self.lock:
            self.username = username
            variable_set = UserVariableSet(username, passwd)
            self.have_login = True
        store.add(variable_set)
        store.commit()
        store.close()
        return True

    def login(self, username: str, passwd: str) -> bool:
        if username == "Guest":
            return False
        global database
        store = Store(database)
        variable_set = store.get(UserVariableSet, username)
        if variable_set is None:
            return False
        if variable_set.passwd == passwd:
            with self.lock:
                self.username = username
                self.have_login = True
            store.close()
            return True
        store.close()
        return False


class Condition(metaclass=ABCMeta):
    @abstractmethod
    def check(self, check_string: str) -> bool:
        pass


class LengthCondition(Condition):
    def __init__(self, op: str, length: int) -> None:
        self.op = op
        self.length = length

    def __repr__(self) -> str:
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
    def __init__(self, string: str) -> None:
        self.string = string

    def __repr__(self) -> str:
        return f"Contain {self.string}"

    def check(self, check_string: str) -> bool:
        return check_string in self.string


class TypeCondition(Condition):
    def __init__(self, type_: str) -> None:
        self.type = type_

    def __repr__(self) -> str:
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
    def __init__(self, string: str) -> None:
        self.string = string

    def __repr__(self) -> str:
        return f"Equal {self.string}"

    def check(self, check_string: str) -> bool:
        return check_string.strip() == self.string.strip()


class Action(metaclass=ABCMeta):
    @abstractmethod
    def exec(self, user_state: UserState, response: list[str], request: Any) -> None:
        pass


class ExitAction(Action):
    def __repr__(self):
        return "Exit"

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        with user_state.lock:
            user_state.state = -1


class GotoAction(Action):
    def __init__(self, next_state: int, verified: bool) -> None:
        self.next = next_state
        self.verified = verified

    def __repr__(self):
        return f"Goto {self.next}"

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        if not user_state.have_login and self.verified:
            raise LoginError
        with user_state.lock:
            user_state.state = self.next


class UpdateAction(Action):
    def __init__(self, variable: str, op: str, value: Union[str, int, float], value_check: Union[str, None]) -> None:
        if UserVariableSet.column_type.get(variable) is None:
            raise GrammarError(f"{variable} 变量名不存在", ["Update", variable, op, value])
        if UserVariableSet.column_type[variable] == "Int":
            if value == "Copy":
                if value_check != "Int":
                    raise GrammarError("使用Update Copy时变量类型检查出错", ["Update", variable, op, value])
            elif not (isinstance(value, float) or isinstance(value, int)) or int(value) != value:
                raise GrammarError("Update的值和变量类型不同", ["Update", variable, op, int(value)])
        elif UserVariableSet.column_type[variable] == "Real":
            if value == "Copy":
                if not (value_check == "Real" or value_check == "Int"):
                    raise GrammarError("使用Update Copy时变量类型检查出错", ["Update", variable, op, value])
            elif not isinstance(value, float):
                raise GrammarError("Update的值和变量类型不同", ["Update", variable, op, value])
        elif UserVariableSet.column_type[variable] == "Text":
            if value == "Copy":
                if value_check is None:
                    raise GrammarError("使用Update Copy时变量类型检查出错", ["Update", variable, op, value])
            if not isinstance(value, str):
                raise GrammarError("Update的值和变量类型不同", ["Update", variable, op, value])
            if op != "Set":
                raise GrammarError("Update字符串变量只允许使用Set操作", ["Update", variable, op, value])

        self.variable = variable
        self.op = op
        self.value = value

    def __repr__(self) -> str:
        return f"Update {self.variable} {self.op} {self.value}"

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        global database
        store = Store(database)
        variable_set: UserVariableSet = store.get(UserVariableSet, user_state.username)
        if self.op == "Add":
            value = getattr(variable_set, self.variable)
            if self.value == "Copy":
                if UserVariableSet.column_type[self.variable] == "Int":
                    setattr(variable_set, self.variable, value + int(request))
                elif UserVariableSet.column_type[self.variable] == "Real":
                    setattr(variable_set, self.variable, value + float(request))
            else:
                setattr(variable_set, self.variable, value + self.value)
        elif self.op == "Sub":
            value = getattr(variable_set, self.variable)
            if self.value == "Copy":
                if UserVariableSet.column_type[self.variable] == "Int":
                    setattr(variable_set, self.variable, value - int(request))
                elif UserVariableSet.column_type[self.variable] == "Real":
                    setattr(variable_set, self.variable, value - float(request))
            else:
                setattr(variable_set, self.variable, value - self.value)
        elif self.op == "Set":
            if self.value == "Copy":
                if UserVariableSet.column_type[self.variable] == "Int":
                    setattr(variable_set, self.variable, int(request))
                elif UserVariableSet.column_type[self.variable] == "Real":
                    setattr(variable_set, self.variable, float(request))
                elif UserVariableSet.column_type[self.variable] == "Text":
                    setattr(variable_set, self.variable, request)
            else:
                if UserVariableSet.column_type[self.variable] == "Text":
                    setattr(variable_set, self.variable, self.value[1:-1])
                else:
                    setattr(variable_set, self.variable, self.value)
        store.commit()
        store.close()


class SpeakAction(Action):
    def __init__(self, contents: list[str]) -> None:
        self.contents = contents
        for content in self.contents:
            if content[0] == '$':
                if UserVariableSet.column_type.get(content[1:]) is None:
                    raise GrammarError(f"{content[1:]} 变量名不存在", ["Speak"] + contents)

    def __repr__(self) -> str:
        return "Speak " + " + ".join(self.contents)

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        res = ""
        global database
        for content in self.contents:
            if content[0] == '$':
                store = Store(database)
                variable_set = store.get(UserVariableSet, user_state.username)
                res += str(getattr(variable_set, content[1:]))
                store.close()
            elif content[0] == '"' and content[-1] == '"':
                res += content[1:-1]
            elif content == "Copy":
                res += request
        response.append(res)


class CaseClause(object):
    def __init__(self, condition: Condition) -> None:
        self.condition = condition
        self.actions: list[Action] = []

    def __repr__(self) -> str:
        return repr(self.condition) + ": " + "; ".join([repr(i) for i in self.actions])


def init_database(path):
    global database
    dir, file_name = os.path.split(path)
    if file_name in os.listdir(dir):
        os.remove(path)
    database = create_database("sqlite:" + path)


def get_database():
    global database
    return database


class StateMachine(object):
    def _action_constructor(self, language_list: list, target_list: list[Action], index: int, verified: list[bool],
                            value_check) -> None:
        for language in language_list:
            if language[0] == "Exit":
                target_list.append(ExitAction())
            elif language[0] == "Goto":
                if language[1] not in self.states:
                    raise GrammarError("Goto状态不存在", language)
                target_list.append(GotoAction(self.states.index(language[1]), verified[self.states.index(language[1])]))
            elif language[0] == "Update":
                if not verified[index]:
                    raise GrammarError("不能在非验证的状态执行Update语句", language)
                target_list.append(UpdateAction(language[1][1:], language[2], language[3], value_check))
            elif language[0] == "Speak":
                target_list.append(SpeakAction(language[1]))

    def __init__(self, files: list[str]) -> None:
        try:
            result = RobotLanguage.parse_files(files)
        except ParseException as err:
            raise GrammarError(err.__str__(), [err.line])
        self.states: list[str] = []
        verified: list[bool] = []
        self.speak: list[list[Action]] = []
        self.case: list[list[CaseClause]] = []
        self.default: list[list[Action]] = []
        self.timeout: list[dict[int, list[Action]]] = []

        create_table_statement = ["CREATE TABLE user_variable (username TEXT PRIMARY KEY, passwd TEXT"]
        for definition in result:
            if definition[0] == "Variable":
                for clause in definition[1]:
                    if UserVariableSet.column_type.get(clause[0]) is not None:
                        raise GrammarError("变量命名冲突", clause)
                    if clause[1] == "Int":
                        setattr(UserVariableSet, clause[0][1:], Int(default=clause[2]))
                        UserVariableSet.column_type[clause[0][1:]] = "Int"
                        create_table_statement.append(f"{clause[0][1:]} INT")
                    elif clause[1] == "Real":
                        setattr(UserVariableSet, clause[0][1:], Float(default=clause[2]))
                        UserVariableSet.column_type[clause[0][1:]] = "Real"
                        create_table_statement.append(f"{clause[0][1:]} REAL")
                    elif clause[1] == "Text":
                        setattr(UserVariableSet, clause[0][1:], Unicode(default=clause[2][1:-1]))
                        UserVariableSet.column_type[clause[0][1:]] = "Text"
                        create_table_statement.append(f"{clause[0][1:]} TEXT")
            elif definition[0] == "State":
                if definition[1] not in self.states:
                    self.states.append(definition[1])
                    if len(definition[2]) == 0:
                        verified.append(False)
                    else:
                        verified.append(True)
                else:
                    raise GrammarError("状态命名冲突", definition[:1])

        if "Welcome" not in self.states:
            raise GrammarError("没有Welcome状态", [])
        else:
            welcome_index = self.states.index("Welcome")
            if verified[welcome_index]:
                raise GrammarError("Welcome状态必须不为Verified", [])
            verified[welcome_index] = verified[0]
            verified[0] = False
            self.states[welcome_index] = self.states[0]
            self.states[0] = "Welcome"

        global database
        store = Store(database)
        store.execute(','.join(create_table_statement) + ')')
        store.add(UserVariableSet("Guest", ''))
        store.commit()
        store.close()

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
                    value_check = "Text"
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
            self._action_constructor(definition[5][1], self.default[-1], state_index, verified, "Text")

            # Timeout子句
            self.timeout.append(dict())
            if len(definition[6]) != 0:
                for timeout_list in definition[6]:
                    self.timeout[-1][timeout_list[1]] = []
                    self._action_constructor(timeout_list[-1], self.timeout[-1][timeout_list[1]],
                                             state_index, verified, None)

    def hello(self, user_state: UserState) -> list[str]:
        response: list[str] = []
        for action in self.speak[user_state.state]:
            action.exec(user_state, response, None)
        return response

    def condition_transform(self, user_state: UserState, msg: str) -> list[str]:
        response: list[str] = []
        for case in self.case[user_state.state]:
            if case.condition.check(msg):
                for action in case.actions:
                    action.exec(user_state, response, msg)
                if user_state.state != -1:
                    response += self.hello(user_state)
                return response
        for action in self.default[user_state.state]:
            action.exec(user_state, response, msg)
        if user_state.state != -1:
            response += self.hello(user_state)
        return response

    def timeout_transform(self, user_state: UserState, now_seconds: int) -> (list[str], bool, bool):
        response: list[str] = []
        with user_state.lock:
            last_seconds = user_state.last_time
            user_state.last_time = now_seconds
        old_state = user_state.state
        for timeout_sec in self.timeout[user_state.state].keys():
            if last_seconds < timeout_sec <= now_seconds:
                for action in self.timeout[user_state.state][timeout_sec]:
                    action.exec(user_state, response, "")
                if user_state.state != -1 and old_state != user_state.state:
                    response += self.hello(user_state)
        return response, user_state.state == -1, old_state != user_state.state


if __name__ == '__main__':
    init_database("../robot.db")
    try:
        m = StateMachine(["../test/parser/case2.txt"])
        print(m.states)
        print(m.speak)
        print(m.case)
        print(m.default)
        print(m.timeout)
    except GrammarError as err:
        print(" ".join([str(item) for item in err.context]))
        print("GrammarError: ", err.msg)
