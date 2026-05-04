from machine import Pin, PWM
from time import sleep

# Broches du moteur a tester (adapte selon ton cablage)
pwmPIN1 = 16   # GP16 = Enable (PWM)
cwPin1  = 14   # GP14 = IN1
acwPin1 = 15   # GP15 = IN2
pwmPIN2 = 17   # GP17 = Enable (PWM)
cwPin2  = 13   # GP13 = IN1
acwPin2 = 12   # GP12 = IN2

def motorMove(speed, direction, speedGP, cwGP, acwGP):
    if speed > 100: speed = 100
    if speed < 0:   speed = 0

    Speed = PWM(Pin(speedGP))
    Speed.freq(1000)

    cw  = Pin(cwGP,  Pin.OUT)
    acw = Pin(acwGP, Pin.OUT)

    Speed.duty_u16(int(speed / 100 * 65535))

    if direction < 0:
        cw.value(0)
        acw.value(1)
    elif direction == 0:
        cw.value(0)
        acw.value(0)
    else:
        cw.value(1)
        acw.value(0)

print("Test : avance 3 sec")
motorMove(60, 1, pwmPIN1, cwPin1, acwPin1)
motorMove(60, 1, pwmPIN2, cwPin2, acwPin2)
sleep(3)

print("Test : recule 3 sec")
motorMove(60, -1, pwmPIN1, cwPin1, acwPin1)
motorMove(60, -1, pwmPIN2, cwPin2, acwPin2)
sleep(3)

print("Stop")
motorMove(0, 0, pwmPIN1, cwPin1, acwPin1)
motorMove(0, 0, pwmPIN2, cwPin2, acwPin2)