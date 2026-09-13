from machine import Pin, PWM
import time

led = Pin("LED", Pin.OUT)
in1 = Pin(16, Pin.OUT)
in2 = Pin(17, Pin.OUT)
ena = PWM(Pin(18))
ena.freq(1000)


def apply(s):
    in1.value(1 if s > 0 else 0)
    in2.value(1 if s < 0 else 0)
    ena.duty_u16(int(abs(s) * 65535))


print("3 sec FORWARD at full")
led.on()
apply(1.0)
time.sleep(3)

print("stop")
apply(0)
led.off()
time.sleep(1)

print("3 sec REVERSE at full")
led.on()
apply(-1.0)
time.sleep(3)

apply(0)
led.off()
print("done")
