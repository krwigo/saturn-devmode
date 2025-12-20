# Detour Notes

TODO:

- improving function resume (flaky)
- expose mcp server

# Rev 4

Added a plugin system with two initial plugins: debug and web. The debug plugin moves log message logic out of the main script. The web plugin creates a simple web server and returns the vat status.

```
11909.368290 using pid 726 for target /customer/resources/chitu
11909.373547 loaded 28 entries, using 6 breakpoints, 31 watches, 3 watch_blocks
11909.376332 PLUGIN plugin-debug.py loaded
11909.386211 mem_reader=/proc/pid/mem
11909.386823 INSTALL arm addr=0xae5b4 orig=0xe1200070 write=0xe1200070 read=0xe1200070 ok=True
11909.387049 armed ota_get_info_AIC@0xae5b4 mode=arm
11909.387423 INSTALL arm addr=0xae07c orig=0xe1200070 write=0xe1200070 read=0xe1200070 ok=True
11909.387578 armed ota_get_info_request@0xae07c mode=arm
11909.387884 INSTALL arm addr=0xb60f4 orig=0xe1200070 write=0xe1200070 read=0xe1200070 ok=True
11909.388041 armed ota_time_check@0xb60f4 mode=arm
11909.392445 PLUGIN plugin-debug.py axis {'axis': 0, 'label': 'Z', 'cur': None, 'target': 352000, 'delta': None, 'home': None, 'max': None, 'pct': None}
11909.393272 PLUGIN plugin-debug.py axis {'axis': 1, 'label': 'X', 'cur': None, 'target': 0, 'delta': None, 'home': None, 'max': None, 'pct': None}
11909.396133 PLUGIN plugin-debug.py printing_busy {'busy': 0}
11909.396672 PLUGIN plugin-debug.py vat_temp {'temp_c': 21.067508697509766, 'online': None, 'state': None, 'control': None, 'flag': None, 'status': 'CHECK'}
11909.945638 PLUGIN plugin-debug.py vat_temp {'temp_c': 21.070837020874023, 'online': 1, 'state': 0, 'control': 0, 'flag': 1, 'status': 'OK'}
11910.571700 PLUGIN plugin-debug.py vat_temp {'temp_c': 21.069236755371094, 'online': 1, 'state': 0, 'control': 0, 'flag': 1, 'status': 'OK'}
11911.189334 PLUGIN plugin-debug.py vat_temp {'temp_c': 21.069169998168945, 'online': 1, 'state': 0, 'control': 0, 'flag': 1, 'status': 'OK'}
11911.690451 PLUGIN plugin-debug.py vat_temp {'temp_c': 21.06926727294922, 'online': 1, 'state': 0, 'control': 0, 'flag': 1, 'status': 'OK'}
11912.203758 PLUGIN plugin-debug.py vat_temp {'temp_c': 21.070995330810547, 'online': 1, 'state': 0, 'control': 0, 'flag': 1, 'status': 'OK'}
```

```
$ curl -s http://192.168.2.1:8000/api/vat_temp | jq
{
  "temp_c": 21.08944320678711,
  "online": 1,
  "state": 0,
  "control": 0,
  "flag": 1,
  "status": "OK"
}
```

# Rev 3

Tested while the printer was idling after boot. Shows moving the plate Z axis 50 mm (`/movez 50`).

## /movez

- cur=267237 target=187237 is a delta of 80,000 steps, which matches 50�mm at 0.000625�mm/step.
- The axis marches down and stops at 187236/187244, which is just rounding jitter around the target.
- speed_mm=5.000000 means it's using the default global speed (from 0x39FAF4), not necessarily the UI-selected speed.

```
/movez 50
5791.092298 CMD pending: movez 50
5791.093215 INSTALL arm addr=0x7744c orig=0xebfe8451 write=0xe1200070 read=0xe1200070 ok=True
5791.093368 armed cmd_hook_printer_loop@0x7744c mode=arm
5791.093632 INSTALL arm addr=0x365ac orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
5791.093715 armed cmd_hook_ui_loop@0x365ac mode=arm
5791.093939 INSTALL arm addr=0x89e14 orig=0xe3a00002 write=0xe1200070 read=0xe1200070 ok=True
5791.094035 armed cmd_hook_temp_loop@0x89e14 mode=arm
5791.094171 CMD waiting for breakpoint: movez 50
5791.100938 REGS tid=746 pc=0x89e14 lr=0xae529800 sp=0xae528ce0 cpsr=0x80010010 r0=0x0 r1=0x2 r2=0x0 r3=0x0
5791.110854 BREAKPOINT_ADDR=0x89e14 prototype="void cmd_hook_temp_loop(void)"
5791.111516 REGS tid=746 pc=0x89e14 lr=0xae529800 sp=0xae528ce0 cpsr=0x80010010 r0=0x0 r1=0x2 r2=0x0 r3=0x0
5791.111975 resume -> restore=True setpc=True
5791.112476 INSTALL arm addr=0x89e18 orig=0xebfffac0 write=0xe1200070 read=0xe1200070 ok=True
5791.117830 temp_step -> step=True rearm=True wait_r=746 wait_status=1407
5791.118445 HIT_CONFIRMED restore=1 setpc=1 step=1 rearm=1 tid=746 pc=0x89e14
5791.124098 CMD movez axis=0 cur=267237 target=187237 dist_mm=50.000000 pos_mm=117.023125 speed_mm=5.000000 flags=0x0
5791.133830 CMD injecting addr=0x535ac thumb=False args=[0, 0, 0, 0]
5791.134453 INSTALL arm addr=0x89e18 orig=0xebfffac0 write=0xe1200070 read=0xe1200070 ok=True
5791.139238 CMD inject call addr=0x535ac thumb=False r0=0 r1=0 r2=0 r3=0 retval=1 (1) restore=ok wait_r=746 wait_status=1407
5791.156799 AXIS Z cur=267237 target=187236 delta=-200 home=160 max=368000 pct=72
5791.387292 AXIS Z cur=266942 target=187236 delta=-3300 home=160 max=368000 pct=72
5791.614549 AXIS Z cur=266107 target=187236 delta=-7100 home=160 max=368000 pct=72
5791.827249 AXIS Z cur=264808 target=187236 delta=-10900 home=160 max=368000 pct=71
5792.045705 AXIS Z cur=263109 target=187236 delta=-13400 home=160 max=368000 pct=71
5792.274769 AXIS Z cur=261273 target=187236 delta=-13400 home=160 max=368000 pct=70
5792.501702 AXIS Z cur=259503 target=187236 delta=-13400 home=160 max=368000 pct=70
5792.730904 AXIS Z cur=257663 target=187236 delta=-13400 home=160 max=368000 pct=70
5792.967048 AXIS Z cur=255738 target=187236 delta=-13400 home=160 max=368000 pct=69
5793.190039 AXIS Z cur=253997 target=187236 delta=-13400 home=160 max=368000 pct=69
5793.309578 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
5793.410917 AXIS Z cur=252237 target=187236 delta=-13400 home=160 max=368000 pct=68
5793.633100 AXIS Z cur=250424 target=187236 delta=-13400 home=160 max=368000 pct=68
5793.853976 AXIS Z cur=248619 target=187236 delta=-13400 home=160 max=368000 pct=67
5794.075882 AXIS Z cur=246899 target=187236 delta=-13400 home=160 max=368000 pct=67
5794.309567 AXIS Z cur=245012 target=187236 delta=-13400 home=160 max=368000 pct=66
5794.519376 AXIS Z cur=243291 target=187236 delta=-13400 home=160 max=368000 pct=66
5794.735521 AXIS Z cur=241568 target=187236 delta=-13400 home=160 max=368000 pct=65
5794.958432 AXIS Z cur=239845 target=187236 delta=-13400 home=160 max=368000 pct=65
5795.175815 AXIS Z cur=238114 target=187236 delta=-13400 home=160 max=368000 pct=64
5795.303573 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
5795.314347 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
5795.398956 AXIS Z cur=236319 target=187236 delta=-13400 home=160 max=368000 pct=64
5795.621184 AXIS Z cur=234505 target=187236 delta=-13400 home=160 max=368000 pct=63
5795.844723 AXIS Z cur=232689 target=187236 delta=-13400 home=160 max=368000 pct=63
5796.078702 AXIS Z cur=230877 target=187236 delta=-13400 home=160 max=368000 pct=62
5796.292425 AXIS Z cur=229144 target=187236 delta=-13400 home=160 max=368000 pct=62
5796.508323 AXIS Z cur=227410 target=187236 delta=-13400 home=160 max=368000 pct=61
5796.740275 AXIS Z cur=225597 target=187236 delta=-13400 home=160 max=368000 pct=61
5796.959188 AXIS Z cur=223787 target=187236 delta=-13400 home=160 max=368000 pct=60
5797.175849 AXIS Z cur=222054 target=187236 delta=-13400 home=160 max=368000 pct=60
5797.305733 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
5797.394064 AXIS Z cur=220354 target=187236 delta=-13400 home=160 max=368000 pct=59
5797.617870 AXIS Z cur=218529 target=187236 delta=-13400 home=160 max=368000 pct=59
5797.852685 AXIS Z cur=216705 target=187236 delta=-13400 home=160 max=368000 pct=58
5798.075619 AXIS Z cur=214876 target=187236 delta=-13400 home=160 max=368000 pct=58
5798.297880 AXIS Z cur=213132 target=187236 delta=-13400 home=160 max=368000 pct=57
5798.518532 AXIS Z cur=211309 target=187236 delta=-13400 home=160 max=368000 pct=57
5798.729564 AXIS Z cur=209666 target=187236 delta=-13400 home=160 max=368000 pct=56
5798.958223 AXIS Z cur=207861 target=187236 delta=-13400 home=160 max=368000 pct=56
5799.176661 AXIS Z cur=206113 target=187236 delta=-13400 home=160 max=368000 pct=55
5799.397075 AXIS Z cur=204281 target=187236 delta=-13400 home=160 max=368000 pct=55
5799.617561 AXIS Z cur=202557 target=187236 delta=-13400 home=160 max=368000 pct=55
5799.844149 AXIS Z cur=200723 target=187236 delta=-13400 home=160 max=368000 pct=54
5800.060997 AXIS Z cur=198968 target=187236 delta=-13400 home=160 max=368000 pct=54
5800.296365 AXIS Z cur=197072 target=187236 delta=-13400 home=160 max=368000 pct=53
5800.517163 AXIS Z cur=195343 target=187236 delta=-13400 home=160 max=368000 pct=53
5800.741429 AXIS Z cur=193535 target=187236 delta=-13400 home=160 max=368000 pct=52
5800.971399 AXIS Z cur=191729 target=187236 delta=-13400 home=160 max=368000 pct=52
5801.202326 AXIS Z cur=189861 target=187236 delta=-13400 home=160 max=368000 pct=51
5801.300713 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
5801.418711 AXIS Z cur=188553 target=187236 delta=-9600 home=160 max=368000 pct=51
5801.643468 AXIS Z cur=187648 target=187236 delta=-5600 home=160 max=368000 pct=50
5801.875629 AXIS Z cur=187283 target=187236 delta=-1700 home=160 max=368000 pct=50
5802.099501 AXIS Z cur=187262 target=187236 delta=-200 home=160 max=368000 pct=50
5802.326278 AXIS Z cur=187244 target=187236 delta=-200 home=160 max=368000 pct=50
5803.301475 REGS tid=746 pc=0xb471d46c lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0x0 r1=0x0 r2=0xae5293c4 r3=0x0
```

## /home

- CMD home axis=0 correctly calls 0x53548 (reset/stop) then 0x53704 (home). That's the same path the UI uses.
- The huge target=907235 while max=368000 is expected: homing runs a long endstop seek move with flag 0xD, so it doesn't clamp to max - it keeps moving until the endstop triggers. That's the long stretch of delta=-13300 chunks as cur rises toward the top.
- The target=360000 segment is the backoff/slow re‑home pass; it reverses and finishes near the top. You can see the smaller steps and the final settle around 360000.
- The later target=1096000 with delta=2700 looks like the final slow creep/settle phase, again using endstop logic, so the target can be “virtual” and beyond max while the endstop controls the stop.

The behavior is consistent with sub_53704: a fast move to trip the endstop, then slow re‑home/backoff, then a final settle.

```
/home
6482.221822 CMD pending: home
6482.222701 INSTALL arm addr=0x7744c orig=0xebfe8451 write=0xe1200070 read=0xe1200070 ok=True
6482.222891 armed cmd_hook_printer_loop@0x7744c mode=arm
6482.223310 INSTALL arm addr=0x365ac orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
6482.223480 armed cmd_hook_ui_loop@0x365ac mode=arm
6482.223824 INSTALL arm addr=0x89e14 orig=0xe3a00002 write=0xe1200070 read=0xe1200070 ok=True
6482.223971 armed cmd_hook_temp_loop@0x89e14 mode=arm
6482.224199 CMD waiting for breakpoint: home
6482.273885 REGS tid=746 pc=0x89e14 lr=0xae529800 sp=0xae528ce0 cpsr=0x80010010 r0=0x0 r1=0x2 r2=0x0 r3=0x0
6482.274290 BREAKPOINT_ADDR=0x89e14 prototype="void cmd_hook_temp_loop(void)"
6482.274541 REGS tid=746 pc=0x89e14 lr=0xae529800 sp=0xae528ce0 cpsr=0x80010010 r0=0x0 r1=0x2 r2=0x0 r3=0x0
6482.274875 resume -> restore=True setpc=True
6482.275281 INSTALL arm addr=0x89e18 orig=0xebfffac0 write=0xe1200070 read=0xe1200070 ok=True
6482.282391 temp_step -> step=True rearm=True wait_r=746 wait_status=1407
6482.282577 HIT_CONFIRMED restore=1 setpc=1 step=1 rearm=1 tid=746 pc=0x89e14
6482.282754 CMD home axis=0
6482.282955 CMD injecting addr=0x53548 thumb=False args=[0, 0, 0, 0]
6482.283583 INSTALL arm addr=0x89e18 orig=0xebfffac0 write=0xe1200070 read=0xe1200070 ok=True
6482.293091 CMD inject call addr=0x53548 thumb=False r0=0 r1=0 r2=0 r3=0 retval=0 (0) restore=ok wait_r=746 wait_status=1407
6482.293354 CMD injecting addr=0x53704 thumb=False args=[0, 0, 0, 0]
6482.293864 INSTALL arm addr=0x89e18 orig=0xebfffac0 write=0xe1200070 read=0xe1200070 ok=True
6482.303306 CMD inject call addr=0x53704 thumb=False r0=0 r1=0 r2=0 r3=0 retval=1 (1) restore=ok wait_r=746 wait_status=1407
6482.373111 AXIS Z cur=171235 target=907235 delta=-200 home=160 max=368000 pct=46   ; target=907235
6482.591309 AXIS Z cur=171560 target=907235 delta=3700 home=160 max=368000 pct=46
6482.804567 AXIS Z cur=172368 target=907235 delta=7300 home=160 max=368000 pct=46
6482.956150 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
6483.025104 AXIS Z cur=173740 target=907235 delta=11100 home=160 max=368000 pct=47
6483.252530 AXIS Z cur=175511 target=907235 delta=13300 home=160 max=368000 pct=47
6483.481278 AXIS Z cur=177302 target=907235 delta=13300 home=160 max=368000 pct=48
..
6503.317966 AXIS Z cur=334783 target=907235 delta=13300 home=160 max=368000 pct=90
6503.543407 AXIS Z cur=336586 target=907235 delta=13300 home=160 max=368000 pct=91
6503.776262 AXIS Z cur=338469 target=907235 delta=13300 home=160 max=368000 pct=91
6504.006718 AXIS Z cur=340270 target=907235 delta=13300 home=160 max=368000 pct=92
6504.234307 AXIS Z cur=342079 target=907235 delta=13300 home=160 max=368000 pct=92
6504.458858 AXIS Z cur=343878 target=907235 delta=13300 home=160 max=368000 pct=93
6504.687568 AXIS Z cur=345678 target=907235 delta=13300 home=160 max=368000 pct=93
6504.918353 AXIS Z cur=347561 target=907235 delta=13300 home=160 max=368000 pct=94
6505.139476 AXIS Z cur=349280 target=907235 delta=13300 home=160 max=368000 pct=94
6505.365561 AXIS Z cur=351081 target=907235 delta=13300 home=160 max=368000 pct=95
6505.594994 AXIS Z cur=352883 target=907235 delta=13300 home=160 max=368000 pct=95
6505.816354 AXIS Z cur=354684 target=907235 delta=13300 home=160 max=368000 pct=96
6506.050678 AXIS Z cur=356484 target=907235 delta=13300 home=160 max=368000 pct=96
6506.283828 AXIS Z cur=358367 target=907235 delta=13300 home=160 max=368000 pct=97
6506.514195 AXIS Z cur=360171 target=907235 delta=13300 home=160 max=368000 pct=97
6506.748318 AXIS Z cur=362050 target=907235 delta=13300 home=160 max=368000 pct=98
6506.970496 AXIS Z cur=363846 target=907235 delta=13300 home=160 max=368000 pct=98
6507.182927 AXIS Z cur=365479 target=907235 delta=13300 home=160 max=368000 pct=99
6507.413631 AXIS Z cur=367363 target=907235 delta=13300 home=160 max=368000 pct=99  ; target=907235
6507.640609 AXIS Z cur=367922 target=360000 delta=-1300 home=160 max=368000 pct=99  ; target=360000
6507.872053 AXIS Z cur=367358 target=360000 delta=-5300 home=160 max=368000 pct=99
6508.097882 AXIS Z cur=366253 target=360000 delta=-9100 home=160 max=368000 pct=99
6508.334049 AXIS Z cur=364536 target=360000 delta=-13300 home=160 max=368000 pct=99
6508.568853 AXIS Z cur=362669 target=360000 delta=-13300 home=160 max=368000 pct=98
6508.786470 AXIS Z cur=361304 target=360000 delta=-9600 home=160 max=368000 pct=98
6509.009764 AXIS Z cur=360437 target=360000 delta=-5800 home=160 max=368000 pct=97
6509.244364 AXIS Z cur=360047 target=360000 delta=-1700 home=160 max=368000 pct=97
6509.457978 AXIS Z cur=360026 target=360000 delta=-200 home=160 max=368000 pct=97
6509.692420 AXIS Z cur=360007 target=360000 delta=-200 home=160 max=368000 pct=97   ; target=360000
6509.924427 AXIS Z cur=360065 target=1096000 delta=1100 home=160 max=368000 pct=97  ; target=1096000
6510.154482 AXIS Z cur=360434 target=1096000 delta=2700 home=160 max=368000 pct=97
6510.376976 AXIS Z cur=360779 target=1096000 delta=2700 home=160 max=368000 pct=98
6510.609121 AXIS Z cur=361139 target=1096000 delta=2700 home=160 max=368000 pct=98
6510.835803 AXIS Z cur=361501 target=1096000 delta=2700 home=160 max=368000 pct=98
6510.966321 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
6511.061513 AXIS Z cur=361862 target=1096000 delta=2700 home=160 max=368000 pct=98
6511.267657 AXIS Z cur=362190 target=1096000 delta=2700 home=160 max=368000 pct=98
6511.502914 AXIS Z cur=362550 target=1096000 delta=2700 home=160 max=368000 pct=98
6511.732548 AXIS Z cur=362918 target=1096000 delta=2700 home=160 max=368000 pct=98
6511.961508 AXIS Z cur=363277 target=1096000 delta=2700 home=160 max=368000 pct=98
6512.186501 AXIS Z cur=363636 target=1096000 delta=2700 home=160 max=368000 pct=98
6512.407934 AXIS Z cur=363982 target=1096000 delta=2700 home=160 max=368000 pct=98
6512.635311 AXIS Z cur=364343 target=1096000 delta=2700 home=160 max=368000 pct=99
6512.862920 AXIS Z cur=364702 target=1096000 delta=2700 home=160 max=368000 pct=99
6512.992981 REGS tid=746 pc=0xb471d468 lr=0xae529800 sp=0xae528cc0 cpsr=0x80010010 r0=0xae528cd0 r1=0x0 r2=0xae5293c4 r3=0x0
6513.075513 AXIS Z cur=365038 target=1096000 delta=2700 home=160 max=368000 pct=99
6513.301484 AXIS Z cur=365398 target=1096000 delta=2700 home=160 max=368000 pct=99
6513.512693 AXIS Z cur=365739 target=1096000 delta=2700 home=160 max=368000 pct=99
6513.726242 AXIS Z cur=366065 target=1096000 delta=2700 home=160 max=368000 pct=99
6513.957488 AXIS Z cur=366439 target=1096000 delta=2700 home=160 max=368000 pct=99
6514.191899 AXIS Z cur=366812 target=1096000 delta=2700 home=160 max=368000 pct=99
6514.413921 AXIS Z cur=367155 target=1096000 delta=2700 home=160 max=368000 pct=99
6514.630419 AXIS Z cur=367498 target=1096000 delta=2700 home=160 max=368000 pct=99
6514.848978 AXIS Z cur=367843 target=1096000 delta=2700 home=160 max=368000 pct=99
```

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
