from unittest import TestCase

from rpnpy.io import splitInput, findModifiers
from rpnpy.modifiers import Modifiers, strToModifiers, MODIFIERS


class TestSplitInput(TestCase):
    """Test the splitInput function."""

    def testEmpty(self):
        """Test an empty string."""
        self.assertEqual(((None, None, None),),
                         tuple(splitInput('')))

    def testComment(self):
        """Test a comment."""
        self.assertEqual(((None, None, None),),
                         tuple(splitInput('# comment')))

    def testCommentPrecededByWhitespace(self):
        """Test a comment preceeded by whitespace."""
        self.assertEqual(((None, None, None),),
                         tuple(splitInput('  # comment')))

    def testCommandWithNoModifiers(self):
        """Test a command with no modifiers"""
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(splitInput('hey')))

    def testTwoCommands(self):
        """Test two commands on one line"""
        self.assertEqual(
            (('hey', Modifiers(), None), ('you', Modifiers(), None)),
            tuple(splitInput('hey you')))

    def testNoSplitAssignment(self):
        """Test an assignment with splitting off"""
        self.assertEqual((('a = 3', strToModifiers('n'), None),),
                         tuple(splitInput('a = 3 :n')))

    def testNoSplitStringWithWhitespace(self):
        """Test a string with whitespace and splitting off"""
        self.assertEqual((('"hey you"', strToModifiers('n'), None),),
                         tuple(splitInput('"hey you" :n')))

    def testTwoCommandsSplitLines(self):
        """Test two words on one line when splitLines is False"""
        self.assertEqual(
            (('hey you', Modifiers(), None),),
            tuple(splitInput('hey you', splitLines=False)))

    def testTwoCommandsSplitLinesOverridden(self):
        """Test two words on one line when splitLines is False but the split
        lines modifier is passed"""
        self.assertEqual(
            (('hey', strToModifiers('s'), None),
             ('you', strToModifiers('s'), None),),
            tuple(splitInput('hey you :s', splitLines=False)))

    def testCommandWithNoModifiersPrecededByWhitespace(self):
        """Test a command with no modifiers preceded by whitespace"""
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(splitInput(' hey')))

    def testCommandWithNoModifiersFollowedByWhitespace(self):
        """Test a command with no modifiers followed by whitespace"""
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(splitInput(' hey')))

    def testCommandWithLeadingSpaceAndNoModifiers(self):
        """Test a command with leading space and no modifiers"""
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(splitInput(' hey')))

    def testCommandWithTrailingSpaceAndNoModifiers(self):
        """Test a command with trailing space and no modifiers"""
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(splitInput('hey ')))

    def testCommandWithSurroundingSpaceAndNoModifiers(self):
        """Test a command with surrounding space and no modifiers"""
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(splitInput(' hey ')))

    def testCommandWithNoModifiersCaseUnchanged(self):
        """Test that command case is unmodified"""
        self.assertEqual((('HeY', Modifiers(), None),),
                         tuple(splitInput('HeY')))

    def testCommandWithModifiers(self):
        """Test a command with modifiers"""
        self.assertEqual((('hey', strToModifiers('=p'), None),),
                         tuple(splitInput('hey :p=')))

    def testCommandWithModifiersNoSpace(self):
        """Test a command with modifiers but no space before the :"""
        self.assertEqual((('hey', strToModifiers('=p'), None),),
                         tuple(splitInput('hey:=p')))

    def testCommandWithCount(self):
        """Test a command with a count"""
        self.assertEqual((('hey', Modifiers(), 101),),
                         tuple(splitInput('hey :101')))

    def testCommandWithCountThenModifiers(self):
        """Test a command with a count then modifiers"""
        self.assertEqual((('hey', strToModifiers('=p'), 101),),
                         tuple(splitInput('hey :101=p')))

    def testCommandWithCountThenSpaceAndModifiers(self):
        """Test a command with a count then a space then modifiers"""
        self.assertEqual((('hey', strToModifiers('=p'), 101),),
                         tuple(splitInput('hey :101 =p')))

    def testCommandWithModifiersThenCount(self):
        """Test a command with modifiers then a count"""
        self.assertEqual((('hey', strToModifiers('=p'), 101),),
                         tuple(splitInput('hey :=p101')))

    def testCommandWithModifiersThenSpaceAndCount(self):
        """Test a command with modifiers, a space, and then a count"""
        self.assertEqual((('hey', strToModifiers('=p'), 101),),
                         tuple(splitInput('hey :=p 101')))

    def testCommandWithModifiersSurroundingCount(self):
        """Test a command with modifiers before and after a count"""
        self.assertEqual((('hey', strToModifiers('=p*'), 16),),
                         tuple(splitInput('hey :=p 16 *')))

    def testDict(self):
        """A dict must not be confused for a string with modifiers."""
        self.assertEqual((("{'a':6,'b':10,'c':15}", Modifiers(), None),),
                         tuple(splitInput("{'a':6,'b':10,'c':15}")))


class TestFindModifiers(TestCase):
    """Test the findModifiers function."""

    def testEmpty(self):
        """Test an empty string."""
        self.assertEqual((-1, Modifiers(), None), findModifiers(''))

    def testSeparatorIsLastLetter(self):
        """Test a string that ends with the separator."""
        self.assertEqual((0, Modifiers(), None), findModifiers(':'))

    def testStringWithNoModifierSeparator(self):
        """Test a string with no modifier separator."""
        self.assertEqual((-1, Modifiers(), None), findModifiers('hello'))

    def testUnknownLetter(self):
        """Test a string with a non-modifier letter."""
        # Before testing, make sure '?' is not actually a valid modifier.
        self.assertFalse('?' in MODIFIERS)
        self.assertEqual((-1, Modifiers(), None), findModifiers('4 :?'))

    def testDict(self):
        """A dict must not be confused for a string with modifiers."""
        self.assertEqual((-1, Modifiers(), None),
                         findModifiers("{'a':6, 'b':10, 'c':15}"))

    def testDictWithModifiers(self):
        """A dict with modifiers must be processed correctly."""
        self.assertEqual((24, strToModifiers('=p'), 17),
                         findModifiers("{'a':6, 'b':10, 'c':15} :=p17"))

    def testDuplicatedLetter(self):
        """A string with a duplicated modifier must be processed correctly."""
        self.assertEqual((4, strToModifiers('=p'), None),
                         findModifiers("abs :=pp"))
