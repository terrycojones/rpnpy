from unittest import TestCase

from rpnpy.io import findCommands, findModifiers
from rpnpy.modifiers import Modifiers, strToModifiers, MODIFIERS


class TestFindModifiers(TestCase):
    "Test the findModifiers function."

    def testEmpty(self):
        "Test an empty string."
        self.assertEqual((-1, Modifiers(), None), findModifiers(''))

    def testSeparatorIsLastLetter(self):
        "Test a string that ends with the separator."
        self.assertEqual((0, Modifiers(), None), findModifiers(':'))

    def testStringWithNoModifierSeparator(self):
        "Test a string with no modifier separator."
        self.assertEqual((-1, Modifiers(), None), findModifiers('hello'))

    def testUnknownLetter(self):
        "Test a string with a non-modifier letter."
        # Before testing, make sure '?' is not actually a valid modifier.
        self.assertFalse('?' in MODIFIERS)
        self.assertEqual((-1, Modifiers(), None), findModifiers('4 :?'))

    def testDict(self):
        "A dict must not be confused for a string with modifiers."
        self.assertEqual((-1, Modifiers(), None),
                         findModifiers("{'a':6, 'b':10, 'c':15}"))

    def testDictWithModifiers(self):
        "A dict with modifiers must be processed correctly."
        self.assertEqual((24, strToModifiers('=p'), 17),
                         findModifiers("{'a':6, 'b':10, 'c':15} :=p17"))

    def testDuplicatedLetter(self):
        "A string with a duplicated modifier must be processed correctly."
        self.assertEqual((4, strToModifiers('=p'), None),
                         findModifiers("abs :=pp"))


class TestFindCommands(TestCase):
    "Test the findCommands function."

    def testEmpty(self):
        "Test an empty string produces no commands at all."
        self.assertEqual(tuple(), tuple(findCommands('')))

    def testComment(self):
        "Test a comment."
        self.assertEqual((('', Modifiers(), None),),
                         tuple(findCommands('# comment')))

    def testCommentPrecededByWhitespace(self):
        "Test a comment preceeded by whitespace."
        self.assertEqual((('', Modifiers(), None),),
                         tuple(findCommands('  # comment')))

    def testCommandWithNoModifiers(self):
        "Test a command with no modifiers"
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(findCommands('hey')))

    def testTwoCommands(self):
        "Test two commands on one line"
        self.assertEqual(
            (('hey', Modifiers(), None), ('you', Modifiers(), None)),
            tuple(findCommands('hey you')))

    def testTwoCommandsFirstWithModifiers(self):
        "Test two commands on one line, the 1st with modifiers (and no space)"
        self.assertEqual(
            (('hey', strToModifiers('='), None), ('you', Modifiers(), None)),
            tuple(findCommands('hey:= you')))

    def testTwoCommandsFirstWithModifiersAfterSpace(self):
        "Test two commands on one line, the 2nd with modifiers after a space"
        self.assertEqual(
            (('hey', strToModifiers('='), None), ('you', Modifiers(), None)),
            tuple(findCommands('hey := you')))

    def testTwoCommandsSecondWithModifiers(self):
        "Test two commands on one line, the 2nd with modifiers (and no space)"
        self.assertEqual(
            (('hey', Modifiers(), None), ('you', strToModifiers('='), None)),
            tuple(findCommands('hey you:=')))

    def testTwoCommandsSecondWithModifiersAfterSpace(self):
        "Test two commands on one line, the 2nd with modifiers after a space"
        self.assertEqual(
            (('hey', Modifiers(), None), ('you', strToModifiers('='), None)),
            tuple(findCommands('hey you :=')))

    def testThreeCommandsSecondWithModifiers(self):
        "Test three commands on one line, the 2nd with modifiers"
        self.assertEqual(
            (('hey', Modifiers(), None), ('you', strToModifiers('='), None),
             ('there', Modifiers(), None)),
            tuple(findCommands('hey you:= there')))

    def testNoSplitAssignment(self):
        "Test an assignment with splitting off"
        self.assertEqual((('a = 3', Modifiers(), None),),
                         tuple(findCommands('a = 3', splitLines=False)))

    def testTwoCommandsSplitLines(self):
        "Test two words on one line when splitLines is False"
        self.assertEqual(
            (('hey you', Modifiers(), None),),
            tuple(findCommands('hey you', splitLines=False)))

    def testCommandWithNoModifiersPrecededByWhitespace(self):
        "Test a command with no modifiers preceded by whitespace"
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(findCommands(' hey')))

    def testCommandWithNoModifiersFollowedByWhitespace(self):
        "Test a command with no modifiers followed by whitespace"
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(findCommands('hey ')))

    def testCommandWithSurroundingSpaceAndNoModifiers(self):
        "Test a command with surrounding space and no modifiers"
        self.assertEqual((('hey', Modifiers(), None),),
                         tuple(findCommands(' hey ')))

    def testCommandWithNoModifiersCaseUnchanged(self):
        "Test that command case is unmodified"
        self.assertEqual((('HeY', Modifiers(), None),),
                         tuple(findCommands('HeY')))

    def testCommandWithCount(self):
        "Test a command with a count"
        self.assertEqual((('hey', Modifiers(), 101),),
                         tuple(findCommands('hey :101')))

    def testCommandWithCountThenModifiers(self):
        "Test a command with a count then modifiers"
        self.assertEqual((('hey', strToModifiers('=p'), 101),),
                         tuple(findCommands('hey :101=p')))

    def testCommandWithModifiersThenCount(self):
        "Test a command with modifiers then a count"
        self.assertEqual((('hey', strToModifiers('=p'), 101),),
                         tuple(findCommands('hey :=p101')))

    def testCommandWithCountThenSpaceAndModifiers(self):
        "Test a command with a count then a space then modifiers with space"
        self.assertEqual(
            (('hey', strToModifiers('=p'), 101),),
            tuple(findCommands('hey :101 =p', splitLines=False)))

    def testCommandWithModifiersSurroundingCount(self):
        "Test a command with modifiers before and after a count"
        self.assertEqual(
            (('hey', strToModifiers('=p*'), 16),),
            tuple(findCommands('hey :=p16*')))

    def testCommandWithModifiersSurroundingCountNoSplit(self):
        "Test a command with modifiers before and after a count"
        self.assertEqual(
            (('hey', strToModifiers('=p*'), 16),),
            tuple(findCommands('hey :=p 16 *', splitLines=False)))

    def testDict(self):
        "A dict must not be confused for a string with modifiers."
        self.assertEqual((("{'a':6,'b':10,'c':15}", Modifiers(), None),),
                         tuple(findCommands("{'a':6,'b':10,'c':15}")))

    def testDictWithModifiers(self):
        "A dict with a count must be processed correctly."
        self.assertEqual((("{'a':6,'b':10,'c':15}", Modifiers(), 7),),
                         tuple(findCommands("{'a':6,'b':10,'c':15}:7")))
