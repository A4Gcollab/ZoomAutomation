/**
 * VONG Automation - Secure Approver Logging
 * 
 * INSTRUCTIONS FOR INSTALLABLE TRIGGER:
 * 1. Paste this code.
 * 2. Save.
 * 3. Go to "Triggers" (Clock icon on left).
 * 4. Add Trigger: 
 *    - Function: secureOnEdit
 *    - Event source: From spreadsheet
 *    - Event type: On edit
 * 5. Save & Authorize.
 */

function secureOnEdit(e) {
    var range = e.range;
    var sheet = range.getSheet();

    if (sheet.getName() !== "Sheet1") return;

    // Check if Status (Col 9) changes to "APPROVED"
    if (range.getColumn() === 9 && e.value === "APPROVED") {

        // With Installable Trigger, this now captures the real user
        var email = Session.getActiveUser().getEmail();

        // Fallback info if still issues (e.g. enterprise restrictions)
        if (!email) {
            email = "User (Check Revision History)";
        }

        // Write Email to "Approved By" (Col 10)
        sheet.getRange(range.getRow(), 10).setValue(email);
        sheet.getRange(range.getRow(), 10).setNote("Approved: " + new Date());
    }
}
