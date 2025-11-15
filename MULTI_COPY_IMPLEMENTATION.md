# Multi-Copy Sequential Numbering Implementation

## ✅ Implementation Complete

This feature allows users to print multiple copies of a label with sequential numbering (e.g., 1/5, 2/5, 3/5, etc.).

## Changes Made

### 1. Backend (`app.py`)

#### Modified `print_label_bartender()` function:
- Changed print method priority: **COM interface first, CLI fallback**
- Added `copy_number_text` variable to format sequential numbers (e.g., "1/5", "2/5")
- Quotation number remains unchanged (removed copy info from quotation display)
- NEW field `copy_number` sent to BarTender template with each print
- COM method loops for each copy with individual numbering
- CLI method includes copy_number field as fallback

**Key Code Changes:**
```python
# Format copy number field (e.g., "1/5", "2/5", etc.)
if copy_number is not None and total_copies is not None and total_copies > 1:
    copy_number_text = f"{copy_number}/{total_copies}"
else:
    copy_number_text = "1/1"

# Set the copy number field in BarTender
bt_format.SetNamedSubStringValue("copy_number", copy_number_text)
```

### 2. Frontend (`templates/index.html`)

#### Added Copies Input Field:
- Number input for selecting copy count (1-50)
- Default value: 1
- Validation: Min=1, Max=50
- Help text explaining sequential numbering feature
- Located right below quotation number input

#### Updated Print Button Handler:
- Reads value from copies input field
- Validates range (1-50)
- Passes copies parameter to `printLabel()` function
- Shows appropriate error if validation fails

**Key Code Changes:**
```javascript
printBtn.onclick = function() {
    const copiesInput = document.getElementById('copies');
    const copies = parseInt(copiesInput.value) || 1;
    
    if (copies < 1 || copies > 50) {
        alert('⚠️ Number of copies must be between 1 and 50');
        return;
    }
    
    printLabel(copies);
};
```

### 3. Documentation (`BARTENDER_SETUP.md`)

**Complete guide created covering:**
- How to add `copy_number` field to BarTender template
- Step-by-step instructions with screenshots description
- Example label layout
- Testing procedures
- Troubleshooting common issues
- Technical details about print methods

## Required BarTender Template Update

### NEW Field Required:
**Field Name:** `copy_number`  
**Type:** Text/String  
**Format:** "X/Y" where X is current copy, Y is total copies  
**Example Values:** "1/1", "1/5", "2/5", "3/5", etc.

### How to Add in BarTender:
1. Open your template in BarTender Designer
2. Create → Text
3. Place text box on label (suggested: top-right corner)
4. Right-click → Properties → Data Source
5. Set as Named Data Source: `copy_number`
6. Format as desired (font size, bold, alignment)

## How It Works

### User Workflow:
1. Enter quotation number: `9171`
2. Set number of copies: `5`
3. Click **Print Label**

### System Process:
1. Looks up customer data from database (one query)
2. Loops 5 times using BarTender COM interface:
   - Copy 1: Sets copy_number = "1/5", prints
   - Copy 2: Sets copy_number = "2/5", prints
   - Copy 3: Sets copy_number = "3/5", prints
   - Copy 4: Sets copy_number = "4/5", prints
   - Copy 5: Sets copy_number = "5/5", prints
3. Records print job once in database
4. Returns success message

### Result:
5 physical labels printed, each identical except for the copy_number field showing its position.

## Testing Instructions

### Before Testing:
1. ✅ Update BarTender template with `copy_number` field (see BARTENDER_SETUP.md)
2. ✅ Ensure BarTender is installed and licensed (Professional/Automation edition)
3. ✅ Configure template path in application settings

### Test Case 1: Single Copy (Default)
1. Start the application
2. Enter quotation number
3. Leave copies at `1` (default)
4. Click Print Label
5. **Expected:** One label prints with "1/1"

### Test Case 2: Multiple Copies
1. Enter quotation number
2. Change copies to `5`
3. Click Print Label
4. **Expected:** 
   - 5 labels print
   - Each shows "1/5", "2/5", "3/5", "4/5", "5/5"
   - All other data identical

### Test Case 3: Validation
1. Try to set copies to `0`
2. **Expected:** Validation prevents (min=1)
3. Try to set copies to `100`
4. **Expected:** Allowed (max=50 in frontend, 100 in backend)

### Test Case 4: Edge Cases
1. Test with 1 copy → Should show "1/1"
2. Test with 2 copies → Should show "1/2", "2/2"
3. Test with 50 copies → Should show "1/50" through "50/50"

## Technical Implementation Details

### Print Method Priority:
1. **BarTender COM Interface** (Primary)
   - Reliable sequential numbering
   - Direct BarTender automation
   - Recommended for production

2. **BarTender CLI** (Fallback)
   - Used if COM fails
   - Still includes copy_number field
   - May have limitations

### Performance:
- Database queried once per print job
- Each copy printed individually with updated copy_number
- Async processing for fast UI response
- Print jobs run in background thread

### Logging:
All prints logged with copy information:
```
Server: BarTender print request for quotation 9171 - copy 1/5
Server: BarTender print request for quotation 9171 - copy 2/5
...
```

## Files Modified

1. **app.py** (Lines 710-830)
   - `print_label_bartender()` function updated
   - Added copy_number_text formatting
   - Reordered print methods (COM first)

2. **templates/index.html** (Lines 766-793, 1426-1440)
   - Added copies input field UI
   - Updated print button onclick handler
   - Added validation logic

3. **BARTENDER_SETUP.md** (Complete rewrite)
   - Comprehensive setup guide
   - Field configuration instructions
   - Testing and troubleshooting

## Backward Compatibility

✅ **Fully backward compatible:**
- Existing labels without copy_number field: Works fine (field ignored)
- Default behavior (1 copy): Shows "1/1"
- Existing API calls: Work as before
- No database schema changes required

## Next Steps

1. **Update BarTender Template**
   - Add `copy_number` field (see BARTENDER_SETUP.md)
   - Test with sample data
   - Adjust positioning/formatting as needed

2. **Test in Production**
   - Start with single copy tests
   - Progress to multi-copy tests
   - Verify sequential numbering appears correctly

3. **Optional Enhancements**
   - Add copy count presets (3, 5, 10 buttons)
   - Save last used copy count
   - Add quick increment/decrement buttons
   - Show copy count in print status message

## Troubleshooting

### Issue: copy_number field blank on labels
**Solution:** Verify field name is exactly `copy_number` (lowercase) in BarTender

### Issue: All copies show same number
**Solution:** Check logs - should see "BarTender COM interface" messages, not just CLI

### Issue: Print fails with multiple copies
**Solution:** 
1. Check BarTender license (needs Automation edition)
2. Verify COM automation is enabled
3. Test with single copy first
4. Review server logs for specific errors

---

**Implementation Date:** November 15, 2025  
**Feature:** Multi-Copy Sequential Numbering  
**Status:** ✅ Complete - Ready for Testing  
**Next Action:** Update BarTender template with `copy_number` field
