# Business Logic

The dashboard uses three broad data lanes: sales, inventory snapshots, and traffic snapshots.

## Processing Flow

1. Validate the uploaded file and detect its data type.
2. Normalize dates, product identifiers, and numeric fields.
3. Use a file hash to prevent accidental duplicate uploads.
4. Store valid rows in the relevant historical table.
5. Calculate KPIs for the selected date and category scope.
6. Report missing or incomplete sources instead of silently replacing them with zero.

## Example Diagnostic Logic

- Stable or rising traffic with falling CVR prioritizes conversion-side checks.
- Strong sales with low DOS prioritizes replenishment checks.
- Rising returns prompts product, expectation, logistics, and after-sales review.
- Missing traffic or inventory snapshots produce explicit data-quality warnings.
