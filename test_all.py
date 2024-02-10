import pytest
import sys
from nedsascript import construct_nedsa


def test_loop():
    assertfile('testloop.nedsa', '+DOESNOTHALT+')
def test_grow():
    assertfile('testgrow.nedsa', '+DOESNOTHALT+')
def test_startendlabel():
    assertfile('teststartendlabel.nedsa', 'SUCCESS')
def test_move():
    assertfile('testmove.nedsa', 'SUCCESS')

def assertfile(filename, result):
    with open('tests/' + filename, 'r') as src:
        assert construct_nedsa(src.read()).decide() == result

def test_runvsdecide():
    with open('tests/teststartendlabel.nedsa', 'r') as src: # using teststartendlabel just as a script that halts
        script = construct_nedsa(src.read())
        assert script.decide() == script.run()
