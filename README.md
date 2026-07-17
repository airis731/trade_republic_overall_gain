# Trade Republic Overall Gain Calculator

This simple tool helps you calculate your total investment performance using data from Trade Republic.

## Before You Start
This tool uses a programming language called **Python**. You need to have it installed on your computer to run the script.
- If you aren't sure if you have it, open your terminal (Command Prompt/Terminal) and type `python --version`. If it shows a number, you are good to go!
- If not, download and install it from [python.org](https://www.python.org/).

## How to use this tool

### 1. Download the code
If you haven't already, open your terminal and type:
`git clone https://github.com/airis731/trade_republic_overall_gain.git`
Then move into the folder:
`cd trade_republic_overall_gain`

### 2. Prepare your Data
You need to export your account data from Trade Republic as a CSV file. Save this file into the `trade_republic_overall_gain` folder you just downloaded.

### 3. Install the helpers
The script needs a few extra "tools" to work. To get them, run this command in your terminal:
`pip install -r requirements.txt`

### 4. Run the Calculator
Now, simply run the script by typing:
`python main.py`
*(Note: If the main file has a different name, replace `main.py` with that name.)*

## Troubleshooting
- **"Command not found":** This usually means Python isn't installed correctly or isn't added to your computer's "Path" settings.
- **"Permission Denied":** Try running the command with `sudo` (on Mac/Linux) or make sure you aren't trying to run the file in a restricted system folder.

## Security Warning
**Never share your Trade Republic exported CSV files with anyone.** They contain your personal financial transaction history. This script runs locally on your computer, so your data stays with you and is not sent anywhere else.
