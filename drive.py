from machine import Pin, PWM

# motor A = LEFT
inA1 = Pin(16, Pin.OUT); inA2 = Pin(17, Pin.OUT)
enA  = PWM(Pin(18)); enA.freq(20000)

# motor B = RIGHT
inB1 = Pin(19, Pin.OUT); inB2 = Pin(20, Pin.OUT)
enB  = PWM(Pin(21)); enB.freq(20000)

LEFT_FLIP  = -1
RIGHT_FLIP = -1

TRIM = 0.0          # -0.5..0.5  positive slows LEFT, negative slows RIGHT

def set_trim(t):
    global TRIM
    TRIM = max(-0.5, min(0.5, t))

def get_trim():
    return TRIM

def _set(a, b, en, s):
    s = max(-1.0, min(1.0, s))
    a.value(1 if s > 0 else 0)
    b.value(1 if s < 0 else 0)
    en.duty_u16(int(abs(s) * 65535))

def drive(left, right):
    l = left  * (1.0 - max(0.0,  TRIM))
    r = right * (1.0 - max(0.0, -TRIM))
    _set(inA1, inA2, enA, l * LEFT_FLIP)
    _set(inB1, inB2, enB, r * RIGHT_FLIP)

def stop():
    drive(0, 0)