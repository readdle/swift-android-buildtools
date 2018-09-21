from argparse import ArgumentParser, OPTIONAL, ONE_OR_MORE, ArgumentError
from gettext import gettext as _, ngettext
import re


"""
Workaround parser to froward args without ugly -Xforward='-forwarded'

:see https://bugs.python.org/issue9334
"""
class ArgumentParserOpt(ArgumentParser):
    def _match_argument(self, action, arg_strings_pattern):
        # match the pattern for this action to the arg strings
        nargs_pattern = self._get_nargs_pattern(action)
        match = re.match(nargs_pattern, arg_strings_pattern)

        # if no match, see if we can emulate optparse and return the
        # required number of arguments regardless of their values
        #
        if match is None:
            import numbers
            nargs = action.nargs if action.nargs is not None else 1
            if isinstance(nargs, numbers.Number) and len(arg_strings_pattern) >= nargs:
                return nargs

        # raise an exception if we weren't able to find a match
        if match is None:
            nargs_errors = {
                None: _('expected one argument'),
                OPTIONAL: _('expected at most one argument'),
                ONE_OR_MORE: _('expected at least one argument'),
            }
            default = ngettext('expected %s argument',
                               'expected %s arguments',
                               action.nargs) % action.nargs
            msg = nargs_errors.get(action.nargs, default)
            raise ArgumentError(action, msg)

        # return the number of arguments matched
        return len(match.group(1))
