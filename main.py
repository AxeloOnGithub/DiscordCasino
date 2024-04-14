import discord
import json
from discord.ext import commands
from interactions import slash_command, SlashContext
from discord.ui import Button, View
from discord import *
import random
from dotenv import load_dotenv
import os
from PIL import Image, ImageDraw, ImageFont
from pymongo import MongoClient
from datetime import date, datetime

#!enviroment variables
load_dotenv("token.env")
mongodb_password = os.getenv("MONGODB_PASSWORD")
token = os.getenv("DISCORD_TOKEN")

cluster = MongoClient(f"mongodb+srv://DiscordCasino:{mongodb_password}@discordcasino.xoeonsi.mongodb.net/?retryWrites=true&w=majority&appName=DiscordCasino")

#!BOT SETTINGS
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".",intents=intents)

#!CLasses
class CardBackground:
    def __init__(self, background_image_path):
        self.background_img = Image.open(background_image_path)
        self.cards = []
        self.next_dealer_position = (650, 290)
        self.next_player_position = (650, 2040)
        self.card_mapping = {}
        self.text_fields = []

        # Generate card names and image paths for clubs
        for value in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]:
            card_name = f"clubs_{value}"
            self.card_mapping[card_name] = f"images/Playing_Cards/{card_name}.png"

        # Generate card names and image paths for hearts, diamonds, and spades (similar pattern)
        for suit in ["hearts", "diamonds", "spades"]:
            for value in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]:
                card_name = f"{suit}_{value}"
                self.card_mapping[card_name] = f"images/Playing_Cards/{card_name}.png"

    def clear_cards(self):
        self.cards = []

    def clear_text_fields(self):
        self.text_fields = []

    def add_card(self, card_name, hand_type="DealerHand", lock=False, hide_dealer=False):
        card_name = card_name.lower()  # Convert to lowercase to handle case-insensitive input

        
        suit_mapping = {"c": "clubs", "h": "hearts", "d": "diamonds", "s": "spades"}
        value_mapping = {"2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "j": "jack", "q": "queen", "k": "king", "a": "ace"}
        
        suit = suit_mapping.get(card_name[0])
        value = value_mapping.get(card_name[1:])
        if suit is None or value is None:
            raise ValueError("Invalid card name")

        full_card_name = f"{suit}_{value}"
        card_image_path = self.card_mapping.get(full_card_name)

        if not card_image_path:
            raise ValueError("Invalid card name")

        if hand_type == "DealerHand":
            position = self.next_dealer_position
            self.next_dealer_position = (self.next_dealer_position[0] + 150, self.next_dealer_position[1])
        elif hand_type == "PlayerHand":
            position = self.next_player_position
            self.next_player_position = (self.next_player_position[0] + 150, self.next_player_position[1])
        else:
            raise ValueError("Invalid hand type")

        self.cards.append((card_image_path, position, lock))

    def add_blank(self, scale_factor=2, output_image_path="images/output_image.jpg"):
        card_img = Image.open("images/Playing_Cards/back.png")

        card_width, card_height = card_img.size
        resized_width = int(card_width * scale_factor)
        resized_height = int(card_height * scale_factor)
        resized_card_img = card_img.resize((resized_width, resized_height))

        x_pos, y_pos = (800, 290)

            # Paste the card on the background
        self.background_img.paste(resized_card_img, (x_pos, y_pos), resized_card_img)

        self.background_img.save(output_image_path)

    def add_blank_card(self, position):
        blank_card_path = "images/Playing_Cards/back.png"  # Replace this with the path to your blank card image
        self.cards.append((blank_card_path, position, False))

    def add_text_field(self, text, position, font_size=120):
        self.text_fields.append((text, position, font_size))

    def add_cards_to_background(self, output_image_path, scale_factor=0.25):

        for card_image_path, position, lock in self.cards:
            # Open card image
            card_img = Image.open(card_image_path)

            # Resize card image based on scale factor
            card_width, card_height = card_img.size
            resized_width = int(card_width * scale_factor)
            resized_height = int(card_height * scale_factor)
            resized_card_img = card_img.resize((resized_width, resized_height))

            # Rotate the card image if lock is True
            if lock:
                resized_card_img = resized_card_img.rotate(90, expand=True)

            # Calculate position to place the card
            x_pos, y_pos = position

            # Paste the card on the background
            self.background_img.paste(resized_card_img, (x_pos, y_pos), resized_card_img)

        # Save the result
        self.background_img.save(output_image_path)

        draw = ImageDraw.Draw(self.background_img)
        for text, position, font_size in self.text_fields:
            font = ImageFont.truetype("arial.ttf", font_size)
            bbox = draw.textbbox(position, text, font=font)
            x = (bbox[0] + bbox[2]) / 2
            y = (bbox[1] + bbox[3]) / 2
            draw.text((x, y), text, fill="black", font=font)

        # Save the result
        self.background_img.save(output_image_path)

class end:

    async def PlayerBust(interaction, bet, ctx):
        await interaction.message.edit(embed=discord.Embed(title="Player Bust! Dealer wins", description=f"You went over 21 and lost your bet of **${bet}**.", color=colors.red), view=None)
        money_handler(ctx, bet, False)
        stats_handler(ctx, "blackjack", False)

    async def DealerBust(interaction, bet, ctx):
        await interaction.message.edit(embed=discord.Embed(title="Dealer Bust! Player wins", description=f"The Dealer went over 21 and your initial bet of ${bet} is now **${bet*2}**.", color=colors.green), view=None)
        money_handler(ctx, bet, True)
        stats_handler(ctx, "blackjack", True)

    async def Push(interaction, bet, ctx):
        await interaction.message.edit(embed=discord.Embed(title="Push!", description=f"You and the Dealers cards were of same value", color=colors.blue), view=None)
        stats_handler(ctx, "blackjack", True)

    async def PlayerWin(interaction, bet, ctx):
        await interaction.message.edit(embed=discord.Embed(title="Player Win!", description=f"Your cards were of higher value than the Dealer and your initial bet of ${bet} is now **${bet*2}**.", color=colors.green), view=None)
        money_handler(ctx, bet, True)
        stats_handler(ctx, "blackjack", True)

    async def DealerWin(interaction, bet, ctx):
        await interaction.message.edit(embed=discord.Embed(title="Dealer Win!", description=f"The Dealers cards were of higher value than yours and you lost bet of **${bet}**.", color=colors.red), view=None)
        money_handler(ctx, bet, False)
        stats_handler(ctx, "blackjack", False)

    async def PlayerBJ(interaction, bet, ctx):
        await interaction.channel.send(embed=discord.Embed(title="Player Blackjack!", description=f"You got a Blackjack and your initial bet of ${bet} is now **${bet*2.5}**.", color=colors.green), view=None)
        money_handler(ctx, bet*1.5, True)
        stats_handler(ctx, "blackjack", True)

    async def DealerBJ(interaction, bet, ctx):
        await interaction.message.edit(embed=discord.Embed(title="Dealer Blackjack!", description=f"The Dealer got a Blackjack and you lost bet of **${bet}**.", color=colors.red), view=None)
        money_handler(ctx, bet, False)
        stats_handler(ctx, "blackjack", False)

class colors:

    blue = 0x006eff
    red = 0xff0000
    green = 0x00ff00

class images:

    heads_logo = "https://lh3.googleusercontent.com/u/0/drive-viewer/AKGpihaOc-4xb5mgyK0qN7hwtf2HMkflN5YQfnQh6ZSINLokPqTMeX9rs566s3SjP1WOb1OwHLsp1GDDaNdG440RNCgENqD8=w1080-h1785-v0"
    tails_logo = "https://lh3.googleusercontent.com/u/0/drive-viewer/AKGpihYqf6Z26jCCrZq57i_mBBPGNFkrSi_urTQ1k13yMj3GdZnkIKHlwdBJVr0pA2juGpcBGSOogtWffOPeLf7322SzF2N2hw=w1080-h1785-v0"
    CF_logo = "https://lh3.googleusercontent.com/u/0/drive-viewer/AKGpihb05RWJrUmlbAF5XzUiZSPt6S8dY3qDd5asXZyDaRF2A_iadPa3HQBMnZEtrjIUUB3ychqfefhPf6dW1aDR-fS9bW2z=w1080-h1785-rw-v1"
    BJ_logo = "https://lh3.googleusercontent.com/u/0/drive-viewer/AKGpihbVYNTA85Qj4OWM6mgLJKDWK7_91WV0aJ3M9oriHbNCAXIEKshznOtDsTUfbEL3PW1plZWqhkOuY1p7RMRJoo_R3QjzUw=w1080-h1785-rw-v1"       

#!COINFLIP FUNCTIONS
def GetData(id=None, name=None, field=None):
    db = cluster["Casino"]
    collection = db["Users"]

    if id != None:
        return collection.find_one({"_id": id}).get(field)
    elif name != None:
        return collection.find_one({"name": name}).get(field)
    
def UpdateData(data, id=None, name=None, field=None, operator="$inc"):
    db = cluster["Casino"]
    collection = db["Users"]

    if id != None:
        collection.update_one({"_id": id}, {operator: {field: data}})
    elif name != None:
        collection.update_one({"name": name}, {operator: {field: data}})

def InsertData(data):
    db = cluster["Casino"]
    collection = db["Users"]

    collection.insert_one(data)

def can_afford(ctx, bet):
    with open("bank.json", "r") as info:
        data = json.load(info)

    if bet > data[str(ctx.user.id)]["balance"]:
        return False
    else:
        return True
    
def money_handler(ctx, bet, add):

    if add:
        UpdateData(bet, id=ctx.user.id, field="balance", operator="$inc")
        UpdateData(-bet, name="Casino", field="balance", operator="$inc")

    if not add:
        UpdateData(-bet, id=ctx.user.id, field="balance", operator="$inc")
        UpdateData(bet, name="Casino", field="balance", operator="$inc")

def stats_handler(ctx, game, won):

    if won:
        UpdateData(1, id=ctx.user.id, field=f"{game}.won", operator="$inc")
        UpdateData(1, name="Casino", field=f"{game}.lost", operator="$inc")

    if not won:
        UpdateData(1, id=ctx.user.id, field=f"{game}.lost", operator="$inc")
        UpdateData(1, name="Casino", field=f"{game}.won", operator="$inc")
    
def stats_collecter(ctx, game):

    PlayerData = GetData(id=ctx.user.id, field=game)
    CasinoData = GetData(name="Casino", field=game)

    stats = [PlayerData.get("won"), PlayerData.get("lost"), CasinoData.get("won"), CasinoData.get("lost")]

    return stats

#!SLASH COMMANDS
@bot.tree.command(name="balance",description="Check your account balance")
async def slash_command(interaction:discord.Interaction):

    data = GetData(id=interaction.user.id, field="balance")

    balance_embed=discord.Embed(title=f"**Account balance of {interaction.user.display_name}**", color=colors.blue)
    balance_embed.set_thumbnail(url=interaction.user.avatar)
    balance_embed.add_field(name="Balance:", value=f"${data}", inline=True)

    await interaction.response.send_message(embed=balance_embed)

@bot.tree.command(name="coinflip",description="50/50 chance to double your bet")
@app_commands.describe(bet = "How much do you want to bet?")
async def slash_command(ctx: SlashContext, bet: int):

    if not can_afford(ctx, bet):
        await ctx.response.send_message(embed=discord.Embed(title="**Coinflip**", description=f"**You cant afford this bet**", color=colors.red).set_image(url=images.CF_logo))
        return

    money_handler(ctx, bet, False)

    heads = discord.ui.Button(label="Heads", style=discord.ButtonStyle.red)
    tails = discord.ui.Button(label="Tails", style=discord.ButtonStyle.grey)
    stats = discord.ui.Button(label="Stats", style=discord.ButtonStyle.grey)

    def flip():
        return random.randint(0,1)
    
    async def heads_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return
    
        result = flip()

        if result == 0:
            await interaction.response.edit_message(embed=discord.Embed(title="**Coinflip**", description=f"It was Heads. You won and doubled your bet.\n**+{bet}$**", color=colors.green).set_image(url=images.heads_logo), view=None)
            money_handler(ctx, bet, True)
            stats_handler(ctx, "coinflip", True)
        else:
            await interaction.response.edit_message(embed=discord.Embed(title="**Coinflip**", description=f"It was Tails. You Lost your bet.\n**-{bet}$**", color=colors.red).set_image(url=images.tails_logo), view=None)
            stats_handler(ctx, "coinflip", False)

    async def tails_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return
        
        result = flip()


        if result == 1:
            await interaction.response.edit_message(embed=discord.Embed(title="**Coinflip**", description=f"It was Tails. You won and doubled your bet.\n**+{bet}$**", color=colors.green).set_image(url=images.tails_logo), view=None)
            money_handler(ctx, bet, True)
            stats_handler(ctx, "coinflip", True)
        else:
            await interaction.response.edit_message(embed=discord.Embed(title="**Coinflip**", description=f"It was Heads. You Lost your bet.", color=colors.red).set_image(url=images.heads_logo), view=None)
            stats_handler(ctx, "coinflip", False)

    async def stats_callback(interaction):
        stats = stats_collecter(ctx, "coinflip")
        await interaction.response.edit_message(embed=discord.Embed(title="**Coinflip**", description=f"Here is the stats of all the Coinflips ever done:", color=colors.blue).add_field(name="Casino:", value=f"Wins:  **{stats[2]}**\nLoses: **{stats[3]}**", inline=True).add_field(name=f"{ctx.user.display_name}:", value=f"Wins:  **{stats[0]}**\nLoses: **{stats[1]}**", inline=True).set_image(url=images.CF_logo), view=None)


    heads.callback = heads_callback
    tails.callback = tails_callback
    stats.callback = stats_callback

    view = View()
    view.add_item(heads)
    view.add_item(tails)
    view.add_item(stats)
    await ctx.response.send_message(embed=discord.Embed(title="**Coinflip**", description=f"50/50 chance to double your money. Choose what side the coin is going to land on. If your choice is correct you double your money, if it isn't you lose your money.", color=colors.blue).set_image(url=images.CF_logo), view=view)

@bot.tree.command(name="blackjack",description="Blackjack: Beat the dealer's hand without going over 21")
@app_commands.describe(bet = "How much do you want to bet?")
async def slash_command(ctx: SlashContext, bet: int):
    background = CardBackground("images/Unavngivet.jpg")
    background.clear_cards()
    background.clear_text_fields()

    deck = ['CA', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'CJ', 'CQ', 'CK', 'DA', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'DJ', 'DQ', 'DK', 'HA', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'HJ', 'HQ', 'HK', 'SA', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'SJ', 'SQ', 'SK']

    bet = bet

    PlayerHand = []
    DealerHand = []


    def DealCard(hand: list, name, insurance=False, lock=False ):
        if lock:
            card = random.choice(deck)
            hand.append(card)
            background.add_card(card, hand_type=name, lock=True)
            background.add_cards_to_background("images/output_image.jpg", scale_factor=2)
            background.add_blank()
        elif insurance:
            card = random.choice(deck)
            hand.append(card)
            background.add_card(card, hand_type=name, lock=False)
            background.add_cards_to_background("images/output_image.jpg", scale_factor=2)
            background.add_blank()
        else:
            if name == "DealerHand":
                card = random.choice(deck)
                hand.append(card)
                background.add_card(card, hand_type=name, lock=False)
                background.add_cards_to_background("images/output_image.jpg", scale_factor=2)
            else:
                card = random.choice(deck)
                hand.append(card)
                background.add_card(card, hand_type=name, lock=False)
                background.add_cards_to_background("images/output_image.jpg", scale_factor=2)
                background.add_blank()

        

    def TotalHand(hand: list):
        HandTotal = 0
        face = ['J', 'Q', 'K']
        
        for card in hand:
            if card[1:].isdigit():
                HandTotal += int(card[1:])
            elif card[1:] in face:
                HandTotal += 10
            elif card[1:] == 'A':
                if HandTotal + 11 <= 21:
                    HandTotal += 11
                else:
                    HandTotal += 1
        
        if HandTotal > 21:
            matching_values = [value for value in hand if value[-1] == "A"]
            if matching_values:
                HandTotal -= 10
        
        return HandTotal

    async def CalcWinner(interaction):

        if TotalHand(PlayerHand) > 21:
            print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
            await end.PlayerBust(interaction, bet, ctx)
        
        elif TotalHand(DealerHand) > 21:
            print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
            await end.DealerBust(interaction, bet, ctx)

        elif TotalHand(DealerHand) == TotalHand(PlayerHand):
            print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
            await end.Push(interaction, bet, ctx)

        elif 21 - TotalHand(PlayerHand) < 21 - TotalHand(DealerHand):
            print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
            await end.PlayerWin(interaction, bet, ctx)
        else:
            print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
            await end.DealerWin(interaction, bet, ctx)

    def ShowDealer():
        background.add_cards_to_background("images/output_image.jpg", scale_factor=2)

    def ShowCards():
        print(f"Player: {PlayerHand}, {TotalHand(PlayerHand)}\nDealer: {DealerHand[0]}, {DealerHand[0][1:]}")

    async def BuyInsurance(interaction, choice="n",get_lose="get"):

        global Insurance

        if get_lose == "get":

            if choice == "y":
                print("yes")
                if TotalHand(DealerHand) == 21:
                    ShowDealer()
                    await end.DealerBJ
                else:
                    print("yes2")
                    await BuyInsurance(interaction, get_lose="lose")
                    money_handler(ctx, bet // 2, False)
                    await interaction.message.edit(attachments=[discord.File("images/output_image.jpg")], view=optionsview)
            if choice == "n":
                print("no")
                if TotalHand(DealerHand) == 21:
                    ShowDealer()
                    await end.DealerBJ
                else:
                    print("no2")
                    await interaction.message.edit(attachments=[discord.File("images/output_image.jpg")], view=optionsview)
        
        if get_lose == "lose":
            print("insurance removed")

    async def AskInsurance(interaction):

        await interaction.channel.send(file=discord.File("images/output_image.jpg"), view=insuranceview)

    async def Options(interaction, bet, choose, ctx):
        if choose == "1":
            Hit(interaction, bet, ctx)
        if choose == "2":
            Stand(interaction)
        if choose == "3":
            await double(interaction, bet)

    async def Hit(interaction, bet, ctx):
        DealCard(PlayerHand, "PlayerHand")
        ShowCards()
        if TotalHand(PlayerHand) >21:
            await interaction.message.edit(attachments=[discord.File("images/output_image.jpg")], view=optionsview)
            await end.PlayerBust(interaction, bet, ctx)
        else:
            await interaction.message.edit(attachments=[discord.File("images/output_image.jpg")], view=optionsview)

    async def double(interaction, bet):
        bet += bet*2
        DealCard(PlayerHand, "PlayerHand", True)
        ShowCards()
        if TotalHand(PlayerHand) >21:
            await end.PlayerBust(interaction, bet, ctx)
        else:
            await Stand(interaction)

    async def Stand(interaction):
        await interaction.message.edit(attachments=[discord.File("images/output_image.jpg")], view=optionsview)
        while TotalHand(DealerHand) <= 16:
            DealCard(DealerHand, "DealerHand")
        await EndGame(interaction) 

    async def StartGame(interaction):

        DealCard(PlayerHand, "PlayerHand")
        DealCard(PlayerHand, "PlayerHand")
        DealCard(DealerHand, "DealerHand")
        DealCard(DealerHand, "DealerHand")
        background.add_blank()

        ShowCards()

        if TotalHand(PlayerHand) == 21:
            if TotalHand(DealerHand) != 21:
                ShowDealer()
                await interaction.message.delete()
                await interaction.channel.send(file=discord.File("images/output_image.jpg"), view=optionsview)
                await end.PlayerBJ(interaction, bet, ctx)
                return

        if TotalHand(PlayerHand) and TotalHand(DealerHand) == 42:
            ShowDealer()
            await interaction.message.delete()
            await end.Push(interaction, bet, ctx)
            return

        if DealerHand[0][1:] == "A":
            await AskInsurance(interaction)

        else:
            await interaction.message.delete()
            await interaction.channel.send(file=discord.File("images/output_image.jpg"), view=optionsview)
            return
            
    async def EndGame(interaction):
        ShowDealer()
        await interaction.message.edit(attachments=[discord.File("images/output_image.jpg")], view=optionsview)
        await CalcWinner(interaction)

    BJ_logo = "https://lh3.googleusercontent.com/u/0/drive-viewer/AKGpihbVYNTA85Qj4OWM6mgLJKDWK7_91WV0aJ3M9oriHbNCAXIEKshznOtDsTUfbEL3PW1plZWqhkOuY1p7RMRJoo_R3QjzUw=w1080-h1785-rw-v1"

    if not can_afford(ctx, bet):
        await ctx.response.send_message(embed=discord.Embed(title="**BlackJack**", description=f"**You cant afford this bet**", color=colors.red).set_image(url=BJ_logo))
        return
    
    start_button = discord.ui.Button(label="Start Game", style=discord.ButtonStyle.red)

    double_button = discord.ui.Button(label="Double", style=discord.ButtonStyle.red)
    stand_button = discord.ui.Button(label="Stand", style=discord.ButtonStyle.red)
    hit_button = discord.ui.Button(label="Hit", style=discord.ButtonStyle.red)

    yes_button = discord.ui.Button(label="Yes, i want insurance", style=discord.ButtonStyle.green)
    no_button = discord.ui.Button(label="No, i don't want insurance", style=discord.ButtonStyle.red)
    
    async def start_button_callback(interaction):

        if ctx.user.id != interaction.user.id:
            return

        await interaction.response.defer()

        await StartGame(interaction)
    
    async def Double_button_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return

        await interaction.response.defer()

        await Options(interaction, bet, "3", ctx)

    async def stand_button_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return
        
        await interaction.response.defer()

        await Stand(interaction)

    async def hit_button_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return
        
        await interaction.response.defer()

        await Hit(interaction, bet, ctx)

    async def yes_button_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return
        
        global Insurance

        await interaction.response.defer()

        Insurance = True

        await BuyInsurance(interaction, "y", "get")

    async def no_button_callback(interaction):
        if ctx.user.id != interaction.user.id:
            return
        
        global Insurance

        await interaction.response.defer()

        Insurance = False

        await BuyInsurance(interaction, "n", "get")
    

    start_button.callback = start_button_callback
    double_button.callback = Double_button_callback
    stand_button.callback = stand_button_callback
    hit_button.callback = hit_button_callback
    yes_button.callback = yes_button_callback
    no_button.callback = no_button_callback

    startview = View()
    startview.add_item(start_button)

    optionsview = View()
    optionsview.add_item(double_button)
    optionsview.add_item(stand_button)
    optionsview.add_item(hit_button)

    insuranceview = View()
    insuranceview.add_item(yes_button)
    insuranceview.add_item(no_button)


    await ctx.response.send_message(embed=discord.Embed(title="**Blackjack**", description=f"Aim to beat the dealer's hand without going over 21. If successful, you win your bet. If not, you lose your bet.\n* Game Rules:\n * Aces are 1 or 11, number cards are face value, and face cards are worth 10\n * Blackjack pays 3:2\n * Insurance Pays 2:1\n * Dealer must stand on 17 and must draw to 16", color=colors.blue).set_image(url=BJ_logo), view=startview)
    
@bot.tree.command(name="transfer",description="transfer money from your account to another users.")
@app_commands.describe(user = "Who do you want to transer money to?", amount = "How much do you want to transfer?")
async def slash_command(ctx: SlashContext, user: discord.User, amount: int):

    if amount > GetData(id=ctx.user.id, field="balance"):
        await ctx.response.send_message(embed=discord.Embed(title=f"**You dont have enough money to make this transaction**", color=colors.red))
    else:
        UpdateData(-amount, id=ctx.user.id, field="balance") #remove amount from command user
        UpdateData(amount, id=user.id, field="balance") #add amount to specified user
        await ctx.response.send_message(embed=discord.Embed(title=f"**Transaction completed**",description=f"successfully transfered **${amount}** to **{user}**", color=colors.green).set_footer(text=f"performed by {ctx.user.display_name} on {str(date.today())}", icon_url=ctx.user.avatar).set_thumbnail(url=user.avatar))

@bot.tree.command(name="beg",description="beg strangers for money.")
async def slash_command(ctx: SlashContext):

    last_time = GetData(id=ctx.user.id, field="beg")
    current_time = datetime.now()
    time_difference = current_time - last_time

    if time_difference.total_seconds() > 24 * 3600:
        amount = random.randint(1,100)
        UpdateData(amount, id=ctx.user.id, field="balance")
        UpdateData(current_time, id=ctx.user.id, field="beg", operator="$set")
        await ctx.response.send_message(embed=discord.Embed(title=f"**Nice! A stranger gave you ${amount}**", color=colors.green))

    else:
        await ctx.response.send_message(embed=discord.Embed(title=f"**You can only beg strangers for money once a day!**", color=colors.red))

#!BOT EVENTS
@bot.event
async def on_ready():
    await bot.tree.sync()

@bot.event
async def on_member_join(member):
    try:
        GetData(member.id) # trying to find the user in the database
        print("skipped")
        return
    except: # if the user doesnt exist we add them to the database
        stats = {
            "_id": member.id,
            "name": member.display_name,
            "balance": 1000,
            "roulette": {
                "won": 0,
                "lost": 0
            },
            "blackjack": {
                "won": 0,
                "lost": 0
            },
            "coinflip": {
                "won": 0,
                "lost": 0
            },
            "beg": 0
        }
        
        InsertData(stats)

bot.run(token)