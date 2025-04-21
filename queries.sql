-- Create View: ItemSalesSummary
CREATE VIEW ItemSalesSummary AS
SELECT  
    i.iId,  
    i.Iname,  
    SUM(o.Amount) AS TotalRevenue,  
    SUM(oi.Icount) AS TotalQuantitySold 
FROM order_item oi 
JOIN item i ON oi.iId = i.iId 
JOIN "ORDER" o ON oi.oId = o.oId 
GROUP BY i.iId, i.Iname;

-- Create View: TopLoyalCustomers
CREATE VIEW TopLoyalCustomers AS
SELECT cId, Cname, LoyaltyScore
FROM customer
ORDER BY LoyaltyScore DESC
LIMIT 10;

-- QV1: Top 3 Revenue-Generating Items
SELECT Iname, TotalRevenue
FROM ItemSalesSummary
ORDER BY TotalRevenue DESC
LIMIT 3;

-- QV2: Items Sold More Than 50 Units
SELECT Iname, TotalQuantitySold
FROM ItemSalesSummary
WHERE TotalQuantitySold > 50;

-- QV3: Top Customer by Loyalty
SELECT Cname, LoyaltyScore
FROM TopLoyalCustomers
ORDER BY LoyaltyScore DESC
LIMIT 1;

-- QV4: Customers with Loyalty Between 4 and 5
SELECT Cname, LoyaltyScore
FROM TopLoyalCustomers
WHERE LoyaltyScore BETWEEN 4 AND 5;

-- QV5: Total Revenue Across All Items
SELECT SUM(TotalRevenue)
FROM ItemSalesSummary;

-- Get highest item ID (used in app.py)
SELECT MAX(iId) FROM ITEM;

-- Get highest vendor ID (used in app.py)
SELECT MAX(vId) FROM VENDOR;

-- Insert into VENDOR_ITEM (used in app.py)
INSERT INTO VENDOR_ITEM (vId, iId)
VALUES (<vendor_id>, <item_id>)
ON CONFLICT (vId, iId) DO NOTHING;

-- Insert or update vendor
INSERT INTO VENDOR (vId, Vname, Street, City, StateAb, ZipCode)
VALUES (...)
ON CONFLICT (vId) DO UPDATE SET ...;

-- Insert or update item
INSERT INTO ITEM (iId, Iname, Sprice, Category)
VALUES (...)
ON CONFLICT (iId) DO UPDATE SET Sprice = ...;

-- Insert or update store stock
INSERT INTO STORE_ITEM (sId, iId, Scount)
VALUES (...)
ON CONFLICT (sId, iId) DO UPDATE SET Scount = ...;

-- Delete from VENDOR_ITEM
DELETE FROM VENDOR_ITEM WHERE iId = <product_id>;

-- Delete from STORE_ITEM
DELETE FROM STORE_ITEM WHERE iId = <product_id>;

-- Delete from ITEM
DELETE FROM ITEM WHERE iId = <product_id>;

-- Delete from VENDOR_STORE
DELETE FROM VENDOR_STORE WHERE vId = <vendor_id>;

-- Delete vendor if no items left
DELETE FROM VENDOR
WHERE vId = <vendor_id>
AND NOT EXISTS (
    SELECT 1 FROM VENDOR_ITEM WHERE vId = <vendor_id>
);