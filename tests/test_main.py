from src import main

def test_main():
    ret = main.main()
    assert ret == "Hello World!"