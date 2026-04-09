from io import BytesIO
from datetime import datetime
import re
import pandas as pd
from fastapi.responses import StreamingResponse


def clean_filename(value: str) -> str:
    value = value.strip().replace(" ", "_")
    value = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    return value


def excel_response(rows: list[dict], filename_prefix: str) -> StreamingResponse:
    df = pd.DataFrame(rows or [])
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")

    output.seek(0)

    filename = clean_filename(
        f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )