from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests


def extract_book_info(isbn):
    """Extract book information from Wheeler's website (robust to quotes)."""
    base_url = "https://www.wheelersbooks.com.au/product/"
    url = base_url + isbn

    try:
        res = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible)"},
            timeout=30,
        )
        if res.status_code != 200:
            return {"isbn": isbn, "error": f"HTTP {res.status_code}"}

        soup = BeautifulSoup(res.text, "html.parser")

        def safe_text(selector: str):
            el = soup.select_one(selector)
            return el.get_text(strip=True) if el else None

        def _row_selector(label_text: str) -> str:
            safe = label_text.replace('"', '\\"')
            return f'div.row:has(label:contains("{safe}")) span'

        def _table_selector(label_text: str) -> str:
            safe = label_text.replace('"', '\\"')
            return f'tr:has(th:contains("{safe}")) td'

        def grab(label: str):
            return safe_text(_row_selector(label)) or safe_text(_table_selector(label))

        def extract_single_book_data(soup_obj, isbn_val, base_url_val):
            """Extract book data from a BeautifulSoup object."""
            categories = [
                a.get_text(strip=True)
                for a in soup_obj.select("div.product-description a[href*='/category/']")
            ]
            categories_text = ", ".join(categories) if categories else None

            image_url = None
            img_el = soup_obj.select_one("img.cover")   
            if img_el and img_el.get("src"):
                src = img_el["src"]

                # make it absolute
                if src.startswith("//"):            
                    src = "https:" + src
                else:                               
                    src = urljoin(base_url_val, src)

                image_url = src

            # Use local grab function that works with the passed soup object
            def local_grab(label: str):
                def local_safe_text(selector: str):
                    el = soup_obj.select_one(selector)
                    return el.get_text(strip=True) if el else None
                
                return local_safe_text(_row_selector(label)) or local_safe_text(_table_selector(label))
            
            return {
                # Identifiers ---------------------------------------------------
                "isbn": isbn_val,
                "isbn_text": local_grab("ISBN:"),
                "title": local_grab("Title") or safe_text("h1.title"),
                "author": local_grab("Author") or safe_text("div.author a[href*='/author/']"),
                "illustrator": safe_text("div.author div:nth-of-type(2) a.link"),
                # Publication ---------------------------------------------------
                "publisher": local_grab("Publisher:") or local_grab("Publisher"),
                "published": local_grab("Published:"),
                "published_imported": local_grab("Published (Imported):"),
                "replaced_by": local_grab("Replaced by:"),
                "language": local_grab("Language:"),
                "series": local_grab("Series:") or safe_text("span.series a"),
                "interest_age": local_grab("Interest age:"),
                "ar_level": local_grab("AR:"),
                "premiers_reading_challenge": local_grab("Premier's Reading Challenge:"),
                "imprint": local_grab("Imprint"),
                "publication_country": local_grab("Publication Country"),
                "edition": local_grab("Edition"),
                # Physical / meta -----------------------------------------------
                "page_count": local_grab("Number of pages"),
                "dimensions": local_grab("Dimensions"),
                "weight": local_grab("Weight"),
                "dewey_code": local_grab("Dewey Code"),
                "reading_age": local_grab("Reading Age"),
                "library_of_congress": local_grab("Library of Congress"),
                "nbs_text": local_grab("NBS Text"),
                "onix_text": local_grab("Onix Text"),
                # Misc -----------------------------------------------------------
                "price": local_grab("Price"),
                "full_description": local_grab("Full Description") or safe_text("div.description"),
                "categories": categories_text,
                "image_url": image_url,
                "scraped_at": datetime.now().isoformat(),
            }

        def get_alternate_data():
            """Extract alternate format data from the current page."""
            alternate_data = []
            all_alt_formats_section = soup.select('#allAltFormats ul li a[href*="/product/"]')
            
            for link in all_alt_formats_section:
                href = link.get('href')
                if href and href != url:  # Don't include current page
                    # Make absolute URL
                    if href.startswith('/'):
                        href = 'https://www.wheelersbooks.com.au' + href

                    try:
                        alt_res = requests.get(
                            href,
                            headers={"User-Agent": "Mozilla/5.0 (compatible)"},
                            timeout=30,
                        )
                        if alt_res.status_code != 200:
                            continue  # Skip this alternate, don't fail entire function

                        alt_soup = BeautifulSoup(alt_res.text, "html.parser")
                        
                        # Create local_grab function for alternate soup
                        def alt_local_grab(label: str):
                            def alt_local_safe_text(selector: str):
                                el = alt_soup.select_one(selector)
                                return el.get_text(strip=True) if el else None
                            
                            return alt_local_safe_text(_row_selector(label)) or alt_local_safe_text(_table_selector(label))
                        
                        # Extract only the 4 alternate fields
                        alt_data = {
                            "alternate_edition": alt_local_grab("Edition"),
                            "alternate_isbn": alt_local_grab("ISBN:"),
                            "alternate_isbn_pub_date": alt_local_grab("Published:"),
                            "alternate_isbn_price": alt_local_grab("Price"),
                        }
                        
                        alternate_data.append(alt_data)
                        
                    except Exception as e:
                        # Log the error but continue processing other alternates
                        print(f"Error processing alternate format {href}: {e}")
                        continue
            
            return alternate_data

        # Extract main book data
        book_data = extract_single_book_data(soup, isbn, url)
        
        # Extract alternate formats
        alternates = get_alternate_data()
        
        # Add alternates to the main book data
        book_data["alternates"] = alternates

        return book_data

    except Exception as exc:
        # Bubble up a clean message
        return {"isbn": isbn, "error": str(exc)}
    

if __name__ == "__main__":
    res = extract_book_info("9780300186116")
    print(res)