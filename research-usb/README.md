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

# hub

To add additional USB devices, a hub was purchased that included 3x 2.0 ports and ethernet. The Dorewin hub (达而稳) was selected based on user reviews. Two critical issues resulted after connecting the hub: cold-boot enumeration failure, and missing kernel drivers.

The hub was not detected during a cold boot but would properly initialize when connected to an already booted system. The ethernet and multiple drives were correctly enumerated. However, the protocol drivers for ethernet did not claim the device which did not create the expected eth1 network device.

```bash
$ dmesg
==20180309==> hub_port_init 1 #0
Plug in USB Port1
usb 2-1: new high-speed USB device number 2 using Sstar-ehci-1
usb 2-1: New USB device found, idVendor=214b, idProduct=7250
usb 2-1: New USB device strings: Mfr=0, Product=1, SerialNumber=0
usb 2-1: Product: USB2.0 HUB # <--
hub 2-1:1.0: USB hub found
hub 2-1:1.0: 4 ports detected

==20180309==> hub_port_init 1 #0
usb 2-1.1: new high-speed USB device number 3 using Sstar-ehci-1
usb 2-1.1: New USB device found, idVendor=048d, idProduct=1234
usb 2-1.1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
usb 2-1.1: Product: Disk 2.0 # <--
usb 2-1.1: Manufacturer: USB
usb 2-1.1: SerialNumber: 7973261286513572221
usb-storage 2-1.1:1.0: USB Mass Storage device detected
cma: cma_alloc(cma c044d0f8, count 1, align 0)
cma: cma_alloc(): returned c71e5440
scsi host0: usb-storage 2-1.1:1.0

==20180309==> hub_port_init 3 #0
usb 2-1.3: new high-speed USB device number 4 using Sstar-ehci-1
usb 2-1.3: New USB device found, idVendor=1609, idProduct=3a04
usb 2-1.3: New USB device strings: Mfr=1, Product=2, SerialNumber=3
usb 2-1.3: Product: USB Disk # <--
usb 2-1.3: Manufacturer: FLash
usb 2-1.3: SerialNumber: 3727187E8353576917429
usb-storage 2-1.3:1.0: USB Mass Storage device detected
usb-storage 2-1.3:1.0: Quirks match for vid 1609 pid 3a04: 8
usb-storage 2-1.3:1.0: This device (1609,3a04,0000 S 06 P 50) has unneeded SubClass and Protocol entries in unusual_devs.h (kernel 4.9.84)
   Please send a copy of this message to <linux-usb@vger.kernel.org> and <usb-storage@lists.one-eyed-alien.net>
scsi host1: usb-storage 2-1.3:1.0

==20180309==> hub_port_init 4 #0
usb 2-1.4: new high-speed USB device number 5 using Sstar-ehci-1
usb 2-1.4: New USB device found, idVendor=1a86, idProduct=e396
usb 2-1.4: New USB device strings: Mfr=1, Product=2, SerialNumber=3
usb 2-1.4: Product: USB 10/100 LAN # <--
usb 2-1.4: Manufacturer: wch.cn
usb 2-1.4: SerialNumber: 3CAB72BEB9CB

scsi 0:0:0:0: Direct-Access     VendorCo ProductCode      2.00 PQ: 0 ANSI: 4
sd 0:0:0:0: [sda] 122880000 512-byte logical blocks: (62.9 GB/58.6 GiB)
sd 0:0:0:0: [sda] Write Protect is off
sd 0:0:0:0: [sda] Mode Sense: 03 00 00 00
sd 0:0:0:0: [sda] No Caching mode page found
sd 0:0:0:0: [sda] Assuming drive cache: write through
 sda: sda1
sd 0:0:0:0: [sda] Attached SCSI removable disk
scsi 1:0:0:0: Direct-Access     EAGET    H500             0000 PQ: 0 ANSI: 2
sd 1:0:0:0: [sdb] 7864320 512-byte logical blocks: (4.03 GB/3.75 GiB)
sd 1:0:0:0: [sdb] Write Protect is off
sd 1:0:0:0: [sdb] Mode Sense: 0b 00 00 08
FAT-fs (sda): utf8 is not a recommended IO charset for FAT filesystems, filesystem will be case sensitive!
sd 1:0:0:0: [sdb] No Caching mode page found
sd 1:0:0:0: [sdb] Assuming drive cache: write through
 sdb: sdb1
sd 1:0:0:0: [sdb] Attached SCSI removable disk

[EXFAT] trying to mount...
FAT-fs (sda1): utf8 is not a recommended IO charset for FAT filesystems, filesystem will be case sensitive!
cma: cma_alloc(cma c044d0f8, count 1, align 0)
cma: cma_alloc(): returned c71e5460
FAT-fs (sdb): utf8 is not a recommended IO charset for FAT filesystems, filesystem will be case sensitive!
[EXFAT] trying to mount...
FAT-fs (sdb1): utf8 is not a recommended IO charset for FAT filesystems, filesystem will be case sensitive!
FAT-fs (sdb1): Volume was not properly unmounted. Some data may be corrupt. Please run fsck.

UBIFS (ubi0:0): completing deferred recovery
UBIFS (ubi0:0): deferred recovery completed
UBIFS (ubi0:0): background thread "ubifs_bgt0_0" started, PID 1614
```

```bash
$ lsusb
Bus 002 Device 002: ID 214b:7250
Bus 001 Device 001: ID 1d6b:0002
Bus 001 Device 004: ID a108:2240
Bus 001 Device 002: ID 1a86:8091
Bus 002 Device 004: ID 1609:3a04
Bus 002 Device 003: ID 048d:1234
Bus 002 Device 001: ID 1d6b:0002
Bus 001 Device 003: ID 0bda:c811
Bus 002 Device 005: ID 1a86:e396
```

```bash
$ ls /media/ -l
total 296
drwxr-xr-x    5 root     root          4096 Jan  1  1970 mmcblk0p1
drwxr-xr-x    2 root     root        131072 Jan  1  1970 mmcblk0p2
drwxr-xr-x    2 root     root        131072 Jan  1  1970 mmcblk0p3
drwxr-xr-x    3 root     root         32768 Jan  1  1970 sda1
drwxr-xr-x    6 root     root          4096 Dec 26 04:10 sdb1
```

```bash
$ uname -r
4.9.84
```

```bash
$ ls /lib/modules/4.9.84/
8188fu.ko             cs1237.ko             gsl_point_id.ko       mi_disp.ko            pl2303.ko             usbhid.ko
8192fu.ko             edt-ft5x06.ko         hr2046.ko             mi_gfx.ko             r8152.ko              usbnet.ko
8821cu.ko             ehci-hcd.ko           jbd2.ko               mi_panel.ko           r8188eu.ko            usbserial.ko
aic8800_fdrv.ko       ext4.ko               kdrv_emac.ko          mi_sys.ko             rtl8812au.ko          uvcvideo.ko
aic_load_fw.ko        fbdev.ko              libphy.ko             mii.ko                sspi.ko               videobuf2-core.ko
ax88179_178a.ko       fixed_phy.ko          lockd.ko              nfs.ko                sstar_100_phy.ko      videobuf2-memops.ko
cdc-acm.ko            fuse.ko               mac80211.ko           nfsv2.ko              sunrpc.ko             videobuf2-v4l2.ko
cfg80211.ko           goodix.ko             mbcache.ko            nfsv3.ko              uhid.ko               videobuf2-vmalloc.ko
ch341.ko              gpio-i2c.ko           mdrv_crypto.ko        nls_utf8.ko           usb-common.ko         wrt_gslX680.ko
cifs.ko               gpio-spi.ko           mhal.ko               ntfs.ko               usb-storage.ko
cryptodev.ko          grace.ko              mi_common.ko          of_mdio.ko            usbcore.ko
```

```bash
$ lsmod
Module                  Size  Used by    Tainted: P
8821cu               1577879  0
cs1237                  4942  0
gpio_spi                3729  2
gpio_i2c                5328  0
sspi                    4069  0
usbnet                 14528  0
uvcvideo               54067  2
videobuf2_vmalloc       4068  1 uvcvideo
videobuf2_memops        1330  1 videobuf2_vmalloc
videobuf2_v4l2          8390  1 uvcvideo
videobuf2_core         17698  2 uvcvideo,videobuf2_v4l2
mac80211              241543  0
cfg80211              161125  2 8821cu,mac80211
kdrv_emac              31324  0
of_mdio                 5815  2 kdrv_emac
sstar_100_phy           1890  1
fixed_phy               2661  1 of_mdio
libphy                 25305  4 kdrv_emac,of_mdio,sstar_100_phy,fixed_phy
mii                     2963  1 usbnet
cdc_acm                13348  0
pl2303                  6639  0
ch341                   4199  0
usbserial              16457  2 pl2303,ch341
uhid                    4991  0
usbhid                 25963  0
usb_storage            35659  2
ehci_hcd               37790  0
usbcore               129629 10 8821cu,usbnet,uvcvideo,cdc_acm,pl2303,ch341,usbserial,usbhid,usb_storage,ehci_hcd
usb_common              2895  1 usbcore
cryptodev              26803  0
mdrv_crypto            21122  1
fuse                   58432  0
ntfs                   71449  0
ext4                  256787  0
jbd2                   46570  1 ext4
mbcache                 5168  1 ext4
nfsv3                  14866  0
nfsv2                  10548  0
nfs                    92759  2 nfsv3,nfsv2
lockd                  44484  3 nfsv3,nfsv2,nfs
sunrpc                146655  4 nfsv3,nfsv2,nfs,lockd
grace                   2219  1 lockd
nls_utf8                1380  5
cifs                  164159  0
edt_ft5x06              7987  0
hr2046                  3059  0
wrt_gslX680            43863  0
gsl_point_id           25167  1 wrt_gslX680
goodix                  8156  0
fbdev                  29720  1
mi_panel               23719  0
mi_disp                98898  0
mi_gfx                 16727  1 mi_disp
mi_sys                848222  4 fbdev,mi_panel,mi_disp,mi_gfx
mi_common               5938  7 fbdev,mi_panel,mi_disp,mi_gfx,mi_sys
mhal                  474764  5 fbdev,mi_panel,mi_disp,mi_gfx,mi_sys
```

## kernel recovery

```bash
$ cat /proc/mtd
dev:    size   erasesize  name
mtd10: 00500000 00020000 "KERNEL"
```

```bash
$ dd if=/dev/mtd10ro of=mtd10ro.bin bs=1M
5+0 records in
5+0 records out
```

```bash
$ ls -l
total 5120
-rwxr-xr-x    1 root     root       5242880 Dec 26 04:17 mtd10ro.bin
```

```bash
$ hexdump -C mtd10ro.bin  | head
00000000  27 05 19 56 6d 86 1c 79  69 26 d3 53 00 1f c3 48  |'..Vm..yi&.S...H|
00000010  20 00 80 00 20 00 80 00  d8 74 5d 4d 05 02 02 03  | ... ....t]M....|
00000020  4d 56 58 34 23 23 49 32  4d 23 67 35 62 61 61 34  |MVX4##I2M#g5baa4|
00000030  61 38 63 34 4b 4c 5f 4c  58 34 30 39 23 23 5b 42  |a8c4KL_LX409##[B|
00000040  fd 37 7a 58 5a 00 00 04  e6 d6 b4 46 02 00 21 01  |.7zXZ......F..!.|
00000050  16 00 00 00 74 2f e5 a3  e1 94 7a ef ff 5d 00 00  |....t/....z..]..|
00000060  a4 ee ca 68 83 8f fa 07  6c 5c a4 c2 ee c0 35 2e  |...h....l\....5.|
00000070  7f 82 15 a3 fa a7 ce db  d0 41 64 0e 54 85 62 55  |.........Ad.T.bU|
00000080  03 f2 54 60 65 45 eb d8  12 b0 bc f2 64 a6 78 ad  |..T`eE......d.x.|
00000090  ce fc ac 1c 1d 24 f5 eb  b2 04 01 51 31 ac 6e f6  |.....$.....Q1.n.|
```

```bash
$ wget "https://www.kernel.org/pub/linux/kernel/v4.x/linux-4.9.84.tar.gz" -O "linux-4.9.84.tar.gz"
```

```bash
$ strings /usr/lib/modules/4.9.84/usbnet.ko | grep vermagic
vermagic=4.9.84 SMP preempt mod_unload ARMv7 thumb2 p2v8
```

```bash
$ ./scripts/extract-ikconfig ../mtd10ro.bin
extract-ikconfig: Cannot find kernel config.
```

Unsuccessful:

```bash
$ apt-get install -y bc
$ make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- multi_v7_defconfig
$ ./scripts/config --file .config --enable CONFIG_SMP
$ ./scripts/config --file .config --enable CONFIG_PREEMPT
$ ./scripts/config --file .config --enable CONFIG_THUMB2_KERNEL
$ ./scripts/config --file .config --enable CONFIG_MODULES
$ ./scripts/config --file .config --enable CONFIG_MODULE_UNLOAD
$ ./scripts/config --file .config --enable CONFIG_USB_SUPPORT
$ ./scripts/config --file .config --enable CONFIG_USB
$ ./scripts/config --file .config --enable CONFIG_USB_EHCI_HCD
$ ./scripts/config --file .config --module CONFIG_USB_USBNET
$ ./scripts/config --file .config --module CONFIG_USB_NET_CDCETHER
$ ./scripts/config --file .config --module CONFIG_USB_NET_CDC_NCM
$ ./scripts/config --file .config --module CONFIG_USB_NET_RNDIS_HOST
$ ./scripts/config --file .config --module CONFIG_USB_NET_CDC_SUBSET
$ make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- olddefconfig
$ make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- modules_prepare
$ make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- M=drivers/net/usb/ modules
$ ls drivers/net/usb/*.ko
```
