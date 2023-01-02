#!/usr/bin/python3

import requests
import argparse
from flask import Flask, render_template
import psycopg2 # import the PostgreSQL adapter for Python
import urllib.parse as urlparse
from bs4 import BeautifulSoup
import ctypes
import re

def get_arguments():
    parser = argparse.ArgumentParser(prog="Subdomain_enumerator", description="Tool to discover subdomains")
    parser.add_argument("-u", "--URL", dest="target_url", help="Target URL you would like to enumerate its subdomains")
    return parser.parse_args()


user_choice=input("Select enum to perform: \n\n 1)subdomain [url WITHOUT http://] \n\n 2)crawler [url must start with 'https://'] \n\n 3)Brute_force_password [full url with the login directory: https://example.com/login/] \n\n 4)GET_froms_from_HTML [example url: 'https://facebook.com'] \n\n 5)Directory_enum [url WITHOUT http://] \n\n $: ")

def request(url):
    try:
        return requests.get(url) #This function will get the response code of the url provided 
    except requests.exceptions.ConnectionError: #usuallly there's an exception that happens when there's a connection error so we're telling python to pass if it happenes.
        pass

#Connection to Database
def save_to_database(test_url):
    # Connect to the database
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="pgda",
        user="postgres",
        password="1234conn"
    )
    cursor = conn.cursor()

    # Insert DATA into the table
    cursor.execute("INSERT INTO subdomains (name) VALUES (%s)", (test_url,))
    conn.commit()
    cursor.execute("SELECT * FROM subdomains")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # Close the connection to the database
    cursor.close()
    conn.close()

#Get URL from user input 
args = get_arguments()
user_URL= args.target_url

app = Flask(__name__)

#Crawler
def extract_links_form(url):
    response = request(url)
    return re.findall('(?:href=")(.*?)"', response.content.decode(errors="ignore"))

def crawl(url):
    target_links = []
    href_links = extract_links_form(url)
    for link in href_links:
        link = urlparse.urljoin(url, link)

        if "#" in link:
            link = link.split("#")[0]

        if user_URL in link and link not in target_links:
            target_links.append(link)
            print(link)
            crawl(link)

#directory_enum
def directory_enum(user_URL):
    with open("/home/main/Desktop/python-proj/wordlists/files-and-dirs-wordlist.txt", "r") as wordlist:
        for line in wordlist:
            word = line.strip()
            test_url = user_URL + "/" + word
            response = request(test_url)
            if response:
                save_to_database(test_url)
                print(" [+] Discovered URL -->" + test_url)

# #BruteForcePass #protip do not show passwords on websites
def brute_force_password(user_URL):
    data_dict = {"username": "admin", "password": "", "login": "submit"}
    with open("/home/main/Desktop/python-proj/wordlists/passwords.txt", "r") as wordlist_file:
        for line in wordlist_file:
            word = line.strip()
            data_dict["password"] = word
            response = requests.post(user_URL, data=data_dict)
            if 'Login failed'.encode('utf-8') not in response.content:
                print("[+] Got the password --> " + word)
                save_to_database(word)
                exit()
        print("[-] Reached end of line.")

#Get forms from an html page #this can't be saved and dispalyed into a website because it returns a from html elemnt
def get_form(user_URL):
    response = request(user_URL)
    parsed_html = BeautifulSoup(response.content, 'html5lib')
    forms_list = parsed_html.findAll("form")
    print(forms_list)



#Subdomain enumeration
if user_choice=="1":
    @app.route("/")
    def main():
        subdomains = []
        with open("/home/main/Desktop/python-proj/wordlists/subdomains-wodlist.txt", "r") as wordlist:
            for line in wordlist:
                word = line.strip()
                test_url = "http://" + word + "." + user_URL
                response = request(test_url)
                if response:
                    save_to_database(test_url)
                    subdomains.append(test_url)
        return render_template("index.html", subdomains=subdomains)
    if __name__ == "__main__":
        app.run(debug=True, use_reloader=False)

#Crawler
elif user_choice=="2":
    @app.route("/")
    def mycuntion():
        crawl(user_URL)
        return render_template("index.html", subdomains=subdomains)
    if __name__ == "__main__":
        app.run(debug=True, use_reloader=False)

#bruteForce
elif user_choice=="3":
    brute_force_password(user_URL)
    
#Get froms from html 
elif user_choice=="4":
    get_form(user_URL)

#Directory_enum
elif user_choice=="5":
    directory_enum(user_URL)