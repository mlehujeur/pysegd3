#!/usr/bin/env python

"""
Copyright (C) 2024  maximilien.lehujeur
Basic stand alone reader for SEGD rev 3.X
"""

from typing import List, Tuple, Dict, Any
import sys
import numpy as np
import datetime
from tempoo.gps import cumulative_leap_seconds


# ========================== GLOBAL VARIABLES
CHANNEL_TYPE_IDENTIFICATIONS: Dict[int, str] = {
    0x00: "Unused",
    0x10: "Seis",
    0x11: "Electromagnetic",
    0x20: "Time break",
    0x21: "Clock timebreak",
    0x22: "Field timebreak",
    0x30: "Up hole",
    0x40: "blablabla",
    0x50: "blablabla",
    0x60: "blablabla",
    0x61: "blablabla",
    0x62: "blablabla",
    0x63: "blablabla",
    0x70: "blablabla",
    0x80: "blablabla",
    0x90: "blablabla",
    0x91: "blablabla",
    0x92: "blablabla",
    0x93: "blablabla",
    0x94: "blablabla",
    0x95: "blablabla",
    0x96: "blablabla",
    0x97: "blablabla",
    0x98: "blablabla",
    0x99: "blablabla",
    0x9A: "blablabla",
    0x9B: "blablabla",
    0x9C: "blablabla",
    0xA0: "blablabla",
    0xB0: "blablabla",
    0xB1: "blablabla",
    0xB2: "blablabla",
    0xB3: "blablabla",
    0xC0: "blablabla",
    0xC1: "blablabla",
    0xC2: "blablabla",
    0xC3: "blablabla",
    0xC4: "blablabla",
    0xC5: "blablabla",
    0xC6: "blablabla",
    0xC7: "blablabla",
    0xC8: "blablabla",
    0xC9: "blablabla",
    0xF0: "blablabla",
        }

SENSOR_TYPES: Dict[bytearray, str] = {
    b'\x00': "not defined",
    b'\x01': "hydrophone",
    b'\x02': "geophone vertical",
    b'\x03': "geophone horizontal inline",
    b'\x04': "geophone horizontal crossline",
    b'\x05': "geophone horizontal other",
    b'\x06': "accelerometer vertical",
    b'\x07': "accelerometer horizontal inline",
    b'\x08': "accelerometer horizontal crossline",
    b'\x09': "accelerometer horizontal other",
    b'\x15': "electric dipole",
    b'\x16': "magnetic coil",
    }

# see segd doc p 39
HEADER_BLOCK_TYPES: Dict[int, str] = {
    0x02: "General Header 2",
    0x03: "General Header 3",
    0x10: "Vessel/Crew identification",
    0x11: "Survey Area Name",
    0x12: "Client Name",
    0x13: "Job Identification",
    0x14: "Line Identification",
    0x15: "Vibrator Source Information",
    0x16: "Explosive Source Information",
    0x17: "Airgun Source Information",
    0x18: "Watergun Source Information",
    0x19: "Electromagnetic Source",
    0x1f: "Other Source Type Information",
    0x20: "Additional Source Information",
    0x21: "Source Auxiliary Channel Reference",
    0x30: "Channel Set Description Block 1",
    0x31: "Channel Set Description Block 2",
    0x32: "Channel Set Description Block 3",
    0x40: "Trace Header Extension 1",
    0x41: "Sensor Info Header Extension Block",
    0x42: "Time Stamp Header Block",
    0x43: "Sensor Calibration Block",
    0x44: "Time Drift Block",
    0x45: "Electromagnetic Src/Recv Desc Block",
    0x50: "Position Block 1",
    0x51: "Position Block 2",
    0x52: "Position Block 3",
    0x55: "Coordinate Reference System Identification Block",
    0x56: "Relative Position Block",
    0x60: "Orientation Header Block",
    0x61: "Measurement Block",
    0x70: "General Trailer Description Block",
    # 0xb0 -> 0xff : "user defined header block"
    0xb0: "Sercel Segd Rev Block",
    0xb2: "Sercel Field Indentification Block",    
    0xbd: "Sercel Reserved Time Drift Block",    
    0xd2: "Sercel Systemld Block1",        
    0xd3: "Sercel Systemld Block2",            
    0xd4: "Sercel Systemld Block3",            
    0xd5: "Sercel Systemld Block4",                    
    }


def print_nested_dict(dct, indent=0):
    for key, val in dct.items():
        if isinstance(val, dict):
            print(" " * indent, key)
            print_nested_dict(val, indent + 4)
        else:
            print(" " * indent, key, val)


# ==========================
# GPS EPOCH expressed in UTC datetime
GPS_EPOCH = datetime.datetime(
    1980, 1, 6, tzinfo=datetime.timezone.utc)

def segd_timestamp(bytes_in: bytes) -> datetime.datetime:
    """
    A SEG-D Rev 3.0 timestamp is an 8 byte, signed, big-endian integer counting the number of microseconds since
    6 Jan 1980 00:00:00 (GPS epoch). The timestamp is equal to GPS time converted to microseconds.
    
    This function reads a number of microseconds since GPS_EPOCH
    And returns a datetime expressed in the UTC time reference
    The leap correction might not be implemented for dates older than 1980 or later than 2024/1/1
    """
    gps_microseconds = int.from_bytes(bytes_in, byteorder="big", signed=True)
    uncorrected_timestamp = GPS_EPOCH.timestamp() + float(gps_microseconds) / 1e6
    leap_correction_in_seconds = cumulative_leap_seconds(uncorrected_timestamp)
   
    gps_datetime = GPS_EPOCH + datetime.timedelta(seconds=gps_microseconds / 1e6)
    utc_datetime = GPS_EPOCH + datetime.timedelta(seconds=gps_microseconds / 1e6 - leap_correction_in_seconds)

    # print(f"{gps_datetime=} => {utc_datetime=}")
    # in 2023 : the following assertion must be verified!!!
    # assert utc_datetime.timestamp() + 18.0 == gps_datetime.timestamp()
    return utc_datetime

def _unpack_time_drift_header(trace_header_buffer: bytes) -> Dict[str, Any]:
    """
    according to segd rev 3 documentation, the time drift header should be stored in
    trace header block 0x44

    :param trace_header_buffer:
    :return time_drift_header:
    """

    time_drift_header = {}
    time_drift_header['time_of_deployment'] = segd_timestamp(trace_header_buffer[:8])
    time_drift_header['time_of_retrieval'] = segd_timestamp(trace_header_buffer[8:16])
    time_drift_header['time_offset_at_deployment_microsec'] = int.from_bytes(trace_header_buffer[16:20],
                                                                             byteorder="big", signed=True)
    time_drift_header['time_offset_at_retrieval_microsec'] = int.from_bytes(trace_header_buffer[20:24], byteorder="big",
                                                                            signed=True)
    time_drift_header['time_drift_corrected'] = int.from_bytes(trace_header_buffer[24:25], byteorder="big",
                                                               signed=False)
    time_drift_header['time_drift_correction_method'] = {
        0x00: "Uncorrected",
        0x01: "Linear Correction",  # (values in this header used)
        0xff: "Other, manufacturer defined method used for correction"
    }[int.from_bytes(trace_header_buffer[25:26], byteorder="big", signed=False)]
    return time_drift_header


def read_segd_rev3(segdfilename: str, verbose: int=0, headonly: bool=False)\
    -> List[Tuple[Dict[str, Any], np.ndarray]]:
    """
    Read segd rev3 file in python
    :param segdfilename: name of the segd file to read in
    :param verbose: 0 = off, 1 = extracted content only, >=2 debug
    :return traces: a list containing one tuple per trace in the file
        each tuple includes a dictionnary formatted like the "stats" attribute of obspy.core.trace.Trace objects
        and a numpy array
    """
    traces = []

    with open(segdfilename, 'rb') as fid:
        general_header_block1 = fid.read(32)
        general_header_block2 = fid.read(32)
        general_header_block3 = fid.read(32)

        # segd revision number
        segd_revision = float(
            f"{general_header_block2[10:11].hex()}.{general_header_block2[11:12].hex()}")
        assert segd_revision >= 3.0, segd_revision

        # additionnal blocks of the general header
        # right 4 bits of byte 11, usigned int
        number_of_additional_blocks_in_general_header = \
            int.from_bytes(bytes([general_header_block1[11] >> 4]), byteorder="big", signed=False)

        if number_of_additional_blocks_in_general_header == 15:
            # means F => then use ghb2
            number_of_additional_blocks_in_general_header = \
                int.from_bytes(general_header_block2[22:24], byteorder="big", signed=False)

        if verbose >= 2:
            print(f"{number_of_additional_blocks_in_general_header=}")

        #general_header_remaining_blocks = fid.read(32 * (number_of_additional_blocks_in_general_header - 2))
        time_drift_header = {}
        reserved_time_drift_header = {}
        for nblock in range(number_of_additional_blocks_in_general_header - 2):
            additionnal_header_block = fid.read(32)
            additionnal_header_block_type = \
                int.from_bytes(
                    additionnal_header_block[31:32], 
                    byteorder="big", 
                    signed=False)
            try:
                header_block_name = HEADER_BLOCK_TYPES[additionnal_header_block_type]
                
                if verbose >= 2:
                    print(f'additionnal general header block detected : '
                          f'{hex(additionnal_header_block_type)}:'
                          f'{header_block_name}')
                          
                if additionnal_header_block_type == 0x44:
                    time_drift_header = _unpack_time_drift_header(additionnal_header_block)

                elif additionnal_header_block_type == 0xbd:
                    reserved_time_drift_header = {
                        "freq_err_rate_at_deployment": int.from_bytes(
                            additionnal_header_block[16:20], 
                            byteorder="big", 
                            signed=True),
                        "freq_err_rate_at_retrieval": int.from_bytes(
                            additionnal_header_block[20:24], 
                            byteorder="big", 
                            signed=True)}
                    
                elif verbose >= 2:
                    print('not implemented')
                    
            except KeyError:
                if verbose >= 2:
                    print(f'additionnal general header block detected : '
                          f'{hex(additionnal_header_block_type)}: '
                          f'UNKNOWN HEADER TYPE')

        # number of scan types per record
        n_scan_type_per_record = int(general_header_block1[27:28].hex())
        if verbose >= 2:
            print(f"{n_scan_type_per_record=}")

        # number of channel sets per scan type
        h = general_header_block1[28:29].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[3:5], byteorder="big", signed=False)
            n_channel_sets_per_scan_type = h
        else:
            n_channel_sets_per_scan_type = int(h)
        if verbose >= 2:
            print(f"{n_channel_sets_per_scan_type=}")

        # number of 32 bytes extensions after each scan type header block
        h = general_header_block1[29:30].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[8:10], byteorder="big", signed=False)
            skew_extension_length = h * 32
        else:
            skew_extension_length = int(h) * 32
        if verbose >= 2:
            print(f"{skew_extension_length=}")

        # extended recording mode
        extended_recording_mode = \
            int.from_bytes(general_header_block3[29:30], byteorder="big", signed=False)
        if verbose >= 2:
            print(f"{extended_recording_mode=}")
        if extended_recording_mode:
            raise NotImplementedError('Extended recording mode not implemented')

        # relative time mode
        relative_time_mode = \
            int.from_bytes(general_header_block3[29:30], byteorder="big", signed=False)
        if verbose >= 2:
            print(f"{relative_time_mode=}")
            
        if relative_time_mode != 0:
            raise NotImplementedError('relative time mode not implemented')

        # ======================================
        general_header = {
            "segd_revision": segd_revision,
            'number_of_additional_blocks_in_general_header': number_of_additional_blocks_in_general_header,
            "time_drift_header": time_drift_header,
            "reserved_time_drift_header": reserved_time_drift_header,
            "n_scan_type_per_record": n_scan_type_per_record,
            "n_channel_sets_per_scan_type": n_channel_sets_per_scan_type,
            "skew_extension_length": skew_extension_length,
            "extended_recording_mode": extended_recording_mode,
            "relative_time_mode": relative_time_mode,
            }
        if verbose >= 1:
            print('# ################## GENERAL HEADER')
            print_nested_dict(general_header)

        # ======================================
        scan_type_headers = {}
        for n_scan_type in range(1, 1 + n_scan_type_per_record):
            # ========================
            # new scan type header
            scan_type_headers[n_scan_type] = {}

            for n_channel_set in range(1, 1 + n_channel_sets_per_scan_type):
                # new channel set in this scan type
                channel_set_descriptor = fid.read(96)  # WARNING IS 96 AFTER 3.0, WAS 32 BEFORE

                # ==
                # scan_type_number : identifies the number of the scan type
                # header to be described by the subsequent bytes
                scan_type_number = int(channel_set_descriptor[0:1].hex())
                # this channel set must belong to the current scan type
                assert scan_type_number == n_scan_type, (scan_type_number, n_scan_type)

                # ==
                # channel_set_number : identifies the channel set to be described in
                # the next 94 bytes within this scan type header.
                channel_set_number = int.from_bytes(channel_set_descriptor[1:3],
                                                    byteorder="big", signed=False)
                # this channel set must be the current channel set
                assert channel_set_number == n_channel_set, (channel_set_number, n_channel_set)
                scan_type_headers[scan_type_number][channel_set_number] = {}

                # ==
                scan_type_headers[scan_type_number][channel_set_number] \
                    ["channel_type_identification"] = CHANNEL_TYPE_IDENTIFICATIONS[int.from_bytes(channel_set_descriptor[3:4], byteorder="big", signed=False)]

                # ==
                scan_type_headers[scan_type_number][channel_set_number] \
                    ["channel_set_starttime_microsecond"] = \
                    int.from_bytes(channel_set_descriptor[4:8],
                                   byteorder="big", signed=True)
                if scan_type_headers[scan_type_number][channel_set_number] \
                    ["channel_set_starttime_microsecond"] != 0:
                    raise NotImplementedError('dont know what to do')
                scan_type_headers[scan_type_number][channel_set_number] \
                    ["channel_set_endtime_microsecond"] = \
                    int.from_bytes(channel_set_descriptor[8:12],
                                   byteorder="big", signed=True)
                if scan_type_headers[scan_type_number][channel_set_number] \
                    ["channel_set_endtime_microsecond"] != 0:
                    raise NotImplementedError('dont know what to do')
                # ==
                scan_type_headers[scan_type_number][channel_set_number]\
                    ["number_of_samples"] = \
                        int.from_bytes(channel_set_descriptor[12:16],
                                       byteorder="big", signed=False)
                # ==
                scan_type_headers[scan_type_number][channel_set_number] \
                    ["sample_descale_multiplication_factor"] = \
                        np.frombuffer(channel_set_descriptor[16:20],
                                      dtype=np.float32)[0]

                # ==
                # number of channels in this channel set
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
                array_forming = int.from_bytes(
                    channel_set_descriptor[26:27],
                    byteorder="big", signed=False)
                if array_forming == 0x01:
                    array_forming = "No array forming"
                elif 0x02 <= array_forming <= 0x0F:
                    array_forming = "%d groups summed, no weighting" % array_forming
                elif 0x10 <= array_forming <= 0x1F:
                    array_forming = "%d groups weighted, overlapping summation" % array_forming
                else:
                    raise ValueError(hex(array_forming))

                scan_type_headers[scan_type_number][channel_set_number] \
                    ["array_forming"] = array_forming

                # ==
                number_of_trace_header_extensions = \
                    int.from_bytes(channel_set_descriptor[27:28],
                                   byteorder="big", signed=False)
                assert number_of_trace_header_extensions != 0

                scan_type_headers[scan_type_number][channel_set_number] \
                    ["number_of_trace_header_extensions"] = \
                        number_of_trace_header_extensions

                # extended_header_flag
                # channel gain control method
                # vertical stack
                # stream cable number
                # header bloc type
                # alias filter freq
                # low cut filter setting
                # alias filter slope
                # low cut filter slope
                # not frequency setting
                # second notch frequency
                # third notch frequency
                # filter phase
                # physical unit
                # undefined
                # header block type
                # filter delay
                # description
                # header block type

            # ======================== last scan type is sample skew header
            sample_skew_header = fid.read(skew_extension_length)

        if verbose >= 2:
            print(scan_type_headers)

        # ======================================
        # extended header
        h = general_header_block1[30:31].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[5:8], byteorder="big", signed=False)
            extended_header_length = h * 32
        else:
            extended_header_length = int(h) * 32

        if verbose >= 2:
            print(f"{extended_header_length=}")
        fid.read(extended_header_length)

        # ======================================
        # external header
        h = general_header_block1[31:32].hex()
        if h == "ff":
            h = int.from_bytes(general_header_block2[27:30], byteorder="big", signed=False)
            external_header_length = h * 32
        else:
            external_header_length = int(h) * 32
        if verbose >= 2:
            print(f"{external_header_length=}")
        fid.read(external_header_length)

        # ====================================== traces
        for scan_type_number, scan_type_header in scan_type_headers.items():
            if verbose >= 2:
                print(f"# ######### {scan_type_number=}")
            for channel_set_number, channel_set_descriptor in scan_type_header.items():

                if verbose  >= 2:
                    print(f"# ========= {channel_set_number=}")
                    
                delta = channel_set_descriptor["sampling_interval_microsec"] * 1e-6
                npts = channel_set_descriptor['number_of_samples']

                for channel_number in range(channel_set_descriptor["number_of_channels"]):
                    if verbose >= 2:
                        print(f"# --------- {channel_number=}")

                    # =========== trace header
            
                    # ========= demux trace header
                    demux_trace_header = fid.read(20)
                    file_number = demux_trace_header[0:2].hex()
                    if file_number == "ffff":
                        file_number = int.from_bytes(demux_trace_header[17:20], byteorder="big", signed=False)
                    else:
                        file_number = int(file_number)  # bcd
                    if verbose >= 2:
                        print(f"{file_number=}")

                    # scan type number
                    scan_type_number = int(demux_trace_header[2:3].hex())  # bcd
                    if verbose >= 2:
                        print(f'{scan_type_number=}')

                    # channel set number
                    channel_set_number = demux_trace_header[3:4].hex()
                    if channel_set_number == "ff":
                        channel_set_number = int.from_bytes(demux_trace_header[15:17], byteorder="big", signed=False)
                    else:
                        channel_set_number = int(channel_set_number)
                    if verbose >= 2:
                        print(f"{channel_set_number=}")

                    trace_number = demux_trace_header[4:6].hex()
                    if trace_number == "ffff":
                        pass  # not in this header, see Extended Trace Number (byte 22–24 of Trace Header Extension)
                    else:
                        trace_number = int(trace_number)
                    if verbose >= 2:
                        print(f"{trace_number=}")

                    first_timing_word = demux_trace_header[6:9]
                    if first_timing_word != b"\x00" * 3:
                        print(first_timing_word)
                        raise NotImplementedError(r'first_timing_word != \x00\x00\x00 not implemented')

                    number_of_trace_header_extensions = int.from_bytes(
                        demux_trace_header[9:10], byteorder="big", signed=False)
                    assert number_of_trace_header_extensions == \
                           scan_type_headers\
                               [scan_type_number]\
                                   [channel_set_number]\
                                       ["number_of_trace_header_extensions"]

                    sample_skew = demux_trace_header[10]
                    if sample_skew != 0:
                        print(sample_skew)
                        raise NotImplementedError(r'sample_skew != \x00 not implemented')

                    # trace_edit
                    # time break window
                    # extended channel set number
                    # extended file number
                    
                    # ========= trace header extension block 1
                    trace_header_extension1 = fid.read(32)

                    receiver_line_number = int.from_bytes(trace_header_extension1[0:3], byteorder="big", signed=True)
                    if verbose >= 2:
                        print(f"{receiver_line_number=}")

                    receiver_point_number = int.from_bytes(trace_header_extension1[3:6], byteorder="big", signed=True)
                    # print(f"receiver_point_number={receiver_point_number}")

                    receiver_point_index = int.from_bytes(trace_header_extension1[6:7], byteorder="big", signed=True)
                    # print(f"receiver_point_number={receiver_point_index}")

                    # reshoot_index
                    # group_index
                    # depth_index
                    # extended_receiver_line_number
                    # extended_receiver_point
                    sensor_type = SENSOR_TYPES[trace_header_extension1[20:21]]
                    if verbose >= 2:
                        print(f'{sensor_type=}')

                    extended_trace_number = int.from_bytes(trace_header_extension1[21:24], byteorder="big", signed=True)
                    if trace_number == "ffff":
                        trace_number = extended_trace_number
                    if verbose >= 2:
                        print(f'{trace_number=}')

                    # number of samples in this trace => why not using the channel set descriptor?
                    number_of_samples = int.from_bytes(trace_header_extension1[24:28], byteorder="big", signed=False)
                    assert number_of_samples == channel_set_descriptor['number_of_samples']
                    # if verbose >= 2:
                    #     print(f"number_of_samples={number_of_samples}")

                    # sensor moving
                    # undefined
                    # physical unit
                    header_block_type = int.from_bytes(trace_header_extension1[31:32], byteorder="big", signed=False)
                    assert header_block_type == 0x40  # i.e. 64
                    if verbose >= 2:
                        print(f"{header_block_type=}, {HEADER_BLOCK_TYPES[header_block_type]=}")

                    # ========= optionnal blocks (see section 5.0 header blocks)
                    # remaining trace header extension blocks (extension 1 already read)
                    # remaining_trace_header = fid.read((channel_set_descriptor["number_of_trace_header_extensions"]-1) * 32)
                    sensor_info_header_extension = {}
                    timestamp_header = {}
                    sensor_calibration_header = {}
                    time_drift_header = {}
                    orientation_header = {}
                    measurement_block_header = {}

                    for optional_trace_header_number in range(1, channel_set_descriptor["number_of_trace_header_extensions"]):

                        # 0 = trace_header_extension1
                        trace_header_buffer = fid.read(32)
                        trace_header_block_type = \
                            int.from_bytes(
                                trace_header_buffer[31:32], 
                                byteorder="big", 
                                signed=False)

                        if verbose >= 2:
                            print(f"trace_header_block_type={hex(trace_header_block_type)}")

                        if trace_header_block_type == 0x40:
                            raise ValueError('optional trace header was of type 0x40 (trace header extension #1)')

                        elif trace_header_block_type == 0x41:
                            # sensor_info_header_extension[''] =
                            # sensor_info_header_extension[''] =
                            pass

                        elif trace_header_block_type == 0x42:
                            # TODO : implement sample_skew (fraction of dt to shift the first sample)
                            # TODO : first_timing_word (??)

                            timestamp_header['time_zero'] = segd_timestamp(trace_header_buffer[:8])
                            # timestamp_header['sample_skew'] = ...
                            # timestamp_header['first_timing_word'] = ...
                            timestamp_header['starttime'] = timestamp_header['time_zero'].timestamp()

                        elif trace_header_block_type == 0x43:
                            # trace_header_buffer
                            # sensor_calibration_header[''] =
                            # sensor_calibration_header[''] =
                            pass

                        elif trace_header_block_type == 0x44:
                            # trace_header_buffer
                            time_drift_header = _unpack_time_drift_header(trace_header_buffer)
                            if verbose >= 2:
                                print(f"{time_drift_header=}")

                        elif 0x50 <= trace_header_block_type <= 0x52:
                            #position block 1-2-3
                            pass

                        elif trace_header_block_type == 0x60:
                            # trace_header_buffer
                            orientation_header['rot_angle_around_X_rad'] = np.frombuffer(trace_header_buffer[:4], dtype=">f4")
                            # orientation_header[''] =
                            # orientation_header[''] =
                            pass

                        elif trace_header_block_type == 0x61:
                            # trace_header_buffer
                            # measurement_block_header['
                            # measurement_block_header[''] =
                            # measurement_block_header[''] =
                            pass

                        elif 0xb0 <= trace_header_block_type <= 0xff:
                            # user defined header block
                            if verbose >= 2:
                                print(f'User defined trace header block detected '
                                      f'(code {hex(trace_header_block_type)})')

                            # if trace_header_block_type in [0xb8, 0xb9, 0xbe, 0xbf]: #0xb8:
                            #     print(trace_header_buffer)
                            #     # xb8 = b'                               \xb8'
                            #     # xb9 = b'\x07\x01\x02\x01\x00\x00\x00\x1d1\x85\x00\x07\x01\x00\x1d1\x85\x00\x00\x01R\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb9'
                            #     # xbe = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\xbe'
                            #     # xbf = b'\x00\x04\xe5\xac\xd5\x0e\xdf\xa0\xc0%m\xe1\xbbau;<\xc6UP\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xbf'
                            #     for i in range(32):
                            #         try:
                            #             print("azerty", hex(trace_header_block_type), i, segd_timestamp(trace_header_buffer[i:i+8]))
                            #         except:
                            #             pass
                        else:

                            raise NotImplementedError(trace_header_block_type, hex(trace_header_block_type))
                            # ... TODO
                            pass
                    if verbose >= 2:
                        print(sensor_info_header_extension)
                        print(timestamp_header)
                        print(sensor_calibration_header)
                        print(time_drift_header)
                        print(orientation_header)
                        print(measurement_block_header)

                    trace_header = {
                        "starttime": timestamp_header['starttime'],  # float
                        "npts": npts,   # int
                        "delta": delta,    # float in sec
                        "segd": {
                            "segd_revision": segd_revision,
                            "receiver_line_number": receiver_line_number,
                            "receiver_point_number": receiver_point_number,
                            "scan_type_number": scan_type_number,
                            "channel_set_number": channel_set_number,
                            "channel_number": channel_number,
                            "trace_number": trace_number,
                            "first_timing_word": first_timing_word,
                            "number_of_trace_header_extensions": number_of_trace_header_extensions,
                            "sample_skew": sample_skew,
                            "receiver_line_number": receiver_line_number,
                            "receiver_point_number": receiver_point_number,
                            "receiver_point_index": receiver_point_index,
                            "reshoot_index": "not implemented yet",
                            "group_index": "not implemented yet",
                            "depth_index": "not implemented yet",
                            "extended_receiver_line_number": "not implemented yet",
                            "extended_receiver_point": "not implemented yet",
                            "sensor_type": sensor_type,
                            "sensor_info_header_extension": sensor_info_header_extension,
                            "timestamp_header": timestamp_header,
                            "sensor_calibration_header": sensor_calibration_header,
                            "time_drift_header": time_drift_header,
                            "orientation_header": orientation_header,
                            "measurement_block_header": measurement_block_header,
                            }}
                    if verbose >= 1:
                        print('# ################## TRACE HEADER')
                        print_nested_dict(trace_header)

                    # data type assumed to be >f4...
                    buff = fid.read(channel_set_descriptor["number_of_samples"] * 4)
                    if not headonly:
                        trace_data = \
                            np.frombuffer(buff, dtype=">f4")
                    else:
                        trace_data = np.array([])
                    if verbose >= 1:
                        print('# ================== TRACE DATA')
                        print(trace_data.shape)
                        print(trace_data.dtype)
                        print(trace_data[:10], "...")                        
                    traces.append((trace_header, trace_data))
        return general_header, traces


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    general_header, traces = read_segd_rev3(sys.argv[1], verbose=1)

    if "--show" in sys.argv[1:]:
        from matplotlib.collections import LineCollection
        segments: List[np.ndarray] = []

        for n, (trace_header, trace_data) in enumerate(traces):
            t = np.arange(trace_header['npts']) * trace_header['delta']
            d = trace_data
            d = 0.1 * d / np.std(d) + n  # for display
            segments.append(np.column_stack((t, d)))

        lc = LineCollection(segments, color="k", alpha=0.3)
        plt.gca().add_collection(lc)
        plt.gca().set_xlim((t.min(), t.max()))
        plt.gca().set_ylim((-1, n+1))
        plt.show()

