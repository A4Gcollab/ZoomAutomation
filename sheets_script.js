/**
 * VONG Automation - Secure Approval Script
 * Adds a menu to Approve videos and log the user's email reliably.
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('✅ VONG Automation')
    .addItem('Approve & Sign', 'approveRow')
    .addToUi();
}

function approveRow() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getActiveRange();
  var row = range.getRow();

  if (row < 2) {
    SpreadsheetApp.getUi().alert("Please select a valid row.");
    return;
  }

  // Confirm
  var ui = SpreadsheetApp.getUi();
  var response = ui.alert('Confirm Approval', 'Approve this recording?', ui.ButtonSet.YES_NO);

  if (response == ui.Button.YES) {
    // Get Email (Running as Active User triggered by Menu)
    var email = Session.getActiveUser().getEmail();
    if (!email) {
      // Fallback if still hidden (rare on menu clicks but possible)
      email = "Unknown User (Sign-in Required)";
    }

    // Validating columns: Status = Col 9 (I), Approved By = Col 10 (J)
    sheet.getRange(row, 9).setValue("APPROVED");
    sheet.getRange(row, 10).setValue(email);
    sheet.getRange(row, 10).setBackground("#d9ead3"); // Light green

    ui.alert("✅ Approved Row " + row + " as: " + email);
  }
}
