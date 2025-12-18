#!/bin/env python3

# struct test: b'\x124Vx'
# ctypes strlen: 12
# sqlite rows: [(1, 'foo')]

import ctypes, sqlite3, struct

print("struct test:", struct.pack("!I", 0x12345678))

libc = ctypes.CDLL(None)
strlen = libc.strlen
strlen.argtypes = [ctypes.c_char_p]
strlen.restype = ctypes.c_size_t
s = b"hello ctypes"
print("ctypes strlen:", strlen(s))

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
cur.execute("INSERT INTO t (name) VALUES (?)", ("foo",))
cur.execute("SELECT id, name FROM t")
print("sqlite rows:", cur.fetchall())
conn.close()
