# CONTAINS THE ARDUINO INSTRUCTION AND CONNECTION TO BLUETOOTH

from telemetrix import telemetrix

IN1 = 2  # Left Motor Direction 1
IN2 = 3  # Left Motor Direction 2
IN3 = 7  # Right Motor Direction 1
IN4 = 8  # Right Motor Direction 2

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
            return

        for pin in [IN1, IN2, IN3, IN4]:
            self.board.set_pin_mode_digital_output(pin)

        self.stop_motors()

    def reconn(self, com_port=None):
        print(com_port)
        try:
            if com_port in [None, '']:
                self.board = telemetrix.Telemetrix()
            else:
                self.board = telemetrix.Telemetrix(
                    com_port=com_port,
                    arduino_wait=10,
                    sleep_tune=0.05
                )
        except RuntimeError as rE:
            print(rE, "\nPlease Enter a Correct Port Name and Press 'Reconnect (BT)' to Try Again...")
    
    def close(self):
        print("Closing Telemetrix Connection...")
        try:
            self.board.shutdown()
        except AttributeError as aR:
            print(aR, "\nNo Board to shutdown, closing anyway...")

    # INSTRUCTIONS


    # TESTING Script
    def update_motors(self, FSlider, TSlider):
        """Processes sliders with exclusive priority for straight motion vs turning at full speed."""
        fwd_raw = FSlider.value()
        trn_raw = TSlider.value()
        
        # Calculate deviation from neutral center (49)
        fwd_intent = fwd_raw - 49
        trn_intent = trn_raw - 49
        
        # Deadzone to prevent jitter around 49
        deadzone = 2
        
        if abs(fwd_intent) > deadzone and abs(fwd_intent) >= abs(trn_intent):
            # --- FORWARD / BACKWARD MODE ---
            if fwd_intent > 0:
                # Move Forward (Both wheels forward at full speed)
                self.set_raw_motors(1, 0, 1, 0)
                print("Moving FORWARD (Full Speed)")
            else:
                # Move Backward (Both wheels backward at full speed)
                self.set_raw_motors(0, 1, 0, 1)
                print("Moving BACKWARD (Full Speed)")
                
        elif abs(trn_intent) > deadzone:
            # --- LEFT / RIGHT PIVOT TURN MODE ---
            if trn_intent > 0:
                # Turn Right (Left wheel forward, Right wheel backward)
                self.set_raw_motors(1, 0, 0, 1)
                print("Turning RIGHT (Full Speed)")
            else:
                # Turn Left (Left wheel backward, Right wheel forward)
                self.set_raw_motors(0, 1, 1, 0)
                print("Turning LEFT (Full Speed)")
        else:
            # --- NEUTRAL / STOP ---
            self.stop_motors()
            print("Motors STOPPED")

    def set_raw_motors(self, l_in1, l_in2, r_in1, r_in2):
        """Sets direction states for left and right motors."""
        self.board.digital_write(IN1, l_in1)
        self.board.digital_write(IN2, l_in2)
        self.board.digital_write(IN3, r_in1)
        self.board.digital_write(IN4, r_in2)

    def stop_motors(self):
        """Stops all motor activity by setting all direction pins LOW."""
        self.board.digital_write(IN1, 0)
        self.board.digital_write(IN2, 0)
        self.board.digital_write(IN3, 0)
        self.board.digital_write(IN4, 0)