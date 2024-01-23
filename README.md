# PYSEGD3 

Standalone package to read/write segd rev3 files in python

## Install 

`pip install pysegd3` 

## Usages
### Load a segd rev 3 file
```python
from pysegd3.readsegd3 import read_segd_rev3

for (trace_header, trace_data) in read_segd_rev3(segdfilename):
    print(trace_header)  # a python dictionnary built like obspy trace stats header
    print(trace_data)  # a numpy array
```

### Load as an obspy stream
Obspy is not included in this package
```bash
pip install obspy
```

```python
from pysegd3.readsegd3_as_obspy import read_segd_rev3_as_obspy

stream = read_segd_rev3_as_obspy(segdfilename)
print(stream)
```

