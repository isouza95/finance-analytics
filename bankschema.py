import pandas as pd

BANK_CONFIGS = {
    "generic_signed_amount": {
        "date_col": "date",
        "desc_col": "description",
        "amount_col": "amount",
        "pending_col": "Pending",
        "pending_true_values": [True, "TRUE", "True", "Yes", "Y", "y"],
        "amount_style": "signed",
    },
    "bank_x_export": {
        "date_col": "Transaction Date",
        "desc_col": "Details",
        "amount_col": "Amount",
        "pending_col": "Status",
        "pending_true_values": ["Pending"],
        "amount_style": "signed",
    },
    "bank_y_export": {
        "date_col": "Posted Date",
        "desc_col": "Description",
        "debit_col": "Debit",
        "credit_col": "Credit",
        "pending_col": None,
        "amount_style": "debit_credit",
    }
}

def normalize_transactions(df, config):
    out = df.copy()
    out = out.rename(columns={
        config["date_col"]: "date",
        config["desc_col"]: "description",
        config["amount_col"]: "amount",
    }
                    )

    out["date"] = pd.to_datetime(out["date"]).dt.date.astype(str)
    out["description"] = out["description"].astype(str).str.strip()
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce")

    pending_col = config.get("pending_col")
    if pending_col and pending_col in out.columns:
        out["Pending"] = out[pending_col].astype(str).str.strip().str.lower().isin(
            ["true", "1", "yes", "y"]
        )
    return out

    