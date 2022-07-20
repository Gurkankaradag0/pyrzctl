# PyRzCtl lets Python control the mouse, and other GUI automation tasks. For Windows
# on Python 3.
# https://github.com/Gurkankaradag0/pyrzctl
# Gurkan Karadag gurkan.karadag.1907@gmail.com (Send me feedback & suggestions!)

# TODO - the following features are half-implemented right now:
# primary secondary mouse button awareness

__version__ = "0.1.1"

import sys
import time
import datetime
import platform
import functools

class PyRzCtlException(Exception):
  """
  PyRzCtl code will raise this exception class for any invalid actions. If PyRzCtl raises some other exception,
  you should assume that this is caused by a bug in PyRzCtl itself. (Including a failure to catch potential
  exceptions raised by PyRzCtl.)
  """

  pass

class FailSafeException(PyRzCtlException):
  """
  This exception is raised by PyRzCtl functions when the user puts the mouse cursor into one of the "failsafe
  points" (by default, one of the four corners of the primary monitor). This exception shouldn't be caught; it's
  meant to provide a way to terminate a misbehaving script.
  """

  pass

if sys.version_info[0:2] in ((3, 1), (3, 2)):
  # Python 3.1 and 3.2 uses collections.Sequence
  import collections

  collectionsSequence = collections.Sequence
else:
  # Python 3.3+ uses collections.abc.Sequence
  import collections.abc

  collectionsSequence = collections.abc.Sequence  # type: ignore

LEFT = "left"
MIDDLE = "middle"
RIGHT = "right"
PRIMARY = "primary"
SECONDARY = "secondary"

if sys.platform.startswith("java"):
  # from . import _rzctl_java as platformModule
  raise NotImplementedError("Jython is not yet supported by RzCtl.")
elif sys.platform == "darwin":
  # from . import _rzctl_osx as platformModule
  raise NotImplementedError("darwin is not yet supported by RzCtl.")
elif sys.platform == "win32":
  from . import _rzctl_win as platformModule
elif platform.system() == "Linux":
  # from . import _rzctl_x11 as platformModule
  raise NotImplementedError("Linux is not yet supported by RzCtl.")
else:
  raise NotImplementedError("Your platform (%s) is not supported by RzCtl." % (platform.system()))

MINIMUM_DURATION = 0.1
MINIMUM_SLEEP = 0.05
PAUSE = 0.1 
FAILSAFE = True
FAILSAFE_POINTS = [(0, 0)]
LOG_SCREENSHOTS = False
LOG_SCREENSHOTS_LIMIT = 10
G_LOG_SCREENSHOTS_FILENAMES = []

def _genericPyRzCtlChecks(wrappedFunction):
  """
  A decorator that calls failSafeCheck() before the decorated function and
  _handlePause() after it.
  """

  @functools.wraps(wrappedFunction)
  def wrapper(*args, **kwargs):
    failSafeCheck()
    returnVal = wrappedFunction(*args, **kwargs)
    _handlePause(kwargs.get("_pause", True))
    return returnVal

  return wrapper

Point = collections.namedtuple("Point", "x y")
Size = collections.namedtuple("Size", "width height")

# General Functions
# =================

def init():
  """
  Initializes the RzCtl module.
  """

  return platformModule._init()

def getPointOnLine(x1, y1, x2, y2, n):
  """
  Returns an (x, y) tuple of the point that has progressed a proportion ``n`` along the line defined by the two
  ``x1``, ``y1`` and ``x2``, ``y2`` coordinates.

  This function was copied from pytweening module, so that it can be called even if PyTweening is not installed.
  """
  x = ((x2 - x1) * n) + x1
  y = ((y2 - y1) * n) + y1
  return (x, y)

def linear(n):
  """
  Returns ``n``, where ``n`` is the float argument between ``0.0`` and ``1.0``. This function is for the default
  linear tween for mouse moving functions.

  This function was copied from PyTweening module, so that it can be called even if PyTweening is not installed.
  """

  # We use this function instead of pytweening.linear for the default tween function just in case pytweening couldn't be imported.
  if not 0.0 <= n <= 1.0:
    raise PyRzCtlException("Argument must be between 0.0 and 1.0.")
  return n

def _handlePause(_pause):
  """
  A helper function for performing a pause at the end of a PyRzCtl function based on some settings.

  If ``_pause`` is ``True``, then sleep for ``PAUSE`` seconds (the global pause setting).
  """
  if _pause:
    assert isinstance(PAUSE, int) or isinstance(PAUSE, float)
    time.sleep(PAUSE)

def position(x=None, y=None):
  """
  Returns the current xy coordinates of the mouse cursor as a two-integer tuple.

  Args:
    x (int, None, optional) - If not None, this argument overrides the x in
      the return value.
    y (int, None, optional) - If not None, this argument overrides the y in
      the return value.

  Returns:
    (x, y) tuple of the current xy coordinates of the mouse cursor.

  NOTE: The position() function doesn't check for failsafe.
  """
  posx, posy = platformModule._position()
  posx = int(posx)
  posy = int(posy)
  if x is not None:  # If set, the x parameter overrides the return value.
    posx = int(x)
  if y is not None:  # If set, the y parameter overrides the return value.
    posy = int(y)
  return Point(posx, posy)

def size():
  """Returns the width and height of the screen as a two-integer tuple.

  Returns:
    (width, height) tuple of the screen size, in pixels.
  """
  return Size(*platformModule._size())

# Mouse Functions
# ===============

"""
NOTE: Although "mouse1" and "mouse2" buttons usually refer to the left and
right mouse buttons respectively, in PyRzCtl 1, 2, and 3 refer to the left,
middle, and right buttons, respectively. This is because Xlib interprets
button 2 as the middle button and button 3 as the right button, so we hold
that for Windows and macOS as well (since those operating systems don't use
button numbers but rather just "left" or "right").
"""

def _normalizeButton(button):
  """
  The left, middle, and right mouse buttons are button numbers 1, 2, and 3 respectively. This is the numbering that
  Xlib on Linux uses (while Windows and macOS don't care about numbers; they just use "left" and "right").

  This function takes one of ``LEFT``, ``MIDDLE``, ``RIGHT``, ``PRIMARY``, ``SECONDARY``, ``1``, ``2``, ``3``, ``4``,
  ``5``, ``6``, or ``7`` for the button argument and returns either ``LEFT``, ``MIDDLE``, ``RIGHT``, ``4``, ``5``,
  ``6``, or ``7``. The ``PRIMARY``, ``SECONDARY``, ``1``, ``2``, and ``3`` values are never returned.

  The ``'left'`` and ``'right'`` mouse buttons will always refer to the physical left and right
  buttons on the mouse. The same applies for buttons 1 and 3.

  However, if ``button`` is ``'primary'`` or ``'secondary'``, then we must check if
  the mouse buttons have been "swapped" (for left-handed users) by the operating system's mouse
  settings.

  If the buttons are swapped, the primary button is the right mouse button and the secondary button is the left mouse
  button. If not swapped, the primary and secondary buttons are the left and right buttons, respectively.

  NOTE: Swap detection has not been implemented yet.
  """
  # TODO - The swap detection hasn't been done yet. For Windows, see https://stackoverflow.com/questions/45627956/check-if-mouse-buttons-are-swapped-or-not-in-c
  # TODO - We should check the OS settings to see if it's a left-hand setup, where button 1 would be "right".

  # Check that `button` has a valid value:
  button = button.lower()

  # Check for valid button arg on Windows:
  if button not in (LEFT, MIDDLE, RIGHT, PRIMARY, SECONDARY, 1, 2, 3):
    raise PyRzCtlException(
      "button argument must be one of ('left', 'middle', 'right', 'primary', 'secondary', 1, 2, 3)"
    )

  # TODO - Check if the primary/secondary mouse buttons have been swapped:
  if button in (PRIMARY, SECONDARY):
    swapped = False  # TODO - Add the operating system-specific code to detect mouse swap later.
    if swapped:
      if button == PRIMARY:
        return RIGHT
      elif button == SECONDARY:
        return LEFT
    else:
      if button == PRIMARY:
        return LEFT
      elif button == SECONDARY:
        return RIGHT

  # Return a mouse button integer value, not a string like 'left':
  return {LEFT: LEFT, MIDDLE: MIDDLE, RIGHT: RIGHT, 1: LEFT, 2: MIDDLE, 3: RIGHT, 4: 4, 5: 5, 6: 6, 7: 7}[button]

@_genericPyRzCtlChecks
def mouseDown(x=None, y=None, button=PRIMARY, duration=0.0, tween=linear, _pause=True):
  """Performs pressing a mouse button down (but not up).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      mouse down happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      mouse down happens. None by default.
    button (str, int, optional): The mouse button pressed down. TODO

  Returns:
    None

  Raises:
    PyRzCtlException: If button is not one of 'left', 'middle', 'right', 1, 2, or 3
  """

  button = _normalizeButton(button)
  if x is None and y is None:
    x, y = position()

  _mouseMoveDrag("move", x, y, 0, 0, duration=0, tween=None)
  platformModule._mouseDown(x, y, button)

@_genericPyRzCtlChecks
def mouseUp(x=None, y=None, button=PRIMARY, duration=0.0, tween=linear, _pause=True):
  """Performs releasing a mouse button up (but not down beforehand).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      mouse up happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      mouse up happens. None by default.
    button (str, int, optional): The mouse button released. TODO

  Returns:
    None

  Raises:
    PyRzCtlException: If button is not one of 'left', 'middle', 'right', 1, 2, or 3
  """

  button = _normalizeButton(button)
  if x is None and y is None:
    x, y = position()

  _mouseMoveDrag("move", x, y, 0, 0, duration=0, tween=None)
  platformModule._mouseUp(x, y, button)

@_genericPyRzCtlChecks
def click(
    x=None, y=None, clicks=1, interval=0.0, button=PRIMARY, duration=0.0, tween=linear, _pause=True
):
  """
  Performs pressing a mouse button down and then immediately releasing it. Returns ``None``.

  When no arguments are passed, the primary mouse button is clicked at the mouse cursor's current location.

  If integers for ``x`` and ``y`` are passed, the click will happen at that XY coordinate. If ``x`` is a string, the
  string is an image filename that PyRzCtl will attempt to locate on the screen and click the center of. If ``x``
  is a sequence of two coordinates, those coordinates will be used for the XY coordinate to click on.

  The ``clicks`` argument is an int of how many clicks to make, and defaults to ``1``.

  The ``interval`` argument is an int or float of how many seconds to wait in between each click, if ``clicks`` is
  greater than ``1``. It defaults to ``0.0`` for no pause in between clicks.

  The ``button`` argument is one of the constants ``LEFT``, ``MIDDLE``, ``RIGHT``, ``PRIMARY``, or ``SECONDARY``.
  It defaults to ``PRIMARY`` (which is the left mouse button, unless the operating system has been set for
  left-handed users.)

  If ``x`` and ``y`` are specified, and the click is not happening at the mouse cursor's current location, then
  the ``duration`` argument is an int or float of how many seconds it should take to move the mouse to the XY
  coordinates. It defaults to ``0`` for an instant move.

  If ``x`` and ``y`` are specified and ``duration`` is not ``0``, the ``tween`` argument is a tweening function
  that specifies the movement pattern of the mouse cursor as it moves to the XY coordinates. The default is a
  simple linear tween. See the PyTweening module documentation for more details.

  The ``pause`` parameter is deprecated. Call the ``PyRzCtl.sleep()`` function to implement a pause.

  Raises:
    PyRzCtlException: If button is not one of 'left', 'middle', 'right', 1, 2, 3
  """
  # TODO: I'm leaving buttons 4, 5, 6, and 7 undocumented for now. I need to understand how they work.
  button = _normalizeButton(button)
  if x is None and y is None:
    x, y = position()

  _mouseMoveDrag("move", x, y, 0, 0, duration, tween)
  time.sleep(0.007)
  for i in range(clicks):
    failSafeCheck()
    if button in (LEFT, MIDDLE, RIGHT):
      platformModule._click(x, y, button)

    time.sleep(interval)

@_genericPyRzCtlChecks
def leftClick(x=None, y=None, interval=0.0, duration=0.0, tween=linear, _pause=True):
  """Performs a left mouse button click.

  This is a wrapper function for click('left', x, y).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      click happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      click happens. None by default.
    interval (float, optional): The number of seconds in between each click,
      if the number of clicks is greater than 1. 0.0 by default, for no
      pause in between clicks.

  Returns:
    None
  """

  # TODO - Do we need the decorator for this function? Should click() handle this? (Also applies to other alias functions.)
  click(x, y, 1, interval, LEFT, duration, tween, _pause=_pause)

@_genericPyRzCtlChecks
def rightClick(x=None, y=None, interval=0.0, duration=0.0, tween=linear, _pause=True):
  """Performs a right mouse button click.

  This is a wrapper function for click('right', x, y).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      click happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      click happens. None by default.
    interval (float, optional): The number of seconds in between each click,
      if the number of clicks is greater than 1. 0.0 by default, for no
      pause in between clicks.

  Returns:
    None
  """
  click(x, y, 1, interval, RIGHT, duration, tween, _pause=_pause)

@_genericPyRzCtlChecks
def middleClick(x=None, y=None, interval=0.0, duration=0.0, tween=linear, _pause=True):
  """Performs a middle mouse button click.

  This is a wrapper function for click('middle', x, y).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      click happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      click happens. None by default.

  Returns:
    None
  """
  click(x, y, 1, interval, MIDDLE, duration, tween, _pause=_pause)

@_genericPyRzCtlChecks
def doubleClick(x=None, y=None, interval=0.0, button=LEFT, duration=0.0, tween=linear, _pause=True):
  """Performs a double click.

  This is a wrapper function for click('left', x, y, 2, interval).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      click happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      click happens. None by default.
    interval (float, optional): The number of seconds in between each click,
      if the number of clicks is greater than 1. 0.0 by default, for no
      pause in between clicks.
    button (str, int, optional): The mouse button released. TODO

  Returns:
    None

  Raises:
    PyRzCtlException: If button is not one of 'left', 'middle', 'right', 1, 2, 3, 4,
      5, 6, or 7
  """
  click(x, y, 2, interval, button, duration, tween, _pause=False)

@_genericPyRzCtlChecks
def tripleClick(x=None, y=None, interval=0.0, button=LEFT, duration=0.0, tween=linear, _pause=True):
  """Performs a triple click.

  This is a wrapper function for click('left', x, y, 3, interval).

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      click happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      click happens. None by default.
    interval (float, optional): The number of seconds in between each click,
      if the number of clicks is greater than 1. 0.0 by default, for no
      pause in between clicks.
    button (str, int, optional): The mouse button released. TODO

  Returns:
    None

  Raises:
    PyRzCtlException: If button is not one of 'left', 'middle', 'right', 1, 2, 3, 4,
      5, 6, or 7
  """
  click(x, y, 3, interval, button, duration, tween, _pause=False)

@_genericPyRzCtlChecks
def moveTo(x=None, y=None, duration=0.0, tween=linear, _pause=True):
  """Moves the mouse cursor to a point on the screen.

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): The x position on the screen where the
      click happens. None by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): The y position on the screen where the
      click happens. None by default.
    duration (float, optional): The amount of time it takes to move the mouse
      cursor to the xy coordinates. If 0, then the mouse cursor is moved
      instantaneously. 0.0 by default.
    tween (func, optional): The tweening function used if the duration is not
      0. A linear tween is used by default.

  Returns:
    None
  """
  _mouseMoveDrag("move", x, y, 0, 0, duration, tween)

@_genericPyRzCtlChecks
def moveRel(xOffset=None, yOffset=None, duration=0.0, tween=linear, _pause=True):
  """Moves the mouse cursor to a point on the screen, relative to its current
  position.

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): How far left (for negative values) or
      right (for positive values) to move the cursor. 0 by default. If tuple, this is used for x and y.
    y (int, float, None, optional): How far up (for negative values) or
      down (for positive values) to move the cursor. 0 by default.
    duration (float, optional): The amount of time it takes to move the mouse
      cursor to the new xy coordinates. If 0, then the mouse cursor is moved
      instantaneously. 0.0 by default.
    tween (func, optional): The tweening function used if the duration is not
      0. A linear tween is used by default.

  Returns:
    None
  """

  _mouseMoveDrag("move", None, None, xOffset, yOffset, duration, tween)

move = moveRel  # For PyRzCtl 1.0, move() replaces moveRel().

@_genericPyRzCtlChecks
def dragTo(
    x=None, y=None, duration=0.11, tween=linear, button=PRIMARY, _pause=True, mouseDownUp=True
):
  """Performs a mouse drag (mouse movement while a button is held down) to a
  point on the screen.

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): How far left (for negative values) or
      right (for positive values) to move the cursor. 0 by default. If tuple, this is used for x and y.
      If x is a str, it's considered a filename of an image to find on
      the screen with locateOnScreen() and click the center of.
    y (int, float, None, optional): How far up (for negative values) or
      down (for positive values) to move the cursor. 0 by default.
    duration (float, optional): The amount of time it takes to move the mouse
      cursor to the new xy coordinates. If 0, then the mouse cursor is moved
      instantaneously. 0.0 by default.
    tween (func, optional): The tweening function used if the duration is not
      0. A linear tween is used by default.
    button (str, int, optional): The mouse button released. TODO
    mouseDownUp (True, False): When true, the mouseUp/Down actions are not perfomed.
      Which allows dragging over multiple (small) actions. 'True' by default.

  Returns:
    None
  """
  
  if x is None and y is None:
    x, y = position()

  if mouseDownUp:
    mouseDown(button=button, _pause=False)
  _mouseMoveDrag("drag", x, y, 0, 0, duration, tween, button)
  if mouseDownUp:
    mouseUp(button=button, _pause=False)

@_genericPyRzCtlChecks
def dragRel(
    xOffset=0, yOffset=0, duration=0.11, tween=linear, button=PRIMARY, _pause=True, mouseDownUp=True
):
  """Performs a mouse drag (mouse movement while a button is held down) to a
  point on the screen, relative to its current position.

  The x and y parameters detail where the mouse event happens. If None, the
  current mouse position is used. If a float value, it is rounded down. If
  outside the boundaries of the screen, the event happens at edge of the
  screen.

  Args:
    x (int, float, None, tuple, optional): How far left (for negative values) or
      right (for positive values) to move the cursor. 0 by default. If tuple, this is used for xOffset and yOffset.
    y (int, float, None, optional): How far up (for negative values) or
      down (for positive values) to move the cursor. 0 by default.
    duration (float, optional): The amount of time it takes to move the mouse
      cursor to the new xy coordinates. If 0, then the mouse cursor is moved
      instantaneously. 0.0 by default.
    tween (func, optional): The tweening function used if the duration is not
      0. A linear tween is used by default.
    button (str, int, optional): The mouse button released. TODO
    mouseDownUp (True, False): When true, the mouseUp/Down actions are not perfomed.
      Which allows dragging over multiple (small) actions. 'True' by default.

  Returns:
    None
  """
  if xOffset is None:
    xOffset = 0
  if yOffset is None:
    yOffset = 0

  if type(xOffset) in (tuple, list):
    xOffset, yOffset = xOffset[0], xOffset[1]

  if xOffset == 0 and yOffset == 0:
    return  # no-op case

  mousex, mousey = platformModule._position()

  if mouseDownUp:
    mouseDown(button=button, _pause=False)
  _mouseMoveDrag("drag", mousex, mousey, xOffset, yOffset, duration, tween, button)
  if mouseDownUp:
    mouseUp(button=button, _pause=False)

drag = dragRel

def _mouseMoveDrag(moveOrDrag, x, y, xOffset, yOffset, duration, tween=linear, button=None):
  """Handles the actual move or drag event, since different platforms
  implement them differently.

  On Windows & Linux, a drag is a normal mouse move while a mouse button is
  held down. On OS X, a distinct "drag" event must be used instead.

  The code for moving and dragging the mouse is similar, so this function
  handles both. Users should call the moveTo() or dragTo() functions instead
  of calling _mouseMoveDrag().

  Args:
    moveOrDrag (str): Either 'move' or 'drag', for the type of action this is.
    x (int, float, None, optional): How far left (for negative values) or
      right (for positive values) to move the cursor. 0 by default.
    y (int, float, None, optional): How far up (for negative values) or
      down (for positive values) to move the cursor. 0 by default.
    xOffset (int, float, None, optional): How far left (for negative values) or
      right (for positive values) to move the cursor. 0 by default.
    yOffset (int, float, None, optional): How far up (for negative values) or
      down (for positive values) to move the cursor. 0 by default.
    duration (float, optional): The amount of time it takes to move the mouse
      cursor to the new xy coordinates. If 0, then the mouse cursor is moved
      instantaneously. 0.0 by default.
    tween (func, optional): The tweening function used if the duration is not
      0. A linear tween is used by default.
    button (str, int, optional): The mouse button released. TODO

  Returns:
    None
  """

  # The move and drag code is similar, but OS X requires a special drag event instead of just a move event when dragging.
  # See https://stackoverflow.com/a/2696107/1893164
  assert moveOrDrag in ("move", "drag"), "moveOrDrag must be in ('move', 'drag'), not %s" % (moveOrDrag)

  moveOrDrag = "move" 

  xOffset = int(xOffset) if xOffset is not None else 0
  yOffset = int(yOffset) if yOffset is not None else 0

  if x is None and y is None and xOffset == 0 and yOffset == 0:
    return  # Special case for no mouse movement at all.

  startx, starty = position()

  x = int(x) if x is not None else startx
  y = int(y) if y is not None else starty

  # x, y, xOffset, yOffset are now int.
  x += xOffset
  y += yOffset

  width, height = size()

  # Make sure x and y are within the screen bounds.
  # x = max(0, min(x, width - 1))
  # y = max(0, min(y, height - 1))

  # If the duration is small enough, just move the cursor there instantly.
  steps = [(x, y)]

  if duration > MINIMUM_DURATION:
    # Non-instant moving/dragging involves tweening:
    num_steps = max(width, height)
    sleep_amount = duration / num_steps
    if sleep_amount < MINIMUM_SLEEP:
      num_steps = int(duration / MINIMUM_SLEEP)
      sleep_amount = duration / num_steps

    steps = [getPointOnLine(startx, starty, x, y, tween(n / num_steps)) for n in range(num_steps)]
    # Making sure the last position is the actual destination.
    steps.append((x, y))

  for tweenX, tweenY in steps:
    if len(steps) > 1:
      # A single step does not require tweening.
      time.sleep(sleep_amount)

    tweenX = int(round(tweenX))
    tweenY = int(round(tweenY))

    # Do a fail-safe check to see if the user moved the mouse to a fail-safe position, but not if the mouse cursor
    # moved there as a result of a this function. (Just because tweenX and tweenY aren't in a fail-safe position
    # doesn't mean the user couldn't have moved the mouse cursor to a fail-safe position.)
    if (tweenX, tweenY) not in FAILSAFE_POINTS:
      failSafeCheck()

    if moveOrDrag == "move":
      platformModule._moveTo(tweenX, tweenY)
    elif moveOrDrag == "drag":
      platformModule._dragTo(tweenX, tweenY, button)
    else:
      raise NotImplementedError("Unknown value of moveOrDrag: {0}".format(moveOrDrag))

  if (tweenX, tweenY) not in FAILSAFE_POINTS:
    failSafeCheck()

def failSafeCheck():
  if FAILSAFE and tuple(position()) in FAILSAFE_POINTS:
    raise FailSafeException(
      "PyRzCtl fail-safe triggered from mouse moving to a corner of the screen. To disable this fail-safe, set pyrzctl.FAILSAFE to False. DISABLING FAIL-SAFE IS NOT RECOMMENDED."
    )

def printInfo(dontPrint=False):
  msg = '''
        Platform: {}
  Python Version: {}
 PyRzctl Version: {}
      Executable: {}
      Resolution: {}
       Timestamp: {}'''.format(*getInfo())
  if not dontPrint:
    print(msg)
  return msg

def getInfo():
  return (sys.platform, sys.version, __version__, sys.executable, size(), datetime.datetime.now())