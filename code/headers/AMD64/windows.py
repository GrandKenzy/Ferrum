import struct

def _align(value: int, alignment: int):
    return (value + alignment - 1) & ~(alignment - 1)


# Standard x64 section flags
SECTION_FLAGS = {
    ".text":  0x60000020,
    ".data":  0xC0000040,
    ".bss":   0xC0000080,
    ".rdata": 0x40000040,
    ".info":  0x42000040,
    ".idata": 0xC0000040,
    ".edata": 0x40000040,
    ".rsrc":  0x40000040,
    ".reloc": 0x42000040,
}

# Data directory index mapping
DIRECTORY_INDEX = {
    ".edata": 0,
    ".idata": 1,
    ".rsrc": 2,
    ".reloc": 5,
}


def generate(
    text_size: int,
    data_size: int,
    bss_size: int,
    other_sections: dict[str, int] | None = None,

    image_base: int = 0x140000000,
    section_alignment: int = 0x1000,
    file_alignment: int = 0x200,

    subsystem: int = 3,

    linker_version: tuple[int, int] = (1, 0),
    os_version: tuple[int, int] = (6, 0),
    image_version: tuple[int, int] = (0, 0),
    subsystem_version: tuple[int, int] = (6, 0),

    stack_reserve: int = 0x100000,
    stack_commit: int = 0x1000,
    heap_reserve: int = 0x100000,
    heap_commit: int = 0x1000,

    dll_characteristics: int = 0x8140,
    characteristics: int = 0x0022,

    timestamp: int = 0
) -> bytes:

    if other_sections is None:
        other_sections = {}

    DOS_HEADER = struct.pack("<2s58sI", b"MZ", b"\x00"*58, 0x80)
    DOS_STUB = b"\x00" * (0x80 - len(DOS_HEADER))
    PE_SIGN = b"PE\x00\x00"

    sections = [
        (".text", text_size),
        (".data", data_size),
        (".bss", bss_size),
    ]

    for name, size in other_sections.items():
        sections.append((name, size))

    number_of_sections = len(sections)
    optional_header_size = 0xF0
    section_table_size = number_of_sections * 40

    headers_size = _align(
        0x80 + len(PE_SIGN) + 20 + optional_header_size + section_table_size,
        file_alignment
    )

    rva = section_alignment
    raw = headers_size

    section_headers = bytearray()

    size_of_code = 0
    size_of_initialized = 0
    size_of_uninitialized = 0

    base_of_code = 0
    entry_point = 0

    directories = [[0, 0] for _ in range(16)]

    for name, size in sections:
        flags = SECTION_FLAGS.get(name, 0x40000040)

        virtual_size = size

        if name == ".bss":
            raw_size = 0
            raw_ptr = 0
        else:
            raw_size = _align(size, file_alignment)
            raw_ptr = raw

        if flags & 0x20:
            size_of_code += _align(size, section_alignment)
        elif flags & 0x40:
            size_of_initialized += _align(size, section_alignment)
        elif flags & 0x80:
            size_of_uninitialized += _align(size, section_alignment)

        if name == ".text":
            base_of_code = rva
            entry_point = rva

        if name in DIRECTORY_INDEX:
            idx = DIRECTORY_INDEX[name]
            directories[idx][0] = rva
            directories[idx][1] = size

        name_bytes = name.encode()[:8].ljust(8, b"\x00")

        section_headers += struct.pack(
            "<8sIIIIIIHHI",
            name_bytes,
            virtual_size,
            rva,
            raw_size,
            raw_ptr,
            0,
            0,
            0,
            0,
            flags
        )

        rva += _align(size, section_alignment)

        if raw_size:
            raw += raw_size

    size_of_image = _align(rva, section_alignment)

    data_directories = bytearray()
    for rva_dir, size_dir in directories:
        data_directories += struct.pack("<II", rva_dir, size_dir)

    major_link, minor_link = linker_version
    os_major, os_minor = os_version
    img_major, img_minor = image_version
    sub_major, sub_minor = subsystem_version

    optional_header = struct.pack(
        "<HBBIIIIIQIIHHHHHHIIIIHHQQQQII",
        0x20B,
        major_link,
        minor_link,
        size_of_code,
        size_of_initialized,
        size_of_uninitialized,
        entry_point,
        base_of_code,
        image_base,
        section_alignment,
        file_alignment,
        os_major,
        os_minor,
        img_major,
        img_minor,
        sub_major,
        sub_minor,
        0,
        size_of_image,
        headers_size,
        0,
        subsystem,
        dll_characteristics,
        stack_reserve,
        stack_commit,
        heap_reserve,
        heap_commit,
        0,
        16
    ) + bytes(data_directories)

    coff_header = struct.pack(
        "<HHIIIHH",
        0x8664,
        number_of_sections,
        timestamp,
        0,
        0,
        len(optional_header),
        characteristics
    )

    headers = bytearray()
    headers += DOS_HEADER
    headers += DOS_STUB
    headers += PE_SIGN
    headers += coff_header
    headers += optional_header
    headers += section_headers

    headers = headers.ljust(headers_size, b"\x00")

    return bytes(headers)
