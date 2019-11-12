instructions = [0x022DA822, 0x12A70003, 0x8D930018, 0x02689820, 0xAD930018, 0x02697824,
                0xAD8FFFF4, 0x018C6020, 0x02A4A825, 0x158FFFF6, 0x8E59FFF0]

f = open('project1output.txt', 'a')

def getCodes(code, address):
    opcode = code >> 26
    rd = False
    if opcode == 0:
        rest, func = getFunction(code)
        rest, shift = getShift(rest)
        rd = rest >> 5 & 0x1f
        rt = rest >> 10 & 0x1f
        rs = rest >> 15 & 0x1f
	outputR(rs, rt, rd, shift, func, address)
    else:
        offset = code & 0xffff
	offset = offset << 2
        if offset >> 15:
            reverse = True
            offset = offset >> 1
            offset = offset ^ 0b11111111111111111 + 1
        else:
            reverse = False
        rest = code >> 16
        rt = rest & 0x1f
        rs = rest >> 5 & 0x1f
	outputI(opcode, rs, rt, offset, reverse, address)

def outputI(opcode, rs, rt, offset, reverse, address):
    if reverse:
	offset = offset * -1
    if opcode == 4:
        write(hex(address)[2:] + '  beq $%i, $%i, address ' % (rs, rt) + hex(address + offset)[2:])  
    elif opcode == 35:
        write(hex(address)[2:] + '  lw $%i, %i ($%i)' % (rt, offset, rs))
    elif opcode == 43:
        write(hex(address)[2:] + '  sw $%i, %i ($%i)' % (rt, offset, rs))
    elif opcode == 5:
        write(hex(address)[2:] + '  bne %i, %i, address ' % (rs, rt) + hex(address + offset)[2:])  


def outputR(rs,rt,rd,shift,func, address):
    if func == 34:
    	write(hex(address)[2:] + '  sub %i, %i, %i' % (rd, rs, rt))
    elif func == 32:
        write(hex(address)[2:] + '  add %i, %i, %i' % (rd, rs, rt))
    elif func == 36:
	    write(hex(address)[2:] + '  and %i, %i, %i' % (rd, rs, rt))
    elif func == 37:
        write(hex(address)[2:] + '  or %i, %i, %i' % (rd, rs, rt))

def getFunction(code):
    function = code & 0x3f
    rest = code >> 6
    return rest, function

def getShift(code):
    shift = code & 0x1f
    rest = code >> 5
    return rest, shift

def write(string):
    f.write(string + '\n')

address = 0x7A060
for inst in instructions:
    getCodes(inst, address)
    address += 4
f.close()
