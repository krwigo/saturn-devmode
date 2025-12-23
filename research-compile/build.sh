#!/bin/bash
# use debian buster as it matches libc versions with the arm device.
# docker run --rm -it -v "$(pwd)":/build -w /build debian:buster

USE_PROXY=${USE_PROXY:-1}
USE_MIRROR=${USE_MIRROR:-1}

WORKDIR="/build"

# enable proxy support (cache, forwarding).
# <proxy>
if [ -n "$USE_PROXY" ]; then
  # export HTTP_PROXY="http://192.168.2.45:8053"
  export HTTP_PROXY="http://192.168.2.2:8040"
  export HTTP_PROXY="$HTTP_PROXY" HTTPS_PROXY="$HTTP_PROXY" http_proxy="$HTTP_PROXY" https_proxy="$HTTP_PROXY"

  cat << 'EOF' > "/etc/apt/apt.conf.d/01proxy"
Acquire::http { Proxy "http://192.168.2.45:8053"; No-Cache "false"; No-Store "false"; Max-Age "31536000"; };
Acquire::https { Proxy "http://192.168.2.45:8053"; No-Cache "false"; No-Store "false"; Max-Age "31536000"; };
Acquire::Check-Valid-Until "false";
EOF
fi
# </proxy>

# debian buster is out of service but available through the archives.
cat << 'EOF' > "/etc/apt/sources.list"
deb http://archive.debian.org/debian buster main contrib non-free
deb http://archive.debian.org/debian buster-updates main contrib non-free
deb http://archive.debian.org/debian-security buster/updates main contrib non-free
EOF

# enable mirror support (debian-elts).
# <mirror>
if [ -n "$USE_MIRROR" ]; then
  if ! command -v wget; then
    apt -qq update
    apt -qq install -y wget
  fi

  if [ ! -e "/etc/apt/trusted.gpg.d/freexian-elts.gpg" ]; then
    wget "https://deb.freexian.com/extended-lts/archive-key.gpg" -O "/etc/apt/trusted.gpg.d/freexian-elts.gpg"
  fi

  cat << 'EOF' > "/etc/apt/sources.list"
deb https://mirrors.tuna.tsinghua.edu.cn/debian-elts buster main contrib non-free
deb http://archive.debian.org/debian buster-updates main contrib non-free
deb http://archive.debian.org/debian-security buster/updates main contrib non-free
EOF
fi
# </mirror>

# enable noninteractive mode due to apt prompts.
export DEBIAN_FRONTEND="noninteractive"

set -x

# enable armhf support for cross-compiling.
dpkg --add-architecture "armhf"

apt -qq update

apt -qq install -y \
  build-essential \
  pkg-config \
  texinfo \
  zip \
  wget \
  file \
  curl \
  ca-certificates \
  python3 \
  git \
  autoconf \
  automake \
  libtool \
  gettext \
  intltool \
  qemu-user \
  libparse-yapp-perl \
  gcc-arm-linux-gnueabihf \
  g++-arm-linux-gnueabihf \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  libffi-dev \
  liblzma-dev \
  uuid-dev \
  libncursesw5-dev \
  libdbus-1-dev \
  libexpat1-dev \
  libdaemon-dev \
  libglib2.0-dev \
  libgdbm-dev \
  libacl1-dev \
  libc6-dev:armhf \
  libffi-dev:armhf \
  libsqlite3-dev:armhf \
  libncursesw5-dev:armhf \
  libdbus-1-dev:armhf \
  libexpat1-dev:armhf \
  libdaemon-dev:armhf \
  libglib2.0-dev:armhf \
  libevent-dev:armhf \
  libgdbm-dev:armhf \
  libgnutls28-dev:armhf \
  libext2fs-dev \
  libcomerr2:armhf \
  comerr-dev:armhf \
  krb5-config \
  libkrb5-dev:armhf \
  libkrb5-dev \
  libpam0g-dev:armhf \
  libacl1-dev:armhf \
  libattr1-dev:armhf

# python source

PYTHONVER="3.12.3"

cd "$WORKDIR"

if [ ! -e "Python-${PYTHONVER}.tar.xz" ]; then
  wget "https://www.python.org/ftp/python/${PYTHONVER}/Python-${PYTHONVER}.tar.xz" -O "Python-${PYTHONVER}.tar.xz"
fi

if [ ! -d "Python-${PYTHONVER}" ]; then
  tar -xf "Python-${PYTHONVER}.tar.xz"
fi

# python native

cd "$WORKDIR"

if [ ! -d "Python-${PYTHONVER}-native" ]; then
  cp -av "Python-${PYTHONVER}" "Python-${PYTHONVER}-native"
fi

cd "Python-${PYTHONVER}-native" || exit 1

./configure --disable-shared --without-ensurepip > /dev/null

make --quiet -j"$(nproc)" || exit 1
make --quiet install > /dev/null || exit 1

# python arm

export TARGET="arm-linux-gnueabihf"
export CC="${TARGET}-gcc"
export CXX="${TARGET}-g++"
export AR="${TARGET}-ar"
export RANLIB="${TARGET}-ranlib"
export STRIP="${TARGET}-strip"
export PKG_CONFIG_LIBDIR="/usr/lib/${TARGET}/pkgconfig:/usr/share/pkgconfig"
export PKG_CONFIG="${TARGET}-pkg-config"
export PKG_CONFIG_SYSROOT_DIR="/"

cd "$WORKDIR"

if [ ! -d "Python-${PYTHONVER}-arm" ]; then
  cp -av "Python-${PYTHONVER}" "Python-${PYTHONVER}-arm"
fi

cd "Python-${PYTHONVER}-arm" || exit 1

# enable python sqlite and ctypes.
cat << 'EOF' > Modules/Setup.local
_ctypes _ctypes/_ctypes.c _ctypes/callbacks.c _ctypes/callproc.c \
    _ctypes/cfield.c _ctypes/stgdict.c \
    -I/usr/include/arm-linux-gnueabihf \
    -L/usr/lib/arm-linux-gnueabihf -l:libffi.a -ldl

_sqlite3 \
  _sqlite/blob.c \
  _sqlite/connection.c \
  _sqlite/cursor.c \
  _sqlite/microprotocols.c \
  _sqlite/module.c \
  _sqlite/prepare_protocol.c \
  _sqlite/row.c \
  _sqlite/statement.c \
  _sqlite/util.c \
  -I/usr/include/arm-linux-gnueabihf \
  -L/usr/lib/arm-linux-gnueabihf -l:libsqlite3.a
EOF

./configure \
  --host="$TARGET" \
  --build="x86_64-linux-gnu" \
  --prefix="/usr/local" \
  --disable-shared --disable-ipv6 \
  --without-ensurepip \
  --with-build-python="/usr/local/bin/python3" \
  ac_cv_file__dev_ptmx="yes" ac_cv_file__dev_ptc="no" > /dev/null

make --quiet -j"$(nproc)" || exit 1
make --quiet install DESTDIR="/out" > /dev/null || exit 1

# screen arm

cd "$WORKDIR"

if [ ! -d "screen/.git" ]; then
  git clone "https://git.savannah.gnu.org/git/screen.git" "screen"
fi

cd "screen" || exit 1

git checkout --quiet "ecea7aa87dbb0fe04ea2145d0a9a7a08dc597088^"

cd "src" || exit 1

if [ ! -f "configure" ]; then
  ./autogen.sh
fi

CPPFLAGS="-I/usr/include/arm-linux-gnueabihf" ./configure \
  --host="$TARGET" \
  --build="x86_64-linux-gnu" \
  --prefix="/usr/local" \
  --disable-pam > /dev/null

make --quiet -j"$(nproc)" || exit 1
# make --quiet -j"$(nproc)" CFLAGS="-O2 -Wall -static" LIBS="-lncursesw -ltinfo" || exit 1
make --quiet install DESTDIR="/out" > /dev/null || exit 1

# nano arm

NANOVER="8.7"

cd "$WORKDIR"

if [ ! -e "nano-${NANOVER}.tar.gz" ]; then
  wget "https://www.nano-editor.org/dist/v8/nano-${NANOVER}.tar.gz" -O "nano-${NANOVER}.tar.gz"
fi

if [ ! -d "nano-${NANOVER}" ]; then
  tar -xf "nano-${NANOVER}.tar.gz"
fi

cd "nano-${NANOVER}" || exit 1

./configure \
  --host="$TARGET" \
  --build="x86_64-linux-gnu" \
  --prefix="/usr/local" \
  --disable-nls > /dev/null

make --quiet -j"$(nproc)" || exit 1
# make --quiet -j"$(nproc)" CFLAGS="-O2 -Wall -static" LIBS="-lncursesw -ltinfo" || exit 1
make --quiet install DESTDIR="/out" > /dev/null || exit 1

# avahi arm

cd "$WORKDIR"

if [ ! -d "avahi/.git" ]; then
  git clone "https://github.com/avahi/avahi" "avahi"
fi

cd "avahi" || exit 1

git checkout --quiet "48c00ff43d1235ea1c84a783a375493fccf3057a"

if [ ! -f "configure" ]; then
  ./autogen.sh
fi

./configure \
  --host="$TARGET" \
  --build="x86_64-linux-gnu" \
  --prefix="/usr/local" \
  --with-distro=none \
  --disable-qt5 \
  --disable-gtk3 \
  --disable-libsystemd \
  --disable-python \
  --disable-mono \
  --disable-manpages > /dev/null

make --quiet -j"$(nproc)" || exit 1
make --quiet install DESTDIR="/out" > /dev/null || exit 1

# cat << 'EOF' > /media/sda1/avahi/avahi-daemon.conf
# [server]
# use-ipv4=yes
# use-ipv6=no
# ratelimit-interval-usec=1000000
# ratelimit-burst=1000
# [publish]
# publish-addresses=yes
# publish-hinfo=no
# publish-workstation=no
# [reflector]
# enable-reflector=no
# EOF

# samba arm

SAMBAVER="4.12.15"

cd "$WORKDIR"

if [ ! -e "samba-${SAMBAVER}.tar.gz" ]; then
  wget "https://download.samba.org/pub/samba/samba-${SAMBAVER}.tar.gz" -O "samba-${SAMBAVER}.tar.gz"
fi

if [ ! -d "samba-${SAMBAVER}" ]; then
  tar -xf "samba-${SAMBAVER}.tar.gz"
fi

cd "samba-${SAMBAVER}" || exit 1

export HOSTCC="gcc"
export PYTHON="/usr/bin/python3"

./configure \
  --cross-compile \
  --cross-execute="qemu-arm -L /usr/arm-linux-gnueabihf" \
  --with-system-mitkrb5 \
  --hostcc="${HOSTCC}" \
  --prefix="/usr/local" \
  --enable-fhs \
  --disable-python \
  --without-json \
  --without-libarchive \
  --without-ldap \
  --without-ads \
  --without-pam \
  --without-ad-dc \
  --bundled-libraries='!asn1_compile,!compile_et' > /dev/null

make --quiet -j"$(nproc)" || exit 1
make --quiet install DESTDIR="/out" > /dev/null || exit 1

cat << 'EOF' > /media/sda1/samba/smb.conf
[global]
workgroup = WORKGROUP
netbios name = CHITU
server role = standalone server
security = user
map to guest = Bad User
guest account = root
force user = root
force group = root
load printers = no
disable spoolss = yes
printing = bsd
printcap name = /dev/null
log level = 0
log file = /dev/null
pam password change = no
[root]
path = /
read only = no
guest ok = yes
browseable = yes
EOF

# /media/sda1/system/usr/local/sbin/nmbd --foreground --log-stdout --configfile=/media/sda1/samba/smb.conf --debuglevel=4 --no-process-group
# /media/sda1/system/usr/local/sbin/nmbd --daemon --configfile=/media/sda1/samba/smb.conf --no-process-group
# /media/sda1/system/usr/local/sbin/smbd --daemon --configfile=/media/sda1/samba/smb.conf --no-process-group

# output

# copy missing terminfo.
cp -av /lib/terminfo /out/usr/local/share/

# copy missing libraries to the arm device.
cp -av /usr/lib/arm-linux-gnueabihf/. /lib/arm-linux-gnueabihf/. /out/usr/local/lib/

# adjust library symbolc links.
cd /out/usr/local/lib && find . -type l | while read -r link; do
    target=$(readlink "$link")
    case "$target" in
        /lib/arm-linux-gnueabihf/*|/usr/lib/arm-linux-gnueabihf/*)
            base=$(basename "$target")
            ln -snf "$base" "$link"
            ;;
    esac
done

# omit python tests and man pages.
rm -rf \
  "/out/usr/local/lib/python3.12/test" \
  "/out/usr/local/share/man" \
  "/build/out.zip" \
  "/build/out.tar"

# export as zip (cannot extract symbolic links).
cd "/out" && zip -q -r "/build/out.zip" "usr"
# cd "/out" && tar -chf "/build/out.tar" "usr"

du -h /build/out.*

# usage

# update the device paths (eg. /etc/profile).
# export PATH=$PATH:/media/sda1/system/usr/local/bin:/media/sda1/system/usr/local/sbin
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/media/sda1/system/usr/local/lib
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/media/sda1/system/usr/local/lib/samba
# export TERM=xterm-256color
# export TERMINFO=/media/sda1/system/usr/local/share/terminfo
