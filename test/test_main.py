"""
Testing main.py
"""

from src.nml import main


def test_main():
    """Test to see return valid"""
    ret = main.main()
    assert ret == "Hello World!"
