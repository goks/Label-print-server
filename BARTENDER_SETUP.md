# BarTender Template Setup for Multi-Copy Sequential Numbering

## Overview
The Label Print Server now supports printing multiple copies with sequential numbering (e.g., 1/5, 2/5, 3/5, etc.). This document explains how to configure your BarTender template to display the copy numbers.

## Required BarTender Template Fields

Your BarTender template (`.btw` file) must have the following **Named Data Sources**:

### Existing Fields (Already Configured)
1. **quotation_number** - The quotation number (e.g., "9171")
2. **customer_name** - Customer/shop name
3. **address** - Full address (combined from address lines)
4. **mobile** - Contact numbers (phone and mobile combined)
5. **packed_time** - Date/time of label printing

### NEW Field Required
6. **copy_number** - Sequential copy number (e.g., "1/5", "2/5", "3/5")
   - Data Type: Text/String
   - Example values: "1/1", "1/5", "2/5", "3/5"
   - This field will automatically be populated by the system

## How to Add the copy_number Field in BarTender

### Step 1: Open Your Template
1. Open your label template in BarTender Designer
2. File should be: `Despatch Label.btw` (or your configured template)

### Step 2: Create a New Text Field
1. Click **Create** → **Text** in the toolbar
2. Place the text box where you want the copy number to appear
   - Suggested location: Top-right corner or bottom of label

### Step 3: Configure as Named Data Source
1. Right-click the new text field → **Properties**
2. Go to the **Data Source** tab
3. Click **Database Field** or **Named Data Source**
4. Set the field name to: **`copy_number`** (exact spelling, lowercase)
5. Click **OK**

### Step 4: Format the Text (Optional)
1. Adjust font size (suggested: 10-14pt)
2. Set font weight (suggested: Bold)
3. Align text (suggested: Right-aligned)
4. Add a prefix if desired (e.g., "Copy: " before the number)

### Step 5: Test the Field
1. In BarTender, go to **File** → **Print Preview**
2. You should see a placeholder or "1/1" in the copy_number field
3. The actual values will be populated when printing from the application

## Example Label Layout

```
╔═══════════════════════════════════════╗
║  QUOTATION: 9171         Copy: 1/5   ║  ← copy_number field here
║                                       ║
║  Customer: ABC Store                  ║
║  Address: 123 Main St, City           ║
║  Contact: 1234567890 | 9876543210     ║
║                                       ║
║  Packed: 15/11/2025 14:30            ║
╚═══════════════════════════════════════╝
```

## How It Works

### When User Prints 5 Copies:
1. User enters quotation number: `9171`
2. User sets number of copies: `5`
3. User clicks **Print Label**
4. System prints 5 separate labels:
   - Label 1: copy_number = "1/5"
   - Label 2: copy_number = "2/5"
   - Label 3: copy_number = "3/5"
   - Label 4: copy_number = "4/5"
   - Label 5: copy_number = "5/5"

All other fields (quotation, customer, address, etc.) remain the same across all copies - only the copy_number changes.

## Testing the Setup

### Test 1: Single Copy
1. Enter a quotation number
2. Leave copies at `1` (default)
3. Click Print
4. Expected: Label shows "1/1"

### Test 2: Multiple Copies
1. Enter a quotation number
2. Set copies to `5`
3. Click Print
4. Expected: 5 labels print with "1/5", "2/5", "3/5", "4/5", "5/5"

## Troubleshooting

### Problem: copy_number field shows blank or error
**Solution**: Ensure the field name is exactly `copy_number` (lowercase, no spaces)

### Problem: All copies show "1/5"
**Solution**: Check that COM interface is being used (not CLI). Check server logs for "BarTender COM interface" messages.

### Problem: Copies not printing sequentially
**Solution**: The system loops through each copy individually. Check logs for "copy X of Y" messages.

## Technical Details

### Print Methods
The system uses two methods in priority order:

1. **BarTender COM Interface** (Primary)
   - Supports sequential numbering
   - Loops through each copy
   - Sets copy_number field individually for each print
   - Provides reliable sequential printing

2. **BarTender CLI** (Fallback)
   - Used if COM interface fails
   - Still includes copy_number field
   - May have limitations with some BarTender versions

### Field Name Reference
All field names used by the system:
- `quotation_number` → Quotation/order number
- `customer_name` → Customer/party name
- `address` → Full delivery address
- `mobile` → Contact phone/mobile numbers
- `packed_time` → Timestamp of label creation
- `copy_number` → Sequential copy indicator (NEW)

## Support

If you encounter issues:
1. Check BarTender template has all required fields
2. Review server logs in `logs/label_print_server.log`
3. Test with single copy first
4. Verify BarTender COM automation is enabled
5. Ensure BarTender version supports automation (Professional/Automation edition)

---

**Last Updated**: November 15, 2025  
**Feature Version**: Multi-Copy Sequential Numbering v1.0
