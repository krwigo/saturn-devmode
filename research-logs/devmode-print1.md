# Devmode Print 1 Timeline Analysis

This analysis uses the monotonic timestamps from the log and keeps the exact log lines for each cited event.

## Timeline (key events)

- Tracer attaches, loads config, and arms OTA breakpoints.
```
1184.676311 using pid 726 for target /customer/resources/chitu
1184.684040 loaded 28 entries, using 6 breakpoints, 39 watches, 3 watch_blocks
1184.688919 PLUGIN plugin-example.py loaded
1185.000584 PLUGIN plugin-web.py web listening on http://0.0.0.0:8000/api/vat_temp
1185.010782 mem_reader=/proc/pid/mem
1185.011660 armed ota_get_info_AIC@0xae5b4 mode=arm
1185.012374 armed ota_get_info_request@0xae07c mode=arm
1185.012867 armed ota_time_check@0xb60f4 mode=arm
```

- Vat temperature comes online at ~16.68 C.
```
1185.034335 PLUGIN plugin-example.py event vat_temperature values={'tank_heat_control': None, 'tank_heat_state': None, 'tank_temp_c': 16.681594848632812, 'tank_temp_flag': None, 'tank_temp_online': None}
1185.042082 PLUGIN plugin-example.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 16.681594848632812, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

- Printing modes are enabled.
```
1190.353336 PLUGIN plugin-example.py event printing values={'printing_level_mode': 1, 'printing_sync_mode': None}
1190.355522 PLUGIN plugin-example.py event printing values={'printing_level_mode': 1, 'printing_sync_mode': 1}
```

- Printer state machine moves through IDLE -> HOME -> CALIBRATE -> PROBE -> HEAT -> LEVEL. (State mapping from `PROJECT.md`.)
```
1190.458803 PLUGIN plugin-example.py event printer values={'printer_current_layer': None, 'printer_event_code': None, 'printer_heat_stage': None, 'printer_options': None, 'printer_pause_flags': None, 'printer_skip_mask': None, 'printer_state': 1, 'printer_wait_reason': None}
1190.577166 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_wait_reason': 0}
1203.067661 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 3, 'printer_wait_reason': 0}
1208.101852 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 4, 'printer_wait_reason': 0}
1260.660900 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 6, 'printer_wait_reason': 0}
1885.515193 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 5, 'printer_wait_reason': 0}
```

- Printing enters STAGE1/2/3.
```
1952.678260 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_wait_reason': 0}
1952.848583 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_wait_reason': 0}
1983.875829 PLUGIN plugin-example.py event printer values={'printer_current_layer': 0, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_wait_reason': 0}
```

- Layer counting begins and progresses to the late-print stage (no total-layer value is logged in this file).
```
1992.430028 PLUGIN plugin-example.py event printer values={'printer_current_layer': 1, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_wait_reason': 0}
4641.913800 PLUGIN plugin-example.py event printer values={'printer_current_layer': 280, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_wait_reason': 0}
4729.695583 PLUGIN plugin-example.py event printer values={'printer_current_layer': 291, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_wait_reason': 0}
```

- Print completes: STOPPING (state 14) then FINISH (state 9).
```
4729.792089 PLUGIN plugin-example.py event printer values={'printer_current_layer': 291, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_wait_reason': 0}
4751.219339 PLUGIN plugin-example.py event printer values={'printer_current_layer': 291, 'printer_event_code': 0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 9, 'printer_wait_reason': 0}
```

- Late vat temperature sample before the command hook sequence.
```
4948.172957 PLUGIN plugin-example.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 25.949703216552734, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

- The `/home` command is queued and the printer-loop hook fires; the session then unloads plugins.
```
4948.195551 CMD pending: home
4948.197061 INSTALL arm addr=0x7744c orig=0xebfe8451 write=0xe1200070 read=0xe1200070 ok=True
4948.197312 armed cmd_hook_printer_loop@0x7744c mode=arm
4948.197743 INSTALL arm addr=0x365ac orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
4948.197843 armed cmd_hook_ui_loop@0x365ac mode=arm
4948.198373 INSTALL arm addr=0x89e14 orig=0xe3a00002 write=0xe1200070 read=0xe1200070 ok=True
4948.198477 armed cmd_hook_temp_loop@0x89e14 mode=arm
4948.199239 CMD waiting for breakpoint: home
4948.210653 [33mBREAKPOINT_ADDR=0x7744c[0m [32mprototype="void cmd_hook_printer_loop(void)"[0m
4948.211381 PLUGIN plugin-example.py event cmd_hook_printer_loop payload={'name': 'cmd_hook_printer_loop', 'addr': 488524, 'pc': 488524}
4948.211851 REGS tid=780 pc=0x7744c lr=0xd3e38 sp=0x9ccbccf8 cpsr=0x60000010 r0=0x2710 r1=0x9ccbccd4 r2=0x3 r3=0x3
4948.212304 resume -> restore=True setpc=True
4948.262046 PLUGIN plugin-example.py unloaded
4948.296672 PLUGIN plugin-web.py web stopped
```

## Observations and learnings

- Total log span is about 3763.6 seconds (1184.676311 -> 4948.296672), roughly 62.7 minutes.
- State transitions follow the expected SLA flow through HEAT/LEVEL and the STAGE1/2/3 loop before STOPPING/FINISH.
- Layer tracking shows progress to layer 291; the log does not include total-layer or exposure/UV settings for this run.
- Vat temperature rises from ~16.68 C at startup to ~25.95 C near the end.
- No error strings appear in the log; the /home hook fires after the print completes.

## Potential follow-ups

- If exposure/UV data is needed for this run, add the `print_info_*`/exposure watches to the configuration and re-capture.
- Confirm whether the post-print `/home` command is expected in the workflow or should be gated.
