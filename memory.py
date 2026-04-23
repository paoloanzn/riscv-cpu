# RISC-V 64 bit (little-endian)

MEM_SIZE = 1024 * 1024 * 128 # 128 Mib


class Memory:
    def __init__(self, preloaded_bytes=None):
        self.size = MEM_SIZE
        if preloaded_bytes is None:
            self._data = [0] * self.size
        else:
            self._data = preloaded_bytes + ([0] * (self.size - len(preloaded_bytes)))
    
    def load(self, addr, size) -> list[int]:
        return self._data[addr:addr+size]

    def store(self, addr, size, bytes_array) -> None:
        self._data[addr:addr+len(bytes_array)]= bytes_array