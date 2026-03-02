import requests
#Settingd logic
def save_settings(info):
    """Should update settings info persistently"""
    default_currency = info[default_currency]
    #total_money = info[total_money]
    currencyList_source = "https://gist.github.com/gp187/4393cbc6dd761225071270c29b341b7b#file-currencies-json" #dev

#Create expenses/income logic
class Expenditure:
    """Object for expenses and incomes"""
    def __init__(self, name, amount, currency, isExpense, items):
        self.name = name
        self.amount = amount
        self.currency = currency
        self.isExpense = isExpense
        self.items = items if isExpense else [] #List of objects [{}]
        
    def update_expenditure(self, name, amount, currency, isExpense, items):
        self.name = name
        self.amount = amount
        self.currency = currency
        self.isExpense = isExpense
        self.items = items if isExpense else []

    def fetch_expenditure(self):
        return {"name": self.name, "amount": self.amount, "currency" : self.currency, "isExpense": self.isExpense, "items":self.items}

def create_expenditure(isExpense, data):
    """Create expense or income using class instantiation. data is a Tuple (name, amount, currency, isExpense, items)"""
    current_expenditure = Expenditure(*data).fetch_expenditure()
    total_money = 0 #Ideally picked from storage
    default_currency = "HKD" #Ideally picked from storage
    if isExpense:
        #function to subtract amount from total money available
        if current_expenditure["currency"] != default_currency: #Currency conversion
            try:
                response = requests.get("https://v6.exchangerate-api.com/v6/f06daf89779f53f98b1276be/pair/" + f"{current_expenditure["currency"]}/{default_currency}/{current_expenditure["amount"]}", timeout=5)
                if response.status_code == 200:
                    total_money -= round(response.json()["conversion_result"], 2)
                else:
                    raise Exception('Currency not found') #Raise exception or error
            except Exception as e:
                print(e)
        else:
            total_money -= current_expenditure["amount"]
        print(total_money)
    else:
        #function to add income amount to total money available
        if current_expenditure['currency'] != 'HKD':
            try:
                response = requests.get("https://v6.exchangerate-api.com/v6/f06daf89779f53f98b1276be/pair/" + f"{current_expenditure["currency"]}/HKD/{current_expenditure["amount"]}", timeout=5)
                if response.status_code == 200:
                    total_money += round(response.json()["conversion_result"], 2)
                else:
                    raise Exception('Currency not found')
            except Exception as e:
                print(e)
        else:
            total_money += current_expenditure["amount"]
        print(total_money)

    #Storage function should store data pesistently using expense_or_income.fetch_expenditure()
create_expenditure(False,('Test', 1000, "ZMW", False, [{'name': 'Item 1', 'qty':2, 'price':100}]))
