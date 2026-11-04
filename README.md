# Freecam for Neopets: The Darkest Faerie

Explore Neopets: The Darkest Faerie with a free camera in PCSX2. Fly around the current area, look with a mouse or controller, and move your character to the camera's position.

This is an unofficial, Windows-only tool for the **USA version (SCUS-97367)**. It changes the game's memory while it runs and does not edit your disc image or save files directly. If you save in-game after moving your character, those changes may become part of your save.

## What you need

- Windows
- [PCSX2](https://pcsx2.net/) 2.x, set up with your own game and BIOS
- The USA version of the game (serial SCUS-97367). Other versions won't work.
- [Python 3](https://www.python.org/downloads/). No extra Python packages are needed.
- Optional: an Xbox-style controller

## Download and setup

1. Download this repository as a ZIP and extract it, or clone it.
2. Keep `freecam.bat`, `freecam.py`, and `controls.ini` together in the extracted folder.
3. In PCSX2, open **Tools** and enable **Show Advanced Settings**.
4. Open **Settings > Advanced**.
5. Enable **PINE** and set its port (slot) to **28011**.

You only need to enable PINE once. If you use a different slot, set `pine_slot` in `controls.ini` to match.

## Using it

1. Start the game in PCSX2 and get into play.
2. Double-click **`freecam.bat`**. A console window opens and says "Ready" once it connects. Keep it open.
3. Click into the game window.
4. Press **`P`**, or click **both sticks together** on a controller, to turn the freecam on.

To stop, turn the freecam off before closing the console window. You can also press **Ctrl+C** in the console to stop it and restore the camera.

## Default controls

The controls only work while the game window is in front.

| Action | Keyboard | Controller |
| --- | --- | --- |
| Freecam on or off | `P` | Click both sticks (L3 + R3) |
| **Move your character to the camera** | `C` | LB + RB together |
| Forward, back | `Y` `N` | Left stick |
| Left, right | `B` `M` | Left stick |
| Up, down | `R` `V` | RT, LT |
| Turn left, right | `U` `O` | Right stick |
| Look up, down | `7` `8` | Right stick |
| Slower, faster | `Z` `X` | LB, RB |
| Look with the mouse | Hold right mouse button | |

The numpad also moves the camera, if you have one: `8` `5` `4` `6` are forward, back, left and right, and `9` `7` are up and down.

## Changing the controls

Open **`controls.ini`** in Notepad, change what you like, save it, and restart the freecam.

Each line is an action and what triggers it. For example:

```ini
[keyboard]
forward = UP
toggle = F10

[controller]
toggle = BACK+START
teleport = A+B
forward = DPAD_UP
```

- **Two ways to do one thing:** use a comma, as in `forward = Y, UP`.
- **Buttons held together:** use a plus, as in `toggle = L3+R3`.
- **Turn something off:** leave it empty, as in `turn_left =`.
- **Swap the sticks:** set `move_stick` and `look_stick` to `left`, `right` or `none`.
- **Speeds and inverted look** are under `[settings]`.
- **To let your character keep moving** while flying, set `freeze_player = no`.

If you use an unrecognised key or button name, the console tells you which one needs fixing.

### Names you can use

**Keyboard:**
- Letters `A` to `Z` and numbers `0` to `9`
- `F1` to `F12`, and the numpad as `NUM0` to `NUM9`
- `UP` `DOWN` `LEFT` `RIGHT`
- `SPACE` `TAB` `ENTER` `BACKSPACE` `SHIFT` `CTRL` `ALT`
- `HOME` `END` `PAGEUP` `PAGEDOWN` `INSERT` `DELETE`
- `COMMA` `PERIOD` `SLASH` `SEMICOLON` `QUOTE` `MINUS` `EQUALS`
- `MOUSE_LEFT` `MOUSE_RIGHT` `MOUSE_MIDDLE`

**Controller:**
- `A` `B` `X` `Y`
- `LB` `RB` `LT` `RT`
- `L3` `R3` (clicking the sticks)
- `DPAD_UP` `DPAD_DOWN` `DPAD_LEFT` `DPAD_RIGHT`
- `START` `BACK`

### Avoiding clashes

Your controls also reach PCSX2, so check them against its own settings:

- **PCSX2's pad:** a key or button mapped to the game's pad still reaches it. With `freeze_player = yes`, your character ignores the pad while the freecam is on, but the toggle button can reach the game when you turn it off. Check your PCSX2 controller bindings if an action also triggers in the game.
- **PCSX2's hotkeys:** check your hotkey bindings for clashes, especially if you change the freecam controls.
- **Combinations:** a button in a held combination doesn't also count alone, so `LB + RB` moves your character without changing speed.

## Good to know

- **Moving your character** puts them at the camera's exact spot, and they fall to the ground from there. Fly low over solid ground first. Over a pit, or from very high up, they may fall a long way or die, so save first.
- **Stay in the area you're in.** Moving your character far away into another world isn't supported, and can freeze the game or garble the screen.
- **Close any text box first.**
- **After a move,** your character may step forward a little when you turn the freecam off.
- **With the default `freeze_player = yes`,** your character ignores the pad and stays in place horizontally while the freecam is on. They can still fall.
- **The camera flies through walls,** and you may see gaps in the world.
- **Loading a new area or a cutscene** can turn the freecam off. Turn it on again afterwards.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| "Waiting for PCSX2" and nothing else | Start the game, enable **Tools > Show Advanced Settings**, then open **Settings > Advanced** and enable **PINE**. Set its port (slot) to **28011**, matching `pine_slot` in `controls.ini` |
| "This only works with the USA disc" | It needs serial SCUS-97367 |
| "Python wasn't found" | Install Python 3 from python.org, then try again |
| Controls do nothing | Click into the game window so it's in front |
| Controller does nothing | It needs to be Xbox-style (XInput). Try the keyboard keys to check the rest works |
| The camera's stuck, or your character won't move | The freecam was closed while it was on. Start it and turn it on and off, or restart the game |
| Your character keeps running off | Check `freeze_player = yes` in `controls.ini` |

## Files

| File | What it is |
| --- | --- |
| `freecam.bat` | Double-click to start |
| `controls.ini` | Your controls and settings |
| `freecam.py` | The program |
| `README.md` | Setup, controls, and troubleshooting |

## Reporting problems

When opening an issue, include your PCSX2 and Python versions, confirm the game's serial is `SCUS-97367`, and describe what happened. Include any error text from the console and any controls you changed.
