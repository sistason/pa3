import gc
import uos
import machine
import webrepl
from flashbdev import bdev

gc.threshold((gc.mem_free() + gc.mem_alloc()) // 4)

gc.collect()

try:
    uos.dupterm(machine.UART(0, 115200), 1)
except (OSError, ValueError):
    pass


try:
    if bdev:
        uos.mount(bdev, '/')
except OSError:
    uos.VfsFat.mkfs(bdev)
    vfs = uos.VfsFat(bdev)
    uos.mount(vfs, '/')

gc.collect()


def start_webrepl():
    #TODO: manually set pw?
    if not uos.path.exists('webrepl_pass'): #TODO
        with open("/webrepl") as f: #TODO
            f.write("testtest")
    webrepl.start()

