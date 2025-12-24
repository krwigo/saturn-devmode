# Devmode Print 5 Timeline Analysis

This analysis uses the monotonic timestamps from the log and keeps the exact log lines for each cited event.

## Timeline (key events)

- Tracer attaches, loads config, and arms OTA breakpoints.
```
330.632389 using pid 721 for target /customer/resources/chitu
330.654072 loaded 28 entries, using 6 breakpoints, 50 watches, 3 watch_blocks
330.667817 plugin-logger.py loaded
330.699146 mem_reader=/proc/pid/mem
330.700298 armed ota_get_info_AIC@0xae5b4 mode=arm
330.701330 armed ota_get_info_request@0xae07c mode=arm
330.702642 armed ota_time_check@0xb60f4 mode=arm
```

- Initial vat temperature telemetry comes online (about 22.23 C at startup).
```
330.745135 plugin-logger.py event vat_temperature values={'tank_heat_control': None, 'tank_heat_state': None, 'tank_temp_c': 22.233322143554688, 'tank_temp_flag': None, 'tank_temp_online': None}
330.746573 plugin-logger.py event vat_temperature values={'tank_heat_control': None, 'tank_heat_state': None, 'tank_temp_c': 22.233322143554688, 'tank_temp_flag': None, 'tank_temp_online': 1}
```

- SDCP metadata resolves (brand/id/name/protocol + resolution).
```
330.826172 plugin-logger.py event sdcp values={'sdcp_brand_name_value_buf': 1195723845, 'sdcp_id_value': 842347110, 'sdcp_machine_name_value_buf': 1970561363, 'sdcp_name_value_buf': 1970561363, 'sdcp_protocol_version_value': 808334166, 'sdcp_resolution_height': 6230, 'sdcp_resolution_width': 15120, 'sdcp_xyzsize_value': 775434546}
```

- Printing modes are enabled.
```
368.879652 plugin-logger.py event printing values={'printing_level_mode': 1, 'printing_sync_mode': None}
368.881098 plugin-logger.py event printing values={'printing_level_mode': 1, 'printing_sync_mode': 1}
```

- Printer enters IDLE then HOME; print job metadata reports 291 total layers. (State mapping from `PROJECT.md`: 1=IDLE, 2=HOME.)
```
368.937651 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': None, 'printer_event_code': None, 'printer_exposure_time_ms': None, 'printer_heat_stage': None, 'printer_options': None, 'printer_pause_flags': None, 'printer_skip_mask': None, 'printer_state': 1, 'printer_uv_pwm': None, 'printer_wait_reason': None, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
369.090957 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
369.104339 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Early prep states: CALIBRATE, PROBE, HEAT, LEVEL. (State mapping: 3=CALIBRATE, 4=PROBE, 6=HEAT, 5=LEVEL.)
```
381.533041 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 3, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
386.535923 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 4, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
437.423718 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 6, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
704.498743 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 5, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Heat stage ramps while in HEAT, reaching stage 2 before LEVEL completes.
```
437.432312 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 1, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 6, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
697.167479 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 6, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Base-layer exposure appears (23000 ms, UV PWM 255).
```
770.117445 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 23000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 5, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Printing enters STAGE1/2/3 with base-layer exposure. (State mapping: 10=STAGE1, 11=STAGE2, 12=STAGE3.)
```
770.181100 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 23000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
770.346078 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 2, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 23000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
793.858410 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 3, 'print_info_total_layer': 291, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 23000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Layer counting begins (layer 1 appears).
```
802.417214 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 291, 'printer_current_layer': 1, 'printer_event_code': 0, 'printer_exposure_time_ms': 23000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Normal-layer exposure appears (2300 ms, UV PWM 255).
```
1153.258381 plugin-logger.py event printer values={'print_info_current_layer': 14, 'print_info_status': 4, 'print_info_total_layer': 291, 'printer_current_layer': 15, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Layer progression reaches mid-print and the final layer.
```
2307.091206 plugin-logger.py event printer values={'print_info_current_layer': 144, 'print_info_status': 4, 'print_info_total_layer': 291, 'printer_current_layer': 145, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3442.616475 plugin-logger.py event printer values={'print_info_current_layer': 290, 'print_info_status': 4, 'print_info_total_layer': 291, 'printer_current_layer': 291, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Print completes: STOPPING then FINISH. (State mapping: 14=STOPPING, 9=FINISH.)
```
3442.670854 plugin-logger.py event printer values={'print_info_current_layer': 290, 'print_info_status': 4, 'print_info_total_layer': 291, 'printer_current_layer': 291, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
3464.134867 plugin-logger.py event printer values={'print_info_current_layer': 291, 'print_info_status': 7, 'print_info_total_layer': 291, 'printer_current_layer': 291, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 9, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Final temperature sample shows the vat around 32.88 C.
```
3525.913410 plugin-logger.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 32.87955093383789, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

## Observations and learnings

- Total log span is about 3195.3 seconds (330.632389 -> 3525.913410), roughly 53.3 minutes, matching a 291-layer print with long base layers and shorter normal exposures.
- State transitions are orderly and match the expected SLA sequence: IDLE -> HOME -> CALIBRATE -> PROBE -> HEAT -> LEVEL -> STAGE1/2/3 -> STOPPING -> FINISH.
- Exposure and UV settings shift from base-layer values (23000 ms, UV PWM 255) to normal-layer values (2300 ms, UV PWM 255), indicating the base-layer phase ends by around layer 15.
- Heat stage rises from 0 to 1 and then 2 during HEAT and remains at stage 2 for the rest of the print.
- No error strings appear in the log; vat temperature climbs from ~22.23 C to ~32.88 C by the end of the capture.

## Potential follow-ups

- Confirm the base exposure (23000 ms) and normal exposure (2300 ms) match the intended print profile for this 291-layer job.
- If a `/home` hook is expected during startup, it does not appear in this log; verify whether that is intentional.
