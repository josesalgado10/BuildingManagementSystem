# Jose Salgado

import Adafruit_DHT
from Adafruit_LCD1602 import Adafruit_CharLCD
from PCF8574 import PCF8574_GPIO
from CIMIS_Extract import *
import RPi.GPIO as GPIO
import time
import threading
import sys

# LCD Setup and Global Variables
PCF8574_address = 0x27
mcp = PCF8574_GPIO(PCF8574_address)
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], GPIO=mcp)
Line1 = ""

# Local Data Initialization
humidity = 0
temperature = 0
average_temperature = 0
desired_temp = 75
weather_index = 0
temperature_list = []

# Moving GPIO pin numbers into Variables
blue_button = 16
red_button = 20
green_button = 21
green_led = 26
red_led = 13
blue_led = 19
pirPin = 12
dhtType = 11
dhtPin = 4

# CIMIS Object Pointer
cimis = None

# flags
door_window_open = False
lights = False
pop_up = False
ac_boot = True
heat_boot = True

# hvac variables
ac_on = False
heat_on = False

# thread pointers
PIR_thread = None
DHT_thread = None


# Start of Functions

# connect GPIO pins for sensors
def setup():
    global pirPin, dhtPin, cimis, blue_button, red_button, green_button, blue_led, red_led, green_led
    lcd_setup()  # Starting the LCD
    GPIO.setmode(GPIO.BCM)  # setting GPIO environment
    GPIO.setwarnings(False)
    GPIO.setup(dhtPin, GPIO.IN)  # dht pin
    GPIO.setup(pirPin, GPIO.IN)  # PIR pin
    # add buttons and LED
    GPIO.setup(blue_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(red_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(green_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(blue_led, GPIO.OUT)
    GPIO.setup(red_led, GPIO.OUT)
    GPIO.setup(green_led, GPIO.OUT)
    GPIO.output(blue_led, 0)
    GPIO.output(red_led, 0)
    GPIO.output(green_led, 0)
    cimis = CIMIS()


# Dht functions

def dht_update():
    while True:
        global humidity, temperature, temperature_list
        humidity, temperature = Adafruit_DHT.read_retry(dhtType, dhtPin)
        temperature = (temperature * 1.8) + 32
        if len(temperature_list) == 3:
            temperature_list.pop(0)
        if len(temperature_list) < 3:
            temperature_list.append(temperature)
        print("Local Hum.:", humidity)
        print("Local Temp.:", temperature)
        time.sleep(1)


def hvac_function():
    global door_window_open, hvac_on, ac_on, heat_on, pop_up, ac_boot, heat_boot
    # check if door/window open
    if door_window_open:
        ac_on = False
        heat_on = False
        ac_boot = True
        heat_boot = True
        GPIO.output(blue_led, 0)
        GPIO.output(red_led, 0)
    else:
        if (weather_index - desired_temp) > 3:
            ac_on = True
            # turn on blue LED
            GPIO.output(red_led, 0)
            GPIO.output(blue_led, 1)
            if ac_boot:
                lcd_ac_on()
                ac_boot = False
        elif (weather_index - desired_temp) < -3:
            heat_on = True
            # turn on red LED
            GPIO.output(blue_led, 0)
            GPIO.output(red_led, 1)
            if heat_boot:
                lcd_heat_on()
                heat_boot = False


def dht_function():
    global temperature, average_temperature, weather_index, temperature_list, pop_up

    # gets temp every 1 sec
    my_thread = threading.Thread(target=dht_update)
    my_thread.daemon = True
    my_thread.start()

    while True:
        average_temperature = float(sum(temperature_list) / 3)
        weather_index = calculate_weather_index()
        hvac_function()
        if not pop_up:
            show_stats()
        elif pop_up:
            while pop_up:
                time.sleep(1)
            
def check_diff():
    global weather_index, desired_temp, ac_on, heat_on
    if (weather_index - desired_temp) > 3 and ac_on == False:
        lcd_ac_on()
    if (weather_index - desired_temp) < -3 and heat_on == False:
        lcd_heat_on()

# calculation functions

def calculate_weather_index():  # calculating data from calling function
    global cimis, average_temperature
    cimis.update_values()
    return average_temperature + 0.05 * cimis.humidity


# pir function

def pir_function():  # done
    global pirPin, green_led, lights
    while True:
        motion = GPIO.input(pirPin)
        if motion == 1:
            lights = True
            GPIO.output(green_led, 1)
        if motion == 0:
            clk = 0
            while motion == 0:
                time.sleep(1)
                clk += 1
                motion = GPIO.input(pirPin)
                if clk == 10:
                    print("No motion for 10 sec, LED off")
                    lights = False
                    GPIO.output(green_led, 0)


# button functions
def green_press(button_press):
    global door_window_open, green_button
    if door_window_open:
        print("Door/window closed")
        door_window_open = False
        lcd_door_window_closed()
    elif not door_window_open:
        print("Door/window opened")
        door_window_open = True
        lcd_door_window_open()


def blue_press(button_press):
    global desired_temp, weather_index
    if desired_temp == 65:
        print("Min AC reached")
    if desired_temp > 65:
        desired_temp -= 1
    check_diff()
    print("Set temp. to:", desired_temp)

def red_press(button_press):
    global desired_temp
    if desired_temp == 85:
        print("Max HEAT reached")
    if desired_temp < 85:
        desired_temp += 1
    check_diff()
    print("Set temp. to:", desired_temp)

# Start of LCD Block
def lcd_setup():
    global Line1
    mcp.output(3, 1)
    lcd.begin(16, 2)
    Line1 = "EECS113 \nFinal Project"
    time.sleep(3)
    update_lcd()


def update_lcd():
    global Line1
    lcd.clear()
    message = str(Line1)
    lcd.message(message)
    time.sleep(3)


def lcd_door_window_open():
    global Line1, pop_up
    Line1 = "DOOR/WINDOW OPEN!\nHVAC HALTED"  # update line 1
    pop_up = True
    update_lcd()
    pop_up = False

def lcd_door_window_closed():
    global Line1, pop_up
    Line1 = "DOOR/WINDOW SHUT!\nHVAC RESUMES"  # update line 1
    pop_up = True
    update_lcd()
    pop_up = False

def lcd_ac_on():
    global Line1, pop_up
    Line1 = "HVAC AC"  # update line 1
    pop_up = True
    update_lcd()
    pop_up = False


def lcd_heat_on():
    global Line1, pop_up
    Line1 = "HVAC HEAT"  # update line 1
    pop_up = True
    update_lcd()
    pop_up = False


def show_stats():
    global Line1
    Line1 = get_string()
    update_lcd()


def get_string():
    global weather_index, desired_temp, door_window_open, hvac_on, ac_on, heat_on, lights

    w_index = str(round(weather_index))

    d_temp = str(round(desired_temp))

    dw_open = "OPEN" if (door_window_open is True) else "SAFE"

    hvac_status = "OFF"
    if ac_on:
        hvac_status = "AC       "
    elif heat_on:
        hvac_status = "HEAT     "
    else:
        hvac_status = "OFF      "

    l_status = "OFF" if (lights is False) else "ON"

    return w_index + "/" + d_temp + "     D:" + dw_open + "\n"+"H:" + hvac_status + "L:" + l_status


# END of LCD Block

def in_loop():
    global DHT_thread, PIR_thread

    DHT_thread = threading.Thread(target=dht_function)
    DHT_thread.daemon = True
    DHT_thread.start()

    PIR_thread = threading.Thread(target=pir_function)
    PIR_thread.daemon = True
    PIR_thread.start()


def button_interrupt():
    GPIO.add_event_detect(blue_button, GPIO.RISING, callback=blue_press, bouncetime=333)
    GPIO.add_event_detect(red_button, GPIO.RISING, callback=red_press, bouncetime=333)
    GPIO.add_event_detect(green_button, GPIO.RISING, callback=green_press, bouncetime=1000)

    while True:
        continue

    GPIO.cleanup()


# END of inLoop
if __name__ == '__main__':
    print("Completing setup...")
    setup()
    print("Setting threads...")
    in_loop()
    print("Starting BMS...")
    button_interrupt()
