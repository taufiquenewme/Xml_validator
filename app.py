import xml.etree.ElementTree as ET
import unittest
import datetime
import pytz
from xmldiff import main, actions
from lxml import etree

class Store:
    def __init__(self, retailer_store_id="1001", store_type="EventNetworkStoreType", timezone="UTC"):
        self.retailer_store_id = retailer_store_id
        self.store_type = store_type
        self.timezone = timezone
        self.extra_data = {
            "workstation_ids": {"dummy_device": "POS001"},
            "WorkstationID": "POS001",
            "is_living_planet_store": False,
            "alternate_id": "ALT123",
            "receipt_email_address": "test@example.com",
        }
    
    def save(self):
        # Mock save method
        pass

class Customer:
    def __init__(self, customer_id="CUST123"):
        self.customer_id = customer_id

class Basket:
    def __init__(self):
        self.basketitem_set = BasketItemSet()

class BasketItemSet:
    def __init__(self):
        self.items = [
            BasketItem("SKU123456", "Wireless Mouse", 1, 25.99),
            BasketItem("SKU654321", "Mechanical Keyboard", 1, 89.99)
        ]
    
    def all(self):
        return self.items

class BasketItem:
    def __init__(self, product_identifier, item_name, item_quantity, price):
        self.product_identifier = product_identifier
        self.item_name = item_name
        self.item_quantity = item_quantity
        self.price = price

class Order:
    def __init__(self, basket, store):
        self.basket = basket
        self.store = store

class TestXMLGeneration(unittest.TestCase):
    def create_store(self):
        return Store()

    def create_user(self):
        return Customer()

    def create_basket(self, customer_obj, store):
        return Basket()

    def create_basket_items(self, basket):
        # Items are already created in Basket initialization
        pass

    def create_entity_audit_logs(self, basket):
        # Mock method - not needed for this test
        pass

    def create_order(self, basket, store):
        return Order(basket, store)

    def create_payments(self, order):
        # Mock method - not needed for this test
        pass

    def create_refund(self):
        # Mock method - not needed for this test
        pass

    def setUp(self):
        self.store = self.create_store()
        self.customer_obj = self.create_user()
        self.basket = self.create_basket(self.customer_obj, self.store)
        self.create_basket_items(self.basket)
        self.create_entity_audit_logs(self.basket)
        self.order = self.create_order(self.basket, self.store)
        self.create_payments(self.order)
        self.create_refund()
        self.store.store_type = "EventNetworkStoreType"
        self.store.retailer_store_id = "1001"
        self.store.timezone = "UTC"
        self.store.save()

        self.generated_xml = self.generate_xml()

    def generate_xml(self):
        pos_log = ET.Element("POSLog")
        transaction = ET.SubElement(pos_log, "Transaction")

        # TransactionHeader
        transaction_header = ET.SubElement(transaction, "TransactionHeader")
        ET.SubElement(transaction_header, "RetailStoreID").text = self.store.retailer_store_id
        ET.SubElement(transaction_header, "WorkstationID").text = self.store.extra_data["WorkstationID"]
        ET.SubElement(transaction_header, "OperatorID").text = "12345"
        ET.SubElement(transaction_header, "TransactionSequenceID").text = "56789"
        ET.SubElement(transaction_header, "BusinessDayDate").text = "2025-03-18"
        ET.SubElement(transaction_header, "BeginDateTime").text = "2025-03-18T10:15:30"

        # RetailTransaction
        retail_transaction = ET.SubElement(transaction, "RetailTransaction")
        for item in self.basket.basketitem_set.all():
            line_item = ET.SubElement(retail_transaction, "LineItem")
            sale = ET.SubElement(line_item, "Sale")
            ET.SubElement(sale, "ItemID").text = item.product_identifier
            ET.SubElement(sale, "Description").text = item.item_name
            ET.SubElement(sale, "Quantity").text = str(item.item_quantity)
            ET.SubElement(sale, "RegularSalesUnitPrice").text = f"{item.price:.2f}"
            ET.SubElement(sale, "ExtendedAmount").text = f"{item.price * item.item_quantity:.2f}"

        # Payment
        payment = ET.SubElement(transaction, "Payment")
        tender = ET.SubElement(payment, "Tender")
        ET.SubElement(tender, "TenderType").text = "CreditCard"
        total_amount = sum(item.price * item.item_quantity for item in self.basket.basketitem_set.all())
        ET.SubElement(tender, "Amount").text = f"{total_amount:.2f}"

        # TransactionTrailer
        transaction_trailer = ET.SubElement(transaction, "TransactionTrailer")
        total = ET.SubElement(transaction_trailer, "Total")
        ET.SubElement(total, "Amount").text = f"{total_amount:.2f}"

        return ET.tostring(pos_log, encoding='unicode')

    def canonicalize_xml(self, xml_str):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_str.encode('utf-8'), parser)
        return etree.tostring(root, method="c14n").decode('utf-8')

    def test_xml_equality(self):
        parser = etree.XMLParser(remove_blank_text=True)
        with open('sample.xml', 'rb') as file:
            expected_xml = etree.parse(file, parser)
        
        # Convert generated XML string to lxml object
        generated_tree = etree.fromstring(self.generated_xml.encode(), parser)
        
        # Canonicalize both XML documents for comparison
        generated_canonical = self.canonicalize_xml(self.generated_xml)
        expected_canonical = self.canonicalize_xml(etree.tostring(expected_xml.getroot(), encoding='unicode'))
        print('aaron:',generated_canonical)
        print('taufique',expected_canonical)

        # Compare canonicalized XML
        self.assertEqual(generated_canonical, expected_canonical)

if __name__ == '__main__':
    unittest.main()