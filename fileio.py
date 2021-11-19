from formats import bh_format, pd_format, zd_format, c_format, v_format, x_format
import sys
from typing import Callable, Dict, IO, Iterator, List, Tuple, Union
from os import path

FormatFunction = Callable[[bytes, int], Union[str, float, int, None]]
FileIOEntry = Tuple[str, int, int, int, FormatFunction, int]
FileField = Union[str, int, float, None]
FileRecord = Dict[str, FileField]


class FileIO:
    formats: Dict[str, FormatFunction] = {
        'bh': bh_format,
        'pd': pd_format,
        'zd': zd_format,
        'c': c_format,
        'v': v_format,
        'x': x_format
    }

    def __init__(self, layout: str) -> None:
        assert path.exists(f'filelay\\{layout}')
        self.filelay = f'filelay\\{layout}'
        self.recl = 0
        self.data_file = ''
        self.layout: List[FileIOEntry] = []
        self.parse_layout()

    def parse_layout(self) -> None:
        with open(self.filelay, 'r') as f:
            line = f.readline()
            comma = line.find(',')
            self.data_file = line[:comma]
            while line[0] != '=':
                line = f.readline()
                if line[:4].lower() == 'recl':
                    self.recl = int(line[5:].strip())
            cursor = 0
            for line in f:
                if line[:5].upper() == '#EOF#':
                    break
                fields = line.split(',')
                if len(fields) >= 2:
                    entry, cursor = self.parse_field(fields, cursor)
                    self.layout.append(entry)
    
    def parse_field(self, fields: List[str], cursor: int) -> Tuple[FileIOEntry, int]:
        field_name = fields[0].lower().strip()
        form = fields[2].lower().strip().split()
        form_type = form[0]
        form_len = form[1]
        decimal_pos = form_len.find('.')
        if decimal_pos == -1:
            decimal = 0
            int_len = int(form_len)
        else:
            decimal = int(form_len[decimal_pos + 1:])
            int_len = int(form_len[:decimal_pos])
        end = cursor + int_len
        entry = (field_name, cursor, end, decimal, self.formats[form_type], int_len)
        return entry, end


class BRFile:
    GOOD_REC = 32
    DEL_REC = 68

    def __init__(self, fileio: FileIO) -> None:
        self.fileio = fileio
        self.records: Dict[int, FileRecord] = dict()
        self.read_file()

    def read_file(self) -> None:
        """
        reads entirety of a BR file
        populating self.records along the way
        self.records is a dict of {record_number: FileIO_entry}
        FileIO_entry is a dict of {subscript_name: field_value}
        """
        with open(self.fileio.data_file, 'rb') as f:
            del_char, reclen = self.get_reclen(f)
            reclen += 1
            for rec, line in enumerate(self.iter_recs(f, reclen), 1):
                if del_char != self.DEL_REC:
                    record: FileRecord = dict()
                    for name, start, end, decimals, convert, _ in self.fileio.layout:
                        try:
                            record[name] = convert(line[start:end], decimals)
                        except Exception as e:
                            record[name] = None
                    self.records[rec] = record
                if len(line) == reclen:
                    del_char = line[-1]
    
    def get_reclen(self, f: IO[bytes]) -> Tuple[int, int]:
        """
        reads the header of a file setting the
        cursor at the beginning of the first record
        returns a tuple of (first_rec_delete_flag, record_length)
        """
        recl = 0
        char = 0
        first_15 = f.read(15)
        for i, byte in enumerate(first_15[9:11]):
            recl += byte << (8 * i)

        while char not in (self.GOOD_REC, self.DEL_REC):
            char = f.read(1)[0]
        return char, recl
    
    @staticmethod
    def iter_recs(f: IO[bytes], size: int) -> Iterator[bytes]:
        """
        generator that yields full file rows (deleted and valid)
        should always be called after self.get_reclen
        since that sets the cursor at the beginning
        of the first record
        """
        rec_bytes = f.read(size)
        while rec_bytes:
            yield rec_bytes
            rec_bytes = f.read(size)

    def create_key(self, *fields: str) -> Dict[str, int]:
        """
        returns a dict of {key: record_number}
        where key is the exact key of the record number
        """
        fields = tuple(field.lower() for field in fields)
        ordered_keys: Dict[int, Tuple[str, int]]
        ordered_keys = {i: ('', 0) for i in range(len(fields))}
        for name, _, _, _, _, field_len in self.fileio.layout:
            try:
                index = fields.index(name)
            except ValueError:
                continue
            ordered_keys[index] = (name, field_len)
            
        keys: Dict[str, int] = dict()
        for rec_number, record in self.records.items():
            key = ''
            for name, field_len in ordered_keys.values():
                if name.endswith('$'):
                    key = key + str(record[name]).ljust(field_len)
                else:
                    key = key + str(record[name]).zfill(field_len)
            keys[key] = rec_number
        return keys


if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_io = FileIO(sys.argv[1])
    else:
        file_io = FileIO('example')
    br_file = BRFile(file_io)
    print(br_file.records)
