import pandas as pd


BANK_CONFIGS = {
    "generic_signed_amount": {
        "date_col_candidates": ["date", "Date", "Transaction Date", "Posted Date", "TransactionDate"],
        "desc_col_candidates": ["description", "Description", "Details", "Memo"],
        "amount_col_candidates": ["amount", "Amount", "Transaction Amount"],
        "pending_col_candidates": ["Pending", "pending", "Status"],
        "pending_true_values": [True, "TRUE", "True", "Yes", "Y", "Pending"],
        "amount_style": "signed",
    },
    "bank_x_export": {
        "date_col_candidates": ["Transaction Date", "Posted Date"],
        "desc_col_candidates": ["Details", "Description"],
        "amount_col_candidates": ["Amount"],
        "pending_col_candidates": ["Status", "Pending"],
        "pending_true_values": ["Pending"],
        "amount_style": "signed",
    },
    "bank_y_export": {
        "date_col_candidates": ["Posted Date", "Transaction Date", "Date"],
        "desc_col_candidates": ["Description", "Details"],
        "debit_col_candidates": ["Debit", "Withdrawals", "Withdrawal Amount"],
        "credit_col_candidates": ["Credit", "Deposits", "Deposit Amount"],
        "pending_col_candidates": ["Pending", "Status"],
        "pending_true_values": ["Pending", True, "TRUE"],
        "amount_style": "debit_credit",
    },
    "bank_with_indicator": {
    "date_col_candidates": ["TransactionDate", "Transaction Date", "PostedDate", "Posted Date", "Date"],
    "desc_col_candidates": ["Description", "Details", "Memo"],
    "amount_col_candidates": ["Amount", "Transaction Amount"],
    "type_col_candidates": ["Credit Debit Indicator"],
    "debit_type_values": ["DEBIT", "Debit", "D", "DBIT"],
    "credit_type_values": ["CREDIT", "Credit", "C", "CRDT"],
    "pending_col_candidates": ["Pending", "Status"],
    "pending_true_values": [True, "TRUE", "True", "Yes", "Y", "Pending"],
    "amount_style": "signed_with_type",
}
}


def _clean_money_series(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()

    s = s.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NULL": pd.NA})

    s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)

    s = s.str.replace(",", "", regex=False)
    s = s.str.replace("$", "", regex=False)

    return pd.to_numeric(s, errors="coerce")


def _resolve_column(df: pd.DataFrame, candidates: list[str] | None, field_name: str, required: bool = True):
    if not candidates:
        if required:
            raise KeyError(f"No candidates provided for required field: {field_name}")
        return None

    normalized_to_actual = {
        str(col).strip().lower(): col for col in df.columns
    }

    for candidate in candidates:
        key = str(candidate).strip().lower()
        if key in normalized_to_actual:
            return normalized_to_actual[key]

    if required:
        raise KeyError(
            f"Could not find a column for '{field_name}'. "
            f"Tried: {candidates}. Available columns: {list(df.columns)}"
        )
    return None


def normalize_transactions(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    out = df.copy()
    amount_style = config.get("amount_style", "signed")

    date_col = _resolve_column(out, config.get("date_col_candidates"), "date")
    desc_col = _resolve_column(out, config.get("desc_col_candidates"), "description")

    amount_col = None
    debit_col = None
    credit_col = None

    amount_col = None
    debit_col = None
    credit_col = None
    type_col = None

    if amount_style == "signed":
        amount_col = _resolve_column(out, config.get("amount_col_candidates"), "amount")

    elif amount_style == "debit_credit":
        debit_col = _resolve_column(out, config.get("debit_col_candidates"), "debit")
        credit_col = _resolve_column(out, config.get("credit_col_candidates"), "credit")

    elif amount_style == "signed_with_type":
        amount_col = _resolve_column(out, config.get("amount_col_candidates"), "amount")
        type_col = _resolve_column(out, config.get("type_col_candidates"), "type indicator")

    else:
        raise ValueError(
            f"Unsupported amount_style: {amount_style!r}. "
            "Use 'signed', 'debit_credit', or 'signed_with_type'."
    )

    pending_col = _resolve_column(
        out,
        config.get("pending_col_candidates"),
        "pending",
        required=False
    )

    out = out.rename(columns={date_col: "date", desc_col: "description"})

    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date.astype("string")
    out["description"] = out["description"].astype(str).str.strip()

    if amount_style == "signed":
        out["amount"] = _clean_money_series(out[amount_col])

    elif amount_style == "debit_credit":
        debit = _clean_money_series(out[debit_col]).fillna(0)
        credit = _clean_money_series(out[credit_col]).fillna(0)
        out["amount"] = credit - debit

    elif amount_style == "signed_with_type":
        out["amount"] = _clean_money_series(out[amount_col]).abs()

        debit_values = {str(v).strip().lower() for v in config.get("debit_type_values", ["debit"])}
        credit_values = {str(v).strip().lower() for v in config.get("credit_type_values", ["credit"])}

        type_vals = out[type_col].astype(str).str.strip().str.lower()

        out.loc[type_vals.isin(debit_values), "amount"] *= -1
        out.loc[type_vals.isin(credit_values), "amount"] = out.loc[type_vals.isin(credit_values), "amount"].abs()

    if pending_col:
        true_values = config.get("pending_true_values", [True, "TRUE", "True", "Yes", "Y"])
        true_values_normalized = {str(v).strip().lower() for v in true_values}

        out["Pending"] = (
            out[pending_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(true_values_normalized)
        )
    elif "Pending" not in out.columns:
        out["Pending"] = False

    out = out.dropna(subset=["date", "description", "amount"]).copy()

    out["date"] = out["date"].astype(str)

    return out