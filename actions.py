from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import smtplib
from email.message import EmailMessage
from smtplib import SMTPException

import pandas as pd
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

ZomatoData = pd.read_csv('zomato.csv')
ZomatoData = ZomatoData.drop_duplicates().reset_index(drop=True)
WeOperate = ['agra', 'ahmedabad', 'aligarh', 'amravati', 'amritsar', 'asansol', 'aurangabad', 'bareilly', 'belgaum',
             'bangalore', 'bhavnagar', 'bhilai', 'bhiwandi', 'bhopal', 'bhubaneswar', 'bijapur', 'bikaner', 'bilaspur',
             'bokaro steel city', 'chandigarh', 'chennai', 'coimbatore', 'cuttack', 'dehradun', 'delhi', 'dhanbad',
             'dindigul', 'durgapur', 'erode', 'faridabad', 'firozabad', 'ghaziabad', 'gorakhpur', 'gulbarga', 'guntur',
             'gurgaon', 'guwahati', 'gwalior', 'hamirpur', 'hubli–dharwad', 'hyderabad', 'indore', 'jabalpur', 'jaipur',
             'jalandhar', 'jammu', 'jamnagar', 'jamshedpur', 'jhansi', 'jodhpur', 'kakinada', 'kannur', 'kanpur',
             'karnal', 'kochi', 'kolhapur', 'kolkata', 'kollam', 'kozhikode', 'kurnool', 'lucknow', 'ludhiana',
             'madurai', 'malappuram', 'mangalore', 'mathura', 'meerut', 'moradabad', 'mumbai', 'mysore', 'nagpur',
             'nanded', 'nashik', 'nellore', 'noida', 'patna', 'puducherry', 'prayagraj', 'pune', 'purulia', 'raipur',
             'rajahmundry', 'rajkot', 'ranchi', 'ratlam', 'rourkela', 'salem', 'sangli', 'shimla', 'siliguri',
             'solapur', 'srinagar', 'surat', 'thanjavur', 'thiruvananthapuram', 'thrissur', 'tiruchirappalli',
             'tirunelveli', 'tiruvannamalai', 'ujjain', 'vadodara', 'varanasi', 'vasai-virar city',
             'vellore and warangal', 'vijayawada', 'vizag']

cuisineList = ['american', 'chinese', 'italian', 'mexican', 'north indian', 'south indian']


# function to search restaurant
def RestaurantSearch(City, Cuisine, Price_1, Price_2):
    print(f"The details are searched in(RestaurantSearch method): {City}-{Cuisine}-{Price_1}-{Price_2}")
    City = str(City)
    Cuisine = str(Cuisine)
    price_1 = int(Price_1)
    price_2 = int(Price_2)
    if City.lower() in WeOperate and Cuisine.lower() in cuisineList:
        return ZomatoData[(ZomatoData['Cuisines'].apply(lambda x: Cuisine.lower() in x.lower())) & (
            ZomatoData['City'].apply(lambda x: str(x).strip().lower() == City.lower())) & (
                              ZomatoData['Average Cost for two'].apply(
                                  lambda x: True if price_1 <= int(x) <= price_2 else False))].loc[:,
               ['Restaurant Name', 'Address', 'Average Cost for two', 'Aggregate rating']].sort_values(
            'Aggregate rating', ascending=False)


# function to get results 
def get_results(loc, cuisine, price):
    """
    args:
        loc: city of restaurant
        cuisine: type of cuisine in restaurant
        price: Average cost for two
    returns:
        'Average Cost for two' column based Sorted resultant Dataframe matching all argument values.
    """
    print(f"The details are fetched for: {loc}-{cuisine}-{price}")
    if price == "Lesser than Rs. 300":
        price_1 = 0
        price_2 = 300
    elif price == "Rs. 300 to Rs. 700":
        price_1 = 300
        price_2 = 700
    elif price == "More than Rs. 700":
        price_1 = 700
        price_2 = 999999
    else:
        price_1 = 0
        price_2 = 999999
    return RestaurantSearch(City=loc, Cuisine=cuisine, Price_1=price_1, Price_2=price_2)


# class to search the restaurants
class ActionSearchRestaurants(Action):
    def name(self):
        return 'action_search_restaurants'

    def run(self, dispatcher, tracker, domain):
        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        price = tracker.get_slot('price')
        print(f"The details are being searched for: {loc}-{cuisine}-{price}")
        results = get_results(loc, cuisine, price)
        print(f"Results of action restaurant search: {results}")
        response = "\n"
        if results.shape[0] == 0:
            response = "We do not operate in {loc} yet"
        else:
            for restaurant in results.iloc[:10].iterrows():
                print(type(restaurant))
                print(restaurant)
                response = response + f"{restaurant[1][0]} in {restaurant[1][1]} has been rated {restaurant[1][3]}\n\n"
        dispatcher.utter_message("=> " + response)


# class to handle sending emails 
class ActionSendMail(Action):
    def name(self):
        return 'action_send_mail'

    def run(self, dispatcher, tracker, domain):
        print("An email will be sent...")
        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        price = tracker.get_slot('price')
        print(f"An email will be sent for: {loc}-{cuisine}-{price}")
        results = get_results(loc, cuisine, price)
        print(f"Results of action restaurant search: {results}")
        response = "\n"
        for restaurant in results[:10].iterrows():
            response = response + f"{restaurant[1][0]} in {restaurant[1][1]} costs {restaurant[1][2]} on average for two and has been rated {restaurant[1][3]}\n\n"

        # sender credentials for login
        sender = 'chattest.test2580@gmail.com'
        sender_password = 'India1234!'

        # Message
        msg = EmailMessage()
        msg.set_content(
            f"This Message contains top Restaurants based on rating: \n\n {response} \n\nThanks\nAahara Bot")

        msg['Subject'] = 'Top Restaurants of your preference.'
        msg['From'] = 'chattest.test2580@gmail.com'
        msg['To'] = tracker.get_slot('mail_id')

        # send mail
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender, sender_password)
            print("Login is successful.")
            server.send_message(msg)
            server.close()
            dispatcher.utter_message("=> " + "Email has been sent to you successfully.")
        except SMTPException as e:
            print("Email can't be sent, Thanks.", e)
            dispatcher.utter_message("=> " + "Invalid email.")


# class to check the location 
class ActionCheckLocation(Action):
    def name(self):
        return 'action_check_loc'

    def run(self, dispatcher, tracker, domain):
        location = tracker.get_slot('location')
        res = False
        if location.lower() in WeOperate:
            res = True
            dispatcher.utter_message(f"=> " + "Yes, we do operate in {location}.")
        else:
            res = False
            dispatcher.utter_message(f"=> " + "No, we don't operate in {location} yet.")
        return [SlotSet('check_resp', res)]