# Registrar Bot

A custom Discord bot that:
- Creates class-specific roles, private channels, and invite links
- Automatically assigns roles based on invite links
- Allows users to join their class with a simple access code

## Commands

- `/createclass` — Create a class role, private channel, and unique invite
- `/joinclass` — Join your class using a code sent by the instructor

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on `.env.example`

3. Run the bot:
   ```
   python main.py
   ```

Deploy on Railway for 24/7 uptime and persistent storage.
