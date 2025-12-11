# Extract Notes

The ChituUpgrade.bin file contains U-Boot instructions for partition extraction. The end of each partition contains a CRC32 checksum.

```bash
$ head ChituUpgrade.bin
# <- this is for comment / total file size must be less than 4KB
#upgrade_bin_version=V1.2.9
#upgrade_force=1

# File Partition: cis.es
```

```bash
$ grep --text Partition ChituUpgrade.bin
# File Partition: cis.es
# File Partition: set_partition.es
# File Partition: ipl.es
# File Partition: ipl_cust.es
# File Partition: uboot.es
# File Partition: logo.es
# File Partition: kernel.es
# File Partition: rootfs.es
# File Partition: miservice.es
# File Partition: customer.es
# File Partition: appconfigs.es
# File Partition: parameter.es
# File Partition: set_config
```

```plaintext
# File Partition: rootfs.es
ubi part UBI
fatload usb 0 0x21000000 $(UpgradeImage) 0x1ff8008 0x260000
# fatload <interface> <dev[:part]> <addr> <filename> [bytesoffset] [bytes]
crccheck 0x21000000 0x1ff8008
# crccheck <addr> <length>
ubi write 0x21000000 rootfs 0x1FF8000
```

Read-only UBI extraction is accomplished with `ubireader_extract_files`.

```bash
$ apt install u-boot-tools xz-utils openssl
```

```bash
$ python3 -m pip install ubi_reader --break-system-packages
```

System files are stored in the rootfs.es partition.

```bash
$ ubireader_extract_files partition_00260000_01FF8008.bin
```

```bash
$ for i in partition_*.bin ; do ubireader_extract_files -o "${i}_fs" $i ; done
```

Chitu restarts `telnetd` without any arguments at launch.

```bash
$ find ubifs-root/ -name shadow -ls
117317928169794181      4 -rw-r--r--   1 root     root          190 Nov  6  2024 ubifs-root/etc/shadow
```

```bash
$ head ubifs-root/etc/shadow
root:$5$LWZE1Y5U$kQvhpcTMvhmcZdVZGPa2.yuOeUmtstssQBWWQRUDJ02:::::::
```

# --shadow

Rather than building a new UBI partition, a known hash can be patched directly in the binary. The salt is specified to keep the new hash length consistent.

```bash
$ openssl passwd -5 -salt LWZE1Y5U 'pass'
$5$LWZE1Y5U$Bp6aYr6/hntJ0ycLZY.IZGV5TxdVyIrBH98.stRpR.8
```

# --startup

To launch programs at startup, the `/etc/init.d/S50telnet` file is repurposed to fork and wait for a USB device with a `startup.sh` file. FAT file systems default to executable permissions. This patch required more effort to disable the LZO compression or else the file would be unreadable after installation.

| Field          | Offset | Size | Description                            | Example Bytes / Notes |
| -------------- | ------ | ---- | -------------------------------------- | --------------------- |
| magic          | 0x00   | 4    | UBIFS magic `0x06101831`               | `31 18 10 06`         |
| crc            | 0x04   | 4    | CRC32 over `[node_start+8 : node_end]` | `03 F2 53 B5`         |
| sqnum          | 0x08   | 8    | Sequence number                        | `2F 00 00 00 …`       |
| len            | 0x10   | 4    | Node total length                      | `A2 01 00 00` (418)   |
| node_type      | 0x14   | 1    | `1 = UBIFS_DATA_NODE`                  | `01`                  |
| group_type     | 0x15   | 1    | Reserved                               | `00`                  |
| padding        | 0x16   | 2    | Reserved                               | `00 00`               |
| key            | 0x18   | 16   | UBIFS key                              | `4F 00 00 … 20`       |
| size           | 0x28   | 4    | Uncompressed data size                 | `66 02 00 00` (614)   |
| compr_type     | 0x2C   | 2    | Compression type (`1=LZO`, `0=NONE`)   | `01 00 → 00 00`       |
| compr_size/pad | 0x2E   | 2    | Unused / padding                       | `00 00`               |

```bash
#!/bin/sh
[ "$1" = "start" ] || exit 0
until /media/sd?1/startup.sh ; do sleep 1 ; done &
exit 0
```

The replacement S50telnet init script polls for USB devices mounted as sd?1 (eg. sda1 sdb1) with the `/startup.sh` file.

# install

The python helper tool can extract, patch, and rebuild the firmware file.

```bash
$ ./tool.py ChituUpgrade.bin --extract
cis.es: offset=0x4000 len=0x5608 crc32_full=06f8b203 payload_len=0x5600 tail_hex=ab98586c calc=ab98586c match=True
cis.es: offset=0xA000 len=0x208 crc32_full=7bd4ba1c payload_len=0x200 tail_hex=a8682bd4 calc=a8682bd4 match=True
ipl.es: offset=0xB000 len=0x5BE8 crc32_full=9d248907 payload_len=0x5BE0 tail_hex=41217aa3 calc=41217aa3 match=True
ipl_cust.es: offset=0x11000 len=0x5368 crc32_full=2a34916d payload_len=0x5360 tail_hex=9e64ef7b calc=9e64ef7b match=True
uboot.es: offset=0x17000 len=0x3D084 crc32_full=04946835 payload_len=0x3D07C tail_hex=d5a6f527 calc=d5a6f527 match=True
logo.es: offset=0x55000 len=0xDF04 crc32_full=2e3500c4 payload_len=0xDEFC tail_hex=6e833820 calc=6e833820 match=True
kernel.es: offset=0x63000 len=0x1FC1A4 crc32_full=0d4809e6 payload_len=0x1FC19C tail_hex=3175ad12 calc=3175ad12 match=True
rootfs.es: offset=0x260000 len=0x1FF8008 crc32_full=d579b32f payload_len=0x1FF8000 tail_hex=0c0bcd58 calc=0c0bcd58 match=True
miservice.es: offset=0x2259000 len=0xA6A008 crc32_full=88c2dfaf payload_len=0xA6A000 tail_hex=b4ae0b82 calc=b4ae0b82 match=True
customer.es: offset=0x2CC4000 len=0x1C56008 crc32_full=8ce1b1ed payload_len=0x1C56000 tail_hex=d4259ea9 calc=d4259ea9 match=True
appconfigs.es: offset=0x491B000 len=0x193008 crc32_full=e7180615 payload_len=0x193000 tail_hex=8c48d6af calc=8c48d6af match=True
parameter.es: offset=0x4AAF000 len=0x193008 crc32_full=70e94dab payload_len=0x193000 tail_hex=86086783 calc=86086783 match=True
```

```bash
$ du -h partition*.bin
24K     partition_00004000_00005608.bin
4.0K    partition_0000A000_00000208.bin
24K     partition_0000B000_00005BE8.bin
24K     partition_00011000_00005368.bin
248K    partition_00017000_0003D084.bin
56K     partition_00055000_0000DF04.bin
2.0M    partition_00063000_001FC1A4.bin
32M     partition_00260000_01FF8008.bin
11M     partition_02259000_00A6A008.bin
29M     partition_02CC4000_01C56008.bin
1.6M    partition_0491B000_00193008.bin
1.6M    partition_04AAF000_00193008.bin
```

```bash
$ ./tool.py ChituUpgrade.bin --shadow --build
patched hash in partition_00260000_01FF8008.bin
rebuilt ASCII CRC for partition_00004000_00005608.bin: ab98586c
rebuilt ASCII CRC for partition_0000A000_00000208.bin: a8682bd4
rebuilt ASCII CRC for partition_0000B000_00005BE8.bin: 41217aa3
rebuilt ASCII CRC for partition_00011000_00005368.bin: 9e64ef7b
rebuilt ASCII CRC for partition_00017000_0003D084.bin: d5a6f527
rebuilt ASCII CRC for partition_00055000_0000DF04.bin: 6e833820
rebuilt ASCII CRC for partition_00063000_001FC1A4.bin: 3175ad12
rebuilt ASCII CRC for partition_00260000_01FF8008.bin: 406d130f
rebuilt ASCII CRC for partition_02259000_00A6A008.bin: b4ae0b82
rebuilt ASCII CRC for partition_02CC4000_01C56008.bin: d4259ea9
rebuilt ASCII CRC for partition_0491B000_00193008.bin: 8c48d6af
rebuilt ASCII CRC for partition_04AAF000_00193008.bin: 86086783
wrote ChituUpgrade.patched.bin
```

```bash
$ md5sum ChituUpgrade.*bin
4b1f203bcbbfa4ee3c1f1e108bb0095d  ChituUpgrade.bin
0624f75a37c247f394930fa6528543fe  ChituUpgrade.patched.bin
```

```bash
./tool.py ChituUpgrade.bin --extract --shadow --startup --build
cis.es: offset=0x4000 len=0x5608 crc32_full=06f8b203 payload_len=0x5600 tail_hex=ab98586c calc=ab98586c match=True
cis.es: offset=0xA000 len=0x208 crc32_full=7bd4ba1c payload_len=0x200 tail_hex=a8682bd4 calc=a8682bd4 match=True
ipl.es: offset=0xB000 len=0x5BE8 crc32_full=9d248907 payload_len=0x5BE0 tail_hex=41217aa3 calc=41217aa3 match=True
ipl_cust.es: offset=0x11000 len=0x5368 crc32_full=2a34916d payload_len=0x5360 tail_hex=9e64ef7b calc=9e64ef7b match=True
uboot.es: offset=0x17000 len=0x3D084 crc32_full=04946835 payload_len=0x3D07C tail_hex=d5a6f527 calc=d5a6f527 match=True
logo.es: offset=0x55000 len=0xDF04 crc32_full=2e3500c4 payload_len=0xDEFC tail_hex=6e833820 calc=6e833820 match=True
kernel.es: offset=0x63000 len=0x1FC1A4 crc32_full=0d4809e6 payload_len=0x1FC19C tail_hex=3175ad12 calc=3175ad12 match=True
rootfs.es: offset=0x260000 len=0x1FF8008 crc32_full=d579b32f payload_len=0x1FF8000 tail_hex=0c0bcd58 calc=0c0bcd58 match=True
miservice.es: offset=0x2259000 len=0xA6A008 crc32_full=88c2dfaf payload_len=0xA6A000 tail_hex=b4ae0b82 calc=b4ae0b82 match=True
customer.es: offset=0x2CC4000 len=0x1C56008 crc32_full=8ce1b1ed payload_len=0x1C56000 tail_hex=d4259ea9 calc=d4259ea9 match=True
appconfigs.es: offset=0x491B000 len=0x193008 crc32_full=e7180615 payload_len=0x193000 tail_hex=8c48d6af calc=8c48d6af match=True
parameter.es: offset=0x4AAF000 len=0x193008 crc32_full=70e94dab payload_len=0x193000 tail_hex=86086783 calc=86086783 match=True
patched shadow partition_00260000_01FF8008.bin
patched startup partition_00260000_01FF8008.bin
rebuilt ASCII CRC for partition_00004000_00005608.bin: ab98586c
rebuilt ASCII CRC for partition_0000A000_00000208.bin: a8682bd4
rebuilt ASCII CRC for partition_0000B000_00005BE8.bin: 41217aa3
rebuilt ASCII CRC for partition_00011000_00005368.bin: 9e64ef7b
rebuilt ASCII CRC for partition_00017000_0003D084.bin: d5a6f527
rebuilt ASCII CRC for partition_00055000_0000DF04.bin: 6e833820
rebuilt ASCII CRC for partition_00063000_001FC1A4.bin: 3175ad12
rebuilt ASCII CRC for partition_00260000_01FF8008.bin: 13278f64
rebuilt ASCII CRC for partition_02259000_00A6A008.bin: b4ae0b82
rebuilt ASCII CRC for partition_02CC4000_01C56008.bin: d4259ea9
rebuilt ASCII CRC for partition_0491B000_00193008.bin: 8c48d6af
rebuilt ASCII CRC for partition_04AAF000_00193008.bin: 86086783
wrote ChituUpgrade.patched.bin
```

Copy the modified `ChituUpgrade.patched.bin` file to a USB drive as `ChituUpgrade.bin` and turn ON the printer. The printer will automatically patch the files and rename the firmware to `ChituUpgrade00.bin`. Afterwards, telnetd will accept the new password `pass` for the root user.

```bash
$ telnet 192.168.1.2
Trying 192.168.1.2...
Connected to 192.168.1.2.
Escape character is '^]'.

(none) login: root
Password:
~: df -h
Filesystem                Size      Used Available Use% Mounted on
ubi:rootfs               37.7M     28.9M      8.8M  77% /
devtmpfs                 54.6M         0     54.6M   0% /dev
tmpfs                    56.6M         0     56.6M   0% /dev/shm
tmpfs                    56.6M      8.0K     56.6M   0% /tmp
tmpfs                    56.6M      4.0K     56.6M   0% /run
tmpfs                    56.6M         0     56.6M   0% /media
ubi0:miservice            9.4M      8.5M    944.0K  90% /config
ubi0:customer            32.4M     25.4M      6.9M  79% /customer
ubi0:appconfigs           2.0M     24.0K      2.0M   1% /appconfigs
ubi0:parameter            2.0M     24.0K      2.0M   1% /parameter
/dev/mmcblk0p2          510.0M      3.1M    506.9M   1% /media/mmcblk0p2
/dev/mmcblk0p3            6.1G      8.3M      6.1G   0% /media/mmcblk0p3
/dev/mmcblk0p1          511.0M    130.7M    380.3M  26% /media/mmcblk0p1
~: uname -a
Linux (none) 4.9.84 #18 SMP PREEMPT Fri Sep 26 11:53:39 CST 2025 armv7l GNU/Linux
~: free -h
              total        used        free      shared  buff/cache   available
Mem:         116.3M       36.6M       54.5M       12.0K       25.2M       74.4M
Swap:             0           0           0
~:
```
