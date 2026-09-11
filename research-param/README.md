# Param Notes

The printer's time-lapse camera is controlled by a small settings file (machine_param_ref.bin). Three settings were killing the video:

1. 5 cm height limit. No recording at all for prints shorter than 5 cm.
2. 30 mm capture start. Camera didn't start shooting until the print grew 30 mm, so you'd only get a few frames.
3. 10-second reveal cap. Video always cut off mid-plate-lift, so you never saw the finished model.

The fix is a small Python script (patch-param.py). It turns off the two height limits, raises the reveal cap to 45 seconds, and recomputes the checksum so the firmware accepts it. Now you get a full time-lapse ending with the finished object in view.

# patch-param

A small, self-contained Python tool (no dependencies) that safely edits machine_param_ref.bin. The firmware only accepts the file if its checksum matches, so the script reimplements the printer's checksum algorithm (verified against the real file) and recomputes it on every edit.

Use it to flip the two height limits off and raise the recording cap, then copy the fixed file back to the printer.

# locations

- `/media/mmcblk0p1/machine_param_ref.bin`
- `/media/mmcblk0p2/frames/*` (post-print merged)
- `/media/mmcblk0p2/*.mp4`
- `/media/mmcblk0p2/log`

# changes

| JSON key | struct_off | BSS global | type | Role |
|---|---|---|---|---|
| `aic_tlp_switch` | 0x1F8 | `byte_39FC80` | byte | on/off (the `.ctb` "Enable" sets this too) |
| `aic_tlp_no_cap_pos` | 0x200 | `flt_39FC84` | float | print-start height gate (the 5 cm blocker, in `sub_4345C`) |
| `aic_tlp_start_cap_pos` | 0x208 | `flt_39FC88` | float | per-layer capture threshold (mm of build height) |
| `aic_tlp_interval_layers` | 0x210 | `dword_39FC8C` | u32 | capture cadence (every N layers) |
| `aic_tlp_snapshot_time` | 0x214 | `dword_39FC90` | u32 | HARD CAP (ms) on total retract/snapshot capture duration — at this age the snapshot path stops (`dword_2FA0CC=0`). Default 10000. |
| `aic_tlp_snapshot_int` | 0x218 | `dword_39FC94` | u32 | minimum spacing (ms) between snapshot frames. Default 70. (Camera's ~100 ms cadence is the real rate.) |
| `z_home_move_to_zero` | 0x21C | `byte_39FC98` | byte | home-sequence flag (see below) |
| `x_home_move_to_zero` | 0x21D | `byte_39FC99` | byte | home-sequence flag (see below) |
| `aic_enable` / `aic_capture_position` | (AI-camera block) | | | camera enable / capture pos |

```
aic_tlp_switch        = 1      (TLP enabled)
aic_tlp_no_cap_pos    = 0      (was 50)   boot/init height gate off
aic_tlp_start_cap_pos = 0      (was 30)   per-layer capture on for short prints
aic_tlp_interval_layers = 10   (default)  1 per-layer frame / 10 layers
aic_tlp_snapshot_time = 45000  (was 10000) THE FIX: retract capture 10s -> 45s
aic_tlp_snapshot_int  = 70     (default)  min snapshot spacing (ms)
z_home_move_to_zero   = 0      (stock)    keep — 1 broke homing
x_home_move_to_zero   = 1      (stock)
```

# json

```json
{
	"APP_first_use": "0",
	"EIOT_binded": "0",
	"EIOT_binded_username": "",
	"EIOT_reg_select": "0",
	"EIOT_test_server_mode": "0",
	"acceleration": "36",
	"after_n_layer_x_time_fast_mode": "2430",
	"after_n_layer_x_time_slow_mode": "4410",
	"agora_appid": "..",
	"agora_license": "..",
	"aic_capture_position": "100",
	"aic_enable": "1",
	"aic_tlp_switch": "1",             # 
	"aic_tlp_no_cap_pos": "50",        #
	"aic_tlp_start_cap_pos": "30",     #
	"aic_tlp_interval_layers": "10",
	"aic_tlp_snapshot_time": "10000",  #
	"aic_tlp_snapshot_int": "70",
	"z_home_move_to_zero": "0",
	"x_home_move_to_zero": "1",
	"z_i_hold": "9",
	"z_i_run": "18",
	"axis_params": [ .. ],
	"beep_frequency": "3000",
	"beep_volume": "100",
	"before_n_layer_x_time_fast_mode": "8420",
	"before_n_layer_x_time_slow_mode": "8420",
	"complete_ctrl_mode": "1",
	"complete_lift_distance": "100",
	"complete_lift_speed": "5",
	"deceleration": "36",
	"feed_in_speed": "2",
	"feed_out_speed": "2",
	"first_starting": "0",
	"first_use_test": "1",
	"i_change_interval": "1",
	"i_change_time": "1000",
	"i_hold": "12",
	"i_run": "25",
	"indicate_light_pwm": "255",
	"indicate_light_pwm_frequency": "200",
	"lock_screen_time": "210",
	"mainboard_fan_ctrl_mode": "2",
	"mainboard_fan_pwm": "255",
	"mainboard_fan_pwm_frequency": "200",
	"manual_control_speed": "5",
	"manual_x_control_speed": "40",
	"manual_x_max_zero": "-10",
	"pausing_ctrl_mode": "1",
	"pausing_lift_distance": "100",
	"pausing_lift_speed": "5",
	"print_estimate_reserved_time": "0",
	"print_file_check": "1",
	"probe_resin_flag": "0",
	"resinbowl_max_volume": "870",
	"resindetect_max_line": "25.5",
	"resindetect_min_line": "4",
	"rest_time_after_drop": "0",
	"rotate_param": [ .. ],
	"rtm_app_id": "",
	"sg_calibrate_cool_time": "5000",
	"sg_calibrate_disturbance_threshold": "50",
	"sg_calibrate_max_cool_time": "30000",
	"sg_calibrate_position": "220",
	"sg_calibrate_speed": "4.5",
	"sg_foregin_release_ths": "500",
	"sg_foregin_triger_ths": "3000",
	"sg_leveing_end_position": "-3",
	"sg_leveing_speed": "2",
	"sg_leveing_start_position": "3",
	"sg_leveing_step_distance": "0.05000000074505806",
	"sg_leveing_ths": "7750",
	"sg_level_zero": "0",
	"sg_release_max_count": "5",
	"sg_release_ths": "1000",
	"sg_resin_probe_c_enable": "1",
	"sg_resin_probe_c_max_ths": "55",
	"sg_resin_probe_c_min_ths": "-55",
	"sg_resin_probe_c_time": "10",
	"sg_resin_probe_end_position": "3",
	"sg_resin_probe_height": "244",
	"sg_resin_probe_speed": "2.5",
	"sg_resin_probe_start_position": "45",
	"sg_resin_probe_step_distance": "0.05000000074505806",
	"sg_resin_probe_ths": "55",
	"sg_resin_probe_volume_reserved": "100",
	"sg_resin_probe_width": "143",
	"sg_resin_zero": "-6096",
	"sg_zero": "-6339",
	"standby_gray_time": "5",
	"standby_time": "180",
	"stoping_ctrl_mode": "1",
	"stoping_lift_distance": "100",
	"stoping_lift_speed": "5",
	"tank_heat_mode_xz": "1",
	"tank_heat_once_time_limit": "35",
	"tank_heat_temperature_range": "1",
	"tank_heat_temperature_range2": "5",
	"tank_heat_wait_time": "1000",
	"tank_heat_x_gap_time": "3000",
	"tank_heat_x_position": "4.636737291354636e+18",
	"tank_heat_x_speed": "4.630826316843713e+18",
	"tank_heat_z_gap_time": "3000",
	"tank_heat_z_position_max": "4.62575976726292e+18",
	"tank_heat_z_position_min": "4.6173155179616e+18",
	"tank_heat_z_speed": "4.6173155179616e+18",
	"tank_pre_heat_max_time": "1440",
	"tank_pre_heat_temperature_target": "30",
	"tank_temperature_detection_state": "1",
	"tank_temperature_max_limit": "60",
	"tank_temperature_mod_10_20": "0",
	"tank_temperature_mod_1_10": "0",
	"tank_temperature_mod_20_": "0",
	"tank_temperature_target": "30",
	"temp_factory_max": "50",
	"temp_factory_min": "0",
	"temp_mode": "0",
	"temperature_detection_state": "1",
	"temperature_max_limit": "80",
	"uv_light_ctrl_mode": "2",
	"uv_light_fan_ctrl_mode": "2",
	"uv_light_fan_pwm": "255",
	"uv_light_fan_pwm_frequency": "200",
	"uv_light_pwm": "255",
	"uv_light_pwm_frequency": "200"
}
```
