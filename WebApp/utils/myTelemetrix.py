# CONTAINS THE ARDUINO INSTRUCTION AND CONNECTION TO BLUETOOTH

from telemetrix import telemetrix

class MyTelemetrix:
    def __init__(self, com_port=None):
        try:
            if com_port == None:
                self.board = telemetrix.Telemetrix()
            else:
                self.board = telemetrix.Telemetrix(
                    com_port=com_port,
                    arduino_wait=10,
                    sleep_tune=0.05
                )
        except RuntimeError as rE:
            print(rE, "\nPlease Enter a Correct Port Name and Press 'Reconnect (BT)' to Try Again...")
            

    def reconn(self, com_port=None):
        if com_port == None:
            self.board = telemetrix.Telemetrix()
        else:
            self.board = telemetrix.Telemetrix(
                com_port=com_port,
                arduino_wait=10,
                sleep_tune=0.05
            )
    
    def close(self):
        print("Closing Telemetrix Connection...")
        try:
            self.board.shutdown()
        except AttributeError as aR:
            print(aR, "\nNo Board to shutdown, closing anyway...")

    # INSTRUCTIONS