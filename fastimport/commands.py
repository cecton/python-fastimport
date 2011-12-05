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

"""Import command classes."""

import stat
import collections

# There is a bug in git 1.5.4.3 and older by which unquoting a string consumes
# one extra character. Set this variable to True to work-around it. It only
# happens when renaming a file whose name contains spaces and/or quotes, and
# the symptom is:
#   % git-fast-import
#   fatal: Missing space after source: R "file 1.txt" file 2.txt
# http://git.kernel.org/?p=git/git.git;a=commit;h=c8744d6a8b27115503565041566d97c21e722584
GIT_FAST_IMPORT_NEEDS_EXTRA_SPACE_AFTER_QUOTE = False


# Lists of command names
COMMAND_NAMES = ['blob', 'checkpoint', 'commit', 'feature', 'progress',
    'reset', 'tag']
FILE_COMMAND_NAMES = ['filemodify', 'filedelete', 'filecopy', 'filerename',
    'filedeleteall']

# Feature names
MULTIPLE_AUTHORS_FEATURE = "multiple-authors"
COMMIT_PROPERTIES_FEATURE = "commit-properties"
EMPTY_DIRS_FEATURE = "empty-directories"
FEATURE_NAMES = [
    MULTIPLE_AUTHORS_FEATURE,
    COMMIT_PROPERTIES_FEATURE,
    EMPTY_DIRS_FEATURE,
    ]


class ImportCommand(object):
    """Base class for import commands."""

    def __init__(self, name):
        self.name = name
        # List of field names not to display
        self._binary = []

    def __str__(self):
        return repr(self)

    def dump_str(self, names=None, child_lists=None, verbose=False):
        """Dump fields as a string.

        :param names: the list of fields to include or
            None for all public fields
        :param child_lists: dictionary of child command names to
            fields for that child command to include
        :param verbose: if True, prefix each line with the command class and
            display fields as a dictionary; if False, dump just the field
            values with tabs between them
        """
        interesting = {}
        if names is None:
            fields = [k for k in list(self.__dict__.keys()) if not k.startswith('_')]
        else:
            fields = names
        for field in fields:
            value = self.__dict__.get(field)
            if field in self._binary and value is not None:
                value = '(...)'
            interesting[field] = value
        if verbose:
            return "%s: %s" % (self.__class__.__name__, interesting)
        else:
            return "\t".join([repr(interesting[k]) for k in fields])


class BlobCommand(ImportCommand):

    def __init__(self, mark, data, lineno=0):
        ImportCommand.__init__(self, 'blob')
        self.mark = mark
        self.data = data
        self.lineno = lineno
        # Provide a unique id in case the mark is missing
        if mark is None:
            self.id = ('@%d' % lineno).encode('ascii')
        else:
            self.id = b':' + mark
        self._binary = ['data']

    def __bytes__(self):
        if self.mark is None:
            mark_line = b""
        else:
            mark_line = b"mark :" + self.mark + b"\n"
        return (b"blob\n" +
                mark_line +
                ("data %d\n" % len(self.data)).encode('ascii') +
                self.data)


class CheckpointCommand(ImportCommand):

    def __init__(self):
        ImportCommand.__init__(self, 'checkpoint')

    def __bytes__(self):
        return b"checkpoint"


class CommitCommand(ImportCommand):

    def __init__(self, ref, mark, author, committer, message, from_,
        merges, file_iter, lineno=0, more_authors=None, properties=None):
        ImportCommand.__init__(self, 'commit')
        self.ref = ref
        self.mark = mark
        self.author = author
        self.committer = committer
        self.message = message
        self.from_ = from_
        self.merges = merges
        self.file_iter = file_iter
        self.more_authors = more_authors
        self.properties = properties
        self.lineno = lineno
        self._binary = ['file_iter']
        # Provide a unique id in case the mark is missing
        if mark is None:
            self.id = '@%d' % lineno
        else:
            self.id = ':%s' % mark

    def __repr__(self):
        return self.to_bytes(include_file_contents=str).decode('utf-8', 'replace')

    def __bytes__(self):
        return self.to_bytes(include_file_contents=True)

    def to_bytes(self, use_features=True, include_file_contents=False):
        if self.mark is None:
            mark_line = b""
        else:
            mark_line = b"mark :" + self.mark + b"\n"
        if self.author is None:
            author_section = ""
        else:
            author_section = b"author " + format_who_when(self.author) + b"\n"
            if use_features and self.more_authors:
                for author in self.more_authors:
                    author_section += b"author " + format_who_when(author) + b"\n"
        committer = b"committer " + format_who_when(self.committer) + b"\n"
        if self.message is None:
            msg_section = b""
        else:
            msg = self.message
            msg_section = ("data %d\n" % len(msg)).encode('ascii') + msg + b"\n"
        if self.from_ is None:
            from_line = b""
        else:
            from_line = b"from " + self.from_ + b"\n"
        if self.merges is None:
            merge_lines = b""
        else:
            merge_lines = b"".join([(b"merge " + m + b"\n") for m in self.merges])
        if use_features and self.properties:
            property_lines = []
            for name in sorted(self.properties):
                value = self.properties[name]
                property_lines.append(format_property(name, value) + b"\n")
            properties_section = b"".join(property_lines)
        else:
            properties_section = b""
        if self.file_iter is None:
            filecommands = b""
        else:
            if include_file_contents:
                format_str = bytes
            else:
                format_str = str
            filecommands = "".join([format_str(c) for c in self.iter_files()])
        return "".join([b"commit " + self.ref,
            mark_line,
            committer, msg_section, from_line, merge_lines, properties_section, filecommands])

    def dump_str(self, names=None, child_lists=None, verbose=False):
        result = [ImportCommand.dump_str(self, names, verbose=verbose)]
        for f in self.iter_files():
            if child_lists is None:
                continue
            try:
                child_names = child_lists[f.name]
            except KeyError:
                continue
            result.append("\t%s" % f.dump_str(child_names, verbose=verbose))
        return '\n'.join(result)

    def iter_files(self):
        """Iterate over files."""
        # file_iter may be a callable or an iterator
        if isinstance(self.file_iter, collections.Callable):
            return self.file_iter()
        return iter(self.file_iter)


class FeatureCommand(ImportCommand):

    def __init__(self, feature_name, value=None, lineno=0):
        ImportCommand.__init__(self, 'feature')
        self.feature_name = feature_name
        self.value = value
        self.lineno = lineno

    def __bytes__(self):
        if self.value is None:
            value_text = b""
        else:
            value_text = b"=" + self.value.encode('utf-8')
        return b"feature " + self.feature_name.encode('utf-8') + value_text


class ProgressCommand(ImportCommand):

    def __init__(self, message):
        ImportCommand.__init__(self, 'progress')
        self.message = message

    def __bytes__(self):
        return b"progress " + self.message


class ResetCommand(ImportCommand):

    def __init__(self, ref, from_):
        ImportCommand.__init__(self, 'reset')
        self.ref = ref
        self.from_ = from_

    def __bytes__(self):
        if self.from_ is None:
            from_line = b""
        else:
            # According to git-fast-import(1), the extra LF is optional here;
            # however, versions of git up to 1.5.4.3 had a bug by which the LF
            # was needed. Always emit it, since it doesn't hurt and maintains
            # compatibility with older versions.
            # http://git.kernel.org/?p=git/git.git;a=commit;h=655e8515f279c01f525745d443f509f97cd805ab
            from_line = "\nfrom " + self.from_ + b"\n"
        return b"reset " + self.ref + from_line


class TagCommand(ImportCommand):

    def __init__(self, id, from_, tagger, message):
        ImportCommand.__init__(self, 'tag')
        self.id = id
        self.from_ = from_
        self.tagger = tagger
        self.message = message

    def __bytes__(self):
        if self.from_ is None:
            from_line = b""
        else:
            from_line = b"\nfrom " + self.from_
        if self.tagger is None:
            tagger_line = b""
        else:
            tagger_line = b"\ntagger " + format_who_when(self.tagger)
        if self.message is None:
            msg_section = b""
        else:
            msg = self.message
            msg_section = ("\ndata %d\n" % len(msg)).encode('ascii') + msg
        return b"tag " + "".join([self.id, from_line, tagger_line, msg_section])


class FileCommand(ImportCommand):
    """Base class for file commands."""
    pass


class FileModifyCommand(FileCommand):

    def __init__(self, path, mode, dataref, data):
        # Either dataref or data should be null
        FileCommand.__init__(self, 'filemodify')
        self.path = check_path(path)
        self.mode = mode
        self.dataref = dataref
        self.data = data
        self._binary = ['data']

    def __bytes__(self):
        return self.to_string(include_file_contents=True)

    def __str__(self):
        return self.to_string(include_file_contents=False)

    def _format_mode(self, mode):
        if mode in (0o755, 0o100755):
            return b"755"
        elif mode in (0o644, 0o100644):
            return b"644"
        elif mode == 0o40000:
            return b"040000"
        elif mode == 0o120000:
            return b"120000"
        elif mode == 0o160000:
            return b"160000"
        else:
            raise AssertionError("Unknown mode %o" % mode)

    def to_string(self, include_file_contents=False):
        datastr = b""
        if stat.S_ISDIR(self.mode):
            dataref = b'-'
        elif self.dataref is None:
            dataref = b"inline"
            if include_file_contents:
                datastr = "\ndata %d\n%s" % (len(self.data), self.data)
        else:
            dataref = "%s" % (self.dataref,)
        path = format_path(self.path)
        return "M %s %s %s%s" % (self._format_mode(self.mode), dataref, path, datastr)


class FileDeleteCommand(FileCommand):

    def __init__(self, path):
        FileCommand.__init__(self, 'filedelete')
        self.path = check_path(path)

    def __bytes__(self):
        return b"D " + format_path(self.path)


class FileCopyCommand(FileCommand):

    def __init__(self, src_path, dest_path):
        FileCommand.__init__(self, 'filecopy')
        self.src_path = check_path(src_path)
        self.dest_path = check_path(dest_path)

    def __bytes__(self):
        return (b"C " +
            format_path(self.src_path, quote_spaces=True) + b" " +
            format_path(self.dest_path))


class FileRenameCommand(FileCommand):

    def __init__(self, old_path, new_path):
        FileCommand.__init__(self, 'filerename')
        self.old_path = check_path(old_path)
        self.new_path = check_path(new_path)

    def __bytes__(self):
        return (b"R " + 
            format_path(self.old_path, quote_spaces=True) + b" " +
            format_path(self.new_path))


class FileDeleteAllCommand(FileCommand):

    def __init__(self):
        FileCommand.__init__(self, 'filedeleteall')

    def __bytes__(self):
        return b"deleteall"


def check_path(path):
    """Check that a path is legal.

    :return: the path if all is OK
    :raise ValueError: if the path is illegal
    """
    if path is None or path == b'' or path[0] == b"/":
        raise ValueError("illegal path '%s'" % path)
    if type(path) != bytes:
        raise TypeError("illegale type for path '%r'" % path)
    return path


def format_path(p, quote_spaces=False):
    """Format a path in utf8, quoting it if necessary."""
    if b'\n' in p:
        import re
        p = re.sub(b'\n', b'\\n', p)
        quote = True
    else:
        quote = p.startswith(b'"') or (quote_spaces and b' ' in p)
    if quote:
        extra = GIT_FAST_IMPORT_NEEDS_EXTRA_SPACE_AFTER_QUOTE and b' ' or b''
        p = b'"' + p + b'"' + extra
    return p


def format_who_when(fields):
    """Format a tuple of name,email,secs-since-epoch,utc-offset-secs as a string."""
    offset = fields[3]
    if offset < 0:
        offset_sign = '-'
        offset = abs(offset)
    else:
        offset_sign = '+'
    offset_hours = offset / 3600
    offset_minutes = offset / 60 - offset_hours * 60
    offset_str = "%s%02d%02d" % (offset_sign, offset_hours, offset_minutes)
    name = fields[0]
    if name == b'':
        sep = b''
    else:
        sep = b' '
    email = fields[1]
    return (name + sep + b"<" + email + b">" +
            (" %d " % fields[2]).encode('ascii') + offset_str.encode('ascii'))


def format_property(name, value):
    """Format the name and value (both unicode) of a property as a string."""
    utf8_name = name.encode('utf8')
    if value is not None:
        utf8_value = value.encode('utf8')
        result = b"property " + utf8_name + (" %d " % len(utf8_value)).encode('ascii') + utf8_value
    else:
        result = b"property " + utf8_name
    return result
