import json
import os
from sense_hat import SenseHat
def main():
    file = "data/temperature.txt"
    sense = SenseHat()
    sense.clear()
    reading = sense.get_temperature()
    reading = reading *1.8000 + 32
    temperature = []
    temperature.append(reading)
    temperature = json.dumps(temperature)
    try:
        f = open(file, 'w')
        f.write(temperature)
    except IOError as e:
        print("Error: " + e.strerror)
    except:
        print("Error writing to file: {}".format(file))


if __name__ == "__main__":
    main()