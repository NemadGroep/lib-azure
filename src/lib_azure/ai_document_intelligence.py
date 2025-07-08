import logging
from decimal import Decimal
from dateparser import parse
from babel.numbers import parse_decimal
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient, DocumentField

logger = logging.getLogger(__name__)

class FormRecognizer:
    def __init__(self, endpoint: str, key: str, dateformat: str ='%Y%m%d'):
        self.client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        self.dateformat = dateformat

    def analyze_document(self, model_id: str, document: bytes):
        """Calls begin_analyze_document() with specified model on document"""
        try:
            poller = self.client.begin_analyze_document(model_id=model_id, document=document)
            result = poller.result().to_dict()
            return result
        except Exception as e:
            logger.exception("Failed to analyze document with %s", model_id)


    def print_result(self, result: dict):
        """Print the result of analyze_document in readable format"""
        try:
            for page in result.get('pages'):
                fields = page.get('fields', {})
                for field_name, field_data in fields.items():
                    value_type = field_data.get('value_type')
                    value = field_data.get('value')
                    if value_type == 'list':
                        for item in value:
                            value_type = item.get('value_type')
                            value = item.get('value')
                            for field_name, field_data in value.items():
                                value_type = field_data.get('value_type')
                                value = field_data.get('value')
                                content = field_data.get('content')
                                bounding_regions = field_data.get('bounding_regions', [])
                                spans = field_data.get('spans', [])
                                confidence = field_data.get('confidence')
                                print(f"Field Name: {field_name}")
                                print(f"  Value Type: {value_type}")
                                print(f"  Value: {value}")
                                print(f"  Content: {content}")
                                print(f"  Bounding Regions: {bounding_regions}")
                                print(f"  Spans: {spans}")
                                print(f"  Confidence: {confidence}")
                    content = field_data.get('content')
                    bounding_regions = field_data.get('bounding_regions', [])
                    spans = field_data.get('spans', [])
                    confidence = field_data.get('confidence')
                    print(f"Field Name: {field_name}")
                    print(f"  Value Type: {value_type}")
                    print(f"  Value: {value}")
                    print(f"  Content: {content}")
                    print(f"  Bounding Regions: {bounding_regions}")
                    print(f"  Spans: {spans}")
                    print(f"  Confidence: {confidence}")
        except Exception as e:
            logger.exception("Failed to print result")
                    

    def parse_numbers(self, result: dict, locale: str):
        """Parse the numbers in the result of the analysis."""
        try:
            for idx, page in enumerate(result.get('pages')):
                fields = page.get('fields', {})
                for field_name, field_data in fields.items():
                    value_type = field_data.get('value_type')
                    if value_type == 'list':
                        value = field_data.get('value')
                        for idxx, item_line in enumerate(value):
                            for nested_field_name, nested_field_data in item_line.get('value', {}).items():
                                value_type = nested_field_data.get('value_type')
                                if nested_field_data.get('content') is not None: 
                                    value = nested_field_data.get('content').replace(' ', '').replace('%', '').replace('€', '')
                                if value_type == 'float':
                                    if value.find('-') != 0 and value.find('-') != -1:
                                        value = '-' + value.replace('-', '')
                                    value = parse_decimal(value, locale=locale)
                                    result['pages'][idx]['fields'][field_name]['value'][idxx]['value'][nested_field_name]['value']  = Decimal(value)
                                elif value_type == 'integer':
                                    if value.find('-') != 0 and value.find('-') != -1:
                                        value = '-' + value.replace('-', '')
                                    result['pages'][idx]['fields'][field_name]['value'][idxx]['value'][nested_field_name]['value'] = int(value)
                        continue
                    if field_data.get('content') is not None: 
                        value = field_data.get('content').replace(' ', '').replace('%', '').replace('€', '').replace('():', '').replace('hoogtarief,', '21')
                        if value_type == 'float':
                            if value.find('-') != 0 and value.find('-') != -1:
                                value = '-' + value.replace('-', '')
                            value = parse_decimal(value, locale=locale)
                            result['pages'][idx]['fields'][field_name]['value']  = Decimal(value)
                        elif value_type == 'integer':
                            if value.find('-') != 0 and value.find('-') != -1:
                                value = '-' + value.replace('-', '')
                            result['pages'][idx]['fields'][field_name]['value'] = int(value)
            return result
        except Exception as e:
            logger.exception("Failed to parse numbers in the result")
            return result

    def parse_dates(self, result: dict):
        """Processes the dates in the result of the analysis."""
        try:
            for idx, page in enumerate(result.get('pages')):
                fields = page.get('fields', {})
                for field_name, field_data in fields.items():
                    value_type = field_data.get('value_type')
                    if value_type == 'list':
                        value = field_data.get('value')
                        for idxx, item_line in enumerate(value):
                            for nested_field_name, nested_field_data in item_line.get('value', {}).items():
                                value_type = nested_field_data.get('value_type')
                                value = nested_field_data.get('content')
                                if value_type == 'date':
                                    result['pages'][idx]['fields'][field_name]['value'][idxx]['value'][nested_field_name]['value'] = parse(value).strftime(self.dateformat)
                        continue
                    value = field_data.get('content')
                    if value_type == 'date' and value is not None:
                        result['pages'][idx]['fields'][field_name]['value'] = parse(value).strftime(self.dateformat)
            return result
        except Exception as e:
            logger.exception("Failed to parse dates in the result")
            return result

    def extract_kv_pairs(self, result: dict):
        """Extract only key-value pairs from analyze_document() result"""
        try:
            kv_pairs = {}
            for page in result.get('pages'):
                fields = page.get('fields', {})
                for field_name, field_data in fields.items():
                    value_type = field_data.get('value_type')
                    value = field_data.get('value')
                    kv_pairs[field_name] = value
                    if value_type == 'list':
                        kv_pairs[field_name] = []
                        for idx, item_line in enumerate(value):
                            kv_pairs[field_name].append({})
                            for nested_field_name, nested_field_data in item_line.get('value', {}).items():
                                nested_value = nested_field_data.get('value')
                                kv_pairs[field_name][idx][nested_field_name] = nested_value
            return kv_pairs
        except Exception as e:
            logger.exception("Failed to extract key-value pairs from the result")
            return {}

