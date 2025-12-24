# Compile Notes

The firmware came with telnetd and busybox but samba and other files were missing.

```bash
$ cat /proc/cpuinfo
processor       : 0
model name      : ARMv7 Processor rev 5 (v7l)
BogoMIPS        : 11.93
Features        : half thumb fastmult vfp edsp thumbee neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xc07
CPU revision    : 5

processor       : 1
model name      : ARMv7 Processor rev 5 (v7l)
BogoMIPS        : 11.93
Features        : half thumb fastmult vfp edsp thumbee neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xc07
CPU revision    : 5

Hardware        : SStar Soc (Flattened Device Tree)
Revision        : 0000
Serial          : 0000000000000000
```

```bash
$ echo $PATH
/bin:/sbin:/usr/bin:/usr/sbin:/config
```

# build

See the [build.sh](build.sh) script which outputs a zip file containing python3, nano, samba4, etc.

```bash
$ docker run --rm -it -v "$(pwd)":/build -w /build debian:buster
```

```bash
$ bash build.sh
```

Copy out.zip to the USB drive (eg., /media/sda1/system/) and unzip (eg., unzip -o out.zip). A few exports are necessary for the programs to locate libraries. The exports can be added to the /etc/profile file used by `ash`.

```bash
$ export PATH=$PATH:/media/sda1/system/usr/local/bin:/media/sda1/system/usr/local/sbin
$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/media/sda1/system/usr/local/lib
$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/media/sda1/system/usr/local/lib/samba
$ export TERM=xterm-256color
$ export TERMINFO=/media/sda1/system/usr/local/share/terminfo
```
