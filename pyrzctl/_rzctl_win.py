# Windows implementation of PyRzCtl functions.
# BSD license
# Gurkan Karadag gurkan.karadag.1907@gmail.com

import ctypes
import ctypes.wintypes
import pyrzctl
from pyrzctl import LEFT, MIDDLE, RIGHT
from time import sleep
import os

import sys
if sys.platform !=  'win32':
  raise Exception('The pyrzctl_win module should only be loaded on a Windows system.')

dllpath = os.path.dirname(os.path.abspath(__file__)) + "/rzctl_dll.dll"

try:
    Crzctl = ctypes.CDLL(dllpath)
except Exception as e:
    raise Exception(e)

LEFT_DOWN = 1
LEFT_UP = 2
RIGHT_DOWN = 4
RIGHT_UP = 8
SCROLL_CLICK_DOWN = 16
SCROLL_CLICK_UP = 32
BACK_DOWN = 64
BACK_UP = 128
FOWARD_DOWN = 256
FOWARD_UP = 512
SCROLL_DOWN = 4287104000
SCROLL_UP = 7865344

# This ctypes structure is for a Win32 POINT structure,
# which is documented here: http://msdn.microsoft.com/en-us/library/windows/desktop/dd162805(v=vs.85).aspx
# The POINT structure is used by GetCursorPos().
class POINT(ctypes.Structure):
  _fields_ = [("x", ctypes.c_long),
              ("y", ctypes.c_long)]

def _init():
  """
  Initializes the RzCtl module.
  """

  return Crzctl.init()

def _position():
  """Returns the current xy coordinates of the mouse cursor as a two-integer
  tuple by calling the GetCursorPos() win32 function.

  Returns:
    (x, y) tuple of the current xy coordinates of the mouse cursor.
  """

  cursor = POINT()
  ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor))
  return (cursor.x, cursor.y)

def _size():
  """Returns the width and height of the screen as a two-integer tuple.

  Returns:
    (width, height) tuple of the screen size, in pixels.
  """
  return (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))

def _moveTo(x, y):
  """Send the mouse move event to Windows by calling SetCursorPos() win32
  function.

  Args:
    button (str): The mouse button, either 'left', 'middle', or 'right'
    x (int): The x position of the mouse event.
    y (int): The y position of the mouse event.

  Returns:
    None
  """
  width, height = _size()
  convertedX = 65536 * x // width + 1
  convertedY = 65536 * y // height + 1

  Crzctl.move(convertedX, convertedY, False)

def _mouseDown(x, y, button):
  """Send the mouse down event to Windows by calling the mouse_event() win32
  function.

  Args:
    x (int): The x position of the mouse event.
    y (int): The y position of the mouse event.
    button (str): The mouse button, either 'left', 'middle', or 'right'

  Returns:
    None
  """
  if button not in (LEFT, MIDDLE, RIGHT):
    raise ValueError('button arg to _click() must be one of "left", "middle", or "right", not %s' % button)

  if button == LEFT:
    EV = LEFT_DOWN
  elif button == MIDDLE:
    EV = SCROLL_CLICK_DOWN
  elif button == RIGHT:
    EV = RIGHT_DOWN

  try:
    _sendMouseEvent(EV, x, y)
  except (PermissionError, OSError):
    pass

def _mouseUp(x, y, button):
  """Send the mouse up event to Windows by calling the mouse_event() win32
  function.

  Args:
    x (int): The x position of the mouse event.
    y (int): The y position of the mouse event.
    button (str): The mouse button, either 'left', 'middle', or 'right'

  Returns:
    None
  """
  if button not in (LEFT, MIDDLE, RIGHT):
    raise ValueError('button arg to _click() must be one of "left", "middle", or "right", not %s' % button)

  if button == LEFT:
    EV = LEFT_UP
  elif button == MIDDLE:
    EV = SCROLL_CLICK_UP
  elif button == RIGHT:
    EV = RIGHT_UP

  try:
    _sendMouseEvent(EV, x, y)
  except (PermissionError, OSError):
    pass


def _click(x, y, button):
  """Send the mouse click event to Windows by calling the mouse_event() win32
  function.

  Args:
    button (str): The mouse button, either 'left', 'middle', or 'right'
    x (int): The x position of the mouse event.
    y (int): The y position of the mouse event.

  Returns:
    None
  """
  if button not in (LEFT, MIDDLE, RIGHT):
    raise ValueError('button arg to _click() must be one of "left", "middle", or "right", not %s' % button)

  _mouseDown(x, y, button)
  _mouseUp(x, y, button)


def _sendMouseEvent(ev, x, y, dwData=0):
  """The helper function that actually makes the call to the mouse_event()
  win32 function.

  Args:
    ev (int): The win32 code for the mouse event. Use one of the MOUSEEVENTF_*
    constants for this argument.
    x (int): The x position of the mouse event.
    y (int): The y position of the mouse event.
    dwData (int): The argument for mouse_event()'s dwData parameter. So far
      this is only used by mouse scrolling.

  Returns:
    None
  """
  assert x != None and y != None, 'x and y cannot be set to None'

  width, height = _size()
  convertedX = 65536 * x // width + 1
  convertedY = 65536 * y // height + 1

  Crzctl.move(convertedX, convertedY, False)
  Crzctl.click(ev)