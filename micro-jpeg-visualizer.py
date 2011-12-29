# Written by Raul Aguaviva as an exercise
# beware not optimized for speed or clarity :-)

from struct import *
import math 

zigzag = [0,  1,  8, 16,  9,  2,  3, 10,
	17, 24, 32, 25, 18, 11,  4,  5,
	12, 19,	26, 33, 40, 48, 41, 34,
	27, 20, 13,  6,  7, 14, 21, 28,
	35, 42, 49, 56, 57, 50, 43, 36,
	29, 22, 15, 23, 30, 37, 44, 51,
	58, 59, 52, 45, 38, 31, 39, 46,
	53, 60, 61, 54, 47, 55, 62, 63]


def hexdump(data):
	for i in range(len(data)):
		print "%x" % unpack("B",data[i]),
	print

def GetArray(type,l, length):
	s = ""
	for i in range(length):
		s =s+type
	return	list(unpack(s,l[:length]))

def UnZigZag( l ):
	o = [0] *64
	for i in range(64):
		o[zigzag[i]]=l[i]
	return o
	
def PrintMatrix( m):
	for j in range(8):
		for i in range(8):
			print "%2f" % m[i+j*8],
		print

def DrawMatrix(x, y, mat):
	size = 3
	j = 0
	for yy in range(8):
		for xx in range(8):
			#print mat[j]
			c = "%02x" % (mat[j]+128)
			j+=1
			w.create_rectangle((x*8+xx)*3, (y*8+yy)*3, (x*8+(xx+1))*3, (y*8+(yy+1))*3, fill="#"+c+c+c)

def RemoveFF00(data):
	datapro = []
	i = 0
	while(True):
		b, = unpack("B",data[i])		
		if (b == 0xff):
			bb, = unpack("B",data[i+1])		
			if (bb == 0):
				datapro.append(data[i])
				i+=1
			else:
				break
		else:
			datapro.append(data[i])
		i+=1
	return datapro

class IDCT:
	def __init__(self):
		self.base = [0]*64

	def NormCoeff(self, n):
		if n ==0:			
			return math.sqrt( 1.0/8.0)
		return math.sqrt( 2.0/8.0)

	def Add(self, n,m, coeff):
		mat = []

		an = self.NormCoeff(n)
		am = self.NormCoeff(m)
				
		for y in range(0,8):			
			for x in range(0,8):
				nn = an*math.cos( n* math.pi * (x +.5)/8.0 )
				mm = am*math.cos( m* math.pi * (y +.5)/8.0 )
				#mat.append( mm*nn)	
				if x==n and y==m:
					mat.append(1)
				else:
					mat.append(0)		
		for i in range(len(mat)):
			self.base[i] += mat[i]*coeff

	def AddZigZag(self, zi, coeff):
		i = zigzag[zi]
		n = i&0x7
		m = i>>3
		self.Add( n,m, coeff)

# conert a string into a bit stream
class Stream:
	def __init__(self, data):
		self.data= data
		self.pos = 0
	def GetBit(self):
		b, = unpack("B",self.data[self.pos/8])
		s = 7-(self.pos%8)
		self.pos+=1		
		return (b>>s ) & 1

	def GetBitN(self, l):
		val = 0;
		for i in range(l):
			val = val*2 + self.GetBit()
		return val

	def GetBitStr(self):
		if self.GetBit()==0:
			return "0"
		return "1"


# Crate huffman bits from table lengths
class HuffmanTable:
	def __init__(self):
		self.caca=[]
		self.bits = []
		self.elements = []
	
	def BitsFromLengths(self, lengths, side, depth):
		if depth <16:		        
			if self.caca[depth]== lengths[depth]:
				self.BitsFromLengths(lengths, side+"0", depth+1)
				self.BitsFromLengths(lengths, side+"1", depth+1)
			else:
				self.caca[depth] +=1
				self.bits.append(side)
	
	def GetHuffmanBits(self,  lengths, elements):
		self.caca=[0] * 16
		self.bits=[]
		self.elements = elements
		self.BitsFromLengths(lengths, "0", 0)
		self.BitsFromLengths(lengths, "1", 0)

	def Find(self,val):
		for i in range(len(self.bits)):
			if self.bits[i]==val:
				return self.elements[i]
		return -1

	def GetValue(self, st):
		val=""
		while(True):
			val +=   st.GetBitStr()
			
			res = self.Find(val)
			if res == 0:
				return 0
			elif ( res != -1):
				print val,
				return res

	def DecodeNumber(self, code, bits):
		print "(%i,%i)" % (code,bits),

		l = 2**(code-1)
		if bits>=l:
			return bits
		else:
			return bits-(2*l-1)

	def GetDC(self, st):
		code = self.GetValue(st)
		bits = st.GetBitN(code)
		
		if (bits==0):
			return 0
		return self.DecodeNumber(code, bits)

	def GetAC(self,st):
		code = self.GetValue(st)
		bits = st.GetBitN(code)
		return self.DecodeNumber(code, bits)

# main class that decodes the jpeg
class jpeg:
	def __init__(self):
		self.lumi_quant = []
		self.crom_quant = []
		self.tables = {}

	def App0Segment(self, data):
		#print len(data)
		Id = data[0:5]
		#print Id, "  ", 
		ver,  den, xden, yden, thw, thh =  unpack(">HBHHBB", data[5:5+9])
		#print ver, den, xden,yden,
		thlen = thw*thh*3
		#print thw,"x",thh

	def App12Segment(self, data):	
		return

	def App14Segment(self, data):	
		return

	def BuildMatrix(self, st, idx, quant, olddccoeff):	
		i = IDCT()	
		print "dc", 
		dccoeff = self.tables[0+idx].GetDC(st) * quant[0] + olddccoeff
		print dccoeff
		if dccoeff!=0:
			print "ac",
			i.AddZigZag(0,dccoeff)
			for l in range(1,64):
				coeff = self.tables[16+idx].GetAC(st) #* quant[l]
				print  coeff
				if coeff==0:
					break
				i.AddZigZag(l,coeff)
		print
		print
		PrintMatrix( i.base)
		print "#"
		return i,dccoeff
	
	def ScanData(self, data):
		#hexdump( data )

		#remove ff00
		data = RemoveFF00(data)
		#hexdump( data )
		st = Stream(data)

		print "decode luminance"
		oldlumdccoeff = 0
		oldCbdccoeff = 0
		oldCrdccoeff = 0
		for i in range(1):
			matL,olddccoeff = self.BuildMatrix(st,0, self.lumi_quant, oldlumdccoeff)
			matCb,oldCbdccoeff = self.BuildMatrix(st,1,self.crom_quant, oldCbdccoeff)
			matCr, oldCrdccoeff = self.BuildMatrix(st,1,self.crom_quant, oldCrdccoeff)
	 		#PrintMatrix( matL.base)
			#DrawMatrix(i, 0, matL.base)		

	def DefineQuantizationTables(self, data):
		hdr, = unpack("B",data[0:1])
		print hdr >>4, hdr & 0xf
		self.lumi_quant =  GetArray("B", data[1:1+64],64)

		hdr, = unpack("B",data[64:65])
		print hdr >>4, hdr & 0xf
		self.crom_quant =  GetArray("B", data[66:2+128],64) 
		PrintMatrix( UnZigZag(self.lumi_quant) )
		print
		PrintMatrix( UnZigZag(self.crom_quant) )

	def BaselineDCT(self, data):
		return
	
	def DefineHuffmanTables(self, data):
		off = 0
		for i in range(4):	
			hdr, = unpack("B",data[off:off+1])
			off+=1

			#print "hdr", hdr
		
			lengths = GetArray("B", data[off:off+16],16) 
			elements = []
			off += 16
		
			hf = HuffmanTable();
			for i in lengths:
				elements+= (GetArray(	"B", data[off:off+i], i)	)
				off = off+i 

			hf.GetHuffmanBits( lengths, elements)
			#print lengths
			#print elements
			self.tables[hdr] = hf


	def StartOfScan(self, data):
		#print self.tables
		#hexdump( data )
		return	

	def decode(self, data):	
		while(True):
			hdr, = unpack(">H", data[0:2])
			if hdr == 0xffd8:
				print "%x" % hdr
				lenchunk = 2
			else:
				lenchunk, = unpack(">H", data[2:4])
				print "%x" % hdr,
				print lenchunk
				lenchunk+=2
				chunk = data[4:lenchunk]
											
				if hdr == 0xffe0:
					self.App0Segment(chunk)
			        elif hdr == 0xffec:
					self.App12Segment(chunk)
			        elif hdr == 0xffee:
					self.App14Segment(chunk)
			        elif hdr == 0xffdb:
					self.DefineQuantizationTables(chunk)
			        elif hdr == 0xffc0:
					self.BaselineDCT(chunk)
			        elif hdr == 0xffc4:
					self.DefineHuffmanTables(chunk)
			        elif hdr == 0xffda:
					self.StartOfScan(data)
					self.ScanData(data[lenchunk:])
				else:							
					break
	
			data = data[lenchunk:]
			if len(data)==0:
				print "end"
				break		


"""
from Tkinter import *
master = Tk()
w = Canvas(master, width=200, height=100)
w.pack()
"""

j = jpeg()
#j.decode(open('images/huff_simple0.jpg', 'r').read())
j.decode(open('images/surfer.jpg', 'r').read())
#j.decode(open('images/porsche.jpg', 'r').read())
#j.decode(open('images/test.jpeg', 'r').read())
#j.decode(open('images/huff_simple0.jpg', 'r').read())
#j.decode(open('images/surfer.jpg', 'r').read())
#j.decode(open('images/parrots.jpg', 'r').read())
"""
#mainloop()
"""
