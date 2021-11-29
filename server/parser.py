import pyparsing as pp

integer_constant = pp.Regex("[-+]?[0-9]+").set_parse_action(lambda tokens: int(tokens[0]))
real_constant = pp.Regex("[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?").set_parse_action(lambda tokens: float(tokens[0]))
string_constant = pp.quoted_string('"')

variable = pp.Combine('$' + pp.Regex("[A-Za-z_][0-9A-Za-z_]*"))
variable_clause = pp.Group(variable + ((pp.Keyword("Int") + integer_constant) ^ (pp.Keyword("Real") + real_constant) ^ (
        pp.Keyword("Text") + string_constant)))
variable_definition = pp.Group(pp.Keyword("Variable") + pp.Group(pp.OneOrMore(variable_clause)))

length_condition = pp.Keyword("Length") + pp.oneOf("< > <= >= =") + integer_constant
contain_condition = pp.Keyword("Contain") + string_constant
type_condition = pp.Keyword("Type") + (pp.Keyword("Int") ^ pp.Keyword("Real"))
equal_condition = string_constant
conditions = length_condition ^ contain_condition ^ type_condition ^ equal_condition

exit_action = pp.Group(pp.Keyword("Exit"))
goto_action = pp.Group(pp.Keyword("Goto") + pp.Word(pp.alphas))
update_action = pp.Group(pp.Keyword("Update") + variable + (
        ((pp.Keyword("Add") ^ pp.Keyword("Sub") ^ pp.Keyword("Set")) + (real_constant ^ pp.Keyword("Copy"))) ^ (
        pp.Keyword("Set") + (string_constant("string") ^ pp.Keyword("Copy")))))
speak_content = variable ^ string_constant
speak_action = pp.Group(pp.Keyword("Speak") + pp.Group(
    (speak_content + pp.ZeroOrMore('+' + speak_content)).set_parse_action(lambda tokens: tokens[0::2])))
speak_action_copy = pp.Group(pp.Keyword("Speak") + pp.Group(
    ((speak_content ^ pp.Keyword("Copy")) + pp.ZeroOrMore(
        '+' + (speak_content ^ pp.Keyword("Copy")))).set_parse_action(lambda tokens: tokens[0::2])))
actions = exit_action ^ goto_action ^ update_action ^ speak_action_copy

case_clause = pp.Group(
    pp.Keyword("Case") + conditions + pp.Group(pp.ZeroOrMore(update_action ^ speak_action_copy) + pp.Opt(
        exit_action ^ goto_action)))
default_clause = pp.Group(pp.Keyword("Default") + pp.Group(pp.ZeroOrMore(update_action ^ speak_action_copy) + pp.Opt(
    exit_action ^ goto_action)))
timeout_clause = pp.Group(pp.Keyword("Timeout") + integer_constant + pp.Group(pp.ZeroOrMore(speak_action) + pp.Opt(
    exit_action ^ goto_action)))

state_definition = pp.Group(
    pp.Keyword("State") + pp.Word(pp.alphas) + pp.Group(pp.Opt(pp.Keyword("Verified"))) + pp.Group(
        pp.ZeroOrMore(speak_action)) + pp.Group(pp.ZeroOrMore(case_clause)) + default_clause + pp.Group(
        pp.ZeroOrMore(timeout_clause)))


class RobotLanguage:
    _language = pp.ZeroOrMore(state_definition ^ variable_definition)

    @staticmethod
    def parse_files(files: list[str]) -> list[pp.ParseResults]:
        result = []
        for file in files:
            if len(file) == 0:
                continue
            result += RobotLanguage._language.parse_file(file, parse_all=True).as_list()
        return result


if __name__ == '__main__':
    print(RobotLanguage.parse_files(["grammar.txt"]))
