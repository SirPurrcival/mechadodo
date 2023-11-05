# -*- coding: utf-8 -*-
"""
Created on Wed Oct 11 10:08:06 2023

@author: Meowlin
"""


import discord
from discord.ext import tasks, commands
import random

import datetime
import asyncio
import math

#from bot_helper import suicide_watch

with open('token.txt') as f:
    token = f.readline()
    

PREFIX = ("/")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(intents=intents,
                    command_prefix=PREFIX, 
                    activity = discord.Game(name="Going Extinct"), 
                    description="Commencing spam annihilation")


bot.threadwatch = dict()

# cog_files = ['bot_helper']

# async def setup(bot):
#     for helper in cog_files:
#         await bot.load_extension(helper)
#         print("%s has loaded." % helper)

## Login
@bot.event
async def on_ready():
    ##Start loop tasks
    change_status.start()
    kill_stragglers.start()
    thread_CPR.start()
    # setup(bot)
    
    try:
        with open("threadwatch.txt") as fn:
            temp = fn.read().split("\n")
            
            print("Threads currently being watched:")
            for entry in temp:
                if entry != '':
                    tid, gid = entry.split("|")
                    tid = int(tid)
                    gid = int(gid)
                    if gid in bot.threadwatch.keys():
                        bot.threadwatch[gid].append(tid)
                    else:
                        bot.threadwatch[gid] = [tid]
                    guild = bot.get_guild(gid)
                    thread = bot.get_channel(tid)
                    print(f"{thread} on {guild}")
                    

    except:
        pass
    
    print('Ready and waitin')
    
@bot.event
async def on_raw_message_edit(msg):
    
    ## Get channel and messages from event
    channel = bot.get_channel(msg.channel_id)
    message = await channel.fetch_message(msg.message_id)
    
    ## If the edited message contains a certain string indicating
    ## that the original message has been deleted, delete the whole message
    if message.content.startswith("[Original Message Deleted]"):
        await message.delete()
        print("Wikispam deleted")

@tasks.loop(minutes=120.0)
async def change_status():
    status = random.randint(0, 2)
    if status == 0:
        await bot.change_presence(activity=discord.Game(name="Going Extinct"))
    elif status == 1:
        await bot.change_presence(activity=discord.Game(name="Removing Spam"))
    elif status == 2:
        await bot.change_presence(activity=discord.Game(name="Dying Entirely Preventable Deaths"))

@tasks.loop(minutes=30.0)
async def kill_stragglers():
    killcount = 0
    for ch in bot.get_all_channels():
        if isinstance(ch, discord.TextChannel):
            try:
                async for message in ch.history(limit=20):
                    if message.content.startswith("[Original Message Deleted]"):
                        await message.delete()
                        killcount += 1
            except:
                continue
    print(f"Removed {killcount} spam messages this cycle.")

          
###############################################################################
######################## Forum life support ###################################
###############################################################################
 
@bot.tree.command(name="thread_life_support", description="Keep your forums and threads alive by unnatural means.")
async def necro(interaction, all_threads: bool):
    if isinstance(interaction.channel, discord.Thread):
        
        ## Get thread and server IDs
        thread = interaction.channel
        guild_id = interaction.channel.guild.id
        
        ## If the flag is set to True, enter all threads into witness
        ## protection programs to prevent them from accidentally being
        ## suicided by discord
        if all_threads == True:
            for thrd in interaction.channel.parent.threads:
                await suicide_watch(interaction, thrd, guild_id)
            await interaction.response.send_message("Entered selected threads into the trauma team platinum package!", 
                                                    ephemeral = True,  
                                                    delete_after=60)
        ## Otherwise just add the single thread
        else:
            ## If we are already watching this thread we don't need to do anything 
            ## but let the user know
            if guild_id in bot.threadwatch.keys():
                if thread.id in bot.threadwatch[guild_id]:
                    await interaction.response.send_message("Thread is already being watched.", 
                                                            ephemeral = True,  
                                                            delete_after=60)
                    return
            
            await suicide_watch(interaction, thread, guild_id)
            await interaction.response.send_message("Entered selected thread into the trauma team platinum package!", 
                                                    ephemeral = True,  
                                                    delete_after=60)
    else:
        ## Let users know that this command should be sent in a thread, not anywhere else.
        await interaction.response.send_message("Use this command in a thread.", delete_after=10)
    
@commands.command()
async def suicide_watch(interaction, thread, guild_id):
    
    ## If we are already watching this thread we don't need to do anything 
    ## but let the user know
    if guild_id in bot.threadwatch.keys():
        if thread.id in bot.threadwatch[guild_id]:
            return
    
    
    ## Get channel ID and write to disk
    try:
        ## If there is a list, append to it
        with open("threadwatch.txt", "a") as fn:
            fn.writelines(str(thread.id) + "|" + str(guild_id) + "\n")
            
    except:
        ## If there isn't, create one
        with open("threadwatch.txt", "w") as fn:
            fn.writelines(str(thread.id) + "|" + str(guild_id) + "\n")
    
    
    ## Set thread life to 7 days
    await thread.edit(auto_archive_duration=10080)
    
    ## Add thread to dictionary. Append to guild if guild has existing threads,
    ## otherwise create new entry for current guild
    if guild_id in bot.threadwatch.keys():
        bot.threadwatch[guild_id].append(thread.id)
    else:
        bot.threadwatch[guild_id] = [thread.id]

###############################################################################
#################### Remove threads from suicide watch ########################
###############################################################################

@bot.tree.command(name="remove_life_support", description="Pull the plug.")
async def remove_thread(interaction, all_threads: bool, archive_threads: bool):
    
    ## Check if this is even posted in a thread, if not, don't do anything.
    if isinstance(interaction.channel, discord.Thread):
        
        ## Get server ID
        guild_id = interaction.channel.guild.id
        ## List of threads
        forum = interaction.channel.parent
        
        ## If the thread is currently not being watched, let the user know.
        if guild_id not in bot.threadwatch.keys():
            await interaction.response.send_message("No threads on this server are being watched.", 
                                                    ephemeral = True,  
                                                    delete_after=5)
            return
        
        
        
        
        ## If flag is set to true, remove all threads from watch
        if all_threads == True:
            for thrd in forum.threads:
                
                
                ## If no more threads on the current server remain, return
                if not guild_id in bot.threadwatch.keys():
                    await interaction.response.send_message(f"Removed all threads in {forum.name} from life support.", 
                                                            ephemeral = True,  
                                                            delete_after=5)
                    return
                
                ## Skip if current thread is not on watchlist
                if thrd.id not in bot.threadwatch[guild_id]:
                    continue
                
                
                ## Go through all threads and try to remove them from our
                ## dictionary. Ignore error if item not in list
                try:
                    bot.threadwatch[guild_id].remove(thrd.id)
                    
                    ## Also delete from .txt
                    with open("threadwatch.txt", "r") as f:
                        lines = f.readlines()
                    with open("threadwatch.txt", "w") as f:
                        for line in lines:
                            if not (str(thrd.id) in line and str(guild_id) in line):
                                f.write(line)
                except:
                    pass
                
                
                            
                
                ## If flag is set to true, also archive thread
                if archive_threads == True:
                    await thrd.edit(archived = True)
                
                ## In case this was the last thread of the server
                ## Delete the key as well
                print(bot.threadwatch)
                if bot.threadwatch[guild_id] == []:
                    del bot.threadwatch[guild_id]

            await interaction.response.send_message(f"Removed all threads in {forum.name} from life support.", 
                                                    ephemeral = True,  
                                                    delete_after=5)
            
        ## Otherwise just delete the single thread from watch
        else:
            
            ## Get thread ID
            thread = interaction.channel
            
            ## If the thread is currently not being watched, let the user know.
            if thread.id not in bot.threadwatch[guild_id]:
                await interaction.response.send_message("Thread is not on watchlist.", 
                                                        ephemeral = True,  
                                                        delete_after=5)
                return
            
            ## Remove from threadwatch
            bot.threadwatch[guild_id].remove(thread.id)
            
            ## Also delete from .txt
            with open("threadwatch.txt", "r") as f:
                lines = f.readlines()
            with open("threadwatch.txt", "w") as f:
                for line in lines:
                    if not (str(thread.id) in line and str(guild_id) in line):
                        f.write(line)
            
            ## If flag is set to true, also archive thread
            if archive_threads == True:
                await thread.edit(archived = True)
            
            ## In case this was the last thread of the server
            ## Delete the key as well
            if bot.threadwatch[guild_id] == []:
                del bot.threadwatch[guild_id]

            await interaction.response.send_message(f"Removed {thread.name} from life support.", 
                                                    ephemeral = True,  
                                                    delete_after=5)
    else:
        ## Let users know that this command should be sent in a thread, not anywhere else.
        await interaction.response.send_message("Use this command in a thread.", 
                                                ephemeral = True,  
                                                delete_after=5)

###############################################################################
########################## List archived threads ##############################
###############################################################################

@bot.tree.command(name="list_watched_threads", description="Secret documents from the witness protection program.")
async def list_threads(interaction):
    
    server = interaction.guild
    thread_dict = bot.threadwatch.values()
    
    output = ""
    
    current_category = 0
    for key in thread_dict:
        for thrd in key:
            thread = await server.fetch_channel(thrd)
            if thread.parent.id == current_category:
                output += "".join("-" + thread.name + "\n")
            else:
                output += "".join(output + thread.parent.name + "\n-" + thread.name + "\n")
                current_category = thread.parent.id
    
    
    await interaction.response.send_message("The following threads are currently being watched:\n" + output, 
                                            ephemeral = True,  
                                            delete_after=60)

@tasks.loop(hours=24.0)
async def thread_CPR():
    
    now = datetime.datetime.now().time().hour
    dt  = datetime.datetime(2023, 12, 12, 4, 0 ,0, 0).time().hour
    
    if now-dt < 0:
        delta_time = math.abs(now-dt)
    else:
        delta_time = 24 - (now-dt)
        
    print(f"Scheduled thread life support commencing in {delta_time} hours.")
    
    await asyncio.sleep(delta_time * 60 * 60)
    
    print("Commencing thread life support")
    
    for guild in bot.threadwatch.keys():
        for thrd in bot.threadwatch[guild]:
            
            ## Changing auto archive duration counts as activity
            thread = await bot.get_guild(guild).fetch_channel(thrd)
            await thread.edit(auto_archive_duration=60)
            await thread.edit(auto_archive_duration=10080)


@bot.command()
async def sync(ctx):
    print("sync command")
    if ctx.author.id == 239086116890869761:
        await bot.tree.sync()
        await ctx.send('Command tree synced.', delete_after=0)
    else:
        await ctx.send('You must be the owner to use this command!')

bot.run(token)
