from unittest import TestCase

from rpnpy.io import splitInput


class TestInput(TestCase):
    """Test the splitInput function."""

    def testEmpty(self):
        """Test an empty string."""
        self.assertEqual(('', set(), None), splitInput(''))

    def testComment(self):
        """Test a comment."""
        self.assertEqual(('', set(), None), splitInput('# comment'))

    def testCommentPrecededByWhitespace(self):
        """Test a comment preceeded by whitespace."""
        self.assertEqual(('', set(), None), splitInput('  # comment'))

    def testLoneSlash(self):
        """Test a slash by itself."""
        self.assertEqual(('/', set(), None), splitInput('/'))

    def testLoneSlashPrecededByWhitespace(self):
        """Test a slash by itself with some leading whitespace."""
        self.assertEqual(('/', set(), None), splitInput(' /'))

    def testLoneSlashFollowedByWhitespace(self):
        """Test a slash by itself with some trailing whitespace."""
        self.assertEqual(('/', set(), None), splitInput('/ '))

    def testLoneSlashSurroundedByWhitespace(self):
        """Test a slash by itself with surrounding whitespace."""
        self.assertEqual(('/', set(), None), splitInput(' / '))

    def testCommandWithNoModifiers(self):
        """Test a command with no modifiers"""
        self.assertEqual(('hey', set(), None), splitInput('hey'))

    def testCommandWithNoModifiersPrecededByWhitespace(self):
        """Test a command with no modifiers preceded by whitespace"""
        self.assertEqual(('hey', set(), None), splitInput(' hey'))

    def testCommandWithNoModifiersFollowedByWhitespace(self):
        """Test a command with no modifiers followed by whitespace"""
        self.assertEqual(('hey', set(), None), splitInput(' hey'))

    def testCommandWithLeadingSpaceAndNoModifiers(self):
        """Test a command with leading space and no modifiers"""
        self.assertEqual(('hey', set(), None), splitInput(' hey'))

    def testCommandWithTrailingSpaceAndNoModifiers(self):
        """Test a command with trailing space and no modifiers"""
        self.assertEqual(('hey', set(), None), splitInput('hey '))

    def testCommandWithSurroundingSpaceAndNoModifiers(self):
        """Test a command with surrounding space and no modifiers"""
        self.assertEqual(('hey', set(), None), splitInput(' hey '))

    def testCommandWithNoModifiersCaseUnchanged(self):
        """Test that command case is unmodified"""
        self.assertEqual(('HeY', set(), None), splitInput('HeY'))

    def testCommandWithModifiers(self):
        """Test a command with modifiers"""
        self.assertEqual(('hey', set('abc'), None), splitInput('hey /abc'))

    def testCommandWithMixedCaseModifiers(self):
        """Test a command with mixed case modifiers"""
        self.assertEqual(('hey', set('abc'), None), splitInput('hey /AbC'))

    def testCommandWithModifiersNoSpace(self):
        """Test a command with modifiers but no space before the /"""
        self.assertEqual(('hey', set('abc'), None), splitInput('hey/abc'))

    def testCommandWithCount(self):
        """Test a command with a count"""
        self.assertEqual(('hey', set(), 101), splitInput('hey /101'))

    def testCommandWithCountThenModifiers(self):
        """Test a command with a count then modifiers"""
        self.assertEqual(('hey', set('abc'), 101), splitInput('hey /101abc'))

    def testCommandWithCountThenSpaceAndModifiers(self):
        """Test a command with a count then a space then modifiers"""
        self.assertEqual(('hey', set('abc'), 101), splitInput('hey /101 abc'))

    def testCommandWithModifiersThenCount(self):
        """Test a command with modifiers then a count"""
        self.assertEqual(('hey', set('abc'), 101), splitInput('hey /abc101'))

    def testCommandWithModifiersThenSpaceAndCount(self):
        """Test a command with modifiers, a space, and then a count"""
        self.assertEqual(('hey', set('abc'), 101), splitInput('hey /abc 101'))

    def testCommandWithModifiersSurroundingCount(self):
        """Test a command with modifiers before and after a count"""
        self.assertEqual(('hey', set('abcd'), 16), splitInput('hey /ab 16 cd'))
