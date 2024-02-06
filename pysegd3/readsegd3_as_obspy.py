#!/usr/bin/env python

"""
Copyright (C) 2024  maximilien.lehujeur
segd3 -> obspy converter 
Note : obspy is not a dependency of this package, install it manually
"""

import sys
from pysegd3.readsegd3 import read_segd_rev3
try:
    from obspy.core.stream import Stream
    from obspy.core.trace import Trace
    from obspy.core.utcdatetime import UTCDateTime

except ImportError:
    raise ImportError('obspy is not installed, please install it separately')
    

def read_segd_rev3_as_obspy(filename: str, verbose: bool=False, headonly: bool=False)\
    -> "obspy.core.stream.Stream":
    """ 
    read a segd file and pack it into a obspy Stream
    """
    if headonly:
        raise NotImplementedError  # TODO
        
    general_header, trace_info_list = read_segd_rev3(filename, verbose=verbose, headonly=headonly)
    
    stream = Stream()
    stream.stats = general_header
    for trace_header, trace_data in trace_info_list:
        trace = Trace(trace_data)  # < can we just put stats here? not sure in headonly mode
        trace_header['starttime'] = UTCDateTime(trace_header['starttime'])  # to obspy format

        for k, v in trace_header.items():
            # be carefull whit headonly, not tested
            trace.stats[k] = v
        stream.append(trace)

    return stream


if __name__ == "__main__":

    stream = read_segd_rev3_as_obspy(
                filename=sys.argv[1],
                verbose=True, headonly=False)

    for trace in stream:
        print('# ----------------------------')
        print(trace)
        print(trace.stats)
        
