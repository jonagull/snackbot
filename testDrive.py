from machine import Pin, PWM
import sys, select, time

# motor A = LEFT
inA1 = Pin(16, Pin.OUT)
inA2 = Pin(17, Pin.OUT)
enA = PWM(Pin(18))
enA.freq(20000)

# motor B = RIGHT
inB1 = Pin(19, Pin.OUT)
inB2 = Pin(20, Pin.OUT)
enB = PWM(Pin(21))
enB.freq(20000)

LEFT_FLIP = 1  # set to -1 if this wheel runs backwards
RIGHT_FLIP = 1


def _set(a, b, en, s):
    s = max(-1.0, min(1.0, s))
    a.value(1 if s > 0 else 0)
    b.value(1 if s < 0 else 0)
    en.duty_u16(int(abs(s) * 65535))


def drive(left, right):
    _set(inA1, inA2, enA, left * LEFT_FLIP)
    _set(inB1, inB2, enB, right * RIGHT_FLIP)


def stop():
    drive(0, 0)


def run():
    level = 0.6
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)

    print("w forward   s back   a left   d right")
    print("q left fwd  e right fwd")
    print("space stop  +/- speed  x quit")
    print("level", level)

    last = time.ticks_ms()
    moving = False

    try:
        while True:
            if poll.poll(0):
                c = sys.stdin.read(1)
                last = time.ticks_ms()
                moving = True

                if c == "w":
                    drive(level, level)
                elif c == "s":
                    drive(-level, -level)
                elif c == "a":
                    drive(-level, level)  # pivot left
                elif c == "d":
                    drive(level, -level)  # pivot right
                elif c == "q":
                    drive(level * 0.3, level)  # arc left
                elif c == "e":
                    drive(level, level * 0.3)  # arc right
                elif c == " ":
                    stop()
                    moving = False
                elif c in "+=":
                    level = min(1.0, level + 0.05)
                    print("level", round(level, 2))
                elif c == "-":
                    level = max(0.1, level - 0.05)
                    print("level", round(level, 2))
                elif c == "x":
                    break

            if moving and time.ticks_diff(time.ticks_ms(), last) > 400:
                stop()
                moving = False

            time.sleep_ms(10)
    finally:
        stop()
        print("stopped")
