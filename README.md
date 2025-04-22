# Oscilloscope Simulation

## Overview

This project is an interactive oscilloscope simulation built using Python's Tkinter and Matplotlib. It demonstrates how to visualize time-domain signals using dynamically adjustable parameters. The simulation displays both the input signal (either sine or cosine) and the corresponding sweep and oscilloscope views.

## Purpose & Scope

The program is designed to:
- **Demonstrate Signal Dynamics:** Visualize the input signal and its transformation through a horizontal sweep.
- **Interactive Controls:** Allow users to configure various parameters such as amplitude, frequency factor, phase, sweep factors, and more.
- **Dynamic Theming & Layout:** Change the visual theme and font sizes on the fly to suit user preferences.
- **Educational/Simulation Tool:** Show how a simple oscilloscope might process input signals using real-time plotting techniques.

## Features

- **Input Signal Selection:** Choose between `sin` and `cos` functions to generate the signal. The label updates dynamically (e.g., "Input Signal: y = Asin(wt+phi)").
- **Adjustable Parameters:**
  - **Amplitude (A)**
  - **Angular Frequency Factor (x factor, where ω = x × π)**
  - **Phase (φ) with a toggle between degrees and radians**
  - **Forward and Return Sweep Factors (Tqt and Tqn)**
- **Graphical User Interface (GUI):**
  - Interactive sliders and entry fields with real-time validation.
  - Quick set buttons for predefined phase values.
  - Theme selection with multiple style presets (e.g., Dark Scope, Light, Blueprint).
  - Responsive layout with dynamic redraw of controls.
- **Plot Views:**
  - **Input Signal Plot:** Shows y(t) versus time.
  - **Sweep Plot:** Displays the normalized horizontal sweep.
  - **Oscilloscope View:** Plots the output signal against the sweep position.

## Installation

### Prerequisites

- **Python 3.x**  
- The following Python packages (most of which are usually installed via standard distributions):
  - Tkinter (typically bundled with Python on Windows)
  - Matplotlib
  - NumPy

### Installing Required Packages

If you do not have the required packages, install them via pip:

```bash
pip install matplotlib numpy
```

## Usage Instructions

1. **Run the Application**  
   Launch the simulation by running the main script:
   ```bash
   python oscilloscope.py
   ```

2. **Interacting with the GUI**  
   - **Input Signal Section:**  
     Choose between the `sin` and `cos` options using the radio buttons. The label above automatically updates to reflect your selection (e.g., "Input Signal: y = Asin(wt+phi)").  
     Adjust the amplitude and frequency factor using the corresponding sliders.  
     Set the phase using the slider and entry box, and toggle the phase unit (degrees or radians) using the provided radio buttons.
     
   - **Quick Set Phase:**  
     Use the quick set buttons to instantly apply common phase values.
     
   - **Sweep Parameters:**  
     Adjust the forward (Tqt) and return (Tqn) sweep factors with the provided controls.
     
   - **Theme and Font Size:**  
     Change the GUI appearance by selecting one of the available themes and font sizes from the drop-down boxes in the control panel. The oscilloscope display will update with the new style immediately.

3. **Real-Time Updates**  
   The simulation recalculates the signals and refreshes the plots in real time as you interact with the controls. Any changes to the controls trigger an update to all three plot views:
   - **Input Signal Plot (Axis 1)**
   - **Sweep Time Plot (Axis 2)**
   - **Oscilloscope Screen (Axis 3)**

## Additional Features

- **Error Handling:**  
  User inputs are validated through try/except blocks to ensure that invalid values are caught and handled gracefully.
  
- **Dynamic Resizing:**  
  The quick set buttons and plot areas automatically adjust based on the window size.
  
- **Theming and Customizability:**  
  Three different themes (Dark Scope, Light, Blueprint) are provided. Theme settings include background and foreground colors, grid and spine colors, and even trace colors for various plots.

