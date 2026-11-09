# Arduino Precision Syringe Pump

An automated microfluidic syringe pump system controlled via Arduino Nano and a custom Python desktop interface.

## Features
- **Non-blocking Stepper Control:** Driven by `AccelStepper` in half-step mode (4076 steps/rev).
- **Desktop GUI:** Built with Python (`Tkinter` / `pyserial`) with manual jogging controls.
- **Pseudo-AI / NLP Parsing:** Natural language command input (volume injection, refill, zeroing).
- **Syringe Calibration Profiles:** Preset configurations for Hamilton, Popper, and CarlRoth syringes.

## Hardware Components
- Arduino Nano (ATmega328P)
- 28BYJ-48 5V Stepper Motor + ULN2003 Driver Board
- M3 Lead Screw (0.5 mm pitch)
- External 5V Power Supply (Shared GND)

## Quick Start
1. Flash `firmware/syringe_pump/syringe_pump.ino` using Arduino IDE.
2. Install Python requirements:
   ```bash
   pip install -r gui/requirements.txt