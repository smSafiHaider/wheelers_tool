from bs4 import BeautifulSoup
from datetime import datetime


def extract_book_info(html):

        try:

            soup = BeautifulSoup(html, "html.parser")

            # ------------------------------------------------------------------ #
            # Helpers                                                            #
            # ------------------------------------------------------------------ #
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

            # ------------------------------------------------------------------ #
            # Category breadcrumbs                                               #
            # ------------------------------------------------------------------ #
            categories = [
                a.get_text(strip=True)
                for a in soup.select("div.product-description a[href*='/category/']")
            ]
            categories_text = ", ".join(categories) if categories else None

            # ------------------------------------------------------------------ #
            # Cover image                                                        #
            # ------------------------------------------------------------------ #
            image_url = None
        
            img_el = soup.select_one("img.cover")
            if img_el and img_el.get("src"):
                image_url = img_el["src"]
                src = img_el["src"]

                # make it absolute
                if src.startswith("//"):            # protocol-relative (//r.wheelers…)
                    src = "https:" + src
                else:                               # relative → join to page origin
                    src = urljoin(url, src)

                image_url = src

            # ------------------------------------------------------------------ #
            # Build dict                                                         #
            # ------------------------------------------------------------------ #
            book_data = {
                # Identifiers ---------------------------------------------------
                "isbn": grab("ISBN:"),
                "isbn_text": grab("ISBN:"),
                "title": grab("Title") or safe_text("h1.title"),
                "author": grab("Author") or safe_text("div.author a[href*='/author/']"),
                "illustrator": safe_text("div.author div:nth-of-type(2) a.link"),
                # Publication ---------------------------------------------------
                "publisher": grab("Publisher:") or grab("Publisher"),
                "published": grab("Published:"),
                "published_imported": grab("Published (Imported):"),
                "replaced_by": grab("Replaced by:"),
                "language": grab("Language:"),
                "series": grab("Series:") or safe_text("span.series a"),
                "interest_age": grab("Interest age:"),
                "ar_level": grab("AR:"),
                "premiers_reading_challenge": grab("Premier's Reading Challenge:"),
                "imprint": grab("Imprint"),
                "publication_country": grab("Publication Country"),
                "edition": grab("Edition"),
                # Physical / meta -----------------------------------------------
                "page_count": grab("Number of pages"),
                "dimensions": grab("Dimensions"),
                "weight": grab("Weight"),
                "dewey_code": grab("Dewey Code"),
                "reading_age": grab("Reading Age"),
                "library_of_congress": grab("Library of Congress"),
                "nbs_text": grab("NBS Text"),
                "onix_text": grab("Onix Text"),
                # Alternates -----------------------------------------------------
                "alternate_edition": grab("Alternate edition"),
                "alternate_isbn": grab("Alternate ISBN"),
                "alternate_isbn_pub_date": grab("Alternate ISBN pub date"),
                "alternate_isbn_price": grab("Alternate ISBN Price"),
                # Misc -----------------------------------------------------------
                "price": grab("Price"),
                "full_description": grab("Full Description") or safe_text("div.description"),
                "categories": categories_text,
                "image_url": image_url,
                "scraped_at": datetime.now().isoformat(),
            }

            return book_data

        except Exception as exc:
            # Bubble up a clean message
            return {"error": str(exc)}
        
with open('9780008696047', 'r') as f:

    print(extract_book_info(f))