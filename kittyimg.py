#!/bin/python

import sys
import PIL.Image
import base64
from tempfile import NamedTemporaryFile
import codecs

def format_cmd_str(cmd, payload=None, max_slice_len=2048):
	central_blk = ','.join(["{}={}".format(k, v) for k, v in cmd.items()]).encode('ascii')
	if payload is not None:
		# we add the m key to signal a multiframe communication
		# appending the end (m=0) key to a single message has no effect
		while len(payload) > max_slice_len:
			payload_blk, payload = payload[:max_slice_len], payload[max_slice_len:]
			yield protocol_start + central_blk + b',m=1;' + payload_blk + protocol_end
		yield protocol_start + central_blk + b',m=0;' + payload + protocol_end
	else:
		yield protocol_start + central_blk + b';' + protocol_end


# we are going to use stdio in binary mode a lot, so due to py2 -> py3
# differnces is worth to do this:
stdbout = getattr(sys.stdout, 'buffer', sys.stdout)
#stdbin = getattr(sys.stdin, 'buffer', sys.stdin)
stream = False
path = sys.argv[1]
backend = PIL.Image
image_id = 0
protocol_start = b'\x1b_G'
protocol_end = b'\x1b\\'
image = backend.open(path)
cmds = {'a': 'T', 'i': image_id, 'q': 2}

try:
	fsenc = sys.getfilesystemencoding()  # returns None if standard utf-8 is used
	# throws LookupError if can't find the codec, TypeError if fsenc is None
	codecs.lookup(fsenc)
except (LookupError, TypeError):
	fsenc = 'utf-8'

if image.mode != 'RGB' and image.mode != 'RGBA':
	image = image.convert('RGB')

if image.format == 'PNG':
#	if stream:
#		# NOT WORKING!!!!
#		cmds.update({'t': 'd', 'f': 100, })
#		payload = base64.standard_b64encode(bytearray().join(map(bytes, image.getdata())))
#	else:
	cmds.update({'t': 'f', 'f': 100, })
	payload = base64.standard_b64encode(path.encode(fsenc))
else:
	if stream:
		cmds.update({'t': 'd', 'f': len(image.getbands()) * 8,
			's': image.width, 'v': image.height, })
		payload = base64.standard_b64encode(bytearray().join(map(bytes, image.getdata())))
	else:
		cmds.update({'t': 't', 'f': 100, })
		with NamedTemporaryFile(prefix='kittyimg_thumb_', suffix='.png', delete=False) as tmpf:
			image.save(tmpf, format='png', compress_level=0)
			payload = base64.standard_b64encode(tmpf.name.encode(fsenc))

for cmd_str in format_cmd_str(cmds, payload=payload):
	stdbout.write(cmd_str)

image.close()
