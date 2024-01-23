#!/usr/bin/env python


"""
Basic reader for SEGD rev 3.0
ML 16/11/2022
"""


import sys
import numpy as np
import datetime


# GPS EPOCH expressed in UTC datetime
GPS_EPOCH = datetime.datetime(
    1980, 1, 6, tzinfo=datetime.timezone.utc)


def segd_timestamp(bytes_in: bytes):
    """
    A SEG-D Rev 3.0 timestamp is an 8 byte, signed, big-endian integer counting the number of microseconds since
    6 Jan 1980 00:00:00 (GPS epoch). The timestamp is equal to GPS time converted to microseconds.
    """
    gps_microseconds = int.from_bytes(bytes_in, byteorder="big", signed=True)

    utc_datetime = \
        GPS_EPOCH + \
        datetime.timedelta(seconds=gps_microseconds / 1e6)
    return utc_datetime


def read_segd_rev3_0(segdfilename: str):
    traces = []

    with open(segdfilename, 'rb') as fid:
        general_header_block1 = fid.read(32)
        general_header_block2 = fid.read(32)
        general_header_block3 = fid.read(32)

        # segd revision number
        segd_revision = float(
            f"{general_header_block2[10:11].hex()}.{general_header_block2[11:12].hex()}")
        assert segd_revision == 3.0, segd_revision

        # additionnal blocks of the general header
        # right 4 bits of byte 11, usigned int
        number_of_additional_blocks_in_general_header = \
            int.from_bytes(bytes([general_header_block1[11] >> 4]), byteorder="big", signed=False)

        if number_of_additional_blocks_in_general_header == 15:
            # means F => then use ghb2
            number_of_additional_blocks_in_general_header = \
                int.from_bytes(general_header_block2[22:24], byteorder="big", signed=False)

        print(f"number_of_additional_blocks_in_general_header: {number_of_additional_blocks_in_general_header}")
        general_header_remaining_blocks = fid.read(32 * (number_of_additional_blocks_in_general_header - 2))

        # number of scan types per record
        n_scan_type_per_record = int(general_header_block1[27:28].hex())
        print(f"n_scan_type_per_record: {n_scan_type_per_record}")

        # number of channel sets per scan type
        h = general_header_block1[28:29].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[3:5], byteorder="big", signed=False)
            n_channel_sets_per_scan_type = h
        else:
            n_channel_sets_per_scan_type = int(h)
        print(f"n_channel_sets_per_scan_type: {n_channel_sets_per_scan_type}")

        # number of 32 bytes extensions after each scan type header block
        h = general_header_block1[29:30].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[8:10], byteorder="big", signed=False)
            skew_extension_length = h * 32
        else:
            skew_extension_length = int(h) * 32
        print(f"skew_extension_length: {skew_extension_length}")

        # extended recording mode
        extended_recording_mode = \
            int.from_bytes(general_header_block3[29:30], byteorder="big", signed=False)
        print(f"extended_recording_mode: {extended_recording_mode}")

        # relative time mode
        relative_time_mode = \
            int.from_bytes(general_header_block3[29:30], byteorder="big", signed=False)
        print(f"relative_time_mode: {relative_time_mode}")
        if relative_time_mode != 0:
            raise NotImplementedError('relative time mode not implemented')

        # ======================================
        scan_type_headers = {}
        for _ in range(n_scan_type_per_record):
            # new scan type header

            for n_channel_set in range(n_channel_sets_per_scan_type):
                # new channel set in this scan type
                channel_set_descriptor = fid.read(96)  # WARNING IS 96 AFTER 3.0, WAS 32 BEFORE

                # ==
                scan_type_number = int(channel_set_descriptor[0:1].hex())
                scan_type_headers[scan_type_number] = {}

                # ==
                channel_set_number = int.from_bytes(channel_set_descriptor[1:3],
                                                    byteorder="big", signed=False)
                scan_type_headers[scan_type_number][channel_set_number] = {}

                # ==
                scan_type_headers[scan_type_number][channel_set_number]\
                    ["number_of_samples"] = \
                        int.from_bytes(channel_set_descriptor[12:16],
                                       byteorder="big", signed=False)

                # ==
                scan_type_headers[scan_type_number][channel_set_number]\
                    ["number_of_channels"] = \
                    int.from_bytes(channel_set_descriptor[20:23],
                                   byteorder="big", signed=False)
                # ==
                scan_type_headers[scan_type_number][channel_set_number]\
                    ["sampling_interval_microsec"] = \
                    int.from_bytes(channel_set_descriptor[23:26],
                                   byteorder="big", signed=False)

                # ==
                scan_type_headers[scan_type_number][channel_set_number] \
                    ["number_of_trace_header_extensions"] = \
                        int.from_bytes(channel_set_descriptor[27:28],
                                       byteorder="big", signed=False)

            sample_skew_header = fid.read(skew_extension_length)
        print(scan_type_headers)

        # ======================================
        # extended header
        h = general_header_block1[30:31].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[5:8], byteorder="big", signed=False)
            extended_header_length = h * 32
        else:
            extended_header_length = int(h) * 32
        print(f"extended_header_length: {extended_header_length}")
        fid.read(extended_header_length)

        # ======================================
        # external header
        h = general_header_block1[31:32].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[27:30], byteorder="big", signed=False)
            external_header_length = h * 32
        else:
            external_header_length = int(h) * 32
        print(f"external_header_length: {external_header_length}")
        fid.read(external_header_length)

        # ====================================== traces
        for scan_type_number, scan_type_header in scan_type_headers.items():
            for channel_set_number, channel_set_descriptor in scan_type_header.items():

                delta = channel_set_descriptor["sampling_interval_microsec"] * 1e-6
                npts = channel_set_descriptor['number_of_samples']

                for channel_number in range(channel_set_descriptor["number_of_channels"]):
                    # =========== trace header

                    # ========= demux trace header
                    demux_trace_header = fid.read(20)
                    first_timing_word = demux_trace_header[6:9]
                    if first_timing_word != b"\x00" * 3:
                        print(first_timing_word)
                        raise NotImplementedError(r'first_timing_word != \x00\x00\x00 not implemented')

                    sample_skew = demux_trace_header[10]
                    if sample_skew != 0:
                        print(sample_skew)
                        raise NotImplementedError(r'sample_skew != \x00 not implemented')

                    # ========= trace header extension block 1
                    trace_header_extension1 = fid.read(32)

                    receiver_line_number = int.from_bytes(trace_header_extension1[0:3], byteorder="big", signed=True)
                    # print(f"receiver_line_number={receiver_line_number}")

                    receiver_point_number = int.from_bytes(trace_header_extension1[3:6], byteorder="big", signed=True)
                    # print(f"receiver_point_number={receiver_point_number}")

                    # number of samples in this trace => why not using the channel set descriptor?
                    number_of_samples = int.from_bytes(trace_header_extension1[24:28], byteorder="big", signed=False)
                    assert number_of_samples == channel_set_descriptor['number_of_samples']
                    # print(f"number_of_samples={number_of_samples}")

                    # remaining trace header extension blocks (extension 1 already read)
                    remaining_trace_header = fid.read((channel_set_descriptor["number_of_trace_header_extensions"]-1) * 32)
                    # ========= optionnal blocks
                    if channel_set_descriptor["number_of_trace_header_extensions"] >= 2:
                        timestamp_header = remaining_trace_header[:32]

                        time_zero = segd_timestamp(timestamp_header[:8])
                        # TODO : implement sample_skew (fraction of dt to shift the first sample)
                        # TODO : first_timing_word (??)

                        starttime = time_zero.timestamp()

                    trace_header = {
                        "starttime": starttime,  # float
                        "npts": npts,   # int
                        "delta": delta,    # float in sec
                        "segd": {
                            "segd_revision": segd_revision,
                            "receiver_line_number": receiver_line_number,
                            "receiver_point_number": receiver_point_number,
                            "scan_type_number": scan_type_number,
                            "channel_set_number": channel_set_number,
                            "channel_number": channel_number,
                            }
                        }

                    # data type assumed to be >f4...
                    trace_data = np.frombuffer(fid.read(channel_set_descriptor["number_of_samples"] * 4), dtype=">f4")
                    traces.append((trace_header, trace_data))
        return traces


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    traces = read_segd_rev3_0(sys.argv[1])

    for n, (trace_header, trace_data) in enumerate(traces):
        t = np.arange(trace_header['npts']) * trace_header['delta']
        d = trace_data

        plt.plot(t, 0.1 * d / np.std(d) + n)

    plt.show()

