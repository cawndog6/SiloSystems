import json
import os
from sense_hat import SenseHat
def main():
    file = "data/pressure.txt"
    sense = SenseHat()
    sense.clear()
    reading = sense.get_pressure()

    pressure = []
    pressure.append(reading)
    pressure = json.dumps(pressure)
    try:
        f = open(file, 'w')
        f.write(pressure)
    except IOError as e:
        print("Error: " + e.strerror)
    except:
        print("Error writing to file: {}".format(file))


if __name__ == "__main__":
    main()