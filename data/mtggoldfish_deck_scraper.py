# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 01:55:46 2023

@author: curti
"""

from urllib.request import Request, urlopen
from lxml import html
from tqdm import tqdm
import json

headers={'User-Agent': 'Mozilla/5.0'}

def scrape_goldfish(search_start, search_end, search_format, tournament_name):
    page_num = 1
    carddict = {}
    reldict = {}
    while True:
        page_url = ''.join(['https://www.mtggoldfish.com/tournament_searches/',
                            'create?commit=Search&page=',
                            str(page_num),
                            '&tournament_search%5B',
                            'date_range%5D=',
                            search_start[0],
                            '%2F',
                            search_start[1],
                            '%2F',
                            search_start[2],
                            '+-+',
                            search_end[0],
                            '%2F',
                            search_end[1],
                            '%2F',
                            search_end[2],
                            '&tournament_search%5Bformat%5D=',
                            search_format.lower(),
                            '&tournament_search%5Bname%5D=&utf8=%E2%9C%93'])
        page_req = Request(page_url, headers = headers)
        webpage = urlopen(page_req)
        pagetree = html.fromstring(str(webpage.read()))
        items = pagetree.xpath('//tr/td/a')
        if len(items) == 0:
            break
        for item in items:
            if tournament_name not in item.text:
                continue
            event_link = 'https://www.mtggoldfish.com/' + item.get('href')
            event_req = Request(event_link, headers=headers)
            webevent = urlopen(event_req)
            eventtree = html.fromstring(str(webevent.read()))
            decktable = eventtree.xpath('//table[contains(@class, "table-tournament")]/tr/td/a[contains(@href, "/deck/")]/@href')
            for deck_link in decktable:
                deck_url = 'https://www.mtggoldfish.com' + deck_link
                deck_req = Request(deck_url, headers=headers)
                webdeck = urlopen(deck_req)
                decktree = html.fromstring(str(webdeck.read()))
                decklist = decktree.xpath('//div[contains(@class,"deck-table-container")]/table[contains(@class, "deck-view-deck-table")]')[0]
                deckcards = {}
                for tr in decklist.getchildren()[:-1]:
                    trclass = tr.get('class')
                    if trclass is not None and 'deck-category-header' in trclass:
                        card_type = tr.getchildren()[0].text.split('\\n')[1]
                        if card_type[-1] == 's':
                            card_type = card_type[:-1]
                    else:
                        if card_type in ['Sideboard', 'Land']:
                            continue
                        qty = int(tr.getchildren()[0].text.replace('\\n', ''))
                        name = tr.getchildren()[1].xpath('./span/a')[0].text
                        carddict[name] = carddict.get(name, {'count': 0,
                                                             'total': 0,
                                                             'type': None})
                        carddict[name]['count'] += 1
                        carddict[name]['total'] += qty
                        carddict[name]['type'] = card_type
                        deckcards[name] = {'qty': qty}
                cardlist = list(deckcards)
                for i in range(len(cardlist)-1):
                    for j in range(i+1, len(cardlist)):
                        relkey = tuple(sorted((cardlist[i], cardlist[j])))
                        ikey = relkey[0]
                        jkey = relkey[1]
                        reldict[relkey] = reldict.get(relkey, {'count': 0,
                                                               'total': 0})
                        reldict[relkey]['count'] += 1
                        reldict[relkey]['total'] += deckcards[ikey]['qty']*deckcards[jkey]['qty']
        page_num += 1
    return carddict, reldict

search_param_sets = {'standard': {'search_start': ['09', '06', '2023'],
                                  'search_end': ['09', '20', '2023'],
                                  'search_format': 'Standard',
                                  'tournament_name': 'Standard Challenge'},
                     'pioneer': {'search_start': ['09', '06', '2023'],
                                 'search_end': ['09', '20', '2023'],
                                 'search_format': 'Pioneer',
                                 'tournament_name': 'Pioneer Challenge'},
                     'modern': {'search_start': ['09', '06', '2023'],
                                'search_end': ['09', '20', '2023'],
                                'search_format': 'Modern',
                                'tournament_name': 'Modern Challenge'},
                     'legacy': {'search_start': ['09', '06', '2023'],
                                'search_end': ['09', '20', '2023'],
                                'search_format': 'Legacy',
                                'tournament_name': 'Legacy Challenge'},
                     'pauper': {'search_start': ['09', '06', '2023'],
                                'search_end': ['09', '20', '2023'],
                                'search_format': 'Pauper',
                                'tournament_name': 'Pauper Challenge'}}
cards_main = {}
rels_main = {}
for param_set in tqdm(search_param_sets.values()):
    mtg_format = param_set['search_format']
    cards, rels = scrape_goldfish(**param_set)
    for card in cards:
        cards_main[card] = cards_main.get(card, {'count': {},
                                                 'total': {},
                                                 'type': None})
        cards_main[card]['count'][mtg_format] = cards_main[card]['count'].get(mtg_format, 0) + cards[card]['count']
        cards_main[card]['total'][mtg_format] = cards_main[card]['total'].get(mtg_format, 0) + cards[card]['total']
        cards_main[card]['type'] = cards[card]['type']
    rels_main[mtg_format] = rels_main.get(mtg_format, {})
    for rel in rels:
        rels_main[mtg_format][rel] = rels_main[mtg_format].get(rel, {'count': 0,
                                                                     'total': 0})
        rels_main[mtg_format][rel]['count'] += rels[rel]['count']
        rels_main[mtg_format][rel]['total'] += rels[rel]['total']
for card in cards_main:
    cards_main[card]['count']['All'] = sum([val for val in cards_main[card]['count'].values()])
    cards_main[card]['total']['All'] = sum([val for val in cards_main[card]['total'].values()])
rels_main_all = {}
for f in rels_main:
    for rel in rels_main[f]:
        rels_main_all[rel] = rels_main_all.get(rel, {'count': 0,
                                                     'total': 0})
        rels_main_all[rel]['count'] += rels_main[f][rel]['count']
        rels_main_all[rel]['total'] += rels_main[f][rel]['total']
rels_main['All'] = rels_main_all


with open('C:\\Git\\mtg-cluster\\data\\cards.json', 'w') as f:
    json.dump(cards_main, f)
    
#Necessary to do this to maintain tuples as keys for the relationships as json does not allow this
def remap_keys(mapping):
    return[{'key': k, 'value': v} for k,v in mapping.items()]    
    
with open('C:\\Git\\mtg-cluster\\data\\rels.json', 'w') as f:
    json.dump({key: remap_keys(value) for key, value in rels_main.items()}, f)