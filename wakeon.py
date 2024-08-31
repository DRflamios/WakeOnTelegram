import os
import platform
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from wakeonlan import send_magic_packet
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Convert the list of authorized user IDs from a comma-separated string to a set of integers
AUTHORIZED_USERS = set(map(int, os.getenv('AUTHORIZED_USERS').split(',')))

# Retrieve device configurations from environment variables
DEVICES = {
    'pc_home': {'mac': os.getenv('PC_HOME_MAC'), 'ip': os.getenv('PC_HOME_IP')},
    'server_office': {'mac': os.getenv('SERVER_OFFICE_MAC'), 'ip': os.getenv('SERVER_OFFICE_IP')}
}

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        update.message.reply_text('Welcome! Use the /wake command to wake up a device.')
    else:
        update.message.reply_text("You are not authorized to use this bot.")

def wake(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        update.message.reply_text("Access denied.")
        return

    # Create a list of buttons for each device
    keyboard = [
        [InlineKeyboardButton(device_name, callback_data=device_name)]
        for device_name in DEVICES.keys()
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text('Select the device to wake up:', reply_markup=reply_markup)

def ping_device(ip: str) -> bool:
    """
    Ping an IP address to check if the device is online.
    Returns True if the device responds, False otherwise.
    """
    # Set the ping parameter based on the operating system
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = f"ping {param} 1 {ip}"

    # Execute the ping command
    response = os.system(command)

    # 0 means the device responded to the ping
    return response == 0

def button(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        update.callback_query.answer("Access denied.")
        return

    query = update.callback_query
    query.answer()

    device_name = query.data

    if device_name in DEVICES:
        mac_address = DEVICES[device_name]['mac']
        ip_address = DEVICES[device_name]['ip']

        # Send the WoL packet
        send_magic_packet(mac_address)
        query.edit_message_text(f"WoL packet sent to {device_name} with MAC address {mac_address}. Checking status...")

        # Wait a few seconds to allow the device to start
        time.sleep(5)

        # Check if the device responds to the ping
        if ping_device(ip_address):
            query.edit_message_text(f"The device {device_name} is now online.")
        else:
            query.edit_message_text(f"Unable to wake up {device_name}. Check the device status and try again.")
    else:
        query.edit_message_text("Device not recognized. Please check the device name.")

def main() -> None:
    # Create the Updater object and pass the bot token
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register command handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("wake", wake))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Start the bot
    updater.start_polling()

    # Keep the bot running until it is interrupted
    updater.idle()

if __name__ == '__main__':
    main()