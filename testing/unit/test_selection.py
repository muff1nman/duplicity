# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
# Copyright 2014 Aaron Whitehouse <aaron@whitehouse.kiwi.nz>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import types
import StringIO
import unittest
import sys

from duplicity.selection import *  # @UnusedWildImport
from duplicity.lazy import *  # @UnusedWildImport
from . import UnitTestCase


class MatchingTest(UnitTestCase):
    """Test matching of file names against various selection functions"""
    def setUp(self):
        super(MatchingTest, self).setUp()
        self.unpack_testfiles()
        self.root = Path("testfiles/select")
        self.Select = Select(self.root)

    def makeext(self, path):
        return self.root.new_index(tuple(path.split("/")))

    def testRegexp(self):
        """Test regular expression selection func"""
        sf1 = self.Select.regexp_get_sf(".*\.py", 1)
        assert sf1(self.makeext("1.py")) == 1
        assert sf1(self.makeext("usr/foo.py")) == 1
        assert sf1(self.root.append("1.doc")) is None

        sf2 = self.Select.regexp_get_sf("hello", 0)
        assert sf2(Path("hello")) == 0
        assert sf2(Path("foohello_there")) == 0
        assert sf2(Path("foo")) is None

    def testTupleInclude(self):
        """Test include selection function made from a regular filename"""
        self.assertRaises(FilePrefixError,
                          self.Select.glob_get_filename_sf, "foo", 1)

        sf2 = self.Select.glob_get_sf("testfiles/select/usr/local/bin/", 1)
        assert sf2(self.makeext("usr")) == 1
        assert sf2(self.makeext("usr/local")) == 1
        assert sf2(self.makeext("usr/local/bin")) == 1
        assert sf2(self.makeext("usr/local/doc")) is None
        assert sf2(self.makeext("usr/local/bin/gzip")) == 1
        assert sf2(self.makeext("usr/local/bingzip")) is None

    def testTupleExclude(self):
        """Test exclude selection function made from a regular filename"""
        self.assertRaises(FilePrefixError,
                          self.Select.glob_get_filename_sf, "foo", 0)

        sf2 = self.Select.glob_get_sf("testfiles/select/usr/local/bin/", 0)
        assert sf2(self.makeext("usr")) is None
        assert sf2(self.makeext("usr/local")) is None
        assert sf2(self.makeext("usr/local/bin")) == 0
        assert sf2(self.makeext("usr/local/doc")) is None
        assert sf2(self.makeext("usr/local/bin/gzip")) == 0
        assert sf2(self.makeext("usr/local/bingzip")) is None

    def testGlobStarInclude(self):
        """Test a few globbing patterns, including **"""
        sf1 = self.Select.glob_get_sf("**", 1)
        assert sf1(self.makeext("foo")) == 1
        assert sf1(self.makeext("")) == 1

        sf2 = self.Select.glob_get_sf("**.py", 1)
        assert sf2(self.makeext("foo")) == 2
        assert sf2(self.makeext("usr/local/bin")) == 2
        assert sf2(self.makeext("what/ever.py")) == 1
        assert sf2(self.makeext("what/ever.py/foo")) == 1

    def testGlobStarExclude(self):
        """Test a few glob excludes, including **"""
        sf1 = self.Select.glob_get_sf("**", 0)
        assert sf1(self.makeext("/usr/local/bin")) == 0

        sf2 = self.Select.glob_get_sf("**.py", 0)
        assert sf2(self.makeext("foo")) is None, sf2(self.makeext("foo"))
        assert sf2(self.makeext("usr/local/bin")) is None
        assert sf2(self.makeext("what/ever.py")) == 0
        assert sf2(self.makeext("what/ever.py/foo")) == 0

    def testGlobRE(self):
        """testGlobRE - test translation of shell pattern to regular exp"""
        assert self.Select.glob_to_re("hello") == "hello"
        assert self.Select.glob_to_re(".e?ll**o") == "\\.e[^/]ll.*o"
        r = self.Select.glob_to_re("[abc]el[^de][!fg]h")
        assert r == "[abc]el[^de][^fg]h", r
        r = self.Select.glob_to_re("/usr/*/bin/")
        assert r == "\\/usr\\/[^/]*\\/bin\\/", r
        assert self.Select.glob_to_re("[a.b/c]") == "[a.b/c]"
        r = self.Select.glob_to_re("[a*b-c]e[!]]")
        assert r == "[a*b-c]e[^]]", r

    def testGlobSFException(self):
        """testGlobSFException - see if globbing errors returned"""
        self.assertRaises(GlobbingError, self.Select.glob_get_normal_sf,
                          "testfiles/select/hello//there", 1)
        self.assertRaises(FilePrefixError,
                          self.Select.glob_get_sf, "testfiles/whatever", 1)
        self.assertRaises(FilePrefixError,
                          self.Select.glob_get_sf, "testfiles/?hello", 0)
        assert self.Select.glob_get_normal_sf("**", 1)

    def testIgnoreCase(self):
        """testIgnoreCase - try a few expressions with ignorecase:"""
        sf = self.Select.glob_get_sf("ignorecase:testfiles/SeLect/foo/bar", 1)
        assert sf(self.makeext("FOO/BAR")) == 1
        assert sf(self.makeext("foo/bar")) == 1
        assert sf(self.makeext("fOo/BaR")) == 1
        self.assertRaises(FilePrefixError, self.Select.glob_get_sf,
                          "ignorecase:tesfiles/sect/foo/bar", 1)

    def testRoot(self):
        """testRoot - / may be a counterexample to several of these.."""
        root = Path("/")
        select = Select(root)

        assert select.glob_get_sf("/", 1)(root) == 1
        assert select.glob_get_sf("/foo", 1)(root) == 1
        assert select.glob_get_sf("/foo/bar", 1)(root) == 1
        assert select.glob_get_sf("/", 0)(root) == 0
        assert select.glob_get_sf("/foo", 0)(root) is None

        assert select.glob_get_sf("**.py", 1)(root) == 2
        assert select.glob_get_sf("**", 1)(root) == 1
        assert select.glob_get_sf("ignorecase:/", 1)(root) == 1
        assert select.glob_get_sf("**.py", 0)(root) is None
        assert select.glob_get_sf("**", 0)(root) == 0
        assert select.glob_get_sf("/foo/*", 0)(root) is None

    def testOtherFilesystems(self):
        """Test to see if --exclude-other-filesystems works correctly"""
        root = Path("/")
        select = Select(root)
        sf = select.other_filesystems_get_sf(0)
        assert sf(root) is None
        if os.path.ismount("/usr/bin"):
            sfval = 0
        else:
            sfval = None
        assert sf(Path("/usr/bin")) == sfval, \
            "Assumption: /usr/bin is on the same filesystem as /"
        if os.path.ismount("/dev"):
            sfval = 0
        else:
            sfval = None
        assert sf(Path("/dev")) == sfval, \
            "Assumption: /dev is on a different filesystem"
        if os.path.ismount("/proc"):
            sfval = 0
        else:
            sfval = None
        assert sf(Path("/proc")) == sfval, \
            "Assumption: /proc is on a different filesystem"


class ParseArgsTest(UnitTestCase):
    """Test argument parsing"""
    def setUp(self):
        super(ParseArgsTest, self).setUp()
        self.unpack_testfiles()
        self.root = None

    def ParseTest(self, tuplelist, indicies, filelists=[]):
        """No error if running select on tuple goes over indicies"""
        if not self.root:
            self.root = Path("testfiles/select")
        self.Select = Select(self.root)
        self.Select.ParseArgs(tuplelist, self.remake_filelists(filelists))
        self.Select.set_iter()
        assert Iter.equal(Iter.map(lambda path: path.index, self.Select),
                          iter(indicies), verbose=1)

    def remake_filelists(self, filelist):
        """Turn strings in filelist into fileobjs"""
        new_filelists = []
        for f in filelist:
            if isinstance(f, types.StringType):
                new_filelists.append(StringIO.StringIO(f))
            else:
                new_filelists.append(f)
        return new_filelists

    def testParse(self):
        """Test just one include, all exclude"""
        self.ParseTest([("--include", "testfiles/select/1/1"),
                        ("--exclude", "**")],
                       [(), ('1',), ("1", "1"), ("1", '1', '1'),
                        ('1', '1', '2'), ('1', '1', '3')])

    def testParse2(self):
        """Test three level include/exclude"""
        self.ParseTest([("--exclude", "testfiles/select/1/1/1"),
                        ("--include", "testfiles/select/1/1"),
                        ("--exclude", "testfiles/select/1"),
                        ("--exclude", "**")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')])

    def test_filelist(self):
        """Filelist glob test similar to above testParse2"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_1_trailing_whitespace(self):
        """Filelist glob test similar to globbing filelist, but with 1 trailing whitespace on include"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "testfiles/select/1/1 \n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_2_trailing_whitespaces(self):
        """Filelist glob test similar to globbing filelist, but with 2 trailing whitespaces on include"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "testfiles/select/1/1  \n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_1_leading_whitespace(self):
        """Filelist glob test similar to globbing filelist, but with 1 leading whitespace on include"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        " testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_2_leading_whitespaces(self):
        """Filelist glob test similar to globbing filelist, but with 2 leading whitespaces on include"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "  testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_1_trailing_whitespace_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 1 trailing whitespace on exclude"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1 \n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_2_trailing_whitespace_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 2 trailing whitespaces on exclude"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1  \n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_1_leading_whitespace_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 1 leading whitespace on exclude"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       [" - testfiles/select/1/1/1\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_2_leading_whitespaces_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 2 leading whitespaces on exclude"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["  - testfiles/select/1/1/1\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_check_excluded_folder_included_for_contents(self):
        """Filelist glob test to check excluded folder is included if contents are"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '1'), ('1', '1', '2'),
                        ('1', '1', '3'), ('1', '2'), ('1', '2', '1'), ('1', '3'), ('1', '3', '1'), ('1', '3', '2'),
                        ('1', '3', '3')],
                       ["+ testfiles/select/1/2/1\n"
                        "- testfiles/select/1/2\n"
                        "testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_with_unnecessary_quotes(self):
        """Filelist glob test similar to globbing filelist, but with quotes around one of the paths."""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- 'testfiles/select/1/1/1'\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_with_unnecessary_double_quotes(self):
        """Filelist glob test similar to globbing filelist, but with double quotes around one of the paths."""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ['- "testfiles/select/1/1/1"\n'
                        'testfiles/select/1/1\n'
                        '- testfiles/select/1\n'
                        '- **'])

    def test_include_filelist_with_full_line_comment(self):
        """Filelist glob test similar to globbing filelist, but with a full-line comment."""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ['- testfiles/select/1/1/1\n'
                        '# This is a test\n'
                        'testfiles/select/1/1\n'
                        '- testfiles/select/1\n'
                        '- **'])

    def test_include_filelist_with_blank_line(self):
        """Filelist glob test similar to globbing filelist, but with a blank line."""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ['- testfiles/select/1/1/1\n'
                        '\n'
                        'testfiles/select/1/1\n'
                        '- testfiles/select/1\n'
                        '- **'])

    def test_include_filelist_with_blank_line_and_whitespace(self):
        """Filelist glob test similar to globbing filelist, but with a blank line and whitespace."""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ['- testfiles/select/1/1/1\n'
                        '  \n'
                        'testfiles/select/1/1\n'
                        '- testfiles/select/1\n'
                        '- **'])

    def test_include_filelist_asterisk(self):
        """Filelist glob test with * instead of 'testfiles'"""
        # Thank you to Elifarley Cruz for this test case
        # (https://bugs.launchpad.net/duplicity/+bug/884371).
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '1'),
                        ('1', '1', '2'), ('1', '1', '3')],
                       ["*/select/1/1\n"
                        "- **"])

    def test_include_filelist_asterisk_2(self):
        """Identical to test_filelist, but with the exclude 'select' replaced with '*'"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/*/1/1/1\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_asterisk_3(self):
        """Identical to test_filelist, but with the auto-include 'select' replaced with '*'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "testfiles/*/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_asterisk_4(self):
        """Identical to test_filelist, but with a specific include 'select' replaced with '*'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "+ testfiles/*/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_asterisk_5(self):
        """Identical to test_filelist, but with all 'select's replaced with '*'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/*/1/1/1\n"
                        "+ testfiles/*/1/1\n"
                        "- testfiles/*/1\n"
                        "- **"])

    def test_include_filelist_asterisk_6(self):
        """Identical to test_filelist, but with numerous excluded folders replaced with '*'"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- */*/1/1/1\n"
                        "+ testfiles/select/1/1\n"
                        "- */*/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_asterisk_7(self):
        """Identical to test_filelist, but with numerous included/excluded folders replaced with '*'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- */*/1/1/1\n"
                        "+ */*/1/1\n"
                        "- */*/1\n"
                        "- **"])

    def test_include_filelist_double_asterisk_1(self):
        """Identical to test_filelist, but with the exclude 'select' replaced with '**'"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/**/1/1/1\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_double_asterisk_2(self):
        """Identical to test_filelist, but with the include 'select' replaced with '**'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "testfiles/**/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    def test_include_filelist_double_asterisk_3(self):
        """Identical to test_filelist, but with the exclude 'testfiles/select' replaced with '**'"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- **/1/1/1\n"
                        "testfiles/select/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_double_asterisk_4(self):
        """Identical to test_filelist, but with the include 'testfiles/select' replaced with '**'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1\n"
                        "**/1/1\n"
                        "- testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_double_asterisk_5(self):
        """Identical to test_filelist, but with all 'testfiles/select's replaced with '**'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- **/1/1/1\n"
                        "**/1/1\n"
                        "- **/1\n"
                        "- **"])

    def test_include_filelist_trailing_slashes(self):
        """Filelist glob test similar to globbing filelist, but with trailing slashes"""
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- testfiles/select/1/1/1/\n"
                        "testfiles/select/1/1/\n"
                        "- testfiles/select/1/\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_trailing_slashes_and_single_asterisks(self):
        """Filelist glob test similar to globbing filelist, but with trailing slashes and single asterisks"""
        # Todo: Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- */select/1/1/1/\n"
                        "testfiles/select/1/1/\n"
                        "- testfiles/*/1/\n"
                        "- **"])

    @unittest.expectedFailure
    def test_include_filelist_trailing_slashes_and_double_asterisks(self):
        """Filelist glob test similar to globbing filelist, but with trailing slashes and double asterisks"""
        # Todo: Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["- **/1/1/1/\n"
                        "testfiles/select/1/1/\n"
                        "- **/1/\n"
                        "- **"])


    def test_filelist_null_separator(self):
        """test_filelist, but with null_separator set"""
        self.set_global('null_separator', 1)
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["\0- testfiles/select/1/1/1\0testfiles/select/1/1\0- testfiles/select/1\0- **\0"])

    def test_exclude_filelist(self):
        """Exclude version of test_filelist"""
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["testfiles/select/1/1/1\n"
                        "+ testfiles/select/1/1\n"
                        "testfiles/select/1\n"
                        "- **"])

    def test_exclude_filelist_asterisk_1(self):
        """Exclude version of test_include_filelist_asterisk"""
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '1'),
                        ('1', '1', '2'), ('1', '1', '3')],
                       ["+ */select/1/1\n"
                        "- **"])

    def test_exclude_filelist_asterisk_2(self):
        """Identical to test_exclude_filelist, but with the exclude 'select' replaced with '*'"""
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["testfiles/*/1/1/1\n"
                        "+ testfiles/select/1/1\n"
                        "testfiles/select/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_exclude_filelist_asterisk_3(self):
        """Identical to test_exclude_filelist, but with the include 'select' replaced with '*'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["testfiles/select/1/1/1\n"
                        "+ testfiles/*/1/1\n"
                        "testfiles/select/1\n"
                        "- **"])

    def test_exclude_filelist_asterisk_4(self):
        """Identical to test_exclude_filelist, but with numerous excluded folders replaced with '*'"""
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["*/select/1/1/1\n"
                        "+ testfiles/select/1/1\n"
                        "*/*/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_exclude_filelist_asterisk_5(self):
        """Identical to test_exclude_filelist, but with numerous included/excluded folders replaced with '*'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["*/select/1/1/1\n"
                        "+ */*/1/1\n"
                        "*/*/1\n"
                        "- **"])

    @unittest.expectedFailure
    def test_exclude_filelist_double_asterisk(self):
        """Identical to test_exclude_filelist, but with all included/excluded folders replaced with '**'"""
        # Todo: Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest([("--exclude-filelist", "file")],
                       [(), ('1',), ('1', '1'), ('1', '1', '2'),
                        ('1', '1', '3')],
                       ["**/1/1/1\n"
                        "+ **/1/1\n"
                        "**/1\n"
                        "- **"])

    def testGlob(self):
        """Test globbing expression"""
        self.ParseTest([("--exclude", "**[3-5]"),
                        ("--include", "testfiles/select/1"),
                        ("--exclude", "**")],
                       [(), ('1',), ('1', '1'),
                        ('1', '1', '1'), ('1', '1', '2'),
                        ('1', '2'), ('1', '2', '1'), ('1', '2', '2')])
        self.ParseTest([("--include", "testfiles/select**/2"),
                        ("--exclude", "**")],
                       [(), ('1',), ('1', '1'),
                        ('1', '1', '2'),
                        ('1', '2'),
                        ('1', '2', '1'), ('1', '2', '2'), ('1', '2', '3'),
                        ('1', '3'),
                        ('1', '3', '2'),
                        ('2',), ('2', '1'),
                        ('2', '1', '1'), ('2', '1', '2'), ('2', '1', '3'),
                        ('2', '2'),
                        ('2', '2', '1'), ('2', '2', '2'), ('2', '2', '3'),
                        ('2', '3'),
                        ('2', '3', '1'), ('2', '3', '2'), ('2', '3', '3'),
                        ('3',), ('3', '1'),
                        ('3', '1', '2'),
                        ('3', '2'),
                        ('3', '2', '1'), ('3', '2', '2'), ('3', '2', '3'),
                        ('3', '3'),
                        ('3', '3', '2')])

    def test_filelist2(self):
        """Filelist glob test similar to above testGlob"""
        self.ParseTest([("--exclude-filelist", "asoeuth")],
                       [(), ('1',), ('1', '1'),
                        ('1', '1', '1'), ('1', '1', '2'),
                        ('1', '2'), ('1', '2', '1'), ('1', '2', '2')],
                       ["""
**[3-5]
+ testfiles/select/1
**
"""])
        self.ParseTest([("--include-filelist", "file")],
                       [(), ('1',), ('1', '1'),
                        ('1', '1', '2'),
                        ('1', '2'),
                        ('1', '2', '1'), ('1', '2', '2'), ('1', '2', '3'),
                        ('1', '3'),
                        ('1', '3', '2'),
                        ('2',), ('2', '1'),
                        ('2', '1', '1'), ('2', '1', '2'), ('2', '1', '3'),
                        ('2', '2'),
                        ('2', '2', '1'), ('2', '2', '2'), ('2', '2', '3'),
                        ('2', '3'),
                        ('2', '3', '1'), ('2', '3', '2'), ('2', '3', '3'),
                        ('3',), ('3', '1'),
                        ('3', '1', '2'),
                        ('3', '2'),
                        ('3', '2', '1'), ('3', '2', '2'), ('3', '2', '3'),
                        ('3', '3'),
                        ('3', '3', '2')],
                       ["""
testfiles/select**/2
- **
"""])

    def testGlob2(self):
        """Test more globbing functions"""
        self.ParseTest([("--include", "testfiles/select/*foo*/p*"),
                        ("--exclude", "**")],
                       [(), ('efools',), ('efools', 'ping'),
                        ('foobar',), ('foobar', 'pong')])
        self.ParseTest([("--exclude", "testfiles/select/1/1/*"),
                        ("--exclude", "testfiles/select/1/2/**"),
                        ("--exclude", "testfiles/select/1/3**"),
                        ("--include", "testfiles/select/1"),
                        ("--exclude", "**")],
                       [(), ('1',), ('1', '1'), ('1', '2')])

    def testGlob3(self):
        """ regression test for bug 25230 """
        self.ParseTest([("--include", "testfiles/select/**1"),
                        ("--include", "testfiles/select/**2"),
                        ("--exclude", "**")],
                       [(), ('1',), ('1', '1'),
                        ('1', '1', '1'), ('1', '1', '2'), ('1', '1', '3'),
                        ('1', '2'),
                        ('1', '2', '1'), ('1', '2', '2'), ('1', '2', '3'),
                        ('1', '3'),
                        ('1', '3', '1'), ('1', '3', '2'), ('1', '3', '3'),
                        ('2',), ('2', '1'),
                        ('2', '1', '1'), ('2', '1', '2'), ('2', '1', '3'),
                        ('2', '2'),
                        ('2', '2', '1'), ('2', '2', '2'), ('2', '2', '3'),
                        ('2', '3'),
                        ('2', '3', '1'), ('2', '3', '2'), ('2', '3', '3'),
                        ('3',), ('3', '1'),
                        ('3', '1', '1'), ('3', '1', '2'), ('3', '1', '3'),
                        ('3', '2'),
                        ('3', '2', '1'), ('3', '2', '2'), ('3', '2', '3'),
                        ('3', '3'),
                        ('3', '3', '1'), ('3', '3', '2')])

    def testAlternateRoot(self):
        """Test select with different root"""
        self.root = Path("testfiles/select/1")
        self.ParseTest([("--exclude", "testfiles/select/1/[23]")],
                       [(), ('1',), ('1', '1'), ('1', '2'), ('1', '3')])

        self.root = Path("/")
        self.ParseTest([("--exclude", "/home/*"),
                        ("--include", "/home"),
                        ("--exclude", "/")],
                       [(), ("home",)])

if __name__ == "__main__":
    unittest.main()
