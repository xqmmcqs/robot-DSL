"""状态机模块。

此模块读取脚本语言语法分析的结果，并且构建状态机模型。

状态机是拓广的Mealy状态机，给定一个输入，可以进行状态转移并且产生输出。可行的输入包括一条用户消息，或者用户超时的时长，输出通常为一个字符串序列。

此模块同时维护一个数据库，存储用户相关的变量。

Copyright (c) 2021 Ziheng Mao.
"""

import os
from abc import ABCMeta, abstractmethod
from threading import Lock
from typing import Any, Union, Optional
from storm.locals import create_database, Store
from storm.properties import Unicode, Int, Float
from pyparsing import ParseException
from server.parser import RobotLanguage


class LoginError(Exception):
    """表示用户未登录的错误。"""
    pass


class GrammarError(Exception):
    """表示脚本语言的语法错误。

    :ivar msg: 错误消息。
    :ivar context: 错误上下文。
    """

    def __init__(self, msg: str, context: list[str]) -> None:
        self.msg = msg
        self.context = context


class UserVariableSet(object):
    """用户变量集，与数据库关联。

    采用storm作为ORM，除了 ``column_type`` 之外各个类属性关联到数据库表中的一列，实例中的相关属性关联到元组的对应属性。

    用户的基础属性包括用户名和密码，其他属性则通过 ``setattr`` 动态添加。

    :var column_type: 表中各列的类型。
    """
    __storm_table__ = 'user_variable'
    column_type = {"username": "Text", "passwd": "Text"}
    username = Unicode(primary=True)
    passwd = Unicode()

    def __init__(self, username: str, passwd: str) -> None:
        self.username = username
        self.passwd = passwd


class UserState(object):
    """用户状态对象。

    :ivar state: 用户在状态机中所处的状态。
    :ivar have_login: 用户是否已经登录。
    :ivar last_time: 距离用户上次发送消息过去的秒数。
    :ivar lock: 互斥锁。
    :ivar username: 用户名。
    """

    def __init__(self) -> None:
        self.state = 0
        self.have_login = False
        self.last_time = 0
        self.lock = Lock()
        self.username = "Guest"

    def register(self, username: str, passwd: str) -> bool:
        """注册新用户。

        首先在数据库中查找用户是否存在，如果不存在，则向数据库中添加一个新用户，并且更新用户名和登录信息。

        :param username: 用户名。
        :param passwd: 密码。
        :return: 如果注册成功，返回True；否则返回False。
        """
        global database, db_lock
        with db_lock:
            store = Store(database)
            if store.get(UserVariableSet, username) is not None:  # 用户已经存在
                store.close()
                return False
            with self.lock:
                self.username = username
                variable_set = UserVariableSet(username, passwd)
                self.have_login = True
            store.add(variable_set)  # 添加新的行
            store.commit()
            store.close()
            return True

    def login(self, username: str, passwd: str) -> bool:
        """用户登录。

        在数据库中查找用户信息，并且验证密码是否正确。

        :param username: 用户名。
        :param passwd: 密码。
        :return: 如果登录成功，返回True；否则返回False。
        """
        if username == "Guest":  # 不能登录访客用户
            return False
        global database, db_lock
        with db_lock:
            store = Store(database)
            variable_set = store.get(UserVariableSet, username)
            if variable_set is None:  # 用户不存在
                store.close()
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
    """条件判断抽象基类。"""

    @abstractmethod
    def check(self, check_string: str) -> bool:
        """判断是否满足条件。

        :param check_string: 需要判断的字符串。
        :return: 如果满足条件，返回True；否则返回False。
        """
        pass


class LengthCondition(Condition):
    """长度判断条件，判断用户输入是否满足长度限制。

    :ivar op: 判断运算符，可以为 ``<``、``>``、``<=``、``>=``、``=`` 其中之一。
    :ivar length: 长度。
    """

    def __init__(self, op: str, length: int) -> None:
        self.op = op
        self.length = length

    def __repr__(self) -> str:
        return f"Length {self.op} {self.length}"

    def check(self, check_string: str) -> bool:
        """
        参考：:py:meth:`Condition.check`
        """
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
    """字符串包含判断条件，判断用户输入是否包含给定串。

    :ivar string: 包含的字符串。
    """

    def __init__(self, string: str) -> None:
        self.string = string

    def __repr__(self) -> str:
        return f"Contain {self.string}"

    def check(self, check_string: str) -> bool:
        """
        参考：:py:meth:`Condition.check`
        """
        return self.string in check_string


class TypeCondition(Condition):
    """字符串字面值类型判断，判断用户输入是否是某种类型。

    :ivar type: 类型，可以为 ``Int``、``Real`` 之一。
    """

    def __init__(self, type_: str) -> None:
        self.type = type_

    def __repr__(self) -> str:
        return f"Type {self.type}"

    def check(self, check_string: str) -> bool:
        """
        参考：:py:meth:`Condition.check`
        """
        if self.type == "Int":
            return check_string.isdigit()
        elif self.type == "Real":
            try:
                float(check_string)
                return True
            except ValueError:
                return False


class EqualCondition(Condition):
    """字符串相等判断，判断用户输入是否和某一个串相等。

    :ivar string: 字符串。
    """

    def __init__(self, string: str) -> None:
        self.string = string

    def __repr__(self) -> str:
        return f"Equal {self.string}"

    def check(self, check_string: str) -> bool:
        """
        参考：:py:meth:`Condition.check`
        """
        return check_string.strip() == self.string.strip()


class Action(metaclass=ABCMeta):
    """动作抽象基类。"""

    @abstractmethod
    def exec(self, user_state: UserState, response: list[str], request: Any) -> None:
        """执行一个动作。

        :param user_state: 用户状态。
        :param response: 产生回复字符串列表。
        :param request: 用户请求字符串。
        """
        pass


class ExitAction(Action):
    """退出动作，结束一个会话。"""

    def __repr__(self):
        return "Exit"

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        """
        参考：:py:meth:`Action.exec`
        """
        with user_state.lock:
            user_state.state = -1


class GotoAction(Action):
    """状态转移动作，转移到一个新状态。

    :ivar next: 转移到的状态。
    :ivar verified: 新状态是否需要登录验证。
    """

    def __init__(self, next_state: int, verified: bool) -> None:
        self.next = next_state
        self.verified = verified

    def __repr__(self):
        return f"Goto {self.next}"

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        """
        参考：:py:meth:`Action.exec`
        """
        if not user_state.have_login and self.verified:
            raise LoginError
        with user_state.lock:
            user_state.state = self.next


class UpdateAction(Action):
    """更新用户变量动作。

    :ivar variable: 变量名。
    :ivar op: 更新操作类型，可以是 ``Add``、``Sub``、``Set`` 之一。
    :ivar value: 更新的值，可以是以双引号开头和结尾的字符串、"Copy"或者一个数字。
    :ivar value_check: 该动作是否处于什么样的类型检查环境，可以是 ``Int``、``Real``、``Text`` 或者None。
    """

    def __init__(self, variable: str, op: str, value: Union[str, int, float], value_check: Optional[str]) -> None:
        if UserVariableSet.column_type.get(variable) is None:
            raise GrammarError(f"{variable} 变量名不存在", ["Update", variable, op, value])
        if UserVariableSet.column_type[variable] == "Int":  # 变量类型是整数
            if value == "Copy":
                if value_check != "Int":  # 必须进行整数类型检查
                    raise GrammarError("使用Update Copy时变量类型检查出错", ["Update", variable, op, value])
            elif not (isinstance(value, float) or isinstance(value, int)) or int(value) != value:  # 字面值必须是整数
                raise GrammarError("Update的值和变量类型不同", ["Update", variable, op, int(value)])
        elif UserVariableSet.column_type[variable] == "Real":  # 变量类型是实数
            if value == "Copy":
                if not (value_check == "Real" or value_check == "Int"):  # 必须进行整数或者浮点数类型检查
                    raise GrammarError("使用Update Copy时变量类型检查出错", ["Update", variable, op, value])
            elif not isinstance(value, float):  # 字面值必须是浮点数
                raise GrammarError("Update的值和变量类型不同", ["Update", variable, op, value])
        elif UserVariableSet.column_type[variable] == "Text":
            if value == "Copy":
                if value_check is None:  # 必须进行类型检查
                    raise GrammarError("使用Update Copy时变量类型检查出错", ["Update", variable, op, value])
            if not isinstance(value, str):  # 字面值必须是字符串
                raise GrammarError("Update的值和变量类型不同", ["Update", variable, op, value])
            if op != "Set":  # 字符串只能进行Set操作
                raise GrammarError("Update字符串变量只允许使用Set操作", ["Update", variable, op, value])

        self.variable = variable
        self.op = op
        self.value = value

    def __repr__(self) -> str:
        return f"Update {self.variable} {self.op} {self.value}"

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        """
        参考：:py:meth:`Action.exec`
        """
        global database, db_lock
        with db_lock:
            store = Store(database)
            variable_set: UserVariableSet = store.get(UserVariableSet, user_state.username)  # 得到用户的变量集
            if self.op == "Add":
                value = getattr(variable_set, self.variable)
                if self.value == "Copy":  # 根据用户输入处理值
                    if UserVariableSet.column_type[self.variable] == "Int":
                        setattr(variable_set, self.variable, value + int(request))
                    elif UserVariableSet.column_type[self.variable] == "Real":
                        setattr(variable_set, self.variable, value + float(request))
                else:
                    setattr(variable_set, self.variable, value + self.value)
            elif self.op == "Sub":
                value = getattr(variable_set, self.variable)
                if self.value == "Copy":  # 根据用户输入处理值
                    if UserVariableSet.column_type[self.variable] == "Int":
                        setattr(variable_set, self.variable, value - int(request))
                    elif UserVariableSet.column_type[self.variable] == "Real":
                        setattr(variable_set, self.variable, value - float(request))
                else:
                    setattr(variable_set, self.variable, value - self.value)
            elif self.op == "Set":
                if self.value == "Copy":  # 根据用户输入处理值
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
    """产生回复动作。

    :ivar contents: 回复内容列表。
    """

    def __init__(self, contents: list[str]) -> None:
        self.contents = contents
        for content in self.contents:
            if content[0] == '$':
                if UserVariableSet.column_type.get(content[1:]) is None:
                    raise GrammarError(f"{content[1:]} 变量名不存在", ["Speak"] + contents)

    def __repr__(self) -> str:
        return "Speak " + " + ".join(self.contents)

    def exec(self, user_state: UserState, response: list[str], request: str) -> None:
        """
        参考：:py:meth:`Action.exec`
        """
        res = ""
        global database, db_lock
        with db_lock:
            for content in self.contents:
                if content[0] == '$':  # 输出变量的值
                    store = Store(database)
                    variable_set = store.get(UserVariableSet, user_state.username)
                    res += str(getattr(variable_set, content[1:]))
                    store.close()
                elif content[0] == '"' and content[-1] == '"':  # 输出字符串
                    res += content[1:-1]
                elif content == "Copy":  # 输出用户的输入
                    res += request
        response.append(res)


class CaseClause(object):
    """条件分支。

    :ivar condition: 条件。
    :ivar action: 满足条件后执行的动作列表。
    """

    def __init__(self, condition: Condition) -> None:
        self.condition = condition
        self.actions: list[Action] = []

    def __repr__(self) -> str:
        return repr(self.condition) + ": " + "; ".join([repr(i) for i in self.actions])


def init_database(path) -> None:
    """初始化数据库。

    :param path: 数据库路径。
    """
    global database, db_lock
    dir, file_name = os.path.split(path)
    if file_name in os.listdir(dir):
        os.remove(path)
    database = create_database("sqlite:" + path)
    db_lock = Lock()


def get_database():
    """返回数据库。"""
    global database
    return database


class StateMachine(object):
    """状态机。

    :ivar states: 状态集合。
    :ivar speak: 状态默认的speak语句集合。
    :ivar case: 状态的条件分支集合。
    :ivar default: 状态的默认分支。
    :ivar timeout: 状态的超时转移分支。
    """

    def _action_constructor(self, language_list: list, target_list: list[Action], index: int, verified: list[bool],
                            value_check: Optional[str]) -> None:
        """构建一个动作列表。

        :param language_list: 语法树的子树，包含一系列动作。
        :param target_list: 构建的动作列表存储到此。
        :param index: 状态编号。
        :param verified: 状态是否需要登录验证。
        :param value_check: 参考:py:class:`UpdateAction`。
        """
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

        create_table_statement = ["CREATE TABLE user_variable (username TEXT PRIMARY KEY, passwd TEXT"]  # 建表语句
        # 处理变量定义和状态集
        for definition in result:
            if definition[0] == "Variable":  # 处理变量定义
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
            elif definition[0] == "State":  # 处理状态定义
                if definition[1] not in self.states:
                    self.states.append(definition[1])  # 将状态名加入状态集
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

        # 建立数据库
        global database, db_lock
        with db_lock:
            store = Store(database)
            store.execute(','.join(create_table_statement) + ')')
            store.add(UserVariableSet("Guest", ''))  # 创建默认的访客用户
            store.commit()
            store.close()

        state_index = -1
        # 处理各个分支和动作
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
        """输出某个状态的默认 ``speak`` 动作。

        :param user_state: 用户状态。
        :return: 输出的字符串列表。
        """
        response: list[str] = []
        for action in self.speak[user_state.state]:
            action.exec(user_state, response, None)
        return response

    def condition_transform(self, user_state: UserState, msg: str) -> list[str]:
        """条件转移。

        :param user_state: 用户状态
        :param msg: 用户输入。
        :return: 输出的字符串列表。
        """
        response: list[str] = []
        for case in self.case[user_state.state]:
            if case.condition.check(msg):
                for action in case.actions:
                    action.exec(user_state, response, msg)
                if user_state.state != -1:  # 新状态的speak动作
                    response += self.hello(user_state)
                return response
        for action in self.default[user_state.state]:
            action.exec(user_state, response, msg)
        if user_state.state != -1:  # 新状态的speak动作
            response += self.hello(user_state)
        return response

    def timeout_transform(self, user_state: UserState, now_seconds: int) -> (list[str], bool, bool):
        """超时转移。

        :param user_state: 用户状态。
        :param now_seconds: 用户未执行操作的秒数。
        :return: 输出的字符串列表、是否需要结束会话、是否转移到新的状态。
        """
        response: list[str] = []
        with user_state.lock:
            last_seconds = user_state.last_time
            user_state.last_time = now_seconds
        old_state = user_state.state
        for timeout_sec in self.timeout[user_state.state].keys():
            if last_seconds < timeout_sec <= now_seconds:  # 检查字典的键是否在时间间隔内
                for action in self.timeout[user_state.state][timeout_sec]:
                    action.exec(user_state, response, "")
                if old_state != user_state.state:  # 如果旧状态和新状态不同，执行新状态的speak动作
                    if user_state.state != -1:
                        response += self.hello(user_state)
                    break
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
