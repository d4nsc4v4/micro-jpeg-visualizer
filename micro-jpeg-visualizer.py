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

def Clamp(col):
	col = col if col<255 else 255
	col = col if col>0 else 0
	return  col

def ColorConversion(Y, Cr, Cb):
	R = Cr*(2-2*.299) + Y
	B = Cb*(2-2*.114) + Y
	G = (Y - .114*B - .299*R)/.587
	return (Clamp(R+128),Clamp(G+128),Clamp(B+128) )

def GetArray(type,l, length):
	s = ""
	for i in range(length):
		s =s+type
	return	list(unpack(s,l[:length]))

def DecodeNumber(code, bits):
	l = 2**(code-1)
	if bits>=l:
		return bits
	else:
		return bits-(2*l-1)
	
def PrintMatrix( m):
	for j in range(8):
		for i in range(8):
			print "%2f" % m[i+j*8],
		print

def XYtoLin(x,y):
	return x+y*8

def DrawMatrix(x, y, matL, matCb,matCr):
	for yy in range(8):
		for xx in range(8):
			c = "#%02x%02x%02x" % ColorConversion( matL[XYtoLin(xx,yy)] , matCb[XYtoLin(xx,yy)], matCr[XYtoLin(xx,yy)])
			w.create_rectangle((x*8+xx)*2, (y*8+yy)*2, (x*8+(xx+1))*2, (y*8+(yy+1))*2, fill=c,outline= c)

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
		return math.sqrt( 1.0/8.0) if (n==0) else math.sqrt( 2.0/8.0)

	def AddIDC(self, n,m, coeff):
		an = self.NormCoeff(n)
		am = self.NormCoeff(m)
				
		for y in range(0,8):			
			for x in range(0,8):
				nn = an*math.cos( n* math.pi * (x +.5)/8.0 )
				mm = am*math.cos( m* math.pi * (y +.5)/8.0 )
				self.base[ XYtoLin(x, y) ] += nn*mm*coeff

	def AddZigZag(self, zi, coeff):
		i = zigzag[zi]
		n = i&0x7
		m = i>>3
		self.AddIDC( n,m, coeff)

# convert a string into a bit stream
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
		return "0" if  self.GetBit()==0 else "1"

# Create huffman bits from table lengths
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

	def GetCode(self, st):
		val=""
		while(True):
			val +=   st.GetBitStr()			
			res = self.Find(val)
			if res == 0:
				return 0
			elif ( res != -1):
				return res

	def GetCoeff(self,st):
		code = self.GetCode(st)
		bits = st.GetBitN(code)
		return DecodeNumber(code, bits)

# main class that decodes the jpeg
class jpeg:
	def __init__(self):
		self.lumi_quant = []
		self.crom_quant = []
		self.tables = {}
		self.width = 0
		self.height = 0

	def BuildMatrix(self, st, idx, quant, olddccoeff):	
		i = IDCT()	
		dccoeff = self.tables[0+idx].GetCoeff(st)  + olddccoeff
		i.AddZigZag(0,dccoeff * quant[0])
		l = 1
		while(l<64):
			code = self.tables[16+idx].GetCode(st) 
			if code == 0:
				break
			elif code >15:
				l+= (code>>4)
				code = code & 0xf				
			bits = st.GetBitN( code )
			if l<64:						
				coeff  =  DecodeNumber(code, bits) * quant[l]
				i.AddZigZag(l,coeff)
				l+=1
		return i,dccoeff
	
	def StartOfScan(self, data):
		data = RemoveFF00(data)

		st = Stream(data)

		oldlumdccoeff = 0
		oldCbdccoeff = 0
		oldCrdccoeff = 0
		for y in range(self.height/8):
			for x in range(self.width/8):
				matL,oldlumdccoeff = self.BuildMatrix(st,0, self.lumi_quant, oldlumdccoeff)
				matCr, oldCrdccoeff = self.BuildMatrix(st,1,self.crom_quant, oldCrdccoeff)
				matCb,oldCbdccoeff = self.BuildMatrix(st,1,self.crom_quant, oldCbdccoeff)
				DrawMatrix(x, y, matL.base, matCb.base, matCr.base )		

	def DefineQuantizationTables(self, data):
		hdr, = unpack("B",data[0:1])
		print hdr >>4, hdr & 0xf
		self.lumi_quant =  GetArray("B", data[1:1+64],64)
		
		hdr, = unpack("B",data[64:65])
		print hdr >>4, hdr & 0xf
		self.crom_quant =  GetArray("B", data[66:2+128],64) 

	def BaselineDCT(self, data):
		hdr, self.height, self.width = unpack(">BHH",data[0:5])
		print "size %ix%i" % (self.width,  self.height)
		
	def DefineHuffmanTables(self, data):
		off = 0
		for i in range(4):	
			hdr, = unpack("B",data[off:off+1])
			off+=1

			lengths = GetArray("B", data[off:off+16],16) 
			off += 16
		
			elements = []
			for i in lengths:
				elements+= (GetArray(	"B", data[off:off+i], i)	)
				off = off+i 

			hf = HuffmanTable();
			hf.GetHuffmanBits( lengths, elements)
			self.tables[hdr] = hf

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
											
			        if hdr == 0xffdb:
					self.DefineQuantizationTables(chunk)
			        elif hdr == 0xffc0:
					self.BaselineDCT(chunk)
			        elif hdr == 0xffc4:
					self.DefineHuffmanTables(chunk)
			        elif hdr == 0xffda:
					self.StartOfScan(data[lenchunk:])
				else:							
					print "chunk unknown: %x" % hdr
	
			data = data[lenchunk:]
			if len(data)==0:
				print "end"
				break		

from Tkinter import *
master = Tk()
w = Canvas(master, width=1600, height=600)
w.pack()

j = jpeg()
#j.decode(open('images/huff_simple0.jpg', 'r').read())
#j.decode(open('images/surfer.jpg', 'r').read())
j.decode(open('images/porsche.jpg', 'r').read())
#j.decode(open('images/test.jpeg', 'r').read())
#j.decode(open('images/huff_simple0.jpg', 'r').read())
#j.decode(open('images/surfer.jpg', 'r').read())
#j.decode(open('images/download.jpg', 'r').read())
#j.decode(open('images/parrots.jpg', 'r').read())
mainloop()

