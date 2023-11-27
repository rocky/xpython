"""This program is self-checking!"""

x = 2023
def f():
    assert 2023 == globals()["x"]    
    assert "y" not in locals()
    y = 2024
    assert 2024 == locals()["y"]
    assert locals() != globals()

f()

