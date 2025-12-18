# docker run --rm -it -v "$(pwd)":/build debian:buster

PYNUM="3.12.3"
PYVER="Python-${PYNUM}"

# <proxy>

export HTTP_PROXY=http://192.168.2.45:8053 HTTPS_PROXY=http://192.168.2.45:8053 http_proxy=http://192.168.2.45:8053 https_proxy=http://192.168.2.45:8053

cat << 'EOF' > /etc/apt/apt.conf.d/01proxy
Acquire::http { Proxy "http://192.168.2.45:8053"; No-Cache "false"; No-Store "false"; Max-Age "31536000"; };
Acquire::https { Proxy "http://192.168.2.45:8053"; No-Cache "false"; No-Store "false"; Max-Age "31536000"; };
Acquire::Check-Valid-Until "false";
EOF

# </proxy>

cat << 'EOF' > /etc/apt/sources.list
deb http://archive.debian.org/debian buster main contrib non-free
deb http://archive.debian.org/debian buster-updates main contrib non-free
deb http://archive.debian.org/debian-security buster/updates main contrib non-free
EOF

# <mirror>

if ! command -v wget; then
  apt -qq update
  apt -qq install -y wget
fi

[ -e /etc/apt/trusted.gpg.d/freexian-elts.gpg ] || wget -O /etc/apt/trusted.gpg.d/freexian-elts.gpg https://deb.freexian.com/extended-lts/archive-key.gpg

cat << 'EOF' > /etc/apt/sources.list
deb https://mirrors.tuna.tsinghua.edu.cn/debian-elts buster main contrib non-free
deb http://archive.debian.org/debian buster-updates main contrib non-free
deb http://archive.debian.org/debian-security buster/updates main contrib non-free
EOF

# </mirror>

set -x

dpkg --add-architecture armhf

apt -qq update

apt -qq install -y \
  build-essential pkg-config \
  zip wget file curl ca-certificates \
  gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf \
  libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
  libsqlite3-dev libffi-dev liblzma-dev uuid-dev libncursesw5-dev \
  libc6-dev:armhf libffi-dev:armhf libsqlite3-dev:armhf

# python native

cd /build

[ -e ${PYVER}.tar.xz ] || wget https://www.python.org/ftp/python/${PYNUM}/${PYVER}.tar.xz
rm -rf ${PYVER}
tar -xf ${PYVER}.tar.xz
cd /build/${PYVER} || exit 1

./configure --disable-shared --without-ensurepip > /dev/null

make --quiet -j$(nproc) || exit 1
make --quiet install || exit 1
make --quiet distclean

# python arm

export TARGET=arm-linux-gnueabihf
export CC=$TARGET-gcc
export CXX=$TARGET-g++
export AR=$TARGET-ar
export RANLIB=$TARGET-ranlib
export STRIP=$TARGET-strip

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
  --host=$TARGET \
  --build=x86_64-linux-gnu \
  --prefix=/usr/local \
  --disable-shared --disable-ipv6 \
  --without-ensurepip \
  --with-build-python=/usr/local/bin/python3 \
  ac_cv_file__dev_ptmx=yes ac_cv_file__dev_ptc=no > /dev/null

make --quiet -j$(nproc) || exit 1
make --quiet install DESTDIR=/out/python-arm || exit 1

rm -rf /out/python-arm/usr/local/lib/python3.12/test/
cd /out/python-arm && zip -q -r /build/python-arm.zip usr
# cd /out/python-arm && tar -chf /build/python-arm.tar usr
du -h /build/python-arm.*
