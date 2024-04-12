import random

deck = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', ]

PlayerHand = []
DealerHand = []

PlayerIn = True
DealerIn = True
Insurance = None

bet = 0

class end():

    def PlayerWin():
        print("Player win")

    def DealerWin():
        print("Dealer win")

    def PlayerBust():
        print("Player Bust")

    def DealerBust():
        print("Dealer Bust")

    def Push():
        print("Push")

    def PlayerBJ():
        print("Player BlackJack")

    def DealerBJ():
        print("Dealer BlackJack")

def DealCard(hand: list, lock=False):
    if lock:
        card = random.choice(deck)
        hand.append(card)
    else:
        card = random.choice(deck)
        hand.append(card)

def TotalHand(hand: list):
    HandTotal = 0
    face = ['J', 'Q', 'K']
    
    for card in hand:
        if card.isdigit():
            HandTotal += int(card)
        elif card in face:
            HandTotal += 10
        elif card == 'A':
            if HandTotal + 11 <= 21:
                HandTotal += 11
            else:
                HandTotal += 1
    
    return HandTotal

def CalcWinner():

    if TotalHand(PlayerHand) > 21:
        print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
        end.PlayerBust()
    
    elif TotalHand(DealerHand) > 21:
        print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
        end.DealerBust()

    elif TotalHand(DealerHand) == TotalHand(PlayerHand):
        print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
        end.Push()

    elif 21 - TotalHand(PlayerHand) < 21 - TotalHand(DealerHand):
        print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
        end.PlayerWin()
    else:
        print(f"{TotalHand(PlayerHand), TotalHand(DealerHand)}")
        end.DealerWin()

def ShowDealer():
    print(f"{DealerHand}")

def ShowCards():
    print(f"Player: {PlayerHand}, {TotalHand(PlayerHand)}\nDealer: {DealerHand[0]}, {DealerHand[0]}")

def BuyInsurance(get_lose):

    global Insurance

    if get_lose == "get":
        choice = input("do you want to buy insurance")
        if choice == "y":
            Insurance = True
        if choice == "n":
            Insurance = False
    
    if get_lose == "lose":
        print("insurance removed")

def Options():
    choose = input("1. Hit 2. Stand 3. Double")
    if choose == "1":
        Hit()
    if choose == "2":
        Stand()
    if choose == "3":
        double()

def Hit():
    DealCard(PlayerHand)
    ShowCards()
    if TotalHand(PlayerHand) >21:
        end.PlayerBust()
    else:
        Options()

def double():
    bet += bet*2
    DealCard(PlayerHand, True)
    ShowCards()
    if TotalHand(PlayerHand) >21:
        end.PlayerBust()
    else:
        Options()

def Stand():
    while TotalHand(DealerHand) <= 16:
        DealCard(DealerHand)
    EndGame()
    

def StartGame():
    DealCard(PlayerHand)
    DealCard(PlayerHand)
    DealCard(DealerHand)
    DealCard(DealerHand)

    ShowCards()

    if TotalHand(PlayerHand) == 21 and TotalHand(DealerHand) != 21:
        ShowDealer()
        end.PlayerBJ()
        return

    if TotalHand(PlayerHand) and TotalHand(DealerHand) == 42:
        ShowDealer()
        end.Push()
        return

    if DealerHand[0] == "A":
        BuyInsurance("get")
        Options()
        if TotalHand(DealerHand) == 21:
            ShowDealer()
            end.DealerBJ()
            return
        else:
            if Insurance:
                BuyInsurance("lose")
            Options()
            return

    else:
        Options()
        
def EndGame():
    ShowDealer()
    CalcWinner()

StartGame()





