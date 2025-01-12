from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
from PIL import Image
import base64
import sqlite3
import json
import io
import re

instruction_prompt = """ Your job is to analyse and extract invoice data from the invoice. The invoice is provided in base64 format. The data extracted from invoice should be in the 
json format given below : 
{
  "invoice_number" : "",
  "invoice_date" : "",
  "vendor_number": "",
  "vendor_name" : "",
  "vendor_address" : {
    "street": "",
    "city": "",
    "state":"",
    "country" : "",
    "zipcode" : "",
  }, 
  "gross_amount": "",
  "net_amount": "",
  "discount_percent" : "",
  "discount_amount": "",
  "tax_amount": "",
  "tax_percent" : "",
  "vat_precent": "", 
  "vat_amount": "",
  "bank_name": "",
  "bank_account_number": "",
  "invoice_line_items": 
  [
    {
     "item_name": "",
     "item_quantity":"",
     "item_unit_price" : "",
     "item_total_amount": "",
    }
  ]
}

Ensure to leave any field as null if failed to identify the data to populate with. For any other request, respond as : {
"message": "Invalid Request"
}
Always respond in valid json as mentioned above without any extra text before or after.
"""

st.title("Invoice Processor using LLM")



# File uploader for images only
uploaded_file = st.file_uploader("Upload Your Invoice", type=["png", "jpg", "jpeg"])

def file_uploads(st, uploaded_file):
    # Check if a file is uploaded
    if uploaded_file is not None:
        # Opening the uploaded image
        image = Image.open(uploaded_file)

        # Displaying the uploaded image
        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Displaying image information
        st.write("Image format:", image.format)
        st.write("Image Mode:", image.mode)
        st.write("Image size:", image.size)

        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format=image.format)
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Display base64 content
        st.text_area("Image in Base64", image_base64, height=200)
   
        try:
            ai_response  = extract_invoice_data(image_base64, instruction_prompt)
        except Exception as e:
            st.text(f"Failed to extract invoice data from LLM: {e}")
            return
        invoice_data = parser_invoice_data(ai_response)
        try:
            insert_invoice_data(invoice_data, cursor)
            st.text("Successfully parsed and stored invoice data in DB")
            st.json(invoice_data)
        except Exception as e:
            st.text(f"Failed to insert invoice data in DB: {e}")


def parser_invoice_data(response):
    # regex = r"\{(?:[^{}]|(?R))*\}"
    regex =  r"```json\n(.*)```"
    match = re.findall(regex,response,re.DOTALL)
    if match:
        try:
            return json.loads(match[-1])
        except Exception as e:
            print(f"Failed to parse JSON:{e}")
            return None 
    return None


def extract_invoice_data(base64_data, instruction_prompt):
    messages = [{
        "role": "system",
        "content" : instruction_prompt
    },
    {
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Extract invoice data from this invoice",
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"},
        },
    ]
    }
    ]

    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    ai_response = response.choices[0].message.content

    return ai_response


# Script to insert invoice data into tables

def insert_invoice_data(invoice_data, cursor):
    insert_invoice_sql = """
    INSERT INTO invoice(
        invoice_number,
        invoice_date,
        vendor_name,
        vendor_number,
        address,
        city,
        state,
        country,
        zip_code,
        tax_percent,
        tax_amount,
        discount_percent,
        discount_amount,
        vat_percent,
        vat_amount,
        bank_name,
        bank_account_number,
        gross_amount,
        net_amount 
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    insert_invoice_line_item_sql = """
    INSERT INTO invoice_line_items
    (invoice_number,
    item_name,
    item_quantity,
    unit_price,
    total_price) VALUES (?,?,?,?,?)
    """ 
    try:
        invoice_line_items = invoice_data.get('invoice_line_items')
        cursor.execute(insert_invoice_sql, (invoice_data.get('invoice_number'),
                                            invoice_data.get('invoice_date'),
                                            invoice_data.get('vendor_name'),
                                            invoice_data.get('vendor_number'),
                                            invoice_data.get('vendor_address').get('street'),
                                            invoice_data.get('vendor_address').get('city'),
                                            invoice_data.get('vendor_address').get('state'),
                                            invoice_data.get('vendor_address').get('country'),
                                            invoice_data.get('vendor_address').get('zipcode'),
                                            invoice_data.get('tax_percent'),
                                            invoice_data.get('tax_amount'),
                                            invoice_data.get('discount_percent'),
                                            invoice_data.get('discount_amount'),
                                            invoice_data.get('vat_percent'),
                                            invoice_data.get('vat_amount'),
                                            invoice_data.get('bank_name'),
                                            invoice_data.get('bank_account_number'),
                                            invoice_data.get('gross_amount'),
                                            invoice_data.get('net_amount')
                                            ))

        
        for line_item in invoice_line_items:
            cursor.execute(insert_invoice_line_item_sql, (
                invoice_data.get('invoice_number'),
                line_item.get("item_name"), 
                line_item.get('item_quantity'),
                line_item.get('item_unit_price'),
                line_item.get('item_total_amount')
            ))

    except Exception as e:
        cursor.close()
        raise Exception(f"Failed to insert invoice data: {e}")



# Code for database connection

conn = sqlite3.connect("test_client.db")
cursor = conn.cursor()

file_uploads(st, uploaded_file)
