import re
import requests
from bs4 import BeautifulSoup


def scrape_html_standard(url):
    """
    Scrapes and cleans HTML content from a standard website.

    Parameters:
    - url: URL of the website to scrape

    Returns:
    - Cleaned and extracted main text content as a string
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.decompose()

        main_content = soup.find("div", class_="single-content") or soup
        raw_text = main_content.get_text(separator=" ", strip=True)
        full_text = re.sub(r'\s+', ' ', raw_text)

        start_patterns = [r"§\s?\d+", r"1\.\s+[^\n\.]+"]
        for pattern in start_patterns:
            match = re.search(pattern, full_text)
            if match:
                full_text = full_text[match.start():]
                break

        end_markers = [
            "Die eingetragene Marke MOCO", "Stand 12/2024", "Ort, Datum",
            "Unterschrift", "Impressum", "©", "Nachtrag Australische spezifische Begriffe"
        ]
        cutoff = int(len(full_text) * 0.7)
        positions = {m: full_text.find(m) for m in end_markers if full_text.find(m) > cutoff}
        if positions:
            full_text = full_text[:min(positions.values())]

        return full_text.strip()

    except Exception:
        return ""


def scrape_html_commonpaper(url):
    """
    Scrapes and processes HTML content from CommonPaper contract pages.

    Parameters:
    - url: URL of the CommonPaper contract

    Returns:
    - Structured contract content as a string with numbered sections
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="entry-content")
        if not content:
            print(f"⚠️ CommonPaper: No main content found – {url}")
            return ""

        result = []

        def walk_list(ol, prefix=""):
            items = ol.find_all("li", recursive=False)
            for idx, li in enumerate(items, 1):
                number = f"{prefix}.{idx}" if prefix else str(idx)
                li_copy = BeautifulSoup(str(li), "html.parser")
                for sublist in li_copy.find_all("ol"):
                    sublist.decompose()
                text = li_copy.get_text(separator=" ", strip=True)
                result.append(f"{number}. {text}")

                sub_ol = li.find("ol")
                if sub_ol:
                    walk_list(sub_ol, number)

        top_ol = content.find("ol")
        if top_ol:
            walk_list(top_ol)
        else:
            print("⚠️ No <ol> found!")

        return "\n".join(result)

    except Exception as e:
        print(f"Error scraping CommonPaper: {e}")
        return ""


def scrape_html_fakturia(url):
    """
    Scrapes and processes HTML content from Fakturia contract pages.

    Parameters:
    - url: URL of the Fakturia contract

    Returns:
    - Structured and cleaned text content with sections and paragraphs
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="entry-content-wrapper")
        if not content:
            print("⚠️ Fakturia: No main content found.")
            return ""

        result = []
        section = ""

        for elem in content.find_all(["h2", "p"]):
            text = re.sub(r'\s+', ' ', elem.get_text(separator=" ", strip=True))

            if elem.name == "h2":
                if section:
                    result.append(section.strip())
                section = text + "\n"
            elif elem.name == "p":
                if re.match(r'^\d+\.\d+', text):
                    section += text + " "
                else:
                    section += text + "\n"

        if section:
            result.append(section.strip())

        for marker in ["Copyright OSB Alliance e.V.", "gemäß CC BY", "Version 1/2015"]:
            if marker in result[-1]:
                result[-1] = result[-1].split(marker)[0].strip()
                break

        return "\n\n".join(result)

    except Exception as e:
        print(f"Error scraping Fakturia: {e}")
        return ""


def scrape_html_mitratech(url):
    """
    Scrapes and processes HTML content from Mitratech or Alyne contract pages.

    Parameters:
    - url: URL of the Mitratech or Alyne contract

    Returns:
    - Cleaned and structured text content starting from main sections
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "form", "noscript"]):
            tag.decompose()

        main = soup.find("main") or soup
        found = False
        blocks = []

        for el in main.find_all(["h1", "h2", "h3", "p", "li", "ol", "ul"]):
            text = el.get_text(separator=" ", strip=True)
            if not text:
                continue

            if not found and text.startswith("1. Allgemeines"):
                found = True
                blocks.append(text)
                continue

            if found and el.name in ["h1", "h2", "h3"] and "Begriffsbestimmungen" in text:
                break

            if found:
                blocks.append(text)

        return "\n\n".join(blocks).strip()

    except Exception as e:
        print(f"Error scraping Mitratech: {e}")
        return ""


def scrape_contract_auto(url):
    """
    Automatically selects and uses the appropriate scraping function based on the URL.

    Parameters:
    - url: The URL of the contract

    Returns:
    - Scraped and processed contract text as a string
    """
    url_lc = url.lower()
    if "commonpaper.com" in url_lc:
        return scrape_html_commonpaper(url)
    elif "fakturia.de" in url_lc:
        return scrape_html_fakturia(url)
    elif "mitratech.com" in url_lc or "alyne.com" in url_lc:
        return scrape_html_mitratech(url)
    else:
        return scrape_html_standard(url)


def read_txt_file(file_path):
    """
    Reads the content of a .txt file.

    Parameters:
    - file_path: Path to the .txt file

    Returns:
    - File content as a string, or an empty string if an error occurs
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""
