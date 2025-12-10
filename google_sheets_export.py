"""
Google Sheets Export Module
Exports crawl results to Google Sheets
"""

import json
import os
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsExporter:
    """Exports crawl results to Google Sheets"""
    
    # Google Sheets API scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    # Your Google Sheet ID (extracted from the shared link)
    SHEET_ID = '1-CTG-z5o9XhLbGy-3SZr5bUF9X0rekKLV0Zw-7DX8xI' 
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize Google Sheets exporter
        
        Args:
            credentials_file: Path to Google service account credentials JSON
        """
        self.credentials_file = credentials_file
        self.service = None
        self.initialize_service()
    
    def initialize_service(self):
        """Initialize Google Sheets API service"""
        try:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(
                    f"Credentials file not found: {self.credentials_file}\n"
                    "Please add your Google service account credentials.json file.\n"
                    "Instructions: https://developers.google.com/sheets/api/quickstart/python"
                )
            
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=creds)
            print("✓ Google Sheets API initialized successfully")
        except Exception as e:
            print(f"Error initializing Google Sheets API: {e}")
            self.service = None
    
    def export_results(self, results: List[Dict[str, Any]], 
                      sheet_name: str = 'Sheet1',
                      append: bool = True) -> bool:
        """
        Export crawl results to Google Sheets
        
        Args:
            results: List of crawl result dictionaries
            sheet_name: Name of the sheet to export to
            append: If True, append to existing data; if False, replace all data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service:
                print("Google Sheets service not initialized")
                return False
            
            if not results:
                print("No results to export")
                return False
            
            # Prepare headers
            headers = [
                'URL',
                'Email',
                'Inquiry Form URL',
                'Company Name',
                'Industry',
                'HTTP Status',
                'Robots Allowed',
                'Last Crawled At',
                'Crawl Status',
                'Error Message'
            ]
            
            # Prepare data rows
            rows = [headers]
            for result in results:
                row = [
                    result.get('url', ''),
                    result.get('email', ''),
                    result.get('inquiryFormUrl', ''),
                    result.get('companyName', ''),
                    result.get('industry', ''),
                    str(result.get('httpStatus', '')),
                    str(result.get('robotsAllowed', '')),
                    result.get('lastCrawledAt', ''),
                    result.get('crawlStatus', ''),
                    result.get('errorMessage', '')
                ]
                rows.append(row)
            
            # Clear existing data if not appending
            if not append:
                self._clear_sheet(sheet_name)
            
            # Write data to sheet
            range_name = f"'{sheet_name}'!A1"
            body = {'values': rows}
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.SHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Exported {len(results)} results to Google Sheets")
            print(f"  Sheet: {sheet_name}")
            print(f"  Updated cells: {result.get('updatedCells', 0)}")
            return True
            
        except HttpError as error:
            print(f"Google Sheets API error: {error}")
            return False
        except Exception as e:
            print(f"Error exporting to Google Sheets: {e}")
            return False
    
    def append_results(self, results: List[Dict[str, Any]], 
                      sheet_name: str = 'Sheet1') -> bool:
        """
        Append crawl results to existing Google Sheets data
        
        Args:
            results: List of crawl result dictionaries
            sheet_name: Name of the sheet to append to
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.service:
                print("Google Sheets service not initialized")
                return False
            
            if not results:
                print("No results to append")
                return False
            
            # Prepare data rows (no headers)
            rows = []
            for result in results:
                row = [
                    result.get('url', ''),
                    result.get('email', ''),
                    result.get('inquiryFormUrl', ''),
                    result.get('companyName', ''),
                    result.get('industry', ''),
                    str(result.get('httpStatus', '')),
                    str(result.get('robotsAllowed', '')),
                    result.get('lastCrawledAt', ''),
                    result.get('crawlStatus', ''),
                    result.get('errorMessage', '')
                ]
                rows.append(row)
            
            # Append data to sheet
            range_name = f"'{sheet_name}'!A:J"
            body = {'values': rows}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.SHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✓ Appended {len(results)} results to Google Sheets")
            print(f"  Sheet: {sheet_name}")
            print(f"  Updated cells: {result.get('updates', {}).get('updatedCells', 0)}")
            return True
            
        except HttpError as error:
            print(f"Google Sheets API error: {error}")
            return False
        except Exception as e:
            print(f"Error appending to Google Sheets: {e}")
            return False
    
    def _clear_sheet(self, sheet_name: str):
        """Clear all data from a sheet"""
        try:
            range_name = f"'{sheet_name}'!A:J"
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.SHEET_ID,
                range=range_name
            ).execute()
            print(f"✓ Cleared existing data in {sheet_name}")
        except Exception as e:
            print(f"Warning: Could not clear sheet: {e}")
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """Get information about the Google Sheet"""
        try:
            if not self.service:
                return {}
            
            result = self.service.spreadsheets().get(
                spreadsheetId=self.SHEET_ID
            ).execute()
            
            sheets = result.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            return {
                'title': result.get('properties', {}).get('title', ''),
                'sheets': sheet_names,
                'url': f'https://docs.google.com/spreadsheets/d/{self.SHEET_ID}/edit'
            }
        except Exception as e:
            print(f"Error getting sheet info: {e}")
            return {}


def export_jsonl_to_sheets(jsonl_file: str, 
                          credentials_file: str = 'credentials.json',
                          sheet_name: str = 'Sheet1',
                          append: bool = False) -> bool:
    """
    Convenience function to export JSONL file to Google Sheets
    
    Args:
        jsonl_file: Path to JSONL results file
        credentials_file: Path to Google service account credentials
        sheet_name: Name of the sheet to export to
        append: If True, append to existing data; if False, replace all
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load results from JSONL file
        results = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        
        if not results:
            print(f"No results found in {jsonl_file}")
            return False
        
        # Export to Google Sheets
        exporter = GoogleSheetsExporter(credentials_file)
        
        if append:
            return exporter.append_results(results, sheet_name)
        else:
            return exporter.export_results(results, sheet_name)
        
    except FileNotFoundError:
        print(f"Results file not found: {jsonl_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSONL file: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == '__main__':
    # Test export
    import sys
    
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
        append_mode = '--append' in sys.argv
        export_jsonl_to_sheets(jsonl_file, append=append_mode)
    else:
        print("Usage: python google_sheets_export.py <jsonl_file> [--append]")
        print("\nExample:")
        print("  python google_sheets_export.py crawl_results.jsonl")
        print("  python google_sheets_export.py crawl_results.jsonl --append")
