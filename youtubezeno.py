import os
import json
import sys
import string
import shutil
import asyncio
import threading
import yt_dlp
import os
import tempfile
import time
import base64
import subprocess
import asyncio
from asyncio import run as arun
from highrise import BaseBot, __main__
from highrise.models import User, SessionMetadata, Position
from highrise import *
from highrise.webapi import *
from highrise.models_webapi import *
from highrise.models import *
import socket
import aiohttp
import aiofiles
import yt_dlp
from mutagen.mp3 import MP3
from collections import deque
import random
from datetime import datetime, timedelta
from HRDB import ownerz, playlist, user_ticket, vip_users, msg, restrict, promo, bot_location, ids

invite = "6706b1dc20084804ef575ccb"

# Icecast server configuration
SERVER_HOST = "link.zeno.fm" # dont change.
SERVER_PORT = 80 # dont change
MOUNT_POINT = "/w1qxknzdxbkuv" # put ur mountpoint after / in ""
STREAM_USERNAME = "source" # dont change
STREAM_PASSWORD = "4iJGVNwr"#"put your password"

AUDIO_FILES = [
    "Nothing.mp3"
]

class BotDefinition:
    def __init__(self, bot: BaseBot, room_id: str, api_token: str):
        self.bot = bot
        self.room_id = room_id
        self.api_token = api_token

class SEA(BaseBot):
    def __init__(self):
        super().__init__()
        self.message_task = None
        self.notification_task = None
        self.promo_task = None
        self.username = None
        self.owner_id = None
        self.owner = None
        self.bot_id = None
        self.skip = False
        self.bitrate = '128k'
        self.choices = {}
        self.req_files = deque()
        self.now = deque()
        self.message = deque()
        self.wait = []
        self.state_file = "bot_state.json"
        self.req_files_dir = "reqfiles"
        self.fav_dir = "fav"
        os.makedirs(self.fav_dir, exist_ok=True)
        os.makedirs(self.req_files_dir, exist_ok=True)
        self.load_state()

    def save_state(self):
        """Save the current state of the req_files deque, with updated file paths."""
        try:
            data = {
                "req_files": [
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "duration": item["duration"],
                        "user": item["user"]
                    }
                    for item in self.req_files
                ]
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving state: {type(e).__name__} - {e}")

    def load_state(self):
        """Load the saved state of the req_files deque from a JSON file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.req_files = deque(data.get("req_files", []))
                    os.remove(self.state_file)
            except Exception as e:
                print(f"Error loading state: {type(e).__name__} - {e}")

    def move_files_and_update_urls(self):
        for item in self.req_files:
            if item["url"].startswith("/tmp/"):
                temp_file_path = item["url"]
                new_file_path = os.path.join(self.req_files_dir, os.path.basename(temp_file_path))

                try:
                    shutil.move(temp_file_path, new_file_path)
                    item["url"] = new_file_path
                except Exception as e:
                    print(f"Error moving file {temp_file_path} to {new_file_path}: {type(e).__name__} - {e}")

    async def restart_bot(self):
        self.move_files_and_update_urls()
        self.save_state()
        await asyncio.sleep(5)
        os.execv(sys.executable, [sys.executable, 'run.py'] + sys.argv[1:])

    async def on_start(self, session_metadata: SessionMetadata):
        try:
            self.username = await self.get_username(session_metadata.user_id)
            self.bot_id = session_metadata.user_id
            self.owner_id = session_metadata.room_info.owner_id
            self.owner = await self.get_username(self.owner_id)
        except Exception as e:
            print("Error in get username, and bot id on start:", e)

        if not (self.owner is None):
            if self.owner not in ownerz:
                ownerz.append(self.owner)
            else:
                pass
        else:
            pass

        if not (self.owner_id is None):
            if self.owner_id not in msg:
                msg.append(self.owner_id)
            else:
                pass
        else:
            pass

        if bot_location:
            await self.highrise.teleport(session_metadata.user_id, Position(**bot_location))
        else:
            await self.highrise.teleport(session_metadata.user_id, Position(15.5, 0.25, 2.5, 'FrontRight'))

        if self.notification_task is None or self.notification_task.done():
            self.notification_task = asyncio.create_task(self.notification())
        else:
            pass

        if self.message_task is None or self.message_task.done():
            self.message_task = asyncio.create_task(self.print_messages())

        if self.promo_task is None or self.promo_task.done():
            self.promo_task = asyncio.create_task(self.promo())
        print(f"{self.username} is alive.")

    async def on_message(self, user_id: str, conversation_id: str, is_new_conversation: bool) -> None:
        try:
            username = await self.get_username(user_id)
            info = await self.webapi.get_user(user_id)
            joined_at = info.user.joined_at
            if isinstance(joined_at, datetime):
                one_month_ago = datetime.now(joined_at.tzinfo) - timedelta(days=30)
                if joined_at <= one_month_ago:
                    if not username in user_ticket:
                        user_ticket[username] = 3
                        await self.highrise.send_message(conversation_id, "Your account is verified.")
                        await self.highrise.send_message(conversation_id, "You got 3 free tickets")
                        ids.append(user_id)
                else:
                    await self.highrise.send_message(conversation_id, "Your account must be atleast 30 days or older.")
        except Exception as e:
            print(e)
                                
    async def get_username(self, user_id):
        user_info = await self.webapi.get_user(user_id)
        return user_info.user.username
    
    async def invite_all(self, user):
        if not user.username in ownerz:
            await self.highrise.send_whisper(user.id, "You cant use this command.")
            return
        try:
            for erm in ids:
                message_id = f"1_on_1:{erm}:{self.bot_id}"
            await self.highrise.send_message(
                message_id,
                message_type="invite",
                content="Join this room!", 
                room_id=invite)
        except Exception as e:
            await self.highrise.chat(f"error: {e}")
    
    async def on_user_move(self, user: User, pos: Position) -> None:
        # contant @SALAR_KHAN in hr to buy auto floor teleport.
        pass

    async def on_user_leave(self, user: User) -> None:
        pass


    async def on_whisper(self, user: User, message: str) -> None:
        pass

    async def on_chat(self, user: User, message: str):
        if message.startswith("/invite"):
            try:
                await self.invite_all(user)
            except Exception as e:
                await self.highrise.chat(f"Issue: {e}")
        if not message.lower() == "no":
            if not message.lower() == "yes":
                if user.username in self.choices:
                    try:
                        if not user.username in self.wait:
                            self.wait.append(user.username)
                            await self.highrise.send_whisper(user.id, "Type 'yes' or 'no' to apply the changes.")
                            await self.highrise.send_whisper(user.id, "If you do not respond with 'yes' or 'no' within 10 seconds, the operation will be considered canceled.")
                        await asyncio.sleep(10)
                        if user.username in self.choices:
                            del self.choices[user.username]
                            if user.username in self.wait:
                                self.wait.remove(user.username)
                            await self.highrise.send_whisper(user.id, "Operation cancelled.")
                    except:
                        pass
                        
        if message.lower() == "no":
            if user.username == "thisuserisded" or user.username in ownerz:
                if user.username in self.choices:
                    await self.highrise.send_whisper(user.id, "Cancelled operation.")
                    del self.choices[user.username]
        
        if message.lower() == "yes":
            if user.username == "thisuserisded" or user.username in ownerz:
                if user.username in self.choices:
                    new_bitrate = self.choices[user.username]
                    self.bitrate = new_bitrate
                    await self.highrise.chat(f"Successfully updated audio bitrate to {new_bitrate}.")
                    del self.choices[user.username]
        
        if message.startswith("/cbit") and (user.username == "thisuserisded" or user.username in ownerz):
            await self.highrise.send_whisper(user.id, f"Currently audio is being broadcasted at {self.bitrate}bps.")
        
        if message.startswith("/bitrate ") and (user.username == "thisuserisded" or user.username in ownerz):
            parts = message.split(" ")
            if len(parts) > 1:
                if parts[1].endswith("k") and parts[1][:-1].isdigit():
                    bitrate = parts[1]
                    await self.highrise.chat(f"Are you sure you want to change audio bitrate to {bitrate} ?")
                    await self.highrise.send_whisper(user.id, "This could effect the audio stream.\n"
"Type 'yes' to confirm else type 'no' to cancel.")
                    self.choices[user.username] = bitrate
                else:
                    await self.highrise.send_whisper(user.id, "Invalid command, usage: /bitrate [number]k\nExample: /bitrate 256k")
            else:
                await self.highrise.send_whisper(user.id, "Invalid command, usage: /bitrate [number]k\nExample: /bitrate 128k")
        
        if message == "/restart" and (user.username == "thisuserisded" or user.username in ownerz):
            try:
                await self.highrise.send_whisper(user.id, "Restarting the bot...")
                await self.restart_bot()
            except Exception as e:
                print("Error in /restart command: ", e)

        if message.startswith("/help"):
            try:
                await self.highrise.send_whisper(user.id,"\nAVAILABLE COMMANDS:\n/play <song name> or /play <youtube url> - Play a song.\n/next - Display the next song in the queue.\n/skip - Skip current song.\n/skip [number] - Skip a song in the queue.")
                await asyncio.sleep(3)
                await self.highrise.send_whisper(user.id, "\n/top [number] - Places a song at number in the queue\n"
                                    "/now - Display the currently playing song\n"
                                    "/dump [number] - Get the info of song in queue\n"
                                    "/wallet - To get info of your tickets.\n"
                                    "/give @user [number] - Give user tickets.")
                await asyncio.sleep(1)
                await self.highrise.send_whisper(user.id, "\n/rlist - Get info about tickets ratelist.\n/info @user - Get user's tickets info.\n/fav - To add to fav playlist.\n/rfav [number] remove from fav playlist.\n/flist - Prints fav playlist.")
                await asyncio.sleep(1)
                await self.highrise.send_whisper(user.id, "\n/cfav - Clears fav playlist.\n/transfer @user [number] - Transfer your tickets to user, (min 6 tickets)") 
                return
            except:
                pass
        
        if message.startswith("/play"):
            if (user.username in vip_users) or (user.username in user_ticket and user_ticket[user.username] > 0) or (user.username in ownerz):
                try:
                    query = message.split(" ", 1)[1]
                    lower_query = query.lower()
                    for item in restrict:
                        if item.lower() in lower_query:
                            await self.highrise.send_whisper(user.id, "This song is restricted. Your ticket is returned.")
                            return
                    if query.startswith("https://"):
                        if "playlist" not in query:
                            await self.highrise.send_whisper(user.id, "Links aren't supported as per now, add by song - artist.")
                            return
                            await self.highrise.send_whisper(user.id, "Your request is being processed. Be patient.")
                            if user.username in user_ticket:
                                if user.username not in ownerz and user.username not in vip_users:
                                    await asyncio.sleep(1)
                                    await self.highrise.send_whisper(user.id, "• Note: Requests cost 1 ticket. Don't waste your tickets. If your requested song is not found, your ticket will be returned to your wallet.")
                            await self.add_to_queue(query, user)
                        else:
                            await self.highrise.send_whisper(user.id, "\n You can't add playlists. Request one song at a time")
                    else:
                        await self.highrise.send_whisper(user.id, "Your request is being processed. Be patient.")
                        if user.username in user_ticket and user.username not in ownerz and user.username not in vip_users:
                            await asyncio.sleep(1)
                            await self.highrise.send_whisper(user.id, "• Note: Requests cost 1 ticket. Don't waste your tickets. If your requested song is not found, your ticket will be returned to your wallet.")
                        await self.add_to_queue(query, user)
                except IndexError:
                    await self.highrise.send_whisper(user.id, "Please provide a song name after /play.")
                except Exception as e:
                    print(f"Error in chat command: {e}")
            else:
                await self.highrise.send_whisper(user.id, "You don't have enough tickets left.")
                await asyncio.sleep(3)
                await self.highrise.send_whisper(user.id, "Type /rlist to get list of rates tokens.")

        if message.startswith("/rlist"):
            try:
                await self.highrise.send_whisper(user.id, f"\n • Note tip @{self.username} in room,\n • 1 tickets costs 5g\n • 3 tickets costs 10g\n • 30 tickets for 100g, etc.")
                await asyncio.sleep(2)
                await self.highrise.send_whisper(user.id, f"\n*NOTE*: you can get vip by tipping 1k to @{self.username} in room.")
                await asyncio.sleep(2)
                await self.highrise.send_whisper(user.id, "Vip users can request songs without tickets. Vip users must renew their vip membership every month.")
            except Exception as e:
                print("Error in rlist:", e)

        if message.startswith("/dump "):
            try:
                index_str = message.split("/dump ")[1]
                index = int(index_str)
                if self.now and self.now[0]['url'] in self.Audio_files:
                    index -= 1
                if 0 <= index < len(self.req_files):
                    file_info = self.req_files[index]
                    now = file_info['title']
                    audio_length = file_info['duration']
                    if file_info.get('user'):
                        await self.highrise.send_whisper(
                            user.id,
                            f"🎵 {index + 1}: {now}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {audio_length}\n (Requested by @{file_info['user']})"
                        )
                    else:
                        await self.highrise.send_whisper(
                            user.id,
                            f"🎵 {now}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {audio_length}"
                        )
                else:
                    await self.highrise.send_whisper(user.id, f"No song found in queue with index {index + 1}.")
            except ValueError:
                await self.highrise.send_whisper(user.id, "Invalid index format. Please provide a valid number after /dump.")
            except Exception as e:
                print(f"Error in /dump command: {e}")
                await self.highrise.send_whisper(user.id, "Error processing the request.")

        if message.startswith("/now"):
            try:
                now_playing = self.now[0]
                now = self.now[0]['title']
                if self.now[0]['user']:
                    await self.highrise.send_whisper(user.id, f"🎵 Now playing: {now}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {self.now[0]['audio_length']}\n (Requested by @{now_playing['user']})")
                else:
                    await self.highrise.send_whisper(user.id, f"🎵 Now playing: {now}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {self.now[0]['audio_length']}")
            except IndexError:
                await self.highrise.send_whisper(user.id, "Nothing is playing right now.")
            except Exception as e:
                print(f"Error in /now command: {e}")
                await self.highrise.send_whisper(user.id, "Error processing the request.")
        
        if message.startswith("/wallet"):
            try:
                if user.username in user_ticket:
                    if user_ticket[user.username] == 0:
                        await self.highrise.send_whisper(user.id, f"You dont have any ticket left in your wallet. Tip @{self.username} to get tickets.")
                        return
                    if user_ticket[user.username] == 1:
                        await self.highrise.send_whisper(user.id, f"You have only {user_ticket[user.username]} ticket left in your wallet.")
                        return
                    await self.highrise.send_whisper(user.id, f"You have total: {user_ticket[user.username]} tickets in your wallet.")
                else:
                    await self.highrise.send_whisper(user.id, "Text this bot to get 3 free tickets.")
            except Exception as e:
                print("The error occurred in wallet:", e)

        if message.startswith("/next"):
            try: 
                if len(self.req_files) > 1:
                    next_file = self.req_files[1]
                    audio_length = (next_file['duration'])
                    next = next_file['title']
                    if next_file['user']:
                        await self.highrise.send_whisper(user.id, f"🎵 Upcoming song: {next}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {audio_length}\n (Requested by @{next_file['user']})")
                    else:
                        await self.highrise.send_whisper(user.id, f"🎵 Upcoming song: {next}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {audio_length}")
                else: 
                    await self.highrise.send_whisper(user.id, "No next item in queue")
            except Exception as e: 
                    print(f"Error in /next command: {e}") 
                    await self.highrise.send_whisper(user.id, "Error checking queue")
        
        if message.startswith("/top") and user.username in ownerz:
            try:
                parts = message.split(" ")
                if len(parts) > 1 and parts[1].isdigit():
                    index = int(parts[1])
                    if 0 < index < len(self.req_files):
                        item_to_move = self.req_files[index]
                        self.req_files.remove(item_to_move)
                        self.req_files.insert(1, item_to_move)
                        await self.highrise.chat(f"Moved {get_ordinal(index)} item to the top of the queue.")
                    else:
                        await self.highrise.send_whisper(user.id, f"No song found in queue with {get_ordinal(index)} number.")
                else:
                    await self.highrise.send_whisper(user.id, "Invalid command. Please use /top with number from queue")
            except Exception as e:
                print(f"Error moving song to top: {e}")
       
        if message.startswith("/skip"):
            try:    
                parts = message.split(" ")
                if len(parts) > 1 and parts[1].isdigit():
                    if int(parts[1]) == 0:
                        return
                    index = int(parts[1]) - 1

                    if self.now[0]['url'] in AUDIO_FILES:
                        adjusted_index = index
                    else:
                        adjusted_index = index + 1
                    if 0 <= adjusted_index < len(self.req_files):
                        removed_file = self.req_files[adjusted_index]
                        rem_length = self.req_files[adjusted_index]['duration']
                        req_user = self.req_files[adjusted_index]['user']
                        fix_rem = removed_file['title']
                        if not (user.username in ownerz or user.username == req_user):
                            await self.highrise.send_whisper(user.id, "NOTE: you can only skip the song if you requested it.")
                            return
                        if os.path.exists(self.req_files[adjusted_index]['url']):
                            os.remove(self.req_files[adjusted_index]['url'])
                        self.req_files.remove(removed_file)
                        
                        await self.highrise.chat(f"🎵 Removed from queue: {fix_rem}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {rem_length}")
                    else: 
                        await self.highrise.send_whisper(user.id, f"No song found in queue with {get_ordinal(index + 1)} number.") 
                else:
                    rem_length = self.now[0]['audio_length']
                    removed_file = self.now[0]
                    req_user = self.now[0]['user']
                    fix_rem = removed_file['title']
                    if not (user.username in ownerz or user.username == req_user):
                        await self.highrise.send_whisper(user.id, "NOTE: you can only skip the current song if you requested it.")
                        return
                    await self.highrise.chat(f"🎵 Skipping {fix_rem}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {rem_length}")
                    await asyncio.sleep(3)
                    self.skip = True
            except Exception as e:
                print(f"Error in /skip command: {e}")
                await self.highrise.send_whisper(user.id, "Nothing is playing.")

        if message.startswith("/queue"): 
            try:
                if len(self.req_files) > 0:
                    if self.now[0]['url'] not in AUDIO_FILES:
                        global_index = 1
                    else:
                        global_index = 0

                    if len(self.req_files) == 1 and global_index == 1:
                        await self.highrise.send_whisper(user.id, "The queue is empty.")
                        return

                    message_content = ""
                    queue_number = 1

                    for _, file in enumerate(list(self.req_files)[global_index:], start=global_index):
                        item = f"{queue_number}. {file['title']}\n"
                        if len(message_content) + len(item) > 255:
                            await self.highrise.send_whisper(user.id, f"\n{message_content.strip()}")
                            message_content = item
                        else:
                            message_content += item
                        queue_number += 1

                    if message_content:
                        await self.highrise.send_whisper(user.id, f"\n{message_content.strip()}")
                else:
                    await self.highrise.send_whisper(user.id, "The queue is empty.")
            except Exception as e:
                print(f"Error in /queue command: {e}")
                await self.highrise.send_whisper(user.id, "Error checking the queue.")
                
        if message.startswith("/info ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                info = message.split(" ", 1)[1]
                infol = info.replace("@", "")
                if infol in user_ticket and user_ticket[infol] > 0:
                    if user_ticket[infol] == 1:
                        await self.highrise.chat(f"User {info} has only {user_ticket[infol]} ticket left.")
                    if user_ticket[infol] > 1:
                        await self.highrise.chat(f"User {info} has only {user_ticket[infol]} tickets left.")
                else:
                    await self.highrise.chat(f"User {info} does not have any ticket.")
            except Exception as e:
                print(e)
                
        if message.startswith("/rem ") and user.username in ownerz:
            try:
                remvip = message.split(" ", 1)[1]
                rem = remvip.replace("@", "")
                if rem in ownerz:
                    ownerz.remove(rem)
                    await self.highrise.chat(f"{remvip} removed from ownerz.")
                else:
                    await self.highrise.send_whisper(user.id, f"{rem} not in ownerz.")
            except:
                pass
                
        if message.startswith("/add ") and user.username in ownerz:
            try:
                vip = message.split(" ", 1)[1]
                allowed = vip.replace("@", "")
                if allowed not in ownerz:
                    ownerz.append(allowed)
                    await self.highrise.chat(f"{vip} added to ownerz.")
                else:
                    await self.highrise.chat(f"{vip} already in ownerz.")
            except:
                await self.highrise.send_whisper(user.id, "Nuh uh")

        if message.startswith("/vipz") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                if vip_users:
                    message_content = ""
                    for idx, user_name in enumerate(vip_users, start=1):
                        item = f"{idx}. {user_name}\n"
                        if len(message_content) + len(item) > 255:
                            await self.highrise.send_whisper(user.id, f"\n{message_content.strip()}")
                            message_content = item
                        else:
                            message_content += item
                    if message_content:
                        await self.highrise.send_whisper(user.id, f"\n{message_content.strip()}")
                else:
                    await self.highrise.send_whisper(user.id, "The vip list is empty.")
            except Exception as e:
                print(f"Error in /vipz command: {e}")
                await self.highrise.send_whisper(user.id, "Error checking the queue.")
        
        if message.startswith("/remv ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                current_date = datetime.now().strftime("%d/%m/%Y")
                remvip = message.split(" ", 1)[1]
                rem = remvip.replace("@", "")
                if rem in vip_users:
                    vip_users.remove(rem)
                    await self.highrise.chat(f"{remvip} removed from vip.")
                    for user_id in msg:
                        message_id = f"1_on_1:{user_id}:{self.bot_id}"
                        try:
                            await self.highrise.send_message(message_id, f"User {remvip} removed from vip on {current_date}, Was removed by @{user.username}")
                            await asyncio.sleep(1)
                        except Exception as e:
                            await self.highrise.chat(f"Failed to send message to {user_id}: {e}")
                            print("Error in sending msg in /addv:", e)
                else:
                    await self.highrise.send_whisper(user.id, f"{rem} not a vip.")
            except:
                pass
                
        if message.startswith("/addv ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                current_date = datetime.now().strftime("%d/%m/%Y")
                vip = message.split(" ", 1)[1]
                allowed = vip.replace("@", "")
                if allowed not in vip_users:
                    vip_users.append(allowed)
                    await self.highrise.chat(f"{vip} added to vip.")
                    for user_id in msg:
                        message_id = f"1_on_1:{user_id}:{self.bot_id}"
                        try:
                            await self.highrise.send_message(message_id, f"User {vip} got their vip on {current_date}, Was added by @{user.username}")
                            await asyncio.sleep(1)
                        except Exception as e:
                            await self.highrise.chat(f"Failed to send message to {user_id}: {e}")
                            print("Error in sending msg in /addv:", e)
                else:
                    await self.highrise.chat(f"{vip} already a vip.")
            except:
                await self.highrise.send_whisper(user.id, "Nuh uh")

        if message.startswith("/transfer"):
            try:
                _, username, value = message.split(" ", 2)
                username = username.strip("@")
                value = int(value)
                if not value >= 6:
                    await self.highrise.send_whisper(user.id, "NOTE: you need to transfer at least 6 tickets.")
                else:
                    if user_ticket[user.username] >= value:
                        user_ticket[username] += value
                        user_ticket[user.username] -= value
                        await self.highrise.chat(f"Sent {value} tickets to {username}.")
                    else:
                        await self.highrise.send_whisper(user.id, "You dont have enough tickets")
            except Exception as e:
                print(f"An error occurred: {e}")

        if message.startswith("/give") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                _, username, value = message.split(" ", 2)
                username = username.strip("@")
                value = int(value)
                user_ticket[username] += value
                if value == 1:
                    await self.highrise.chat(f"Sent {value} ticket to {username}.")
                    return
                await self.highrise.chat(f"Sent {value} tickets to {username}.")
            except Exception as e:
                print(f"An error occurred: {e}")

        if message.startswith("/rfav ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                parts = message.split(" ")
                if len(parts) > 1 and parts[1].isdigit():
                    index = int(parts[1]) - 1
                    if 0 <= index <= len(playlist):
                        removed_file = playlist[index]
                        rem_length = removed_file.get('audio_length', 'Unknown length')
                        fix_rem = removed_file.get('title', 'Unknown title')
                        file_path = removed_file.get('url', '')
                        if file_path and os.path.exists(file_path):
                            os.remove(file_path)
                            playlist.pop(index)

                            await self.highrise.chat(f"🎵 Removed from queue: {fix_rem}\n🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {rem_length}")
                    else:
                        await self.highrise.send_whisper(user.id, f"No song found in queue at position {get_ordinal(parts[1])}.")
                else:
                    await self.highrise.send_whisper(user.id, "Please provide a valid song number to remove.")
            except Exception as e:
                print(f"Error in /rfav command: {e}")
                await self.highrise.send_whisper(user.id, f"Error: {e}")

        if message.startswith("/flist"):
            try: 
                if playlist: 
                    message_content = ""
                    for idx, file in enumerate(list(playlist), start=1):
                        item = f"{idx}. {file['title']}\n"
                        if len(message_content) + len(item) > 255:
                            await self.highrise.send_whisper(user.id, f"\n{message_content.strip()}")
                            message_content = item
                        else:
                            message_content += item
                    if message_content:
                        await self.highrise.send_whisper(user.id, f"\n{message_content.strip()}")
                else:
                    await self.highrise.send_whisper(user.id, "The queue is empty.")
            except Exception as e:
                print(f"Error in /flist command: {e}")
                await self.highrise.send_whisper(user.id, "Error checking the queue.")

        if message.startswith("/fav") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                if self.now:
                    fav = self.now[0]
                    if any(item['url'] == fav['url'] for item in playlist):
                        await self.highrise.chat(f"{fav['title']} is already in the favorites playlist.")
                        return
                    if fav['url'] in AUDIO_FILES:
                        await self.highrise.send_whisper(user.id, "• Note: you can only add requested songs to favorites.")
                    else:
                        permanent_file = f"/home/container/fav/{fav['title']}.mp3"
                        try:
                            shutil.copy(fav['url'], permanent_file)
                        except Exception as e:
                            print("Error in /fav copy:", e)
                            return
                        fav['url'] = permanent_file
                        playlist.append(fav)
                        await self.highrise.chat(f"{fav['title']} has been added to the favorites playlist.")
                else:
                    await self.highrise.chat("Nothing is playing right now.")
            except Exception as e:
                print("Error in /fav command:", e)

        if message.startswith("/cfav"):
            if user.username in ownerz or user.username == "thisuserisded":
                if playlist:
                    for item in playlist:
                        if os.path.exists(item['url']):
                            try:
                                os.remove(item['url'])
                            except:
                                print("Error in /cfav for loop:", e)
                    playlist.clear()
                    await self.highrise.chat("Fav playlist is cleared.")
                else:
                    await self.highrise.chat("Fav playlist is already empty.")
            else:
                await self.highrise.send_whisper(user.id, "You dont have access to this command.")

        if message.startswith("/cmsg") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                if msg:
                    msg.clear()
                    await self.highrise.chat("Message list is cleared.")
                else:
                    await self.highrise.chat("Message list is already empty.")
            except:
                print("Error in /cmsg:", e)

        if message.startswith("/rmsg ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                user = message.split(" ", 1)[1]
                username = user.replace("@", "")
                room_users = (await self.highrise.get_room_users()).content
                user_id = None
                for user in room_users:
                    if user[0].username.lower() == username.lower():
                        user_id = user[0].id
                        break
                if user_id is None:
                    await self.highrise.send_whisper(user.id,"User not found in room.")
                    return
                if user_id in msg:
                    msg.remove(user_id)
                    await self.highrise.chat(f"User @{username} is removed from message list.")
                else:
                    await self.highrise.chat("User is not in list.")
            except Exception as e:
                    print("Error in /rmsg:", e)

        if message.startswith("/msg ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                user = message.split(" ", 1)[1]
                username = user.replace("@", "")
                room_users = (await self.highrise.get_room_users()).content
                user_id = None
                for user in room_users:
                    if user[0].username.lower() == username.lower():
                        user_id = user[0].id
                        break
                if user_id is None:
                    await self.highrise.send_whisper(user.id,"User not found in room.")
                    return
                if user_id not in msg:
                    msg.append(user_id)
                    await self.highrise.chat(f"User @{username} is added to message list.")
                else:
                    await self.highrise.chat("User is already in list.")
            except Exception as e:
                    print("Error in /msg:", e)

        if message.startswith("/res ") and user.username in ownerz:
            try:    
                res = message.split(" ", 1)[1]
                if not res in restrict:
                    restrict.append(res)
                    await self.highrise.chat("This song is added to restricted songs.")
                else:
                    await self.highrise.chat("This song is already is restricted.")
            except Exception as e:
                print(f"Error in /restrict command: {e}")
                
        if message.startswith("/unres ") and user.username in ownerz:
            try:    
                res = message.split(" ", 1)[1]
                if res in restrict:
                    restrict.remove(res)
                    await self.highrise.chat("This song is removed from restricted songs.")
                else:
                    await self.highrise.chat("This song is not restricted.")
            except Exception as e:
                print(f"Error in /unrestrict command: {e}")

        if message.startswith("/promo ") and user.username in ownerz:
            try:    
                prom = message.lstrip("/promo ").strip()
                if prom:
                    if prom not in promo:
                        promo.append(prom)
                        await self.highrise.chat("This message has been added to the promo list.")
                    else:
                        await self.highrise.chat("This message is already in the promo list.")
                else:
                    await self.highrise.chat("Please provide a promotional message after /promo.")
            except Exception as e:
                print(f"Error in /promo command: {e}")
                
        if message.startswith("/rpromo ") and user.username in ownerz:
            try:    
                prom = message.lstrip("/promo ").strip()
                if prom:
                    if prom in promo:
                        promo.remove(prom)
                        await self.highrise.chat("This message is removed from promo list.")
                    else:
                        await self.highrise.chat("This message is not in promo list.")
                else:
                    await self.highrise.chat("Please provide a promotional message after /promo.")
            except Exception as e:
                print(f"Error in /rpromo command: {e}")

        if message.startswith("/cpromo"):
            try:
                if user.username == "thisuserisded" or user.username in ownerz:
                    if promo:
                        promo.clear()
                        await self.highrise.chat("Cleared promo list.")
                    else:
                        await self.highrise.chat("Promo list is already empty.")
                else:
                    pass
            except:
                pass

        if message.startswith("/accs") and user.username in ownerz:
            try:
                total = len(user_ticket)
                empty = {key: value for key, value in user_ticket.items() if value == 0}
                active = {key: value for key, value in user_ticket.items() if value > 0 and value != 3}
                total_empty = len(empty)
                total_active = len(active)
                await self.highrise.chat(f"\nThere are total {total} users, {total_active} with active accs, while only {total_empty} users have 0 balance.")
            except Exception as e:
                print("Error in /accs:", e)

        if message.startswith("/withdraw ") and (user.username in ownerz or user.username == "thisuserisded"):
            try:
                parts = message.split(" ")
                if len(parts) != 2:
                    await self.highrise.send_whisper(user.id, "\nUsage: /withdraw [number].")
                    return
                try:
                    amount = int(parts[1])
                except:
                    await self.highrise.send_whisper(user.id, "Dont use decimals and floats only use integars [number].")
                    return
                bot_wallet = await self.highrise.get_wallet()
                bot_amount = bot_wallet.content[0].amount
                if bot_amount <= amount:
                    await self.highrise.send_whisper(user.id, "Sir, i dont have enough balance.")
                    return
                """Possible values are: "gold_bar_1",
            "gold_bar_5", "gold_bar_10", "gold_bar_50", 
            "gold_bar_100", "gold_bar_500", 
            "gold_bar_1k", "gold_bar_5000", "gold_bar_10k" """
                bars_dictionary = {10000: "gold_bar_10k", 
                               5000: "gold_bar_5000",
                               1000: "gold_bar_1k",
                               500: "gold_bar_500",
                               100: "gold_bar_100",
                               50: "gold_bar_50",
                               10: "gold_bar_10",
                               5: "gold_bar_5",
                               1: "gold_bar_1"}
                fees_dictionary = {10000: 1000,
                               5000: 500,
                               1000: 100,
                               500: 50,
                               100: 10,
                               50: 5,
                               10: 1,
                               5: 1,
                               1: 1}
                tip = []
                total = 0
                for bar in bars_dictionary:
                    if amount >= bar:
                        bar_amount = amount // bar
                        amount = amount % bar
                        for i in range(bar_amount):
                            tip.append(bars_dictionary[bar])
                            total = bar+fees_dictionary[bar]
                if total > bot_amount:
                    await self.highrise.send_whisper(user.id, "Sir, i dont have enough funds.")
                    return
                tip_string = ",".join(tip)
                await self.highrise.tip_user(user.id, tip_string)
            except Exception as e:
                print("Error in /withdraw:", e)

        if message == "/setbot" and user.username in ownerz:
            try:
                room_users = await self.highrise.get_room_users()
                for room_user, pos in room_users.content:
                    if room_user.username == user.username:
                        bot_location["x"] = pos.x
                        bot_location["y"] = pos.y
                        bot_location["z"] = pos.z
                        bot_location["facing"] = pos.facing
                        await self.highrise.send_whisper(user.id, f"Bot location set to {bot_location}")
                        break
            except Exception as e:
                print("Set bot:", e)

        if message == "/base" and user.username in ownerz:
            try:
                if bot_location:
                    await self.highrise.walk_to(Position(**bot_location))
            except Exception as e:
                print("Error in /base:", e)

        if message.startswith("/bwallet"):
            try:
                await self.bot_wallet(user, message)
            except:
                pass
    
    async def bot_wallet(self, user: User, message: str):
        if user.username in ownerz or user.username == "thisuserisded":
            wallet = await self.highrise.get_wallet()
            for item in wallet.content:
                if item.type == "gold":
                    gold = item.amount
                    await self.highrise.send_whisper(user.id, f"Sir, My current balance is {gold} gold!")
                    return
            await self.highrise.send_whisper(f"Hello, {user.username}! I don't have any gold.")
        else:
            await self.highrise.send_whisper(user.id, "You don't have access to this command")
    
    async def on_user_join(self, user: User, pos: Position) -> None:
        try:
            response = await self.webapi.get_user(user.id)
            joined_at = response.user.joined_at
            
            if isinstance(joined_at, datetime):
                one_month_ago = datetime.now(joined_at.tzinfo) - timedelta(days=30)
                if joined_at <= one_month_ago:
                    if not user.username in user_ticket:
                        await self.highrise.send_whisper(user.id, "Welcome to the room <3.\nDm this bot /verify to get free tickets. Each song request costs 1 ticket.")
                        await asyncio.sleep(2)
                        await self.highrise.send_whisper(user.id, "Type /play 'song' to request a song. Type /help for all commands.")
                        await asyncio.sleep(1)
                        await self.highrise.send_whisper(user.id, "If the bot malfunctions pm @SALAR_KHAN.")
                    else:
                        await self.highrise.send_whisper(user.id, "Welcome back to room <3.\nType /wallet to get info of your tickets. Type /help for all commands.")
                        await asyncio.sleep(2)
                        await self.highrise.send_whisper(user.id, "If the bot malfunctions pm @thisuserisded.")
                else:
                    await self.highrise.send_whisper(user.id, "Welcome to room <3.\nThis is a music bot. Type /rlist to get ratelist, each song request costs 1 ticket. Type /wallet to get info of your tickets. Type /play to request a song.")
                    await asyncio.sleep(2)
                    await self.highrise.send_whisper(user.id, "If the bot malfunctions pm @SALAR_KHAN.")
            else:
                pass
        except:
            pass

    async def on_tip(self, sender: User, receiver: User, tip: CurrencyItem | Item) -> None:
        try:
            if tip.amount == 1 and receiver.username == self.username:
                if sender.username in vip_users:
                    await self.highrise.send_whisper(sender.id, "You're already VIP, you don't need tickets.")
                else:
                    await self.highrise.send_whisper(sender.id, "Tip at least 5g to get a ticket.")

            elif tip.amount == 5 and receiver.username == self.username:
                user_ticket[sender.username] = user_ticket.get(sender.username, 0) + 1
                if sender.username in vip_users:
                    await self.highrise.send_whisper(sender.id, "You're already VIP, you don't need tickets.")
                else:
                    await self.highrise.chat(f"{sender.username}'s wallet has been updated with 2 tickets for tipping 5g.")
                    await self.highrise.send_whisper(sender.id, f"Total tickets in your wallet: {user_ticket[sender.username]}")

            elif tip.amount == 10 and receiver.username == self.username:
                user_ticket[sender.username] = user_ticket.get(sender.username, 0) + 3
                if sender.username in vip_users:
                    await self.highrise.send_whisper(sender.id, "You're already VIP, you don't need tickets.")
                else:
                    await self.highrise.chat(f"{sender.username}'s wallet has been updated with 3 tickets for tipping 10g.")
                    await self.highrise.send_whisper(sender.id, f"Total tickets in your wallet: {user_ticket[sender.username]}")

            elif tip.amount == 1000 and receiver.username == self.username:
                current_date = datetime.now().strftime("%d/%m/%Y")
                day = datetime.now().strftime("%d")
                if sender.username in vip_users:
                    await self.highrise.send_whisper(user.id, "Your vip period has been extended. Thanks for tipping gold. <3")
                    for user_id in msg:
                        message_id = f"1_on_1:{user_id}:{self.bot_id}"
                        try:
                            await self.highrise.send_message(message_id, f"User @{sender.username} tipped 1000g on {current_date}.")
                            await asyncio.sleep(1)
                        except Exception as e:
                            print("Error in sending msg abt tip:", e)

                else:
                    vip_users.append(sender.username)
                    await self.highrise.send_whisper(user.id, "Youre added to vip users. If you face any error pm @SALAR_KHAN. Enjoy <3")
                    await self.highrise.send_whisper(user.id, f"\n*NOTE*: your vip is started from {current_date}, Make sure to renew your vip before {get_ordinal(day)} of next month.")
                    for user_id in msg:
                        message_id = f"1_on_1:{user_id}:{self.bot_id}"
                        try:
                            await self.highrise.send_message(message_id, f"User @{sender.username} got their vip on {current_date}.")
                            await asyncio.sleep(1)
                        except Exception as e:
                            print("Error in sending msg abt tip:", e)

            elif tip.amount % 10 == 0 and tip.amount >= 10 and receiver.username == self.username:
                tickets = (tip.amount // 10) * 3
                user_ticket[sender.username] = user_ticket.get(sender.username, 0) + tickets
                await self.highrise.chat(f"{sender.username}'s wallet has been updated with {tickets} tickets for tipping {tip.amount}g.")
                await self.highrise.send_whisper(sender.id, f"Total tickets in your wallet: {user_ticket[sender.username]}")
            else:
                pass
        except Exception as e:
            print(e)
            await self.highrise.send_whisper(sender.id, f"Error occurred: {e}. Please inform @thisuserisded.")

    async def add_to_queue(self, query, user):
        """Search for a song and add it to the queue using yt-dlp."""
        buffered_file_path, track_duration, track = await self.search_track(query, user)
        if buffered_file_path:
            self.req_files.append({
                'url': buffered_file_path,
                'title': track['title'],
                'uploader': track['uploader'],
                'duration': track_duration,
                'user': user.username,
            })
            await self.highrise.chat(f'🎵 {track["title"]}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• ({track_duration}) added to queue\n (Requested by @{user.username})')
            if user.username in user_ticket:
                if user.username not in ownerz:
                    if user.username not in vip_users:
                        user_ticket[user.username] -= 1
                        await self.highrise.send_whisper(user.id, f"Remaining tickets in your wallet: {user_ticket[user.username]}")
        else:
            await asyncio.sleep(2)
            await self.highrise.send_whisper(user.id, "Couldn't add your song. Make sure to not request same song that's already in queue and dont request songs longer than 6 minutes.")
            await asyncio.sleep(2)
            await self.highrise.send_whisper(user.id, "Your ticket is returned to your wallet. Try again.")

    async def download_chunk(self, session, url, start, end, queue):
        headers = {'Range': f'bytes={start}-{end}'}
        async with session.get(url, headers=headers) as response:
            if response.status not in [206, 200]:
                print(f"Failed to download chunk: {response.status}")
                await queue.put(None)
                return

            chunk = await response.content.read()
            await queue.put((start, chunk))

    async def download_audio(self, session, audio_url, download_queue):
        retries = 3
        for attempt in range(retries):
            async with session.head(audio_url) as response:
                if response.status == 302:
                    audio_url = response.headers['Location']
                    continue
                if response.status != 200:
                    print(f"Failed to get audio info: {response.status}")
                    await download_queue.put(None)
                    return
                break
            asyncio.sleep(1)
        else:
            print("Failed to get audio info after retries")
            await download_queue.put(None)
            return

        total_size = int(response.headers.get('Content-Length'))
        chunk_size = total_size // 4  # Download in 4 chunks

        tasks = []
        for i in range(4):
            start = i * chunk_size
            end = (i + 1) * chunk_size - 1 if i != 3 else total_size - 1
            tasks.append(self.download_chunk(session, audio_url, start, end, download_queue))

        await asyncio.gather(*tasks)
        await download_queue.put(None)

    async def write_audio(self, temp_file_path, download_queue, buffer_queue):
        buffer_size = 10 * 1024 * 1024  # 10 MB buffer size

        async with aiofiles.open(temp_file_path, 'wb') as temp_file:
            while True:
                item = await download_queue.get()
                if item is None:
                    break
                start, chunk = item
                await temp_file.seek(start)
                await temp_file.write(chunk)
                await buffer_queue.put(chunk)
                download_queue.task_done()

            await buffer_queue.put(None)

    async def buffer_audio(self, audio_url):
        async with aiohttp.ClientSession() as session:
            try:
                temp_file_path = tempfile.mktemp(suffix='.mp3')
                download_queue = asyncio.Queue()
                buffer_queue = asyncio.Queue()

                download_task = asyncio.create_task(self.download_audio(session, audio_url, download_queue))
                write_task = asyncio.create_task(self.write_audio(temp_file_path, download_queue, buffer_queue))

                await asyncio.sleep(1)
                await asyncio.gather(download_task, write_task)
                return temp_file_path

            except Exception as e:
                print(f"Buffering error: {e}")
                return None

    async def search_track(self, query, user):
        """Search for a track using yt-dlp and buffer the audio."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch1',
            'max_downloads': 1,  # Limit the search to only 1 result
            'match_filter': yt_dlp.utils.match_filter_func('duration > 10 & duration < 450 & view_count > 1000'),
            'extractor_args': {'youtube': {'skip': ['dash', 'hls']}}
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if query.startswith("http"):
                    info = ydl.extract_info(query, download=False)
                else:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]

                track_url = info['url']
                track_duration = f"{info['duration'] // 60}:{info['duration'] % 60:02d}"
                track = {
                    "title": info['title'],
                    "uploader": info['uploader']
                }
                for items in self.req_files:
                    if items["title"] == info['title']:
                        await self.highrise.send_whisper(user.id, "The song is already in queue.")
                        return None, None, None

                attempts = 0
                while attempts < 3:
                    buffered_file_path = await self.buffer_audio(track_url)
                    file_size = os.path.getsize(buffered_file_path)
                    if file_size >= 4 * 1024:
                        break
                    attempts += 1
                    await asyncio.sleep(1)

                if file_size >= 4 * 1024:
                    return buffered_file_path, track_duration, track
                else:
                    return None, None, None
        except Exception as e:
            print(f"Error searching track: {e}")
            return None, None, None

    async def promo(self):
        while True:
            try:
                for items in promo:
                    await self.highrise.chat(items)
                    await asyncio.sleep(100)
                else:
                    await asyncio.sleep(100)
            except:
                pass
            await asyncio.sleep(300)

    async def notification(self):
        while True:
            try:
                if not self.req_files:
                    await self.highrise.chat("There are no song requests left. Type /play to request a song.")
            except:
                pass
            await asyncio.sleep(277)
    
    async def print_messages(self):
        while True:
            try:
                if self.message:
                    nowplaying = self.message[0]
                    fix_nowplaying = nowplaying['title']
                    if nowplaying['user']:
                        await self.highrise.chat(f"🎵 Now playing: {fix_nowplaying}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {nowplaying['audio_length']}\n (Requested by @{nowplaying['user']})")
                    else:
                        await self.highrise.chat(f"🎵 Now playing: {fix_nowplaying}\n 🎵 ▷ •ı||ıı|ıı|ı||ı|ıı||ı• {nowplaying['audio_length']}")
                    self.message.clear()
            except:
                pass
            await asyncio.sleep(5)

    async def run(self, room_id: str, token: str):
        definitions = [BotDefinition(self, room_id, token)]
        await __main__.main(definitions)
    
    def get_audio_length(self, audio_path):
        try:
            audio = MP3(audio_path)
            length = audio.info.length
            length = max(length, 0)
            minutes = int(length // 60)
            seconds = int(length % 60)
            return f"{minutes}:{seconds:02d}"
        except Exception as e:
            print(f"Error getting audio length for {audio_path}: {e}")
            return None

def get_ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix

def connect_to_icecast():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        sock.connect((SERVER_HOST, SERVER_PORT))
        print("Connected to Icecast server.")
        
        auth = f"source:{STREAM_PASSWORD}"
        headers = (
            f"PUT {MOUNT_POINT} HTTP/1.0\r\n"
            f"Authorization: Basic {base64.b64encode(auth.encode()).decode()}\r\n"
            f"Content-Type: audio/mpeg\r\n"
            f"ice-name: ROBINS MUSIC ®\r\n"
            f"ice-genre: Various\r\n"
            f"ice-url: http://{SERVER_HOST}:{SERVER_PORT}{MOUNT_POINT}\r\n"
            f"ice-public: 1\r\n"
            f"ice-audio-info: bitrate=320\r\n"
            f"\r\n"
        )
        sock.sendall(headers.encode('utf-8'))
        
        response = sock.recv(1024).decode('utf-8')
        print(f"Server response: {response}")
        
        if "HTTP/1.0 200 OK" in response:
            print("Authentication successful.")
        else:
            print("Unexpected server response. Closing connection.")
            sock.close()
            return None
        return sock
    except Exception as e:
        print(f"Connection error: {e}")
        return None


def start_streaming(bot_instance):
    try:
        while True:
            sock = connect_to_icecast()
            if sock:
                try:
                    while True:
                        if bot_instance.req_files:
                            audio_file = bot_instance.req_files[0]['url']
                            print(f"Streaming from bot_instance.req_files: {bot_instance.req_files[0]['title']}")
                        elif playlist:
                            random.shuffle(playlist)
                            erm = random.choice(playlist)
                            audio_file = erm['url']
                            print(f"Streaming from fav: {erm['title']}")
                        else:
                            random.shuffle(AUDIO_FILES)
                            audio_file = random.choice(AUDIO_FILES)

                        success = stream_audio(sock, audio_file, bot_instance)
                        if not success:
                            print("Stream interrupted, attempting reconnection...")
                            sock.close()
                            break

                        if bot_instance.skip:
                            bot_instance.skip = False
                            if bot_instance.now:
                                current_song = bot_instance.now.popleft()
                                for index, item in enumerate(bot_instance.req_files):
                                    if item == current_song:
                                        del bot_instance.req_files[index]
                                        break
                                print(f"Skipped: {current_song['title']}")
                            continue
                except Exception as e:
                    print(f"Error during streaming: {e}")
                    if sock:
                        sock.close()
            else:
                print("Failed to connect to Icecast server.")

            print("Reconnecting ...")
            time.sleep(3)
    except Exception as e:
        print(f"Error in start_streaming: {e}")

def stream_audio(sock, audio_file, bot_instance):
    try:
        print(f"Streaming audio file: {audio_file}")
        if audio_file != "Nothing.mp3":
            bot_instance.now.clear()
            bot_instance.message.clear()
            if audio_file in AUDIO_FILES:
                bot_instance.now.append({
                    'url': audio_file,
                    'title': audio_file.replace(".mp3", ""),
                    'user': None,
                    'audio_length': bot_instance.get_audio_length(audio_file)
                })
                bot_instance.message.append({
                    'url': audio_file,
                    'title': audio_file.replace(".mp3", ""),
                    'user': None,
                    'audio_length': bot_instance.get_audio_length(audio_file)
                })
        
        if playlist:
            matching_item = next((item for item in playlist if item['url'] == audio_file), None)
            if matching_item:
                details = {
                'url': matching_item['url'],
                'title': matching_item['title'],
                'user': None,
                'audio_length': matching_item['audio_length']
                }
                bot_instance.now.append(details)
                bot_instance.message.append(details)
    
        if bot_instance.req_files:
            if audio_file == bot_instance.req_files[0]['url']:
                bot_instance.now.append({
            'url': bot_instance.req_files[0]['url'],
            'title': bot_instance.req_files[0]['title'],
            'user': bot_instance.req_files[0]['user'],
            'audio_length': bot_instance.req_files[0]['duration']
        })
                bot_instance.message.append({
            'url': bot_instance.req_files[0]['url'],
            'title': bot_instance.req_files[0]['title'],
            'user': bot_instance.req_files[0]['user'],
            'audio_length': bot_instance.req_files[0]['duration']
        })
        else:
            pass

        command = [
            'ffmpeg',
            '-re',
            '-i', audio_file,
            '-map', '0:a',
            '-c:a', 'libmp3lame',
            '-ar', '44100',
            '-b:a', bot_instance.bitrate,
            '-f', 'mp3',
            '-content_type', 'audio/mpeg',
            '-buffer_size', '500k',
            '-'
        ]
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            data = process.stdout.read(4096)
            if bot_instance.skip:
                print(f"Skipping: {audio_file}")
                process.terminate()
                for index, item in enumerate(bot_instance.req_files):
                    if item['url'] == audio_file:
                        del bot_instance.req_files[index]
                        break
                if os.path.exists(audio_file):
                    if audio_file not in AUDIO_FILES:
                        if not any(item['url'] == audio_file for item in playlist):
                            try:
                                os.remove(audio_file)
                                print(f"Temporary file removed: {audio_file}")
                            except Exception as e:
                                print(f"Error cleaning up temporary file {audio_file}: {e}")
                return True
            if not data:
                process.terminate()
                print(f"Finished streaming: {audio_file}")
                bot_instance.message.clear()
                bot_instance.now.clear()
                # Clean up the req_files and now lists
                for index, item in enumerate(bot_instance.req_files):
                    if item['url'] == audio_file:
                        del bot_instance.req_files[index]
                        break
                if os.path.exists(audio_file):
                    if audio_file not in AUDIO_FILES:
                        if not any(item['url'] == audio_file for item in playlist):
                            try:
                                os.remove(audio_file)
                                print(f"Temporary file removed: {audio_file}")
                            except Exception as e:
                                print(f"Error cleaning up temporary file {audio_file}: {e}")

                return True
            try:
                sock.sendall(data)
            except (BrokenPipeError, ConnectionResetError) as e:
                print(f"Connection lost while sending chunk: {e}")
                process.terminate()
                return False
            time.sleep(0.05)
    except Exception as e:
        print(f"Streaming error: {e}")
        return False

def cleanup_temp_file(self, temp_file_path):
    """Remove the temporary file from memory."""
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Temporary file removed: {temp_file_path}")
    except Exception as e:
        print(f"Error cleaning up temporary file {temp_file_path}: {e}")
