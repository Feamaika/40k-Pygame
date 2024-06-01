## Though it'd be cool to make a simple top-down strategy game
# Currently based on the rules of 4th edition tabletop Warhammer 40k

## Requirements for map (some notes in Dutch)
# Grid als omgeving
# afstand tot andere units op grid kunnen berekenen
# proximiteit, voor charge kunnen uitvoeren
# stats per units, of beter nog: individuele onderdelen


#To do: cover en meer special rules meenemen
#           misschien daar met bonussen op to-hit en to-wound werken i.p.v. abilities?
#           Wel abilties als re-rolls en power, rending
#       Kunnen kiezen wélke wapens je vuurt in Shooting Phase
#       Grenades in Close Combat?
#       Psychic powers??


import random, re, numpy as np
from rolldice import *  #result, explanation = rolldice.roll_dice('12d6 + 10')

class Game:
    def __init__(self):
        self.groups = []
        self.turn = 1
        self.totalturns = 0
    def start(self, *groups):
        self.groups = list(groups)
        self.totalturns = 1
        self.reset_turn()
    def current_turn(self):
        print(f"The game is now in turn {self.totalturns}.")
    def next_turn(self):
        self.turn += 1
        self.totalturns += 1
        self.reset_turn()
    def reset_turn(self):
        for group in self.groups:
            group.reset_turn()

class Vehicle:
    def __init__(self, name, BS, ArmF, ArmS, ArmR, type, WS=None, S=None, I=0, A=None, weapons=None, capacity=None, members=None):
        self.passengers = 0
        self.name = name
        self.WS = WS
        self.BS = BS
        self.S = S
        self.I = I
        self.A = A
        self.ArmF = ArmF
        self.ArmS = ArmS
        self.ArmR = ArmR
        self.capacity = capacity
        self.type = type
        self.weapons = weapons
        self.rangedweapons = []
        self.meleeweapons = []
        self.turn = 1
        self.HP = 1 #to mark a vehicle as destroyed, and maybe to adapt to rules of later editions later
        if "walker" in self.type.casefold():
            self.movement = 6
        elif "fast" in self.type.casefold():
            self.movement = 24
        else:
            self.movement = 12
        self.size = 1 #quick fix
        self.actions_done = []
        self.members = []
        if members is not None:
            self.add_passengers(members)
        if weapons:
            for w in self.weapons:
                if 'melee' in w.Type.casefold():
                    self.meleeweapons.append(w)
                else:
                    self.rangedweapons.append(w)
    
    def add_passengers(self, passengers):
        if isinstance(passengers, Troop):
            if self.passengers < self.capacity:
                self.members.append(passengers)
                self.passengers += 1
            else:
                print(f"{self.name} is full.")
        elif isinstance(passengers, Squad):
            for member in passengers.members:
                if self.passengers < self.capacity:
                    self.members.append(member)
                    self.passengers += 1
                else:
                    print(f"{self.name} is full.")
                    break
    
    def disembark_passengers(self):
        self.passengers = 0
        self.members = []
        print("All passengers have disembarked from {}".format(self.name))
        
    def remove_Troop(self, name):
        for troop in self.members:
            if troop.name == name:
                troop.W -= 1
                if troop.W <= 0:
                    self.members.remove(troop)
                    self.passengers -= 1
                    print(f"Passenger {troop.name} is removed.")
                else:
                    print(f"Passenger {troop.name} loses 1 wound.")
                return
        print(f"There is no {name} in this vehicle.")    
        
    def _check_cap(self):    #deze kan weg of aangepast
        if self.passengers < self.capacity:
            return True
        else:
            print("Vehicle is full!") #iets van break binnen for t in add_Troops(t)
            return False

    def charge_at(self, target):
        if 'charged' not in self.actions_done and self.turn > 0:
            self.actions_done.append('charged')
            self.actions_done.append('fired')
            self.melee(target)
        else:
            print(f"{self.name} cannot charge during this turn anymore.")
            
    def damage(self, target=None, weapon=None):
        weapon.Strength = min(weapon.Strength, 10)
        if target==None:
            targetT = int(input('Target Toughness?'))
        elif type(target).__name__ == 'Monster':
            targetT = target.T
        else:
            targetT = max([troop.T for troop in target.members], key=[troop.T for troop in target.members].count)
        td = random.randint(1, 6)
        if td == 1:
            print(f"{self.name} fails to wound target. (■{td})") #return False 
        elif td >= (4+targetT-weapon.Strength):
            print(f"{self.name} wounds the target with the {weapon.Name}! (■{td})")
            self.wounding_hits += 1
        elif (td == 6) and (targetT-weapon.Strength==3):
            print(f"{self.name} manages to wound the target! (■{td})")
            self.wounding_hits += 1
        else:
            if 'living am' in weapon.Special.casefold(): #n/a, maar misschien voor andere soort later
                re_roll = roll_dice('d6')[0]
                if re_roll >= (4+targetT-weapon.Strength):
                    print(f"The {self.weapon}'s ammunition burrows deep, wounding the target! (■{re_roll})")
                    self.wounding_hits += 1
                elif (re_roll == 6) and (targetT-weapon.Strength==3):
                    print(f"The {self.weapon}'s ammunition burrows deep and wounds the target! (■{re_roll})")
                    self.wounding_hits += 1
                    #self.weaponAP = weapon.AP
            else:
                print(f"{self.name} fails to wound target with the {weapon.Name}.")  #return False
    
    def damage_vehicle(self, target=None, weapon=None):
        if 'lance' in weapon.Special.casefold():
            AV = 12
        else:
            sidehit = int(input('Which side was hit? (Front=1, Sides=2, Rear=3)'))
            if sidehit==1:
                AV = target.ArmF
            elif sidehit==2:
                AV = target.ArmS
            elif sidehit==3:
                AV = target.ArmR
            else:
                print("No valid selection")
        td = roll_dice('2d6')[0] if 'melta' in weapon.Special.casefold() else roll_dice('d6')[0] #if under half range, technically
        if td+weapon.Strength==AV:
            if weapon.AP==1:
                self.pen_hits += 1
            else:
                self.glancing_hits += 1
            print(f"A glancing hit on {target.name}!")
        elif td+weapon.Strength>AV:
            if 'ordnance' in weapon.Type.casefold():
                self.ord_hits += 1
            else:
                self.pen_hits += 1
            print(f'A penetrating hit on {target.name}!')
        else:
            print('The shot bounces off the vehicle\'s armour...')
    
    def glancing_hit(self, weapon=None):
        r = roll_dice('d6')[0]
        if r < 3:
            print(f'The {self.name}\'s crew is shaken.')
            self.actions_done.append('fired')
        elif r == 3:
            print(f'The crew from the {self.name} is stunned.')
            self.actions_done.append('moved')
            self.actions_done.append('fired')
        elif r == 4:
            if len(self.weapons)>0:
                x = random.randint(1, len(self.weapons))-1
                lost_arm = self.weapons[x].Name
                print(f'The {self.name}\'s {lost_arm} is destroyed by the attack.')
                self.weapons.pop(x) #removing the destroyed armament
            else:
                r = 5
        if r == 5:
            if self.movement == 0:
                r == 6
            else:
                print(f'{self.name} is immobilised by the attack.')
                self.movement = 0
        if r == 6:
            print(f'The {self.name} is taken out of action.')
            self.HP = self.size = 0

    def penetrating_hit(self, weapon=None):
        r = roll_dice('d6')[0]
        print_result = ""
        if r <= 3:
            print_result = f'The crew from the {self.name} is stunned. '
            if self.members is not None:
                print_result = print_result + 'The vehicle\'s passengers rush to get out! '
                if 'moved' in self.actions_done:
                    for m in range(self.passengers):
                        mp = roll_dice('d6')[0]
                        if mp >= 4:
                            self.members[m].is_wounded(unit=self)
            self.actions_done.append('moved')
            self.actions_done.append('fired')
        if r == 2:
            if len(self.weapons)>0:
                x = random.randint(1, len(self.weapons))-1
                lost_arm = self.weapons[x].Name
                print_result = print_result + f'The {lost_arm} is destroyed by the attack. '
                self.weapons.pop(x) 
            else:
                r = 3
        if r == 3:
            if self.movement == 0:
                r == 4
            else:
                print(f'{self.name} is immobilised by the attack. ')
                self.movement = 0
        if r >= 4:
            print_result = print_result + f'{self.name} is taken out of action!'
            self.HP = self.size = 0
        if r == 6:
            print_result = print_result + f'An explosion scatters flaming debris {random.randint(1, 6)}" in every direction.'
            #models in range suffer a wound (saving throws allowed) on a 4+
        print(print_result)
            
    def ordnance_hit(self, weapon=None):
        print_result = ""
        if r <= 3:
            print_result = f'The crew from the {self.name} is stunned. '
            if self.members is not None:
                print_result = print_result + 'The vehicle\'s passengers rush to get out! '
                if 'moved' in self.actions_done:
                    for m in range(self.passengers):
                        mp = roll_dice('d6')[0]
                        if mp >= 4:
                            self.members[m].is_wounded(unit=self)
            self.actions_done.append('moved')
            self.actions_done.append('fired')
        if r == 2:
            if len(self.weapons)>0:
                x = random.randint(1, len(self.weapons))-1
                lost_arm = self.weapons[x].Name
                print_result = print_result + f'The {lost_arm} is destroyed by the attack. '
                self.weapons.pop(x) 
            else:
                r = 3
        if r == 3:
            if self.movement == 0:
                r == 4
            else:
                print(f'{self.name} is immobilised by the attack. ')
                self.movement = 0
        if r >= 4:
            print_result = print_result + f'{self.name} is taken out of action!'
            self.HP = self.size = 0
        if r == 5:
            print_result = print_result + f'An explosion scatters flaming debris {random.randint(1, 6)}" in every direction.'
        elif r == 6:
            print_result = print_result + f'An explosion scatters flaming debris 6" in every direction and kills any passengers.'
            #non-passenger models in range suffer a wound (saving throws allowed) on a 4+
        print(print_result)
    
    def fire(self, target, weapon=None):
        th = roll_dice('d6')[0]
        if th >= (7-self.BS):
            if 'large blast' in weapon.Special.casefold():
                lb = min(target.size, roll_dice('d5+2')[0])
                print(f"The large blast hits %i enemy troops!" % (lb))
                for _ in range(lb):
                    if type(target).__name__ == 'Vehicle':
                        self.damage_vehicle(target=target, weapon=weapon)
                    else:
                        self.damage(target=target, weapon=weapon)
            elif 'blast' in weapon.Special.casefold():
                nb = min(target.size, roll_dice('d4+1')[0])
                print(f"The blast hits %i enemy troops!" % (nb))
                for _ in range(nb):
                    if type(target).__name__ == 'Vehicle':
                        self.damage_vehicle(target=target, weapon=weapon)
                    else:
                        self.damage(target=target, weapon=weapon)
            else:
                print(f"They fire and hit! (■%i)" % (th))
                if type(target).__name__ == 'Vehicle':
                    self.damage_vehicle(target=target, weapon=weapon)
                else:
                    self.damage(target=target, weapon=weapon)
        else:
            if 'twin' in weapon.Special.casefold():     #of roll_dice('2d6K1')[0]
                re_roll = random.randint(1, 6)
                if re_roll >= (7-self.BS):
                    print(f"%s\'s spray of bullets (%s) hits! (■%i)" % (self.name, weapon.Name, re_roll))
                    if type(target).__name__ == 'Vehicle':
                        self.damage_vehicle(target=target, weapon=weapon)
                    else:
                        self.damage(target=target, weapon=weapon)
            else:
                print(f"They fire but miss. (■%i)" % (th))
    
    def fire_at(self, target):
        if self.type=="Open-topped":
            self.passBS = max([troop.BS for troop in self.members], key=[troop.BS for troop in self.members].count)
        if self.rangedweapons != []:    
            if 'fired' not in self.actions_done and self.turn > 0:
                self.actions_done.append('fired')
                target_size_before = target.size if type(target).__name__ == 'Squad' else 1
                for w in self.rangedweapons:
                    self.wounding_hits = self.glancing_hits = self.pen_hits = self.ord_hits = 0
                    shots = w.TypeNum
                    print(f"%s aims the %s at the %s..." % (self.name, w.Name, target.name))
                    for s in range(0, shots):
                        if target.size > 0:
                            self.fire(target, weapon=w) 
                        else:
                            print("Target unit is already wiped out.")
                        
                    if self.wounding_hits > 0:
                        for s in range(0, self.wounding_hits):
                            if target.size > 0:
                                target.saving_throw(weaponAP=w.AP, weaponS=w.Strength)
                            else:
                                print("The target is already dead.")
                            
                    if self.glancing_hits > 0:
                        for s in range(0, self.glancing_hits):
                            target.glancing_hit(weapon=w)
                    if self.pen_hits > 0:
                        for s in range(0, self.pen_hits):
                            target.penetrating_hit(weapon=w)
                    if self.ord_hits > 0:
                        for s in range(0, self.ord_hits):
                            target.ordnance_hit(weapon=w)
                    
                target_size_after = target.size if type(target).__name__ == 'Squad' else 1
                if type(target).__name__ == 'Squad' and target.size > 0:
                    print("Troops left in the unit:",target_size_after)
                    if (target_size_before * 0.25) <= (target_size_before-target_size_after):
                        print(f"\nBecause of the amount of shooting casualties, the {target.name} takes a morale test.")
                        target.morale_test(mod = -1 if (target.size/target.initsize)<=.5 else 0)
            else:
                print(f"{self.name} cannot fire anymore this turn.")
        else:
            print(f"{self.name} is not able to shoot.")
            
    def melee(self, target=None):
        if 'walker' in self.type.casefold():
            self.actions_done.append('fought')
            self.wounding_hits = self.glancing_hits = self.pen_hits = 0
            w = self.meleeweapons[0]
            if target==None:
                targetWS = int(input('Target Weapon Skill?'))
            else:   #uitgaande van gevecht tegen Squads, net als bij Monsters (nog aanvullen)
                targetWS = min([troop.WS for troop in target.members], key=[troop.WS for troop in target.members].count)
            if self.WS - targetWS > 0:
                mod = -1
            elif self.WS / targetWS < 0.5:
                mod = 1
            else:
                mod = 0
            attacks = self.A+1 if 'charged' in self.actions_done else self.A
            for a in range(attacks):    
                th = roll_dice('d6')[0]
                if th >= (4+mod):
                    print(f"%s manages to hit %s! (■%i)" % (self.name, target.name, th))
                    if type(target).__name__ == 'Vehicle':
                        self.damage_vehicle(target=target, weapon=w) #één melee wapen voor een walker?
                    else:
                        self.damage(target=target, weapon=w)
                    #self.damage(target=target, weaponS=self.S, weaponAP=self.weaponAP)
                else:
                    print(f"%s fails to hit the target. (■%i)" % (self.name, th))
                    
            if self.wounding_hits > 0:
                for h in range(0, self.wounding_hits):
                    target.saving_throw(weaponAP=w.AP, weaponS=w.Strength)
            if self.glancing_hits > 0:
                for h in range(0, self.glancing_hits):
                    target.glancing_hit()
            if self.pen_hits > 0:
                for h in range(0, self.pen_hits):
                    target.penetrating_hit()
            
        else:
            print(f"{self.name} cannot fight in close combat.")
            pass
      
    def move(self):
        #move = 6; shoot = 0
        if 'moved' not in self.actions_done and self.turn > 0:
            self.actions_done.append('moved')
            #print(f"{self.name} moves across the battlefield...")
            extra = '' #if shoot==0 else ',\n and an additional %i" in the Shooting Phase if they don\'t fire this turn. ' % (shoot)
            print(f'{self.name} can move {self.movement}" in the Movement Phase this turn{extra}... ')
        else:
            print(f"{self.name} cannot move during this turn anymore.")
        
    def reset_turn(self):
        self.actions_done = []
        self.turn = 1

class Monster:
    def __init__(self, name, WS, BS, S, T, W, I, A, Ld, Sv, weapons):
        self.size = 1
        self.name = name
        self.WS = WS
        self.BS = BS
        self.S = S
        self.T = T
        self.W = W
        self.I = I
        self.A = A
        self.Ld = Ld
        self.Sv = Sv
        self.turn = 1
        self.size = 1 #quick fix
        self.actions_done = [] 
        self.weapons = weapons
        self.rangedweapons = []
        self.meleeweapons = []
        self.rerolltohit = 0
        self.rerolltowound = 0
        if weapons:
            for w in self.weapons:
                if 'melee' in w.Type.casefold():
                    self.meleeweapons.append(w)
                else:
                    self.rangedweapons.append(w)

    def damage(self, target=None, weapon=None):
        if target==None:
            targetT = int(input('Target Toughness?'))
        else:
            targetT = max([troop.T for troop in target.members], key=[troop.T for troop in target.members].count)
        td = random.randint(1, 6)
        if td == 1:
            print(f"{self.name} fails to wound target. (■{td})") #return False 
        elif td >= (4+targetT-weapon.Strength):
            print(f"{self.name} wounds the target with the {weapon.Name}! (■{td})")
            self.wounding_hits += 1
            #self.weaponAP = weapon.AP  # Pass the weapon's AP to the unit (Squad object)
        elif (td == 6) and (targetT-weapon.Strength==3):
            print(f"{self.name} manages to wound the target! (■{td})")
            self.wounding_hits += 1
            #self.weaponAP = weapon.AP
        else:
            if 'living am' in weapon.Special.casefold(): #n/a, maar misschien voor andere soort later
                re_roll = roll_dice('d6')[0]
                if re_roll >= (4+targetT-weapon.Strength):
                    print(f"The {self.weapon}'s ammunition burrows deep, wounding the target! (■{re_roll})")
                    self.wounding_hits += 1
                elif (re_roll == 6) and (targetT-weapon.Strength==3):
                    print(f"The {self.weapon}'s ammunition burrows deep and wounds the target! (■{re_roll})")
                    self.wounding_hits += 1
                    #self.weaponAP = weapon.AP
            else:
                print(f"{self.name} fails to wound target with the {weapon.Name}.")  #return False
    
    def damage_vehicle(self, target=None, weapon=None):
        if 'lance' in weapon.Special.casefold():
            AV = 12
        else:
            sidehit = int(input('Which side was hit? (Front=1, Sides=2, Rear=3)'))
            if sidehit==1:
                AV = target.ArmF
            elif sidehit==2:
                AV = target.ArmS
            elif sidehit==3:
                AV = target.ArmR
            else:
                print("No valid selection")
        if 'melta' in weapon.Special.casefold() or 'sniper' in weapon.Special.casefold():
            td = roll_dice('2d6')[0] 
        else:
            td = roll_dice('d6')[0]
        if 'rending' in weapon.Special.casefold() and td==6:
            print('The rending attacks rips apart the vehicle\'s armour!')
            td += roll_dice('d6')[0]
        if (td+weapon.Strength)>AV:
            if 'ordnance' in weapon.Special.casefold():
                self.ord_hits += 1
            else:
                self.pen_hits += 1
            print(f'A penetrating hit on {target.name}!')
        elif (td+weapon.Strength)==AV or ('gauss' in weapon.Special.casefold() and roll_dice('d6')[0]==6):
            if weapon.AP==1:
                self.pen_hits += 1
            else:
                self.glancing_hits += 1
            print(f"A glancing hit on {target.name}!")
        else:
            print('The hit bounces off the vehicle\'s armour...')
    
    def fire(self, target, weapon=None):
        th = roll_dice('d6')[0]
        if th >= (7-self.BS):
            if type(target).__name__ == 'Squad':
                if 'large blast' in weapon.Special.casefold():
                    lb = min(target.size, roll_dice('d5+2')[0])
                    print(f"The large blast hits %i enemy troops!" % (lb))
                    for _ in range(lb):
                        self.damage(target=target, weapon=weapon)
                elif 'blast' in weapon.Special.casefold():
                    nb = min(target.size, roll_dice('d4+1')[0])
                    print(f"The blast hits %i enemy troops!" % (nb))
                    for _ in range(nb):
                        self.damage(target=target, weapon=weapon)
            else:
                print(f"They fire and hit! (■%i)" % (th))
                if type(target).__name__ == 'Vehicle':
                    self.damage_vehicle(target=target, weapon=weapon)
                else:
                    self.damage(target=target, weapon=weapon)
        else:
            if 'twin' in weapon.Special.casefold():     #of roll_dice('2d6K1')[0]
                re_roll = random.randint(1, 6)
                if re_roll >= (7-self.BS):
                    print(f"%s\'s spray of shots hits the target! (■%i)" % (self.name, re_roll))
                    if type(target).__name__ == 'Vehicle':
                        self.damage_vehicle(target=target, weapon=weapon)
                    else:
                        self.damage(target=target, weapon=weapon)
            else:
                print(f"They fire but miss. (■%i)" % (th))
    
    def fire_at(self, target):
        if self.rangedweapons == []:
            print(f"{self.name} is not able to shoot.")
        else: 
            if 'fired' not in self.actions_done and self.turn > 0:
                self.actions_done.append('fired')
                target_size_before = target.size if type(target).__name__ == 'Squad' else 1
                for w in self.rangedweapons:
                    self.wounding_hits = self.glancing_hits = self.pen_hits = self.ord_hits = 0        
                    shots = w.TypeNum
                    print(f"%s aims the %s at the %s..." % (self.name, w.Name, target.name))
                    for s in range(0, shots):
                        if type(target).__name__ == 'Squad' and target.size == 0:
                            print("Target unit has been destroyed.")
                        else:
                            self.fire(target, weapon=w)
                            
                    if self.wounding_hits > 0:
                        for s in range(0, self.wounding_hits):
                            if type(target).__name__ == 'Squad' and target.size == 0:
                                print("Target unit has been completely destroyed.")
                            else:
                                target.saving_throw(weaponAP=w.AP, weaponS=w.Strength)
                    if self.glancing_hits > 0:
                        for s in range(0, self.glancing_hits):
                            target.glancing_hit()
                    if self.pen_hits > 0:
                        for s in range(0, self.pen_hits):
                            target.penetrating_hit()
                    if self.ord_hits > 0:
                        for s in range(0, self.ord_hits):
                            target.ordnance_hit()
                    
                target_size_after = target.size if type(target).__name__ == 'Squad' else 1
                if type(target).__name__ == 'Squad' and target.size > 0:
                    print("Troops left in the unit:",target_size_after)
                    if (target_size_before * 0.25) <= (target_size_before-target_size_after):
                        print(f"\nBecause of the amount of shooting casualties, the {target.name} takes a morale test.")
                        target.morale_test(mod = -1 if (target.size/target.initsize)<=.5 else 0)
            else:
                print(f"{self.name} cannot fire anymore this turn.")
    
    def is_wounded(self, instant=False):
        if instant:
            self.W -= 9    #kan ook op 0 zetten maar dit is leuker
            print(f"{self.name} is killed instantly by the attack!")
        else:
            self.W -= 1
        if self.W <= 0:
            #self.size -= 1
            print(f"{self.name} is killed by the attack.")
        else:
            print(f"{self.name} loses 1 wound.")
        return
    
    def melee(self, target=None):
        if 'fought' not in self.actions_done and self.turn > 0:
            self.actions_done.append('fought')
            self.wounding_hits = self.glancing_hits = self.pen_hits = 0
            target.I = np.mean([troop.I for troop in self.members]) if type(target).__name__ == 'Squad' else target.I
            if self.I > target.I:
                    print(f'{self.name} gets to strike first.')
            elif self.I < target.I:
                print(f'{target.name} gets to strike first.')
            elif self.I == target.I:
                print(f'{self.name} and {target.name} strike at the same time.')
            
            if self.meleeweapons == []:
                weapon = Weapon('melee weapon', 0, self.S, 0, 'Melee')   #ignoring armour saves for Monstrous Creatures
            else:
                weapon = self.meleeweapons[0] #always use first melee weapon?? Attacks per troop, voor gemak geen onderscheid in wapens
            if 'poisoned' in weapon.Special.casefold():
                pass
            
            if target==None:
                targetWS = int(input('Target Weapon Skill?'))
            elif type(target).__name__ == 'Squad':
                targetWS = min([troop.WS for troop in target.members], key=[troop.WS for troop in target.members].count)
            elif type(target).__name__ == 'Monster' or (type(target).__name__ == 'Vehicle' and "Walker" in target.type.casefold()):
                targetWS = target.WS
            else:
                targetWS = None
            
            mod = 0
            if targetWS != None: 
                if self.WS - targetWS > 0:
                    mod = -1
                elif self.WS / targetWS < 0.5:
                    mod = 1
            
            attacks = self.A+1 if 'charged' in self.actions_done else self.A
            for _ in range(0, attacks):
                th = roll_dice('d6')[0]
                if type(target).__name__ == 'Vehicle':
                    if th >= 4 if 'moved' in target.actions_done else 1:
                        self.damage_vehicle(target=target, weapon=weapon)
                else:
                    if 'rending' in weapon.Special.casefold() and th==6:
                        target.saving_throw(weaponAP=weapon.AP, weaponS=weapon.Strength)
                    elif th >= (4+mod):
                        print(f"%s manages to hit %s! (■%i)" % (self.name, target.name, th))
                        self.damage(target=target, weapon=weapon)
                    else:
                        print(f"%s\'s attack fails to hit the target. (■%i)" % (self.name, th))
            
            if self.wounding_hits > 0:
                for h in range(0, self.wounding_hits):
                    target.saving_throw(weaponAP=weapon.AP, weaponS=weapon.Strength)
            if self.glancing_hits > 0:
                for h in range(0, self.glancing_hits):
                    target.glancing_hit()
            if self.pen_hits > 0:
                for h in range(0, self.pen_hits):
                    target.penetrating_hit()
        else:
            print(f"{self.name} cannot fight anymore this turn.")
       
    def move(self):
        move = 6; shoot = 0
        if 'fleet' in self.special.casefold():
            shoot = roll_dice('d6')[0]
        if 'jump' in self.special.casefold():
            move += 6
        if 'moved' not in self.actions_done and self.turn > 0:
            self.actions_done.append('moved')
            #print(f"{self.name} moves across the battlefield...")
            extra = '' if shoot==0 else ',\n and an additional %i" in the Shooting Phase if they don\'t fire this turn. ' % (shoot)
            print(f'{self.name} can move {move}" in the Movement Phase this turn{extra}... ')
        else:
            print(f"{self.name} cannot move during this turn anymore.") 
             
    def reset_turn(self):
        self.actions_done = []
        self.turn = 1
        
    def saving_throw(self, weaponAP=None, weaponS=None):
        if '/' in self.Sv:
            print(f"{self.name} has multiple save options: {self.Sv}")
            choice = input("Which save do you want to use? (Enter 'A' for armor save, 'I' for invulnerable save): ")
            while choice.upper() not in ['A', 'I']:
                choice = input("Invalid choice. Enter 'A' for armor save, 'I' for invulnerable save: ")
            if choice.upper() == 'A':
                troop_save = int(self.Sv.split('/')[0][0]) if self.Sv.split('/')[0][0]!='-' else 99
            elif choice.upper() == 'I':
                troop_save = int(self.Sv.split('/')[1][0])
            else:
                pass
        else:
            troop_save = int(self.Sv[0])
            choice = 'A'
        
        if weaponS>=(2*self.T):
            instantdeath = True
        else:
            instantdeath = False

        if weaponAP is not None and weaponAP <= troop_save and choice.upper()=='A':
            print('\nNo saving throws due to weapon\'s armour penetration...')
            self.is_wounded(instant=instantdeath)
        elif (weaponAP is not None and choice.upper()=='A') or choice.upper()=='I':
            tw = random.randint(1, 6)
            if tw < int(troop_save):
                print(f"Saving throw failed. (■%i)" % (tw))
                self.is_wounded(instant=instantdeath)
            else:
                print(f"Monster passes its saving throw! (■%i)" % (tw))
        else:
            print('Missing weaponAP')
    
class Squad:
    def __init__(self, name, members=None, special=''):
        self.size = 0
        self.name = name
        self.members = []
        self.special = special
        self.turn = 1
        self.actions_done = []
        if members:
            self.add_Troops(members)
            self.initsize = len(self.members)
    def add_Troop(self, troop):
        self.members.append(troop)
        self.size = len(self.members)
    def add_Troops(self, troop):
        self.members.extend(troop) #instead of append
        self.size = len(self.members)
    def remove_Troop(self, name, instant=False):
        for troop in self.members:
            if troop.name == name:
                if instant:
                    troop.W -= 9    #kan ook op 0 zetten maar dit is leuker
                    print(f"{troop.name} is killed instantly by the attack!")
                else:
                    troop.W -= 1
                if troop.W <= 0:
                    self.members.remove(troop)
                    self.size -= 1
                    print(f"Removed {troop.name} from the unit.")
                else:
                    print(f"{troop.name} loses 1 wound.")
                return
        print(f"There is no {name} in this unit.")
        
    def all_fire(self):
        for t in self.members:
            t.fire()
    def composition(self):
        print("This",self.name,"is composed of:")
        #print(", ".join([troop.name for troop in self.members]))
        names_count = {}
        for troop in self.members:
            if troop.name in names_count:
                names_count[troop.name] += 1
            else:
                names_count[troop.name] = 1
        names = []
        for name, count in names_count.items():
            if count > 1:
                names.append(f"{name} {count}x")
            else:
                names.append(name)
        print(", ".join(names))
        
    def charge_at(self, target):
        assaultrange = 6
        if 'artiller' in self.special.casefold():
            assaultrange = 0
        if 'beast' in self.special.casefold() or 'cavalr' in self.special.casefold():
            assaultrange += 6
        if 'charged' not in self.actions_done and self.turn > 0:
            self.actions_done.append('charged')
            self.actions_done.append('fired')
            print(f'{self.name} can assault {assaultrange}" this Assault Phase.')
            in_assault_range = input('Is the target unit in range to assault?')
            if in_assault_range:
                self.melee(target)
        else:
            print(f"{self.name} cannot charge during this turn anymore.")
            
    def fire_at(self, target):
        self.BS = max([troop.BS for troop in self.members], key=[troop.BS for troop in self.members].count)
        #if max([troop.weaponshots for troop in self.members], key=[troop.weaponshots for troop in self.members].count) > 0:
        if any([] != troop.rangedweapons for troop in self.members):
            if 'fired' not in self.actions_done and self.turn > 0:
                self.actions_done.append('fired')
                print(f"%s takes aim at the %s..." % (self.name,target.name))
                target_size_before = target.size if type(target).__name__ == 'Squad' else 1
                #print("Target size:",target_size_before)
                for troop in self.members:
                    self.wounding_hits = self.glancing_hits = self.pen_hits = self.ord_hits = 0
                    if troop.rangedweapons != []:    
                        for w in troop.rangedweapons:
                            shots = w.TypeNum
                            #print(f"%s aims the %s at the %s..." % (self.name, w.Name, target.name))
                            for s in range(0, shots):
                                if target.size > 0:
                                    troop.fire_at(target, self, weapon=w) #self.members[s].fire_at(target, self)
                                else:
                                    print("Target unit completely destroyed.")
                                
                            if self.wounding_hits > 0:
                                for s in range(0, self.wounding_hits):
                                    if target.size > 0:
                                        target.saving_throw(weaponAP=w.AP, weaponS=w.Strength)
                                    else:
                                        print("Target unit has been destroyed.")
                            if self.glancing_hits > 0:
                                for s in range(0, self.glancing_hits):
                                    target.glancing_hit()
                            if self.pen_hits > 0:
                                for s in range(0, self.pen_hits):
                                    target.penetrating_hit()
                            if self.ord_hits > 0:
                                for s in range(0, self.ord_hits):
                                    target.ordnance_hit()
                                    
                target_size_after = target.size if type(target).__name__ == 'Squad' else 1
                if type(target).__name__ == 'Squad' and target.size > 0:
                    print("Troops left in the unit:",target_size_after)
                    if (target_size_before * 0.25) <= (target_size_before-target_size_after):
                        print(f"\nBecause of the amount of shooting casualties, the {target.name} takes a morale test.")
                        target.morale_test(mod = -1 if (target.size/target.initsize)<=.5 else 0)
            else:
                print(f"{self.name} cannot fire anymore this turn.")
        else:
            print(f"{self.name} is not able to shoot.")

    def Ld_test(self, mod=0):
        self.Ld = max([troop.Ld for troop in self.members], key=[troop.Ld for troop in self.members].count)
        test = roll_dice('2d6')[0]
        if test == 2:
            print(f"{self.name} displays insane heroism!")
            return True
        elif test <= (self.Ld + mod):
            print(f"{self.name} passes the Leadership test. (■{test})")
            return True
        else:
            print(f"{self.name} fails the Leadership test. (■{test})")
            return False

    def melee(self, target):
        if 'fought' not in self.actions_done and self.turn > 0:
                self.actions_done.append('fought')
                self.wounding_hits = self.glancing_hits = self.pen_hits = 0
                print(f"%s is in close combat with %s..." % (self.name, target.name))
                self.I = np.mean([troop.I for troop in self.members]) #N.B. pas hierna wordt gecheckt op de wapens van troepen en evt. aanpassing van I
                target.I = np.mean([troop.I for troop in self.members]) if type(target).__name__ == 'Squad' else target.I
                if self.I > target.I:
                    print(f'{self.name} gets to strike first.')
                elif self.I < target.I:
                    print(f'{target.name} gets to strike first.')
                elif self.I == target.I:
                    print(f'{self.name} and {target.name} strike at the same time.')
                for troop in self.members:
                    attacks = troop.A+1 if 'charged' in self.actions_done else troop.A
                    for a in range(0, attacks):
                        troop.melee(target, self) 
                        
                    if self.wounding_hits > 0:
                        for h in range(0, self.wounding_hits):
                            target.saving_throw(weaponAP=self.weaponAP, weaponS=self.weaponS)
                    if self.glancing_hits > 0:
                        for h in range(0, self.glancing_hits):
                            target.glancing_hit()
                    if self.pen_hits > 0:
                        for h in range(0, self.pen_hits):
                            target.penetrating_hit()
        else:
            print(f"{self.name} cannot fight anymore this turn.")
    
    def morale_test(self, mod=0):
        self.Ld_test(mod=mod)
    
    def move(self):
        move = 6; shoot = 0
        if 'fleet' in self.special.casefold() or 'beast' in self.special.casefold() or 'cavalr' in self.special.casefold():
            shoot = roll_dice('d6')[0]
        if 'jump' in self.special.casefold() or 'bike' in self.special.casefold():
            move += 6
        if 'moved' not in self.actions_done and self.turn > 0:
            self.actions_done.append('moved')
            #print(f"{self.name} moves across the battlefield...")
            extra = '' if shoot==0 else ',\n and an additional %i" in the Shooting Phase if they don\'t fire this turn. ' % (shoot)
            print(f'{self.name} can move {move}" in the Movement Phase this turn{extra}... ')
        else:
            print(f"{self.name} cannot move during this turn anymore.")    

    def reset_turn(self):
        self.actions_done = []
        self.turn = 1
    
    def saving_throw(self, weaponAP=None, weaponS=None):
        print('\nSelecting target...')
        print("(",", ".join([troop.name for troop in self.members]),")")
        wounded = input("Who is wounded? (Enter name or number)") 
        if wounded.isdigit():
            wounded_index = int(wounded) - 1
            if wounded_index >= 0 and wounded_index < len(self.members):
                wounded = self.members[wounded_index]
            else:
                print("Invalid selection.")
                return
        else:
            wounded = next((troop for troop in self.members if troop.name == wounded), None) #leer wat Next doet
            if wounded is None:
                print(f"There is no {wounded} in this unit.")
                return

        if '/' in wounded.Sv:
            print(f"{wounded.name} has multiple save options: {wounded.Sv}")
            choice = input("Which save do you want to use? (Enter 'A' for armor save, 'I' for invulnerable save): ")
            while choice.upper() not in ['A', 'I']:
                choice = input("Invalid choice. Enter 'A' for armor save, 'I' for invulnerable save: ")
            if choice.upper() == 'A':
                troop_save = int(wounded.Sv.split('/')[0][0]) if wounded.Sv.split('/')[0][0]!='-' else 99
            elif choice.upper() == 'I':
                troop_save = int(wounded.Sv.split('/')[1][0])
            else:
                pass
        else:
            troop_save = int(wounded.Sv[0])
            choice = 'A'
        
        if weaponS>=(2*wounded.T):
            instantdeath = True
        else:
            instantdeath = False

        if weaponAP is not None and weaponAP <= troop_save and choice.upper()=='A':
            print('\nNo saving throws due to weapon\'s armour penetration...')
            self.remove_Troop(wounded.name, instant=instantdeath)
        elif (weaponAP is not None and choice.upper()=='A') or choice.upper()=='I':
            tw = random.randint(1, 6)
            if tw < int(troop_save):
                print(f"Saving throw failed. (■%i)" % (tw))
                self.remove_Troop(wounded.name, instant=instantdeath)
            else:
                print(f"Unit passes its saving throw! (■%i)" % (tw))
        else:
            print('Missing weaponAP')
 
class Troop:
    def __init__(self, name, WS, BS, S, T, W, I, A, Ld, Sv, weapons):
        self.name = name
        self.WS = WS
        self.BS = BS
        self.S = S
        self.T = T
        self.W = W
        self.I = I
        self.A = A
        self.Ld = Ld
        self.Sv = Sv
        self.weapons = weapons
        self.rangedweapons = []
        self.meleeweapons = []
        self.rerolltohit = 0
        self.rerolltowound = 0
        if weapons:
            for w in self.weapons:
                if 'melee' in w.Type.casefold():
                    self.meleeweapons.append(w)
                    if bool(re.search('power fist', w.Name)) or bool(re.search('power claw', w.Name)) or bool(re.search('power klaw', w.Name)):
                        self.S *= 2
                        self.I = 1
                    if bool(re.search('lightning claw', w.Name)):
                        self.S *= 2
                        self.rerolltowound += 1
                else:
                    self.rangedweapons.append(w)
        # if type(weapon) is str:
        #     self.weapon = weapon
        #     if bool(re.search('pow', weapon)) or bool(re.search('relic', weapon)) or bool(re.search('force', weapon)):
        #         self.weaponAP = 1
        #     else:
        #         self.weaponAP = 7
        #     if bool(re.search('fist', weapon)) or bool(re.search('law', weapon)):
        #         self.S *= 2
        #     self.weaponshots = 0
        #     self.weaponspecial = ""
        # else:    
        #     self.weapon = weapon.Name
        #     self.weaponrange = weapon.Range
        #     self.weaponS = weapon.Strength
        #     self.weaponAP = weapon.AP
        #     self.weapontype = weapon.Type
        #     self.weaponshots = weapon.TypeNum
        #     self.weaponspecial = weapon.Special
            
    def damage(self, target=None, unit=None, weapon=None):
        weapon.Strength = min(weapon.Strength, 10)
        if target==None:
            targetT = int(input('Target Toughness?'))
        elif type(target).__name__ == 'Monster':
            targetT = target.T
        else:
            targetT = max([troop.T for troop in target.members], key=[troop.T for troop in target.members].count)
        td = random.randint(1, 6)
        if 'sniper' in weapon.Special.casefold() and td>=4:
            print(f"{self.name} wounds the target.")
        elif td == 1:
            print(f"{self.name} fails to wound target. (■{td})") #return False 
        elif td >= (4+targetT-weapon.Strength):
            print(f"{self.name} wounds the target! (■{td})")
            if unit != None:
                unit.wounding_hits += 1
                unit.weaponAP = weapon.AP  # Pass the weapon's AP to the unit (Squad object)
                unit.weaponS = weapon.Strength
        elif (td == 6) and (targetT-weapon.Strength==3):
            print(f"{self.name} manages to wound the target! (■{td})")
            if unit != None:
                unit.wounding_hits += 1
                unit.weaponAP = weapon.AP
                unit.weaponS = weapon.Strength
        else:
            if 'living am' in weapon.Special.casefold():
                re_roll = roll_dice('d6')[0]
                if re_roll >= (4+targetT-weapon.Strength):
                    print(f"The {weapon.Name}'s ammunition burrows deep, wounding the target! (■{re_roll})")
                    if unit != None:
                        unit.wounding_hits += 1
                        unit.weaponAP = weapon.AP
                        unit.weaponS = weapon.Strength
                elif (re_roll == 6) and (targetT-weapon.Strength==3):
                    print(f"The {weapon.Name}'s ammunition burrows deep and wounds the target! (■{re_roll})")
                    if unit != None:
                        unit.wounding_hits += 1
                        unit.weaponAP = weapon.AP
                        unit.weaponS = weapon.Strength
            else:
                print(f"{self.name} fails to wound target. (■{td})")  #return False
    
    def damage_vehicle(self, target=None, unit=None, weaponS=None, weaponAP=None, weaponspecial=None):
        if 'lance' in weaponspecial.casefold():
            AV = 12
        else:
            sidehit = int(input('Which side was hit? (Front=1, Sides=2, Rear=3)'))
            if sidehit==1:
                AV = target.ArmF
            elif sidehit==2:
                AV = target.ArmS
            elif sidehit==3:
                AV = target.ArmR
            else:
                print("No valid selection")
        if 'melta' in weaponspecial.casefold() or 'sniper' in weaponspecial.casefold():
            td = roll_dice('2d6')[0] 
        else:
            td = roll_dice('d6')[0]
        if 'rending' in weaponspecial.casefold() and td==6:
            print('The rending attacks rips apart the vehicle\'s armour!')
            td += roll_dice('d6')[0]
        if (td+weaponS)>AV:
            if 'ordnance' in weaponspecial.casefold():
                unit.ord_hits += 1
            else:
                unit.pen_hits += 1
            print(f'A penetrating hit on {target.name}!')
        elif (td+weaponS)==AV or ('gauss' in weaponspecial.casefold() and roll_dice('d6')[0]==6):
            if weaponAP==1:
                unit.pen_hits += 1
            else:
                unit.glancing_hits += 1
            print(f"A glancing hit on {target.name}!")
        else:
            print('The hit bounces off the vehicle\'s armour...')
        #print((td+weaponS)) #check
                
    def fire(self):
        th = random.randint(1, 6)
        if th >= (7-self.BS):
            print(f"%s fires (%i) and hits!" % (self.name, th))
            self.damage() #return True
        else:
            print(f"%s fires (%i) and misses." % (self.name, th)) #return False
            
    def fire_at(self, target, unit, weapon=None):
        if self.rangedweapons == []:
            print(f'{self.name} has no ranged weapons.')
        else: 
            #if any('heavy' in w.Type.lower() for w in self.rangedweapons):
            if 'heavy' in weapon.Type.lower():
                unit.actions_done.append('moved')
            if 'rapid' in weapon.Type.lower():
                unit.actions_done.append('charged')
                
            th = random.randint(1, 6)
            if 'gets hot' in weapon.Special.casefold() and th==1:
                print(f"The {self.name} gets hot!")
                self.is_wounded(unit)
            if 'rending' in weapon.Special.casefold() and th==6:
                print(f"The {self.name} hits with a rending shot!")
                if unit != None:
                    unit.wounding_hits += 1
                    unit.weaponAP = 1
            if 'sniper' in weapon.Special.casefold() and th>=2:
                print(f"%s places a crack shot (%s) and hits!" % (self.name, weapon.Name))
                if type(target).__name__ == 'Vehicle':
                    self.damage_vehicle(target=target, unit=unit, weaponAP=weapon.AP, weaponS=weapon.Strength, weaponspecial=weapon.Special)
                else:
                    self.damage(target=target, unit=unit, weapon=weapon)
            elif th >= (7-self.BS):
                #print(f"%s fires (%i) and hits!" % (self.name, th))
                print(f"%s fires (%s) and hits! (■%i)" % (self.name, weapon.Name, th))
                if type(target).__name__ == 'Vehicle':
                    self.damage_vehicle(target=target, unit=unit, weaponAP=weapon.AP, weaponS=weapon.Strength, weaponspecial=weapon.Special)
                else:
                    self.damage(target=target, unit=unit, weapon=weapon)
            else:
                if 'twin' in weapon.Special.casefold():   #of roll_dice('2d6K1')[0]?
                    re_roll = random.randint(1, 6)
                    if re_roll >= (7-self.BS):
                        print(f"%s\'s spray of bullets (%s) hits! (■%i)" % (self.name, weapon.Name, re_roll))
                        if type(target).__name__ == 'Vehicle':
                            self.damage_vehicle(target=target, unit=unit, weaponAP=weapon.AP, weaponS=weapon.Strength, weaponspecial=weapon.Special)
                        else:
                            self.damage(target=target, unit=unit, weapon=weapon)
                else:
                    print(f"%s fires (%s) but misses." % (self.name, weapon.Name))
    
    def is_wounded(self, unit=None):
        tw = random.randint(1, 6)  #print(tw)
        if tw >= int(self.Sv[0]):
            return False
        else:
            self.W -= 1
            if self.W <= 0:
                print(self.name, "is killed.")
                unit.remove_Troop(self.name)
            else:
                print(self.name, "gets burned.")

    def Ld_test(self, mod=0, psychic=False):
        test = roll_dice('2d6')[0]
        if psychic:
            return test
        else:    
            if test == 2:
                return True
            elif test <= (self.Ld + mod):
                return True
            else:
                return False
    
    def melee(self, target=None, unit=None):
        if self.meleeweapons == []:
            weapon = Weapon('close combat weapon', 0, self.S, 9, 'Melee')
        else:
            weapon = self.meleeweapons[0] #always use first melee weapon?? Attacks per troop, voor gemak geen onderscheid in wapens
        if 'poisoned' in weapon.Special.casefold():
            pass
        
        th = roll_dice('d6')[0]
        targetWS = None
        if type(target).__name__ == 'Vehicle' and "Walker" not in target.type.casefold():
            if th >= 4 if 'moved' in target.actions_done else 1:
                self.damage_vehicle(target=target, unit=unit, weaponS=weapon.Strength, weaponAP=weapon.AP, weaponspecial=weapon.Special)
        elif target==None:
            targetWS = int(input('Target Weapon Skill?'))
        elif type(target).__name__ == 'Monster' or (type(target).__name__ == 'Vehicle' and "Walker" in target.type.casefold()):
            targetWS = target.WS
        else:
            targetWS = min([troop.WS for troop in target.members], key=[troop.WS for troop in target.members].count)
        
        if targetWS != None:
            if self.WS - targetWS > 0:
                mod = -1
            elif self.WS / targetWS < 0.5:
                mod = 1
            else:
                mod = 0
            
            if 'rending' in weapon.Special.casefold() and th==6:
                target.saving_throw(weaponAP=weapon.AP, weaponS=weapon.Strength)
            elif th >= (4+mod):
                print(f"%s manages to hit %s! (■%i)" % (self.name, target.name, th))
                #self.damage(target=target, unit=unit, weaponS=self.S, weaponAP=self.weaponAP)
                self.damage(target=target, unit=unit, weapon=weapon)
            else:
                print(f"%s fails to hit the target. (■%i)" % (self.name, th))
    
    def psychic(self):
        test = self.Ld_test(psychic=True)
        if test == 2 or test == 12:
            print(f"{self.name} suffers an attack from the Warp!")
            self.is_wounded()
        if test <= self.Ld:
            print(f"%s passes their psychic test. (■%i)" % (self.name, test))
            return True
        else:
            print(f"%s cannot concentrate this turn. (■%i)" % (self.name, test))
            return False

class Weapon:
    def __init__(self, Name, Range, Strength, AP, Type, TypeNum=1, Special=''):
        self.Name = Name    #N.B. alleen bij Weapon zijn alle attributes met hoofdletter
        self.Range = Range
        self.Strength = Strength
        self.AP = AP
        self.Type = Type
        self.TypeNum = TypeNum
        self.Special = Special

Bolter = Weapon('boltgun', 24, 4, 5, 'Rapid Fire')
HeavyBolter = Weapon('heavy bolter',36, 5, 4, 'Heavy', 3)
StormBolter = Weapon('storm bolter',24, 4, 5, 'Assault', 2)
PlasmaPistol = Weapon('plasma pistol',12, 7, 2, 'Pistol', Special="Gets Hot!")
PowerFist = Weapon('power fist', 0, 8, 0, 'Melee', Special="power")
RelicBlade = Weapon('relic blade', 0, 6, 0, 'Melee', Special="power")
SM = Troop('Space Marine', 4,4,4,4,1,4,1,8,'3+',[Bolter]) #SM1.fire()
SMS = Troop('Space Marine Sergeant', 4,4,4,4,1,4,2,9,'3+',[PlasmaPistol])
SMC = Troop('Space Marine Captain', 6,5,4,4,3,5,3,10,'2+',[Bolter, RelicBlade])
SMTC = Troop('Space Marine Terminator Captain', 6,5,4,4,3,5,3,10,'2+/5+',[StormBolter, PowerFist])

SM_squad = Squad('Space Marine Tactical Squad', [SM, SM, SM, SMS])
SM_squad.add_Troop(SMTC) #SM_squad.add_Troops([SM1, SM1]) #SM_squad.remove_Troop(SM2)
#SM1.is_wounded() #check maar nog niet automatisch verwijderd......
SM_squad.composition() #SM_squad.all_fire()

Lasgun = Weapon('lasgun', 24, 3, 9, 'Rapid Fire')
Sniper = Weapon('sniper', 36, 0, 6, 'Heavy', Special='Sniper')
Meltagun = Weapon('meltagun', 12, 8, 1, 'Assault', Special='Melta')
GrenadeLauncher = Weapon('frag grenade launcher', 24, 3, 6, 'Assault', Special='Blast')
G = Troop('Guardsman',3,3,3,3,1,3,1,7,'5+',[Lasgun]); GS = Troop('Guardsman',3,3,3,3,1,3,1,7,'5+',[Sniper])
GG = Troop('Guardsman',3,3,3,3,1,3,1,7,'5+',[GrenadeLauncher]); GM = Troop('Guardsman',3,3,3,3,1,3,1,7,'5+',[Meltagun])
SWSquad = Squad('Special Weapon Squad', [G, G, G, GS, GM, GG])

Fleshborer = Weapon('fleshborer', 12, 4, 5, 'Assault', Special='Living Ammunition')
Spinefist = Weapon('spinefist', 12, 3, 5, 'Assault', Special='Twin-linked')
TWDevourer = Weapon('twinked-linked devourer', 18, 6, 9, 'Assault', 8, Special='Twin-linked, Living Ammunition')
BarbedStrangler = Weapon('barbed strangler', 36, 8, 5, 'Assault', Special='Large blast, pinning')
RendingClaws = Weapon('rending claws', 0, 0, 9, 'Melee', Special='rending')
ScythingTalons = Weapon('scything talons', 0, 0, 9, 'Melee', Special='re-roll 1s')
TG = Troop('Termagant',3,3,3,3,1,4,1,5,'6+',[Fleshborer]) #'Fleshborer' with S+1 damage and X attacks
SG = Troop('Spinegaunt',3,3,3,3,1,4,1,5,'6+',[Spinefist])
HG = Troop('Hormagaunt',4,3,3,3,1,4,2,5,'6+',[ScythingTalons])
GS = Troop('Genestealer',6,0,4,4,1,6,2,10,'5+',[RendingClaws]); BL = Troop('Broodlord',7,0,5,5,3,7,4,10,'4+',[RendingClaws, ScythingTalons])
Carnifex1 = Monster('Thornback',3,3,10,6,4,1,2,10,'3+',[TWDevourer, BarbedStrangler])
TG_squad = Squad('Termagant brood', [TG, TG, TG, TG, TG, TG, TG, TG], special='Fleet of claw')
SG_squad = Squad('Spinegaunt brood', [SG, SG, SG, SG, SG, SG, SG, SG, SG, SG], special='Fleet of claw')
HG_squad = Squad('Hormagaunt brood', [HG, HG, HG, HG, HG, HG, HG, HG], special='Fleet of claw')
GB_squad = Squad('Genestealer brood', [GS, GS, GS, GS, BL])

Shoota = Weapon('shoota', 18, 4, 6, 'Assault', 2); Rokkit = Weapon('rokkit launcha', 24, 8, 3, 'Assault', 1)
AB1 = Troop('\'Ard Boy',4,2,3,4,1,2,2,7,'4+',[Shoota]); AB2 = Troop('\'Ard Boy',4,2,3,4,1,2,2,7,'4+',[Rokkit])
ABN = Troop('\'Ard Boy Nob',4,2,4,4,2,3,3,7,'4+',[Shoota])
OB_squad = Squad('\'Ard Boyz mob', [AB1, AB1, AB1, AB2, AB2, AB2, AB2, ABN])

GaussBlaster = Weapon('gauss blaster', 24, 5, 4, 'Rapid Fire', 'Gauss')
TWTeslaDestr = Weapon('twin-linked tesla destructor', 24, 7, 9, 'Assault', 4, 'Twin-linked, Tesla, Arc')
NI = Troop('Necron Immortal',4,4,4,4,1,2,1,10,'3+',[GaussBlaster])
NI_squad = Squad('Necron Immortals', [NI, NI, NI, NI, NI])
NScythe = Vehicle('Night Scythe', 4, 11, 11, 11, capacity=15, type='Fast, Skimmer', weapons=[TWTeslaDestr], members=NI_squad)

Demolisher = Weapon('Demolisher cannon',24, 10, 2, 'Ordnance')
Rhino = Vehicle('Rhino Transport', 4, 11, 11, 10, 'Tank', capacity=10, members=SM_squad)
Rhino.add_passengers(SMC)
Vindicator = Vehicle('Vindicator', 4, 13, 11, 10, 'Tank', capacity=0, weapons=[Demolisher, StormBolter])

AssaultCannon = Weapon('assault cannon', 24, 6, 4, 'Heavy', TypeNum=4, Special='Rending'); Doomfist = Weapon('nemesis doom fist', 0, 10, 0, 'Melee', Special="power")
DN = Vehicle('Grey Knight Dreadnought', WS=4, BS=4, S=6, ArmF=12, ArmS=12, ArmR=10, I=4, A=2, type='Walker', weapons=[StormBolter, Doomfist, AssaultCannon])
Dae = Troop('Daemonette',4,0,4,3,1,4,2,8,'-/5+', weapons=None) #default of daemonic talons?
DPD_squad = Squad('Daemonette pack', [Dae, Dae, Dae, Dae, Dae])

# game1 = Game(); game1.start(Vindicator, Rhino, SM_squad, TG_squad, SG_squad, HG_squad, OB_squad, 
#                           Carnifex1, SWSquad, NScythe, DPD_squad, DN)

# SM_squad.fire_at(SG_squad)
# TG_squad.fire_at(SM_squad)
# SM_squad.move()
# SM_squad.charge_at(HG_squad)
# HG_squad.charge_at(SM_squad)
# SM_squad.melee(HG_squad)
# SG_squad.fire_at(SM_squad)
# TG_squad.composition()
# OB_squad.fire_at(SM_squad)
# OB_squad.morale_test()

# game1.next_turn()
# game1.current_turn()

# Vindicator.fire_at(TG_squad)
# GB_squad.melee(Vindicator)
# Rhino.move(); OB_squad.fire_at(Rhino)
# Vindicator.fire_at(NScythe)
# SWSquad.fire_at(NScythe)
# NScythe.fire_at(Rhino)
# Carnifex1.fire_at(SM_squad)
# DPD_squad.charge_at(SM_squad)
# DN.fire_at(SG_squad)
# DN.charge_at(DPD_squad)



############ Building the pygame

#To do: achtergrond, ground overlay
#       custom aantal units per leger
#       movement vertellen of bijhouden


import pygame as pygame, math as math, string   #eztext voor text input?


def play_game():
    
    game = Game(); game.start(Vindicator, SM_squad, SWSquad, TG_squad, HG_squad, Carnifex1)   #eerste 3 units per leger
        
    pygame.init()                                 #start up dat pygame
    clock = pygame.time.Clock()                   #for framerate or something? still not very sure
    Screen = pygame.display.set_mode([960, 1080])  #making the window, width*height
    Done = False                                  #variable to keep track if window is open
    MapSize = 40                                  #how many tiles in either direction of grid

    TileWidth = 20                                #pixel sizes for grid squares
    TileHeight = 20
    TileMargin = 4

    BLACK = (0, 0, 0)                             #some color definitions
    GREEN = (0, 255, 0)
    DARKGREEN = (0, 130, 0)
    RED = (255, 0, 0)
    DARKRED = (150, 0, 0)
    BLUE = (0, 0, 255)
    randomBackDrop = random.sample([pygame.Color('gray69'), pygame.Color('darkolivegreen3'), #https://www.pygame.org/docs/ref/color_list.html
                                    pygame.Color('azure3'), pygame.Color('wheat2')], 1).pop()

    pygame.display.set_caption('Warhammer 40k simulator! (Press ESC to quit.)')
    font_title = pygame.font.Font('40k_resources/OPTIFurst-Bold.otf', 50); font_text = pygame.font.Font('40k_resources/RollboxRegular.ttf', 16)
    title_surface = font_title.render('My 40k game', False, 'White')
    text_surface1  = font_text.render('Click the unit you wish to move. Press Enter to end the turn, T to see unit composition,', False, 'White')
    text_surface2  = font_text.render('M to mark move and C to iniate charge.', False, 'White')

    class MapTile(object):                       #The main class for stationary things that inhabit the grid ... grass, trees, rocks and stuff.
        def __init__(self, Type, Column, Row):
            self.Name = Type
            self.Column = Column
            self.Row = Row
            self.Unit = None
            self.Objects = []  # Store objects that occupy the tile

    class Character(Squad, Monster, Vehicle):                    
        def __init__(self, parent, Column, Row):
            #super().__init__(Squad)
            super().__init__(parent.name)
            self.Name = parent.name
            self.Column = Column
            self.Row = Row
            self.ParentClass = parent.__class__.__name__
            self.parent = parent
        #for attr, value in parent.__dict__.items(): # Update the instance with attributes from the parent class
            #    setattr(self, attr, value)
        #self.__dict__.update(parent.__dict__)    #THIS LINE, I WAS ASKING FOR THIS SIMPLE LINE  
        def __getattr__(self, name):
            return getattr(self.parent, name)
            
        def CollisionCheck(self, Direction):       #Checks if anything is on top of the grass in the direction that the character wants to move. Used in the move function
            if Direction == "UP":
                if len(Map.Grid[self.Column][(self.Row)-1]) > 1:
                    return True
            elif Direction == "LEFT":
                if len(Map.Grid[self.Column-1][(self.Row)]) > 1:
                    return True
            elif Direction == "RIGHT":
                if len(Map.Grid[self.Column+1][(self.Row)]) > 1:
                    return True
            elif Direction == "DOWN":
                if len(Map.Grid[self.Column][(self.Row)+1]) > 1:
                    return True
            return False

        def Location(self):
            print("Coordinates: " + str(self.Column) + ", " + str(self.Row))
            
        def MeasureDistance(self, target_column, target_row):
            dx = target_column - self.Column
            dy = target_row - self.Row
            return round(math.sqrt(dx**2 + dy**2), 1)
            
        def Move(self, Direction):              #This function is how a character moves around in a certain direction
            if Direction == "UP":
                if self.Row > 0:                #If within boundaries of grid
                    if self.CollisionCheck("UP") == False:       #And nothing in the way
                        self.Row -= 1            #Go ahead and move

            elif Direction == "LEFT":
                if self.Column > 0:
                    if self.CollisionCheck("LEFT") == False:
                        self.Column -= 1

            elif Direction == "RIGHT":
                if self.Column < MapSize-1:
                    if self.CollisionCheck("RIGHT") == False:
                            self.Column += 1

            elif Direction == "DOWN":
                if self.Row < MapSize-1:
                    if self.CollisionCheck("DOWN") == False:
                        self.Row += 1 


    class Map(object):              #The main class; where the action happens
        #global MapSize
        def __init__(self):
            self.Grid = []  # Initialize the grid
            for Row in range(MapSize):
                self.Grid.append([])
                for Column in range(MapSize):
                    self.Grid[Row].append([])

            for Row in range(MapSize):
                for Column in range(MapSize):
                    TempTile = MapTile("Dirt", Column, Row)
                    self.Grid[Column][Row].append(TempTile)

            for i in range(random.randint(4, 11)):          #Placing random rocks
                RandomRow = random.randint(0, MapSize - 1)
                RandomColumn = random.randint(0, MapSize - 1)
                TempTile = MapTile("Rock", RandomColumn, RandomRow)
                self.Grid[RandomColumn][RandomRow].append(TempTile)
                
            for i in range(random.randint(0, 3)):          #Placing random water
                RandomRow = random.randint(0, MapSize - 1)
                RandomColumn = random.randint(0, MapSize - 1)
                TempTile = MapTile("Water", RandomColumn, RandomRow)
                self.Grid[RandomColumn][RandomRow].append(TempTile)
                for _ in range(random.randint(0, 2)):
                    NoiseRow = random.randint(-1, 1)
                    NoiseCol = random.randint(-1, 1)
                    #print("RandomColumn:",RandomColumn); print("RandomRow:",RandomRow)
                    #print("NoiseCol:",NoiseCol); print("NoiseRow:",NoiseRow)
                    if (RandomColumn+NoiseCol)<MapSize and (RandomRow+NoiseRow)<MapSize:
                        TempTile = MapTile("Water", RandomColumn+NoiseCol, RandomRow+NoiseRow)
                        self.Grid[RandomColumn+NoiseCol][RandomRow+NoiseRow].append(TempTile)

            for i in range(random.randint(0, 5)*3):          #Placing random trees
                RandomRow = random.randint(0, MapSize - 1)
                RandomColumn = random.randint(0, MapSize - 1)
                TempTile = MapTile("Tree", RandomColumn, RandomRow)
                self.Grid[RandomColumn][RandomRow].append(TempTile)

            self.teams = {
                1: [],  #game.groups[:len(game.groups)//2]
                2: []
            }
            teamcounter = 0
            for team in self.teams.values():                    #dividing the units over the teams
                half = int(len(game.groups)/2)
                teamcounter += 1
                for s in range(half):               #number of units per team
                    RandomRow = random.randint(0, MapSize - 1)      #placing the units randomly on the battlefield
                    RandomColumn = random.randint(0, MapSize - 1)
                    unit = Character(game.groups[s+(half if teamcounter>1 else 0)], RandomColumn, RandomRow)
                    team.append(unit)

            # for team in self.teams.values(): 
            #     for _ in range(3):  #number of heroes per team
            #         RandomRow = random.randint(0, MapSize - 1)
            #         RandomColumn = random.randint(0, MapSize - 1)
            #         unit = Character("Hero", RandomColumn, RandomRow)
            #         team.append(unit)

            self.current_team = 1  # Starting team

        def ask_for_target(self, event):
            print("(Left-click the target cell)")
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Left click
                            pos = pygame.mouse.get_pos()
                            column = pos[0] // (TileWidth + TileMargin)
                            row = pos[1] // (TileHeight + TileMargin)
                            return row, column
        
        def update(self):        #Very important function
                                #This function goes through the entire grid
                                #And checks to see if any object's internal coordinates
                                #Disagree with its current position in the grid
                                #If they do, it removes the objects and places it 
                                #on the grid according to its internal coordinates 
            for Column in range(MapSize):   #this makes sure the moving unit doesn't leave a trail ;)
                for Row in range(MapSize):
                    self.Grid[Column][Row][0].Unit = None  # Clear the Unit information
                    self.Grid[Column][Row][0].Objects = []  # Clear the objects list

            for team in self.teams.values():
                for unit in team:
                    tile = self.Grid[int(unit.Column)][int(unit.Row)][0]  # Get the MapTile
                    if (unit.ParentClass == "Squad" and len(unit.parent.members)>0) \
                        or (unit.ParentClass == "Monster" and unit.parent.W>0) \
                            or (unit.ParentClass == "Vehicle" and unit.parent.HP>0):                     #check if unit is wiped out
                        tile.Unit = unit  # Place the hero on the tile
                        tile.Objects.append(unit)  # Add hero to the objects list of the tile       
                    
        def DrawUnits(self):
            for Column in range(MapSize):
                for Row in range(MapSize):
                    tile = self.Grid[Column][Row][0]  # Access the first element of the nested list
                    #TileColor = BLACK
                    if tile.Unit:
                        if tile.Unit in self.teams[1]:
                            if self.current_team == 1:
                                TileColor = GREEN
                            else:
                                TileColor = DARKGREEN
                        elif tile.Unit in self.teams[2]:
                            if self.current_team == 1:
                                TileColor = DARKRED
                            else:
                                TileColor = RED
                        pygame.draw.rect(Screen, TileColor, [(TileMargin + TileWidth) * Column + TileMargin,
                                                            (TileMargin + TileHeight) * Row + TileMargin,
                                                            TileWidth, TileHeight])
                        # Draw unit's initial as a capital letter
                        font = pygame.font.Font(None, 30)
                        initial = tile.Unit.Name[0].upper()
                        text = font.render(initial, True, BLACK)
                        text_rect = text.get_rect(center=((TileMargin + TileWidth) * Column + TileMargin + TileWidth/2,
                                                        (TileMargin + TileHeight) * Row + TileMargin + TileHeight/2))
                        Screen.blit(text, text_rect)

    Map = Map()
    selected_unit = None  # Variable to track the selected hero
    
    while not Done:     #Main pygame loop

        for event in pygame.event.get():         #catching events
            if event.type == pygame.QUIT:
                Done = True       

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    Pos = pygame.mouse.get_pos()
                    Column = Pos[0] // (TileWidth + TileMargin)
                    Row = Pos[1] // (TileHeight + TileMargin)
                    print("( Grid position",str(Row) + ", " + str(Column),") :")

                    for i in range(len(Map.Grid[Column][Row])):
                        print(str(Map.Grid[Column][Row][i].Name))
                        if Map.Grid[Column][Row][i].Unit:
                            print(str(Map.Grid[Column][Row][i].Unit.Name))
                            #print(Map.Grid[Column][Row][0].Unit)
                            #print(Map.Grid[Column][Row][0].Unit.ParentClass)
                            #print(Map.Grid[Column][Row][0].Unit.parent)
                            #Map.Grid[Column][Row][0].Unit.composition()
                            #print(Map.Grid[Column][Row][0].Objects[0])
                            print("Actions done this turn:",Map.Grid[Column][Row][0].Unit.parent.actions_done,"\n")
                    selected_unit = Map.Grid[Column][Row][0].Unit  # Select the unit at the clicked position
                
                elif event.button == 2:  # Middle click to measure
                    if selected_unit:
                        Pos = pygame.mouse.get_pos()
                        Column = Pos[0] // (TileWidth + TileMargin)
                        Row = Pos[1] // (TileHeight + TileMargin)
                        distance = selected_unit.MeasureDistance(Column, Row)
                        print("Distance:", distance)
                        
                elif event.button == 3:  # Right click to attack
                    if selected_unit:
                        Pos = pygame.mouse.get_pos()
                        Column = Pos[0] // (TileWidth + TileMargin)
                        Row = Pos[1] // (TileHeight + TileMargin)
                        distance = selected_unit.MeasureDistance(Column, Row)
                        if Map.Grid[Column][Row][0].Objects != []:
                            if int(distance)>1:
                                print(f'{selected_unit.Name} fires at {Map.Grid[Column][Row][0].Objects[0].Name} from a distance of {int(distance)}"')
                                selected_unit.parent.fire_at(Map.Grid[Column][Row][0].Unit.parent) #or .Objects[0] ?
                            if int(distance)==1:
                                print(f'{selected_unit.Name} fights in close combat...')
                                selected_unit.parent.melee(Map.Grid[Column][Row][0].Unit.parent)
                        else:
                            print("Nothing there to attack...")
                        
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    Done = True
                if event.key == pygame.K_RETURN:                                        # Change turn
                    Map.current_team = 2 if Map.current_team == 1 else 1                # Switch to the other team
                    game.next_turn()
                    print(f"\n\nEnd of turn. It is now the turn for team {string.ascii_uppercase[Map.current_team-1]}.")
                    selected_unit = None                                                # Deselect the hero
                if event.key == pygame.K_c and selected_unit:
                    print("Where do you want to charge?")
                    target_row, target_column = Map.ask_for_target(event)
                    #print("Charging target: (Grid position {}, {})".format(target_row, target_column))
                    selected_unit.parent.charge_at(Map.Grid[target_column][target_row][0].Unit.parent)
                if event.key == pygame.K_m and selected_unit:
                    selected_unit.parent.move()
                if event.key == pygame.K_t and selected_unit:
                    if selected_unit.ParentClass == 'Squad':
                        selected_unit.parent.composition()
                    elif selected_unit.ParentClass == 'Vehicle':
                        print(f'The {selected_unit.Name} has {len(selected_unit.parent.members)} passengers')
                if event.key == pygame.K_LEFT and selected_unit:
                    selected_unit.Move("LEFT")                          # Move the selected hero
                if event.key == pygame.K_RIGHT and selected_unit:
                    selected_unit.Move("RIGHT")
                if event.key == pygame.K_UP and selected_unit:
                    selected_unit.Move("UP")
                if event.key == pygame.K_DOWN and selected_unit:
                    selected_unit.Move("DOWN")
                    
        Screen.fill(BLACK)
        Screen.blit(title_surface, (20, 960))
        Screen.blit(text_surface1, (30, 1030))
        Screen.blit(text_surface2, (30, 1055))

        for Row in range(MapSize):                                      # Drawing the map grid
            for Column in range(MapSize):
                for i in range(0, len(Map.Grid[Column][Row])):
                    Color = randomBackDrop
                    if Map.Grid[Column][Row][i].Name == "Tree":
                        Color = pygame.Color('sienna4')
                    if Map.Grid[Column][Row][i].Name == "Rock":
                        Color = pygame.Color('snow4')
                    if Map.Grid[Column][Row][i].Name == "Water":
                        Color = BLUE

                pygame.draw.rect(Screen, Color, [(TileMargin + TileWidth) * Column + TileMargin,
                                                (TileMargin + TileHeight) * Row + TileMargin,
                                                TileWidth,
                                                TileHeight])

        clock.tick(60)      #Limit to 60 fps or something
        Map.update()
        Map.DrawUnits()
        pygame.display.flip()     #Honestly not sure what this does, but it breaks if I remove it
        #Volgens ChatGPT: The pygame.display.flip() function is used to update the contents of the entire display. It basically makes the updated frame visible on the screen. So, it's necessary to call pygame.display.flip() after drawing everything to the screen to make the changes visible to the user.

    pygame.quit()


play_game()