import array
import mmap
import re

from contextlib import contextmanager

XOR_MASK = 0x2c
XOR_MASK_BYTES = XOR_MASK.to_bytes(length=1, byteorder='little', signed=False)


def transcrypt(data):
    mask = XOR_MASK
    arr = array.array('B', data)
    return array.array('B', [u ^ mask for u in arr]).tobytes()


def encrypt_str(s):
    data = s.encode(encoding='utf-8', errors='strict')
    return transcrypt(data)


def decrypt_str(data):
    data = transcrypt(data)
    return data.decode(encoding='utf-8', errors='strict')


START_SIGNATURE_VERBOSE = encrypt_str('{\r\n    "format_ver":')
START_SIGNATURE_MINIFIED = encrypt_str('{"format_ver":')


@contextmanager
def open_mmap_read(path):
    with open(path, 'rb') as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as m:
            yield m


def iter_sections(data):
    regex = re.escape(START_SIGNATURE_VERBOSE) + b'|' + re.escape(START_SIGNATURE_MINIFIED)

    for match in re.finditer(regex, m):
        start_index = match.start()
        end_index = data.find(START_SIGNATURE_VERBOSE, start_index + 1)
        if end_index == -1:
            end_index = data.find(START_SIGNATURE_MINIFIED, start_index + 1)
            if end_index == -1:
                end_index = data.find(b'\x00\x00\x00\x00', start_index + 1)
                if end_index == -1:
                    continue

        section = m[start_index:end_index]
        yield section.rstrip(b'\x00')


def iter_decrypted_sections(data):
    for section in iter_sections(m):
        yield transcrypt(section)


def iter_decoded_sections(data):
    for section in iter_decrypted_sections(m):
        yield section.decode(encoding='utf-8', errors='strict')


import json
import os
os.makedirs('/home/openglfreak/Pimax/JSONs', exist_ok=True)
with open_mmap_read('pi_server.exe') as m:
    for section in iter_decoded_sections(m):
        if 'Pimax' in section or 'pimax' in section or '"usb_vid":1155' in section:
            parsed_section = json.loads(section)
            print(json.dumps(parsed_section, indent=4))
            name = parsed_section.get('name', None)
            if not name:
                name = 'default'
            with open('/home/openglfreak/Pimax/JSONs/' + name + '.json', 'w') as f:
                json.dump(parsed_section, f, indent=4)
