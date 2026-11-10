#!/bin/sh
# Installs every Orrery plug-in in this folder for the current user: VST3 to ~/.vst3, CLAP to ~/.clap and
# the standalone apps (when the tarball carries a Standalone/ folder) to ~/.local/bin.
#   sh install-linux.sh              install
#   sh install-linux.sh --uninstall  remove again
set -e
cd "$(dirname "$0")"
V="$HOME/.vst3/Orrery Suite"
C="$HOME/.clap/Orrery Suite"
B="$HOME/.local/bin"
if [ "$1" = "--uninstall" ]; then
    rm -rf "$V" "$C"
    for p in Standalone/*; do
        [ -f "$p" ] && rm -f "$B/$(basename "$p")"
    done
    echo "Orrery removed from $V, $C and $B"
    exit 0
fi
mkdir -p "$V" "$C"
for p in VST3/*.vst3; do
    [ -e "$p" ] || continue
    rm -rf "${V:?}/$(basename "$p")"
    cp -r "$p" "$V/"
done
for p in CLAP/*.clap; do
    [ -e "$p" ] && cp "$p" "$C/"
done
for p in Standalone/*; do
    [ -f "$p" ] || continue
    mkdir -p "$B"
    cp "$p" "$B/"
    chmod +x "$B/$(basename "$p")"
done
echo "Installed to $V and $C:"
ls "$V" "$C"
if [ -d Standalone ]; then echo "Standalone apps in $B:"; ls Standalone; fi
echo "Rescan plug-ins in your DAW."
