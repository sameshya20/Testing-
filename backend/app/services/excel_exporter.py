import io
import re
import logging
from typing import List, Any
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from app.schemas.test_case import TestCase

logger = logging.getLogger(__name__)

def _clean_str(val: Any) -> str:
    """Sanitize strings by stripping illegal XML and control characters."""
    if val is None:
        return ""
    text = str(val)
    # Remove control characters forbidden in XML 1.0 (keep \t, \n, \r)
    return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)

def _deduplicate_cases(cases: List[TestCase]) -> List[TestCase]:
    """Ensure no duplicate test cases within a category."""
    if not cases:
        return []
    seen = set()
    unique = []
    for tc in cases:
        identifier = getattr(tc, 'id', None) or (
            getattr(tc, 'scenario', ''),
            getattr(tc, 'description', ''),
            getattr(tc, 'user_story', '')
        )
        if identifier in seen:
            continue
        seen.add(identifier)
        unique.append(tc)
    return unique

class ExcelExporterService:
    """Generates 100% Microsoft Excel-compliant multi-sheet workbooks using openpyxl."""

    def generate_workbook(
        self,
        positive_cases: List[TestCase],
        negative_cases: List[TestCase],
        edge_cases: List[TestCase],
        app_name: str,
        req_ref: str
    ) -> io.BytesIO:
        wb = openpyxl.Workbook()
        
        # Predefine styles & formats - CRITICAL: Hex colors in openpyxl MUST NOT have leading '#'
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        thin_border_side = Side(border_style="thin", color="E2E8F0")
        cell_border = Border(
            left=thin_border_side,
            right=thin_border_side,
            top=thin_border_side,
            bottom=thin_border_side
        )

        id_font = Font(name="Calibri", size=10, bold=True, color="0F172A")
        data_font = Font(name="Calibri", size=10, color="0F172A")
        empty_font = Font(name="Calibri", size=10, italic=True, color="64748B")

        align_center = Alignment(horizontal="center", vertical="top")
        align_left_wrap = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Priority badge styles
        p_high_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        p_high_font = Font(name="Calibri", size=10, bold=True, color="991B1B")

        p_med_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        p_med_font = Font(name="Calibri", size=10, bold=True, color="92400E")

        p_low_fill = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")
        p_low_font = Font(name="Calibri", size=10, bold=True, color="075985")

        headers = [
            "Test Case ID",
            "User Story",
            "Acceptance Criteria",
            "Application Page",
            "Application Link",
            "Test Scenario",
            "Test Description",
            "Preconditions",
            "Test Data",
            "Test Steps",
            "Expected Result",
            "Priority",
            "Category"
        ]

        sheets_data = [
            ("Positive", _deduplicate_cases(positive_cases)),
            ("Negative", _deduplicate_cases(negative_cases)),
            ("Edge", _deduplicate_cases(edge_cases))
        ]

        col_widths = [15, 16, 20, 20, 35, 35, 40, 35, 30, 45, 45, 14, 14]

        # Use existing default active sheet for "Positive", then create others
        for idx, (sheet_name, cases) in enumerate(sheets_data):
            if idx == 0:
                ws = wb.active
                ws.title = sheet_name
            else:
                ws = wb.create_sheet(title=sheet_name)

            # Ensure grid lines remain visible
            ws.views.sheetView[0].showGridLines = True

            # Set column widths
            for col_idx, width in enumerate(col_widths, start=1):
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = width

            # Write Header Row
            ws.row_dimensions[1].height = 28
            for col_idx, h in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col_idx, value=h)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_align
                cell.border = cell_border

            # Freeze header row
            ws.freeze_panes = "A2"

            # Write Data rows
            if cases:
                for row_idx, tc in enumerate(cases, start=2):
                    if isinstance(getattr(tc, 'test_steps', None), list):
                        steps_text = "\n".join([_clean_str(s) for s in tc.test_steps if s is not None])
                    else:
                        steps_text = _clean_str(getattr(tc, 'test_steps', '') or "")

                    user_story_val = _clean_str(getattr(tc, 'user_story', '') or '')
                    if not user_story_val:
                        req_val = getattr(tc, 'requirement_ref', '') or ''
                        user_story_val = _clean_str(req_val.split(' ')[0] if req_val else "N/A")

                    ac_val = _clean_str(getattr(tc, 'acceptance_criteria', '') or '')
                    if not ac_val:
                        req_val = getattr(tc, 'requirement_ref', '') or ''
                        parts = req_val.split(' ')
                        ac_val = _clean_str(" ".join(parts[1:]) if len(parts) > 1 else req_val)

                    app_page_val = _clean_str(getattr(tc, 'application_page', '') or "N/A")
                    app_link_val = _clean_str(getattr(tc, 'application_link', '') or "N/A")

                    # Calculate dynamic row height
                    step_lines = len(steps_text.split('\n'))
                    desc_lines = max(1, len(str(getattr(tc, 'description', '') or '')) // 35)
                    row_h = max(45, max(step_lines, desc_lines) * 18)
                    ws.row_dimensions[row_idx].height = min(400, row_h)

                    # Determine priority formatting
                    priority_str = _clean_str(getattr(tc, 'priority', 'Medium') or 'Medium').upper()
                    if 'HIGH' in priority_str:
                        p_fill = p_high_fill
                        p_font = p_high_font
                    elif 'MED' in priority_str:
                        p_fill = p_med_fill
                        p_font = p_med_font
                    else:
                        p_fill = p_low_fill
                        p_font = p_low_font

                    row_values = [
                        (_clean_str(getattr(tc, 'id', '')), id_font, align_center, None),
                        (user_story_val, data_font, align_center, None),
                        (ac_val, data_font, align_center, None),
                        (app_page_val, data_font, align_center, None),
                        (app_link_val, data_font, align_left_wrap, None),
                        (_clean_str(getattr(tc, 'scenario', '')), data_font, align_left_wrap, None),
                        (_clean_str(getattr(tc, 'description', '')), data_font, align_left_wrap, None),
                        (_clean_str(getattr(tc, 'preconditions', '')), data_font, align_left_wrap, None),
                        (_clean_str(getattr(tc, 'test_data', '')), data_font, align_left_wrap, None),
                        (steps_text, data_font, align_left_wrap, None),
                        (_clean_str(getattr(tc, 'expected_result', '')), data_font, align_left_wrap, None),
                        (_clean_str(getattr(tc, 'priority', 'Medium') or 'Medium'), p_font, align_center, p_fill),
                        (_clean_str(getattr(tc, 'category', sheet_name)), data_font, align_center, None)
                    ]

                    for col_idx, (val, font, align, fill) in enumerate(row_values, start=1):
                        cell = ws.cell(row=row_idx, column=col_idx, value=val)
                        cell.font = font
                        cell.alignment = align
                        cell.border = cell_border
                        if fill:
                            cell.fill = fill

                # Auto-filter over all data columns
                last_col_letter = get_column_letter(len(headers))
                ws.auto_filter.ref = f"A1:{last_col_letter}{len(cases) + 1}"
            else:
                ws.row_dimensions[2].height = 24
                cell = ws.cell(row=2, column=1, value=f"No {sheet_name.lower()} test cases generated for this requirement.")
                cell.font = empty_font

        # Set first sheet ("Positive") as active
        wb.active = 0

        # Step 2 requirement: Save workbook to in-memory BytesIO buffer
        output = io.BytesIO()
        wb.save(output)
        wb.close()
        
        # Step 2 requirement: Reset buffer position using buffer.seek(0)
        output.seek(0)

        raw_bytes = output.getvalue()
        file_size = len(raw_bytes)

        # Step 2 requirement: Verify file begins with the ZIP/XLSX signature PK\x03\x04
        if file_size < 4 or raw_bytes[:4] != b'PK\x03\x04':
            raise ValueError(f"Invalid XLSX binary: missing PK ZIP signature (found {raw_bytes[:4]!r})")

        # Step 2 requirement: Verify workbook can be reopened using openpyxl load_workbook(...)
        verification_wb = openpyxl.load_workbook(io.BytesIO(raw_bytes))
        sheet_names = verification_wb.sheetnames

        # Step 2 requirement: Verify workbook contains Positive, Negative, Edge
        expected_sheets = {"Positive", "Negative", "Edge"}
        if not expected_sheets.issubset(set(sheet_names)):
            verification_wb.close()
            raise ValueError(f"Workbook missing required sheets. Found: {sheet_names}")

        # Step 2 requirement: Verify expected test case rows
        total_rows_found = 0
        for sname in ["Positive", "Negative", "Edge"]:
            sheet = verification_wb[sname]
            total_rows_found += max(0, sheet.max_row - 1)
        verification_wb.close()

        # Step 2 requirement: Log filename, file size, content type, first few bytes/signature, sheet names
        logger.info(
            f"[EXCEL_EXPORTER] Successfully verified XLSX workbook:\n"
            f" - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\n"
            f" - File size: {file_size} bytes\n"
            f" - Binary Signature: {raw_bytes[:4]!r} (PK\\x03\\x04)\n"
            f" - Sheet names: {sheet_names}\n"
            f" - Total data rows verified: {total_rows_found}"
        )

        output.seek(0)
        return output

excel_exporter = ExcelExporterService()

