import discord
import os
import random
from discord import app_commands
from discord.ext import commands
import string
import sys
from dotenv import load_dotenv
from discord.ui import Button, View
import asyncio
from datetime import datetime
import redis
import tracemalloc
import aiofiles

tracemalloc.start()

# Connect to Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)  # Adjust host and port if needed

# Load environment variables from .env file
load_dotenv()

# Access the bot token
TOKEN = os.getenv("TOKEN")

# You define the necessary intents
intents = discord.Intents.all()
intents.members = True
intents.typing = True
intents.presences = True

bot = commands.Bot(command_prefix='?', intents=intents)

# Global variable to store the invoice count
invoice_count = 0

bot.load_extension("jishaku")

support_role_id = 1224717647157924012  # Adjust the role ID as needed
# File path for the invoice count file
INVOICE_COUNT_FILE = 'invoice_count.txt'

async def save_invoice_count():
    global invoice_count
    async with aiofiles.open(INVOICE_COUNT_FILE, 'w') as file:
        await file.write(str(invoice_count))
    print(f"Invoices Saving: {invoice_count}")

async def load_invoice_count():
    global invoice_count
    try:
        async with aiofiles.open(INVOICE_COUNT_FILE, 'r') as file:
            data = await file.read()
            data = data.strip()
            if data:
                invoice_count = int(data)
                print(f"Loaded invoice count: {invoice_count}")
    except FileNotFoundError:
        print("Invoice count file not found. Creating a new one.")
        await save_invoice_count()
    except ValueError:
        print("Error: Unable to load invoice count. File contains invalid data.")

@bot.event
async def on_ready():
    print('Bot is ready and logged in as {0.user}'.format(bot))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name="Virtual Life"))

    # Channel to be purged and then send the setup_tickets command
    channel_id = 1224751818165194815
    channel = bot.get_channel(channel_id)

    channel_id2 = 1225797722704052286
    channel2 = bot.get_channel(channel_id2)
    
    await send_dashboard_embeds(channel2)

    if channel:
        # Purge all messages in the channel
        await channel.purge(limit=None)  # Be careful with this in production!
        print(f"All messages in {channel.name} have been purged.")

        # Create the setup_tickets message
        await setup_tickets_simple(channel)
        await setup_support_tickets_simple(channel)
    
    await load_invoice_count()

    await bot.tree.sync()

async def setup_tickets_simple(channel):
    guild = channel.guild
    support_role_id = 1224717647157924012  # Example support role ID
    view = OrderView(guild, support_role_id)  # Corrected to match the revised constructor
    embed = discord.Embed(title="Welcome to the Order Ticket Center!", description="Select an option below to proceed.", color=0xFF5733)
    embed.add_field(name="Available Services", value="Please choose one of the options below to create an order ticket.")
    embed.set_footer(text="Your fidelity is our priority!", icon_url="https://cdn.discordapp.com/attachments/1223622352953151660/1225142352239267911/Composition_1_1.gif?ex=6638717a&is=66371ffa&hm=988e782c7f0e9a53b8b74055ec8b4f09fa3cd1a5d041d67e036853080cd0dcbf")
    view = OrderView(channel.guild, 1224717647157924012)  # Only pass the guild and support role ID
    # Assuming you are sending some kind of message to attach the view to:
    await channel.send(embed=embed, view=view)

async def setup_support_tickets_simple(channel):
    guild = channel.guild
    view = OrderView(guild, support_role_id)  # Corrected to match the revised constructor
    embed = discord.Embed(title="Welcome to the Support Ticket Center!", description="Select an option below to proceed.", color=0xFF5733)
    embed.add_field(name="Available Services", value="Please choose one of the options below to create a support ticket.")
    embed.set_footer(text="Your security is our priority!", icon_url="https://cdn.discordapp.com/attachments/1223622352953151660/1225142352239267911/Composition_1_1.gif?ex=6638717a&is=66371ffa&hm=988e782c7f0e9a53b8b74055ec8b4f09fa3cd1a5d041d67e036853080cd0dcbf")
    view = SupportView(channel.guild, 1224717647157924012)  # Only pass the guild and support role ID
    await channel.send(embed=embed, view=view)

@bot.event
async def on_disconnect():
    print('Bot is disconnecting')
    save_invoice_count()

@bot.hybrid_command()
async def generate(ctx):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return  # Make sure to return here to prevent further execution

    key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    embed = discord.Embed(
        title="Kritany Private Token",
        description="Please be patient as one of our operators authorizes the key.",
        color=0xFF5733
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1235315299553902664.webp?size=96&quality=lossless")
    embed.add_field(name="Given by", value=ctx.author.display_name)
    embed.add_field(name="Key", value=key)

    await ctx.send(embed=embed)

async def has_support_role(ctx):
    # Check if the member has the support role
    support_role = ctx.guild.get_role(support_role_id)
    return support_role in ctx.author.roles

@bot.hybrid_command(name='invoice')
@app_commands.describe(user='The user to invoice', payment_method='Method of payment', price='Total price', promo_percentage='Discount percentage')
async def invoice(ctx: commands.Context, user: discord.Member, payment_method: str, price: float, promo_percentage: float = 0.0):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return
    global invoice_count
    invoice_count += 1
    invoice_number = str(invoice_count).zfill(3)
    promo_discount = price * (promo_percentage / 100)
    promo_price = price - promo_discount
    embed = discord.Embed(
        title=f"Invoice #{invoice_number}",
        description="ᴹᴬᴰᴱ ᶠᴼᴿ ᴬ ⱽᴵᴿᵀᵁᴬᴸ ᴸᴵᶠᴱ ᴼᴿᴰᴱᴿ",
        color=0xFF5733
    )
    embed.add_field(name="Method of Payment", value=payment_method, inline=False)
    embed.add_field(name="Price", value=f"{price:.2f} (After {promo_percentage}% discount: {promo_price:.2f})", inline=False)
    embed.add_field(name="Promotional Discount", value=f"{promo_percentage}%", inline=False)
    embed.add_field(name="Status", value="UNPAID", inline=False)
    await ctx.send(embed=embed)
    save_invoice_count()

@bot.hybrid_command()
@app_commands.describe(invoice_id='The Invoice Message ID')
async def invoice_paid(ctx, invoice_id: int):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return
    try:
        # Fetch the original message by its ID
        message = await ctx.channel.fetch_message(invoice_id)

        # Check if the message contains an embed
        if message.embeds:
            # Get the first embed
            embed = message.embeds[0]

            # Find the index of the "Status" field
            status_index = None
            for index, field in enumerate(embed.fields):
                if field.name == "Status":
                    status_index = index
                    break

            # If "Status" field is found, update its value
            if status_index is not None:
                embed.set_field_at(index=status_index, name="Status", value="PAID", inline=False)
                await message.edit(embed=embed)
                await ctx.send("Invoice status updated to PAID.")
            else:
                await ctx.send("No 'Status' field found in the specified message.")
        else:
            await ctx.send("No embed found in the specified message. Please provide a valid invoice ID.")
    except discord.NotFound:
        await ctx.send("Invoice not found. Please provide a valid invoice ID.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.hybrid_command()
async def set_invoice_count(ctx, count: int):
    global invoice_count
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return
    
    if count < 0:
        await ctx.send("Invoice count cannot be negative.")
        return

    invoice_count = count
    save_invoice_count()
    await ctx.send(f"Invoice count has been set to {count}.")

# Command to reload the bot
@bot.command()
async def reload(ctx):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    """Reload the entire bot."""
    await ctx.send("Reloading bot...")

    # Unload all extensions
    for extension in list(bot.extensions):
        bot.unload_extension(extension)

    # Reload the Python script
    python = sys.executable
    os.execl(python, python, *sys.argv)



class OrderView(discord.ui.View):
    def __init__(self, guild, support_role_id):
        super().__init__()
        self.guild = guild
        self.support_role_id = support_role_id

    async def create_ticket(self, interaction, ticket_type):
        # Mapping ticket types to their respective category IDs
        category_ids = {
            'Liveries': 1236864588243402813,
            'Clothes': 1236864527300165854,
            'Kritany': 1236860959079927848,
            'Graphic Designs': 1236864782125236226,
            'Multiple Things': 1236873120472633486 
        }
        category_id = category_ids[ticket_type]
        category = self.guild.get_channel(category_id)
        support_role = self.guild.get_role(self.support_role_id)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True)
        }
        ticket_channel = await category.create_text_channel(
            name=f"{ticket_type.lower().replace(' ', '-')}-{interaction.user.display_name}", 
            overwrites=overwrites
        )
        
        welcome_embed = discord.Embed(
            title=f"Order Ticket!",
            description=f"Hi {interaction.user.mention}, please be patient while a staff member gets to you.",
            color=discord.Color.blue()
        )
        welcome_embed.add_field(name="User", value=interaction.user.mention)
        welcome_embed.add_field(name="Role", value=support_role.mention)
        welcome_embed.set_footer(text="Thank you for ordering!")

        await ticket_channel.send(content=support_role.mention, embed=welcome_embed)
        await interaction.response.send_message(f"Your {ticket_type} ticket has been created: {ticket_channel.mention}", ephemeral=True)

    @discord.ui.select(
        placeholder="Choose the type of order",
        options=[
            discord.SelectOption(label="🏎️ Liveries", value="Liveries", description="Order custom liveries"),
            discord.SelectOption(label="👕 Clothes", value="Clothes", description="Order custom clothes"),
            discord.SelectOption(label="🖌️ Graphic Designs", value="Graphic Designs", description="Order graphic design work"),
            discord.SelectOption(label="🌟 Kritany", value="Kritany", description="Order for Kritany"),
            discord.SelectOption(label="2️⃣ Multiple Things", value="Multiple Things", description="Order involving multiple categories")
        ],
        min_values=1,  # Minimum number of items that must be selected
        max_values=1   # Maximum number of items that can be selected
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await self.create_ticket(interaction, select.values[0])

class SupportView(discord.ui.View):
    def __init__(self, guild, support_role_id):
        super().__init__()
        self.guild = guild
        self.support_role_id = support_role_id

    async def create_ticket(self, interaction, ticket_type):
        # Specific category IDs for support and report
        category_ids = {
            'General Support': 1236860854868250724,
            'Order Report': 1236860932999614536
        }
        category_id = category_ids[ticket_type]
        category = self.guild.get_channel(category_id)
        support_role = self.guild.get_role(self.support_role_id)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            support_role: discord.PermissionOverwrite(read_messages=True)
        }
        ticket_channel = await category.create_text_channel(
            name=f"{ticket_type.lower().replace(' ', '-')}-{interaction.user.display_name}", 
            overwrites=overwrites
        )
        
        welcome_embed = discord.Embed(
            title=f"{ticket_type} Support Ticket",
            description=f"Hi {interaction.user.mention}, your issue is important to us. Please be patient while we handle your request.",
            color=0xFF5733
        )
        welcome_embed.set_footer(text="Thank you for reaching out!")
        
        await ticket_channel.send(content=support_role.mention, embed=welcome_embed)
        await interaction.response.send_message(f"Your {ticket_type} support ticket has been created: {ticket_channel.mention}", ephemeral=True)

    @discord.ui.button(label="General Support", style=discord.ButtonStyle.primary, custom_id="general_support_button", emoji="<:adminwhite:1224746423661367298>")
    async def general_support_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, 'General Support')

    @discord.ui.button(label="Order Report", style=discord.ButtonStyle.secondary, custom_id="order_report_button", emoji="<:warningicon:1224778155542184141>")
    async def order_report_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, 'Order Report')

@bot.command()
async def setup_tickets(ctx):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    embed = discord.Embed(title="Welcome to the Store Bot", description="Select an option below to proceed.", color=0xFF5733)
    embed.add_field(name="Available Services", value="Please choose one of the options below to create a support ticket.")
    embed.set_footer(text="Your satisfaction is our priority!", icon_url="https://cdn.discordapp.com/attachments/1223622352953151660/1225142352239267911/Composition_1_1.gif?ex=6638717a&is=66371ffa&hm=988e782c7f0e9a53b8b74055ec8b4f09fa3cd1a5d041d67e036853080cd0dcbf")
    view = OrderView(ctx.guild, 1224753088649494548, 1224717647157924012)
    await ctx.send(embed=embed, view=view)

@bot.hybrid_command(name="done", description="Marks a ticket as complete and notifies staff to proceed with closure.")
async def done(ctx):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    # Rename the ticket channel
    await ctx.channel.edit(name=f"done")

    # Get the support role
    support_role = ctx.guild.get_role(support_role_id)
    if support_role is None:
        message = "The support role does not exist."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    # Send an embed message
    embed = discord.Embed(
        title="Order Completion",
        description=f"The order has been marked as complete and payment has been processed. {support_role.mention}, please proceed with the ending procedures.",
        color=0xFF5733
    )
    await ctx.channel.send(embed=embed)

    # Final response based on command type
    if hasattr(ctx, 'respond'):
        await ctx.respond(f"Ticket has been marked as complete. Notification sent to {support_role.mention}.", ephemeral=True)
    else:
        await ctx.send(f"Ticket has been marked as complete. Notification sent to {support_role.mention}.")

@bot.hybrid_command(name="close", description="Closes the current ticket by deleting the channel.")
async def close(ctx):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    # Logging or notification before deletion can be added here if needed
    if hasattr(ctx, 'respond'):
        await ctx.respond("Closing this ticket and deleting the channel...", ephemeral=True)

    # Delete the channel
    await ctx.channel.delete(reason="Ticket closed by user command.")

async def send_dashboard_embeds(channel2):
    # Purge the channel
    await channel2.purge(limit=30)  # Purge the last 10 messages in the channel
    
    # First embed with the dashboard banner image
    embed1 = discord.Embed(color=0x000000)
    embed1.set_image(url="https://cdn.discordapp.com/attachments/1223626595634511942/1237175444529221745/bannerdashboard.png")

    # Second embed for detailed server dashboard
    embed2 = discord.Embed(
        title="`         ☬ VIRTUAL LIFE DASHBOARD ☬         `",
        description="Navigate key sections and understand server hierarchy.",
        color=0x000000
    )

    # Adding fields for the rules channel
    embed2.add_field(
        name="`SERVER RULES`",
        value=f"Ensure to read and follow the server rules [here](https://discord.com/channels/{channel2.guild.id}/1224717691315552359).",
        inline=False
    )

    # Adding fields for seller ranks
    embed2.add_field(
        name="`OFFICIAL SELLER RANKS`",
        value=f"Meet our certified sellers. Do not order from anyone else.\n"
            f"- <@&1224717639201329278>\n"
            f"- <@&1224717641503997983>\n"
            f"- <@&1224759573727019039>",
        inline=False
    )

    # Adding fields for important channels
    embed2.add_field(
        name="`KEY CHANNELS`",
        value=f"Navigate to important areas of our community:\n"
            f"- Vouches: [Channel Link](https://discord.com/channels/{channel2.guild.id}/1224750116896903288)\n"
            f"- Tickets: [Channel Link](https://discord.com/channels/{channel2.guild.id}/1224751818165194815)",
        inline=False
    )

    # Footer and author with logo
    embed2.set_footer(text="Providing quality and assurance.")
    embed2.set_author(name="VIRTUAL LIFE MANAGEMENT TEAM", icon_url="https://cdn.discordapp.com/attachments/1223626595634511942/1237152602769195100/botgifv2.gif")

    # Sending both embeds to the channel
    await channel2.send(embed=embed1)
    await channel2.send(embed=embed2)

@bot.command()
async def rules(ctx):
    # First embed with just the rules image
    embed1 = discord.Embed(
        color=0x000000
    )
    embed1.set_image(url="https://cdn.discordapp.com/attachments/1223626595634511942/1237175420890382352/rulesbanner.png")

    # Second embed with individual fields for each rule, all inlined
    embed2 = discord.Embed(
        title="",
        description="`          ☬ VIRTUAL LIFE  ☬           `",
        color=0x000000
    )
    # General Server Rules
    embed2.add_field(name="> No Harassment", value="Harassing, bullying, or discriminatory behavior will not be tolerated.", inline=True)
    embed2.add_field(name="> Keep It Clean", value="Avoid posting adult content or using offensive language.", inline=True)
    embed2.add_field(name="> Respect Privacy", value="Do not share someone's personal information without their consent.", inline=True)
    embed2.add_field(name="> Follow Discord's TOS", value="Adhere to all terms outlined in Discord’s Terms of Service.", inline=True)
    # Virtual Life Shop Rules
    embed2.add_field(name="> No Spoonfeeding", value="Do not request complete solutions or excessive hand-holding. Use available resources to learn independently.", inline=True)
    embed2.add_field(name="> Respect & Patience", value="Maintain a respectful tone at all times. Avoid impatience or rudeness.", inline=True)
    embed2.add_field(name="> Non-Refundable Payments", value="Payments are final and non-refundable unless otherwise specified.", inline=True)
    embed2.add_field(name="> Vouching Requirement", value="You must vouch within 24 hours to activate any warranty.", inline=True)
    embed2.add_field(name="> Fixed Pricing", value="Prices are non-negotiable. Do not request to reduce the price of your order.", inline=True)

    # Footer and author with logo
    embed2.set_footer(text="Sors salutis et virtutis michi nunc contraria")
    embed2.set_author(name="VIRTUAL LIFE MANAGEMENT TEAM", icon_url="https://cdn.discordapp.com/attachments/1223626595634511942/1237152602769195100/botgifv2.gif")

    # Sending both embeds to the channel
    await ctx.send(embed=embed1)
    await ctx.send(embed=embed2)

@bot.event
async def on_message(message):
    # Check if the message is in the specified channel and contains the word "vouch"
    if message.channel.id == 1224750116896903288 and "vouch" in message.content.lower():
        # Save the vouch message to a text file
        with open("vouches.txt", "a") as file:
            file.write(f"Message ID: {message.id}\n")
            file.write(f"Content: {message.content}\n")
            file.write(f"Author: {message.author}\n")
            file.write(f"User ID: {message.author.id}\n")
            file.write(f"Timestamp: {message.created_at}\n\n")

        # Create the embed
        embed = discord.Embed(
            title="`THANK YOU FOR YOUR VOUCH!`",
            description="We appreciate your support. You will receive a promo code soon!",
            color=0x000000
        )
        # Footer and author with logo
        embed.set_footer(text="Providing quality and assurance.")
        embed.set_author(name="VIRTUAL LIFE MANAGEMENT TEAM", icon_url="https://cdn.discordapp.com/attachments/1223626595634511942/1237152602769195100/botgifv2.gif")

        # Send the embed as a reply to the message
        await message.reply(embed=embed)

    # Let other commands and events continue to work
    await bot.process_commands(message)

@bot.hybrid_command(name="rename", description="Renames the current channel.")
@app_commands.describe(new_name="The new name for the channel")
async def rename(ctx, new_name: str):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    # Rename the channel
    try:
        await ctx.channel.edit(name=new_name)
        confirmation_message = f"Channel name changed to {new_name}"
        if hasattr(ctx, 'respond'):
            await ctx.respond(confirmation_message, ephemeral=True)
        else:
            await ctx.send(confirmation_message)
    except discord.Forbidden:
        error_message = "I do not have permission to rename this channel."
        if hasattr(ctx, 'respond'):
            await ctx.respond(error_message, ephemeral=True)
        else:
            await ctx.send(error_message)
    except discord.HTTPException as e:
        error_message = f"Failed to rename the channel. {str(e)}"
        if hasattr(ctx, 'respond'):
            await ctx.respond(error_message, ephemeral=True)
        else:
            await ctx.send(error_message)

@bot.hybrid_command(name="disable", description="Closes a user's ticket and notifies them via DM.")
@app_commands.describe(user="The user to notify", reason="The reason for the ticket closure")
async def disable(ctx, user: discord.Member, reason: str):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return

    # Attempt to send a DM to the user
    try:
        embed = discord.Embed(
            title="Ticket Closed",
            description="Your ticket has been closed, and your order will not proceed further unless you submit a new one with a better attitude.",
            color=discord.Color.red()
        )
        embed.add_field(name="REASON FOR CLOSURE", value=reason)
        embed.set_footer(text="Respect is the key to cooperation.", icon_url="https://cdn.discordapp.com/attachments/1223622352953151660/1225142352239267911/Composition_1_1.gif?ex=6638717a&is=66371ffa&hm=988e782c7f0e9a53b8b74055ec8b4f09fa3cd1a5d041d67e036853080cd0dcbf")
        await user.send(embed=embed)
    except discord.HTTPException:
        error_message = "Failed to send a DM to the user."
        if hasattr(ctx, 'respond'):
            await ctx.respond(error_message, ephemeral=True)
        else:
            await ctx.send(error_message)
        return

    # Confirm deletion to the command initiator before actual deletion
    confirmation_message = "The channel will now be deleted and the user has been notified."
    try:
        if hasattr(ctx, 'respond'):
            # Use followup.send for slash commands if the original interaction has already been responded to
            await ctx.followup.send(confirmation_message, ephemeral=True)
        else:
            await ctx.send(confirmation_message)
    except discord.HTTPException as e:
        await ctx.send(f"Failed to send confirmation: {str(e)}")

    # Wait a bit before deleting the channel to ensure the message is sent
    await asyncio.sleep(1)  # Sleep for 1 second

    # Delete the channel
    try:
        await ctx.channel.delete(reason="Disabled by command.")
    except discord.Forbidden:
        error_message = "I do not have permission to delete this channel."
        if hasattr(ctx, 'respond'):
            await ctx.respond(error_message, ephemeral=True)
        else:
            await ctx.send(error_message)
    except discord.HTTPException as e:
        error_message = f"Failed to delete the channel. {str(e)}"
        if hasattr(ctx, 'respond'):
            await ctx.respond(error_message, ephemeral=True)
        else:
            await ctx.send(error_message)


# PROMOTION SYSTEM


# Create a command group using app_commands.Group

class UsedButton(discord.ui.Button):
    def __init__(self, promo_code):
        super().__init__(style=discord.ButtonStyle.red, label="Used?", emoji="<:win11erroicon:1224747056959062067>")
        self.promo_code = promo_code

    async def callback(self, interaction: discord.Interaction):
        # Read all lines from the file
        with open("promocodes.txt", "r") as file:
            lines = file.readlines()
        # Write back all lines except the one with the promo code
        with open("promocodes.txt", "w") as file:
            for line in lines:
                if line.split(',')[0] != self.promo_code:
                    file.write(line)
        await interaction.response.send_message("Promo code has been marked as used and removed.", ephemeral=True)

@bot.hybrid_command(name="promo_generate", description="Generate a promo code for a user with a specified discount.")
@app_commands.describe(user="The user to generate the promo for", discount="The discount percentage")
async def promo_generate(ctx: commands.Context, user: discord.User, discount: int):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return
    """Generate a new promo code."""
    promo_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Store promo code details along with the creator's ID in a text file
    with open("promocodes.txt", "a") as file:
        file.write(f"{promo_code},{user.id},{ctx.author.id},{discount},{date_created}\n")
    await ctx.send(f"Promo code **{promo_code}** with {discount}% discount generated for {user.mention} by {ctx.author.mention} on {date_created}.")

    # Send DM to the user with promo code details
    try:
        embed = discord.Embed(
            title="🎉 You've Received a Promotion Code! 🎉",
            description=f"Congratulations! You've been granted a promotion code that provides a {discount}% discount.",
            color=discord.Color.green()
        )
        embed.add_field(name="Promo Code", value=promo_code)
        embed.add_field(name="Discount", value=f"{discount}% off")
        embed.add_field(name="Promo Code Creator", value=f"{ctx.author.display_name}")
        embed.set_footer(text=f"Thank you for using our service! We hope you enjoy your discount. | discord.gg/virtulife")
        await user.send(embed=embed)
    except discord.HTTPException:
        await ctx.send(f"Failed to send DM to {user.display_name}. They might have DMs disabled.")
    except discord.Forbidden:
        await ctx.send(f"Do not have permission to send DMs to {user.display_name}.")


@bot.hybrid_command(name="promo_check", description="Check details of a promo code.")
@app_commands.describe(promo_code="The promo code to check")
async def promo_check(ctx: commands.Context, promo_code: str):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return
    try:
        with open("promocodes.txt", "r") as file:
            lines = file.readlines()
            for line in lines:
                code, user_id, creator_id, discount, date_created = line.strip().split(',')
                if code == promo_code:
                    user = await bot.fetch_user(int(user_id))
                    creator = await bot.fetch_user(int(creator_id))
                    embed = discord.Embed(
                        title="Promo Code Details",
                        description=f"**Code:** {promo_code}\n**Discount:** {discount}%\n**Date Created:** {date_created}",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Owned by", value=f"{user.name}#{user.discriminator}")
                    embed.add_field(name="Created by", value=f"{creator.name}#{creator.discriminator}")
                    
                    view = discord.ui.View()
                    view.add_item(UsedButton(promo_code))
                    
                    await ctx.send(embed=embed, view=view)
                    return
        await ctx.send("Promo code not found.")
    except FileNotFoundError:
        await ctx.send("No promo codes have been generated yet.")

@bot.hybrid_command(name="promo_list", description="List all promotional codes currently available.")
async def promo_list(ctx: commands.Context):
    if not await has_support_role(ctx):
        message = "You do not have the necessary role to use this command."
        if hasattr(ctx, 'respond'):
            await ctx.respond(message, ephemeral=True)
        else:
            await ctx.send(message)
        return
    """List all promotional codes."""
    if not os.path.exists("promocodes.txt"):
        await ctx.send("No promotional codes have been generated yet.")
        return

    with open("promocodes.txt", "r") as file:
        lines = file.readlines()

    if not lines:
        await ctx.send("No promotional codes are currently available.")
        return

    # Create an embed to list all promo codes
    embed = discord.Embed(
        title="List of All Promotional Codes",
        description="Here are all the promotional codes currently available:",
        color=discord.Color.blue()
    )

    for line in lines:
        promo_code, user_id, creator_id, discount, date_created = line.strip().split(',')
        user = await bot.fetch_user(int(user_id))
        creator = await bot.fetch_user(int(creator_id))
        embed.add_field(
            name=f"Code: {promo_code} ({discount}% off)",
            value=f"User: {user.name}#{user.discriminator}\n"
                f"Creator: {creator.name}#{creator.discriminator}\n"
                f"Date Created: {date_created}",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.hybrid_command(name="image_perms", description="Toggle image permissions for a user in this channel.")
@app_commands.describe(user="The user to toggle image permissions for")
async def image_perms(ctx: commands.Context, user: discord.Member):
    # Use the channel from the context where the command is invoked
    channel = ctx.channel

    # Check current permissions for the user in the channel
    current_overwrites = channel.overwrites_for(user)
    
    # Toggle the attach_files and embed_links permissions
    new_perms = not current_overwrites.attach_files  # Assume both permissions are synchronized
    current_overwrites.attach_files = new_perms
    current_overwrites.embed_links = new_perms

    # Set the modified permissions
    await channel.set_permissions(user, overwrite=current_overwrites)

    # Create an embed to inform about the change
    embed = discord.Embed(
        title="Permissions Updated",
        description=f"{'Enabled' if new_perms else 'Disabled'} the ability to attach files and embed links for {user.mention} in this channel.",
        color=discord.Color.green() if new_perms else discord.Color.red()
    )
    await ctx.send(embed=embed, ephemeral=True if isinstance(ctx, discord.Interaction) else False)

@bot.hybrid_command(name="remind_order", description="Send a reminder to specific users to complete an order.")
async def remind_order(ctx: commands.Context):
    # User IDs to be reminded
    user_id_1 = 925423922399301712
    user_id_2 = 398809599836160011

    # Fetching the users from their IDs
    user_1 = await bot.fetch_user(user_id_1)
    user_2 = await bot.fetch_user(user_id_2)

    # Construct the mention string
    mentions = f"{user_1.mention} {user_2.mention}"

    # Embed for additional order details
    embed = discord.Embed(
        title="Order Reminder",
        description="You have an order pending. Please check and complete it as soon as possible.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="This is a system-generated reminder.")

    # Sending the message
    await ctx.send(content=mentions, embed=embed)

@bot.hybrid_command(name="shame", description="Bans a user and adds him to the hall of shame.")
async def shame(ctx, member: discord.Member, *, reason: str):
    # Check if the command user has the allowed role
    allowed_role_id=1225149548201250816
    if discord.utils.get(ctx.author.roles, id=allowed_role_id):
        # Create an embed for the hall of shame
        embed = discord.Embed(title="MEMBER BAN", description="This member has been banned.", color=0xFF5733)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1223622352953151660/1225141710359625798/Composition_1.gif?ex=663919a1&is=6637c821&hm=970726e9b7e12d0dcb9bfe954f319b3597fd3bcc0f1d68a867757bce31288177&")
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Banned by {ctx.author.name}")
        embed.set_author(name="O Fortuna, velut luna, statu variabilis.", icon_url="https://cdn.discordapp.com/emojis/1226176750682378261.gif?size=96&quality=lossless")
        
        # Get the hall of shame channel by its ID
        hall_of_shame_channel = bot.get_channel(1232827855004762153)
        
        # Send the embed to the hall of shame channel
        await hall_of_shame_channel.send(embed=embed)
        
        # Ban the user
        await ctx.guild.ban(member, reason=reason)
        
        await ctx.send(f"{member.mention} has been banned and added to the Hall of Shame for: {reason}.")
    else:
        await ctx.send("You do not have permission to use this command.")

@bot.hybrid_command(name="show_vouches", description="Show all saved vouches.")
async def show_vouches(ctx):
    vouches = []

    # Read vouches from the text file
    with open("vouches.txt", "r") as file:
        lines = file.readlines()
        vouch_info = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Message ID:"):
                vouch_info["message_id"] = line.split("Message ID: ")[1]
            elif line.startswith("Content:"):
                vouch_info["content"] = line.split("Content: ")[1]
            elif line.startswith("Author:"):
                vouch_info["author"] = line.split("Author: ")[1]
            elif line.startswith("User ID:"):
                vouch_info["user_id"] = line.split("User ID: ")[1]
            elif line.startswith("Timestamp:"):
                vouch_info["timestamp"] = line.split("Timestamp: ")[1]
                vouches.append(vouch_info)
                vouch_info = {}

    # Create the embed
    embed = discord.Embed(
        title="`VOUCHES`",
        description="Here are all vouches received:",
        color=0x000000
    )

    # Add vouches to the embed
    for vouch in vouches:
        embed.add_field(
            name=f"Author: {vouch['author']} (User ID: {vouch['user_id']})",
            value=f"Message ID: {vouch['message_id']}\nContent: {vouch['content']}\nTimestamp: {vouch['timestamp']}",
            inline=False
        )

    # Footer and author with logo
    embed.set_footer(text="Providing quality and assurance.")
    embed.set_author(name="VIRTUAL LIFE MANAGEMENT TEAM", icon_url="https://cdn.discordapp.com/attachments/1223626595634511942/1237152602769195100/botgifv2.gif")

    # Send the embed
    await ctx.send(embed=embed)

bot.run(TOKEN)
