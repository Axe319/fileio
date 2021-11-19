from fileio import FileIO, BRFile


def main():
    # create a layout object
    layout = FileIO('example')
    # create a file object with the layout object
    file = BRFile(layout)
    # loop through all records
    for record_number, record in file.records.items():
        print(record_number, record)

    # create a key to the file using the field key$
    keys = file.create_key('key$')
    # get the record number with the key '000001'
    record_number_for_key_1 = keys['000001']
    # get the record with that record number
    record_for_key_1 = file.records[record_number_for_key_1]
    # print a few fields from that record
    print(record_for_key_1['name$'])
    print(record_for_key_1['last$'])
    print(record_for_key_1['age'])


if __name__ == '__main__':
    main()
