# Devmode Print 3 Timeline Analysis

This analysis uses the monotonic timestamps from the log and keeps the exact log lines for each cited event.

## Timeline (key events)

- Tracer attaches, loads config, and arms OTA breakpoints.
```
524.260693 using pid 726 for target /customer/resources/chitu
524.281173 loaded 28 entries, using 6 breakpoints, 48 watches, 3 watch_blocks
524.304055 plugin-logger.py loaded
524.333671 mem_reader=/proc/pid/mem
524.334624 armed ota_get_info_AIC@0xae5b4 mode=arm
524.335473 armed ota_get_info_request@0xae07c mode=arm
524.335961 armed ota_time_check@0xb60f4 mode=arm
```

- Initial vat temperature telemetry comes online (about 29.68 C at startup).
```
524.361299 plugin-logger.py event vat_temperature values={'tank_heat_control': None, 'tank_heat_state': None, 'tank_temp_c': 29.681901931762695, 'tank_temp_flag': None, 'tank_temp_online': None}
524.365447 plugin-logger.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 29.681901931762695, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

- SDCP metadata resolves (brand/id/name/protocol + resolution).
```
524.420631 plugin-logger.py event sdcp values={'sdcp_brand_name_value_buf': 1195723845, 'sdcp_id_value': 842347110, 'sdcp_machine_name_value_buf': 1970561363, 'sdcp_name_value_buf': 1970561363, 'sdcp_protocol_version_value': 808334166, 'sdcp_resolution_height': 6230, 'sdcp_resolution_width': 15120, 'sdcp_xyzsize_value': 775434546}
```

- Printing modes are enabled.
```
549.900402 plugin-logger.py event printing values={'printing_level_mode': 1, 'printing_sync_mode': None}
549.901483 plugin-logger.py event printing values={'printing_level_mode': 1, 'printing_sync_mode': 1}
```

- Printer state machine transitions from IDLE to HOME. (State mapping from `PROJECT.md`: 1=IDLE, 2=HOME.)
```
549.961760 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': None, 'printer_event_code': None, 'printer_exposure_time_ms': None, 'printer_heat_stage': None, 'printer_options': None, 'printer_pause_flags': None, 'printer_skip_mask': None, 'printer_state': 1, 'printer_uv_pwm': None, 'printer_wait_reason': None, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
549.971729 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': None, 'printer_heat_stage': None, 'printer_options': 0, 'printer_pause_flags': None, 'printer_skip_mask': None, 'printer_state': 1, 'printer_uv_pwm': None, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
550.075490 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 0, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Print job metadata appears: total layers = 162; print status enters active queue.
```
550.091780 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 0, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
550.258657 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 2, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Early prep states: CALIBRATE, PROBE, LEVEL. (State mapping: 3=CALIBRATE, 4=PROBE, 5=LEVEL.)
```
562.470824 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 3, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
567.492403 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 4, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
618.275491 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 5, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Printing enters STAGE1/2/3. (State mapping: 10=STAGE1, 11=STAGE2, 12=STAGE3.)
```
691.456887 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 0.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
691.684078 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 2, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
717.711920 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 3, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Early exposure settings: base exposure 25000 ms, UV PWM 204; print status steps to 2 and 3; then to 4 (steady printing). Heat stage ramps 0 -> 1 -> 2.
```
691.462111 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 0.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
691.463125 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 1, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
691.518895 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 2, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
691.730770 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 3, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
717.732861 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 0, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
718.694375 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 1, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
725.147879 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Layer counting begins (layer 1 appears) and state cycles back into STAGE1/STAGE2 for the layer loop.
```
726.285347 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 0, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
726.299354 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 1, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
726.341050 plugin-logger.py event printer values={'print_info_current_layer': 0, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 1, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
726.352235 plugin-logger.py event printer values={'print_info_current_layer': 1, 'print_info_status': 3, 'print_info_total_layer': 162, 'printer_current_layer': 1, 'printer_event_code': 0, 'printer_exposure_time_ms': 25000.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 204.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Mid-print exposure and UV settings shift to normal-layer values.
```
864.629372 plugin-logger.py event printer values={'print_info_current_layer': 4, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 5, 'printer_event_code': 0, 'printer_exposure_time_ms': 22477.77734375, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
1050.500111 plugin-logger.py event printer values={'print_info_current_layer': 12, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 13, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- Late-print layers progress from 158 to 162 with the expected state cycling (STAGE10/11/12), then STOPPING and FINISH.
```
2332.480472 plugin-logger.py event printer values={'print_info_current_layer': 158, 'print_info_status': 3, 'print_info_total_layer': 162, 'printer_current_layer': 158, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2336.925347 plugin-logger.py event printer values={'print_info_current_layer': 158, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 159, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 10, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2344.721769 plugin-logger.py event printer values={'print_info_current_layer': 159, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 160, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2352.514100 plugin-logger.py event printer values={'print_info_current_layer': 160, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 161, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 11, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2360.246915 plugin-logger.py event printer values={'print_info_current_layer': 161, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 12, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2360.356358 plugin-logger.py event printer values={'print_info_current_layer': 161, 'print_info_status': 4, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2360.409573 plugin-logger.py event printer values={'print_info_current_layer': 161, 'print_info_status': 7, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2360.410552 plugin-logger.py event printer values={'print_info_current_layer': 162, 'print_info_status': 7, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 14, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2381.771591 plugin-logger.py event printer values={'print_info_current_layer': 162, 'print_info_status': 7, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 9, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
2381.999862 plugin-logger.py event printer values={'print_info_current_layer': 162, 'print_info_status': 9, 'print_info_total_layer': 162, 'printer_current_layer': 162, 'printer_event_code': 0, 'printer_exposure_time_ms': 2300.0, 'printer_heat_stage': 2, 'printer_options': 0, 'printer_pause_flags': 0, 'printer_skip_mask': 8, 'printer_state': 9, 'printer_uv_pwm': 255.0, 'printer_wait_reason': 0, 'uv_light_ctrl_mode': 514, 'uv_light_ctrl_state': 2, 'uv_light_pwm_base': 255, 'uv_light_pwm_scale': 255}
```

- The `/home` command is queued and injected via cmd_hook_printer_loop after STOPPING/FINISH; the breakpoint hits and the inject calls return.
```
2403.031908 CMD pending: home
2403.032769 INSTALL arm addr=0x7744c orig=0xebfe8451 write=0xe1200070 read=0xe1200070 ok=True
2403.032908 armed cmd_hook_printer_loop@0x7744c mode=arm
2403.033468 INSTALL arm addr=0x365ac orig=0xe92d4ff0 write=0xe1200070 read=0xe1200070 ok=True
2403.033575 armed cmd_hook_ui_loop@0x365ac mode=arm
2403.034053 INSTALL arm addr=0x89e14 orig=0xe3a00002 write=0xe1200070 read=0xe1200070 ok=True
2403.034182 armed cmd_hook_temp_loop@0x89e14 mode=arm
2403.034578 CMD waiting for breakpoint: home
2403.049036 [33mBREAKPOINT_ADDR=0x7744c[0m [32mprototype="void cmd_hook_printer_loop(void)"[0m
2403.049582 plugin-logger.py event cmd_hook_printer_loop payload={'name': 'cmd_hook_printer_loop', 'addr': 488524, 'pc': 488524}
2403.049835 REGS tid=781 pc=0x7744c lr=0xd3e38 sp=0x9cc8acf8 cpsr=0x60000010 r0=0x2710 r1=0x9cc8acd4 r2=0x3 r3=0x3
2403.067621 [35mHIT_CONFIRMED restore=1 setpc=1 step=1 rearm=1 tid=781 pc=0x7744c[0m
2403.067788 CMD home axis=0
2403.067950 CMD injecting addr=0x53548 thumb=False args=[0, 0, 0, 0]
2403.075539 CMD inject call addr=0x53548 thumb=False r0=0 r1=0 r2=0 r3=0 retval=0 (0) restore=ok wait_r=781 wait_status=1407
2403.075771 CMD injecting addr=0x53704 thumb=False args=[0, 0, 0, 0]
2403.089970 CMD inject call addr=0x53704 thumb=False r0=0 r1=0 r2=0 r3=0 retval=1 (1) restore=ok wait_r=781 wait_status=1407
```

- Repeated register dumps show the same thread parked at a different PC (likely a periodic debug dump from the tracer loop).
```
2406.042315 REGS tid=781 pc=0xb46a2468 lr=0x9cc8b800 sp=0x9cc8acd8 cpsr=0x80000010 r0=0x9cc8ace8 r1=0x0 r2=0x9cc8b3c4 r3=0x0
2456.040307 REGS tid=781 pc=0xb46a2468 lr=0x9cc8b800 sp=0x9cc8acd8 cpsr=0x80000010 r0=0x9cc8ace8 r1=0x0 r2=0x9cc8b3c4 r3=0x0
```

- Vat temperature remains stable and slowly rises; final sample is about 30.27 C.
```
2456.047695 plugin-logger.py event vat_temperature values={'tank_heat_control': 0, 'tank_heat_state': 0, 'tank_temp_c': 30.271310806274414, 'tank_temp_flag': 1, 'tank_temp_online': 1}
```

## Observations and learnings

- Total log span is about 1931.8 seconds (524.260693 -> 2456.047695), roughly 32.2 minutes, which matches a full 162-layer print with base layers and shorter normal exposures.
- State transitions are orderly and match the expected SLA pipeline: IDLE -> HOME -> CALIBRATE -> PROBE -> LEVEL -> STAGE1/2/3 loops -> STOPPING -> FINISH.
- Exposure and UV settings shift from long base-layer exposure (25000 ms, UV PWM 204) to shorter normal layers (around 2300 ms, UV PWM 255), indicating a base-layer phase followed by normal layers.
- Heat stage transitions (0 -> 1 -> 2) occur early and remain at stage 2 for the rest of the print; no heat error or oscillation is visible.
- No error strings appear in the log; the only notable post-print activity is the command hook breakpoint and repeated register dumps, which are consistent with normal tracer operations rather than printer faults.

## Potential follow-ups

- If the command hook is expected during the print (not after), adjust when the hook is armed; the log shows it hitting after STOPPING/FINISH.
- If exposure/power ramps should be consistent across base layers, verify the change from 25000 ms to 22477.777 ms and then to 2300 ms aligns with print profile settings.
