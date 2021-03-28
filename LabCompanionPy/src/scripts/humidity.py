import json
import os
from sense_hat import SenseHat
def main():
    file = "data/humidity.txt"
    sense = SenseHat()
    sense.clear()
    reading = sense.get_humidity()

    humidity = []
    humidity.append(reading)
    humidity = json.dumps(humidity)
    try:
        f = open(file, 'w')
        f.write(humidity)
    except IOError as e:
        print("Error: " + e.strerror)
    except:
        print("Error writing to file: {}".format(file))


if __name__ == "__main__":
    main()