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

See the [build.sh](build.sh) script which outputs a zip file containing python3, nano, samba4, avahi, and screen. All have been tested except for avahi as nmbd was sufficient advertisement.

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

# archives

Everything below was performed in a debian:13 trixie docker container.

```bash
$ dpkg --add-architecture armhf
```

```bash
TARGET=arm-linux-gnueabihf
CC="$TARGET-gcc"
CXX="$TARGET-g++"
```

## dropbear

```bash
$ wget https://matt.ucc.asn.au/dropbear/releases/dropbear-2025.88.tar.bz2 && \
  tar xjf dropbear-2025.88.tar.bz2
```

The device path is `/bin:/sbin:/usr/bin:/usr/sbin:/config` which means dropbear cannot find dbclient or sftp-server, yet. The definitions are located in the `localoptions.h` file.

Edit localoptions.h:

```c
#define DROPBEAR_PATH_SSH_PROGRAM "/config/dbclient"
#define SFTPSERVER_PATH "/config/sftp-server"
#define DEFAULT_PATH "/bin:/sbin:/usr/bin:/usr/sbin:/config"
#define DEFAULT_ROOT_PATH "/usr/sbin:/usr/bin:/sbin:/bin:/config"
```

Build.

```bash
$ ./configure \
  --host=arm-linux-gnueabihf CC=arm-linux-gnueabihf-gcc CFLAGS="-Os" LDFLAGS="-static" \
  --disable-zlib --disable-pam --disable-lastlog --disable-utmp --disable-wtmp --enable-static
```

```bash
$ make -j"$(nproc)" PROGRAMS="dropbear dbclient dropbearkey scp" MULTI=1
```

Like busybox, dropbearmulti determines the tool by execution filename.

```bash
$ ln -s dropbearmulti dropbear
$ ln -s dropbearmulti dbclient
$ ln -s dropbearmulti dropbearkey
$ ln -s dropbearmulti scp
```

Run.

```bash
$ ./dropbearkey -t rsa -f /path/to/dropbear_rsa_host_key
```

```bash
$ ./dropbear -r /path/to/dropbear_rsa_host_key -p 0.0.0.0:22 -E
```

## bftpd

```bash
$ wget https://downloads.sourceforge.net/project/bftpd/bftpd/bftpd-6.3/bftpd-6.3.tar.gz && \
  tar xf bftpd-6.3.tar.gz
```

```bash
$ CC="arm-linux-gnueabihf-gcc -static" make
```

Example runtime config file (eg. bftpd.conf):

```conf
global {
  DENY_LOGIN="no"
  PATH_FTPUSERS=""
  ROOTDIR="/"
  AUTO_CHDIR="/"
  DO_CHROOT="no"
  RATIO="none"
}

user ftp {
  ANONYMOUS_USER="yes"
  ROOTDIR="/"
}

user anonymous {
  ALIAS="ftp"
}
```

Run.

```bash
$ ./bftpd -h
Usage: ./bftpd [-h] [-v] [-i|-d|-D] [-c <filename>|-n]
-h print this help
-v display version number
-i (default) run from inetd
-d daemon mode: fork() and run in TCP listen mode
-D run in TCP listen mode, but don't pre-fork()
-c read the config file named "filename" instead of /etc/bftpd.conf
-n no config file, use defaults
```

```bash
$ ./bftpd -d -c /path/to/bftpd.conf
```

## fsck.fat

TODO:
