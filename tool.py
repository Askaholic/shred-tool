#! /usr/bin/env python

import sys
import os.path
import random
import math

DELETE = False
EXACT = False
PASSES = 5
VERBOSE = False
WRITE_ZEROES = False
GUTMANN = False

def printHelp():
	print "usage:\ttool filename {arguments}\n"
	print "\t-g, --gutmann\t\tUse the Gutmann 35-pass method"
	print "\t-n, --iterations\tSet the number of passes to write random data"
	print "\t-u\t\t\tDelete the file"
	print "\t-v, --verbose\t\tEnable verbose output"
	print "\t-x, --exact\t\tDo not round up to the next full block size"
	print "\t-z, --zero\t\tWrite a final pass of zeros"
	print "\t-h, --help\t\tDisplay help"
	quit()

def writeZeroes(file, size):
	if VERBOSE:
		print "Writing zeroes..."
	writeBytes(file, size, "\x00")
	if VERBOSE:
		print "Writing zeroes completed"

def writeRandom(file, size, passes):
	if VERBOSE and PASSES > 0:
		print "Writing " + str(passes) + " passes of random data..."
	writeRandomQuiet(file, size, passes)
	if VERBOSE:
		print "Writing random data completed"

def writeRandomQuiet(file, size, passes):
	for i in range(0, passes):
		file.seek(0,0)
		try:
			file.write(os.urandom(size))
		except NotImplementedError:
			for i in range(0, size):
				value = random.randint(0, 255)
				file.write(str(chr(value)))

def writeBytes(file, size, byte):
	file.seek(0,0)
	for i in range(0, size):
		file.write(byte)
		
def writeBytePattern(file, size, bytePattern):
	file.seek(0,0)
	bytePatternIndex = 0;
	bytePatternLength = len(bytePattern)
	for i in range(0, size):
		file.write(bytePattern[bytePatternIndex])
		bytePatternIndex = (bytePatternIndex + 1) % bytePatternLength

def writeGutmann(file, size):
	if VERBOSE:
		print "Using Gutmann 35-pass method..."
	writeRandomQuiet(file, size, 4)
	writeBytes(file, size, "\x55")
	writeBytes(file, size, "\xAA")
	writeBytePattern(file, size, ["\x92", "\x49", "\x24"])
	writeBytePattern(file, size, ["\x49", "\x24", "\x92"])
	writeBytePattern(file, size, ["\x24", "\x92", "\x49"])
	i = 0
	while (i < 256):
		writeBytes(file, size, chr(i))
		i = i + 17
	writeBytePattern(file, size, ["\x92", "\x49", "\x24"])
	writeBytePattern(file, size, ["\x49", "\x24", "\x92"])
	writeBytePattern(file, size, ["\x24", "\x92", "\x49"])
	writeBytePattern(file, size, ["\x6D", "\xB6", "\xDB"])
	writeBytePattern(file, size, ["\xB6", "\xDB", "\x6D"])
	writeBytePattern(file, size, ["\xDB", "\x6D", "\xB6"])
	writeRandomQuiet(file, size, 4)
	if VERBOSE:
		print "35-pass complete"

# Make sure that there is a file name
arglen = len(sys.argv)
if arglen <= 1:
	print "You must give a file name"
	quit()
	
if sys.argv[1] == "--help":
	printHelp()
	
file_name = sys.argv[1]

# Parse additional arguments
if arglen > 2:
	for i in range (2, arglen):
		arg = sys.argv[i]
		if arg[0] == '-':
			if arg[1] == '-':
				# Single options
				if arg == "--zero":
					WRITE_ZEROES = True
				elif arg == "--iterations":
					PASSES = int(sys.argv[i + 1])
					i += 1
				elif arg == "--exact":
					EXACT = True
				elif arg == "--gutmann":
					GUTMANN = True
				elif arg == "--verbose":
					VERBOSE = True
				elif arg == "--help":
					printHelp()
				else:
					print "Unrecognized argument: " + arg
					printHelp()
			# Single flags that take arguments
			elif arg == "-n":
					PASSES = int(sys.argv[i + 1])
					i += 1
			else:
				for c in range(1, len(arg)):
					# Multiple flags
					if arg[c] == 'z':
						WRITE_ZEROES = True
					elif arg[c] == 'x':
						EXACT = True
					elif arg[c] == 'u':
						DELETE = True
					elif arg[c] == 'g':
						GUTMANN = True
					elif arg[c] == 'v':
						VERBOSE = True
					elif arg[c] == 'h':
						printHelp()
					else:
						print "Unrecognized flag: -" + arg[c]
						printHelp()
		
# Check if file exists
if not os.path.isfile(file_name):
	print "File: '" + file_name + "' does not exist"
	if file_name[0] == '-':
		print "\tTry --help"
	quit()

file_stats = os.stat(file_name)
bytes_to_write = file_stats.st_size

if not EXACT:
	bytes_to_write = int(math.ceil(float(file_stats.st_size)/file_stats.st_blksize)) * file_stats.st_blksize

if VERBOSE:
	print "Destroying: " + file_name
	print "File size: " + str(file_stats.st_size)
	print "Bytes to overwrite: " + str(bytes_to_write)

file = open(file_name, "rb+", 1)

if GUTMANN:
	writeGutmann(file, bytes_to_write)
else:
	writeRandom(file, bytes_to_write, PASSES)
		
	if WRITE_ZEROES:
		writeZeroes(file, bytes_to_write)
	
file.close()

if DELETE:
	if VERBOSE:
		print "Removing file..."
	os.remove(file_name)
	if VERBOSE:
		print "Removed file succesfully"