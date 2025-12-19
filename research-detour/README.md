# Detour Notes

# Rev 3

TODO:

- improving function resume (flaky)
- call move-home function
- expose mcp server

# Rev 2

Since python3 was successfully built with ptrace and ctypes, hooking functions and memory is now working. These were tested on chitu v1.5.5;

```
427.063076 using pid 715 for target /customer/resources/chitu
427.066940 loaded 18 entries, using 3 breakpoints, 23 watches, 3 watch_blocks
427.067287 watch axis_target_position_in_step base=0x2fa124 index=0 offset=0x50 kind=s32 size=4
427.067407 watch axis_target_position_in_step base=0x2fa124 index=1 offset=0x50 kind=s32 size=4
..
427.068486 watch printing_level_mode base=0x2fda90 index=0 offset=0x30 kind=u8 size=1
427.068608 watch printing_sync_mode base=0x2fda90 index=0 offset=0x31 kind=u8 size=1
..
427.081910 INSTALL arm addr=0xb60f4 ok=True
427.082082 armed ota_time_check@0xb60f4 mode=arm
..
```

Axis movements (memory):

```
1006.637834 AXIS Z cur=321254 target=1056000 delta=7600 home=160 max=368000 pct=87
1006.638531 AXIS X cur=2411 target=39822 delta=5120 home=0 max=19911 pct=12
1006.873758 AXIS Z cur=322753 target=1056000 delta=11700 home=160 max=368000 pct=87
1006.874504 AXIS X cur=3541 target=39822 delta=5120 home=0 max=19911 pct=17
1007.095056 AXIS Z cur=324512 target=1056000 delta=13300 home=160 max=368000 pct=88
1007.095735 AXIS X cur=4609 target=39822 delta=5120 home=0 max=19911 pct=23
1007.316898 AXIS Z cur=326273 target=1056000 delta=13300 home=160 max=368000 pct=88
1007.317699 AXIS X cur=5677 target=39822 delta=5120 home=0 max=19911 pct=28
1007.550669 AXIS Z cur=328125 target=1056000 delta=13300 home=160 max=368000 pct=89
1007.551408 AXIS X cur=6800 target=39822 delta=5120 home=0 max=19911 pct=34
1007.783264 AXIS Z cur=329975 target=1056000 delta=13300 home=160 max=368000 pct=89
1007.783926 AXIS X cur=7922 target=39822 delta=5120 home=0 max=19911 pct=39
1008.015703 AXIS Z cur=331825 target=1056000 delta=13300 home=160 max=368000 pct=90
1008.016401 AXIS X cur=9044 target=39822 delta=5120 home=0 max=19911 pct=45
1008.246797 AXIS Z cur=333661 target=1056000 delta=13300 home=160 max=368000 pct=90
1008.247480 AXIS X cur=10157 target=39822 delta=5120 home=0 max=19911 pct=51
1008.478286 AXIS Z cur=335499 target=1056000 delta=13300 home=160 max=368000 pct=91
1008.478925 AXIS X cur=11272 target=39822 delta=5120 home=0 max=19911 pct=56
1008.701433 AXIS Z cur=337244 target=1056000 delta=13300 home=160 max=368000 pct=91
1008.702056 AXIS X cur=12332 target=39822 delta=5120 home=0 max=19911 pct=61
1008.933149 AXIS Z cur=339088 target=1056000 delta=13300 home=160 max=368000 pct=92
1008.933881 AXIS X cur=13450 target=39822 delta=5120 home=0 max=19911 pct=67
1009.164606 AXIS Z cur=340939 target=1056000 delta=13300 home=160 max=368000 pct=92
1009.165345 AXIS X cur=14575 target=39822 delta=5120 home=0 max=19911 pct=73
..
1017.308861 AXIS Z cur=363678 target=1096000 delta=2700 home=160 max=368000 pct=98
1017.309527 AXIS X cur=6096 target=0 delta=16772096 home=0 max=19911 pct=30
1017.538237 AXIS Z cur=364044 target=1096000 delta=2700 home=160 max=368000 pct=98
1017.538932 AXIS X cur=4976 target=0 delta=16772096 home=0 max=19911 pct=24
1017.771177 AXIS Z cur=364413 target=1096000 delta=2700 home=160 max=368000 pct=99
1017.771860 AXIS X cur=3850 target=0 delta=16772096 home=0 max=19911 pct=19
1018.003521 AXIS Z cur=364781 target=1096000 delta=2700 home=160 max=368000 pct=99
1018.004292 AXIS X cur=2725 target=0 delta=16772096 home=0 max=19911 pct=13
1018.224382 AXIS Z cur=365130 target=1096000 delta=2700 home=160 max=368000 pct=99
1018.224998 AXIS X cur=1658 target=0 delta=16772096 home=0 max=19911 pct=8
1018.453221 AXIS Z cur=365477 target=1096000 delta=2700 home=160 max=368000 pct=99
1018.453879 AXIS X cur=595 target=0 delta=16772096 home=0 max=19911 pct=2
..
1018.676634 AXIS Z cur=365845 target=1096000 delta=2700 home=160 max=368000 pct=99
1018.896283 AXIS Z cur=366188 target=1096000 delta=2700 home=160 max=368000 pct=99
1019.120085 AXIS Z cur=366544 target=1096000 delta=2700 home=160 max=368000 pct=99
1019.344158 AXIS Z cur=366893 target=1096000 delta=2700 home=160 max=368000 pct=99
1019.566396 AXIS Z cur=367249 target=1096000 delta=2700 home=160 max=368000 pct=99
1019.794700 AXIS Z cur=367610 target=1096000 delta=2700 home=160 max=368000 pct=99
1020.018899 AXIS Z cur=367951 target=1096000 delta=2700 home=160 max=368000 pct=99
```

VAT temperature (memory):

```
2117.898767 VAT_TEMP OK temp=19.22C online=1 state=0 control=0
2118.911357 VAT_TEMP OK temp=19.21C online=1 state=0 control=0
2120.309735 VAT_TEMP OK temp=19.22C online=1 state=0 control=0
2120.817348 VAT_TEMP OK temp=19.23C online=1 state=0 control=0
2121.373922 VAT_TEMP OK temp=19.22C online=1 state=0 control=0
2123.790651 VAT_TEMP OK temp=19.21C online=1 state=0 control=0
2124.301074 VAT_TEMP OK temp=19.22C online=1 state=0 control=0
```

OTA check for updates (function):

```
87.651633 BREAKPOINT_ADDR=0xae5b4 prototype="void ota_get_info_AIC(void)"
87.652083 REGS tid=1195 pc=0xae5b4 lr=0xb6e8f390 sp=0x85ad6d50 cpsr=0x60000010 r0=0x2e3418 r1=0x85ad7340 r2=0x85ad6d58 r3=0xae5b4
87.652436 resume -> restore=True setpc=True
87.673342 single_step -> step=False rearm=False
87.673483 breakpoint disabled_runtime after step failure
87.673655 HIT_CONFIRMED restore=1 setpc=1 step=0 rearm=0 tid=1195 pc=0xae5b4
..
87.674547 BREAKPOINT_ADDR=0xae07c prototype="int ota_get_info_request(int idx)"
87.674959 REGS tid=1194 pc=0xae07c lr=0xb6e8f390 sp=0x832d1d50 cpsr=0x60000010 r0=0x2e3418 r1=0x832d2340 r2=0x832d1d58 r3=0xae07c
87.675434 resume -> restore=True setpc=True
87.696352 single_step -> step=False rearm=False
87.696507 breakpoint disabled_runtime after step failure
87.696643 HIT_CONFIRMED restore=1 setpc=1 step=0 rearm=0 tid=1194 pc=0xae07c
```

# Rev 1

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
