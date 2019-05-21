from unittest import TestCase

from rpnpy.errors import UnknownModifiersError, IncompatibleModifiersError
from rpnpy.modifiers import Modifiers, strToModifiers, MODIFIERS


class TestModifiers(TestCase):
    "Test the Modifiers namedtuple and functions."

    def testUnknownModifiers(self):
        "Unknown modifiers must be detected."
        error = r"^\('x', 'y', 'z'\)$"
        self.assertRaisesRegex(
            UnknownModifiersError, error, strToModifiers, 'yxz')

    def testIncompatibleModifiersPushAndPreserve(self):
        "Incompatible modifiers must be detected."
        error = r'= \(preserve stack\) makes no sense with ! \(push\)'
        self.assertRaisesRegex(
            IncompatibleModifiersError, error, strToModifiers, '!=')

    def testIncompatibleModifiersSplitNoSplit(self):
        "Incompatible modifiers split and noSplit must be detected."
        error = r'\(split lines\) makes no sense with n \(do not split lines\)'

        self.assertRaisesRegex(
            IncompatibleModifiersError, error, strToModifiers, 'ns')

    def testKnownModifiers(self):
        "Make sure only known modifiers are present."
        self.assertEqual(sorted('*=!cDinps'), sorted(MODIFIERS))

    def testNamesDiffer(self):
        "Make sure all known modifiers have different names."
        self.assertEqual(len(MODIFIERS), len(set(MODIFIERS.values())))

    def testDefaultsFalse(self):
        "Test all attributes default to False."
        modifiers = Modifiers()
        for name in MODIFIERS.values():
            self.assertEqual(False, getattr(modifiers, name))

    def testAll(self):
        "Test the strToModifiers function sets all."
        modifiers = strToModifiers('*')
        self.assertTrue(modifiers.all)

    def testDebug(self):
        "Test the strToModifiers function sets debug."
        modifiers = strToModifiers('D')
        self.assertTrue(modifiers.debug)

    def testForceCommand(self):
        "Test the strToModifiers function sets forceCommand."
        modifiers = strToModifiers('c')
        self.assertTrue(modifiers.forceCommand)

    def testIterate(self):
        "Test the strToModifiers function sets iterate."
        modifiers = strToModifiers('i')
        self.assertTrue(modifiers.iterate)

    def testPresevereStack(self):
        "Test the strToModifiers function sets preserveStack."
        modifiers = strToModifiers('=')
        self.assertTrue(modifiers.preserveStack)

    def testNoSplit(self):
        "Test the strToModifiers function sets noSplit."
        modifiers = strToModifiers('n')
        self.assertTrue(modifiers.noSplit)

    def testPrint(self):
        "Test the strToModifiers function sets print."
        modifiers = strToModifiers('p')
        self.assertTrue(modifiers.print)

    def testPush(self):
        "Test the strToModifiers function sets push."
        modifiers = strToModifiers('!')
        self.assertTrue(modifiers.push)

    def testSplit(self):
        "Test the strToModifiers function sets split."
        modifiers = strToModifiers('s')
        self.assertTrue(modifiers.split)
