from datetime import datetime
import requests
#Settingd logic
def save_settings(info):
    """Should update settings info persistently"""
    default_currency = info['default_currency']
    #total_money = info[total_money]
    currencyList_source = "https://gist.githubusercontent.com/gp187/4393cbc6dd761225071270c29b341b7b/raw/eb21c79192c4308152ba74924a4efc4bdfaa4377/currencies.json" #dev

#Create expenses/income logic

class Expense:
    """Object for expenses"""
    def __init__(self, name, category, currency, amount, items):
        self.name = name
        self.category = category
        self.currency = currency
        self.amount = amount
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.isExpense = True
        self.items = items
        
    def update_expense(self, name, amount, currency, items):
        self.name = name
        self.updated_at = datetime.now()
        self.amount = amount
        self.currency = currency
        self.items = items
    
    def __delete__(self, instance):
        return "Expense deleted successfully"

    def fetch_expense(self):
        return {"name": self.name, "amount": self.amount, "currency" : self.currency, "isExpense": self.isExpense, "category" : self.category, "items": self.items, "created_at": self.created_at, "updated_at": self.updated_at}

class Income(Expense):
    """Object for incomes"""
    def __init__(self, name, category, currency, amount, items):
        super().__init__(name, category, currency, amount, items=[]) #Incomes should not have items, only expenses
        self.isExpense = False

    def fetch_income(self):
        return super().fetch_expense() #Income and expense have the same attributes, so we can reuse the fetch_expense method
    
    def update_income(self, name, amount, currency, items):
        return super().update_expense(name, amount, currency, items)

def create_expense_or_income(isExpense, data):
    """Create expense or income using class instantiation. data is a dictionary with keys as (name, amount, currency, category, items #List of objects [{}])"""
    current = Expense(**data).fetch_expense() if isExpense else Income(**data).fetch_income()
    total_money = 0 #Ideally picked from storage
    default_currency = "HKD" #Ideally picked from storage
    print(current)
    if isExpense:
        #function to subtract amount from total money available
        if current["currency"] != default_currency: #Currency conversion
            try:
                response = requests.get("https://v6.exchangerate-api.com/v6/f06daf89779f53f98b1276be/pair/" + f"{current["currency"]}/{default_currency}/{current["amount"]}", timeout=5)
                if response.status_code == 200:
                    total_money -= round(response.json()["conversion_result"], 2)
                else:
                    print(response.json())
                    raise Exception('Currency not found') #Raise exception or error
            except Exception as e:
                print(e)
        else:
            total_money -= current["amount"]
        print(total_money)
    else:
        #function to add income amount to total money available
        if current['currency'] != 'HKD':
            try:
                response = requests.get("https://v6.exchangerate-api.com/v6/f06daf89779f53f98b1276be/pair/" + f"{current["currency"]}/HKD/{current["amount"]}", timeout=5)
                if response.status_code == 200:
                    total_money += round(response.json()["conversion_result"], 2)
                else:
                    raise Exception('Currency not found')
            except Exception as e:
                print(e)
        else:
            total_money += current["amount"]
    
    print(total_money, 'class test', current)

    #Storage function should store data pesistently using expense_or_income.fetch_expense()

create_expense_or_income(True, data = {'name': 'Test', 'category': 'Test Cat', 'currency': "ZMW", 'amount': 1000, 'items': [{'name': 'Item 1', 'qty': 2, 'price': 100}]})

#add logic to store currency conversion table locally and update it every 24 hours to reduce API calls and improve performance.
#test out possible data structures and algorithms for storing and retrieving expenses/incomes, currency conversion table and currencyList efficiently, implementing task 2 choices.
#currencies.json should only contain the information we need 
