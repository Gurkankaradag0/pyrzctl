# PyRzCtl
A windows-platform GUI automation Python module for human beings. Used to programmatically control the mouse.  

## Dependencies
* Razer Synapse 3 or greater is required.  
  Get it with "[Razer Synapse 3](https://www.razer.com/synapse-3)" and install all modules.  
  *No Razer hardware required.*

## Install Project
```python
pip install https://github.com/Gurkankaradag0/pyrzctl/archive/refs/heads/main.zip
```

## Usage
```python
import pyrzctl

if not pyrzctl.init(): # Initialize the RzCtl module. (when you do not do this, the mouse functions will not work.)
    print('Failed to initialize pyrzctl.')

sWidth, sHeight = pyrzctl.size() # Returns two integers, the width and height of the screen. (The primary monitor, in multi-monitor setups.)
x, y = pyrzctl.position() # Returns two integers, the x and y of the mouse cursor's current position.
pyrzctl.moveTo(1080, 50) # Move the mouse to the x, y coordinates 1080, 50.
pyrzctl.click() # Click the mouse at its current location.
pyrzctl.click(500, 500) # Click the mouse at the x, y coordinates 500, 500.
pyrzctl.move(None, 10) # Move mouse 10 pixels down, that is, move the mouse relative to its current position.
pyrzctl.moveTo(1080, 50, duration=2) # Move mouse over 2 seconds.
pyrzctl.dragTo(1080, 500) # Drag the mouse on the x, y coordinates 1080, 500.
pyrzctl.drag(None, 10) # Drag the mouse 10 pixels down, that is, drag the mouse relative to its current position.
pyrzctl.doubleClick() # Double click the mouse at the current position.
pyrzctl.rightClick() # Right click the mouse at the current position.
pyrzctl.middleClick() # Middle click the mouse at the current position.
pyrzctl.tripleClick() # Triple click the mouse at the current position.
```

## Donate
[![Build](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/gurkankrdg)

## Social
[![Linkedin](https://img.shields.io/badge/linkedin-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/g%C3%BCrkan-karada%C4%9F-bb0243205/)
