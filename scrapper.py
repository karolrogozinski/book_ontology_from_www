import requests
from bs4 import BeautifulSoup
import numpy as np

DOMAIN_URL = 'https://lubimyczytac.pl'
CATEGORIES_URL = 'https://lubimyczytac.pl/ksiazki/kategorie'


def get_categories(categories_url: str = CATEGORIES_URL) -> list:
    """
    returns 4 lists:
    - main categories names
    - main categories urls
    - sub categories names
    - sub categories urls
    """

    page = requests.get(categories_url)
    soup = BeautifulSoup(page.content, "html.parser")

    main_cats = soup.find_all('div', class_='container categoryCategories__bg')
    main_cats_cut = [cat.find('div', class_='categoryCategories__title')
                     for cat in main_cats]
    main_cats_names = [cat.text.strip() for cat in main_cats_cut]
    main_cats_urls = [cat.find('a').get("href") for cat in main_cats_cut]

    sub_cats = [cat.find('div', class_='categoryCategories__list')
                for cat in main_cats]
    sub_cats = [item_list.find_all('a', class_='categoryCategories__listItem')
                for item_list in sub_cats]
    sub_cats_names = [[cat.text for cat in cat_list] for cat_list in sub_cats]
    sub_cats_urls = [[DOMAIN_URL+item.get("href") for item in itemlist]
                     for itemlist in sub_cats]

    return main_cats_names, main_cats_urls, sub_cats_names, sub_cats_urls
    # categories_dict = {}
    # for main_category, sub_categories_list, sub_urls in zip(main_categories_names, sub_categories_names, sub_categories_urls):
    #     categories_dict[main_category] = dict(zip(sub_categories_list, sub_urls))


def book_dict(book_link: str) -> dict:
    """
    Creating a dict with properties of a book, containing:
    - title,
    - author,
    - author_url,
    - page_number,
    - reading_mins,
    - category,
    - category_url,
    - publisher,
    - series,
    - rating,
    - description.
    """

    book_url = DOMAIN_URL + book_link
    page = requests.get(book_url)
    soup = BeautifulSoup(page.content, "html.parser")

    # title
    title = soup.find('h1', class_="book__title").text.strip()

    # author info
    author = soup.find('a', class_='link-name d-inline-block')
    author_text = author.text.strip()
    author_url = author.get("href")

    try:
        # page number
        page_number = int(soup.find('span', class_='book-pages')
                          .text.replace('str.', '').strip())

        # reading time (equal to page number in minutes)
        time_info_spans = soup.find_all('span', class_='time-info-small')
        numbers = [int(span.previous_sibling.strip())
                   for span in time_info_spans
                   if span.previous_sibling
                   and span.previous_sibling.strip().isdigit()]
        if numbers[0] and numbers[1]:
            time = numbers[0]*60 + numbers[1]
        elif numbers[0]:
            time = numbers[0]*60
        else:
            time = np.nan
    except:
        page_number = np.nan
        time = np.nan

    # publisher
    publisher_span = soup.find('span',
                               class_='book__txt d-block d-xs-none mt-2 mb-3')
    if publisher_span is None:
        publisher_span = soup.find('span',
                                   class_='book__txt d-block d-xs-none mt-2')
    publisher = publisher_span.find('a').text.strip()

    # series
    series_span = soup.find('span', class_='d-none d-sm-block mt-1')
    if series_span:
        series = series_span.find('a').text.strip()
    else:
        series = ''

    # category info
    category = soup.find('a', class_='book__category')
    category_class = category.text.strip()
    category_url = DOMAIN_URL+category.get("href")

    # rating
    rating_div = soup.find('div', class_='rating-value')
    span_content = rating_div.find('span', class_='big-number')
    rating = float(span_content.text.strip().replace(',', '.'))

    # description
    description = soup.find('div', id='book-description')
    desc_paragraph = description.find('p')
    description_text = desc_paragraph.text

    book_dict = {
        'title'       : title,
        'author'      : author_text,
        'author_url'  : author_url,
        'page_number' : page_number,
        'reading_mins': time,
        'category'    : category_class,
        'category_url': category_url,
        'publisher'   : publisher,
        'series'      : series,
        'rating'      : rating,
        'description' : description_text
    }

    return book_dict


def book_pages_from_cat_urls(num_categories=None) -> list:
    books_pages = []
    _, _, _, sub_cats_urls = get_categories()

    if num_categories and num_categories < len(sub_cats_urls):
        sub_cats_urls = sub_cats_urls[:num_categories]

    for cat in sub_cats_urls:
        for subcat in cat:
            page = requests.get(subcat)
            soup = BeautifulSoup(page.content, "html.parser")
            url = soup.find('a', class_='btn btn-primary').get("href")
            books_pages.append(url)
    return books_pages


def books_urls(book_number: int = 3, num_categories: int = None) -> list:
    books_urls = []
    books_pages = book_pages_from_cat_urls(num_categories=num_categories)

    for link in books_pages:
        # finding all books urls on a page
        page = requests.get(link)
        soup = BeautifulSoup(page.content, "html.parser")

        links = soup.find_all("a", class_='authorAllBooks__singleTextTitle')
        links_to_books = [str(link.get("href")) for link in links 
                          if str(link.get("href")).find('/ksiazka') != -1]
        books_urls.extend(links_to_books[:book_number])

    return books_urls


def create_books_dicts(books_urls: list) -> list:
    return [book_dict(link) for link in books_urls]
