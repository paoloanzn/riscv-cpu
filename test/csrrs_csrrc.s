main:
  addi x5, x0, 0x12       # x5 = 0x12
  csrrs x5, mstatus, x5   # x5 = 0, mstatus = 0 | 0x12 = 0x12
  addi x6, x0, 0x34       # x6 = 0x34
  csrrc x6, mstatus, x6   # x6 = 0x12, mstatus = 0x12 & ~0x34 = 0x02
  # (bit 1 survives: 0b10010 & ~0b110100 = 0b10 = 0x02)
  addi x7, x0, 0x55       # x7 = 0x55
  csrrwi x7, 0x341, 0     # clear mcause to 0; x7 = old value
  addi x8, x0, 0x00       # x8 = 0
  csrrwi x8, 0x342, 0     # clear mtval to 0; x8 = old value
# expect x5=0, x6=0x12, x7=0, x8=0, csr[0x300]=0x2, csr[0x341]=0, csr[0x342]=0