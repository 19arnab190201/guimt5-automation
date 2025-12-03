import pygetwindow as gw
print([w.title for w in gw.getAllWindows() if w.title])
