# Testing in the EdgeTX simulator (no radio / no SD card needed)

EdgeTX Companion 2.12 is installed and includes the **TX15 simulator**
(`libedgetx-tx15-simulator.dylib`), so you can drive the model — sticks,
switches, channel monitor, gimbal LEDs, sounds — entirely on the Mac.

## One-time: point the simulator at this repo's SD folder

1. Open **EdgeTX Companion 2.12**.
2. **Settings → Application Settings → Profiles** (or the toolbar profile): set
   **Radio type = RadioMaster TX15**, firmware 2.12.
3. **Settings → … → set the "SD structure path"** to a working SD folder. Easiest
   is to deploy this repo into a throwaway SD folder and point Companion there:
   ```bash
   ./deploy.sh ~/tx15-sim-sd      # creates/fills a sim SD tree from sdcard/
   ```
   Then set Companion's SD path to `~/tx15-sim-sd`.
   (That folder also needs the full EdgeTX SD contents — sounds/scripts — so grab
   them once via Companion's **SD card** download, or copy a known-good card into
   `~/tx15-sim-sd` first, then `./deploy.sh ~/tx15-sim-sd` on top.)

## Each test cycle

```bash
python3 build_model.py      # regenerate sdcard/MODELS/model3.yml from CONFIG
./deploy.sh ~/tx15-sim-sd   # push model + scripts into the sim SD
```
Then in Companion: **Tools → Simulate radio** (or open the radio profile and click
**Simulate**). Select **model3 / ANT**.

### What to check in the sim
- **Channel Monitor** (usually a tab/outputs page): move sticks/switches and watch
  CH1/CH2/CH3. Confirm the weapon channel sits where expected when disarmed.
- **Switches/sticks:** SE (arm), SA, SF, and the gimbals — drag them with the mouse.
- **Gimbal LEDs:** the sim renders the RGB rings, so `combat.lua` is testable here.
- **Sounds:** arm/disarm/alarm tracks play through the Mac.

## Why this workflow
Edit `build_model.py` CONFIG (or the Lua) → regenerate → test in the sim → commit →
`./deploy.sh` to the real card only once it's right. The card is never the source
of truth, so a flaky/corrupt SD can't lose your config again.
