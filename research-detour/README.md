# Detour Notes

The purpose of this experiment is to determine if python3 can ptrace another program running on the arm system without pip or dependencies. Although this test was performed on 86/64 arch, the results show 
that ctypes was successful at deducing the function call and counter integer.

For return to home functionality, the next test should attempt to invoke a function in the program from python.

```bash
$ ./program
pid 468053
heartbeat 0
heartbeat 1
heartbeat 2
heartbeat 3
heartbeat 4
heartbeat 5
heartbeat 6
heartbeat 7
heartbeat 8
```

```bash
$ python3 tracer.py 468053
[*] hooking printf at 0x7ff8402f3900
[*] attached
[*] breakpoint installed
[+] printf hit: counter=5
[+] printf hit: counter=6
^C[*] detaching
```
