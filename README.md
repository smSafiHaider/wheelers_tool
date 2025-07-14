# Wheeler's Books ISBN Scraper

A Python GUI application for scraping book information from Wheeler's Books website using ISBN numbers. The application provides a user-friendly interface for bulk scraping book data, downloading cover images, and exporting results to various formats.

## Features

- **Bulk ISBN Processing**: Load ISBN lists from CSV or Excel files
- **Comprehensive Data Extraction**: Scrapes detailed book information including:
  - Basic info (title, author, publisher, ISBN)
  - Publication details (published date, language, series)
  - Physical properties (page count, dimensions, weight)
  - Pricing and availability
  - Categories and descriptions
  - Alternate format information
- **Image Download**: Optional book cover image downloading with organized file naming
- **Database Integration**: Save scraped data directly to MySQL database
- **Export Options**: Export data to CSV or Excel formats
- **Real-time Progress Tracking**: Live progress updates and detailed logging
- **Error Handling**: Robust error handling with detailed error reporting

## Requirements

### Python Version
- Python 3.7 or higher

### Dependencies
```
tkinter (usually included with Python)
requests
beautifulsoup4
pandas
sqlalchemy
pymysql
pillow
openpyxl
```

## Installation

1. **Clone or download** the application files

2. **Install required packages**:
   ```bash
   pip install requests beautifulsoup4 pandas sqlalchemy pymysql pillow openpyxl
   ```

3. **Run the application**:
   ```bash
   python scrapper.py
   ```

## Usage

### 1. Prepare Your ISBN File

Create a CSV or Excel file containing ISBN numbers:
- The file should have a column named "ISBN" (case-insensitive)
- If no "ISBN" column is found, the first column will be used
- Each row should contain one ISBN number

Example CSV format:
```csv
ISBN
9780123456789
9780987654321
9781234567890
```

### 2. Configure Database Settings (Optional)

If you want to save data to a MySQL database:

1. Go to the **Database Settings** tab
2. Enter your MySQL connection details:
   - Host (default: localhost)
   - Port (default: 3306)
   - Database name
   - Username
   - Password
3. Click **Test Connection** to verify settings
4. Click **Save Settings** to store configuration

### 3. Run the Scraper

1. **Select Input File**: Click "Select CSV/Excel File" and choose your ISBN file
2. **Configure Options**:
   - Check "Download Book Images" if you want to download cover images
   - Choose images folder location if downloading images
   - Check "Save to Database" if you want to save to MySQL
3. **Start Scraping**: Click "Start Scraping" to begin the process
4. **Monitor Progress**: Watch the progress bar and log for real-time updates

### 4. Export Results

After scraping is complete:
- Click **Export to CSV** to save data as a CSV file
- Click **Export to Excel** to save data as an Excel file

## Data Fields Extracted

The scraper extracts the following information for each book:

### Basic Information
- ISBN
- Title
- Author
- Illustrator
- Publisher
- Published date
- Language
- Series
- Price

### Extended Details
- Publication country
- Edition
- Imprint
- Page count
- Dimensions
- Weight
- Interest age
- Reading age
- AR level
- Premier's Reading Challenge status

### Classification
- Dewey Code
- Library of Congress
- Categories
- NBS Text
- Onix Text

### Alternate Formats
- Alternate edition
- Alternate ISBN
- Alternate publication date
- Alternate price

### Images and Metadata
- Image URL
- Local image path (if downloaded)
- Full description
- Scraped timestamp

## File Structure

```
wheelers_scraper/
├── scrapper.py          # Main application
├── db_config.json               # Database configuration (auto-generated)
├── book_images/                 # Downloaded images folder (default)
│   ├── 9780123456789_BookTitle.jpg
│   └── 9780987654321_AnotherBook.jpg
└── README.md                    
```

## Configuration Files

### Database Configuration (`db_config.json`)
Automatically created and managed through the GUI:
```json
{
  "host": "localhost",
  "port": "3306",
  "database": "books_db",
  "username": "root",
  "password": ""
}
```

## Database Schema

If using database storage, the application creates a table named `wheelers_books` with columns corresponding to all extracted data fields.

## Error Handling

The application includes comprehensive error handling:
- **Network errors**: Timeout and connection issues
- **File format errors**: Invalid CSV/Excel files
- **Database errors**: Connection and query issues
- **Image download errors**: Invalid or inaccessible images
- **Parsing errors**: Missing or malformed data on web pages

All errors are logged in the application log with timestamps for debugging.

## Performance Notes

- The scraper includes a 30-second timeout for each request
- Images are verified after download to ensure validity
- Progress is updated in real-time
- Memory usage is optimized for large ISBN lists
- Failed requests are logged but don't stop the entire process

## Troubleshooting

### Common Issues

1. **"No file selected" error**
   - Ensure you've selected a valid CSV or Excel file
   - Check that the file contains ISBN numbers

2. **Database connection failed**
   - Verify MySQL server is running
   - Check connection credentials in Database Settings
   - Ensure the database exists

3. **Image download failures**
   - Check internet connection
   - Verify write permissions to images folder
   - Some images may be protected or unavailable

4. **Scraping errors**
   - Website structure may have changed
   - Network connectivity issues
   - Invalid ISBN numbers in input file

### Getting Help

- Check the application log for detailed error messages
- Verify all dependencies are installed correctly
- Ensure you have proper permissions for file and database operations

## Legal Considerations

- This tool is for educational and research purposes
- Respect Wheeler's Books terms of service
- Use reasonable delays between requests
- Don't overload their servers with excessive concurrent requests

## Version Information

- **Version**: 1.0
- **Python Compatibility**: 3.7+
- **GUI Framework**: tkinter
- **Last Updated**: 2025

## License

This software is provided as-is for educational purposes. Users are responsible for complying with all applicable laws and website terms of service.
