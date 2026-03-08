# build_hola.py
# Generates a minimal Windows x64 executable that prints "Hola mundo"
# using kernel32 imports (GetStdHandle, WriteFile, Sleep).
# This file is intended for testing the PE header generator.
# use headers/AMD64/windows.py
from AMD64.windows import generate, _align
import struct

file_alignment = 0x200
section_alignment = 0x1000

# ---------------------------------------------------------
# Static data used by the program
# ---------------------------------------------------------

# Message printed to stdout
msg = b"Hola mundo\n"
data = msg
data_size = len(data)

# Import definitions
dll_name = b"kernel32.dll\x00"
fn_names = [b"GetStdHandle\x00", b"WriteFile\x00", b"Sleep\x00"]
n_funcs = len(fn_names)

# ---------------------------------------------------------
# Initial section layout assumptions
# ---------------------------------------------------------

# Reserve enough space for code. The final size is recalculated later.
text_size = 256

# Placeholder for .idata size (computed later)
idata_virtual_size = 0

# Section list used to reproduce the same layout logic as generate()
sections = [
    (".text", text_size),
    (".data", data_size),
    (".bss", 0x1000),
    (".idata", 0),
]

number_of_sections = len(sections)
optional_header_size = 0xF0
section_table_size = number_of_sections * 40

# ---------------------------------------------------------
# Compute header size exactly like the PE generator
# ---------------------------------------------------------

headers_size = _align(
    0x80 + len(b"PE\x00\x00") + 20 + optional_header_size + section_table_size,
    file_alignment
)

# ---------------------------------------------------------
# Pre-calculate section RVAs and raw offsets
# ---------------------------------------------------------

rva_cursor = _align(headers_size, section_alignment)
raw_cursor = headers_size

section_info = {}

for name, vsz in sections:
    rva = rva_cursor

    if name == ".bss":
        raw_size = 0
        raw_ptr = 0
    else:
        if name == ".idata":
            raw_size = _align(vsz if vsz else 0x1000, file_alignment)
        else:
            raw_size = _align(vsz, file_alignment)
        raw_ptr = raw_cursor

    section_info[name] = {
        "rva": rva,
        "vsize": vsz,
        "raw_ptr": raw_ptr,
        "raw_size": raw_size
    }

    rva_cursor += _align(vsz if vsz else 0x1000, section_alignment)

    if raw_size:
        raw_cursor += raw_size

# ---------------------------------------------------------
# Construct the .idata import section
# ---------------------------------------------------------

# Layout:
#   IMAGE_IMPORT_DESCRIPTOR
#   NULL_DESCRIPTOR
#   ILT (Import Lookup Table)
#   IAT (Import Address Table)
#   Hint/Name entries
#   DLL name string

ilt_offset = 0x28

# Ensure ILT is aligned to 8 bytes
if ilt_offset % 8 != 0:
    ilt_offset = ((ilt_offset + 7) // 8) * 8

ilt_size = 8 * (n_funcs + 1)

iat_offset = ilt_offset + ilt_size
iat_size = 8 * (n_funcs + 1)

# ---------------------------------------------------------
# Build Hint/Name entries
# ---------------------------------------------------------

hn_block = bytearray()
hn_addrs = []

for fn in fn_names:
    hn_addrs.append(None)

for fn in fn_names:
    if len(hn_block) % 2 != 0:
        hn_block += b"\x00"

    hint_offset = len(hn_block)
    hn_addrs[fn_names.index(fn)] = hint_offset

    # WORD hint + function name + null terminator
    hn_block += struct.pack("<H", 0) + fn

dll_name_offset = len(hn_block)
hn_block += dll_name

# ---------------------------------------------------------
# Calculate total .idata size
# ---------------------------------------------------------

idata_size = (iat_offset + iat_size) + len(hn_block)
idata_raw_size = _align(idata_size, file_alignment)

section_info[".idata"]["vsize"] = idata_size
section_info[".idata"]["raw_size"] = idata_raw_size

# ---------------------------------------------------------
# Recompute RVAs with final section sizes
# ---------------------------------------------------------

rva_cursor = _align(headers_size, section_alignment)

for name, _ in sections:
    vsz = section_info[name]["vsize"]
    section_info[name]["rva"] = rva_cursor
    rva_cursor += _align(vsz if vsz else 0x1000, section_alignment)

# Recompute raw file offsets
raw_cursor = headers_size

for name, _ in sections:
    if name == ".bss":
        section_info[name]["raw_ptr"] = 0
        section_info[name]["raw_size"] = 0
    else:
        raw_size = _align(section_info[name]["vsize"], file_alignment)
        section_info[name]["raw_ptr"] = raw_cursor
        section_info[name]["raw_size"] = raw_size
        raw_cursor += raw_size

# ---------------------------------------------------------
# Fill .idata section bytes
# ---------------------------------------------------------

idata = bytearray(b"\x00" * idata_size)

# ILT entries
for i, fn in enumerate(fn_names):
    hint_rva = (
        section_info[".idata"]["rva"]
        + (iat_offset + iat_size)
        + hn_addrs[i]
    )

    entry = struct.pack("<Q", hint_rva)
    off = ilt_offset + (8 * i)
    idata[off:off+8] = entry

# Null ILT terminator
idata[ilt_offset + 8 * n_funcs: ilt_offset + 8 * (n_funcs + 1)] = struct.pack("<Q", 0)

# IAT initialized with ILT values
for i in range(n_funcs):
    idata[iat_offset + 8*i : iat_offset + 8*(i+1)] = \
        idata[ilt_offset + 8*i : ilt_offset + 8*(i+1)]

idata[iat_offset + 8*n_funcs : iat_offset + 8*(n_funcs+1)] = struct.pack("<Q", 0)

# Copy Hint/Name block
hn_start = iat_offset + iat_size
idata[hn_start:hn_start+len(hn_block)] = hn_block

# ---------------------------------------------------------
# IMAGE_IMPORT_DESCRIPTOR
# ---------------------------------------------------------

orig_first_thunk_rva = section_info[".idata"]["rva"] + ilt_offset
first_thunk_rva = section_info[".idata"]["rva"] + iat_offset
name_rva = section_info[".idata"]["rva"] + hn_start + dll_name_offset

descriptor = struct.pack(
    "<IIIII",
    orig_first_thunk_rva,
    0,
    0,
    name_rva,
    first_thunk_rva
)

idata[0:20] = descriptor

# ---------------------------------------------------------
# Build the .text section (x64 assembly)
# ---------------------------------------------------------

text = bytearray()

# sub rsp,40
text += b"\x48\x83\xEC\x28"

# mov ecx, -11 (STD_OUTPUT_HANDLE)
text += b"\xB9" + struct.pack("<I", 0xFFFFFFF5)

# call [GetStdHandle]
call1_off = len(text)
text += b"\xFF\x15" + b"\x00\x00\x00\x00"

# mov rcx, rax
text += b"\x48\x89\xC1"

# lea rdx, [msg]
lea_off = len(text)
text += b"\x48\x8D\x15" + b"\x00\x00\x00\x00"

# mov r8d, len(msg)
text += b"\x41\xB8" + struct.pack("<I", len(msg))

# xor r9d,r9d
text += b"\x45\x31\xC9"

# call [WriteFile]
call2_off = len(text)
text += b"\xFF\x15" + b"\x00\x00\x00\x00"

# mov ecx, 10000
text += b"\xB9" + struct.pack("<I", 10000)

# call [Sleep]
call3_off = len(text)
text += b"\xFF\x15" + b"\x00\x00\x00\x00"

# restore stack
text += b"\x48\x83\xC4\x28"

# ret
text += b"\xC3"

# ---------------------------------------------------------
# Patch RIP-relative displacements
# ---------------------------------------------------------

text_rva = section_info[".text"]["rva"]

iat_rva_base = section_info[".idata"]["rva"] + iat_offset

getstd_iat_rva = iat_rva_base + 0*8
writefile_iat_rva = iat_rva_base + 1*8
sleep_iat_rva = iat_rva_base + 2*8

# GetStdHandle call
next_instr_rva = text_rva + call1_off + 6
disp1 = getstd_iat_rva - next_instr_rva
text[call1_off+2:call1_off+6] = struct.pack("<i", disp1)

# Message pointer
next_instr_rva = text_rva + lea_off + 7
msg_rva = section_info[".data"]["rva"]
disp_lea = msg_rva - next_instr_rva
text[lea_off+3:lea_off+7] = struct.pack("<i", disp_lea)

# WriteFile call
next_instr_rva = text_rva + call2_off + 6
disp2 = writefile_iat_rva - next_instr_rva
text[call2_off+2:call2_off+6] = struct.pack("<i", disp2)

# Sleep call
next_instr_rva = text_rva + call3_off + 6
disp3 = sleep_iat_rva - next_instr_rva
text[call3_off+2:call3_off+6] = struct.pack("<i", disp3)

text_size = len(text)

# ---------------------------------------------------------
# Align section data for file layout
# ---------------------------------------------------------

text_block = bytes(text) + b"\x00" * (_align(text_size, file_alignment) - text_size)
data_block = data + b"\x00" * (_align(data_size, file_alignment) - data_size)
idata_block = bytes(idata) + b"\x00" * (_align(len(idata), file_alignment) - len(idata))

# ---------------------------------------------------------
# Generate PE headers
# ---------------------------------------------------------

header = generate(
    text_size,
    data_size,
    bss_size=0x1000,
    other_sections={
        ".idata": len(idata)
    },
    subsystem=3
)

# ---------------------------------------------------------
# Final executable assembly
# ---------------------------------------------------------

exe = header + text_block + data_block + idata_block

with open("hello_kernel32.exe", "wb") as f:
    f.write(exe)

print("hello_kernel32.exe generated (size: {})".format(len(exe)))
