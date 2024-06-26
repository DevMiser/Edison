Raspberry Pi’s newest OS (Bookworm) released on December 5, 2023, does not work well with this installation.
For best results, use a Raspberry Pi 4 (not a Raspberry Pi 5) and use the legacy 64-bit OS.
Instructions are in the Important - Please Read file on this repository.

On March 26, 2024, OpenAI updated its billing system to require the pre-purchase of credits in order to use the API for most users.  If you do not pre-purchase credits, you will get an API error.

Also, The i2C interface needs to be turned on in order for the display to show the time (thank you to luckyzero46 for pointing this out).  To do so, open a terminal and enter:

sudo raspi-config

Then use the arrow on your keyboard to scroll down to Interface Options and press Enter.  Next scroll down to I2C and press Enter.  You will be asked whether you want to enable the I2C interface.  Scroll to Yes and press enter.  Then press OK followed by Finish and reboot your Pi.

<img width="507" alt="1" src="https://github.com/DevMiser/Edison/assets/22980908/974a35bc-242d-4440-ab28-e83d991dd81a">
<img width="515" alt="2" src="https://github.com/DevMiser/Edison/assets/22980908/410cfe68-9cf2-4993-a3e9-0ccc085c36b2">
<img width="493" alt="3" src="https://github.com/DevMiser/Edison/assets/22980908/42582045-36a6-4883-ad5c-c6a8237fff66">
<img width="491" alt="4" src="https://github.com/DevMiser/Edison/assets/22980908/643bbb0e-9f71-4397-b364-4157a660582e">
<img width="478" alt="5" src="https://github.com/DevMiser/Edison/assets/22980908/99cbede1-72a6-473a-a6a9-f99ae586e5c9">
<img width="486" alt="6" src="https://github.com/DevMiser/Edison/assets/22980908/d56b2d30-092e-4c88-9ef4-e9ee3d1f948f">
<img width="490" alt="7" src="https://github.com/DevMiser/Edison/assets/22980908/f9ebae96-3a0e-41fd-a904-4acec56cd9c2">
<img width="495" alt="8" src="https://github.com/DevMiser/Edison/assets/22980908/e74c483a-dbc8-4e46-a0dc-2d763d68d796">
<img width="505" alt="9" src="https://github.com/DevMiser/Edison/assets/22980908/2b2fbebc-9ce6-4952-902e-85f6d63a6e24">
<img width="494" alt="10" src="https://github.com/DevMiser/Edison/assets/22980908/71ff0d82-e953-4635-a428-5f27cf944b5c">
<img width="515" alt="11" src="https://github.com/DevMiser/Edison/assets/22980908/d1617e15-6dc4-4eb8-917a-6ac27ec3bc49">
<img width="479" alt="12" src="https://github.com/DevMiser/Edison/assets/22980908/03a8809f-f7a3-44ac-95b8-5f62d2eaa18b">
