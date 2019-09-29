import urequests
import network
import machine
import ntptime
import utime


class Watchdog:
    NETWORK = ('pa-debug', 'ahchaiSaph6oomieN3oo')

    def __init__(self):
        self.downtime = 0

        self.relay_powercut = machine.Pin(14, machine.Pin.OUT)
        self.relay_powercut.off()

        network.WLAN(network.AP_IF).active(False)
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)
        self.connect_to_AP()

    def run(self):
        while self.downtime < 60:
            utime.sleep(60)
            if self.check_connectivity():
                if self.check_pa_data():
                    self.downtime = 0
                    self.update_ntp()
                    continue
            else:
                self.connect_to_AP()

            self.downtime += 1

        self.reset_pi()
        self.reset_self()

    def check_pa_data(self):
        ret = urequests.get("http://pa.freitagsrunde.org/api/02")
        if ret.status_code == 200:
            timestamp = ret.json().get('entries', {}).get('date')
            if timestamp is not None and type(timestamp) is int:
                return utime.time()-timestamp < 3600

    def update_ntp(self):
        try:
            ntptime.settime()
        except OSError:
            pass

    def reset_pi(self):
        self.relay_powercut.on()
        utime.sleep(2)
        self.relay_powercut.off()

    def reset_self(self):
        machine.reset()

    def check_connectivity(self):
        if self.sta_if.isconnected():
            ret = urequests.get("http://pa.freitagsrunde.org")
            return ret.status_code == 200

    def connect_to_AP(self):
        if self.sta_if.isconnected():
            return True

        self.sta_if.connect(*self.NETWORK)


if __name__ == '__main__':
    watchdog = None
    try:
        watchdog = Watchdog()
        watchdog.run()
    except:
        # Be very sure the Pi is on when the watchdog fails
        if watchdog is not None:
            watchdog.relay_powercut.on()
        else:
            machine.Pin(14, machine.Pin.OUT).on()
