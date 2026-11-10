"""Wraps a plug-in's own state (getStateInformation bytes) the way JUCE's VST3 host stores it, so RefCapture /
RefRender can load it into the VST3 build:  python nulltest/vst3state_lib.py inner.bin out.bin"""
import os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts', 'nulltest'))   # scripts/nulltest/ref_state_lib.py
from ref_state_lib import b64enc


def wrap(inner):
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<VST3PluginState><IComponent>' + b64enc(inner)
           + '</IComponent></VST3PluginState>').encode() + b'\0'
    return b'VC2!' + struct.pack('<I', len(xml) - 1) + xml


def own_state(**props):
    attrs = ' '.join(f'{k}="{v}"' for k, v in props.items())
    x = f'<?xml version="1.0" encoding="UTF-8"?>\n<Positron {attrs}/>'.encode() + b'\0'
    return b'VC2!' + struct.pack('<I', len(x)) + x


if __name__ == '__main__':
    open(sys.argv[2], 'wb').write(wrap(open(sys.argv[1], 'rb').read()))
