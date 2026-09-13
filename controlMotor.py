from machine import Pin, PWM
import sys, select, time

in1 = Pin(16, Pin.OUT)
in2 = Pin(17, Pin.OUT)
ena = PWM(Pin(18))
ena.freq(1000)

in3 = Pin(19, Pin.OUT)
in4 = Pin(20, Pin.OUT)
enb = PWM(Pin(21))
enb.freq(1000)

LEFT_FLIP = 1
RIGHT_FLIP = 1


def _set(a, b, en, s):
    s = max(-1.0, min(1.0, s))
    a.value(1 if s > 0 else 0)
    b.value(1 if s < 0 else 0)
    en.duty_u16(int(abs(s) * 65535))


def drive(l, r):
    _set(in1, in2, ena, l * LEFT_FLIP)
    _set(in3, in4, enb, r * RIGHT_FLIP)


level = 0.3
poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

print("w/a/s/d drive   space stop   +/- speed   q quit")
print("level", level)

last = time.ticks_ms()
moving = False

try:
    while True:
        if poll.poll(0):
            c = sys.stdin.read(1)
            last = time.ticks_ms()

            if c == "w":
                drive(level, level)
                moving = True
            elif c == "s":
                drive(-level, -level)
                moving = True
            elif c == "a":
                drive(-level, level)
                moving = True
            elif c == "d":
                drive(level, -level)
                moving = True
            elif c == " ":
                drive(0, 0)
                moving = False
            elif c in "+=":
                level = min(1.0, level + 0.05)
                print("level", round(level, 2))
            elif c == "-":
                level = max(0.1, level - 0.05)
                print("level", round(level, 2))
            elif c == "q":
                break

        if moving and time.ticks_diff(time.ticks_ms(), last) > 400:
            drive(0, 0)
            moving = False

        time.sleep_ms(10)
finally:
    drive(0, 0)
    print("stopped")
