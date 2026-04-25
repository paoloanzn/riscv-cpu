main:
  addi x5, x0, 0x42       # x5 = 0x42
  addi x6, x0, 0xAB       # x6 = 0xAB (value to write to CSR)
  csrrw x5, mstatus, x6   # x5 = old mstatus (0), mstatus = x6
# expect x5=0, csr[0x300]=0xAB