import os
import json
import boto3
from datetime import datetime
from decimal import Decimal
import re

# Initialize AWS clients.
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
dynamodb_client = boto3.resource('dynamodb', region_name='us-east-2')

# Define the Dynamo DB table name.
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMO_DB_TABLE")

# Define the destination bucket name.
DESTINATION_BUCKET = os.environ.get("DEST_BUCKET_NAME")

def safe_decimal(value):
    """Converts a string representation of a number to a Decimal object, handling errors and cleaning currency symbols."""
    if not isinstance(value, str):
        value = str(value) 

    try:
        # Clean Currency Strings.
        # Remove common currency symbols ($€£), commas (thousands separator), and extra spaces.
        cleaned_value = re.sub(r'[$,€£]', '', value).strip()
        
        if cleaned_value:
            return Decimal(cleaned_value)
        else:
            return Decimal('0.00')
    except Exception as e:
        # Fallback if conversion fails.
        print(f"Error converting '{value}' to Decimal: {e}")
        return Decimal('0.00')

def parse_purchase_date(date_text):
    """
    Attempts to parse a raw date string into the DynamoDB sort key format 'YYYY-MM-DD'.
    If parsing fails, returns the default fallback string.
    """
    if not date_text:
        return '0000-00-00'

    # List of common date formats found on receipts/invoices
    date_formats = [
        '%Y-%m-%d',       # YYYY-MM-DD (Standard ISO)
        '%m/%d/%Y',       # MM/DD/YYYY
        '%d/%m/%Y',       # DD/MM/YYYY
        '%b %d, %Y',      # Nov 20, 2023
        '%B %d, %Y',      # November 20, 2023
        '%m/%d/%y',       # MM/DD/YY (e.g., 12/08/25)
        '%d-%m-%Y',       # DD-MM-YYYY
    ]

    # Clean the date string by removing timestamps if present (e.g., "12/08/2025 10:30:00")
    clean_date_text = date_text.split(' ')[0].strip()

    for date_format in date_formats:
        try:
            # Attempt to parse using the current format
            date_obj = datetime.strptime(clean_date_text, date_format)
            
            # Success! Return the date in the standardized sort key format
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            # If parsing fails for this format, try the next one
            continue
            
    # If all parsing attempts fail
    return '0000-00-00' # The intended fallback for the sort key

def lambda_handler(event, context):
    """
    Handles S3 object creation events, calls Textract AnalyzeExpense, 
    stores the full JSON output to a destination bucket, and saves extracted data in DynamoDB.
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Get S3 Object Info from the event
        record = event['Records'][0]
        source_bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        file_size = record['s3']['object']['size']
        
        print(f"Processing file: s3://{source_bucket}/{key} of size {file_size} bytes")

        # Basic size check (10MB limit)
        if file_size > 10485760: 
            print("File size exceeds 10MB limit. Skipping Textract call.")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'File too large for synchronous processing.'})
            }
            
        # Call Textract AnalyzeExpense
        response = textract_client.analyze_expense(
            Document={
                'S3Object': {
                    'Bucket': source_bucket,
                    'Name': key
                }
            }
        )
        print("Textract AnalyzeExpense completed.")

        output_key = key.rsplit('.', 1)[0] + '.json'
        raw_full_json_key = f"textract_output/{output_key}"

        # Store the JSON response in the destination S3 bucket
        s3_client.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=raw_full_json_key,
            Body=json.dumps(response, indent=2), 
            ContentType='application/json'
        )
        print(f"Successfully stored full Textract JSON to s3://{DESTINATION_BUCKET}/{raw_full_json_key}")


        # Extract Key-Value Pairs and Line Items
        
        document_id = key 
        
        expense_summary = {
            'documentId': document_id, 
            's3Path': f"s3://{source_bucket}/{key}",
            'vendorName': 'N/A', 
            'dateOfPurchase': '0000-00-00', 
            'subtotal': 0.0,
            'tax': 0.0,
            'totalPrice': 0.0,
            'paymentType': 'N/A',
            'extractedLineItems': []
        }
        
        if response['ExpenseDocuments']:
            expense_doc = response['ExpenseDocuments'][0]
            
            summary_fields = expense_doc.get('SummaryFields', [])
            
            for field in summary_fields:
                field_type = field.get('Type', {}).get('Text', 'UNKNOWN')
                value_detected = field.get('ValueDetection', {}).get('Text', '')
                
                if field_type == 'VENDOR_NAME':
                    expense_summary['vendorName'] = value_detected

                elif field_type == 'INVOICE_RECEIPT_DATE':
                    
                    expense_summary['dateOfPurchase'] = parse_purchase_date(value_detected)

                elif field_type == 'SUBTOTAL':
                    # Using the detected value if it's a number, otherwise default to 0.0
                    try:
                        expense_summary['subtotal'] = safe_decimal(field.get('ValueDetection', {}).get('Text', 0.0))
                    except ValueError:
                         pass
                elif field_type == 'TAX':
                     try:
                        expense_summary['tax'] = safe_decimal(field.get('ValueDetection', {}).get('Text', 0.0))
                     except ValueError:
                         pass
                elif field_type == 'TOTAL':
                     try:
                        expense_summary['totalPrice'] = safe_decimal(field.get('ValueDetection', {}).get('Text', 0.0))
                     except ValueError:
                         pass
                elif field_type == 'PAYMENT_METHOD':
                    expense_summary['paymentType'] = value_detected 

            line_item_groups = expense_doc.get('LineItemGroups', [])
            
            for group in line_item_groups:
                for item in group.get('LineItems', []):
                    # Store raw values (as strings) first
                    raw_line_item_data = {} 
                    
                    for field in item.get('LineItemExpenseFields', []):
                        field_type = field.get('Type', {}).get('Text', 'UNKNOWN')
                        value_detected = field.get('ValueDetection', {}).get('Text', '')
                        
                        if field_type == 'ITEM':
                            raw_line_item_data['itemDescription'] = value_detected
                        elif field_type == 'QUANTITY':
                            raw_line_item_data['quantity'] = value_detected 
                        elif field_type == 'UNIT_PRICE':
                             raw_line_item_data['unitPrice'] = value_detected
                        elif field_type == 'PRICE': 
                            raw_line_item_data['totalPriceFromTextract'] = value_detected

                    if raw_line_item_data:
                        # Convert necessary raw strings to Decimal for calculation
                        unit_price = safe_decimal(raw_line_item_data.get('unitPrice', '0.00'))
                        quantity = safe_decimal(raw_line_item_data.get('quantity', '1')) # Default quantity to 1
                        
                        # Perform the calculation
                        line_item_total = unit_price * quantity
                        
                        # Create the final, cleaned line item dictionary
                        final_line_item = {
                            'itemDescription': raw_line_item_data.get('itemDescription'),
                            # Store components as Decimal for DynamoDB (using the safe_decimal function)
                            'quantity': quantity,
                            'unitPrice': unit_price,
                            # Store the calculated value
                            'lineItemTotal': line_item_total
                        }

                        expense_summary['extractedLineItems'].append(final_line_item)
        
        # Store Data in DynamoDB
        table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
        data_for_dynamo = table.put_item(Item=expense_summary)

        print(f"Expense Summary: {expense_summary}")
        print(f"Above Expense Summary added successfully to DynamoDB: {data_for_dynamo}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Textract analysis, JSON storage, and DynamoDB commit complete.'})
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'message': 'Processing failed.'})
        }
