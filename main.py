from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from dateutil.tz import gettz
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
# import functions_framework


# Change to hp_deadline_fighter_main(cloud_event) and uncomment the functions_framework rows when deploy
# @functions_framework.cloud_event
def hp_deadline_fighter_main():

    # Set up calendar

    JST = gettz('Asia/Tokyo')

    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )

    service = build(
        "calendar", "v3", credentials=credentials, cache_discovery=False
    )

    # Set up Soup

    URL = "https://www.elineupmall.com/helloproject-fc"

    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    link_container = soup.find('div', {'class': 'ty-sidebox-important artist menu'})

    for i in link_container.find_all('a', {'class': 'ty-menu__item-link'}, href=True):
            
            try:

        
                page2 = requests.get(i['href'])

                soup2 = BeautifulSoup(page2.content, "html.parser")

                # Find deadline

                deadline_content = str(soup2.find_all('p')[2])

                deadline_tag = "受付締切日："
                deadline_tag_position = deadline_content.find(deadline_tag)
                deadline_start_position = deadline_tag_position + 6
                deadline_end_position = deadline_content.split(deadline_tag)[1].find("<")

                deadline_string = deadline_content[deadline_tag_position+6:deadline_start_position+deadline_end_position]


                # Find title

                product_title_string = soup2.find_all('span', {"class": "ty-mainbox-title__left"})[0].text
                print('Product: ' + product_title_string)

                # Parse deadline

                deadline_string_western = deadline_string.strip().replace('（月）', ' ').replace('（火）', ' ').replace('（水）', ' ').replace('（木）', ' ').replace('（金）', ' ').replace('（土）', ' ').replace('（日）', ' ').replace('：', ':')
                deadline_datetime = datetime.strptime(deadline_string_western, "%Y年%m月%d日 %H:%M").replace(tzinfo=JST)
                deadline_datetime_plus_one_min = deadline_datetime + timedelta(minutes=1)



                # Find events at the same time

                events_list = (
                        service.events()
                        .list(
                            calendarId=os.environ["CALENDAR_EMAIL"],
                            timeMin=deadline_datetime.isoformat(),
                            timeMax=deadline_datetime_plus_one_min.isoformat(),
                            singleEvents=True,
                            orderBy="startTime",
                        )
                .execute()
                )

                events = events_list.get("items", [])


                if not events:
                    print('No event in time slot')

                    event = {
                        'summary': product_title_string,
                        'start': {
                            'dateTime': deadline_datetime.isoformat(),
                        },
                        'end': {
                            'dateTime': deadline_datetime_plus_one_min.isoformat(),
                            }
                    }

                    event = service.events().insert(calendarId=os.environ["CALENDAR_EMAIL"], body=event).execute()
                    print('Event created at ' + str(deadline_datetime))

                elif any(event['summary'] == product_title_string for event in events) is False:
                    print('There are events with different name')
                    event = {
                        'summary': product_title_string,
                        'start': {
                            'dateTime': deadline_datetime.isoformat(),
                        },
                        'end': {
                            'dateTime': deadline_datetime_plus_one_min.isoformat(),
                        }
                    }

                    event = service.events().insert(calendarId=os.environ["CALENDAR_EMAIL"], body=event).execute()
                    print('Event ' + product_title_string + ' is created')
                else:
                    print('Event '  + product_title_string + ' already exist')
            
            except Exception as e:
                 print(e)
                 pass
                 
    return 

