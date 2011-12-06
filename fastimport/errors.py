# Copyright (C) 2008 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Exception classes for fastimport"""

# Prefix to messages to show location information
_LOCATION_FMT = "line %(lineno)d: "

class FastImportError(Exception):

    def __str__(self):
        return self._fmt % self.__dict__


class ParsingError(FastImportError):
    """The base exception class for all import processing exceptions."""

    _fmt = _LOCATION_FMT + "Unknown Import Parsing Error"

    def __init__(self, lineno):
        FastImportError.__init__(self)
        self.lineno = lineno


class MissingBytes(ParsingError):
    """Raised when EOF encountered while expecting to find more bytes."""

    _fmt = (_LOCATION_FMT + "Unexpected EOF - expected %(expected)d bytes,"
        " found %(found)d")

    def __init__(self, lineno, expected, found):
        ParsingError.__init__(self, lineno)
        self.expected = expected
        self.found = found


class MissingTerminator(ParsingError):
    """Raised when EOF encountered while expecting to find a terminator."""

    _fmt = (_LOCATION_FMT +
        "Unexpected EOF - expected '%(terminator)s' terminator")

    def __init__(self, lineno, terminator):
        ParsingError.__init__(self, lineno)
        self.terminator = terminator


class InvalidCommand(ParsingError):
    """Raised when an unknown command found."""

    _fmt = (_LOCATION_FMT + "Invalid command '%(cmd)s'")

    def __init__(self, lineno, cmd):
        ParsingError.__init__(self, lineno)
        self.cmd = cmd.decode('ascii', 'replace')


class MissingSection(ParsingError):
    """Raised when a section is required in a command but not present."""

    _fmt = (_LOCATION_FMT + "Command %(cmd)s is missing section %(section)s")

    def __init__(self, lineno, cmd, section):
        ParsingError.__init__(self, lineno)
        self.cmd = cmd
        self.section = section


class BadFormat(ParsingError):
    """Raised when a section is formatted incorrectly."""

    _fmt = (_LOCATION_FMT + "Bad format for section %(section)s in "
        "command %(cmd)s: found '%(text)s'")

    def __init__(self, lineno, cmd, section, text):
        ParsingError.__init__(self, lineno)
        self.cmd = cmd
        self.section = section
        self.text = text


class InvalidTimezone(ParsingError):
    """Raised when converting a string timezone to a seconds offset."""

    _fmt = (_LOCATION_FMT +
        "Timezone %(timezone)r could not be converted.%(reason)s")

    def __init__(self, lineno, timezone, reason=None):
        ParsingError.__init__(self, lineno)
        self.timezone = timezone
        if reason:
            self.reason = ' ' + reason
        else:
            self.reason = ''


class UnknownDateFormat(FastImportError):
    """Raised when an unknown date format is given."""

    _fmt = ("Unknown date format '%(format)s'")

    def __init__(self, format):
        FastImportError.__init__(self)
        self.format = format


class MissingHandler(FastImportError):
    """Raised when a processor can't handle a command."""

    _fmt = ("Missing handler for command %(cmd)s")

    def __init__(self, cmd):
        FastImportError.__init__(self)
        self.cmd = cmd


class UnknownParameter(FastImportError):
    """Raised when an unknown parameter is passed to a processor."""

    _fmt = ("Unknown parameter - '%(param)s' not in %(knowns)s")

    def __init__(self, param, knowns):
        FastImportError.__init__(self)
        self.param = param
        self.knowns = knowns


class BadRepositorySize(FastImportError):
    """Raised when the repository has an incorrect number of revisions."""

    _fmt = ("Bad repository size - %(found)d revisions found, "
        "%(expected)d expected")

    def __init__(self, expected, found):
        FastImportError.__init__(self)
        self.expected = expected
        self.found = found


class BadRestart(FastImportError):
    """Raised when the import stream and id-map do not match up."""

    _fmt = ("Bad restart - attempted to skip commit %(commit_id)s "
        "but matching revision-id is unknown")

    def __init__(self, commit_id):
        FastImportError.__init__(self)
        self.commit_id = commit_id


class UnknownFeature(FastImportError):
    """Raised when an unknown feature is given in the input stream."""

    _fmt = ("Unknown feature '%(feature)s' - try a later importer or "
        "an earlier data format")

    def __init__(self, feature):
        FastImportError.__init__(self)
        self.feature = feature
