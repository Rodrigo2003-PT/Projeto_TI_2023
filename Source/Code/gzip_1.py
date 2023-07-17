# Author: Marco Simoes
# Adapted from Java's implementation of Rui Pedro Paiva
# Teoria da Informacao, LEI, 2022

import sys
from huffmantree import HuffmanTree


class GZIPHeader:
	''' class for reading and storing GZIP header fields '''

	ID1 = ID2 = CM = FLG = XFL = OS = 0
	MTIME = []
	lenMTIME = 4
	mTime = 0

	# bits 0, 1, 2, 3 and 4, respectively (remaining 3 bits: reserved)
	FLG_FTEXT = FLG_FHCRC = FLG_FEXTRA = FLG_FNAME = FLG_FCOMMENT = 0   
	
	# FLG_FTEXT --> ignored (usually 0)
	# if FLG_FEXTRA == 1
	XLEN, extraField = [], []
	lenXLEN = 2
	
	# if FLG_FNAME == 1
	fName = ''  # ends when a byte with value 0 is read
	
	# if FLG_FCOMMENT == 1
	fComment = ''   # ends when a byte with value 0 is read
		
	# if FLG_HCRC == 1
	HCRC = []
		
		
	
	def read(self, f):
		''' reads and processes the Huffman header from file. Returns 0 if no error, -1 otherwise '''

		# ID 1 and 2: fixed values
		self.ID1 = f.read(1)[0]  
		if self.ID1 != 0x1f: return -1 # error in the header
			
		self.ID2 = f.read(1)[0]
		if self.ID2 != 0x8b: return -1 # error in the header
		
		# CM - Compression Method: must be the value 8 for deflate
		self.CM = f.read(1)[0]
		if self.CM != 0x08: return -1 # error in the header
					
		# Flags
		self.FLG = f.read(1)[0]
		
		# MTIME
		self.MTIME = [0]*self.lenMTIME
		self.mTime = 0
		for i in range(self.lenMTIME):
			self.MTIME[i] = f.read(1)[0]
			self.mTime += self.MTIME[i] << (8 * i) 				
						
		# XFL (not processed...)
		self.XFL = f.read(1)[0]
		
		# OS (not processed...)
		self.OS = f.read(1)[0]
		
		# --- Check Flags
		self.FLG_FTEXT = self.FLG & 0x01
		self.FLG_FHCRC = (self.FLG & 0x02) >> 1
		self.FLG_FEXTRA = (self.FLG & 0x04) >> 2
		self.FLG_FNAME = (self.FLG & 0x08) >> 3
		self.FLG_FCOMMENT = (self.FLG & 0x10) >> 4
					
		# FLG_EXTRA
		if self.FLG_FEXTRA == 1:
			# read 2 bytes XLEN + XLEN bytes de extra field
			# 1st byte: LSB, 2nd: MSB
			self.XLEN = [0]*self.lenXLEN
			self.XLEN[0] = f.read(1)[0]
			self.XLEN[1] = f.read(1)[0]
			self.xlen = self.XLEN[1] << 8 + self.XLEN[0]
			
			# read extraField and ignore its values
			self.extraField = f.read(self.xlen)
		
		def read_str_until_0(f):
			s = ''
			while True:
				c = f.read(1)[0]
				if c == 0: 
					return s
				s += chr(c)
		
		# FLG_FNAME
		if self.FLG_FNAME == 1:
			self.fName = read_str_until_0(f)
		
		# FLG_FCOMMENT
		if self.FLG_FCOMMENT == 1:
			self.fComment = read_str_until_0(f)
		
		# FLG_FHCRC (not processed...)
		if self.FLG_FHCRC == 1:
			self.HCRC = f.read(2)
			
		return 0
			



class GZIP:
	''' class for GZIP decompressing file (if compressed with deflate) '''

	gzh = None
	gzFile = ''
	fileSize = origFileSize = -1
	numBlocks = 0
	f = None
	

	bits_buffer = 0
	available_bits = 0		

	
	def __init__(self, filename):
		self.gzFile = filename
		self.f = open(filename, 'rb')
		self.f.seek(0,2)
		self.fileSize = self.f.tell()
		self.f.seek(0)

		
	

	def decompress(self):
		''' main function for decompressing the gzip file with deflate algorithm '''
		
		numBlocks = 0

		# get original file size: size of file before compression
		origFileSize = self.getOrigFileSize()
		print(origFileSize)
		
		# read GZIP header
		error = self.getHeader()
		if error != 0:
			print('Formato invalido!')
			return
		
		# show filename read from GZIP header
		print(self.gzh.fName)
		
		
		# MAIN LOOP - decode block by block
		BFINAL = 0	
		while not BFINAL == 1:	
			
			BFINAL = self.readBits(1)
							
			BTYPE = self.readBits(2)					
			if BTYPE != 2:
				print('Error: Block %d not coded with Huffman Dynamic coding' % (numBlocks+1))
				return
			

			# ================ Exercicio 1 ======================
			hlit = self.readBits(5)
			hdist = self.readBits(5)
			hclen = self.readBits(4)

			print("hlit", hlit)
			print("hdist", hdist)
			print("hclen", hclen)


			# ================ Exercicio 2 ======================
			order_list = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 12, 2, 14, 1, 15]
			lengths = [0 for _ in range(len(order_list))]

			for i in range(hclen + 4):
				lengths[order_list[i]] = self.readBits(3)

			print("lengths: ", lengths)


			# ================= Exercicio 3 ========================
			def bounds(lenghts):
				"""Calculate min and max of an array."""
				for elem in lenghts:
					if elem != 0:
						min = max = elem
						break

				for elem in lenghts:
					if elem != 0 and elem < min:
						min = elem
					elif elem > max:
						max = elem

				return min, max

			def occurencies(lengths, min, max):
				"""Calculate all occurencies of a length."""
				count = [0 for _ in range(min, max + 1)]

				for elem in lengths:
					if elem != 0:
						count[elem - min] += 1

				return count

			def generate_codes(min, max, count, lengths):
				"""Generate all codes."""
				number = 0
				bin_codes = []

				for i in range(min, max + 1):
					number = number << 1
					for _ in range(count[i - min]):
						code = bin(number)[2:]
						if len(code) != i:
							code = '0' * (i - len(code)) + code

						bin_codes.append(code)
						number = number + 1

				codes = [i for i in range(len(lengths))]
				for i in codes:
					for k in range(len(bin_codes)):
						if len(bin_codes[k]) == lengths[i]:
							codes[i] = bin_codes[k]
							bin_codes[k] = ""
							break

				for i in range(len(codes)):
					if len(str(codes[i])) < min:
						codes[i] = ""

				return codes


			min, max = bounds(lengths)
			count = occurencies(lengths, min, max)
			codes = generate_codes(min, max, count, lengths)

			# Print codes
			for i in range(len(codes)):
				print("Symbol: ", i, "code: ", codes[i])

			hft = HuffmanTree()
			verbose = True
			for i in range(len(codes)):
				if codes[i] != "":
					hft.addNode(codes[i], i, verbose)


			# ================== Exercicio 4 e 5 =========================
			def read_huffman_trees(hft, codes, hlen, hlit=True):

				if hlit:
					ll = 257
				else:
					ll = 1

				h_list = [-1 for _ in range(hlen + ll)]
				i = 0
				while i < hlen + 257:
					if hlit and i >= hlen + 257:
						break
					elif not hlit and i >= hlen + 1:
						break

					code = ""
					p = -2
					hft.resetCurNode()
					while p == -2:
						new_bit = self.readBits(1)
						code += str(new_bit)
						p = hft.nextNode(str(new_bit))

					if codes.index(code) > -1:
						if codes.index(code) == 16:
							bit = self.readBits(2)
							for j in range(bit + 3 + 1):
								h_list[i + j] = h_list[i - 1]
							i += bit + 3

						elif codes.index(code) == 17:
							bit = self.readBits(3)
							for j in range(bit + 3 + 1):
								h_list[i + j] = 0
							i += bit + 3

						elif codes.index(code) == 18:
							bit = self.readBits(7)
							for j in range(bit + 11 + 1):
								h_list[i + j] = 0
							i += bit + 11

						elif codes.index(code) < 16:
							h_list[i] = codes.index(code)
							i += 1

					elif codes.index(code) == -1:
						h_list[i] = 0
						i += 1

				return h_list

			list_hliterais = read_huffman_trees(hft, codes, hlit)
			print("literals: ", list_hliterais)

			list_hdist = read_huffman_trees(hft, codes, hdist, False)
			print("distancias: ", list_hdist)


			# ===================== Exercicio 6 ==========================
			min, max = bounds(list_hdist)
			count = occurencies(list_hdist, min, max)
			hdist_codes = generate_codes(min, max, count, list_hdist)

			# Print codes
			for i in range(len(hdist_codes)):
				print("Symbol: ", i, "code: ", hdist_codes[i])

			min, max = bounds(list_hliterais)
			count = occurencies(list_hliterais, min, max)
			hliterals_codes = generate_codes(min, max, count, list_hliterais)
			for i in range(len(hliterals_codes)):
				print("Symbol: ", i, "code: ", hliterals_codes[i])

			hft_literals = HuffmanTree()
			for i in range(len(hliterals_codes)):
				if hliterals_codes[i] != "":
					hft_literals.addNode(hliterals_codes[i], i, verbose)

			hft_dist = HuffmanTree()
			for i in range(len(hdist_codes)):
				if hdist_codes[i] != "":
					hft_dist.addNode(hdist_codes[i], i, verbose)

			# Exercicio 7
			text = []
			bits = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0]
			length = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258]
			dist = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049,3073, 4097,6145, 8193, 12289, 16385, 24577]
			bits2 = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13]

			while True:
				node = self.search_node(hft_literals)

				if 0 <= node < 256:
					text.append(node)
				elif node == 256:
					print("FINISHED")
					break
				elif 256 < node < 286:
					pos = node - 257
					bit = self.readBits(bits[pos])
					comp = length[pos] + bit

					node = self.search_node(hft_dist)

					bit = self.readBits(bits2[node])
					distancia = dist[node] + bit

					ll = len(text)
					for i in range(comp):
						text.append(text[ll - distancia + i])

				else:
					print("ERROR")
					break

			
			# ================= Exercicio 8 =======================
			for i in range(len(text)):
				text[i] = chr(text[i])

			file = open("output.txt", "w")
			for elem in text:
				file.write(elem)
			file.close()

			# update number of blocks read
			numBlocks += 1

		# close file			
		
		self.f.close()	
		print("End: %d block(s) analyzed." % numBlocks)


	def search_node(self, huffman_tree):
		node = -1

		while node == -1 or node == -2:
			code = str(self.readBits(1))
			node = huffman_tree.nextNode(code)

		huffman_tree.resetCurNode()
		return node
	
	
	def getOrigFileSize(self):
		''' reads file size of original file (before compression) - ISIZE '''
		
		# saves current position of file pointer
		fp = self.f.tell()
		
		# jumps to end-4 position
		self.f.seek(self.fileSize-4)
		
		# reads the last 4 bytes (LITTLE ENDIAN)
		sz = 0
		for i in range(4): 
			sz += self.f.read(1)[0] << (8*i)
		
		# restores file pointer to its original position
		self.f.seek(fp)
		
		return sz		
	

	
	def getHeader(self):  
		''' reads GZIP header'''

		self.gzh = GZIPHeader()
		header_error = self.gzh.read(self.f)
		return header_error
		

	def readBits(self, n, keep=False):
		''' reads n bits from bits_buffer. if keep = True, leaves bits in the buffer for future accesses '''

		while n > self.available_bits:
			self.bits_buffer = self.f.read(1)[0] << self.available_bits | self.bits_buffer
			self.available_bits += 8
		
		mask = (2**n)-1
		value = self.bits_buffer & mask

		if not keep:
			self.bits_buffer >>= n
			self.available_bits -= n

		return value


if __name__ == '__main__':

	# gets filename from command line if provided
	filename = "FAQ.txt.gz"
	if len(sys.argv) > 1:
		fileName = sys.argv[1]			

	# decompress file
	gz = GZIP(fileName)
	gz.decompress()
	