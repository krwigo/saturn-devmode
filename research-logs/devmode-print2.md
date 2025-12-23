# Devmode Print 2 Timeline Analysis

This analysis uses the monotonic timestamps from the log and keeps the exact log lines for each cited event.

## Timeline (key events)

- Tracer attaches, loads config, and arms OTA breakpoints.
```
3536.370088 using pid 721 for target /customer/resources/chitu
3536.385483 loaded 28 entries, using 6 breakpoints, 48 watches, 3 watch_blocks
3536.401041 plugin-logger.py loaded
3536.415178 mem_reader=/proc/pid/mem
3536.415767 INSTALL arm addr=0xae5b4 orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
3536.415972 armed ota_get_info_AIC@0xae5b4 mode=arm
3536.416417 INSTALL arm addr=0xae07c orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
3536.416599 armed ota_get_info_request@0xae07c mode=arm
3536.416968 INSTALL arm addr=0xb60f4 orig=0xe3043e78 write=0xe1200070 read=0xe1200070 ok=True
3536.417174 armed ota_time_check@0xb60f4 mode=arm
```

- Vat temperature comes online at ~18.38 C.
```
3536.452480 plugin-logger.py event vat_temperature values={'tank_heat_control': None, 'tank_heat_state': None, 'tank_temp_c': 18.378889083862305, 'tank_temp_flag': None, 'tank_temp_online': None}
3536.462798 plugin-logger.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 18.378889083862305, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

- SDCP metadata resolves (brand/id/name/protocol + resolution).
```
3536.497356 plugin-logger.py event sdcp values={'sdcp_brand_name_value_buf': 1195723845, 'sdcp_id_value': 842347110, 'sdcp_machine_name_value_buf': 1970561363, 'sdcp_name_value_buf': 1970561363, 'sdcp_protocol_version_value': 808334166, 'sdcp_resolution_height': 6230, 'sdcp_resolution_width': 15120, 'sdcp_xyzsize_value': 775434546}
```

- The `/home` command is queued and injected via the temp loop hook (cmd_hook_temp_loop).
```
3538.392465 CMD pending: home
3538.394515 INSTALL arm addr=0x7744c orig=0xebfe8451 write=0xe1200070 read=0xe1200070 ok=True
3538.394671 armed cmd_hook_printer_loop@0x7744c mode=arm
3538.395273 INSTALL arm addr=0x365ac orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
3538.395383 armed cmd_hook_ui_loop@0x365ac mode=arm
3538.395849 INSTALL arm addr=0x89e14 orig=0xe3a00002 write=0xe1200070 read=0xe1200070 ok=True
3538.395935 armed cmd_hook_temp_loop@0x89e14 mode=arm
3538.396428 CMD waiting for breakpoint: home
3538.477468 [33mBREAKPOINT_ADDR=0x89e14[0m [32mprototype="void cmd_hook_temp_loop(void)"[0m
3538.478206 plugin-logger.py event cmd_hook_temp_loop payload={'name': 'cmd_hook_temp_loop', 'addr': 564756, 'pc': 564756}
3538.478582 REGS tid=764 pc=0x89e14 lr=0xa2c1b800 sp=0xa2c1ace0 cpsr=0x80010010 r0=0x0 r1=0x2 r2=0x0 r3=0x0
3538.484623 [35mHIT_CONFIRMED restore=1 setpc=1 step=1 rearm=1 tid=764 pc=0x89e14[0m
3538.484760 CMD home axis=0
3538.484900 CMD injecting addr=0x53548 thumb=False args=[0, 0, 0, 0]
3538.497238 CMD inject call addr=0x53548 thumb=False r0=0 r1=0 r2=0 r3=0 retval=0 (0) restore=ok wait_r=764 wait_status=1407
3538.497471 CMD injecting addr=0x53704 thumb=False args=[0, 0, 0, 0]
3538.516127 CMD inject call addr=0x53704 thumb=False r0=0 r1=0 r2=0 r3=0 retval=1 (1) restore=ok wait_r=764 wait_status=1407
```

- Printer state machine moves through IDLE -> HOME -> CALIBRATE -> PROBE -> HEAT -> LEVEL. (State mapping from `PROJECT.md`.)
```
3576.866457 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': None, 'printer_event_code': None, 'printer_exposure_time_ms': None, 'printer_heat_stage': None, 'printer_options': None, 'printer_pause_flags': None, 'printer_skip_mask': None, 'printer_state': 1, 'printer_uv_pwm': None, 'printer_wait_reason': None, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3577.001945 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3577.072448 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3589.445105 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 3, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3594.435555 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 4, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3647.203645 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 6, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
4196.436994 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 5, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Printing enters STAGE1/2/3 with base-layer exposure (25000 ms, UV PWM 204).
```
4264.140286 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
4264.295388 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
4290.312675 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 3, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Layer counting begins and normal-layer exposure is active (2300 ms, UV PWM 255).
```
4298.907722 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 1, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
4298.964676 plugin-logger.py event printer values={'print_info_current_layer': 1, 'print_info_status': 3, 'print_info_total_layer': 162, 'printer_current_layer': 1, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
4623.408686 plugin-logger.py event printer values={'print_info_current_layer': 12, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 13, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Print completes: STOPPING (state 14) then FINISH (state 9).
```
5938.219748 plugin-logger.py event printer values={'print_info_current_layer': 161, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
5938.444483 plugin-logger.py event printer values={'print_info_current_layer': 161, 'print_info_status': 7, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
5938.446767 plugin-logger.py event printer values={'print_info_current_layer': 162, 'print_info_status': 7, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
5959.710894 plugin-logger.py event printer values={'print_info_current_layer': 162, 'print_info_status': 7, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 9, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
5959.944373 plugin-logger.py event printer values={'print_info_current_layer': 162, 'print_info_status': 9, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 9, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Final temperature sample shows the vat around 19.94 C.
```
14131.990821 plugin-logger.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 19.9448299407959, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

## Observations and learnings

- Total log span is about 10595.6 seconds (3536.370088 -> 14131.990821), roughly 2.94 hours, consistent with a full 162-layer print and long base layers.
- State transitions follow the expected SLA sequence; HEAT (6) completes before LEVEL (5), then the STAGE1/2/3 loop repeats for layers.
- The `/home` command is executed early via cmd_hook_temp_loop, indicating a manual or scripted homing action before printing begins.
- Exposure settings shift from base-layer values (25000 ms, UV PWM 204) to normal-layer values (2300 ms, UV PWM 255).
- No error strings appear; vat temperature remains stable, rising from ~18.38 C to ~19.94 C by the end of the log.

## Potential follow-ups

- Confirm whether the early `/home` command is expected in the workflow; if not, tighten when cmd hooks are armed.
- If exposure timings should be uniform, verify the base-to-normal transition aligns with the print profile.
