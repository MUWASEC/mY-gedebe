#!/bin/sh

REPO_DIR=$PWD
GDB_DIR=/opt/gdb-src/
mkdir -p $GDB_DIR && pushd $GDB_DIR

### pwndbg
git clone https://github.com/pwndbg/pwndbg
pushd pwndbg
./setup.sh
popd

### gef
git clone https://github.com/hugsy/gef

### gef bata24
git clone https://github.com/bata24/gef gef-kernel

### create shortcut & gdbinit
sudo cp "$REPO_DIR/bin/*" /usr/local/bin/
cp "$REPO_DIR/gdbinit" ~/.gdbinit
cp -r "$REPO_DIR/mygdb/" "$GDB_DIR"
popd