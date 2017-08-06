import sqlite3 
import datetime
import csv

# Class used to store the cash amount of an account
class CashBox(object):
    def __init__(self,balance=0.0):
        self.balance = balance
    def deposit(self, amount):
        self.balance +=amount
        return self.balance
    def withdraw(self, amount):
        self.balance -=amount
        return self.balance
    def get_balance(self):    
        return self.balance

# class Entity is used to associate an ID with a full name
class Entity(object):
    def __init__(self, name, ID):
        self.name=name
        self.ID=ID
    def identify(self):
        return self.ID
    def get_name(self):
        return self.name
        
# class used to associate a stock (ID is the stock symbol and name is the full name) with a a bid price and an ask price         
class Stock(Entity):
    def __init__(self,symbol, name, bid_price,ask_price):
        super(Stock, self).__init__(name, symbol)
        self.bid_price = bid_price
        self.ask_price = ask_price
    
    def get_ask_price(self):
        
        random = self.ask_price * 0
        return self.ask_price - random
        
    def get_bid_price(self):
        random = self.bid_price * 0
        return self.bid_price + random

# class used to store the stocks currently owned by an investor (the ID is the ID of the investor, date is the purchase date)        
class Purchased():
    def __init__(self,ID,symbol,quantity,date):
        self.ID=ID
        self.symbol=symbol
        self.quantity=quantity
        self.date=date
        
#class used to represent an investor being both an entity and a cashbox        
class Investor(Entity, CashBox):
    
    def __init__(self, name, ID):
        Entity.__init__(self, name, ID)
        CashBox.__init__(self)
    
# class used to store the market prices of the different stocks
class Market:
    def __init__(self):
        self.market_dic={}

    def add_stock(self,symbol, name, bid_price, ask_price):        
        newstock=Stock(symbol, name, bid_price,ask_price)
        self.market_dic[symbol] = newstock

    def get_bid_price(self,symbol):
        item = self.market_dic[symbol]
        return item.get_bid_price()

    def get_ask_price(self,symbol):
        item = self.market_dic[symbol]
        return item.get_ask_price()

    def show_market(self):
        for i in self.market_dic:
            item= self.market_dic[i]
            print item.identify(), item.get_name(), item.get_bid_price(), item.get_ask_price()

#class representing the borker.  The broker is assigned ID=0 
class Broker(CashBox):
    next_ID=0
    def __init__(self):
        CashBox.__init__(self)
        conn= sqlite3.connect('Broker')

        c= conn.cursor()
        c.execute('''create table if not exists Investor(ID Int Not NULL, NAME  CHAR(20) NOT NULL, Balance FLoat)''')
        
        # Set the next variable reinitializeDB to True to force reinitializing the whole program.
        # Set it to False to continue from session to session using the data stored in the database
        reinitializeDB = False
        #Check if the Broker line has already been inserted into the Investor table
        db_1st_run = c.execute('select * from Investor where ID==0')
        for line in db_1st_run:
            print line
            if line[0] ==0: # The Broker line has already been inserted into the Investor table
                print "Tables already exist and filled"
            else:
                print "empty table"
                reinitializeDB = True
        if( reinitializeDB ):
            initialize (c)
        conn.commit()
        self.market=Market()
        allMarket = c.execute('select * from Market')
        for line in allMarket:
            self.market.add_stock(line[0],line[1],line[2],line[3])
        self.investors=[]
        self.purchased_stocks=[]
        allInvestor = c.execute('select * from Investor')
        for line in allInvestor:
            print line
            if line[0] ==0: # this is the broker's own line. put his balance in his cashbox
                self.deposit(line[2])
            else:
                # add the investor to the list of investors within the broker
                # new_investor, name, balance, ID 
                self.add_investor(False, line[1],line[2],line[0],)
                if line[0]> self.next_ID:
                    self.next_ID = line[0]
        
        allPurchasedStocks = c.execute('select * from Stock')
        for line in allPurchasedStocks:
            # add the investor to the list of investors within the broker
            self.add_purchased(line[0],line[1],line[2],line[3])
        c.close()
    def __del__(self):
        conn= sqlite3.connect('Broker')
        c= conn.cursor()
        c.execute("delete from Investor")
        c.execute("delete from Stock")
        sqlStatement= 'insert into Investor values (0, "Kinda Maleh", %f)' %(self.get_balance())
        c.execute( sqlStatement )
        for client in self.investors:
            sqlStatement= 'insert into Investor values (%d, "%s", %f)' %(client.ID, client.name,client.get_balance())

            c.execute( sqlStatement )
        for line in self.purchased_stocks:
             sqlStatement = 'insert into Stock values(%d, "%s", %d,"%s")' %(line.ID,line.symbol,line.quantity,line.date)
            
             c.execute(sqlStatement)
        conn.commit()
        c.close()
    def get_next_ID(self):
        self.next_ID +=1
        return self.next_ID
    def add_investor(self, new_ID, name,balance=0, ID=0):
        if new_ID==True:
            ID= self.get_next_ID()
        new_investor=Investor(name,ID)
        new_investor.deposit(balance)
        self.investors.append(new_investor)
        return ID
    def add_purchased(self,ID,symbol,quantity,date):
         new_purchased=Purchased(ID,symbol,quantity,date)
         self.purchased_stocks.append(new_purchased)
    def buy(self,symbol,ID,quantity):
        ask_price=self.market.get_ask_price(symbol)
        total_price= ask_price*quantity

        # find the investor
        for client in self.investors:
            if client.identify()==ID:        
                balance = client.get_balance()
                commission=10 
                today= datetime.date.today()
                if balance>= total_price +commission:
                    client.withdraw(total_price)
                    self.deposit(commission)
                    print "Broker Buy Commision: ", self.get_balance()
                    self.add_purchased(ID,symbol,quantity,today)
                    print "Purchased stocks for ",client.get_name(), client.get_balance(),quantity, total_price
                    return  True
                else:
                    return False #sorry not enough balance                              
                break
                
    def show_market(self):            
        self.market.show_market()
        
    def sell(self,symbol,ID,quantity):
        commission=10
        
        bid_price=self.market.get_bid_price(symbol)
        total_price= bid_price*quantity
        # find the investor
        
        for client in self.investors:
            if client.identify()==ID:
                for i,line in enumerate(self.purchased_stocks):
                    if (line.ID==ID) and (line.quantity==quantity) and (line.symbol==symbol):
                        del self.purchased_stocks[i]
                        client.deposit(total_price-commission)               
                        self.deposit(commission)
                        print "Broker Sell Commision: ", self.get_balance()
                        print "sold stocks for ",client.get_name(), client.get_balance(),quantity, total_price
            
                        return  True
                
        return False #sorry cannt sell                              
               
    
    def show_investors(self):#
        
        for client in self.investors:
            print client.identify(), client.get_name(), 'Cash position: ', client.get_balance()
        
    def show_purchased(self,ID):#
        
        for client in self.investors:
            if client.identify()==ID:        
                print client.get_name(), 'Cash position: ', client.get_balance()
        for line in self.purchased_stocks:
            if line.ID==ID:
                print line.quantity,line.symbol,line.date
                

def initialize( c ):
    c.execute("delete from Investor")
    c.execute("delete from Stock")
    c.execute("delete from Market")
    c.execute('''create table if not exists Stock(ID Int Not NULL, Symbol char(5)Not Null,  Quanity Int, Date Int)''')
    c.execute('''create table if not exists Market(Symbol char(5)Not Null, NAME CHAR(20) NOT NULL, BidPrice FLoat, AskPrice FLoat)''')
    c.execute("insert into  Investor values ('0', 'Kenda Maleh', '0')")

    with open('Market_Quotes.csv', 'r') as fo:
        alllines = csv.reader(fo,delimiter=',')
        for lines in alllines:
            sqlStatement= 'insert into Market values ("%s", "%s", %f, %f)' %(lines[0],lines[1] ,float(lines[2]), float(lines[3]))
            c.execute( sqlStatement )


broker=Broker()

#Examples of the uses of the different available methods of the borker

#show the stocks we know about and their prices
broker.show_market()

#Adding an investor; will be assigned the next ID number
print broker.add_investor( True, 'Ravi', 10000 ); 
print broker.add_investor( True, 'Steve', 9999 )

#Invstor with ID = 1 wants to purchase 40 shares of Tesla
if (broker.buy("TSLA",1,40)):
    print "congratulation you did buy"
else:
    print "Sorry, could not buy"

#Invstor with ID = 2 wants to purchase 20 shares of Cisco
if( broker.buy("CSCO",2,20)):
    print "congratulation you did buy"
else:
    print "Sorry, could not buy"

#Invstor with ID = 1 wants to purchase 10 more shares of Tesla
if( broker.buy( "TSLA", 1, 10 )):
    print "congratulation you did buy"
else:
    print "Sorry, could not buy"

# show what investor with ID=2 has so far    
broker.show_purchased(2)

#Invstor with ID = 1 wants to sell 40 shares of Tesla
if( broker.sell("TSLA",1,40)):
    print "We sold TSLA for investor with ID=1"
else:
    print "Could not sell TSLA for investor with ID=1"
    
if broker.sell("TSLA",2,40):
    print "We sold TSLA for investor with ID=2"
else:
    print "Could not sell TSLA for investor with ID=2"

#Show the stocks owned by Investor with ID=1
broker.show_purchased(1) 

#Show the stocks owned by Investor with ID=2
broker.show_purchased(2) 

broker.show_investors()  

print "broker profit ", broker.get_balance()     

del broker
