from multiprocessing import Pool
import bs4 as bs
import random
import string
import requests


def random_starting_url():
    starting = "".join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(3))
    url = "".join(["http://www.", starting, ".com"])
    return url


def handle_local_links(url, link):
    if link.startswith("/"):
        return "".join([url, link])
    else:
        return str(link)


def get_links(url):
    try:
        response = requests.get(url)
        b_soup_content = bs.BeautifulSoup(response.text, 'lxml')
        body = b_soup_content.body
        links = [link.get("href") for link in body.find_all("a")]
        links = [handle_local_links(url, link) for link in links]
        links = [str(link.encode("ascii")) for link in links]
        return links
    except TypeError as e:
        print("Error", e)
        return []
    except IndexError as e:
        print(e)
        return []
    except AttributeError as e:
        print(e)
        return []
    except Exception as e:
        print(e)
        return []


def main():
    how_many = 15
    pool_processes = Pool(processes=how_many)
    parse_urls = [random_starting_url() for _ in range(how_many)]
    data = pool_processes.map(get_links, [link for link in parse_urls])
    data = [url for url_list in data for url in url_list]
    pool_processes.close()

    with open("urls.html", "w") as f:
        f.write("<h6>{}</h6>".format(str(data)))


if __name__ == "__main__":
    main()
