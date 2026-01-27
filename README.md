# MiniTools

A React PWA passiong project containing multiple tools to improve efficiency and accuracy currently for Miniso staff.

**ROSTER TOOL**
Features

- Shift slots (e.g. 9am - 4pm requires 2 ppl)
- Employee
  - Availability (hard constraint)
  - Preferred days (soft constraint)
  - When2meet ui
  - Add an all day checkbox for each day
- Persistent storage (needa work this one out)
- Figure out session persistence (use tool next week with same config)

Spits out Gantt chart (can consider other visuals) of roster for the week (visual will largely depend on how they make the roster)

**PRICE CHECKER**
Features

- Uses OCR for barcode scanning (should provide manual serial number input for times barcode kaput)
- Uses API to query a price database
- 'Community driven' price data (data is supplied by other miniso slaves)
- If a product DOES NOT exist in the database, user is asked to provide its price for future scans
  - If asked to provide price for product, user should be allowed to refuse providing. (They ceebs)
- Option to also allow price updating (edge case of price changes)

**PAY CALC**
Features

- This can be calculated locally (no need for API)
- Input shifts (down to the minute) expected payday (the Thursday the payday comes at)
- Option to also add overtime hours
- Accounts for unpaid 30s, bonuses from >6pm, weekends, holidays
- Gives total sum, as well as breakdown of the bonuses (ideally identical to payslip layout for easier comparison)

**POTENTIAL FEATURES**
Authentication

- Register emails and passwords

Cloud based data persistence

- Allow for device syncing
