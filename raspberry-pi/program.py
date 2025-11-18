from gpiozero import LED, Button
from time import sleep
from signal import pause

led = LED(18)
button = Button(17)

button.when_pressed = led.on
button.when_released = led.off

print('Starting button listener...')
pause()
