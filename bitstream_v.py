class BitstreamWriter:
    def __init__(self):
        self.nbits  = 0
        self.curbyte = 0
        self.vbytes = []

    """ add single bit """
    def add(self, x):
        self.curbyte |= x << (8-1 - (self.nbits % 8))
        self.nbits += 1

        if self.nbits % 8 == 0:
            self.vbytes.append(chr(self.curbyte))
            self.curbyte = 0

    """ get byte-aligned bits """
    def getbytes(self):
        if self.nbits & 7 == 0:
            return "".join(self.vbytes)

        return "".join(self.vbytes) + chr(self.curbyte)


class BitstreamReader:
    def __init__(self, blob):
        self.blob = blob
        self.pos  = 0

    """ extract next bit """
    def get(self):
        ibyte = self.pos / 8
        ibit  = self.pos & 7

        self.pos += 1
        return (ord(self.blob[ibyte]) & (1 << (7 - ibit))) >> (7 - ibit)

    def finished(self):
        return self.pos >= len(self.blob) * 8


"""
Input dl contains monotonically groving integers
"""


def get_bit_repr(number):
    binary = lambda n: n > 0 and [n & 1] + binary(n >> 1) or []
    bits = binary(number)
    while len(bits) % 7 != 0:
        bits.append(0)
    res = []
    for i, b in enumerate(bits):
        res.append(b)
        if (i + 1) % 7 == 0 and i > 0:
            if len(bits) - (i + 1) > 0:
                res.append(1)
            else:
                res.append(0)
    return res


def get_num_repr(bits):
    dl = []
    cur_number = 0
    cur_bits = 0
    i = 0
    for b in bits:
        # if reserved bit
        if (i + 1) % 8 == 0 and i != 0:
            i += 1
            if b == 0:
                ##last byte
                dl.append(cur_number)
                cur_number = 0
                cur_bits = 0
                continue
            else:
                continue
        ## not all the number has received
        cur_number += (2 ** cur_bits) * b
        cur_bits += 1
        i += 1
    return dl


def compress_varbyte_v(dl):
    bs = BitstreamWriter()

    """ Write your code here """

    for i in dl:
        num = get_bit_repr(i)
        ## add new bytes to a long sequence of bytes via method add
        # print(num)
        for val in num:
            bs.add(val)
    return bs.getbytes()


def decompress_varbyte_v(s):
    bs = BitstreamReader(s)
    dl = []

    """ Write your code here """

    bits = []
    while not bs.finished():
        bit = bs.get()
        bits.append(bit)
    # print(bits)
    dl = get_num_repr(bits)
    return dl


############### Simple 9 ###############

def encode(bs, dl, num):
    num_info_bits = 4
    bits_count = 0
    tmp = num
    for i in range(num_info_bits):
        if tmp & 1:
            bs.add(1)
        else:
            bs.add(0)
        tmp = tmp >> 1
        bits_count += 1

    for i in dl:
        for k in range(28 / num):
            if i & 1:
                bs.add(1)
            else:
                bs.add(0)
            i = i >> 1
            bits_count += 1

    while bits_count < 32:
        bs.add(0)
        bits_count += 1
    return bs


def compress_simple(dl):
    bs = BitstreamWriter()

    prev_max = 0
    prev = 0

    arr = []
    for i in dl:
        j = 0;
        temp = i
        i -= prev
        prev = temp

        if i > prev_max:
            prev_max = i

        if (len(arr) + 1) * prev_max.bit_length() > 28:
            bs = encode(bs, arr, len(arr))
            prev_max = i
            arr = [i]
            continue
        arr.append(i)

    if len(arr) > 0:
        bs = encode(bs, arr, len(arr))
    return bs.getbytes()


def decode(br):
    num = 0
    bits_read = 0
    num_info_bits = 4

    for i in range(num_info_bits):
        cur_bit = br.get()
        if cur_bit:
            num += 2 ** i
        bits_read += 1

    ret = []
    for i in range(num):
        s = 0
        for k in range(28 / num):
            cur_bit = br.get()
            s += cur_bit * 2 ** k
            bits_read += 1
        ret.append(s)
    for k in range(32 - bits_read):
        br.get()
    return ret


def decompress_simple(s):
    br = BitstreamReader(s)
    dl = []
    while not br.finished():
        dl.extend(decode(br))
    res = []
    prev = 0
    for i in dl:
        temp = prev + i
        prev = temp
        res.append(temp)
    return res