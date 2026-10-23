# Set up the Temp Stick MCP — the plain-words guide

This guide is written for busy people, not computer people. Short steps.
No jargon. Setup takes about five minutes, one time only.

When you are done, you will be able to open your AI app (like Claude) and
ask one question:

**"How's my freezer?"**

...and it will answer with the real temperature, straight from your Temp
Stick sensor.

## What you need before you start

1. A Temp Stick sensor, already set up and showing in your Temp Stick
   account.
2. The email and password you use to sign in to Temp Stick.
3. A computer with your AI app on it (Claude Desktop, Claude Code, or
   Cursor).

## Part 1 — Get your key

Your key is a short code that lets the program read your sensors. Treat
it like a password: never send it in a chat or an email.

1. Open your web browser and go to **mytempstick.com**
2. Sign in with your Temp Stick email and password.
3. Open the **Account Page**.
4. Click the **Developers** tab.
5. Click **Show Key**.
6. Copy the key that appears. (On a Mac: Command + C. On Windows:
   Ctrl + C.)

Keep that key ready. You will paste it once, in Part 3.

## Part 2 — Get the program

1. Go to **github.com/obseard223/tempstick-mcp**
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Unzip the file and put the folder somewhere you will not lose it —
   your Documents folder is fine.
5. Remember where you put it. You need the folder's location in Part 3.
   - Mac example: `/Users/yourname/Documents/tempstick-mcp-main`
   - Windows example: `C:\Users\yourname\Documents\tempstick-mcp-main`

## Part 3 — Paste in the settings block

You are going to paste one small block of settings into your AI app and
change two things inside it.

**If you use Claude Desktop:**

1. Open Claude Desktop.
2. Open **Settings**, then **Developer**, then click **Edit Config**.
   A settings file opens.
3. Delete what is in it and paste this whole block:

```json
{
  "mcpServers": {
    "tempstick": {
      "command": "python3",
      "args": ["PASTE-THE-FOLDER-LOCATION-HERE/server.py"],
      "env": { "TEMPSTICK_API_KEY": "PASTE-YOUR-KEY-HERE" }
    }
  }
}
```

4. Now fix the two spots, carefully:
   - Replace `PASTE-YOUR-KEY-HERE` with the key you copied in Part 1.
   - Replace `PASTE-THE-FOLDER-LOCATION-HERE` with the folder location
     from Part 2. Example: `/Users/yourname/Documents/tempstick-mcp-main/server.py`
   - On Windows, write `python` instead of `python3`, and use backslashes
     like the Windows example above.
5. Save the file.

**If you use Cursor or Claude Code**, the same block works — the README
has the exact spots to paste it for each app.

## Part 4 — Restart the app

1. Quit the AI app completely. (Closing the window is not enough on a
   Mac — right-click the app icon and choose Quit.)
2. Open it again.

## Part 5 — Ask about your freezer

In a new chat, type any of these:

- **"How's my freezer?"**
- "What's the temperature in the walk-in?"
- "Is any of my sensors offline or low on battery?"
- "Has the freezer been warm at any point today?"

That is it. You are set up.

## If something goes wrong

- **It says "Invalid X-API-KEY."** The key copy went wrong. Redo Part 1
  and paste the key again, exactly as shown.
- **The AI says it has no sensor tool.** The app did not fully restart.
  Redo Part 4.
- **The AI finds no sensors.** Sign in at mytempstick.com and check your
  sensor shows there first. The program can only see what your account
  can see.

## Or: let your own Claude do the work

Copy this whole block and paste it into a chat with your own Muse. It
will do the computer parts for you and only ask you for the two things
only you can do.

```text
Install the OpenPandora Temp Stick MCP for me, from this repo:
https://github.com/obseard223/tempstick-mcp

Walk me through it one step at a time, in plain words, and do every
step you can do yourself (files, settings, config) without asking me.

Only ask me to do two things:
1. Copy my API key, when you get to that step — tell me the exact taps:
   sign in at mytempstick.com, open the Account Page, click the
   Developers tab, click Show Key, copy the key. I will paste it where
   you tell me. Never ask me to send the key in this chat.
2. Restart the app, when you tell me to.

When everything is done, prove it works: use the new tools to list my
Temp Stick sensors, and tell me what my freezer temperature is right now.
```
