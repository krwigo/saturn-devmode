# USB Notes

With the `S50telnet` service repurposed to execute `/media/sd?1/startup.sh`, this directory is about handling startup and launching programs.

# layout

The layout is not specific and depends entirely on how your startup.sh is written. All of these were tested using the 4GB yellow USB device provided by Elegoo. I purchased a 64GB short USB drive to permanently install in the printer to store the compiled programs and video recordings.

```plaintext
/media/sda1/dropbear/dropbearmulti
/media/sda1/dropbear/dropbear_rsa_host_key
/media/sda1/dropbear/dropbear_rsa_host_key.pub
/media/sda1/bftpd/bftpd
/media/sda1/bftpd/bftpd.conf
/media/sda1/startup.log
/media/sda1/startup.sh
```

# startup.sh

The script **must** exit 0 or the script will be considered as a failed service causing it to continuously run. Using `pidof` to detect existing daemons is **recommended** as the device has limited hardware resources which could impact the printing process.

```sh
#!/bin/sh
# eg. /media/sda1/startup.sh
script_path=$0

# eg. /media/sda1
script_dir=$(dirname "$script_path")

# bftpd
if ! pidof bftpd >/dev/null 2>&1; then
	$script_dir/bftpd/bftpd -d -c $script_dir/bftpd/bftpd2.conf
fi

# dropbear
if ! pidof dropbear >/dev/null 2>&1; then
	ln -s $script_dir/dropbear/dropbearmulti /config/dropbear
	ln -s $script_dir/dropbear/dropbearmulti /config/dbclient
	ln -s $script_dir/dropbear/dropbearmulti /config/dropbearkey
	ln -s $script_dir/dropbear/dropbearmulti /config/scp
	/config/dropbearkey -t rsa -f $script_dir/dropbear/dropbear_rsa_host_key
	/config/dropbear -r $script_dir/dropbear/dropbear_rsa_host_key -p 0.0.0.0:22 -E
fi

exit 0
```

Afterwards, the processes automatically launch.

```plaintext
/: ps -ef f
PID   USER     COMMAND
  711 root     /customer/resources/chitu
  777 root     telnetd
  848 root     /sbin/getty -L console 0 vt100
  950 root     /media/sda1/bftpd/bftpd -d -c /media/sda1/bftpd/bftpd2.conf
  957 root     /config/dropbear -r /media/sda1/dropbear/dropbear_rsa_host_key -p 0.0.0.0:22 -E
 1010 root     wpa_supplicant -D nl80211,wext -C /var/run/wpa_supplicant -B -i wlan0
 1110 root     udhcpc -i wlan0 -b -p /tmp/wlan0_udhcpc.pid -s /config/default.script
 2394 root     /media/sda1/bftpd/bftpd -d -c /media/sda1/bftpd/bftpd2.conf
```
