# CONTAINS THE ARDUINO INSTRUCTION, BLUETOOTH, MOTORS, AND PCA9685 SERVO VIA TELEMETRIX I2C

from telemetrix import telemetrix
import time

IN1 = 2  # Left Motor Direction 1
IN2 = 3  # Left Motor Direction 2
IN3 = 7  # Right Motor Direction 1
IN4 = 8  # Right Motor Direction 2

PCA9685_ADDR = 0x40  # Default I2C address for PCA9685

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
                
            # Initialize motor pins
            for pin in [IN1, IN2, IN3, IN4]:
                self.board.set_pin_mode_digital_output(pin)

            # --- INITIALIZE PCA9685 VIA TELEMETRIX I2C ---
            self.board.set_pin_mode_i2c()
            time.sleep(0.1)
            
            # Configure PCA9685 for 50Hz Servo frequency
            # 1. Put into sleep mode
            self.board.i2c_write(PCA9685_ADDR, [0x00, 0x10])
            time.sleep(0.01)
            # 2. Set prescale for 50Hz (25MHz / (4096 * 50) - 1 = 121)
            self.board.i2c_write(PCA9685_ADDR, [0xFE, 121])
            time.sleep(0.01)
            # 3. Wake up and enable auto-increment
            self.board.i2c_write(PCA9685_ADDR, [0x00, 0x20])
            time.sleep(0.01)

            # SG90 pulse width boundaries in microseconds
            self.servo_min_us = 500   # Adjust if it buzzes at 0°
            self.servo_max_us = 2400  # Adjust if it buzzes at 180°

            self.stop_motors()
            self.set_servo_angle(3, 90) # Start servo index 3 at neutral center (90°)

        except Exception as e:
            print(f"\nError initializing board/PCA9685: {e}")
            print("\nPlease Enter a Correct Port Name and Press 'Reconnect (BT)' to Try Again...")
            self.board = None

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
            
            if self.board:
                for pin in [IN1, IN2, IN3, IN4]:
                    self.board.set_pin_mode_digital_output(pin)
                self.board.set_pin_mode_i2c()
        except:
            print("\nPlease Enter a Correct Port Name and Press 'Reconnect (BT)' to Try Again...")
            self.board = None

    def close(self):
        print("Closing Connections...")
        try:
            self.board.shutdown()
        except:
            print("\nNo Board to shutdown, closing anyway...")

    # --- SERVO CONTROL VIA TELEMETRIX I2C ---
    def set_servo_angle(self, channel, angle):
        """Moves the SG90 servo on a specific PCA9685 channel (0-15) to a given angle (0-180)."""
        if self.board:
            angle = max(0, min(180, angle))
            
            # Map angle to pulse width in microseconds
            pulse_us = self.servo_min_us + (angle / 180.0) * (self.servo_max_us - self.servo_min_us)
            
            # Convert microseconds to 12-bit PWM ticks (20,000 µs period at 50Hz)
            pulse_ticks = int((pulse_us / 20000.0) * 4096)
            
            # PCA9685 channel registers start at 0x06, 4 bytes per channel
            reg = 0x06 + 4 * channel
            
            on_l = 0
            on_h = 0
            off_l = pulse_ticks & 0xFF
            off_h = (pulse_ticks >> 8) & 0xFF
            
            # Send I2C command to PCA9685
            self.board.i2c_write(PCA9685_ADDR, [reg, on_l, on_h, off_l, off_h])
            print(f"Servo on channel {channel} moved to {angle}° ({pulse_us}µs)")

    # MOTOR INSTRUCTIONS (Unchanged)
    def update_motors(self, forwardSlider, turnSlider):
        fwd_raw = forwardSlider.value()
        trn_raw = turnSlider.value()
        
        fwd_intent = fwd_raw - 49
        trn_intent = trn_raw - 49
        
        deadzone = 2
        if self.board:
            if abs(fwd_intent) > deadzone and abs(fwd_intent) >= abs(trn_intent):
                if fwd_intent > 0:
                    self.set_raw_motors(1, 0, 1, 0)
                    print("Moving FORWARD (Full Speed)")
                else:
                    self.set_raw_motors(0, 1, 0, 1)
                    print("Moving BACKWARD (Full Speed)")
            elif abs(trn_intent) > deadzone:
                if trn_intent > 0:
                    self.set_raw_motors(1, 0, 0, 1)
                    print("Turning RIGHT (Full Speed)")
                else:
                    self.set_raw_motors(0, 1, 1, 0)
                    print("Turning LEFT (Full Speed)")
            else:
                self.stop_motors()
                print("Motors STOPPED")

    def set_raw_motors(self, l_in1, l_in2, r_in1, r_in2):
        if self.board:
            self.board.digital_write(IN1, l_in1)
            self.board.digital_write(IN2, l_in2)
            self.board.digital_write(IN3, r_in1)
            self.board.digital_write(IN4, r_in2)

    def stop_motors(self):
        if self.board:
            self.board.digital_write(IN1, 0)
            self.board.digital_write(IN2, 0)
            self.board.digital_write(IN3, 0)
            self.board.digital_write(IN4, 0)