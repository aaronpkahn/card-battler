#!/bin/bash

if [ -z "$1" ]; then
    USERNAME=$(whoami)
else
    USERNAME="$1"
fi

DISCORD_BOT_TOKEN=$(security find-generic-password -s "discord-card-battler-token" -a $USERNAME -w)

if [ -z "$DISCORD_BOT_TOKEN" ]; then
  echo "Error: Could not retrieve DISCORD_BOT_TOKEN from Keychain."
  echo "To add the token to your Keychain, run the following command:"
  echo "security add-generic-password -s \"discord-card-battler-token\" -a $USERNAME -w \"<your-token-here>\""
  exit 1
fi

export DISCORD_BOT_TOKEN

python bot.py
